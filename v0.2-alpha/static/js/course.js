(() => {
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
  const courseId = location.pathname.split("/").filter(Boolean).pop();

  function notify(message, kind = "success") {
    if (window.LocalAcademy?.toast) window.LocalAcademy.toast(message, kind);
    else alert(message);
  }

  function openEdit() {
    const modal = $("#edit-course-modal");
    window.LocalAcademy?.openModal(modal);
  }

  async function rescan(button) {
    if (!window.confirm("Scan this course folder for new, moved, or removed files?")) return;
    button.disabled = true;
    const original = button.innerHTML;
    button.classList.add("is-loading");
    try {
      const response = await fetch(`/courses/${courseId}/rescan`, { method: "POST", headers: { "Accept": "application/json" } });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || "The folder could not be scanned.");
      notify(`Scan complete · ${result.files_count} files in this course.`);
      window.setTimeout(() => location.reload(), 450);
    } catch (error) {
      notify(error.message, "error");
      button.disabled = false;
      button.classList.remove("is-loading");
      button.innerHTML = original;
    }
  }

  function init() {
    $$('[data-edit-course]').forEach(button => button.addEventListener("click", openEdit));
    $$('[data-rescan-course]').forEach(button => button.addEventListener("click", () => rescan(button)));

    $("[data-toggle-folders]")?.addEventListener("click", event => {
      const folders = $$(".curriculum-folder");
      const shouldOpen = folders.some(folder => !folder.open);
      folders.forEach(folder => { folder.open = shouldOpen; });
      event.currentTarget.textContent = shouldOpen ? "Collapse sections" : "Expand sections";
    });

    $$('[data-mark-watched]').forEach(button => button.addEventListener("click", async event => {
      event.preventDefault();
      event.stopPropagation();
      const hash = button.dataset.markWatched;
      const completed = button.dataset.completed !== "true";
      button.disabled = true;
      try {
        const response = await fetch(`/api/mark-watched/${hash}`, {
          method: "POST",
          headers: { "Content-Type": "application/json", "Accept": "application/json" },
          body: JSON.stringify({ completed }),
        });
        if (!response.ok) throw new Error("Could not update lesson progress.");
        button.dataset.completed = String(completed);
        button.title = completed ? "Mark incomplete" : "Mark complete";
        button.setAttribute("aria-label", button.title);
        button.classList.toggle("is-complete", completed);
        const row = button.closest(".lesson-row");
        row?.classList.toggle("is-completed", completed);
        const check = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        check.setAttribute("viewBox", "0 0 24 24");
        const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        path.setAttribute("d", completed ? "m5 12 4.5 4.5L19 7" : "M12 3.5a8.5 8.5 0 1 0 0 17 8.5 8.5 0 0 0 0-17Zm-4 8.5 2.6 2.6L16 9");
        check.append(path);
        button.replaceChildren(check);
        notify(completed ? "Lesson marked complete." : "Lesson marked incomplete.");
      } catch (error) {
        notify(error.message, "error");
      } finally {
        button.disabled = false;
      }
    }));

    $$('[data-rename-file]').forEach(button => button.addEventListener("click", async event => {
      event.preventDefault();
      event.stopPropagation();
      const name = window.prompt("Lesson display name", button.dataset.oldName || "");
      if (name === null || !name.trim()) return;
      try {
        const response = await fetch(`/api/rename/${button.dataset.renameFile}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ display_name: name.trim() }),
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || "Could not rename this lesson.");
        notify("Lesson name updated.");
        window.setTimeout(() => location.reload(), 350);
      } catch (error) { notify(error.message, "error"); }
    }));

    $("[data-delete-course]")?.addEventListener("click", async event => {
      if (!window.confirm("Remove this course from LocalAcademy? The files in its folder will not be deleted, but course progress and notes will be removed.")) return;
      const button = event.currentTarget;
      button.disabled = true;
      try {
        const response = await fetch(`/courses/${courseId}/delete`, { method: "POST", headers: { "Accept": "application/json" } });
        if (!response.ok) throw new Error("Could not remove this course.");
        location.assign("/courses");
      } catch (error) {
        notify(error.message, "error");
        button.disabled = false;
      }
    });

    const form = $("#edit-course-form");
    form?.addEventListener("submit", async event => {
      event.preventDefault();
      const submit = $('button[type="submit"]', form);
      const errorBox = $("#edit-course-error");
      const data = Object.fromEntries(new FormData(form).entries());
      submit.disabled = true;
      if (errorBox) errorBox.hidden = true;
      try {
        const response = await fetch(`/courses/${form.dataset.courseId}/metadata`, {
          method: "POST",
          headers: { "Content-Type": "application/json", "Accept": "application/json" },
          body: JSON.stringify(data),
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || "Could not save course details.");
        window.LocalAcademy?.closeModal($("#edit-course-modal"));
        notify("Course details saved.");
        window.setTimeout(() => location.reload(), 350);
      } catch (error) {
        if (errorBox) { errorBox.textContent = error.message; errorBox.hidden = false; }
        submit.disabled = false;
      }
    });

    const uploadButton = $("#upload-course-thumbnail");
    const uploadInput = $("#course-thumbnail-file");
    uploadButton?.addEventListener("click", () => uploadInput?.click());
    uploadInput?.addEventListener("change", async () => {
      const file = uploadInput.files?.[0];
      if (!file) return;
      const formData = new FormData();
      formData.append("file", file);
      uploadButton.disabled = true;
      try {
        const response = await fetch("/upload/image", { method: "POST", body: formData });
        const result = await response.json();
        if (!response.ok || !result.url) throw new Error(result.error || "Image upload failed.");
        $("#course-thumbnail").value = result.url;
        notify("Cover uploaded. Save course details to apply it.");
      } catch (error) { notify(error.message, "error"); }
      finally { uploadButton.disabled = false; uploadInput.value = ""; }
    });
  }

  document.addEventListener("DOMContentLoaded", init);
})();
