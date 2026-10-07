"""An opt-in, isolated sample library for evaluating LocalAcademy's interface.

Run `python demo.py`. Never points at or changes the normal application database.
All courses, people, notes, and progress in this preview are illustrative.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app import create_app
from library import scan_course_folder
from models import Bookmark, Category, Course, Creator, Note, PlaybackProgress, Tag, db


SAMPLE_COURSES = (
    {
        "name": "Foundations of visual design", "subject": "Design", "instructor": "Maya Chen",
        "description": "Build your eye for composition, contrast, color, and typography. A thoughtful introduction to the decisions behind clear visual communication.",
        "lessons": ("Seeing like a designer", "Understanding visual hierarchy", "Balance and composition", "Working with color", "The rhythm of typography", "Designing with intention"),
        "idea": "Hierarchy gives the reader a starting point. Use scale, contrast, and spacing to make the most important idea visible first.",
        "exercise": "Take a page you use every day. List the three things your eye notices first, then sketch a clearer order for them.",
        "note": "Contrast isn’t only about color. Scale, weight, and space can guide attention just as well.",
        "completed": 3,
    },
    {
        "name": "Python, one idea at a time", "subject": "Development", "instructor": "Leon Okafor",
        "description": "Learn to turn small problems into clear Python programs. Practice with variables, functions, collections, and useful everyday exercises.",
        "lessons": ("A first small program", "Thinking in functions", "Lists and dictionaries", "Reading and writing files", "Working through errors", "A useful little project"),
        "idea": "A function gives a useful task a name. Start with a clear input and output; keep each function responsible for one small idea.",
        "exercise": "Write a function that converts minutes into hours and remaining minutes. Try zero, a value below sixty, and a value above sixty.",
        "note": "Small functions are easier to understand. Give each one a single job and a name that explains it.",
        "completed": 2,
    },
    {
        "name": "The science of learning", "subject": "Learning", "instructor": "Amelia Brooks",
        "description": "Understand attention, memory, and deliberate practice. Make your study sessions more useful without making them more complicated.",
        "lessons": ("How attention works", "Building a memory", "Retrieval practice", "Spacing your study", "Using feedback", "A study rhythm that lasts"),
        "idea": "Retrieval practice means recalling an idea before looking at the answer. It reveals the gaps that rereading can hide.",
        "exercise": "Close your notes and write down three things you learned today. Reopen them, check your recall, and revisit what was missing tomorrow.",
        "note": "Try recalling an idea before rereading it. The effort helps me see what I actually understand.",
        "completed": 1,
    },
    {
        "name": "A practical guide to photography", "subject": "Creative arts", "instructor": "Sara Rahimi",
        "description": "Look closer at light, framing, and the moments worth noticing. Practice making considered photographs with the camera you already have.",
        "lessons": ("Learning to notice light", "A frame with intention", "Exposure in practice", "Working with natural light", "Choosing the right moment", "Editing with restraint"),
        "idea": "Before adjusting a camera, notice where the light comes from. Its direction changes the shape, texture, and mood of your subject.",
        "exercise": "Photograph one object beside a window at three different times of day. Compare the edges of the shadows and the color of the light.",
        "note": "Notice the light before choosing a camera setting.", "completed": 0,
    },
    {
        "name": "Writing with clarity", "subject": "Communication", "instructor": "Tomás Rivera",
        "description": "Write sentences that say what you mean. Find the structure, concrete language, and editing habits that help your reader understand.",
        "lessons": ("Know your reader", "A sentence with a job", "Structure before polish", "Concrete words", "Editing for clarity", "A final careful read"),
        "idea": "Start with the reader’s question. Give each paragraph one main idea, and choose a concrete verb whenever it makes the sentence clearer.",
        "exercise": "Rewrite a long email in half as many words. Keep its main request, the reason for it, and the next step.",
        "note": "Each paragraph should have one idea worth keeping.", "completed": 0,
    },
    {
        "name": "Understanding our natural world", "subject": "Science", "instructor": "Nora Patel",
        "description": "Practice observing the patterns around you. Explore ecosystems, field notes, and how a good question becomes a careful investigation.",
        "lessons": ("Observe before explaining", "Asking a useful question", "Patterns in an ecosystem", "Keeping field notes", "Evidence and uncertainty", "Your own small investigation"),
        "idea": "An observation describes what you can see or measure. An explanation proposes why it happened. Keeping them separate makes an investigation clearer.",
        "exercise": "Observe a nearby tree for five minutes. Write ten observations without explaining them, then turn one observation into a question.",
        "note": "Separate what I observe from how I explain it.", "completed": 0,
    },
)


def make_sample_video(root: Path, course_dir: Path, sample: dict, index: int) -> bool:
    """Optional silent study slide: ffmpeg is not required to run the demo."""
    if index > 2:
        return False
    executable = os.environ.get("FFMPEG_BIN") or shutil.which("ffmpeg")
    if not executable:
        try:
            import imageio_ffmpeg
            executable = imageio_ffmpeg.get_ffmpeg_exe()
        except (ImportError, RuntimeError):
            return False
    target = course_dir / "01 · Study sessions" / "02 · Understanding the idea.mp4"
    if target.exists():
        return True
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return False
    import textwrap
    slide = root / f"slide-{index}.png"
    image = Image.new("RGB", (1280, 720), "#eaf0e2")
    draw = ImageDraw.Draw(image)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    def font(size):
        try:
            return ImageFont.truetype(font_path, size)
        except OSError:
            return ImageFont.load_default(size=size)
    draw.text((90, 100), "YOUR NEXT IDEA", fill="#52654b", font=font(18))
    draw.text((90, 145), sample["lessons"][1], fill="#2e4734", font=font(46))
    draw.line((90, 230, 1190, 230), fill="#becdbb", width=1)
    draw.multiline_text((90, 285), textwrap.fill(sample["idea"], width=52), fill="#435a47", font=font(30), spacing=15)
    draw.text((90, 630), "LocalAcademy / Sample lesson / Silent study slide", fill="#52654b", font=font(17))
    image.save(slide)
    try:
        subprocess.run([
            executable, "-loglevel", "error", "-y", "-loop", "1", "-framerate", "5", "-i", str(slide),
            "-t", "180", "-c:v", "libx264", "-preset", "ultrafast", "-tune", "stillimage",
            "-pix_fmt", "yuv420p", "-an", "-movflags", "+faststart", str(target),
        ], check=True, timeout=35, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    except (subprocess.SubprocessError, OSError):
        target.unlink(missing_ok=True)
        return False
    captions = target.with_name(target.stem + ".en.vtt")
    captions.write_text(
        "WEBVTT\n\n00:00.000 --> 00:30.000\nThis is a silent sample study slide.\n\n"
        f"00:30.000 --> 01:30.000\n{sample['idea']}\n\n"
        f"01:30.000 --> 03:00.000\nTry it yourself: {sample['exercise']}\n", encoding="utf-8",
    )
    return True


def seed_demo(app) -> None:
    root = Path(app.instance_path) / "demo"
    root.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    with app.app_context():
        # Reusing a demo preserves changes made while evaluating the UI.
        if Course.query.count():
            return
        for index, sample in enumerate(SAMPLE_COURSES):
            course_dir = root / "courses" / f"course-{index + 1}"
            sections = (course_dir / "01 · Study sessions", course_dir / "02 · Practice & resources")
            for section in sections:
                section.mkdir(parents=True, exist_ok=True)
            for lesson_index, lesson in enumerate(sample["lessons"]):
                section = sections[0] if lesson_index < 4 else sections[1]
                reading = section / f"{lesson_index + 1:02d} · {lesson}.md"
                reading.write_text(
                    f"# {lesson}\n\n{sample['description']}\n\n## The idea\n\n{sample['idea']}\n\n"
                    f"## Try it yourself\n\n{sample['exercise']}\n\n"
                    "## A moment to reflect\n\nWrite one thing you understand more clearly now, and one question you would like to explore.\n\n"
                    "This is illustrative course material created for the LocalAcademy sample library.\n", encoding="utf-8",
                )
            quiz = sections[1] / "07 · Check your understanding.html"
            quiz.write_text('''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Check your understanding</title><style>body{margin:0;background:#f7f9f6;color:#25372b;font:16px/1.8 system-ui}main{max-width:650px;margin:40px auto;padding:28px}h1{font-size:30px;line-height:1.2}fieldset{border:1px solid #becdbb;border-radius:10px;padding:22px}label{display:block;margin:14px 0}button{padding:12px 18px;border:0;border-radius:7px;color:white;background:#2e654b;font:inherit;cursor:pointer}output{display:block;margin-top:22px;color:#2e654b}</style><main><p>LocalAcademy · Sample practice</p><h1>What makes a useful study session?</h1><form id="quiz"><fieldset><legend>Choose one answer</legend><label><input type="radio" name="answer" value="reread" required> Reread everything without pausing.</label><label><input type="radio" name="answer" value="practice"> Recall an idea, apply it, and check what you learned.</label><label><input type="radio" name="answer" value="rush"> Finish the material as quickly as possible.</label></fieldset><p><button>Check my answer</button></p><output id="feedback" aria-live="polite"></output></form></main><script>document.getElementById('quiz').addEventListener('submit',e=>{e.preventDefault();document.getElementById('feedback').textContent=new FormData(e.target).get('answer')==='practice'?'That’s the idea. Use a little practice to find out what you understand.':'Try again. Look for the answer that asks you to use what you learned.';});</script></html>''', encoding="utf-8")
            has_video = make_sample_video(root, course_dir, sample, index)
            category = Category.query.filter_by(name=sample["subject"]).first() or Category(name=sample["subject"])
            creator = Creator.query.filter_by(name=sample["instructor"]).first() or Creator(name=sample["instructor"])
            tag = Tag.query.filter_by(name="Self-paced").first() or Tag(name="Self-paced")
            course = Course(
                display_name=sample["name"], root_path=str(course_dir), is_available=True,
                description=sample["description"], categories=[category], creators=[creator], tags=[tag],
                created_at=now - timedelta(days=index * 3 + 2),
                last_accessed=now - timedelta(hours=index * 4 + 1),
            )
            db.session.add(course)
            db.session.commit()
            scan_course_folder(course, str(Path(app.instance_path) / "thumbnails"))
            files = sorted((file for file in course.files if file.file_type != "subtitle"), key=lambda file: file.relative_path)
            for file in files:
                stem = Path(file.relative_path).stem
                file.display_name = stem.split(" · ", 1)[-1]
                if file.file_type == "video":
                    file.display_name = sample["lessons"][1]
            readings = [file for file in files if file.file_type == "text"]
            for file in readings[:sample["completed"]]:
                db.session.add(PlaybackProgress(course_id=course.id, file_id=file.id, current_time=0, completed=True, last_watched=now - timedelta(days=1)))
            if has_video:
                video = next(file for file in files if file.file_type == "video")
                video.duration = 180
                course.total_duration = 180
                db.session.add(PlaybackProgress(course_id=course.id, file_id=video.id, current_time=(63, 38, 92)[index], completed=False, last_watched=now - timedelta(hours=index)))
                db.session.add(Bookmark(file_id=video.id, timestamp=30, label="The central idea", created_at=now - timedelta(hours=index + 1)))
                note_file = video
            else:
                note_file = readings[0]
            if index < 3:
                db.session.add(Note(file_id=note_file.id, timestamp=30 if has_video else None, content=sample["note"], created_at=now - timedelta(hours=index + 2), updated_at=now - timedelta(hours=index + 2)))
            db.session.commit()


def create_demo_app():
    root = Path(__file__).resolve().parent / "instance" / "demo"
    root.mkdir(parents=True, exist_ok=True)
    app = create_app({
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{root / 'sample-library.db'}",
        "ENABLE_DRIVE_MONITOR": False, "DEMO_MODE": True,
    })
    seed_demo(app)
    return app


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run an isolated, illustrative LocalAcademy sample library.")
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()
    application = create_demo_app()
    print("Sample courses, people, and progress are illustrative. The normal library is unchanged.")
    application.run(host="0.0.0.0", port=args.port, debug=False)
