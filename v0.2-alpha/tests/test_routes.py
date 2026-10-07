import io
import os
import tempfile
import unittest

from app import create_app
from models import CourseFile, db


class LearningAppTests(unittest.TestCase):
    def setUp(self):
        self.temp_root = tempfile.TemporaryDirectory()
        self.course_root = self.temp_root.name
        for filename, payload in {
            "lesson01.mp4": b"sample-video-data",
            "lesson02.wav": b"sample-audio-data",
            "worksheet.pdf": b"%PDF-1.4%%EOF",
            "diagram.png": b"not-a-real-png-but-validly-indexed",
        }.items():
            with open(os.path.join(self.course_root, filename), "wb") as media:
                media.write(payload)
        with open(os.path.join(self.course_root, "lesson01.en.srt"), "w", encoding="utf-8") as captions:
            captions.write("""1
00:00:00,000 --> 00:00:01,200
Hello course.
""")
        with open(os.path.join(self.course_root, "quiz.html"), "w", encoding="utf-8") as lesson:
            lesson.write("<!doctype html><h1>Quiz</h1><button>Submit</button>")
        with open(os.path.join(self.course_root, "reading.md"), "w", encoding="utf-8") as reading:
            reading.write("# A reading\nA useful paragraph.")
        with open(os.path.join(self.course_root, "reference.bin"), "wb") as attachment:
            attachment.write(b"download me")

        self.app = create_app({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "ENABLE_DRIVE_MONITOR": False,
        })
        self.client = self.app.test_client()
        response = self.client.post("/courses/add", json={
            "display_name": "Learning fundamentals",
            "root_path": self.course_root,
            "description": "A local course for route tests.",
            "creator_names": "Ada Lovelace",
            "category_names": "Foundations, Design",
            "tag_names": "beginner",
        })
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.course_id = response.json["course_id"]
        with self.app.app_context():
            self.files = {
                file.file_type: file.file_hash
                for file in CourseFile.query.filter_by(course_id=self.course_id).all()
                if file.file_type != "subtitle"
            }

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        self.temp_root.cleanup()

    def test_dashboard_and_course_detail_render(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        detail = self.client.get(f"/courses/{self.course_id}")
        self.assertEqual(detail.status_code, 200)
        self.assertIn(b"Learning fundamentals", detail.data)
        self.assertIn(b"Course content", detail.data)

    def test_supported_lessons_render_in_the_player(self):
        for file_type in ("video", "audio", "pdf", "image", "html", "text", "file"):
            response = self.client.get(f"/player/{self.files[file_type]}")
            self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertEqual(self.client.get(f"/player/text/{self.files['text']}").status_code, 200)
        html_hash = self.files["html"]
        html_reader = self.client.get(f"/player/html/{html_hash}/")
        self.assertEqual(html_reader.status_code, 200)
        html_reader.close()
        # HTML lessons are served in the sandboxed reader, not inline at the app origin.
        self.assertEqual(self.client.get(f"/player/serve/{html_hash}").status_code, 404)

    def test_sidecar_and_attached_transcripts(self):
        video_hash = self.files["video"]
        response = self.client.get(f"/player/api/{video_hash}/transcript")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["cues"][0]["text"], "Hello course.")
        self.assertEqual(self.client.get(f"/player/subtitles/{response.json['track']['file_hash']}.vtt").status_code, 200)

        uploaded_vtt = b"""WEBVTT

00:00:00.000 --> 00:00:01.000
Attached caption
"""
        upload = self.client.post(
            f"/player/{video_hash}/subtitles",
            data={"file": (io.BytesIO(uploaded_vtt), "captions.vtt")},
            content_type="multipart/form-data",
        )
        self.assertEqual(upload.status_code, 200, upload.get_data(as_text=True))
        attached_key = upload.json["track"]["key"]
        transcript = self.client.get(f"/player/api/{video_hash}/transcript?track={attached_key}")
        self.assertEqual(transcript.status_code, 200)
        self.assertEqual(transcript.json["cues"][0]["text"], "Attached caption")
        self.assertEqual(self.client.get(upload.json["track"]["url"]).status_code, 200)

    def test_progress_notes_bookmarks_and_share_links(self):
        video_hash = self.files["video"]
        progress = self.client.post(f"/player/progress/{video_hash}", json={"current_time": 3.5, "completed": False})
        self.assertEqual(progress.status_code, 200)
        note = self.client.post(f"/player/notes/{video_hash}", json={"content": "Remember this idea", "timestamp": 2.0})
        self.assertEqual(note.status_code, 200)
        bookmark = self.client.post(f"/player/bookmarks/{video_hash}", json={"timestamp": 2.5, "label": "Key idea"})
        self.assertEqual(bookmark.status_code, 200)
        share = self.client.post("/player/timestamp-link", json={"timestamp": 42, "file_hash": video_hash})
        self.assertEqual(share.status_code, 200)
        self.assertIn("?t=42", share.json["link"])

    def test_global_and_course_settings(self):
        response = self.client.post("/settings/update", json={
            "playback_speed": 1.5,
            "skip_silence_enabled": True,
            "skip_silence_db_threshold": -44,
            "skip_silence_min_duration": 0.7,
            "skip_silence_speed": 8,
            "subtitle_enabled": True,
            "auto_advance": False,
            "hotkeys": {"play_pause": "num_4"},
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get("/settings").status_code, 200)
        self.assertEqual(self.client.get("/settings/hotkeys").json["hotkeys"]["play_pause"], "num_4")
        course = self.client.post(f"/settings/course/{self.course_id}", json={"playback_speed": "2"})
        self.assertEqual(course.status_code, 200)
        self.assertEqual(self.client.post(f"/settings/course/{self.course_id}/reset").status_code, 200)

    def test_timestamp_validation_and_hotkey_queue(self):
        response = self.client.post(f"/player/progress/{self.files['video']}", json={"current_time": -1})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.client.post("/api/hotkey/next_file").status_code, 200)
        self.assertEqual(self.client.get("/api/hotkey/poll").json["actions"], ["next_file"])


if __name__ == "__main__":
    unittest.main()
