/* Apply the saved palette before CSS paints. All assets remain local. */
(() => {
  const themes = {
    campus: { name: "Campus", color: "#f7f9f6", mode: "light" },
    ocean: { name: "Ocean", color: "#f5f8fc", mode: "light" },
    parchment: { name: "Parchment", color: "#faf7f0", mode: "light" },
    mulberry: { name: "Mulberry", color: "#faf6f9", mode: "light" },
    midnight: { name: "Midnight", color: "#141d23", mode: "dark" },
  };
  const aliases = { light: "campus", dark: "midnight" };
  const media = window.matchMedia("(prefers-color-scheme: dark)");
  let preference = "campus";

  function normalize(value) {
    value = aliases[value] || value;
    return value === "system" || Object.hasOwn(themes, value) ? value : "campus";
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
    const active = preference === "system" ? (media.matches ? "midnight" : "campus") : preference;
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

  try { preference = normalize(localStorage.getItem("la-theme")); } catch (_) { /* Default to the daylight campus palette. */ }
  apply(preference, false);
  media.addEventListener("change", () => { if (preference === "system") apply("system", false); });
  window.addEventListener("storage", event => {
    if (event.key === "la-theme" || event.key === null) apply(event.newValue || "campus", false);
  });
  document.addEventListener("DOMContentLoaded", syncControls);
  window.LATheme = { apply, themes, getPreference: () => preference };
})();
