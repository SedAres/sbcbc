# LocalAcademy 0.2 — Options & Customizability Reference

Everything a new owner can change, in one place: every in-app setting, every per-course
override, every keyboard shortcut, every environment variable, every cap and guardrail,
and the documented extension points for changing the app itself.

`README.md` explains what LocalAcademy is and how to run it. This file explains **how to
make it yours**.

---

# Part 1 — The pitch

*A talk for the developers' department. Roughly eight minutes spoken.*

---

Every team I have worked with has the same room.

It is not a room exactly. It is a network share, or a folder called `Courses`, or a USB
drive somebody labelled `Backup2 (real)`. Inside it: forty-two hours of conference
videos, a dozen PDFs somebody paid for, a folder of tutorials that a colleague recorded
before they left, and three EPUBs you keep meaning to get to. It is genuinely good
material. Nobody finishes it. Not because anyone is lazy — because the entry cost is
absurd. You have to remember which drive is mounted, which file was the one that finally
explained indexes, and what minute you were on when your last meeting started.

So people don't. They open a tab, they search YouTube, they watch something forty
minutes long that turns out to be a sales demo, and they learn less. The good material
rots quietly on a disk.

LocalAcademy is the smallest possible fix for that, and I want to be precise about how
small, because precision is the pitch.

It is a Flask app. It has no frontend framework and no build step. It does not copy your
files, re-encode your files, upload your files, or ask you to trust anybody's cloud. It
reads a folder you point it at, writes an index into a single SQLite file, and gives you
a learning player that remembers the exact second you stopped. That is the whole trick.
Everything else in this repository is craft applied to that trick.

Here is why I think a department of engineers should care, in the order you will
actually care about it.

**One: you can read all of it.** The runtime is about 2,300 lines of Python across four
files, 2,500 lines of JavaScript and CSS, and 620 lines of Jinja templates. There is no
`node_modules`. There is no transpiler between the source you read and the bytes that
run. If you have an afternoon and a reason, you can hold this entire application in your
head. That property is worth more than any feature list I could read to you, because it
means the answer to "can we make it do X" is not a vendor conversation. It is a pull
request.

**Two: deployment is three commands.** `python -m venv .venv`, `pip install -r
requirements.txt`, `python app.py`. Two dependencies: Flask and Flask-SQLAlchemy. It
binds `0.0.0.0:5000` so a colleague or a tablet on your LAN can reach it. It generates a
temporary secret key on boot if you don't give it one, so it runs before you have
configured anything, and takes a real `SECRET_KEY` when you are ready to be serious. Your
data is a file. Back it up with `cp`. Move it with `mv`. Diff it with a tool you already
have. No migrations service, no connection pool to tune, no cluster to babysit.

**Three: your files never move, so trying it is free.** This is the part that makes it
adoptable in an organization. `Add a course` asks for a name and a folder path on the
server's machine. It indexes. It does not ingest. Remove the course later and the dialog
tells you plainly that the original files will not be deleted — and the code matches the
sentence. The row and its learning data go; your folder is untouched, byte for byte. You
can evaluate this thing with real production content and not worry that production
content will come back rearranged.

**Four: it plays everything you actually have.** Video, audio, PDF, EPUB, Markdown,
plain text, HTML, images, Office documents, archives, source files. We are not going to
tell you that AVI or WMV plays beautifully in a browser, because that is not how codecs
work; we are going to tell you that the file still shows up as a downloadable resource
instead of vanishing from the course. Unrecognized files are kept, not silently dropped.
FFmpeg and FFprobe are optional upgrades — duration, quality labels, poster frames —
never requirements. The app does not fail because your demo machine is missing a binary.
That is a design decision, and it is the right one for a tool that has to survive contact
with a corporate laptop.

**Five: the details are engineered, not decorated.** Some examples, because this is where
I would want proof.

Silence skip does not guess. The player taps the Web Audio API, computes loudness in
dBFS over a rolling window, waits for quiet to persist past a minimum duration, and only
then accelerates — at a rate you choose, up to sixteen times — snapping back to normal
speed the instant speech or music returns. No re-encoding, no silence file, no mutation
of the source. If that behavior is wrong for one course, you override the threshold,
duration, and rate for that course alone and leave the other forty courses alone.

Captions are political in most organizations: SRT here, ASS there, a colleague's VTT.
LocalAcademy discovers SRT, VTT, ASS, SSA, and SUB sidecars, parses them server-side,
converts cues to safe WebVTT, strips out markup that could carry a script, and serves
`text/vtt` with `nosniff`. You can also attach a caption file from the player and it
lands in the database, not the folder. Every cue is also readable as a transcript panel
beside the lesson, so a viewer without audio still gets the words.

HTML lessons are the dangerous lesson type. Any HTML file a colleague downloaded is a
potential script at your origin. So HTML lessons never render at the app origin. They
are served through a dedicated route inside a restrictive sandboxed frame. That is the
kind of decision that tells you the author was thinking about threat models and not
about screenshots.

And when something does not exist — a missing page, an unplugged drive, an empty search —
the app explains what happened and offers a way back. A 404 with a recovery path. That
sounds small. It is the difference between a tool people keep using and a tool people
quietly stop opening.

**Six: the extension surface is documented and shallow.** This is the part I would want
as an engineer, so I have written the whole of it into Part 2 of this document.

Adding a sixth theme is a four-file change, and those four files are named for you:
palette tokens in `themes.css`, the `UI_THEMES` list in `app.py`, the pre-paint registry
in `theme.js`, and the browser test that asserts all palettes exist. Because the CSS
consumes semantic tokens — `--surface`, `--primary`, `--danger`, `--line` — a palette is
data, not a refactor. No selector hunting.

Adding a file type is an edit to one set in `library.py` and a line in `get_file_type()`.
If you want `.srt`-style handling for a format from your own toolchain, the parser
registry is a function, not a plugin API you have to reverse-engineer.

Adding a setting means adding a key to `DEFAULT_SETTINGS` and a type to `SETTING_TYPES`.
It gets persistence, type coercion, validation, and a default automatically. Add the same
key to `COURSE_SETTING_TYPES` and it becomes per-course overridable with a NULL meaning
"inherit the global value" — a pattern that is already carrying seven settings and is the
reason a single noisy course does not force a global preference change on you.

Adding a global hotkey action means one entry in `_HOTKEY_ACTIONS` and one line in the
player's action map. The Windows helper script reads its numpad mapping from your saved
preferences at launch, so remapping is a dropdown in the settings page, not a code edit.

**Seven: it takes accessibility and responsive design seriously without being asked.**
Dialogs trap focus, restore it on close, mark the background inert, and focus **Cancel**
on destructive confirmations. Tabs use real ARIA relationships and arrow-key navigation.
Icon-only controls carry accessible names. Small text stays readable on tinted surfaces.
Reduced-motion preferences turn off decorative animation. The layout recomposes at
laptop, tablet, and phone widths, with a focus-managed drawer on small screens. There is
a browser suite that runs Playwright over the demo, captures desktop and mobile routes
and all five palettes, and can add axe-core checks from a local file. We are not claiming
it is certified. We are claiming it was tested on purpose.

**Eight: you can demo it without risking anyone's library.** `python demo.py` builds a
clearly labelled sample library — six courses, instructors, notes, progress, readings, an
interactive quiz — in its own database and its own folder, and tells you so on screen
while it runs. Show it to your manager in one command. Delete one file to regenerate it.
Candidate evaluation and stakeholder demos both stop being scary.

Now the honest part, because you would find it in five minutes anyway and I would rather
be the one to say it.

LocalAcademy has no authentication and no user accounts. It is a trusted-network
application. Put it behind your VPN, on a private subnet, or on `localhost`, and do not
port-forward it to the internet. It has no mobile app — it is responsive web, which is
the tradeoff that lets one codebase serve a laptop, a tablet, and a phone. It has no
license file yet, so do not redistribute it outside your organization until your legal
review has something to review. These are the real limits. Everything else on this list
is a knob.

So here is what I am actually asking for. Not a migration, not a budget line, not a
quarter of your team's time. Pick one folder. The one with the training videos nobody
watches. Run three commands. Point LocalAcademy at it, and let two engineers use it for a
week. If it does not earn its place in their week, you have spent ten minutes and one
virtual environment. If it does, you have an internal learning platform with an index
file you control, an extension surface you can extend, and a codebase your team can
actually read.

The material is already on your disk. It deserves a front door.

---

# Part 2 — Every option and customization point

## 2.1 Where options live

| Surface | Changed from | Applies to | Persisted in |
| --- | --- | --- | --- |
| Appearance / theme | Header palette menu, or Preferences → Appearance | The current browser | `localStorage` key `la-theme` |
| Global player preferences | Preferences page (`/settings`) | Every course on this server | `settings` table |
| Per-course overrides | Course → Player settings (`/settings/course/<id>`) | One course | `course_settings` table |
| In-player controls | Lesson player toolbar | The open lesson | Playback position, captions, and completion go to the database; volume and theater toggling are session-only |
| Library browsing | Course library toolbar | The current view | URL query parameters |
| Course metadata & artwork | Add-course dialog, course page, course settings | One course | `courses`, `creators`, `categories`, `tags` tables |
| Lesson names | Rename on the course page | One lesson | `course_files.display_name` |
| Captions | Player caption panel | One lesson | Sidecar files, or the `subtitle_tracks` table |
| Timestamp links | Preferences → Timestamp links | Every copied timestamp | `settings.timestamp_template` |
| Global desktop hotkeys | Preferences → Keyboard shortcuts | The Windows helper | `settings.hotkeys` |
| Server & deployment | Environment variables | The whole process | Nothing (process environment) |
| Application constants (`Config`) | Code, `app.py` | The whole process | Code |
| File-type coverage | Code, `library.py` | Scanning and rendering | Code |
| Themes | Code, four files | The whole UI | Code + `localStorage` |
| Demo / QA behavior | Command-line flags | That run only | Nothing |

**Grouping that matters:** appearance is browser-local and instant. Player preferences are
server-side and explicitly saved. A theme you choose on your laptop does not change a
colleague's screen; a playback speed you save does change every course you open on every
device.

---

## 2.2 Server & deployment options

### Environment variables

| Variable | Default | What it does |
| --- | --- | --- |
| `SECRET_KEY` | Random 32-byte hex generated at boot | Flask session secret. Generated values change on every restart, so set a private value for a persistent deployment. |
| `DATABASE_URL` | `sqlite:///<instance>/localacademy-v02.db` | Full SQLAlchemy URI. Any SQLAlchemy-supported backend works; SQLite gets `check_same_thread=False` automatically. |
| `PORT` | `5000` | TCP port for the built-in server. |
| `FFMPEG_BIN` | Unset | Explicit path to an FFmpeg executable used by `demo.py` for sample video generation. |

```bash
export SECRET_KEY="a-private-random-value"
export DATABASE_URL="sqlite:////srv/academy/academy.db"
export PORT=8080
python app.py
```

### Application constants (`Config` in `app.py`)

| Constant | Default | Notes |
| --- | --- | --- |
| `MAX_CONTENT_LENGTH` | `64 MB` | Ceiling for any single request body. Override with `app.config` if you need larger uploads. |
| `ENABLE_DRIVE_MONITOR` | `True` | Background thread that re-checks whether each course folder still exists and flips `is_available`. |
| `DRIVE_MONITOR_INTERVAL` | `30` seconds | Sleep between availability sweeps. Clamped to a 10-second minimum. |
| `SQLALCHEMY_TRACK_MODIFICATIONS` | `False` | Standard SQLAlchemy noise suppression. |

### Endpoints worth knowing

| Route | Purpose |
| --- | --- |
| `/health` | Returns `{"status":"ok","version":"0.2-alpha"}`. Use it as a container or uptime probe. |
| `/hotkeys.ahk` | Downloads the optional AutoHotkey helper script. |
| `/api/hotkey/<action>` | Accepts a hotkey action from a trusted local caller. |
| `/api/hotkey/poll` | Drains the queued actions for the focused browser tab. |
| `/settings/hotkeys` | Returns the saved hotkey map as JSON, which is how the helper script configures itself. |

### Hosting shape

The built-in server binds `0.0.0.0`, so a phone or tablet on the same LAN can reach it.
**There is no authentication and no user accounts.** Bind it to a trusted network,
front it with your own reverse proxy and auth if you need one, and do not expose it
directly to the public internet. Set `ENABLE_DRIVE_MONITOR = False` in `Config` if you do
not want a background thread touching the database.

---

## 2.3 Appearance options

Five palettes ship in `static/css/themes.css`:

| Theme | Character | Mode |
| --- | --- | --- |
| **Campus** | Sage green, ivory surfaces, quiet academic tone | Light (default) |
| **Ocean** | Cool blue surfaces, coastal | Light |
| **Parchment** | Warm paper, restrained ochre accents | Light |
| **Mulberry** | Soft plum and rose-tinted surfaces | Light |
| **Midnight** | Deep slate with sage accents | Dark |

| Option | Where | Behavior |
| --- | --- | --- |
| Pick a palette | Header palette menu, or Preferences → Appearance | Applies immediately, no reload |
| **Follow device appearance** | Checkbox in Appearance | Switches between Campus (light) and Midnight (dark) to match `prefers-color-scheme` |
| Cross-tab sync | Automatic | Changing the theme updates other open tabs through the `storage` event |
| Persistence | Automatic | Stored in `localStorage` under `la-theme`; storage failures fall back to Campus rather than breaking the page |
| Legacy values | Automatic | Old `light` / `dark` values are aliased to `campus` / `midnight` |

Two deliberate design constraints: preview thumbnails reuse the live palette tokens, so a
preview cannot drift from reality; and course cover colors keep their book identity
across palettes while the surrounding chrome follows your theme. Video controls stay dark
on purpose, because they sit over arbitrary media.

### Add a sixth theme

A four-file change, in this order:

1. `static/css/themes.css` — add `html[data-theme="yourtheme"]` and
   `.theme-preview[data-preview-theme="yourtheme"]` blocks defining the full semantic set
   (`--page`, `--sidebar`, `--surface`, `--surface-raised`, `--surface-soft`,
   `--surface-hover`, `--line`, `--line-strong`, `--input-line`, `--text`, `--text-soft`,
   `--muted`, `--faint`, `--primary`, `--primary-ink`, `--primary-hover`, `--accent-soft`,
   `--feature`, `--feature-ink`, `--feature-muted`, `--success`, `--warning`, `--danger`
   plus their soft variants, `--shadow`, `--scrim`, `--media-ground`).
2. `app.py` — add an entry to `UI_THEMES` with `id`, `name`, and `description`.
3. `static/js/theme.js` — add the theme to the `themes` registry with its `name`, `color`
   (browser chrome color), and `mode` (`light` or `dark`).
4. `tests/test_ui.py` — extend the theme coverage test so the new palette is asserted
   everywhere the others are.

If your palette is not light or dark in the usual sense, note that `--media-ground` sets
the surface behind media and `--scrim` controls dialog dimming.

---

## 2.4 Global player preferences

Open **Preferences** (`/settings`). Saved with the **Save preferences** button, or reset
with **Reset preferences**. Resetting clears the settings table and re-seeds every
default, so it also returns your timestamp template and hotkey map to their defaults —
but it leaves courses, progress, notes, bookmarks, uploaded artwork, and appearance
preferences untouched.

### Playback behavior

| Option | Default | Allowed values |
| --- | --- | --- |
| Default playback speed | `1×` | `0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.5, 3, 4` — server accepts `0.25–4.0` from API callers |
| Subtitles & transcript | On | Show the first available caption track when a lesson opens |
| Auto-advance lessons | On | Move to the next lesson when the current one ends |
| Open in theater mode | Off | Start the player with workspace chrome removed |
| Reading direction | LTR | LTR or RTL for course reading panels |

### Silence skip

| Option | Default | UI range | Server bounds |
| --- | --- | --- | --- |
| Skip quiet sections | Off | On / Off | boolean |
| Silence threshold | `-42 dB` | `-70 … -20 dB`, step 1 | `-80 … 0` |
| Minimum quiet duration | `0.65 s` | `0.2 … 2 s`, step 0.05 | `0.1 … 5.0` |
| Quiet playback speed | `8×` | `2, 3, 5, 8, 10, 12, 16` | `2.0 … 16.0` |

The player measures actual waveform loudness (RMS in dBFS) rather than trusting silence
metadata, requires the quiet stretch to persist past the minimum duration, then
accelerates; normal speed returns as soon as sound resumes. Source files are never
modified.

### Timestamp links

| Option | Default |
| --- | --- |
| Link format (`timestamp_template`) | `[{HH}:{MM}:{SS}]({url})` |

Placeholders: `{HH}`, `{MM}`, `{SS}` for the time; `{url}` for an absolute, shareable
lesson link (`/player/<hash>?t=<seconds>`); `{timestamp}` for raw seconds. Maximum 300
characters. Whatever you write is what gets copied to your clipboard from the player.

### Keyboard shortcuts

In-player shortcuts are fixed. The optional **system-wide** numpad controls are fully
remappable:

| Action | Default numpad key |
| --- | --- |
| Play / pause | `5` |
| Back 5 seconds | `4` |
| Forward 5 seconds | `6` |
| Previous lesson | `1` |
| Next lesson | `3` |
| Volume up | `8` |
| Volume down | `2` |
| Speed up | `9` |
| Slow down | `7` |
| Toggle captions | `0` |

Any action can be set to **None**, any of the ten numpad keys can be assigned to any
action, and multiple actions may share the same key. On Windows, download the helper
script from the settings page, run it with AutoHotkey v2, and it reads your saved map at
launch. It talks to `127.0.0.1:5000`; use it only on a trusted network.

---

## 2.5 In-player controls

**Toolbar:** play/pause, seek back, seek forward, mute, volume slider, playback speed,
silence-skip toggle (with a live status readout), captions toggle, theater mode,
fullscreen, mark complete, add note, add bookmark, copy timestamp link.

**Player keyboard shortcuts:**

| Shortcut | Action |
| --- | --- |
| `Space` | Play / pause |
| `←` / `→` | Seek 5 seconds |
| `Shift + ←` / `Shift + →` | Previous / next lesson |
| `↑` / `↓` | Volume `±0.05` |
| `T` | Theater mode |
| `F` | Fullscreen |
| `Escape` | Exit theater mode, if it is active |
| `C` | Captions |
| `N` | Add a note |
| `B` | Save a bookmark |
| `Ctrl / ⌘ + K` | Search the library |

**Playback speed** is adjustable live in `0.25` steps between `0.25×` and `4×` — from the
toolbar, the number keys above, or the `speed_up` / `speed_down` global hotkeys.

**Reading options** depend on the lesson type, because the app only offers controls that
make sense:

| Lesson type | Available tools |
| --- | --- |
| Video / audio | Transcript, lessons, notes, saved bookmarks, captions, timestamps, silence skip |
| PDF | Embedded browser PDF viewer with its toolbar enabled, lessons, notes, bookmarks |
| EPUB | Chapter navigation, font size cycling `16 → 18 → 20 → 22 → 24 → 16 px`, lessons, notes, bookmarks |
| Text / Markdown | Reader with the lesson's text, lessons, notes, bookmarks |
| HTML | Restrictive sandboxed frame (`allow-scripts allow-forms`, no same-origin access), lessons, notes, bookmarks |
| Images | Zoom toggle, lessons, notes, bookmarks |
| Downloads / unknown | Download the original file, lessons, notes, bookmarks |

**Notes** can be general or timestamped, and are editable and deletable. **Bookmarks**
store a position and an optional label; saved notes and bookmarks reveal their panel
automatically, and dashboard note links open the Notes panel directly.

---

## 2.6 Per-course overrides

Reach these from **Course → Player settings**. Every control offers **Use global
default**, and a value of `NULL` in the database genuinely means "inherit". Clearing every
override deletes the row rather than storing a table of nulls.

| Overridable setting | Inherited from |
| --- | --- |
| Playback speed | Global default speed |
| Silence skip on/off | Global silence-skip switch |
| Silence threshold | Global threshold |
| Minimum quiet duration | Global duration |
| Quiet playback speed | Global quiet rate |
| Subtitles & transcript | Global captions switch |
| Reading direction | Global reading direction |

**Reset course overrides** returns one course to the global defaults.

Deliberately *not* overridable per course, because inheriting is the sensible behavior:
auto-advance, open-in-theater-mode, and the timestamp template.

**Why this matters:** one lecture with a quiet recording booth does not force you to
loosen the silence threshold for your entire library. Override that course, leave the
rest alone.

---

## 2.7 Library browsing options

The course library (`/courses`) accepts these URL parameters, all of which survive
navigation:

| Parameter | Values | Default |
| --- | --- | --- |
| `view` | `grid`, `list` | `grid` |
| `filter` | `all`, `available`, `unavailable`, `progress` | `all` |
| `sort` | `name`, `recent`, `accessed` | `name` |
| `q` | free text, max 120 characters | empty |
| `add` | `1` opens the add-course dialog directly | – |

Invalid values fall back safely rather than erroring. Sorting is performed server-side;
text filtering is immediate and local. `progress` filters to courses with an unfinished
lesson that has been started.

**Search** matches course names, descriptions, **instructors, categories, and tags** —
not just titles. Global search (`Ctrl / ⌘ + K`) is debounced, cancels stale requests,
announces result counts, supports keyboard result selection, returns up to 8 courses and
12 lessons, and falls back to library search if the request fails.

**Course content search** searches a single course's index in place, auto-opens matching
folders, announces the match count, and explains how to recover from an empty result.

**Collections:** every course can carry instructors, categories, and tags. Browse them at
`/collections` and open any one at `/collections/<kind>/<item_id>` where `kind` is
`creators`, `categories`, or `tags`. New entries are created by name from the Collections
page, or through `POST /api/taxonomy/<kind>`; duplicate names are rejected with `409`.
Instructors, categories, and tags each also carry `icon`, `banner`, and `theme` fields on
the model, so artwork can be attached through the API even though v0.2 has no upload
control for them in the interface. The sidebar surfaces your first four categories, in
alphabetical order, as quick subjects.

**Browsing defaults worth knowing:** the dashboard shows four in-progress lessons and
eight recent courses, and the player loads up to 400 recent notes and 400 bookmarks per
course.

---

## 2.8 Course import & metadata

**Add a course** asks for two things first — a display name and the folder path on the
**server's machine** — and hides everything else behind optional details.

| Field | Limit / notes |
| --- | --- |
| Display name | Required, max 255 characters |
| Folder path | Required, unique, max 1024 characters; must exist on the server |
| Description | Max 20,000 characters |
| Instructors | Comma-separated, free text, created on demand |
| Categories | Comma-separated, free text, created on demand |
| Tags | Comma-separated, free text, created on demand |

After import you can also set a **description**, replace the **cover image**, and
**rename individual lessons**. Lesson names fall back to the file name when no display
name is set. On Windows the drive letter of the root path is recorded so an offline
removable drive can be reported accurately.

Removing a course deletes its progress, notes, and bookmarks from the database and
**never touches the original files** — the confirmation dialog says so explicitly.

---

## 2.9 Artwork uploads

| Item | Rule |
| --- | --- |
| Accepted formats | JPG, JPEG, PNG, GIF, WebP, AVIF |
| Maximum size | 8 MB |
| Stored as | Random 12-byte hex name plus the original extension, in `instance/uploads/` |
| Served from | `/uploads/<filename>` with a 1-hour cache |
| Generated thumbnails | `/thumbnails/<filename>` with a 24-hour cache |

Artwork is used for course covers, and taxonomy entities accept an icon and a banner.
Courses without artwork get a flat, colored book cover as an intentional fallback rather
than an empty box.

---

## 2.10 Supported files & what happens to each

| Category | Extensions | How it opens |
| --- | --- | --- |
| Video | `mp4 m4v mov webm mkv avi wmv flv ogv` | Media player |
| Audio | `mp3 wav flac aac m4a ogg oga opus wma aiff aif alac` | Media player |
| Reading | `pdf epub txt md markdown rst log` | PDF viewer, EPUB reader, or text reader |
| Interactive | `html htm` | Restrictive sandboxed frame |
| Images | `jpg jpeg png gif bmp webp avif` | Zoomable image view |
| Captions | `srt vtt ass ssa sub` | Converted to WebVTT and used as a caption track or transcript |
| Downloads | Office, `csv json xml`, archives, `py js css ipynb psd ai sketch` | Download the original file |
| Anything else | any other extension | Kept as a downloadable resource — files are never silently dropped |

**Scanner behavior you can rely on:**

- Lessons sort naturally, so `lesson2` precedes `lesson10`.
- **Any file or folder whose name starts with a dot is skipped** — this covers
  `.DS_Store` and `.git`, and it also means a lesson in a hidden folder, or a lesson
  named `.example.mp4`, will not be indexed. Rename it if you want it to appear.
- The system files `Thumbs.db`, `desktop.ini`, and `ehthumbs.db` are skipped, and the
  scanner does not descend into `.svn`, `__pycache__`, `.venv`, `node_modules`, or
  `$RECYCLE.BIN`.
- Unfamiliar files are indexed rather than discarded.
- Rescanning a course is a single button and picks up changes on disk.

**Optional media intelligence:** if `ffprobe` is on `PATH`, the app records real
durations and video quality; if `ffmpeg` is on `PATH`, it can generate small local poster
images. Neither is required. Without them, durations arrive from the browser on first
playback and the app still works end to end.

### Adjust file-type coverage

In `library.py`:

- Add an extension to the relevant set — `VIDEO_EXTENSIONS`, `AUDIO_EXTENSIONS`,
  `PDF_EXTENSIONS`, `EPUB_EXTENSIONS`, `IMAGE_EXTENSIONS`, `HTML_EXTENSIONS`,
  `TEXT_EXTENSIONS`, `SUBTITLE_EXTENSIONS`, or `DOWNLOAD_EXTENSIONS`.
- If the new extension should use a non-default reader, add it to the corresponding
  branch in `get_file_type()`.
- Extend `IGNORED_DIRECTORIES` or `IGNORED_NAMES` if your folders carry vendor cruft.

---

## 2.11 Captions & transcripts

| Option | Details |
| --- | --- |
| Sidecar discovery | SRT, VTT, ASS, SSA, SUB files next to the media are found automatically |
| Upload from the player | SRT, VTT, ASS, SSA, SUB; max **10 MB** |
| Upload metadata | Optional `label` (max 120 characters) and `language` tag (max 16 characters, default `und`) |
| Default label | Derived from the file name when you do not supply one |
| Ordering | Sidecar and attached tracks are both listed; the player uses the first available by default |
| Removal | Attached tracks can be deleted from the player |
| Conversion | All formats are parsed server-side and re-emitted as safe WebVTT |
| Delivery | Served as `text/vtt; charset=utf-8` with `Cache-Control: no-cache` and `X-Content-Type-Options: nosniff` |

Captions are only offered for audio and video lessons. Uploading a caption file to a PDF
returns a clear error rather than failing silently. Attached captions live in the database
(`subtitle_tracks`), so they survive the course folder being reorganized and are covered
by a database backup.

---

## 2.12 Demo mode options

`demo.py` builds and serves a fully labelled sample library in its own database and folder
tree, with six courses, instructors, notes, progress, readings, an interactive quiz, and
optional silent study-slide videos.

| Flag | Default | Purpose |
| --- | --- | --- |
| `--port` | `5000` | Port for the demo server |

| Behavior | Details |
| --- | --- |
| Isolation | `instance/demo/sample-library.db` and `instance/demo/courses/` — your real library is untouched |
| Transparency | Prints that sample courses, people, and progress are illustrative |
| Video generation | Uses `FFMPEG_BIN`, then a system `ffmpeg`, then the optional `imageio-ffmpeg` binary |
| Slide rendering | Uses Pillow |
| Degraded mode | Without media dependencies the demo still runs with readings and interactive lessons |
| Regeneration | Stop the server and delete *only* `instance/demo/sample-library.db` |

---

## 2.13 Testing & QA options

```bash
python -m unittest discover -s tests -v          # Python suite
for file in static/js/*.js; do node --check "$file"; done   # JS syntax
```

| Browser suite flag | Purpose |
| --- | --- |
| `--base-url` | Target server, default `http://127.0.0.1:5000` |
| `--browser-executable` | Use an existing Chromium instead of a Playwright-managed one |
| `--axe-file` | Path to a local `axe.min.js` for WCAG accessibility checks |
| `--screenshots` | Output directory, default `.cache/qa` |
| `--record-issues` | Report findings without failing the run |

Run it against the **demo**, not a personal library. It exercises navigation, search,
filtering, themes, settings, course content search, import, progress, notes, bookmarks,
captions, playback controls, responsive layouts, and keyboard interaction, and captures
desktop and mobile routes plus all five palettes. Screenshots and JSON reports land in the
git-ignored `.cache/qa/`.

---

## 2.14 Data, storage, and privacy options

| Data | Lives in | Portable? |
| --- | --- | --- |
| Course index, progress, notes, bookmarks, captions, preferences | SQLite database (`instance/localacademy-v02.db` by default) | Yes — one file |
| Uploaded artwork | `instance/uploads/` | Yes |
| Generated thumbnails | `instance/thumbnails/` | Yes, regenerable |
| Appearance preference | Browser `localStorage` | Per browser |
| Course content | Your original folders, never copied | Already yours |

Set `DATABASE_URL` to relocate the database — for example onto a backed-up volume — and
back it up before changing database paths or testing a different version. Because course
files stay in place, a database backup is a complete backup of everything LocalAcademy
knows.

---

## 2.15 Guardrails at a glance

| Limit | Value |
| --- | --- |
| Any request body | 64 MB |
| Caption upload | 10 MB |
| Artwork upload | 8 MB |
| Caption extensions | `srt vtt ass ssa sub` |
| Artwork extensions | `jpg jpeg png gif webp avif` |
| Course display name | 255 characters |
| Course description | 20,000 characters |
| Course root path | 1,024 characters |
| Timestamp template | 300 characters |
| Search query | 120 characters |
| Caption label / language | 120 / 16 characters |
| Playback speed | `0.25 – 4.0×` |
| Silence threshold | `-80 – 0 dB` |
| Minimum quiet duration | `0.1 – 5.0 s` |
| Quiet playback speed | `2.0 – 16.0×` |
| Drive monitor interval | 10 seconds minimum |

Out-of-range values sent to the API are clamped where a clamp is safe and rejected with a
clear error where it is not. Invalid browsing parameters fall back to defaults instead of
erroring.

---

## 2.16 Extension recipes

**Add a setting.**

1. Add the key and default to `DEFAULT_SETTINGS` in `models.py`.
2. Add the key and Python type to `SETTING_TYPES`.
3. Add it to `COURSE_SETTING_TYPES` if it should be overridable per course.
4. Persistence, type coercion, validation, and defaults follow automatically.

**Add a theme.** See §2.3 — four files, `themes.css`, `app.py`, `theme.js`, `tests/test_ui.py`.

**Add a file type.** See §2.10 — one set plus one branch in `library.py`.

**Add a global hotkey action.**

1. Add the action name to `_HOTKEY_ACTIONS` in `app.py`.
2. Handle it in the player's action map in `static/js/player.js`.
3. Add a row to the mapping list in `templates/settings.html` so it appears as a dropdown,
   and to the `actions` array in `hotkeys.ahk`.

**Change the timestamp format.** No code required — edit **Timestamp links** in
Preferences, up to 300 characters.

**Move the database.** Set `DATABASE_URL`. Nothing else changes.

**Turn off background monitoring.** Set `ENABLE_DRIVE_MONITOR = False` in `Config`.

**Verify any change.** Run `python -m unittest discover -s tests -v`, `node --check` on
every browser script you touched, and the browser smoke suite against the demo.

---

## 2.17 Known limits

Stated plainly so nobody discovers them late:

- **No authentication, no user accounts, no per-user libraries.** One shared library, one
  set of preferences, one set of notes. Trusted-network use only.
- **No mobile app.** Responsive web only, by design.
- **No license file in this repository.** Add one before distributing outside your
  private environment.
- **HTML lessons are sandboxed, not guaranteed harmless.** The iframe is restrictive, but
  only add course folders you trust.
- **Browser codec support still governs playback.** An indexed AVI or WMV file may not
  play in the browser; it stays available as a download.
- **Removable drives must be reconnected** before their lessons open. Availability is
  reported, not simulated.

---

## See also

- `README.md` — what LocalAcademy is, installation, supported file types, and deployment
  notes.
- `DESIGN.md` — the visual system, responsive behavior, interaction conventions, and
  guidance for adding a palette without scattering selectors through `app.css`.
