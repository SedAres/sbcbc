"""Presentation and navigation regressions for the v0.2 redesign."""
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser

from app import UI_THEMES, create_app
from models import Course, CourseFile, db


class ElementIds(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.elements = []

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))
        for key, value in attrs:
            if key == "id":
                self.ids.append(value)


class PresentationTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.TemporaryDirectory()
        self.app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "ENABLE_DRIVE_MONITOR": False})
        self.client = self.app.test_client()
        self.courses = []
        for index, name in enumerate(("Visual foundations", "A writing practice")):
            course_path = os.path.join(self.root.name, str(index))
            os.makedirs(course_path)
            with open(os.path.join(course_path, "01-reading.md"), "w", encoding="utf-8") as file:
                file.write("# A course reading\n\nA useful idea to explore.")
            response = self.client.post("/courses/add", json={
                "display_name": name, "root_path": course_path, "creator_names": "Maya Chen",
                "category_names": "Design", "tag_names": "Beginner", "description": "Practice with intention.",
            })
            self.assertEqual(response.status_code, 200)
            self.courses.append(response.json["course_id"])
        with self.app.app_context():
            self.lesson_hash = CourseFile.query.filter_by(course_id=self.courses[0]).first().file_hash

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        self.root.cleanup()

    def test_all_five_themes_are_available_everywhere(self):
        self.assertEqual(len(UI_THEMES), 5)
        for route in ("/", "/courses", "/collections", "/continue-watching", "/settings", f"/player/{self.lesson_hash}"):
            html = self.client.get(route).get_data(as_text=True)
            for theme in UI_THEMES:
                self.assertIn(f'data-theme-choice="{theme["id"]}"', html)
        settings = self.client.get("/settings").get_data(as_text=True)
        self.assertEqual(settings.count('class="theme-choice"'), 5)
        self.assertIn("Theme changes apply immediately", settings)

    def test_theme_bootstrap_precedes_stylesheets_and_is_local(self):
        html = self.client.get("/").get_data(as_text=True)
        self.assertLess(html.index("js/theme.js"), html.index("css/themes.css"))
        self.assertIn('rel="icon"', html)
        self.assertIn("fonts/onest-latin-400-normal.woff2", html)
        self.assertNotIn("fonts.googleapis.com", html)
        self.assertNotIn("cdn.jsdelivr.net", html)

    def test_routes_have_unique_element_ids(self):
        for route in ("/", "/courses", "/courses?view=list", "/settings", "/collections", f"/courses/{self.courses[0]}", f"/player/{self.lesson_hash}"):
            parser = ElementIds()
            response = self.client.get(route)
            self.assertEqual(response.status_code, 200)
            parser.feed(response.get_data(as_text=True))
            self.assertEqual(len(parser.ids), len(set(parser.ids)), route)

    def test_import_has_progressive_optional_fields(self):
        html = self.client.get("/courses?add=1").get_data(as_text=True)
        self.assertIn('class="import-optional-details"', html)
        self.assertIn('id="folder-path-hint"', html)
        self.assertIn('name="root_path" required', html)
        self.assertIn('aria-describedby="add-course-description"', html)

    def test_existing_library_without_progress_has_a_start_action(self):
        html = self.client.get("/").get_data(as_text=True)
        self.assertIn("Start learning", html)
        self.assertNotIn("Add your first course", html)

    def test_empty_library_onboarding_is_honest(self):
        for course_id in self.courses:
            self.client.post(f"/courses/{course_id}/delete", json={})
        html = self.client.get("/").get_data(as_text=True)
        self.assertIn("Add your first course", html)
        self.assertIn("Choose your course folder", html)
        self.assertIn('value="0" max="1"', html)

    def test_search_matches_instructor_category_and_tag(self):
        for term in ("Maya", "Design", "Beginner", "intention"):
            library = self.client.get(f"/courses?q={term}").get_data(as_text=True)
            self.assertIn("Visual foundations", library)
            self.assertEqual(len(self.client.get(f"/search?q={term}").json["courses"]), 2)

    def test_library_preserves_filter_view_query_and_sort(self):
        html = self.client.get("/courses?view=list&filter=available&q=Design&sort=recent").get_data(as_text=True)
        self.assertIn('value="recent" selected', html)
        self.assertIn('id="course-list"', html)
        self.assertIn("sort=recent", html)
        self.assertIn("q=Design", html)
        self.assertIn("view=list", html)

    def test_sort_orders_courses(self):
        with self.app.app_context():
            now = datetime.now(timezone.utc)
            visual = db.session.get(Course, self.courses[0])
            writing = db.session.get(Course, self.courses[1])
            visual.created_at, writing.created_at = now, now - timedelta(days=3)
            visual.last_accessed, writing.last_accessed = now - timedelta(days=1), now
            db.session.commit()
        by_name = self.client.get("/courses?sort=name").get_data(as_text=True)
        by_recent = self.client.get("/courses?sort=recent").get_data(as_text=True)
        by_access = self.client.get("/courses?sort=accessed").get_data(as_text=True)
        self.assertLess(by_name.index('aria-label="Open A writing practice'), by_name.index('aria-label="Open Visual foundations'))
        self.assertLess(by_recent.index('aria-label="Open Visual foundations'), by_recent.index('aria-label="Open A writing practice'))
        self.assertLess(by_access.index('aria-label="Open A writing practice'), by_access.index('aria-label="Open Visual foundations'))

    def test_invalid_query_options_fall_back_safely(self):
        html = self.client.get("/courses?sort=unknown&filter=unknown&view=unknown").get_data(as_text=True)
        self.assertIn('value="name" selected', html)
        self.assertIn('id="course-grid"', html)
        self.assertIn('aria-current="page">All courses', html)

    def test_filtered_empty_state_does_not_claim_the_library_is_empty(self):
        html = self.client.get("/courses?q=no-such-subject").get_data(as_text=True)
        self.assertIn("No courses found.", html)
        self.assertIn("View all courses", html)
        self.assertNotIn("Your first course belongs here", html)

    def test_latest_notes_link_directly_to_study_tools(self):
        self.client.post(f"/player/notes/{self.lesson_hash}", json={"content": "A thought worth keeping"})
        html = self.client.get("/").get_data(as_text=True)
        self.assertIn("A thought worth keeping", html)
        self.assertIn(f'/player/{self.lesson_hash}#notes', html)
        with self.app.app_context():
            db.session.get(Course, self.courses[0]).is_available = False
            db.session.commit()
        self.assertNotIn("A thought worth keeping", self.client.get("/").get_data(as_text=True))

    def test_player_has_named_tabs_and_accessible_note_dialog(self):
        html = self.client.get(f"/player/{self.lesson_hash}").get_data(as_text=True)
        for name in ("transcript", "lessons", "notes", "bookmarks"):
            self.assertIn(f'aria-controls="panel-{name}"', html)
            self.assertIn(f'aria-labelledby="tab-{name}"', html)
        self.assertIn('aria-labelledby="note-dialog-title"', html)
        self.assertIn('aria-labelledby="bookmark-dialog-title"', html)
        self.assertIn("Your note", html)

    def test_reading_tools_do_not_offer_unsupported_media_actions(self):
        parser = ElementIds()
        parser.feed(self.client.get(f"/player/{self.lesson_hash}").get_data(as_text=True))
        transcript = next(attrs for tag, attrs in parser.elements if attrs.get("data-panel-tab") == "transcript")
        self.assertIn("hidden", transcript)
        timestamp = next(attrs for tag, attrs in parser.elements if tag == "input" and attrs.get("name") == "timestamped")
        self.assertNotIn("checked", timestamp)
        bookmark_time = next(attrs for tag, attrs in parser.elements if attrs.get("class") == "bookmark-time-line")
        self.assertIn("hidden", bookmark_time)

    def test_course_content_search_and_persistent_settings_save_are_present(self):
        course = self.client.get(f"/courses/{self.courses[0]}").get_data(as_text=True)
        self.assertIn('data-lesson-filter', course)
        self.assertIn('data-lesson-filter-status', course)
        self.assertIn('data-lesson-filter-empty', course)
        settings = self.client.get("/settings").get_data(as_text=True)
        self.assertIn('id="settings-save-status"', settings)
        self.assertIn('class="settings-actions"', settings)
        self.assertIn("Save preferences", settings)

    def test_keyboard_wayfinding_is_present(self):
        html = self.client.get("/courses").get_data(as_text=True)
        self.assertIn('class="skip-link" href="#page-main"', html)
        self.assertIn('aria-label="Workspace"', html)
        self.assertIn('aria-controls="sidebar" aria-expanded="false"', html)

    def test_collection_creation_returns_the_detail_identifier(self):
        response = self.client.post("/api/taxonomy/categories", json={"name": "New subject"})
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json["success"])
        item = response.json["item"]
        detail = self.client.get(f'/collections/categories/{item["id"]}')
        self.assertEqual(detail.status_code, 200)
        self.assertIn(b"New subject", detail.data)

    def test_not_found_has_a_recovery_path(self):
        page = self.client.get("/a-page-that-isnt-here")
        self.assertEqual(page.status_code, 404)
        self.assertIn(b"Back to your library", page.data)
        api = self.client.get("/api/not-here", headers={"Accept": "application/json"})
        self.assertEqual(api.status_code, 404)
        self.assertIn("error", api.json)

    def test_ui_assets_are_served(self):
        for path in ("css/themes.css", "css/app.css", "js/theme.js", "fonts/onest-latin-400-normal.woff2", "img/study-books.webp", "img/favicon.svg"):
            response = self.client.get(f"/static/{path}")
            self.assertEqual(response.status_code, 200, path)
            response.close()


if __name__ == "__main__":
    unittest.main()
