# LocalAcademy

LocalAcademy is a private, self-hosted learning workspace for course material that already lives on your computer. Add a course folder, browse its lessons, resume where you left off, read or watch in a focused player, and keep notes and bookmarks alongside your files.

LocalAcademy is built with Flask, Jinja, SQLAlchemy, and vanilla JavaScript. There is no frontend framework or build step.

> This repository currently contains the redesigned `v0.2-alpha` application. The older `v01-alpha` application is intentionally left unchanged.

## Features

- **Local course library** — index folders and nested sections without copying the original files.
- **Resume-first dashboard** — continue an unfinished lesson, see course progress, and revisit recent notes.
- **Multiple lesson types** — video, audio, PDF, EPUB, text, Markdown, HTML, images, documents, archives, code, and downloadable resources.
- **Focused lesson player** — playback speed, seeking, volume, theater mode, fullscreen, auto-advance, and keyboard shortcuts.
- **Transcripts and captions** — discover SRT/VTT/ASS/SSA/SUB sidecars or attach caption files from the player.
- **Notes and bookmarks** — save general notes, timestamped notes, lesson bookmarks, and shareable timestamp links.
- **Silence skip** — optionally accelerate confirmed quiet sections of audio or video without modifying the source file.
- **Course organization** — descriptions, cover artwork, instructors, categories, tags, collections, and per-course player settings.
- **Five themes** — Campus, Ocean, Parchment, Mulberry, and Midnight, with browser persistence and device appearance support.
- **Responsive and accessible UI** — keyboard navigation, focus-managed dialogs, readable mobile layouts, and local assets.
- **Privacy-minded HTML lessons** — HTML lessons are opened inside a restrictive sandboxed frame.

## Requirements

- Python 3.10 or newer
- A modern web browser
- Optional: Node.js for JavaScript syntax checks
- Optional: FFmpeg or FFprobe for richer media metadata and demo video generation

## Quick start

From the repository root:

```bash
cd v0.2-alpha
python -m venv .venv
```

Activate the environment:

```bash
# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Install the runtime dependencies and start the app:

```bash
pip install -r requirements.txt
python app.py
```

Open [http://localhost:5000](http://localhost:5000) in your browser. Select **Add a course** and provide a folder path on the computer running the Flask server.

The default SQLite database is created at:

```text
v0.2-alpha/instance/localacademy-v02.db
```

LocalAcademy binds to `0.0.0.0` by default, which allows access from another device on a trusted local network. The application is intended for a trusted private environment; do not expose it directly to the public internet.

## Configuration

The application generates a temporary secret key when `SECRET_KEY` is not set. For a persistent deployment, set a private value before starting the server:

```bash
# macOS / Linux
export SECRET_KEY="use-a-private-random-value"
python app.py
```

To use a different SQLite database, set `DATABASE_URL` to an absolute SQLite URL:

```bash
export DATABASE_URL="sqlite:////absolute/path/to/academy.db"
python app.py
```

The root path of every course is evaluated by the machine running LocalAcademy. If a course is stored on a removable drive, reconnect the drive before opening its lessons.

## Demo mode

The isolated demo creates a clearly labeled sample library without touching the normal database:

```bash
pip install -r requirements-dev.txt
python demo.py --port 5000
```

The demo contains six illustrative courses, sample instructors, notes, progress, readings, interactive lessons, and optional silent study-slide videos. Its data is stored separately in:

```text
v0.2-alpha/instance/demo/sample-library.db
v0.2-alpha/instance/demo/courses/
```

The demo automatically uses a configured `FFMPEG_BIN`, a system FFmpeg executable, or the optional `imageio-ffmpeg` binary when available. Pillow is used to render the sample slides. If media dependencies are unavailable, the demo still works with readings and interactive lessons.

To regenerate the sample database, stop the demo server and remove **only** `instance/demo/sample-library.db`. Do not remove `instance/localacademy-v02.db` unless you intend to remove your normal library.

## Themes

Themes can be changed from the palette menu in the header or from **Preferences → Appearance**.

| Theme | Description |
| --- | --- |
| **Campus** | Sage green, ivory surfaces, and a quiet academic tone. Default. |
| **Ocean** | Cool blue surfaces with a coastal feel. |
| **Parchment** | Warm paper tones with restrained ochre accents. |
| **Mulberry** | Soft plum and rose-tinted surfaces. |
| **Midnight** | Deep slate with sage accents for dark environments. |

Theme changes apply immediately and are saved in the current browser. They are separate from server-side player preferences. **Follow device appearance** switches between Campus for light mode and Midnight for dark mode.

See [DESIGN.md](DESIGN.md) for the visual system, responsive layouts, interaction conventions, accessibility decisions, and maintenance guidance.

## Supported file types

| Category | Examples |
| --- | --- |
| Video | MP4, M4V, MOV, WebM, MKV, AVI, WMV, FLV, OGV |
| Audio | MP3, WAV, FLAC, AAC, M4A, OGG/OGA, Opus, WMA, AIFF, ALAC |
| Reading | PDF, EPUB, TXT, Markdown, RST, LOG |
| Interactive | HTML, HTM |
| Images | JPG/JPEG, PNG, GIF, BMP, WebP, AVIF |
| Captions | SRT, VTT, ASS, SSA, SUB |
| Downloadable resources | Office formats, CSV/JSON/XML, archives, source files, and other files |

Browser playback depends on the codecs supported by the browser. FFmpeg and FFprobe are optional. They improve duration, quality, poster-image, and demo-video support but are not required for the core library.

## Keyboard shortcuts

Keyboard shortcuts are available in the lesson player:

| Shortcut | Action |
| --- | --- |
| `Space` | Play or pause |
| `Left` / `Right` | Seek backward or forward five seconds |
| `Shift + Left` / `Shift + Right` | Previous or next lesson |
| `Up` / `Down` | Adjust volume |
| `T` | Toggle theater mode |
| `F` | Toggle fullscreen |
| `C` | Toggle captions |
| `N` | Add a note |
| `B` | Save a bookmark |
| `Ctrl + K` / `Cmd + K` | Search the library |

On Windows, `hotkeys.ahk` provides optional system-wide numpad controls through AutoHotkey v2. Use it only on a trusted local network.

## Development and testing

Install the development dependencies:

```bash
cd v0.2-alpha
source .venv/bin/activate
pip install -r requirements-dev.txt
```

Run the Python test suite:

```bash
python -m unittest discover -s tests -v
```

Check all browser JavaScript files with Node.js:

```bash
for file in static/js/*.js; do node --check "$file"; done
```

### Browser smoke tests

The browser suite is designed to run against the isolated demo, not a real personal library. It verifies navigation, search, filtering, themes, settings, course content search, import, progress, notes, bookmarks, captions, playback controls, responsive layouts, and keyboard interactions.

Start the demo in one terminal:

```bash
python demo.py --port 5000
```

Install a Playwright browser if needed:

```bash
python -m playwright install chromium
```

Run the browser checks in another terminal:

```bash
python tests/browser_smoke.py
```

For an existing Chromium executable:

```bash
python tests/browser_smoke.py \
  --browser-executable /absolute/path/to/chromium
```

For local axe-core accessibility checks, provide a local `axe.min.js` file:

```bash
python tests/browser_smoke.py \
  --axe-file /absolute/path/to/axe.min.js
```

Screenshots and JSON reports are written to the ignored `.cache/qa/` directory.

## Project structure

```text
v0.2-alpha/
├── app.py                    Flask application factory, routes, and APIs
├── models.py                 SQLAlchemy models and learning preferences
├── library.py                Folder scanner, media helpers, captions, EPUB reader
├── demo.py                   Isolated illustrative preview
├── templates/                Jinja pages and reusable UI fragments
├── static/css/themes.css     Semantic theme tokens
├── static/css/app.css        Responsive component styles
├── static/js/theme.js        Pre-paint theme selection and synchronization
├── static/js/app.js          Navigation, dialogs, search, and course import
├── static/js/player.js       Player, transcripts, notes, progress, silence skip
├── static/js/course.js       Course editing and lesson interactions
├── static/js/settings.js     Global and per-course preferences
├── tests/                    Python and browser regression tests
├── DESIGN.md                 Design system and interaction documentation
└── requirements*.txt         Runtime and development dependencies
```

## Privacy and safety notes

- Course files remain in their original folders; LocalAcademy indexes them in its local database.
- Progress, notes, bookmarks, and player preferences are stored locally.
- Appearance preferences are stored in the browser.
- HTML lessons run inside a sandboxed iframe, but only add course folders you trust.
- LocalAcademy does not provide accounts or authentication. Keep the server on a trusted network.
- Back up the database before changing database paths or testing a different application version.

## License

No license file is currently included in this repository. Add a project license before distributing LocalAcademy outside your private environment.
