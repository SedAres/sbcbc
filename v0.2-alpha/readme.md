# LocalAcademy 0.2-alpha

A redesigned, self-hosted course library for folders of learning material. Version 0.2 is a clean rewrite of the original Flask application: a calmer black-and-white interface, a proper study workspace, and a more reliable browser-based player.

## Start here

```bash
cd v0.2-alpha
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open [http://localhost:5000](http://localhost:5000), choose **Add a course**, and enter a folder path on the computer running LocalAcademy. The server indexes the folder in place; course files are not copied or uploaded. The app binds to `0.0.0.0` so it can also be used in a local network or a hosted development preview.

The default database is created at `v0.2-alpha/instance/localacademy-v02.db`. Set `SECRET_KEY` and, if desired, `DATABASE_URL` before launching to customize the install:

```bash
# Linux / macOS
export SECRET_KEY="use-a-private-random-value"
export DATABASE_URL="sqlite:////absolute/path/to/academy.db"
python app.py
```

To reuse a compatible LocalAcademy 0.1 database, point `DATABASE_URL` at its absolute SQLite path. The new app keeps the original course, lesson, progress, notes, bookmarks, and preference table names, and creates its new caption-attachment table on startup. Back up the database before trying a different database path.

## Run the regression tests

With the virtual environment active, run:

```bash
python -m unittest discover -s tests -v
```

To check the browser scripts as well (requires Node.js):

```bash
for file in static/js/*.js; do node --check "$file"; done
```

## What it can do

- **Private course library** — scan course folders and nested sections; keep folders available/offline status current; rescan to pick up new, moved, and removed content.
- **Modern learning dashboard** — continue learning, completion progress, recent courses, library search, grid/list views, and filters for in-progress, available, and offline courses.
- **Multiple lesson formats** — video, audio, PDF, images, EPUB books, plain text/Markdown, standalone HTML lessons and interactive tests, common Office documents, archives, source files, and other files. Unsupported browser-native formats stay in the course and can be downloaded from the player.
- **Course organization** — descriptions, cover artwork, instructors, categories, tags, and per-course player overrides.
- **Learning progress** — resume playback, mark any resource complete, auto-advance, and keep progress by lesson.
- **Player tools** — playback speed, seek/volume shortcuts, theater and fullscreen modes, notes, timestamped bookmarks, shareable timestamp links, and an optional Windows global-hotkey helper.
- **Transcript panel** — detect matching caption sidecars next to a lesson (for example `lesson.srt`, `lesson.en.vtt`, or `lesson.en-US.srt`), or attach an SRT/VTT/ASS/SSA/SUB file in the player. Search a transcript, follow the active caption, click a line to seek, and show captions on video/audio.
- **Silence skip** — measure time-domain RMS loudness correctly in dBFS, confirm a quiet stretch for a configurable duration, accelerate and mute only that stretch, then return to the selected playback rate when sound resumes. Audio is analyzed before a separate output gain mutes the quiet interval, so muting never blinds the detector to returning speech. Uses AudioWorklet when available and an analyser fallback otherwise; the analyser is created once per player rather than repeatedly on every toggle.
- **Privacy-minded HTML tests** — local HTML lessons are framed with a restrictive sandbox. Files remain in your course folder.
- **Local preferences** — dark monochrome by default, optional light theme, player defaults, per-course overrides, and keyboard shortcuts.

## Supported file types

| Kind | Examples |
| --- | --- |
| Video | MP4, M4V, MOV, WebM, MKV, AVI, WMV, FLV, OGV |
| Audio | MP3, WAV, FLAC, AAC, M4A, OGG/OGA, Opus, WMA, AIFF, ALAC |
| Reading | PDF, EPUB, TXT, Markdown, RST, LOG |
| Interactive | HTML, HTM |
| Images | JPG/JPEG, PNG, GIF, BMP, WebP, AVIF |
| Caption sidecars | SRT, VTT, ASS, SSA, SUB |
| Downloadable resources | Common Office formats, CSV/JSON/XML, archives, code, and other file types |

Video/audio playback depends on the codecs supported by the user's browser. Optional `ffprobe` and `ffmpeg` binaries add duration, quality, and poster-image discovery; the app still works without them. PDF viewing uses the browser's built-in PDF viewer. EPUB chapters are extracted into a safe text reading view using Python's standard library.

## Keyboard shortcuts

| Shortcut | Action |
| --- | --- |
| Space | Play / pause |
| Left / right arrows | Seek back / forward 5 seconds |
| Shift + left / right arrows | Previous / next lesson |
| Up / down arrows | Volume |
| T | Theater mode |
| F | Fullscreen |
| C | Toggle captions |
| N | Add a note |
| B | Save a bookmark |
| Ctrl / Cmd + K | Search the library |

On Windows, run `hotkeys.ahk` with AutoHotkey v2 for system-wide numpad controls while the browser is unfocused. The helper posts to the local hotkey API; keep it on a trusted local network.

## Project layout

```text
app.py                    Flask app factory, routes, and APIs
models.py                 SQLAlchemy models and learning preferences
library.py                Folder scanner, media helpers, caption parser, EPUB reader
templates/                Jinja views for the dashboard, library, course, and player
static/css/app.css        Responsive monochrome design system
static/js/app.js          Navigation, search, course import, theme toggle
static/js/player.js       Media controls, transcript, notes, progress, silence skip
static/js/settings.js     Global and per-course preferences
static/js/course.js       Course editing and curriculum interactions
```

## Notes

- The root path is evaluated by the machine running the Flask server. If a course is on a removable drive, reconnect it before playback; availability is refreshed in the background.
- The silence feature speeds through confirmed quiet audio; it does not rewrite or permanently edit the media file. Threshold and minimum duration can be tuned in global or per-course settings.
- Only choose course folders you trust. HTML course files run inside a sandboxed iframe, but their own scripts can still run within that isolated frame.
- LocalAcademy is designed for a trusted, personal environment and does not include accounts or authentication. Do not expose the server directly to the public internet.
