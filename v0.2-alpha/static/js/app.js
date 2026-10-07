(() => {
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

  function toast(message, type = "success") {
    const region = $("#toast-region") || $("#course-toast");
    if (!region) return;
    const item = document.createElement("div");
    item.className = `toast-message ${type}`;
    item.textContent = message;
    region.append(item);
    requestAnimationFrame(() => item.classList.add("is-visible"));
    window.setTimeout(() => {
      item.classList.remove("is-visible");
      window.setTimeout(() => item.remove(), 250);
    }, 3200);
  }

  function openModal(modal) {
    if (!modal) return;
    modal.hidden = false;
    document.body.classList.add("modal-open");
    const focusable = $("input:not([type=hidden]), button, textarea, select", modal);
    window.setTimeout(() => focusable?.focus(), 40);
  }

  function closeModal(modal) {
    if (!modal) return;
    modal.hidden = true;
    if (!$$(".modal-backdrop:not([hidden])").length) document.body.classList.remove("modal-open");
  }

  function setTheme(theme) {
    document.documentElement.dataset.theme = theme;
    try { localStorage.setItem("la-theme", theme); } catch (_) { /* private browsing */ }
  }

  function createSearchResult(item, kind) {
    const link = document.createElement("a");
    link.className = "search-result";
    link.href = item.url;
    const icon = document.createElement("span");
    icon.className = `search-result-icon ${kind}`;
    icon.textContent = kind === "course" ? "▤" : (kind === "file" ? "▶" : "↗");
    const copy = document.createElement("span");
    copy.className = "search-result-copy";
    const title = document.createElement("strong");
    title.textContent = item.display_name;
    const detail = document.createElement("small");
    detail.textContent = kind === "course" ? "Course" : (item.course_name || "Lesson");
    copy.append(title, detail);
    link.append(icon, copy);
    return link;
  }

  function initGlobalSearch() {
    const input = $("#global-search-input");
    const results = $("#search-results");
    if (!input || !results) return;
    let timer = 0;
    const close = () => { results.hidden = true; };
    input.addEventListener("input", () => {
      window.clearTimeout(timer);
      const query = input.value.trim();
      if (query.length < 2) { close(); return; }
      timer = window.setTimeout(async () => {
        try {
          const response = await fetch(`/search?q=${encodeURIComponent(query)}`, { headers: { "Accept": "application/json" } });
          const data = await response.json();
          results.replaceChildren();
          const courses = data.courses || [];
          const files = data.files || [];
          if (!courses.length && !files.length) {
            const empty = document.createElement("div");
            empty.className = "search-empty";
            empty.textContent = "No matching courses or lessons";
            results.append(empty);
          } else {
            if (courses.length) {
              const heading = document.createElement("p");
              heading.className = "search-group-label";
              heading.textContent = "COURSES";
              results.append(heading, ...courses.map(item => createSearchResult(item, "course")));
            }
            if (files.length) {
              const heading = document.createElement("p");
              heading.className = "search-group-label";
              heading.textContent = "LESSONS & RESOURCES";
              results.append(heading, ...files.map(item => createSearchResult(item, "file")));
            }
          }
          results.hidden = false;
        } catch (_) {
          close();
        }
      }, 180);
    });
    input.addEventListener("focus", () => { if (input.value.trim().length >= 2 && results.childElementCount) results.hidden = false; });
    document.addEventListener("click", event => { if (!event.target.closest(".global-search")) close(); });
    document.addEventListener("keydown", event => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        input.focus();
        input.select();
      }
      if (event.key === "Escape" && document.activeElement === input) {
        input.blur();
        close();
      }
    });
  }

  function initCourseImport() {
    const modal = $("#add-course-modal");
    const form = $("#add-course-form");
    if (!modal || !form) return;
    $$('[data-open-add]').forEach(button => button.addEventListener("click", () => openModal(modal)));
    $$('[data-close-modal]', modal).forEach(button => button.addEventListener("click", () => closeModal(modal)));
    modal.addEventListener("click", event => { if (event.target === modal) closeModal(modal); });
    if (!modal.hidden) openModal(modal);
    form.addEventListener("submit", async event => {
      event.preventDefault();
      const error = $("#add-course-error");
      const submit = $("button[type=submit]", form);
      const data = Object.fromEntries(new FormData(form).entries());
      if (error) { error.hidden = true; error.textContent = ""; }
      submit.disabled = true;
      submit.classList.add("is-loading");
      try {
        const response = await fetch("/courses/add", {
          method: "POST",
          headers: { "Content-Type": "application/json", "Accept": "application/json" },
          body: JSON.stringify(data),
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || "The course could not be added.");
        window.location.assign(`/courses/${result.course_id}`);
      } catch (err) {
        if (error) { error.textContent = err.message; error.hidden = false; }
        submit.disabled = false;
        submit.classList.remove("is-loading");
      }
    });
  }

  function initLibraryFilter() {
    const input = $("#course-filter");
    if (!input) return;
    const cards = $$('[data-course-card]');
    const empty = $("#filter-empty");
    const apply = () => {
      const query = input.value.trim().toLocaleLowerCase();
      let visible = 0;
      cards.forEach(card => {
        const show = (card.dataset.title || "").includes(query);
        card.hidden = !show;
        if (show) visible += 1;
      });
      if (empty) empty.hidden = visible !== 0;
    };
    input.addEventListener("input", apply);
    apply();
  }

  function initSideNav() {
    const menu = $("#mobile-menu");
    const sidebar = $("#sidebar");
    if (!menu || !sidebar) return;
    menu.addEventListener("click", () => document.body.classList.toggle("sidebar-open"));
    document.addEventListener("click", event => {
      if (document.body.classList.contains("sidebar-open") && !event.target.closest("#sidebar") && !event.target.closest("#mobile-menu")) {
        document.body.classList.remove("sidebar-open");
      }
    });
  }

  function initModals() {
    document.addEventListener("click", event => {
      const closeButton = event.target.closest("[data-close-modal]");
      if (closeButton) closeModal(closeButton.closest(".modal-backdrop"));
      if (event.target.classList?.contains("modal-backdrop")) closeModal(event.target);
    });
    document.addEventListener("keydown", event => {
      if (event.key === "Escape") {
        $$(".modal-backdrop:not([hidden])").forEach(closeModal);
        document.body.classList.remove("sidebar-open");
      }
    });
  }

  function init() {
    $("#theme-toggle")?.addEventListener("click", () => {
      setTheme(document.documentElement.dataset.theme === "light" ? "dark" : "light");
    });
    initGlobalSearch();
    initCourseImport();
    initLibraryFilter();
    initSideNav();
    initModals();
  }

  window.LocalAcademy = { toast, openModal, closeModal };
  document.addEventListener("DOMContentLoaded", init);
})();
