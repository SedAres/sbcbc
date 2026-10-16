/* Apply the saved appearance before CSS paints. All assets remain local.
   v0.3 ships the Duolingo-style "duo" (light) design plus its "duo-night"
   dark extension. Saved v0.1/v0.2 preferences migrate: every old light
   palette -> duo, old dark palettes -> duo-night. */
(() => {
  const themes = {
    duo: { name: "Duo", color: "#ffffff", mode: "light" },
    "duo-night": { name: "Night Owl", color: "#131f24", mode: "dark" },
  };
  const aliases = {
    light: "duo", campus: "duo", ocean: "duo", parchment: "duo", mulberry: "duo",
    dark: "duo-night", midnight: "duo-night",
  };
  const media = window.matchMedia("(prefers-color-scheme: dark)");
  let preference = "duo";

  function normalize(value) {
    value = aliases[value] || value;
    return value === "system" || Object.hasOwn(themes, value) ? value : "duo";
  }

  function syncControls() {
    const active = document.documentElement.dataset.theme;
    document.querySelectorAll("[data-theme-choice]").forEach(button => {
      button.setAttribute("aria-pressed", String(button.dataset.themeChoice === active));
    });
    document.querySelectorAll("[data-theme-system]").forEach(input => { input.checked = preference === "system"; });
    document.querySelectorAll("[data-current-theme-name]").forEach(label => { label.textContent = themes[active].name; });
  }

  function apply(value, persist = true) {
    preference = normalize(value);
    const active = preference === "system" ? (media.matches ? "duo-night" : "duo") : preference;
    document.documentElement.dataset.theme = active;
    document.documentElement.dataset.themePreference = preference;
    document.documentElement.style.colorScheme = themes[active].mode;
    document.querySelector('meta[name="theme-color"]')?.setAttribute("content", themes[active].color);
    if (persist) {
      try { localStorage.setItem("la-theme", preference); } catch (_) { /* Works for this page when storage is unavailable. */ }
    }
    syncControls();
    return themes[active].name;
  }

  try { preference = normalize(localStorage.getItem("la-theme")); } catch (_) { /* Default to the bright Duo palette. */ }
  apply(preference, false);
  media.addEventListener("change", () => { if (preference === "system") apply("system", false); });
  window.addEventListener("storage", event => {
    if (event.key === "la-theme" || event.key === null) apply(event.newValue || "duo", false);
  });
  document.addEventListener("DOMContentLoaded", syncControls);
  window.LATheme = { apply, themes, getPreference: () => preference };
})();
