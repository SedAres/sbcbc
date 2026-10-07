(() => {
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

  function initRangeOutputs() {
    $$('[data-setting-range]').forEach(input => {
      const output = input.parentElement.querySelector('[data-range-output]');
      const update = () => {
        if (!output) return;
        const unit = input.name.includes("threshold") ? " dB" : (input.name.includes("duration") ? " sec" : "");
        output.value = `${input.value}${unit}`;
        output.textContent = `${input.value}${unit}`;
      };
      input.addEventListener("input", update);
      update();
    });

    $$('[data-range-setting]').forEach(group => {
      const range = $('[data-bound-setting]', group);
      const value = $('[data-bound-value]', group);
      const output = $('[data-range-output]', group);
      if (!range || !value) return;
      const unit = value.name.includes("threshold") ? " dB" : " sec";
      const update = () => {
        value.value = range.value;
        range.dataset.override = "true";
        if (output) output.textContent = `${range.value}${unit}`;
      };
      range.addEventListener("input", update);
      group.querySelector('[data-inherit-setting]')?.addEventListener("click", () => {
        range.value = range.dataset.default || range.value;
        value.value = "";
        range.dataset.override = "false";
        if (output) output.textContent = `Global (${range.value}${unit})`;
      });
    });
  }

  function readForm(form) {
    const data = {};
    for (const [key, value] of new FormData(form).entries()) data[key] = value;
    $$('input[type="checkbox"][name]', form).forEach(input => { data[input.name] = input.checked; });
    const hotkeys = {};
    $$('[data-hotkey-action]', form).forEach(select => { hotkeys[select.dataset.hotkeyAction] = select.value; });
    if (Object.keys(hotkeys).length) data.hotkeys = hotkeys;
    return data;
  }

  function initGlobalSettings() {
    const form = $("#global-settings-form");
    if (!form) return;
    const error = $("#settings-error");
    const status = $("#settings-save-status");
    const submit = $('button[type="submit"]', form);
    form.addEventListener("submit", async event => {
      event.preventDefault();
      submit.disabled = true;
      if (error) error.hidden = true;
      if (status) status.textContent = "Saving your preferences…";
      try {
        const response = await fetch("/settings/update", {
          method: "POST",
          headers: { "Content-Type": "application/json", "Accept": "application/json" },
          body: JSON.stringify(readForm(form)),
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || "Could not save preferences.");
        if (status) status.textContent = "Preferences saved just now.";
        window.LocalAcademy?.toast("Your preferences have been saved.");
        $$('[data-range-output]', form).forEach(output => {
          const range = output.parentElement.querySelector('input[type="range"]');
          if (range) {
            const unit = range.name.includes("threshold") ? " dB" : (range.name.includes("duration") ? " sec" : "");
            output.textContent = `${range.value}${unit}`;
          }
        });
      } catch (err) {
        if (error) { error.textContent = err.message; error.hidden = false; }
        if (status) status.textContent = "Could not save changes.";
      } finally {
        submit.disabled = false;
      }
    });
    form.addEventListener("change", event => {
      const toggle = event.target.closest('.switch-control input[type="checkbox"]');
      if (toggle) {
        const label = toggle.parentElement.querySelector("b");
        if (label) {
          label.textContent = toggle.name === "rtl_enabled" ? (toggle.checked ? "RTL" : "LTR") : (toggle.checked ? "On" : "Off");
        }
      }
      if (status) status.textContent = "You have unsaved changes.";
    });

    $("#reset-settings")?.addEventListener("click", async event => {
      const button = event.currentTarget;
      if (!window.confirm("Reset playback preferences? Courses, notes, bookmarks, and progress will stay untouched.")) return;
      button.disabled = true;
      try {
        const response = await fetch("/settings/reset", { method: "POST", headers: { "Accept": "application/json" } });
        if (!response.ok) throw new Error("Could not reset preferences.");
        window.location.reload();
      } catch (err) {
        window.LocalAcademy?.toast(err.message, "error");
        button.disabled = false;
      }
    });
  }

  function initCourseSettings() {
    const form = $("#course-settings-form");
    if (!form) return;
    const courseId = form.dataset.courseId;
    const error = $("#course-settings-error");
    form.addEventListener("submit", async event => {
      event.preventDefault();
      const button = $('button[type="submit"]', form);
      button.disabled = true;
      if (error) error.hidden = true;
      try {
        const response = await fetch(`/settings/course/${courseId}`, {
          method: "POST",
          headers: { "Content-Type": "application/json", "Accept": "application/json" },
          body: JSON.stringify(readForm(form)),
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || "Could not save course settings.");
        window.LocalAcademy?.toast("Course settings saved.");
      } catch (err) {
        if (error) { error.textContent = err.message; error.hidden = false; }
      } finally {
        button.disabled = false;
      }
    });
    $("#reset-course-settings")?.addEventListener("click", async event => {
      if (!window.confirm("Remove all overrides and use your global defaults for this course?")) return;
      const button = event.currentTarget;
      button.disabled = true;
      try {
        const response = await fetch(`/settings/course/${courseId}/reset`, { method: "POST" });
        if (!response.ok) throw new Error("Could not reset course settings.");
        window.location.reload();
      } catch (err) {
        window.LocalAcademy?.toast(err.message, "error");
        button.disabled = false;
      }
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    initRangeOutputs();
    initGlobalSettings();
    initCourseSettings();
  });
})();
