# LocalAcademy · a personal campus

## Product and scope

LocalAcademy indexes learning material that already lives in local folders. The core jobs are to find a course, resume a lesson, understand progress, capture a useful idea, and return to it later. The redesign is for self-directed learning, not a public course marketplace or a social platform.

Only **v0.2-alpha** is redesigned. Flask/Jinja, vanilla JavaScript, the database models, local course files, readers, transcripts, playback tools, and per-course overrides are retained. There is no frontend build step. The normal app has no seeded or invented activity; sample people and learning data belong only to the explicitly labeled `demo.py` preview.

## Visual direction

**Quiet academic, rather than dashboard chrome.** Book-inspired covers, restrained rules, paper-like surfaces, and a single learning illustration give the library a coherent educational identity. Flat, colored book covers are intentional fallbacks when a course has no supplied artwork; uploaded covers continue to work.

- **Onest** handles body copy, navigation, labels, and controls. **Bricolage Grotesque** gives headings and book titles a distinctive, readable voice. WOFF2 files and their OFL licenses are in `static/fonts/`.
- The workspace uses a persistent desktop sidebar and a compact contextual header. Content remains constrained and readable on wide screens.
- Layouts recompose at laptop, tablet, and phone widths. Small screens receive a focus-managed navigation drawer, compact theme selector, expandable search, single-column course cards, and stacked player/study tools.
- SVG icons share a consistent stroke and carry hidden decorative semantics. Icon-only controls have explicit accessible names. There are no icon fonts or remote asset requests.
- Motion is short, purposeful feedback. Reduced-motion preferences turn off decorative transitions and smooth scrolling.

## Semantic themes

`static/css/themes.css` defines **Campus**, **Ocean**, **Parchment**, **Mulberry**, and **Midnight**. Components consume semantic tokens rather than hard-coded light/dark overrides:

- `page`, `sidebar`, `surface`, `surface-raised`, `surface-soft`: spatial hierarchy.
- `text`, `text-soft`, `muted`, `faint`: readable emphasis levels.
- `primary`, `primary-ink`, `accent-soft`: selection and the next useful action.
- `feature`, `feature-ink`, `feature-muted`: the resume/onboarding panel.
- `line`, `line-strong`, `input-line`: dividers and control boundaries.
- `success`, `warning`, `danger`, and their soft surfaces: meaningful status, not decoration.

Preview thumbnails use the same live palette tokens. Small subdued text is kept readable even on tinted surfaces. Course cover colors retain their book identity across palettes; the surrounding interface and reading surfaces follow the selected theme. Video controls intentionally stay dark to remain legible over arbitrary media.

`static/js/theme.js` runs **before stylesheets paint**. It reads `la-theme` in localStorage, recognizes legacy light/dark values, updates the document theme/color scheme/browser color, and synchronizes selections, device appearance, and open tabs. Storage errors do not break the page. Appearance is immediate and browser-local, not part of the server-side player-preferences form.

## Interaction conventions

### Start or resume without searching for the next step

The dashboard gives an in-progress lesson priority. Existing libraries with no progress get a genuine **Start learning** action. Empty libraries instead receive concise folder-import guidance. Completion and notebook content use real data; saved playback positions are labeled **Playback progress**, never presented as time studied or a streak.

### Find and organize

The course library supports meaningful availability/progress filters, grid/list layouts, actual server-side sorts, and immediate local text filtering. Instructor, category, and tag terms are searchable. Query, view, filter, and sort survive navigation. A course's content index can also be searched in place: matching folders open automatically, the result count is announced, and an empty match state explains how to recover. Global search is debounced, cancels stale requests, supports keyboard results and Ctrl/⌘ K, announces result counts, and falls back to library search if a request fails.

### Import progressively

**Add a course** first asks for its name and the folder path on the **server's computer**. Description, instructors, categories, and tags sit behind optional details. Pending states disable duplicate submission; errors stay beside the form without losing input. Success takes the learner to the indexed course.

### Study with less distraction

The player keeps the lesson and media controls primary, with **Transcript**, **Lessons**, **Notes**, and **Saved** in a secondary panel. Non-media readers show only the relevant Lessons, Notes, and Saved tools, and do not offer unsupported captions or timestamps. Tabs have explicit ARIA relationships, a single keyboard tab stop, and arrow/Home/End navigation. Saved notes and bookmarks reveal their destination panel automatically; dashboard note links open the Notes panel directly. Theater mode removes workspace chrome without introducing another player.

### Safe dialogs and clear outcomes

`window.LocalAcademy` centralizes toasts, icons, dialogs, confirmation, and naming prompts. Import, note/bookmark composers, and destructive confirmations share focus trapping, background `inert`, Escape, and focus restoration. Busy saves cannot accidentally dismiss a dialog. Destructive confirmations initially focus **Cancel**. Removing a course explains that original files stay untouched. Completion chips and course progress summaries update without a reload.

Preferences distinguish immediate appearance changes from explicitly saved player settings. The save action stays visible while scrolling long settings sections, unsaved changes are named immediately, and leaving with pending edits prompts before they are lost. Resetting global or per-course player preferences preserves courses, learning data, and appearance. Unavailable folders offer reconnection/rescan guidance; missing pages offer a library recovery path.

## Verification and maintenance

- Run the Python tests and `node --check` for every browser script.
- `tests/browser_smoke.py` exercises the isolated demo, captures main desktop/mobile routes and all five palettes, and checks keyboard search, sorting/filtering, themes, dialogs, navigation, and the import-to-study workflow. An optional local axe-core script adds WCAG checks.
- Inspect the captured dashboard, library, course, player, and Appearance screen—not just a component in isolation. Check small phones, tablet widths, and a dark palette.
- Generated databases, demo content, browser binaries, and captures remain ignored. Source assets and their licenses/provenance are retained.
- Keep new component colors semantic; do not add a sixth palette by scattering selectors through `app.css`. Add it consistently to the palette tokens, Python theme list, pre-paint JavaScript registry, and browser tests.

LocalAcademy is still a trusted personal-server app without authentication. Visual polish is not an internet-facing security boundary; see the README's deployment notes.
