"""File discovery, media helpers, subtitle parsing, and course-tree utilities."""
from __future__ import annotations

import hashlib
import html
import mimetypes
import os
import posixpath
import re
import shutil
import subprocess
import zipfile
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from typing import Any
from xml.etree import ElementTree

from models import CourseFile, PlaybackProgress, db

VIDEO_EXTENSIONS = {".mp4", ".m4v", ".mov", ".webm", ".mkv", ".avi", ".wmv", ".flv", ".ogv"}
AUDIO_EXTENSIONS = {
    ".mp3", ".wav", ".flac", ".aac", ".m4a", ".ogg", ".oga", ".opus",
    ".wma", ".aiff", ".aif", ".alac",
}
PDF_EXTENSIONS = {".pdf"}
EPUB_EXTENSIONS = {".epub"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".avif"}
HTML_EXTENSIONS = {".html", ".htm"}
TEXT_EXTENSIONS = {".txt", ".md", ".markdown", ".rst", ".log"}
SUBTITLE_EXTENSIONS = {".srt", ".vtt", ".ass", ".ssa", ".sub"}
DOWNLOAD_EXTENSIONS = {
    ".doc", ".docx", ".odt", ".rtf", ".ppt", ".pptx", ".odp", ".xls", ".xlsx",
    ".ods", ".csv", ".json", ".xml", ".zip", ".7z", ".rar", ".tar", ".gz",
    ".py", ".js", ".css", ".ipynb", ".psd", ".ai", ".sketch",
}
IGNORED_NAMES = {".ds_store", "thumbs.db", "desktop.ini", "ehthumbs.db"}
IGNORED_DIRECTORIES = {".git", ".svn", "__pycache__", ".venv", "node_modules", "$recycle.bin"}


def get_file_type(extension: str) -> str:
    ext = extension.lower()
    if ext in VIDEO_EXTENSIONS:
        return "video"
    if ext in AUDIO_EXTENSIONS:
        return "audio"
    if ext in PDF_EXTENSIONS:
        return "pdf"
    if ext in EPUB_EXTENSIONS:
        return "epub"
    if ext in IMAGE_EXTENSIONS:
        return "image"
    if ext in HTML_EXTENSIONS:
        return "html"
    if ext in TEXT_EXTENSIONS:
        return "text"
    if ext in SUBTITLE_EXTENSIONS:
        return "subtitle"
    if ext in DOWNLOAD_EXTENSIONS:
        return "download"
    # Keep unfamiliar files in the course rather than silently losing them.
    return "file"


def natural_key(value: str) -> tuple[tuple[int, Any], ...]:
    """Sort lesson2 before lesson10 without comparing unlike Python types."""
    parts = re.split(r"(\d+)", str(value).casefold())
    return tuple((1, int(part)) if part.isdigit() else (0, part) for part in parts)


def format_duration(seconds: float | int | None) -> str:
    value = max(0, int(seconds or 0))
    hours, remainder = divmod(value, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


def format_duration_human(seconds: float | int | None) -> str:
    value = max(0, int(seconds or 0))
    hours, remainder = divmod(value, 3600)
    minutes = remainder // 60
    if hours and minutes:
        return f"{hours}h {minutes}m"
    if hours:
        return f"{hours}h"
    return f"{minutes}m"


def format_file_size(size: int | None) -> str:
    value = max(0, int(size or 0))
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} TB"


def generate_file_hash(course_id: int, relative_path: str) -> str:
    canonical = f"{course_id}:{PurePosixPath(relative_path).as_posix().casefold()}"
    return hashlib.sha256(canonical.encode("utf-8", "surrogatepass")).hexdigest()[:16]


def _run_probe(arguments: list[str], timeout: int = 8) -> str | None:
    if not shutil.which(arguments[0]):
        return None
    try:
        result = subprocess.run(arguments, capture_output=True, text=True, timeout=timeout, check=False)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return None
    return None


def get_media_duration(file_path: str) -> int | None:
    result = _run_probe([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", file_path,
    ])
    try:
        duration = float(result) if result else 0
        return max(1, round(duration)) if duration > 0 else None
    except (ValueError, OverflowError):
        return None


def get_video_quality(file_path: str) -> str | None:
    result = _run_probe([
        "ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
        "stream=height", "-of", "default=noprint_wrappers=1:nokey=1", file_path,
    ])
    try:
        height = int(result) if result else 0
    except ValueError:
        return None
    if height >= 2160:
        return "4K"
    if height >= 1440:
        return "1440p"
    if height >= 1080:
        return "1080p"
    if height >= 720:
        return "720p"
    if height >= 480:
        return "480p"
    return f"{height}p" if height else None


def extract_video_thumbnail(file_path: str, output_dir: str) -> str | None:
    """Create a small local poster image when ffmpeg is installed."""
    if not shutil.which("ffmpeg"):
        return None
    duration = get_media_duration(file_path)
    if not duration:
        return None
    os.makedirs(output_dir, exist_ok=True)
    image_name = hashlib.sha256(os.path.abspath(file_path).encode()).hexdigest()[:20] + ".jpg"
    output_path = os.path.join(output_dir, image_name)
    if not os.path.exists(output_path):
        try:
            subprocess.run([
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", str(max(0, int(duration * 0.12))),
                "-i", file_path, "-frames:v", "1", "-vf", "scale=640:-2", "-q:v", "4", "-y", output_path,
            ], capture_output=True, timeout=15, check=False)
        except (OSError, subprocess.TimeoutExpired):
            return None
    return f"/thumbnails/{image_name}" if os.path.isfile(output_path) else None


def _is_inside(path: str, root: str) -> bool:
    try:
        return os.path.commonpath([os.path.realpath(path), os.path.realpath(root)]) == os.path.realpath(root)
    except (OSError, ValueError):
        return False


def scan_course_folder(course: Any, thumbnail_dir: str | None = None) -> list[CourseFile]:
    """Rescan a course folder in a stable, natural order and retain progress for matches."""
    root = os.path.realpath(os.path.expanduser(course.root_path))
    if not os.path.isdir(root):
        course.is_available = False
        db.session.commit()
        return []

    course.root_path = root
    course.is_available = True
    existing_rows = CourseFile.query.filter_by(course_id=course.id).all()
    existing_by_path = {PurePosixPath(row.relative_path).as_posix().casefold(): row for row in existing_rows}
    old_hashes = {row.file_hash for row in existing_rows if row.file_hash}
    active_hashes: set[str] = set()
    scanned: list[CourseFile] = []

    for current_root, directories, filenames in os.walk(root, followlinks=False):
        directories[:] = sorted(
            [name for name in directories if not name.startswith(".") and name.casefold() not in IGNORED_DIRECTORIES],
            key=natural_key,
        )
        filenames.sort(key=natural_key)
        for order_index, filename in enumerate(filenames):
            if filename.startswith(".") or filename.casefold() in IGNORED_NAMES:
                continue
            full_path = os.path.join(current_root, filename)
            if not os.path.isfile(full_path) or not _is_inside(full_path, root):
                continue
            extension = Path(filename).suffix.lower()
            file_type = get_file_type(extension)
            relative_path = os.path.relpath(full_path, root).replace(os.sep, "/")
            key = PurePosixPath(relative_path).as_posix().casefold()
            try:
                size = os.path.getsize(full_path)
            except OSError:
                continue

            record = existing_by_path.get(key)
            if record is not None:
                file_hash = record.file_hash
                record.file_path = os.path.realpath(full_path)
                record.relative_path = relative_path
                record.file_name = filename
                record.file_type = file_type
                record.file_extension = extension
                record.file_size = size
                record.parent_folder = str(PurePosixPath(relative_path).parent)
                if record.parent_folder == ".":
                    record.parent_folder = None
                record.order_index = order_index
            else:
                file_hash = generate_file_hash(course.id, relative_path)
                if file_hash in old_hashes or CourseFile.query.filter_by(file_hash=file_hash).first():
                    file_hash = hashlib.sha256(f"{root}:{relative_path}".encode()).hexdigest()[:16]
                record = CourseFile(
                    file_hash=file_hash,
                    course_id=course.id,
                    file_path=os.path.realpath(full_path),
                    relative_path=relative_path,
                    file_name=filename,
                    file_type=file_type,
                    file_extension=extension,
                    file_size=size,
                    parent_folder=str(PurePosixPath(relative_path).parent),
                    order_index=order_index,
                )
                if record.parent_folder == ".":
                    record.parent_folder = None
                db.session.add(record)

            if file_type in {"audio", "video"} and record.duration is None:
                record.duration = get_media_duration(record.file_path)
            if file_type == "video":
                if record.video_quality is None:
                    record.video_quality = get_video_quality(record.file_path)
                if record.thumbnail is None and thumbnail_dir:
                    record.thumbnail = extract_video_thumbnail(record.file_path, thumbnail_dir)

            active_hashes.add(file_hash)
            scanned.append(record)

    for row in existing_rows:
        if row.file_hash not in active_hashes:
            db.session.delete(row)

    course.total_files = len(scanned)
    course.total_duration = sum(
        int(row.duration or 0) for row in scanned if row.file_type in {"audio", "video"}
    )
    db.session.commit()
    return sorted(scanned, key=lambda row: natural_key(row.relative_path))


def get_folder_structure(course_id: int) -> tuple[dict[str, Any], dict[int, PlaybackProgress], set[int]]:
    """Build a curriculum tree and per-file progress index for a course page/player."""
    files = CourseFile.query.filter_by(course_id=course_id).order_by(CourseFile.relative_path).all()
    progress_rows = PlaybackProgress.query.filter_by(course_id=course_id).all()
    progress_map = {row.file_id: row for row in progress_rows}
    watched_ids = {row.file_id for row in progress_rows if row.completed}

    def new_node(name: str, path: str) -> dict[str, Any]:
        return {
            "name": name,
            "path": path,
            "children": [],
            "files": [],
            "total_duration": 0,
            "watched_duration": 0,
            "file_count": 0,
        }

    root = new_node("Course content", "")
    for file in files:
        # Sidecar caption files are represented in the transcript panel, not as lessons.
        if file.file_type == "subtitle":
            continue
        parts = PurePosixPath(file.relative_path).parts
        node = root
        for part in parts[:-1]:
            folder_path = f"{node['path']}/{part}".strip("/")
            child = next((item for item in node["children"] if item["name"] == part), None)
            if child is None:
                child = new_node(part, folder_path)
                node["children"].append(child)
            node = child
        node["files"].append(file)
        node["file_count"] += 1
        if file.file_type in {"audio", "video"}:
            node["total_duration"] += int(file.duration or 0)
            progress = progress_map.get(file.id)
            if progress and progress.completed:
                node["watched_duration"] += int(file.duration or 0)

    def calculate(node: dict[str, Any]) -> None:
        for child in node["children"]:
            calculate(child)
            node["total_duration"] += child["total_duration"]
            node["watched_duration"] += child["watched_duration"]
            node["file_count"] += child["file_count"]
        node["children"].sort(key=lambda item: natural_key(item["name"]))
        node["files"].sort(key=lambda item: natural_key(item.file_name))

    calculate(root)
    return root, progress_map, watched_ids


def tree_to_json(node: dict[str, Any], watched_ids: set[int] | None = None) -> dict[str, Any]:
    return {
        "name": node["name"],
        "path": node["path"],
        "children": [tree_to_json(child, watched_ids) for child in node["children"]],
        "files": [
            {
                "id": file.id,
                "file_hash": file.file_hash,
                "file_name": file.file_name,
                "display_name": file.title,
                "file_type": file.file_type,
                "duration": file.duration or 0,
                "file_size": file.file_size or 0,
                "parent_folder": file.parent_folder,
                "thumbnail": file.thumbnail,
                "completed": (
                    file.id in watched_ids if watched_ids is not None
                    else bool(file.id and any(p.file_id == file.id and p.completed for p in file.progress))
                ),
            }
            for file in node["files"]
        ],
        "total_duration": node["total_duration"],
        "watched_duration": node["watched_duration"],
        "file_count": node["file_count"],
    }


def _track_language(filename: str, media_stem: str) -> tuple[str, str]:
    stem = Path(filename).stem
    suffix = stem[len(media_stem):].lstrip("._-") if stem.casefold().startswith(media_stem.casefold()) else ""
    if not suffix:
        return "und", "Captions"
    match = re.search(r"([a-z]{2,3}(?:[-_][a-z]{2})?)", suffix, re.IGNORECASE)
    if match:
        language = match.group(1).replace("_", "-").lower()
        labels = {"en": "English", "es": "Spanish", "fr": "French", "de": "German", "it": "Italian", "pt": "Portuguese", "ar": "Arabic", "ja": "Japanese", "zh": "Chinese", "ru": "Russian"}
        return language, labels.get(language.split("-")[0], language.upper())
    return "und", suffix.replace(".", " ").replace("_", " ").replace("-", " ").title() or "Captions"


def associated_subtitles(file: CourseFile) -> list[dict[str, Any]]:
    """Match exact sidecars and language-suffixed sidecars without loose prefix collisions."""
    if file.file_type not in {"video", "audio"}:
        return []
    media_path = PurePosixPath(file.relative_path)
    media_stem = media_path.stem
    parent = str(media_path.parent)
    if parent == ".":
        parent = None
    candidates = CourseFile.query.filter_by(course_id=file.course_id, file_type="subtitle").all()
    tracks: list[dict[str, Any]] = []
    for subtitle in candidates:
        subtitle_path = PurePosixPath(subtitle.relative_path)
        if (str(subtitle_path.parent) if str(subtitle_path.parent) != "." else None) != parent:
            continue
        sidecar_stem = subtitle_path.stem
        media_folded, sidecar_folded = media_stem.casefold(), sidecar_stem.casefold()
        if sidecar_folded == media_folded:
            suffix = ""
            exact = 0
        elif any(sidecar_folded.startswith(media_folded + separator) for separator in (".", "_", "-")):
            suffix = sidecar_stem[len(media_stem):]
            exact = 1
        else:
            continue
        language, label = _track_language(subtitle.file_name, media_stem)
        if not suffix:
            language, label = "und", "Captions"
        tracks.append({
            "key": f"sidecar:{subtitle.file_hash}",
            "label": label,
            "language": language,
            "source": "folder",
            "url": f"/player/subtitles/{subtitle.file_hash}.vtt",
            "file_hash": subtitle.file_hash,
            "exact": exact,
            "_path": subtitle.relative_path,
        })
    for attached in file.attached_subtitles:
        tracks.append({
            "key": f"attached:{attached.id}",
            "id": attached.id,
            "label": attached.label,
            "language": attached.language or "und",
            "source": "attached",
            "url": f"/player/subtitles/attached/{attached.id}.vtt",
            "exact": 0,
            "_path": attached.original_name or "",
        })
    tracks.sort(key=lambda track: (track["exact"], track["label"].casefold(), track["_path"].casefold()))
    for track in tracks:
        track.pop("exact", None)
        track.pop("_path", None)
    return tracks


_TIMESTAMP = re.compile(r"(?:(\d{1,2}):)?(\d{1,2}):(\d{2})[,.](\d{1,3})")


def _time_seconds(value: str) -> float | None:
    match = _TIMESTAMP.search(value.strip())
    if not match:
        return None
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2))
    seconds = int(match.group(3))
    millis = int((match.group(4) + "000")[:3])
    return hours * 3600 + minutes * 60 + seconds + millis / 1000


def _plain_caption(value: str) -> str:
    value = re.sub(r"\{\\[^}]*\}", "", value)
    value = re.sub(r"<[^>]*>", "", value)
    value = value.replace(r"\N", "\n").replace(r"\n", "\n").replace(r"\h", " ")
    value = html.unescape(value)
    value = re.sub(r"[ \t]+", " ", value)
    return value.strip()


def parse_subtitles(content: str, extension: str) -> list[dict[str, Any]]:
    """Parse WebVTT, SRT, common ASS/SSA, and MicroDVD captions into safe cue records."""
    ext = extension.lower()
    if not ext.startswith("."):
        ext = "." + ext
    raw = content.replace("\ufeff", "").replace("\r\n", "\n").replace("\r", "\n")
    cues: list[dict[str, Any]] = []

    if ext in {".ass", ".ssa"}:
        for line in raw.splitlines():
            if not line.strip().casefold().startswith("dialogue:"):
                continue
            parts = line.split(",", 9)
            if len(parts) != 10:
                continue
            start, end = _time_seconds(parts[1]), _time_seconds(parts[2])
            text = _plain_caption(parts[9])
            if start is not None and end is not None and end > start and text:
                cues.append({"start": start, "end": end, "text": text})
    elif ext == ".sub":
        for line in raw.splitlines():
            match = re.match(r"\{(\d+)\}\{(\d+)\}(.*)", line)
            if not match:
                continue
            start, end = int(match.group(1)) / 25, int(match.group(2)) / 25
            text = _plain_caption(match.group(3))
            if end > start and text:
                cues.append({"start": start, "end": end, "text": text})
    else:
        for block in re.split(r"\n\s*\n", raw):
            lines = [line.strip("\ufeff") for line in block.splitlines() if line.strip()]
            if not lines or lines[0].strip().upper().startswith(("WEBVTT", "NOTE", "STYLE", "REGION")):
                continue
            timing_index = next((i for i, line in enumerate(lines) if "-->" in line), None)
            if timing_index is None:
                continue
            timing = lines[timing_index]
            left, right = timing.split("-->", 1)
            start, end = _time_seconds(left), _time_seconds(right)
            text = _plain_caption("\n".join(lines[timing_index + 1:]))
            if start is not None and end is not None and end > start and text:
                cues.append({"start": start, "end": end, "text": text})

    cues.sort(key=lambda cue: (cue["start"], cue["end"]))
    # Prevent malformed files from shipping pathological cue tables to the browser.
    return cues[:100_000]


def cues_to_webvtt(cues: list[dict[str, Any]]) -> str:
    def stamp(seconds: float) -> str:
        millis = round(max(0, seconds) * 1000)
        hours, millis = divmod(millis, 3_600_000)
        minutes, millis = divmod(millis, 60_000)
        whole_seconds, millis = divmod(millis, 1000)
        return f"{hours:02d}:{minutes:02d}:{whole_seconds:02d}.{millis:03d}"

    blocks = ["WEBVTT", ""]
    for cue in cues:
        text = html.escape(cue["text"], quote=False).replace("\n", "\n")
        blocks.extend([
            f"{stamp(cue['start'])} --> {stamp(cue['end'])}",
            text,
            "",
        ])
    return "\n".join(blocks)


def read_subtitle_file(path: str) -> tuple[list[dict[str, Any]], str]:
    extension = Path(path).suffix.lower()
    with open(path, "r", encoding="utf-8-sig", errors="replace") as source:
        raw = source.read(10 * 1024 * 1024 + 1)
    if len(raw) > 10 * 1024 * 1024:
        raise ValueError("Subtitle file is larger than 10 MB")
    cues = parse_subtitles(raw, extension)
    return cues, cues_to_webvtt(cues)


class _ReadableHTML(HTMLParser):
    """Extract readable chapter text without executing or returning EPUB markup."""
    BLOCK_TAGS = {"p", "div", "br", "li", "h1", "h2", "h3", "h4", "blockquote", "tr"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.ignored_depth = 0
        self.title_parts: list[str] = []
        self.heading_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "svg", "noscript"}:
            self.ignored_depth += 1
        if tag in self.BLOCK_TAGS:
            self.parts.append("\n")
        if tag in {"h1", "h2", "h3", "title"}:
            self.heading_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "svg", "noscript"} and self.ignored_depth:
            self.ignored_depth -= 1
        if tag in self.BLOCK_TAGS:
            self.parts.append("\n")
        if tag in {"h1", "h2", "h3", "title"} and self.heading_depth:
            self.heading_depth -= 1

    def handle_data(self, data: str) -> None:
        if self.ignored_depth:
            return
        text = re.sub(r"\s+", " ", data).strip()
        if text:
            self.parts.append(text + " ")
            if self.heading_depth:
                self.title_parts.append(text)


def extract_epub_chapters(path: str) -> list[dict[str, str]]:
    """Read EPUB spine text with Python's standard library as an offline-friendly reader."""
    max_total = 64 * 1024 * 1024
    chapters: list[dict[str, str]] = []
    with zipfile.ZipFile(path) as book:
        infos = {info.filename: info for info in book.infolist() if not info.is_dir()}
        container = book.read("META-INF/container.xml")
        container_root = ElementTree.fromstring(container)
        rootfile = next((node.attrib.get("full-path") for node in container_root.iter() if node.tag.endswith("rootfile")), None)
        if not rootfile or rootfile not in infos:
            raise ValueError("This EPUB has no readable package document")
        package = ElementTree.fromstring(book.read(rootfile))
        manifest: dict[str, str] = {}
        for item in package.iter():
            if item.tag.endswith("item"):
                item_id, href = item.attrib.get("id"), item.attrib.get("href")
                media_type = item.attrib.get("media-type", "")
                if item_id and href and ("html" in media_type or "xhtml" in media_type):
                    manifest[item_id] = posixpath.normpath(posixpath.join(posixpath.dirname(rootfile), href.split("#", 1)[0]))
        spine_ids = [node.attrib.get("idref") for node in package.iter() if node.tag.endswith("itemref")]
        consumed = 0
        for href in spine_ids:
            member = manifest.get(href or "")
            if not member or member not in infos:
                continue
            info = infos[member]
            consumed += info.file_size
            if info.file_size > 8 * 1024 * 1024 or consumed > max_total:
                continue
            try:
                source = book.read(member).decode("utf-8", errors="replace")
            except (KeyError, OSError):
                continue
            parser = _ReadableHTML()
            parser.feed(source)
            text = re.sub(r"\n{3,}", "\n\n", "".join(parser.parts)).strip()
            if text:
                title = " ".join(parser.title_parts).strip() or PurePosixPath(member).stem.replace("_", " ")
                chapters.append({"title": title[:180], "text": text[:300_000]})
    if not chapters:
        raise ValueError("No readable text chapters were found in this EPUB")
    return chapters[:250]


def mime_for(path: str) -> str:
    return mimetypes.guess_type(path)[0] or "application/octet-stream"
