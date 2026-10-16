# LocalAcademy v0.3 — Duolingo-style design system

## Product (unchanged from v0.2)
LocalAcademy indexes learning material that already lives in local folders. Find a course, resume a lesson, understand progress, capture an idea, return to it later. Flask/Jinja, SQLAlchemy, vanilla JS, no build step, no remote assets. Routes, models, APIs, player behaviour, per-course overrides and the isolated `demo.py` preview are carried over from `v0.2-alpha` unchanged; only the visual system, copy tone, versioned storage (`instance/localacademy-v03.db`), and the font changed.

## Visual system (implemented, not aspirational)
Playful learning with high-energy brand character: a white app-like foundation, vivid green anchors, rounded illustration-driven UI, bold friendly type, and gamified feedback on **real** data only (course/lesson counts, completion, playback position — never invented streaks or XP).

- **Colour (spec tokens in `static/css/themes.css`)** — `--duo-green #58CC02` (primary CTA), `--duo-green-deep #46A302` (pressed depth/hover), `--duo-green-soft #D7FFB8`, white/`#F7F7F7` surfaces, ink `#4B4B4B`, muted `#777777`, blue `#1CB0F6` (secondary/XP-progress), yellow `#FFD900` (reward/count badges), red `#FF4B4B` (literal errors/offline), purple `#CE82FF`, border `#E5E5E5`, hard shadow `#D7D7D7`, focus tint `#84D8FF`. Components consume semantic tokens (`--page`, `--surface`, `--line`, `--primary`, `--success`, `--danger`…); hex values live in `themes.css`, geometry/duolingo behaviour in `static/css/duo.css` (loaded last).
- **Type** — `--font-display/--font-body: "din-round", "Nunito", …`. Nunito (400/700/800/900) is self-hosted from `@fontsource/nunito` under SIL OFL (`static/fonts/`), so no device needs din-round or a network. Body copy is bold and chunky (weight 700 base, 900 headings); mono only for paths/durations/counters.
- **Geometry & depth** — cartoon-physical, not SaaS-soft: 16px controls, 24px cards, 2px borders, and a hard bottom edge (`border-bottom: 4px` on buttons, `0 6px 0` card shadows). Buttons press (`translateY(3px)` + shrinking bottom edge). Progress bars are 14px rounded tracks — green for completion, blue for in-lesson playback.
- **Layout** — app-first lanes: white 264px sidebar with pill navigation (soft-green active state, yellow count badges), progress/rewards surfaced on the dashboard rail, mascot art punctuating the resume/welcome panels rather than flooding pages. Breakpoints inherit v0.2 behaviour (<768px single-column, stacked full-width CTAs; desktop wide hero + rail); touch targets stay ≥50px.
- **Mascot** — `static/img/mascot.svg` is an original green-owl mark drawn for this project (see `static/img/PROVENANCE.md`); it is not a Duolingo asset and no Duolingo name, logo, or illustration is reproduced.

## Appearance (behaviour kept, palettes replaced)
The five v0.2 decorative palettes collapse to **Duo / Night Owl** + *Use device appearance*. `static/js/theme.js` still runs pre-paint, persists `la-theme`, syncs open tabs, and **migrates** old values (`campus/ocean/parchment/mulberry/light → duo`, `midnight/dark → duo-night`). Night Owl (`#131F24` canvas) is the dark extension of the same roles; the media stage stays near-black in both.

## States
Hover (brightness/fill), focus (4px `#84D8FF` ring), active nav (soft-green pill + green outline), pressed buttons (bottom edge collapses), disabled, loading, error (red text/soft fill), empty (bordered card with a recovery action), current lesson (soft-green fill + inset green bar) — all from the same tokens. `prefers-reduced-motion` disables the press/hover transitions.

## House rules
White first · green means "go" · blue means progress/links · yellow/purple are rewards, never body text · chunky and pressable, never thin-minimal · progress must be readable before decoration · mascot supports the path, never overpowers it · no fake streaks/XP — gamify only what the library actually knows.

## Verification
`python -m unittest discover -s tests -v` · `node --check static/js/*.js` · `python demo.py --port 5000` + `python tests/browser_smoke.py` (captures Duo/Night Owl, desktop/tablet/mobile, and checks themes/search/player flows).
