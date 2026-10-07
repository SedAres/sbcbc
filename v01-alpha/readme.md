# LocalAcademy

Self-hosted course library manager built with Flask. Manage offline video courses with progress tracking, notes, bookmarks, and a full-featured media player.

## Quick Start

```bash
pip install -r requirements.txt
python app.py
```

Open http://localhost:5000

## Project Structure

```
utils.py   → Config, DB models, file scanning, background services
app.py     → Flask app factory, all routes, entry point
html.py    → All HTML templates (Jinja2 + Alpine.js + Tailwind CSS)
readme.md  → This file
```

## Features

- **Course Management** — Add folders, auto-scan for media, organize by subfolder
- **Media Player** — Video, audio, PDF, image viewer with custom controls
- **Progress Tracking** — Auto-save position, resume playback, completion status
- **Notes & Bookmarks** — Timestamped notes, clickable bookmarks, sort/filter
- **Skip Silence** — Auto-speed-up during silent parts (configurable threshold/speed)
- **Global Hotkeys** — NumPad control (5:play/pause, 4/6:seek, 8/2:volume, 9/7:speed, 1/3:prev/next, 0:subtitles)
- **Per-Course Settings** — Override global playback/silence settings per course
- **Drive Monitoring** — Auto-detect external drive connect/disconnect
- **Search** — Real-time search across courses and files

## Supported Formats

Video: mp4, mkv, avi, mov, wmv, flv, webm, m4v
Audio: mp3, wav, flac, aac, ogg, m4a, wma
Docs: pdf
Images: jpg, jpeg, png, gif, bmp, webp, svg
Subtitles: srt, vtt, ass, ssa, sub

## Keyboard Shortcuts

| Key | Action | Key | Action |
|-----|--------|-----|--------|
| Space | Play/Pause | F | Fullscreen |
| ←/→ | Seek ±5s | T | Theater mode |
| ↑/↓ | Volume | S | Subtitles |

## Configuration

Set environment variables or edit `Config` class in `utils.py`:

```bash
export SECRET_KEY="your-secret-key"
export DATABASE_URL="sqlite:///localacademy.db"
```

## Tech Stack

**Backend:** Flask, SQLAlchemy, SQLite, Watchdog, pynput
**Frontend:** Jinja2, Tailwind CSS, Alpine.js, PDF.js

## Requirements

```
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
watchdog==3.0.0
pynput==1.7.6
```

## License

MIT
