"""LocalAcademy 0.2 — self-hosted course library and learning player."""
from __future__ import annotations

import json
import math
import os
import secrets
import threading
import time
import zipfile
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flask import (
    Flask, abort, flash, jsonify, redirect, render_template, request,
    send_file, send_from_directory, url_for,
)
from sqlalchemy import func, or_
from werkzeug.utils import secure_filename

from library import (
    HTML_EXTENSIONS, SUBTITLE_EXTENSIONS, associated_subtitles, cues_to_webvtt,
    extract_epub_chapters, format_duration, format_duration_human, format_file_size,
    get_folder_structure, mime_for, natural_key, parse_subtitles, read_subtitle_file,
    scan_course_folder, tree_to_json,
)
from models import (
    COURSE_SETTING_TYPES, DEFAULT_SETTINGS, SETTING_TYPES, Bookmark, Category,
    Course, CourseFile, CourseSetting, Creator, Note, PlaybackProgress, Setting,
    SubtitleTrack, Tag, db,
)


UI_THEMES = (
    {"id": "campus", "name": "Campus", "description": "Sage & forest · Light"},
    {"id": "ocean", "name": "Ocean", "description": "Coastal blue · Light"},
    {"id": "parchment", "name": "Parchment", "description": "Warm paper · Light"},
    {"id": "mulberry", "name": "Mulberry", "description": "Soft plum · Light"},
    {"id": "midnight", "name": "Midnight", "description": "Deep slate · Dark"},
)


_HOTKEY_ACTIONS = {
    "play_pause", "rewind_5s", "forward_5s", "prev_file", "next_file",
    "volume_up", "volume_down", "speed_up", "speed_down", "toggle_subtitles",
}
_hotkey_queue: deque[str] = deque(maxlen=40)
_hotkey_lock = threading.Lock()
_monitor_lock = threading.Lock()
_monitor_started = False


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 64 * 1024 * 1024
    ENABLE_DRIVE_MONITOR = True
    DRIVE_MONITOR_INTERVAL = 30


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().casefold() in {"1", "true", "yes", "on", "enabled"}


def _names(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        values = value.replace("\n", ",").split(",")
    elif isinstance(value, (tuple, list)):
        values = value
    else:
        values = [value]
    result: list[str] = []
    seen: set[str] = set()
    for item in values:
        name = str(item).strip()
        if name and name.casefold() not in seen:
            result.append(name[:255])
            seen.add(name.casefold())
    return result


def _ensure_named(model: type, names: list[str]) -> list[Any]:
    found = []
    for name in names:
        row = model.query.filter(func.lower(model.name) == name.casefold()).first()
        if row is None:
            row = model(name=name)
            db.session.add(row)
            db.session.flush()
        found.append(row)
    return found


def _set_course_taxonomy(course: Course, data: dict[str, Any]) -> None:
    for key, model, relation in (
        ("creator_names", Creator, "creators"),
        ("category_names", Category, "categories"),
        ("tag_names", Tag, "tags"),
    ):
        id_key = key.replace("_names", "_ids")
        if id_key in data:
            ids = data.get(id_key) or []
            if not isinstance(ids, (list, tuple)):
                ids = [ids]
            rows = model.query.filter(model.id.in_([int(item) for item in ids if str(item).isdigit()])).all() if ids else []
            setattr(course, relation, rows)
        elif key in data:
            setattr(course, relation, _ensure_named(model, _names(data.get(key))))


def _get_settings(course: Course | None = None) -> dict[str, Any]:
    values = {key: Setting.get(key, default) for key, default in DEFAULT_SETTINGS.items()}
    if course:
        override = CourseSetting.query.filter_by(course_id=course.id).first()
        if override:
            for key in COURSE_SETTING_TYPES:
                value = getattr(override, key, None)
                if value is not None:
                    values[key] = value
    return values


def _initialize_defaults() -> None:
    missing = {
        key: value
        for key, value in DEFAULT_SETTINGS.items()
        if Setting.query.filter_by(key=key).first() is None
    }
    if missing:
        Setting.set_many(missing)


def _get_or_create_progress(file: CourseFile) -> PlaybackProgress:
    row = PlaybackProgress.query.filter_by(file_id=file.id).order_by(PlaybackProgress.id).first()
    if row is None:
        row = PlaybackProgress(course_id=file.course_id, file_id=file.id, current_time=0, completed=False)
        db.session.add(row)
        db.session.flush()
    return row


def _course_progress(course: Course) -> dict[str, Any]:
    lessons = [file for file in course.files if file.file_type != "subtitle"]
    completed_ids = {
        row.file_id for row in PlaybackProgress.query.filter_by(course_id=course.id, completed=True).all()
    }
    watched = sum(1 for file in lessons if file.id in completed_ids)
    lesson_count = len(lessons)
    active = PlaybackProgress.query.filter_by(course_id=course.id, completed=False).filter(
        PlaybackProgress.current_time > 0
    ).count()
    percent = round(watched * 100 / lesson_count) if lesson_count else 0
    return {
        "watched": watched,
        "total": lesson_count,
        "percent": percent,
        "in_progress": bool(active or watched),
        "completed_ids": completed_ids,
    }


def _continue_learning(limit: int | None = 6, course_ids: list[int] | None = None) -> list[PlaybackProgress]:
    query = (
        PlaybackProgress.query.join(Course).join(CourseFile)
        .filter(PlaybackProgress.completed.is_(False), PlaybackProgress.current_time > 0)
        .filter(Course.is_available.is_(True), CourseFile.file_type != "subtitle")
        .order_by(PlaybackProgress.last_watched.desc())
    )
    if course_ids is not None:
        if not course_ids:
            return []
        query = query.filter(PlaybackProgress.course_id.in_(course_ids))
    rows = query.limit(max(30, (limit or 1000) * 8)).all()
    seen_courses: set[int] = set()
    result: list[PlaybackProgress] = []
    for row in rows:
        if row.course_id in seen_courses:
            continue
        seen_courses.add(row.course_id)
        result.append(row)
        if limit is not None and len(result) >= limit:
            break
    return result


def _progress_rows(course: Course) -> dict[int, PlaybackProgress]:
    rows = PlaybackProgress.query.filter_by(course_id=course.id).order_by(PlaybackProgress.last_watched.desc()).all()
    # Legacy databases could contain duplicates; the newest row wins.
    result: dict[int, PlaybackProgress] = {}
    for row in rows:
        result.setdefault(row.file_id, row)
    return result


def _file_by_hash(file_hash: str) -> CourseFile:
    file = CourseFile.query.filter_by(file_hash=file_hash).first_or_404()
    if not file.course or not file.course.is_available or not os.path.isfile(file.file_path):
        abort(404, description="This course file is currently unavailable.")
    return file


def _file_records_in_order(course_id: int) -> list[CourseFile]:
    rows = CourseFile.query.filter_by(course_id=course_id).all()
    rows = [row for row in rows if row.file_type != "subtitle"]
    return sorted(rows, key=lambda row: natural_key(row.relative_path))


def _safe_global_setting(key: str, value: Any) -> Any:
    kind = SETTING_TYPES[key]
    if kind is bool:
        return _bool(value)
    if kind is str:
        return str(value)[:300]
    try:
        parsed = kind(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"Invalid value for {key}") from exc
    if isinstance(parsed, float) and not math.isfinite(parsed):
        raise ValueError(f"Invalid value for {key}")
    bounds = {
        "playback_speed": (0.25, 4.0),
        "skip_silence_db_threshold": (-80, 0),
        "skip_silence_min_duration": (0.1, 5.0),
        "skip_silence_speed": (2.0, 16.0),
    }
    if key in bounds:
        low, high = bounds[key]
        parsed = max(low, min(high, parsed))
    return parsed


def _check_available_courses() -> None:
    changed = False
    for course in Course.query.all():
        available = os.path.isdir(course.root_path)
        if bool(course.is_available) != available:
            course.is_available = available
            changed = True
    if changed:
        db.session.commit()


def _drive_monitor_worker(app: Flask) -> None:
    while True:
        try:
            with app.app_context():
                _check_available_courses()
        except Exception as exc:  # a background health check must not take down the server
            app.logger.warning("Drive availability check failed: %s", exc)
        time.sleep(max(10, int(app.config.get("DRIVE_MONITOR_INTERVAL", 30))))


def _start_drive_monitor(app: Flask) -> None:
    global _monitor_started
    # Avoid two polling threads when a development server's reloader is enabled.
    if app.debug and os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        return
    with _monitor_lock:
        if _monitor_started:
            return
        thread = threading.Thread(target=_drive_monitor_worker, args=(app,), daemon=True, name="course-drive-monitor")
        thread.start()
        _monitor_started = True


def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    os.makedirs(app.instance_path, exist_ok=True)
    database_path = os.path.join(app.instance_path, "localacademy-v02.db")
    app.config.from_object(Config)
    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI=Config.SQLALCHEMY_DATABASE_URI or f"sqlite:///{database_path}",
    )
    if app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite:"):
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"connect_args": {"check_same_thread": False}}
    if test_config:
        app.config.update(test_config)
    db.init_app(app)

    @app.context_processor
    def inject_template_helpers() -> dict[str, Any]:
        return {
            "fmt_dur": format_duration,
            "fmt_dur_h": format_duration_human,
            "fmt_size": format_file_size,
            "site_name": "LocalAcademy",
            "ui_themes": UI_THEMES,
            "library_count": Course.query.count(),
            "nav_categories": Category.query.order_by(Category.name).limit(4).all(),
            "demo_mode": app.config.get("DEMO_MODE", False),
            "today_label": datetime.now(timezone.utc).strftime("%A, %d %B"),
        }

    with app.app_context():
        db.create_all()
        _initialize_defaults()

    @app.errorhandler(404)
    def page_not_found(error):
        if request.path.startswith("/api/") or request.accept_mimetypes.best == "application/json":
            return jsonify(error="This page or resource is not available."), 404
        return render_template("not_found.html", message=getattr(error, "description", None)), 404

    # ── Dashboard and search ───────────────────────────────────────────────
    @app.get("/")
    def index():
        continue_learning = _continue_learning(limit=4)
        courses = Course.query.order_by(Course.last_accessed.desc().nullslast(), Course.created_at.desc()).limit(8).all()
        stats = {
            "courses": Course.query.count(),
            "available": Course.query.filter_by(is_available=True).count(),
            "lessons": CourseFile.query.filter(CourseFile.file_type != "subtitle").count(),
            "watched": PlaybackProgress.query.filter_by(completed=True).count(),
            "study_seconds": int(db.session.query(func.sum(PlaybackProgress.current_time)).scalar() or 0),
            "notes": Note.query.count(),
        }
        cards = {course.id: _course_progress(course) for course in courses}
        recent_notes = (
            Note.query.join(CourseFile).join(Course)
            .filter(Course.is_available.is_(True))
            .order_by(Note.updated_at.desc()).limit(3).all()
        )
        starter_file = next((
            file for course in courses if course.is_available
            for file in _file_records_in_order(course.id)
            if file.file_type != "subtitle"
        ), None)
        return render_template(
            "dashboard.html", continue_learning=continue_learning, recent_courses=courses,
            course_cards=cards, stats=stats, recent_notes=recent_notes, starter_file=starter_file,
        )

    @app.get("/continue-watching")
    def continue_watching():
        items = _continue_learning(limit=None)
        cards = {item.course_id: _course_progress(item.course) for item in items}
        return render_template("continue_watching.html", items=items, course_cards=cards)

    @app.get("/api/stats")
    def api_stats():
        return jsonify(
            courses=Course.query.count(),
            available=Course.query.filter_by(is_available=True).count(),
            lessons=CourseFile.query.filter(CourseFile.file_type != "subtitle").count(),
            watched=PlaybackProgress.query.filter_by(completed=True).count(),
            study_seconds=int(db.session.query(func.sum(PlaybackProgress.current_time)).scalar() or 0),
        )

    @app.get("/search")
    def search():
        query = request.args.get("q", "").strip()[:120]
        if not query:
            return jsonify(courses=[], files=[])
        like = f"%{query}%"
        courses = Course.query.filter(
            or_(
                Course.display_name.ilike(like), Course.description.ilike(like),
                Course.creators.any(Creator.name.ilike(like)),
                Course.categories.any(Category.name.ilike(like)),
                Course.tags.any(Tag.name.ilike(like)),
            )
        ).order_by(Course.display_name).limit(8).all()
        files = CourseFile.query.join(Course).filter(
            Course.is_available.is_(True),
            CourseFile.file_type != "subtitle",
            or_(CourseFile.file_name.ilike(like), CourseFile.display_name.ilike(like), CourseFile.relative_path.ilike(like)),
        ).order_by(CourseFile.file_name).limit(12).all()
        return jsonify(
            courses=[{"id": course.id, "display_name": course.display_name, "url": url_for("course_detail", course_id=course.id)} for course in courses],
            files=[{"file_hash": file.file_hash, "display_name": file.title, "course_name": file.course.display_name, "url": url_for("play", file_hash=file.file_hash)} for file in files],
        )

    # ── Course library ────────────────────────────────────────────────────
    @app.get("/courses")
    def courses():
        view = request.args.get("view", "grid")
        filter_type = request.args.get("filter", "all")
        if filter_type not in {"all", "available", "unavailable", "progress"}:
            filter_type = "all"
        sort_by = request.args.get("sort", "name")
        if sort_by not in {"name", "recent", "accessed"}:
            sort_by = "name"
        query = Course.query
        if filter_type == "available":
            query = query.filter_by(is_available=True)
        elif filter_type == "unavailable":
            query = query.filter_by(is_available=False)
        elif filter_type == "progress":
            query = query.join(PlaybackProgress).filter(
                PlaybackProgress.current_time > 0, PlaybackProgress.completed.is_(False)
            ).distinct()
        search_query = request.args.get("q", "").strip()[:120]
        if search_query:
            like = f"%{search_query}%"
            query = query.filter(or_(
                Course.display_name.ilike(like), Course.description.ilike(like),
                Course.creators.any(Creator.name.ilike(like)),
                Course.categories.any(Category.name.ilike(like)),
                Course.tags.any(Tag.name.ilike(like)),
            ))
        sort_columns = {
            "name": (func.lower(Course.display_name), Course.id),
            "recent": (Course.created_at.desc(), Course.id.desc()),
            "accessed": (Course.last_accessed.desc().nullslast(), func.lower(Course.display_name)),
        }
        courses_list = query.order_by(*sort_columns[sort_by]).all()
        progress = {course.id: _course_progress(course) for course in courses_list}
        return render_template(
            "courses.html", courses=courses_list, course_cards=progress,
            view_mode=view if view in {"grid", "list"} else "grid", filter_type=filter_type,
            sort_by=sort_by, search_query=search_query, show_add_modal=request.args.get("add") == "1",
        )

    @app.post("/courses/add")
    def add_course():
        data = request.get_json(silent=True) or request.form.to_dict()
        name = str(data.get("display_name", "")).strip()[:255]
        raw_path = str(data.get("root_path", "")).strip()
        if not name or not raw_path:
            return jsonify(error="Enter both a course name and a folder path."), 400
        root_path = os.path.realpath(os.path.expanduser(raw_path))
        if not os.path.isdir(root_path):
            return jsonify(error="That folder does not exist on the computer running LocalAcademy."), 400
        if Course.query.filter_by(root_path=root_path).first():
            return jsonify(error="This folder is already in your library."), 409

        course = Course(
            display_name=name,
            root_path=root_path,
            is_available=True,
            description=str(data.get("description", "")).strip()[:20_000],
        )
        if os.name == "nt" and len(root_path) > 1 and root_path[1] == ":":
            course.drive_letter = root_path[0].upper()
        db.session.add(course)
        try:
            db.session.flush()
            _set_course_taxonomy(course, data)
            db.session.commit()
            files = scan_course_folder(course, os.path.join(app.instance_path, "thumbnails"))
        except Exception as exc:
            db.session.rollback()
            app.logger.exception("Course import failed")
            return jsonify(error=f"Could not add this course: {exc}"), 500
        return jsonify(success=True, course_id=course.id, files_found=len(files))

    @app.get("/courses/<int:course_id>")
    def course_detail(course_id: int):
        course = db.get_or_404(Course, course_id)
        course.last_accessed = datetime.now(timezone.utc)
        db.session.commit()
        tree, progress_map, watched_ids = get_folder_structure(course.id)
        lessons = sorted(
            [file for file in course.files if file.file_type != "subtitle"],
            key=lambda file: natural_key(file.relative_path),
        )
        latest = PlaybackProgress.query.filter_by(course_id=course.id, completed=False).filter(
            PlaybackProgress.current_time > 0
        ).order_by(PlaybackProgress.last_watched.desc()).first()
        resume_file = latest.file if latest and latest.file else (lessons[0] if lessons else None)
        stats = _course_progress(course)
        return render_template(
            "course_detail.html", course=course, tree=tree, progress_map=progress_map,
            watched_ids=watched_ids, tree_json=tree_to_json(tree, watched_ids), course_stats=stats,
            resume_file=resume_file, course_settings=_get_settings(course),
        )

    @app.post("/courses/<int:course_id>/rescan")
    def rescan_course(course_id: int):
        course = db.get_or_404(Course, course_id)
        try:
            files = scan_course_folder(course, os.path.join(app.instance_path, "thumbnails"))
        except Exception as exc:
            db.session.rollback()
            app.logger.exception("Course scan failed")
            return jsonify(error=f"Scan failed: {exc}"), 500
        return jsonify(success=True, files_count=len(files))

    @app.post("/courses/<int:course_id>/delete")
    def delete_course(course_id: int):
        course = db.get_or_404(Course, course_id)
        title = course.display_name
        db.session.delete(course)
        db.session.commit()
        if request.is_json:
            return jsonify(success=True)
        flash(f'"{title}" was removed from your library.', "success")
        return redirect(url_for("courses"))

    @app.post("/courses/<int:course_id>/metadata")
    def update_course_metadata(course_id: int):
        course = db.get_or_404(Course, course_id)
        data = request.get_json(silent=True) or {}
        if "display_name" in data:
            name = str(data["display_name"]).strip()
            if name:
                course.display_name = name[:255]
        if "description" in data:
            course.description = str(data["description"]).strip()[:20_000]
        if "thumbnail" in data:
            course.thumbnail = str(data["thumbnail"]).strip()[:512] or None
        _set_course_taxonomy(course, data)
        db.session.commit()
        return jsonify(success=True, course=course.to_dict())

    @app.post("/courses/<int:course_id>/thumbnail")
    def update_course_thumbnail(course_id: int):
        course = db.get_or_404(Course, course_id)
        data = request.get_json(silent=True) or request.form
        course.thumbnail = str(data.get("thumbnail", "")).strip()[:512] or None
        db.session.commit()
        return jsonify(success=True)

    @app.get("/courses/<int:course_id>/files")
    def course_files(course_id: int):
        db.get_or_404(Course, course_id)
        rows = CourseFile.query.filter_by(course_id=course_id).order_by(CourseFile.relative_path).all()
        return jsonify(files=[file.to_dict() for file in rows])

    # ── Course player ─────────────────────────────────────────────────────
    @app.get("/player/<string:file_hash>")
    def play(file_hash: str):
        file = _file_by_hash(file_hash)
        if file.file_type == "subtitle":
            abort(404)
        course = file.course
        course.last_accessed = datetime.now(timezone.utc)
        progress = _get_or_create_progress(file)
        db.session.commit()
        settings = _get_settings(course)
        notes = [row.to_dict() for row in Note.query.filter_by(file_id=file.id).order_by(Note.created_at.desc()).all()]
        bookmarks = [row.to_dict() for row in Bookmark.query.filter_by(file_id=file.id).order_by(Bookmark.timestamp).all()]
        all_notes = [
            row.to_dict() for row in Note.query.join(CourseFile).filter(CourseFile.course_id == course.id)
            .order_by(Note.created_at.desc()).limit(400).all()
        ]
        all_bookmarks = [
            row.to_dict() for row in Bookmark.query.join(CourseFile).filter(CourseFile.course_id == course.id)
            .order_by(Bookmark.timestamp).limit(400).all()
        ]
        tree, _, watched_ids = get_folder_structure(course.id)
        lesson_files = _file_records_in_order(course.id)
        current_index = next((i for i, item in enumerate(lesson_files) if item.id == file.id), 0)
        try:
            start_time = float(request.args.get("t", progress.current_time or 0))
            if not math.isfinite(start_time) or start_time < 0:
                start_time = 0
        except (TypeError, ValueError):
            start_time = 0
        if file.duration:
            start_time = min(start_time, max(0, file.duration - 0.25))
        tracks = associated_subtitles(file)
        player_data = {
            "fileHash": file.file_hash,
            "fileId": file.id,
            "fileType": file.file_type,
            "courseId": course.id,
            "startTime": start_time,
            "duration": file.duration or 0,
            "currentTime": progress.current_time or 0,
            "completed": bool(progress.completed),
            "settings": settings,
            "tracks": tracks,
            "files": [
                {"file_hash": item.file_hash, "file_id": item.id, "title": item.title,
                 "file_type": item.file_type, "duration": item.duration or 0}
                for item in lesson_files
            ],
            "currentIndex": current_index,
            "notes": notes,
            "bookmarks": bookmarks,
            "allNotes": all_notes,
            "allBookmarks": all_bookmarks,
            "watchedIds": list(watched_ids),
            "tree": tree_to_json(tree, watched_ids),
        }
        return render_template(
            "player.html", file=file, course=course, progress=progress, settings=settings,
            notes=notes, bookmarks=bookmarks, all_course_notes=all_notes,
            all_course_bookmarks=all_bookmarks, tree=tree, tree_json=player_data["tree"],
            subtitle_tracks=tracks, start_time=start_time, watched_file_ids=list(watched_ids),
            lesson_files=lesson_files, current_index=current_index, player_data=player_data,
        )

    @app.get("/player/serve/<string:file_hash>")
    def serve_file(file_hash: str):
        file = _file_by_hash(file_hash)
        # HTML lessons must be opened in the sandboxed reader route, never inline at the app origin.
        if file.file_type == "html":
            abort(404)
        response = send_file(
            file.file_path,
            mimetype="application/pdf" if file.file_type == "pdf" else mime_for(file.file_path),
            as_attachment=False,
            download_name=Path(file.file_name).name,
            conditional=True,
            max_age=0,
        )
        response.headers.setdefault("Content-Disposition", "inline")
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.get("/player/download/<string:file_hash>")
    def download_file(file_hash: str):
        file = _file_by_hash(file_hash)
        return send_file(file.file_path, as_attachment=True, download_name=Path(file.file_name).name, conditional=True)

    @app.get("/player/html/<string:file_hash>/")
    def serve_html_lesson(file_hash: str):
        file = _file_by_hash(file_hash)
        if Path(file.file_path).suffix.lower() not in HTML_EXTENSIONS:
            abort(404)
        response = send_file(file.file_path, mimetype="text/html", conditional=True, max_age=0)
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.get("/player/html/<string:file_hash>/<path:asset_path>")
    def serve_html_asset(file_hash: str, asset_path: str):
        file = _file_by_hash(file_hash)
        if Path(file.file_path).suffix.lower() not in HTML_EXTENSIONS:
            abort(404)
        asset_root = os.path.dirname(file.file_path)
        # send_from_directory rejects path traversal; only sidecar assets in this lesson folder resolve.
        return send_from_directory(asset_root, asset_path, conditional=True, max_age=0)

    @app.get("/player/text/<string:file_hash>")
    def serve_text(file_hash: str):
        file = _file_by_hash(file_hash)
        if file.file_type != "text":
            abort(404)
        try:
            with open(file.file_path, "r", encoding="utf-8-sig", errors="replace") as source:
                text = source.read(2 * 1024 * 1024 + 1)
        except OSError:
            abort(404)
        if len(text) > 2 * 1024 * 1024:
            text = text[:2 * 1024 * 1024] + "\n\n[Preview limited to 2 MB]"
        return app.response_class(text, content_type="text/plain; charset=utf-8")

    epub_cache: dict[tuple[str, float], list[dict[str, str]]] = {}

    @app.get("/player/epub/<string:file_hash>/chapters")
    def epub_chapters(file_hash: str):
        file = _file_by_hash(file_hash)
        if file.file_type != "epub":
            abort(404)
        key = (file.file_path, os.path.getmtime(file.file_path))
        try:
            chapters = epub_cache.get(key)
            if chapters is None:
                chapters = extract_epub_chapters(file.file_path)
                epub_cache.clear()
                epub_cache[key] = chapters
        except (OSError, ValueError, zipfile.BadZipFile) as exc:
            return jsonify(error=str(exc)), 422
        requested = request.args.get("chapter", type=int)
        if requested is None:
            return jsonify(chapters=[{"title": chapter["title"], "index": index} for index, chapter in enumerate(chapters)])
        if requested < 0 or requested >= len(chapters):
            return jsonify(error="Chapter not found"), 404
        return jsonify(chapter=chapters[requested], index=requested, count=len(chapters))

    @app.get("/player/subtitles/<string:subtitle_hash>.vtt")
    def serve_sidecar_subtitle(subtitle_hash: str):
        subtitle = CourseFile.query.filter_by(file_hash=subtitle_hash, file_type="subtitle").first_or_404()
        if not subtitle.course.is_available or not os.path.isfile(subtitle.file_path):
            abort(404)
        try:
            _, webvtt = read_subtitle_file(subtitle.file_path)
        except (OSError, ValueError) as exc:
            return app.response_class(f"WEBVTT\n\nNOTE {exc}\n", status=422, content_type="text/vtt; charset=utf-8")
        response = app.response_class(webvtt, content_type="text/vtt; charset=utf-8")
        response.headers["Cache-Control"] = "no-cache"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.get("/player/subtitles/attached/<int:track_id>.vtt")
    def serve_attached_subtitle(track_id: int):
        track = db.get_or_404(SubtitleTrack, track_id)
        if not track.file.course.is_available:
            abort(404)
        response = app.response_class(track.webvtt_content, content_type="text/vtt; charset=utf-8")
        response.headers["Cache-Control"] = "no-cache"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.post("/player/<string:file_hash>/subtitles")
    def attach_subtitle(file_hash: str):
        file = _file_by_hash(file_hash)
        if file.file_type not in {"video", "audio"}:
            return jsonify(error="Captions can only be attached to audio or video lessons."), 400
        uploaded = request.files.get("file")
        if uploaded is None or not uploaded.filename:
            return jsonify(error="Choose a subtitle file first."), 400
        filename = secure_filename(uploaded.filename)
        extension = Path(filename).suffix.lower()
        if extension not in SUBTITLE_EXTENSIONS:
            return jsonify(error="Use an SRT, VTT, ASS, SSA, or SUB caption file."), 400
        try:
            raw = uploaded.stream.read(10 * 1024 * 1024 + 1)
            if len(raw) > 10 * 1024 * 1024:
                return jsonify(error="Subtitle files must be 10 MB or smaller."), 413
            text = raw.decode("utf-8-sig", errors="replace")
            cues = parse_subtitles(text, extension)
            if not cues:
                return jsonify(error="No readable caption cues were found in that file."), 422
        except (OSError, ValueError) as exc:
            return jsonify(error=str(exc)), 400
        language = str(request.form.get("language", "und")).strip()[:16] or "und"
        label = str(request.form.get("label", "")).strip()[:120]
        if not label:
            label = Path(filename).stem.replace(".", " ").replace("_", " ").title() or "Captions"
        track = SubtitleTrack(
            file_id=file.id,
            label=label,
            language=language,
            original_name=filename,
            webvtt_content=cues_to_webvtt(cues),
        )
        db.session.add(track)
        db.session.commit()
        return jsonify(
            success=True,
            track={
                "key": f"attached:{track.id}", "id": track.id, "label": track.label,
                "language": track.language, "source": "attached",
                "url": url_for("serve_attached_subtitle", track_id=track.id),
            },
        )

    @app.delete("/player/subtitles/attached/<int:track_id>")
    def delete_attached_subtitle(track_id: int):
        track = db.get_or_404(SubtitleTrack, track_id)
        db.session.delete(track)
        db.session.commit()
        return jsonify(success=True)

    @app.get("/player/api/<string:file_hash>/transcript")
    def transcript(file_hash: str):
        file = _file_by_hash(file_hash)
        track_key = request.args.get("track", "")
        available = associated_subtitles(file)
        if not track_key and available:
            track_key = available[0]["key"]
        match = next((item for item in available if item["key"] == track_key), None)
        if match is None:
            return jsonify(error="Transcript not found", cues=[]), 404
        try:
            if track_key.startswith("sidecar:"):
                sidecar = CourseFile.query.filter_by(file_hash=track_key.split(":", 1)[1], file_type="subtitle").first_or_404()
                cues, _ = read_subtitle_file(sidecar.file_path)
            else:
                attached = SubtitleTrack.query.filter_by(id=match["id"], file_id=file.id).first_or_404()
                cues = parse_subtitles(attached.webvtt_content, ".vtt")
        except (OSError, ValueError) as exc:
            return jsonify(error=f"Could not read captions: {exc}", cues=[]), 422
        return jsonify(track=match, cues=cues)

    # ── Playback progress, notes, bookmarks, and lesson actions ─────────────
    @app.post("/player/progress/<string:file_hash>")
    def update_progress(file_hash: str):
        file = _file_by_hash(file_hash)
        data = request.get_json(silent=True) or {}
        try:
            current_time = float(data.get("current_time", 0) or 0)
        except (TypeError, ValueError):
            return jsonify(error="Invalid playback position."), 400
        if not math.isfinite(current_time) or current_time < 0:
            return jsonify(error="Invalid playback position."), 400
        if file.duration:
            current_time = min(current_time, float(file.duration))
        row = _get_or_create_progress(file)
        row.current_time = current_time
        row.completed = _bool(data.get("completed", row.completed))
        row.last_watched = datetime.now(timezone.utc)
        db.session.commit()
        return jsonify(success=True, progress=row.to_dict())

    @app.post("/api/mark-watched/<string:file_hash>")
    def mark_watched(file_hash: str):
        file = _file_by_hash(file_hash)
        data = request.get_json(silent=True) or {}
        row = _get_or_create_progress(file)
        row.completed = _bool(data.get("completed", True))
        row.last_watched = datetime.now(timezone.utc)
        if row.completed and file.duration:
            row.current_time = max(row.current_time or 0, float(file.duration))
        db.session.commit()
        return jsonify(success=True, completed=bool(row.completed))

    @app.post("/api/set-duration/<string:file_hash>")
    def set_duration(file_hash: str):
        file = _file_by_hash(file_hash)
        data = request.get_json(silent=True) or {}
        try:
            duration = float(data.get("duration", 0))
        except (TypeError, ValueError):
            return jsonify(error="Invalid duration."), 400
        if file.duration is None and math.isfinite(duration) and 0 < duration < 7 * 24 * 3600:
            file.duration = round(duration)
            db.session.commit()
        return jsonify(success=True)

    @app.post("/api/rename/<string:file_hash>")
    def rename_file(file_hash: str):
        file = _file_by_hash(file_hash)
        data = request.get_json(silent=True) or {}
        title = str(data.get("display_name", "")).strip()[:512]
        file.display_name = title or None
        db.session.commit()
        return jsonify(success=True, display_name=file.title)

    @app.route("/player/notes/<string:file_hash>", methods=["GET", "POST"])
    def manage_notes(file_hash: str):
        file = _file_by_hash(file_hash)
        if request.method == "GET":
            rows = Note.query.filter_by(file_id=file.id).order_by(Note.created_at.desc()).all()
            return jsonify(notes=[row.to_dict() for row in rows])
        data = request.get_json(silent=True) or {}
        content = str(data.get("content", "")).strip()
        if not content:
            return jsonify(error="Write a note before saving."), 400
        if len(content) > 5000:
            return jsonify(error="Notes are limited to 5,000 characters."), 400
        timestamp = data.get("timestamp")
        try:
            timestamp = float(timestamp) if timestamp is not None else None
        except (TypeError, ValueError, OverflowError):
            return jsonify(error="Invalid note timestamp."), 400
        if timestamp is not None and (not math.isfinite(timestamp) or timestamp < 0):
            return jsonify(error="Invalid note timestamp."), 400
        note = Note(file_id=file.id, content=content, timestamp=timestamp)
        db.session.add(note)
        db.session.commit()
        return jsonify(success=True, note=note.to_dict())

    @app.route("/player/notes/<int:note_id>", methods=["PUT", "DELETE"])
    def edit_note(note_id: int):
        note = db.get_or_404(Note, note_id)
        if request.method == "DELETE":
            db.session.delete(note)
            db.session.commit()
            return jsonify(success=True)
        data = request.get_json(silent=True) or {}
        content = str(data.get("content", "")).strip()
        if not content or len(content) > 5000:
            return jsonify(error="A note must contain 1 to 5,000 characters."), 400
        note.content = content
        note.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return jsonify(success=True, note=note.to_dict())

    @app.route("/player/bookmarks/<string:file_hash>", methods=["GET", "POST"])
    def manage_bookmarks(file_hash: str):
        file = _file_by_hash(file_hash)
        if request.method == "GET":
            rows = Bookmark.query.filter_by(file_id=file.id).order_by(Bookmark.timestamp).all()
            return jsonify(bookmarks=[row.to_dict() for row in rows])
        data = request.get_json(silent=True) or {}
        try:
            timestamp = float(data.get("timestamp"))
        except (TypeError, ValueError):
            return jsonify(error="A bookmark needs a valid timestamp."), 400
        if not math.isfinite(timestamp) or timestamp < 0:
            return jsonify(error="A bookmark needs a valid timestamp."), 400
        label = str(data.get("label", "")).strip()[:255] or f"Moment at {format_duration(timestamp)}"
        bookmark = Bookmark(file_id=file.id, timestamp=timestamp, label=label)
        db.session.add(bookmark)
        db.session.commit()
        return jsonify(success=True, bookmark=bookmark.to_dict())

    @app.delete("/player/bookmarks/<int:bookmark_id>")
    def delete_bookmark(bookmark_id: int):
        db.session.delete(db.get_or_404(Bookmark, bookmark_id))
        db.session.commit()
        return jsonify(success=True)

    @app.post("/player/timestamp-link")
    def timestamp_link():
        data = request.get_json(silent=True) or {}
        file_hash = str(data.get("file_hash", ""))
        file = _file_by_hash(file_hash)
        try:
            raw_seconds = float(data.get("timestamp", 0))
            seconds = max(0, int(raw_seconds)) if math.isfinite(raw_seconds) else 0
        except (TypeError, ValueError, OverflowError):
            seconds = 0
        link = url_for("play", file_hash=file.file_hash, t=seconds, _external=True)
        template = Setting.get("timestamp_template", DEFAULT_SETTINGS["timestamp_template"])
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds_part = divmod(remainder, 60)
        label = (
            template.replace("{HH}", f"{hours:02d}").replace("{MM}", f"{minutes:02d}")
            .replace("{SS}", f"{seconds_part:02d}").replace("{timestamp}", str(seconds)).replace("{url}", link)
        )
        return jsonify(link=link, markdown=label)

    # ── Settings ───────────────────────────────────────────────────────────
    @app.get("/settings")
    def settings_page():
        return render_template("settings.html", settings=_get_settings())

    @app.post("/settings/update")
    def update_settings():
        data = request.get_json(silent=True) or request.form.to_dict()
        values = {}
        try:
            for key, kind in SETTING_TYPES.items():
                if key in data:
                    values[key] = _safe_global_setting(key, data[key])
        except ValueError as exc:
            return jsonify(error=str(exc)), 400
        if "hotkeys" in data:
            hotkeys = data["hotkeys"]
            if isinstance(hotkeys, str):
                try:
                    hotkeys = json.loads(hotkeys)
                except json.JSONDecodeError:
                    hotkeys = {}
            if isinstance(hotkeys, dict):
                values["hotkeys"] = {str(key): str(value)[:32] for key, value in hotkeys.items() if str(key) in _HOTKEY_ACTIONS}
        if values:
            Setting.set_many(values)
        if request.is_json:
            return jsonify(success=True, settings=_get_settings())
        flash("Your learning preferences have been saved.", "success")
        return redirect(url_for("settings_page"))

    @app.route("/settings/course/<int:course_id>", methods=["GET", "POST"])
    def course_settings(course_id: int):
        course = db.get_or_404(Course, course_id)
        override = CourseSetting.query.filter_by(course_id=course.id).first()
        if request.method == "GET":
            if request.accept_mimetypes.best == "application/json":
                return jsonify(override.to_dict() if override else {})
            return render_template("course_settings.html", course=course, settings=_get_settings(course), overrides=override.to_dict() if override else {})

        data = request.get_json(silent=True) or request.form.to_dict()
        if override is None:
            override = CourseSetting(course_id=course.id)
            db.session.add(override)
        try:
            for key, kind in COURSE_SETTING_TYPES.items():
                if key not in data:
                    continue
                value = data[key]
                if value is None or value == "":
                    setattr(override, key, None)
                else:
                    parsed = _safe_global_setting(key, value)
                    setattr(override, key, parsed)
        except ValueError as exc:
            db.session.rollback()
            return jsonify(error=str(exc)), 400
        if all(getattr(override, key) is None for key in COURSE_SETTING_TYPES):
            db.session.delete(override)
        db.session.commit()
        return jsonify(success=True)

    @app.post("/settings/course/<int:course_id>/reset")
    def reset_course_settings(course_id: int):
        db.get_or_404(Course, course_id)
        override = CourseSetting.query.filter_by(course_id=course_id).first()
        if override:
            db.session.delete(override)
            db.session.commit()
        return jsonify(success=True)

    @app.post("/settings/reset")
    def reset_settings():
        Setting.query.delete()
        db.session.commit()
        _initialize_defaults()
        return jsonify(success=True)

    @app.get("/settings/hotkeys")
    def get_hotkeys():
        return jsonify(hotkeys=Setting.get("hotkeys", DEFAULT_SETTINGS["hotkeys"]))

    # ── Searchable creators, categories, and tags ──────────────────────────
    taxonomy_models = {"creators": Creator, "categories": Category, "tags": Tag}

    @app.get("/collections")
    def collections():
        data = {name: model.query.order_by(model.name).all() for name, model in taxonomy_models.items()}
        return render_template("collections.html", collections=data)

    @app.get("/collections/<kind>/<int:item_id>")
    def collection_detail(kind: str, item_id: int):
        model = taxonomy_models.get(kind)
        if model is None:
            abort(404)
        item = db.get_or_404(model, item_id)
        courses_list = sorted(item.courses, key=lambda course: course.display_name.casefold())
        course_cards = {course.id: _course_progress(course) for course in courses_list}
        return render_template("collection_detail.html", kind=kind, item=item, courses=courses_list, course_cards=course_cards)

    @app.get("/api/taxonomy/<kind>")
    def list_taxonomy(kind: str):
        model = taxonomy_models.get(kind)
        if model is None:
            abort(404)
        rows = model.query.order_by(model.name).all()
        return jsonify(items=[{**row.to_dict(), "course_count": len(row.courses)} for row in rows])

    @app.post("/api/taxonomy/<kind>")
    def create_taxonomy(kind: str):
        model = taxonomy_models.get(kind)
        if model is None:
            abort(404)
        data = request.get_json(silent=True) or {}
        name = str(data.get("name", "")).strip()[:255]
        if not name:
            return jsonify(error="A name is required."), 400
        existing = model.query.filter(func.lower(model.name) == name.casefold()).first()
        if existing:
            return jsonify(error="That name already exists.", item=existing.to_dict()), 409
        row = model(name=name, icon=data.get("icon"), banner=data.get("banner"))
        db.session.add(row)
        db.session.commit()
        return jsonify(success=True, item=row.to_dict()), 201

    # ── Artwork uploads and thumbnails ─────────────────────────────────────
    @app.post("/upload/image")
    def upload_image():
        upload = request.files.get("file")
        if upload is None or not upload.filename:
            return jsonify(error="Choose an image first."), 400
        extension = Path(secure_filename(upload.filename)).suffix.lower()
        if extension not in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif"}:
            return jsonify(error="Use a JPG, PNG, GIF, WebP, or AVIF image."), 400
        raw = upload.stream.read(8 * 1024 * 1024 + 1)
        if len(raw) > 8 * 1024 * 1024:
            return jsonify(error="Images must be 8 MB or smaller."), 413
        upload_dir = os.path.join(app.instance_path, "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        filename = f"{secrets.token_hex(12)}{extension}"
        with open(os.path.join(upload_dir, filename), "wb") as destination:
            destination.write(raw)
        return jsonify(url=url_for("uploaded_image", filename=filename))

    @app.get("/uploads/<path:filename>")
    def uploaded_image(filename: str):
        return send_from_directory(os.path.join(app.instance_path, "uploads"), filename, conditional=True, max_age=3600)

    @app.get("/thumbnails/<path:filename>")
    def thumbnail(filename: str):
        return send_from_directory(os.path.join(app.instance_path, "thumbnails"), filename, conditional=True, max_age=86400)

    @app.get("/hotkeys.ahk")
    def download_hotkeys():
        helper = os.path.join(os.path.dirname(__file__), "hotkeys.ahk")
        if not os.path.isfile(helper):
            abort(404)
        return send_file(helper, as_attachment=True, download_name="localacademy-hotkeys.ahk")

    # ── Optional desktop hotkey bridge (AutoHotkey can call this locally) ───
    @app.post("/api/hotkey/<action>")
    def push_hotkey(action: str):
        if action not in _HOTKEY_ACTIONS:
            return jsonify(error="Unknown hotkey action."), 404
        with _hotkey_lock:
            _hotkey_queue.append(action)
        return jsonify(success=True)

    @app.get("/api/hotkey/poll")
    def poll_hotkeys():
        with _hotkey_lock:
            actions = list(_hotkey_queue)
            _hotkey_queue.clear()
        return jsonify(actions=actions)

    @app.get("/health")
    def health():
        return jsonify(status="ok", version="0.2-alpha")

    if app.config.get("ENABLE_DRIVE_MONITOR") and not app.testing:
        _start_drive_monitor(app)
    return app


if __name__ == "__main__":
    application = create_app()
    application.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
