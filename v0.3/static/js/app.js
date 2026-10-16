(() => {
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
  let activeModal = null;
  let modalState = null;
  let closeSideNav = () => {};

  function icon(name) {
    const paths = {
      book: "M12 5c-3-2-6-2-9-1v15c3-1 6 0 9 2 3-2 6-3 9-2V4c-3-1-6-1-9 1ZM12 5v16M6 8l3 1m6 0 3-1",
      file: "M6 3h8l4 4v14H6V3ZM14 3v5h5M9 12h6M9 16h6",
      play: "m9 5 11 7-11 7V5Z",
      pause: "M7 5h3v14H7zM14 5h3v14h-3z",
      close: "m6 6 12 12M6 18 18 6",
      plus: "M12 5v14M5 12h14",
      minus: "M5 12h14",
      check: "m5 12 4.5 4.5L19 7",
      edit: "m15 5 4 4M4 20l4.5-1 11-11a2.1 2.1 0 0 0-3-3l-11 11L4 20Z",
      bookmark: "M6 4a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v17l-6-4-6 4V4Z",
    };
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.setAttribute("aria-hidden", "true");
    svg.setAttribute("focusable", "false");
    const path = document.createElementNS(svg.namespaceURI, "path");
    path.setAttribute("d", paths[name] || paths.file);
    if (name === "play" || name === "pause") {
      path.setAttribute("fill", "currentColor");
      path.setAttribute("stroke", "none");
    }
    svg.append(path);
    return svg;
  }

  function toast(message, type = "success") {
    const region = $("#toast-region");
    if (!region) return;
    if ($$(".toast-message", region).some(item => item.textContent === message)) return;
    const item = document.createElement("div");
    item.className = `toast-message ${type}`;
    item.textContent = message;
    if (type === "error") item.setAttribute("role", "alert");
    while (region.childElementCount >= 4) region.firstElementChild.remove();
    region.append(item);
    requestAnimationFrame(() => item.classList.add("is-visible"));
    window.setTimeout(() => {
      item.classList.remove("is-visible");
      window.setTimeout(() => item.remove(), 250);
    }, type === "error" ? 7000 : 4000);
  }

  function focusableElements(root) {
    return $$('a[href], button:not(:disabled), input:not(:disabled):not([type="hidden"]), textarea:not(:disabled), select:not(:disabled), summary, [tabindex]:not([tabindex="-1"])', root)
      .filter(item => item.getClientRects().length && !item.closest("[inert]"));
  }

  function trapFocus(event, root) {
    if (event.key !== "Tab") return;
    const items = focusableElements(root);
    if (!items.length) { event.preventDefault(); root.focus(); return; }
    const first = items[0];
    const last = items.at(-1);
    if (event.shiftKey && (document.activeElement === first || !root.contains(document.activeElement))) {
      event.preventDefault(); last.focus();
    } else if (!event.shiftKey && (document.activeElement === last || !root.contains(document.activeElement))) {
      event.preventDefault(); first.focus();
    }
  }

  function openModal(modal) {
    if (!modal || activeModal === modal) return;
    closeSideNav();
    if (activeModal) closeModal(activeModal, false);
    const previousFocus = document.activeElement;
    const inert = [];
    // Dialogs live inside their routes. Disable siblings at each level, not the
    // whole app shell (which would also disable the dialog itself).
    let branch = modal;
    while (branch.parentElement && branch !== document.body) {
      for (const sibling of branch.parentElement.children) {
        if (sibling === branch || ["SCRIPT", "STYLE", "LINK"].includes(sibling.tagName) || sibling.id === "toast-region") continue;
        inert.push([sibling, sibling.inert]);
        sibling.inert = true;
      }
      branch = branch.parentElement;
    }
    modal.hidden = false;
    activeModal = modal;
    modalState = { previousFocus, inert };
    document.body.classList.add("modal-open");
    const target = $('[autofocus]', modal) || $('input:not([type="hidden"]):not(:disabled), textarea:not(:disabled), select:not(:disabled)', modal) || $('button:not(:disabled)', modal) || $('[role="dialog"]', modal);
    target?.focus();
  }

  function closeModal(modal, restoreFocus = true) {
    if (!modal) return;
    if (modal.getAttribute("aria-busy") === "true") return;
    modal.hidden = true;
    if (activeModal === modal) {
      const state = modalState;
      for (const [element, wasInert] of state?.inert || []) element.inert = wasInert;
      activeModal = null;
      modalState = null;
      document.body.classList.remove("modal-open");
      if (restoreFocus && state?.previousFocus?.isConnected) state.previousFocus.focus();
    }
    modal.dispatchEvent(new CustomEvent("la:modal-closed"));
  }

  function actionDialog({ title, message, confirmLabel = "Continue", danger = false, value = null, inputLabel = "Name", maxLength = 255 }) {
    return new Promise(resolve => {
      const modal = document.createElement("div");
      modal.className = "modal-backdrop";
      modal.hidden = true;
      const dialog = document.createElement("section");
      dialog.className = "modal-card modal-compact";
      dialog.setAttribute("role", "dialog");
      dialog.setAttribute("aria-modal", "true");
      dialog.tabIndex = -1;
      const id = `action-dialog-${Date.now()}`;
      dialog.setAttribute("aria-labelledby", `${id}-title`);
      dialog.setAttribute("aria-describedby", `${id}-copy`);
      const heading = document.createElement("div");
      heading.className = "modal-heading";
      const headingText = document.createElement("h2");
      headingText.id = `${id}-title`;
      headingText.textContent = title;
      const close = document.createElement("button");
      close.type = "button";
      close.className = "icon-button";
      close.dataset.closeModal = "";
      close.setAttribute("aria-label", "Close");
      close.append(icon("close"));
      heading.append(headingText, close);
      const copy = document.createElement("p");
      copy.id = `${id}-copy`;
      copy.className = "confirm-copy";
      copy.textContent = message;
      const form = document.createElement("form");
      form.className = "form-stack";
      let input;
      if (value !== null) {
        const label = document.createElement("label");
        label.textContent = inputLabel;
        input = document.createElement("input");
        input.value = value;
        input.required = true;
        input.maxLength = maxLength;
        label.append(input);
        form.append(label);
      }
      const actions = document.createElement("div");
      actions.className = "modal-actions";
      const cancel = document.createElement("button");
      cancel.type = "button";
      cancel.className = "button button-secondary";
      cancel.dataset.closeModal = "";
      cancel.textContent = "Cancel";
      const confirm = document.createElement("button");
      confirm.type = "submit";
      confirm.className = `button ${danger ? "button-danger" : "button-primary"}`;
      confirm.textContent = confirmLabel;
      actions.append(cancel, confirm);
      form.append(actions);
      dialog.append(heading, copy, form);
      modal.append(dialog);
      document.body.append(modal);
      let answer = value === null ? false : null;
      modal.addEventListener("la:modal-closed", () => { modal.remove(); resolve(answer); }, { once: true });
      form.addEventListener("submit", event => {
        event.preventDefault();
        if (input && !input.value.trim()) { input.setCustomValidity("Enter a name."); input.reportValidity(); return; }
        answer = input ? input.value.trim() : true;
        closeModal(modal);
      });
      input?.addEventListener("input", () => input.setCustomValidity(""));
      openModal(modal);
      if (input) { input.focus(); input.select(); } else cancel.focus();
    });
  }

  function createSearchResult(item, kind) {
    const link = document.createElement("a");
    link.className = "search-result";
    link.href = item.url;
    const mark = document.createElement("span");
    mark.className = "search-result-icon";
    mark.append(icon(kind === "course" ? "book" : "file"));
    const copy = document.createElement("span");
    copy.className = "search-result-copy";
    const title = document.createElement("strong");
    title.textContent = item.display_name;
    const detail = document.createElement("small");
    detail.textContent = kind === "course" ? "Course" : (item.course_name || "Lesson");
    copy.append(title, detail);
    link.append(mark, copy);
    return link;
  }

  function initGlobalSearch() {
    const input = $("#global-search-input");
    const results = $("#search-results");
    const mobileButton = $("#mobile-search");
    if (!input || !results) return;
    let timer;
    let requestId = 0;
    let controller;
    let resultQuery = "";
    const status = $("#search-status");
    const close = () => { results.hidden = true; if (status) status.textContent = ""; };
    const show = () => { results.hidden = false; };
    const openSearch = () => {
      if (matchMedia("(max-width: 760px)").matches) {
        document.body.classList.add("search-open");
        mobileButton?.setAttribute("aria-expanded", "true");
      }
      input.focus();
    };
    const closeSearch = () => {
      clearTimeout(timer);
      ++requestId;
      controller?.abort();
      close();
      document.body.classList.remove("search-open");
      mobileButton?.setAttribute("aria-expanded", "false");
    };
    mobileButton?.addEventListener("click", () => {
      if (document.body.classList.contains("search-open")) { closeSearch(); mobileButton.focus(); }
      else openSearch();
    });
    const shortcut = $("[data-search-shortcut]");
    if (shortcut) shortcut.textContent = /Mac|iPhone|iPad/.test(navigator.platform) ? "⌘ K" : "Ctrl K";
    input.addEventListener("input", () => {
      clearTimeout(timer);
      controller?.abort();
      const id = ++requestId;
      const query = input.value.trim();
      resultQuery = "";
      close();
      if (query.length < 2) { results.replaceChildren(); return; }
      timer = setTimeout(async () => {
        controller = new AbortController();
        try {
          const response = await fetch(`/search?q=${encodeURIComponent(query)}`, { headers: { Accept: "application/json" }, signal: controller.signal });
          if (!response.ok) throw new Error("Search unavailable");
          const data = await response.json();
          if (id !== requestId || input.value.trim() !== query) return;
          results.replaceChildren();
          const courses = data.courses || [];
          const files = data.files || [];
          if (!courses.length && !files.length) {
            const empty = document.createElement("div");
            empty.className = "search-empty";
            empty.textContent = "No matching courses or lessons. Try another search.";
            results.append(empty);
          } else {
            for (const [items, kind, label] of [[courses, "course", "Courses"], [files, "file", "Lessons & resources"]]) {
              if (!items.length) continue;
              const heading = document.createElement("p");
              heading.className = "search-group-label";
              heading.textContent = label;
              results.append(heading, ...items.map(item => createSearchResult(item, kind)));
            }
          }
          resultQuery = query;
          if ($(".global-search").contains(document.activeElement)) {
            show();
            if (status) status.textContent = `${courses.length} matching courses and ${files.length} matching lessons.`;
          }
        } catch (error) {
          if (error.name === "AbortError" || id !== requestId) return;
          const empty = document.createElement("div");
          empty.className = "search-empty";
          empty.textContent = "Search couldn’t load. Press Enter to search your course library.";
          results.replaceChildren(empty);
          if (document.activeElement === input) show();
        }
      }, 180);
    });
    input.addEventListener("focus", () => { if (input.value.trim() === resultQuery && resultQuery && results.childElementCount) show(); });
    $(".global-search").addEventListener("keydown", event => {
      const links = $$(".search-result", results);
      if (results.hidden || !links.length) return;
      const index = links.indexOf(document.activeElement);
      if (event.key === "ArrowDown") { event.preventDefault(); links[(index + 1) % links.length].focus(); }
      if (event.key === "ArrowUp") { event.preventDefault(); if (index <= 0) input.focus(); else links[index - 1].focus(); }
    });
    document.addEventListener("click", event => { if (!event.target.closest(".global-search") && !event.target.closest("#mobile-search")) closeSearch(); });
    document.addEventListener("keydown", event => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k" && !activeModal) {
        event.preventDefault();
        if (document.body.classList.contains("theater-active")) $('[data-action="theater"]')?.click();
        closeSideNav(); openSearch(); input.select();
      }
      if (event.key === "Escape" && !activeModal && document.body.classList.contains("search-open")) {
        closeSearch(); mobileButton?.focus();
      } else if (event.key === "Escape" && $(".global-search").contains(document.activeElement)) {
        input.focus(); closeSearch();
      }
    });
  }

  function initThemes() {
    const picker = $("#theme-picker");
    $$('[data-theme-choice]').forEach(button => button.addEventListener("click", () => {
      const name = window.LATheme.apply(button.dataset.themeChoice);
      if (picker?.open && picker.contains(button)) { picker.open = false; $("summary", picker).focus(); }
      toast(`${name} theme applied.`);
    }));
    $$('[data-theme-system]').forEach(input => input.addEventListener("change", () => {
      window.LATheme.apply(input.checked ? "system" : document.documentElement.dataset.theme);
      toast(input.checked ? "Theme follows your device’s appearance." : "Theme saved for this browser.");
    }));
    picker?.addEventListener("toggle", () => $("summary", picker).setAttribute("aria-expanded", String(picker.open)));
    document.addEventListener("click", event => { if (picker?.open && !picker.contains(event.target)) picker.open = false; });
    document.addEventListener("keydown", event => {
      if (event.key === "Escape" && picker?.open) { picker.open = false; $("summary", picker).focus(); }
    });
  }

  function initCourseImport() {
    const modal = $("#add-course-modal");
    const form = $("#add-course-form");
    if (!modal || !form) return;
    $$('[data-open-add]').forEach(button => button.addEventListener("click", () => openModal(modal)));
    if (!modal.hidden) openModal(modal);
    form.addEventListener("submit", async event => {
      event.preventDefault();
      const error = $("#add-course-error");
      const submit = $('button[type="submit"]', form);
      const label = $("[data-submit-label]", submit);
      const data = Object.fromEntries(new FormData(form).entries());
      if (error) { error.hidden = true; error.textContent = ""; }
      submit.disabled = true;
      modal.setAttribute("aria-busy", "true");
      if (label) label.textContent = "Indexing your folder…";
      try {
        const response = await fetch("/courses/add", { method: "POST", headers: { "Content-Type": "application/json", Accept: "application/json" }, body: JSON.stringify(data) });
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || "The course could not be added. Check the folder path and try again.");
        window.location.assign(`/courses/${result.course_id}`);
      } catch (err) {
        if (error) { error.textContent = err.message; error.hidden = false; }
        submit.disabled = false;
        modal.removeAttribute("aria-busy");
        if (label) label.textContent = "Add to library";
      }
    });
  }

  function initLibrary() {
    const input = $("#course-filter");
    if (!input) return;
    const cards = $$('[data-course-card]');
    const empty = $("#filter-empty");
    const apply = () => {
      const query = input.value.trim().toLocaleLowerCase();
      let visible = 0;
      cards.forEach(card => {
        card.hidden = !(card.dataset.title || "").toLocaleLowerCase().includes(query);
        if (!card.hidden) visible++;
      });
      if (empty) empty.hidden = visible !== 0;
    };
    input.addEventListener("input", apply);
    $("#clear-course-filter")?.addEventListener("click", () => {
      if (new URL(location.href).searchParams.get("q")) { location.assign("/courses"); return; }
      input.value = ""; apply(); input.focus();
    });
    $$('a', $(".filter-tabs")).concat($$('a', $(".view-switch"))).forEach(link => {
      link.addEventListener("click", () => {
        const url = new URL(link.href);
        input.value.trim() ? url.searchParams.set("q", input.value.trim()) : url.searchParams.delete("q");
        link.href = url.toString();
      });
    });
    $("#library-sort")?.addEventListener("change", event => {
      const url = new URL(location.href);
      url.searchParams.set("sort", event.currentTarget.value);
      input.value.trim() ? url.searchParams.set("q", input.value.trim()) : url.searchParams.delete("q");
      location.assign(url.toString());
    });
    apply();
  }

  function initSideNav() {
    const menu = $("#mobile-menu");
    const sidebar = $("#sidebar");
    const scrim = $("#sidebar-scrim");
    const main = $(".app-main");
    if (!menu || !sidebar) return;
    const mobile = matchMedia("(max-width: 960px)");
    let wasInert = false;
    const close = (restore = true) => {
      const wasOpen = document.body.classList.contains("sidebar-open");
      document.body.classList.remove("sidebar-open");
      if (scrim) scrim.hidden = true;
      menu.setAttribute("aria-expanded", "false");
      menu.setAttribute("aria-label", "Open navigation");
      sidebar.inert = mobile.matches;
      if (wasOpen) { main.inert = wasInert; if (restore && mobile.matches) menu.focus(); }
    };
    closeSideNav = () => close(false);
    menu.addEventListener("click", () => {
      if (document.body.classList.contains("sidebar-open")) { close(); return; }
      wasInert = main.inert;
      main.inert = true;
      sidebar.inert = false;
      document.body.classList.add("sidebar-open");
      if (scrim) scrim.hidden = false;
      menu.setAttribute("aria-expanded", "true");
      menu.setAttribute("aria-label", "Close navigation");
      $("#sidebar-close")?.focus();
    });
    $("#sidebar-close")?.addEventListener("click", () => close());
    scrim?.addEventListener("click", () => close());
    mobile.addEventListener("change", () => close(false));
    document.addEventListener("keydown", event => {
      if (!document.body.classList.contains("sidebar-open")) return;
      if (event.key === "Escape") { event.preventDefault(); close(); }
      trapFocus(event, sidebar);
    });
    close(false);
  }

  function initModals() {
    document.addEventListener("click", event => {
      const closeButton = event.target.closest("[data-close-modal]");
      if (closeButton) closeModal(closeButton.closest(".modal-backdrop, .note-composer"));
      if (event.target.classList?.contains("modal-backdrop")) closeModal(event.target);
    });
    document.addEventListener("keydown", event => {
      if (!activeModal) return;
      if (event.key === "Escape") { event.preventDefault(); closeModal(activeModal); }
      trapFocus(event, activeModal);
    });
  }

  function initSettingsNav() {
    const links = $$(".settings-nav a");
    if (!links.length || !("IntersectionObserver" in window)) return;
    const observer = new IntersectionObserver(entries => {
      const entry = entries.find(item => item.isIntersecting);
      if (!entry) return;
      links.forEach(link => link.classList.toggle("is-active", link.hash === `#${entry.target.id}`));
    }, { rootMargin: "-100px 0px -55% 0px", threshold: 0 });
    links.forEach(link => { const target = $(link.hash); if (target) observer.observe(target); });
  }

  window.LocalAcademy = {
    toast, icon, openModal, closeModal,
    confirm: options => actionDialog(options),
    prompt: options => actionDialog({ ...options, value: options.value ?? "" }),
  };
  document.addEventListener("DOMContentLoaded", () => {
    initSideNav(); initModals(); initThemes(); initGlobalSearch(); initCourseImport(); initLibrary(); initSettingsNav();
  });
})();
