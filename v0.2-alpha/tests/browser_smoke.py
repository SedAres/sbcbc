"""Browser regression checks against the isolated demo (not a real library).

Install requirements-dev.txt and Playwright Chromium; start `python demo.py`.
Run `python tests/browser_smoke.py`. Captures and reports go into ignored .cache/.
Use --browser-executable for a preinstalled Chromium and --axe-file for an
optional local axe-core script. No browser-test dependencies are used by the app.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
THEMES = ("campus", "ocean", "parchment", "mulberry", "midnight")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:5000")
    parser.add_argument("--browser-executable")
    parser.add_argument("--axe-file")
    parser.add_argument("--screenshots", default=str(ROOT / ".cache" / "qa"))
    parser.add_argument("--record-issues", action="store_true", help="Record visual/a11y findings without making them an exit failure.")
    args = parser.parse_args()
    out = Path(args.screenshots)
    out.mkdir(parents=True, exist_ok=True)
    base = args.base_url.rstrip("/")
    report = {"flows": [], "pages": [], "theme_contrast": {}, "console_errors": [], "page_errors": []}

    with sync_playwright() as p:
        options = {"headless": True, "args": ["--no-sandbox", "--disable-dev-shm-usage"]}
        if args.browser_executable:
            options.update(executable_path=str(Path(args.browser_executable).resolve()))
            options["args"] += ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"]
        browser = p.chromium.launch(**options)
        context = browser.new_context(viewport={"width": 1440, "height": 1000}, reduced_motion="reduce")
        page = context.new_page()
        page.on("pageerror", lambda error: report["page_errors"].append(str(error)))
        report["expected_http_errors"] = []
        expected_error_urls = set()
        def console_message(message):
            if message.type != "error":
                return
            url = message.location.get("url", "")
            if url in expected_error_urls and "Failed to load resource" in message.text:
                report["expected_http_errors"].append({"url": url, "message": message.text})
            else:
                report["console_errors"].append(message.text)
        page.on("console", console_message)

        def goto(route="/"):
            response = page.goto(base + route, wait_until="domcontentloaded")
            assert response.status == 200, f"{route}: {response.status}"
            page.evaluate("document.fonts.ready")
            expect(page.locator("#page-main")).to_be_visible()
            return response

        goto()
        if not page.locator(".demo-badge").count():
            raise RuntimeError("Use the isolated demo.py server, not a real course library, for browser checks.")
        course_url = page.locator(".course-card .course-cover").first.get_attribute("href")
        course_id = int(course_url.rsplit("/", 1)[-1])
        files = context.request.get(base + f"/courses/{course_id}/files").json()["files"]
        video = next((file for file in files if file["file_type"] == "video"), None)
        reading = next(file for file in files if file["file_type"] == "text")
        player_url = f'/player/{(video or reading)["file_hash"]}'

        media_url = None
        if video:
            goto(player_url)
            media_url = page.locator("video").get_attribute("src")

        def flow(name, check):
            try:
                check()
                report["flows"].append({"name": name, "status": "passed"})
            except Exception as error:
                report["flows"].append({"name": name, "status": "failed", "error": str(error)[:900]})

        def settle():
            page.evaluate("document.fonts.ready")
            page.evaluate("document.querySelector('#toast-region')?.replaceChildren()")
            page.evaluate("window.scrollTo(0,0)")

        def capture(name, route, size):
            goto(route)
            settle()
            if page.locator("video").count():
                page.wait_for_function("document.querySelector('video').readyState >= 2 && !document.querySelector('video').seeking")
            page.screenshot(path=str(out / f"{name}-{size}.png"), full_page=True)
            overflow = page.evaluate("""() => ({
              viewport: innerWidth, document: document.documentElement.scrollWidth,
              offenders: [...document.querySelectorAll('main *')].filter(e => {
                const r=e.getBoundingClientRect();return r.width && r.right > innerWidth+2 && getComputedStyle(e).position !== 'fixed';
              }).slice(0,8).map(e => e.tagName.toLowerCase()+'.'+e.className)
            })""")
            violations = []
            if args.axe_file:
                page.add_script_tag(path=args.axe_file)
                result = page.evaluate("""async () => await axe.run(document, {runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','best-practice']}})""")
                violations = [{"id": v["id"], "impact": v["impact"], "description": v["description"], "nodes": [n["target"] for n in v["nodes"][:8]]} for v in result["violations"]]
            report["pages"].append({"name": name, "size": size, "overflow": overflow, "violations": violations})

        # One batched visual round covers every requested palette and main route.
        for theme in THEMES:
            goto()
            page.locator("#theme-picker summary").click()
            page.locator(f'#theme-picker [data-theme-choice="{theme}"]').click()
            page.reload(wait_until="domcontentloaded")
            assert page.locator("html").get_attribute("data-theme") == theme
            assert page.evaluate("getComputedStyle(document.documentElement).colorScheme") == ("dark" if theme == "midnight" else "light")
            capture("dashboard-" + theme, "/", "desktop")
            report["theme_contrast"][theme] = page.evaluate("""() => {
              const s=getComputedStyle(document.documentElement);
              const color=k=>s.getPropertyValue('--'+k).trim();
              return Object.fromEntries(['page','sidebar','surface','feature','text','text-soft','muted','faint','primary','primary-ink','feature-ink','feature-muted','success','danger'].map(k=>[k,color(k)]));
            }""")
        page.evaluate("LATheme.apply('campus')")
        routes = (("dashboard", "/"), ("library", "/courses"), ("library-list", "/courses?view=list"),
                  ("course", course_url), ("player", player_url), ("reading", f'/player/{reading["file_hash"]}'), ("preferences", "/settings"),
                  ("collections", "/collections"), ("continue", "/continue-watching"))
        for label, width, height in (("desktop", 1440, 1000), ("mobile", 390, 844)):
            page.set_viewport_size({"width": width, "height": height})
            for name, route in routes:
                capture(name, route, label)
        page.set_viewport_size({"width": 768, "height": 1024})
        capture("dashboard", "/", "tablet")
        page.set_viewport_size({"width": 320, "height": 800})
        capture("preferences", "/settings", "small-mobile")
        page.set_viewport_size({"width": 1440, "height": 1000})

        def search_check():
            goto()
            page.keyboard.press("Control+k")
            assert page.locator("#global-search-input").evaluate("e=>e===document.activeElement")
            page.locator("#global-search-input").fill("hierarchy" if video else "reading")
            expect(page.locator("#search-results .search-result").first).to_be_visible()
            page.keyboard.press("ArrowDown")
            assert page.locator(".search-result").first.evaluate("e=>e===document.activeElement")
            page.keyboard.press("Escape")
            expect(page.locator("#search-results")).to_be_hidden()
        flow("Keyboard search and result navigation", search_check)

        def filter_check():
            goto("/courses")
            total = page.locator("[data-course-card]").count()
            page.locator("#course-filter").fill("Python")
            expect(page.locator("[data-course-card]:visible")).to_have_count(1)
            page.locator("#course-filter").fill("no-such-course-here")
            expect(page.locator("#filter-empty")).to_be_visible()
            page.locator("#clear-course-filter").click()
            expect(page.locator("[data-course-card]:visible")).to_have_count(total)
            page.locator("#library-sort").select_option("recent")
            expect(page).to_have_url(re.compile(r"sort=recent"))
            page.get_by_role("link", name="List view", exact=True).click()
            expect(page.locator("#course-list")).to_be_visible()
            assert "sort=recent" in page.url
        flow("Library filtering, sorting, and view preservation", filter_check)

        def course_content_check():
            goto(course_url)
            total = page.locator("[data-lesson-row]").count()
            assert total > 0
            page.locator("[data-lesson-filter]").fill("hierarchy")
            expect(page.locator("[data-lesson-filter-status]")).to_contain_text("matching")
            assert page.locator("[data-lesson-row]:visible").count() > 0
            page.locator("[data-lesson-filter]").fill("this-will-not-match-any-lesson")
            expect(page.locator("[data-lesson-filter-empty]")).to_be_visible()
            expect(page.locator("[data-lesson-row]:visible")).to_have_count(0)
            page.locator("[data-lesson-filter]").fill("")
            expect(page.locator("[data-lesson-filter-empty]")).to_be_hidden()
            expect(page.locator("[data-lesson-row]:visible")).to_have_count(total)
        flow("Course content search and recovery", course_content_check)

        def appearance_check():
            goto("/settings")
            status = page.locator("#settings-save-status").inner_text()
            page.locator('#appearance [data-theme-choice="ocean"]').click()
            assert page.locator("html").get_attribute("data-theme") == "ocean"
            assert page.locator("#settings-save-status").inner_text() == status
            page.reload(wait_until="domcontentloaded")
            expect(page.locator('#appearance [data-theme-choice="ocean"]')).to_have_attribute("aria-pressed", "true")
            page.emulate_media(color_scheme="dark")
            page.locator("#appearance [data-theme-system]").check()
            expect(page.locator("html")).to_have_attribute("data-theme", "midnight")
            assert page.locator("#settings-save-status").inner_text() == status
            page.emulate_media(color_scheme="light")
            expect(page.locator("html")).to_have_attribute("data-theme", "campus")
            page.locator('#appearance [data-theme-choice="mulberry"]').click()
            expect(page.locator("#appearance [data-theme-system]")).not_to_be_checked()
            other = context.new_page()
            other.goto(base)
            other.evaluate("LATheme.apply('parchment')")
            expect(page.locator("html")).to_have_attribute("data-theme", "parchment")
            other.close()
            page.locator('#appearance [data-theme-choice="campus"]').click()
        flow("Themes persist, synchronize, and follow device appearance", appearance_check)

        def settings_check():
            goto("/settings")
            page.locator("#setting-speed").select_option("1.25")
            expect(page.locator("#settings-save-status")).to_have_text("You have unsaved changes.")
            page.get_by_role("button", name="Save preferences", exact=True).click()
            expect(page.locator("#settings-save-status")).to_have_text("Preferences saved just now.")
            expect(page.locator("#settings-error")).to_be_hidden()
            page.locator("#reset-settings").click()
            expect(page.locator(".modal-compact").get_by_role("button", name="Cancel", exact=True)).to_be_focused()
            page.keyboard.press("Escape")
            expect(page.locator("#reset-settings")).to_be_focused()
        flow("Player preferences save and safe reset cancellation", settings_check)

        def modal_check():
            goto()
            opener = page.get_by_role("button", name="Add a course", exact=True)
            opener.click()
            expect(page.locator('#add-course-form input[name="display_name"]')).to_be_focused()
            page.keyboard.press("Shift+Tab")
            page.keyboard.press("Shift+Tab")
            assert page.locator("#add-course-modal").evaluate("e=>e.contains(document.activeElement)")
            page.locator('#add-course-form input[name="display_name"]').fill("Browser verification")
            page.locator('#add-course-form input[name="root_path"]').fill("/a-folder-that-does-not-exist")
            expected_error_urls.add(base + "/courses/add")
            page.get_by_role("button", name="Add to library", exact=True).click()
            expect(page.locator("#add-course-error")).to_contain_text("folder does not exist")
            expect(page.get_by_role("button", name="Add to library", exact=True)).to_be_enabled()
            page.keyboard.press("Escape")
            expect(page.locator("#add-course-modal")).to_be_hidden()
            expect(opener).to_be_focused()
        flow("Import focus trap, error recovery, and focus restoration", modal_check)

        def mobile_check():
            page.set_viewport_size({"width": 390, "height": 844})
            goto()
            assert page.locator("#sidebar").evaluate("e=>e.inert")
            page.locator("#mobile-menu").click()
            expect(page.locator("#mobile-menu")).to_have_attribute("aria-expanded", "true")
            page.keyboard.press("Tab")
            assert page.locator("#sidebar").evaluate("e=>e.contains(document.activeElement)")
            page.keyboard.press("Escape")
            expect(page.locator("#mobile-menu")).to_be_focused()
            assert not page.locator(".app-main").evaluate("e=>e.inert")
            page.locator("#mobile-search").click()
            expect(page.locator("#global-search-input")).to_be_visible()
            page.locator("#global-search-input").fill("hierarchy" if video else "reading")
            expect(page.locator("#search-results")).to_be_visible()
            page.keyboard.press("Escape")
            expect(page.locator("#mobile-search")).to_be_focused()
            page.set_viewport_size({"width": 1440, "height": 1000})
        flow("Mobile navigation and search are keyboard-accessible", mobile_check)

        def collection_check():
            goto("/collections")
            page.get_by_role("button", name="Create collection", exact=True).click()
            page.locator('#collection-form input[name="name"]').fill("Design")
            expected_error_urls.add(base + "/api/taxonomy/categories")
            page.locator('#collection-form button[type="submit"]').click()
            expect(page.locator("#collection-error")).to_contain_text("already exists")
            expect(page.locator('#collection-form button[type="submit"]')).to_be_enabled()
            page.keyboard.press("Escape")
            expect(page.locator("#collection-modal")).to_be_hidden()
        flow("Collection validation and recovery", collection_check)

        def study_flow():
            (ROOT / "instance").mkdir(exist_ok=True)
            fixture_id = None
            with tempfile.TemporaryDirectory(prefix="browser-check-", dir=ROOT / "instance") as folder:
                Path(folder, "01-lesson.md").write_text("# A useful lesson\n\nPractice, reflect, and keep one good idea.", encoding="utf-8")
                extra_captions = Path(folder, "extra.srt")
                extra_captions.write_text("1\n00:00:00,000 --> 00:00:05,000\nAn attached caption.\n", encoding="utf-8")
                try:
                    goto()
                    page.get_by_role("button", name="Add a course", exact=True).click()
                    page.locator('#add-course-form input[name="display_name"]').fill("Browser verification course")
                    page.locator('#add-course-form input[name="root_path"]').fill(folder)
                    page.locator('#add-course-form button[type="submit"]').click()
                    expect(page).to_have_url(re.compile(r"/courses/\d+$"))
                    fixture_id = int(page.url.rsplit("/",1)[-1])
                    page.locator("[data-mark-watched]").first.click()
                    expect(page.locator("[data-course-percent]").first).to_have_text("100%")
                    expect(page.locator("[data-course-percent]").last).to_have_text("100%")
                    page.locator("[data-rename-file]").first.click()
                    dialog = page.get_by_role("dialog")
                    dialog.get_by_label("Lesson name").fill("A lesson worth keeping")
                    dialog.get_by_role("button", name="Save name", exact=True).click()
                    expect(page.locator(".lesson-name")).to_have_text("A lesson worth keeping")
                    page.locator(".lesson-main").first.click()
                    expect(page.locator(".player-title-copy h1")).to_have_text("A lesson worth keeping")
                    expect(page.locator("[data-text-content]")).to_contain_text("Practice, reflect")
                    expect(page.locator("[data-complete-label]").first).to_have_text("Completed")
                    expect(page.locator("[data-complete-label]").last).to_have_text("Completed")
                    page.locator('[data-action="mark-complete"]').first.click()
                    expect(page.locator("[data-complete-label]").first).to_have_text("Mark complete")
                    expect(page.locator("[data-complete-label]").last).to_have_text("Mark complete")
                    page.get_by_role("button", name="Take a note", exact=True).click()
                    expect(page.locator('[data-note-form] input[name="timestamped"]')).not_to_be_checked()
                    page.get_by_label("Your note", exact=True).fill("A good idea from this lesson.")
                    page.get_by_role("button", name="Save note", exact=True).click()
                    expect(page.locator('[data-panel-tab="notes"]')).to_have_attribute("aria-selected", "true")
                    expect(page.locator("[data-notes-list]")).to_contain_text("A good idea from this lesson.")
                    page.locator("[data-notes-list] .saved-item-delete").click()
                    expect(page.get_by_role("button", name="Cancel", exact=True)).to_be_focused()
                    page.keyboard.press("Escape")
                    expect(page.locator("[data-notes-list] .saved-item")).to_have_count(1)
                    page.locator("[data-notes-list] .saved-item-delete").click()
                    page.locator(".modal-compact").get_by_role("button", name="Delete note", exact=True).click()
                    expect(page.locator("[data-notes-list] .saved-item")).to_have_count(0)
                    page.get_by_role("button", name="Bookmark", exact=True).click()
                    page.get_by_label("Bookmark name").fill("The beginning")
                    page.locator('[data-bookmark-form] button[type="submit"]').click()
                    expect(page.locator("[data-bookmarks-list]")).to_contain_text("The beginning")
                    page.locator('[data-panel-tab="notes"]').click()
                    page.locator('[data-panel-tab="notes"]').press("ArrowRight")
                    expect(page.locator('[data-panel-tab="bookmarks"]')).to_be_focused()
                    expect(page.locator('[data-panel-tab="bookmarks"]')).to_have_attribute("aria-selected", "true")
                    expect(page.locator('[data-panel-tab="transcript"]')).to_be_hidden()
                    # Exercise actual media controls without changing the sample lessons.
                    if media_url:
                        response = context.request.get(base + media_url)
                        assert response.ok
                        Path(folder, "02-slide.mp4").write_bytes(response.body())
                        Path(folder, "02-slide.en.vtt").write_text("WEBVTT\n\n00:00:00.000 --> 00:00:10.000\nA first idea.\n\n00:00:10.000 --> 00:03:00.000\nA second idea.\n", encoding="utf-8")
                        assert context.request.post(base + f"/courses/{fixture_id}/rescan", data={}).ok
                        indexed = context.request.get(base + f"/courses/{fixture_id}/files").json()["files"]
                        lecture = next(file for file in indexed if file["file_type"] == "video")
                        goto(f'/player/{lecture["file_hash"]}')
                        page.wait_for_function("document.querySelector('video').readyState >= 2")
                        page.locator(".control-play").click()
                        page.wait_for_function("!document.querySelector('video').paused")
                        page.locator(".control-play").click()
                        page.wait_for_function("document.querySelector('video').paused")
                        page.locator('[data-action="seek-forward"]').click()
                        assert page.locator("video").evaluate("e=>e.currentTime") >= 5
                        page.locator("[data-seekbar]").press("Home")
                        assert page.locator("video").evaluate("e=>e.currentTime") < 1
                        expect(page.locator(".transcript-cue")).to_have_count(2)
                        page.locator(".transcript-cue").last.click()
                        assert 9 <= page.locator("video").evaluate("e=>e.currentTime") <= 11
                        page.locator("[data-caption-file]").set_input_files(str(extra_captions))
                        expect(page.locator("[data-transcript-list]")).to_contain_text("An attached caption.")
                        page.locator("[data-delete-track]").click()
                        page.locator(".modal-compact").get_by_role("button", name="Remove track", exact=True).click()
                        expect(page.locator(".transcript-cue")).to_have_count(2)
                        expect(page.locator("[data-delete-track]")).to_be_hidden()
                        page.locator('[data-action="captions"]').click()
                        expect(page.locator('[data-action="captions"]')).to_have_attribute("aria-pressed", "false")
                        page.locator('[data-action="theater"]').click()
                        expect(page.locator("body")).to_have_class(re.compile("theater-active"))
                        page.keyboard.press("Escape")
                        expect(page.locator("body")).not_to_have_class(re.compile("theater-active"))
                        page.locator('[data-action="theater"]').click()
                        page.keyboard.press("Control+k")
                        expect(page.locator("body")).not_to_have_class(re.compile("theater-active"))
                        expect(page.locator("#global-search-input")).to_be_focused()
                finally:
                    if fixture_id:
                        # Stop player heartbeats before removing their temporary course.
                        page.goto(base, wait_until="domcontentloaded")
                        response = context.request.post(base + f"/courses/{fixture_id}/delete", data={})
                        assert response.ok
        flow("Import, completion, rename, notes, bookmarks, captions, and playback", study_flow)

        def legacy_and_storage_check():
            for stored, expected in (("light", "campus"), ("dark", "midnight"), ("unknown", "campus")):
                isolated = browser.new_context()
                isolated.add_init_script(f"localStorage.setItem('la-theme', {json.dumps(stored)})")
                tab = isolated.new_page()
                tab.goto(base)
                expect(tab.locator("html")).to_have_attribute("data-theme", expected)
                isolated.close()
            isolated = browser.new_context()
            isolated.add_init_script("Storage.prototype.getItem=()=>{throw new Error('Unavailable')};Storage.prototype.setItem=()=>{throw new Error('Unavailable')};")
            tab = isolated.new_page()
            tab.goto(base + "/settings")
            tab.locator('#appearance [data-theme-choice="ocean"]').click()
            expect(tab.locator("html")).to_have_attribute("data-theme", "ocean")
            isolated.close()
        flow("Legacy themes and unavailable browser storage", legacy_and_storage_check)

        goto()
        page.evaluate("LATheme.apply('campus')")
        browser.close()

    report_path = out / "report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    failures = [item for item in report["flows"] if item["status"] == "failed"]
    visual = [item for item in report["pages"] if item["overflow"]["document"] > item["overflow"]["viewport"] + 1 or item["violations"]]
    for result in report["flows"]:
        print(f'{result["status"].upper():6} {result["name"]}')
        if "error" in result:
            print(result["error"])
    print(f"\n{len(report['pages'])} viewport/theme captures; {len(visual)} with visual/accessibility findings.")
    print(f"Page errors: {len(report['page_errors'])}; console errors: {len(report['console_errors'])}")
    print(f"Report: {report_path}")
    return 1 if failures or report["page_errors"] or report["console_errors"] or (visual and not args.record_issues) else 0


if __name__ == "__main__":
    sys.exit(main())
