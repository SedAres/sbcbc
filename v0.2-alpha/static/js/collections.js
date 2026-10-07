(() => {
  const $ = (selector, root = document) => root.querySelector(selector);

  function init() {
    const modal = $("#collection-modal");
    const form = $("#collection-form");
    if (!modal || !form) return;
    $("[data-open-collection-modal]")?.addEventListener("click", () => window.LocalAcademy?.openModal(modal));
    form.addEventListener("submit", async event => {
      event.preventDefault();
      const submit = $('button[type="submit"]', form);
      const errorBox = $("#collection-error");
      const data = Object.fromEntries(new FormData(form).entries());
      if (errorBox) errorBox.hidden = true;
      submit.disabled = true;
      try {
        const response = await fetch(`/api/taxonomy/${encodeURIComponent(data.kind)}`, {
          method: "POST",
          headers: { "Content-Type": "application/json", "Accept": "application/json" },
          body: JSON.stringify({ name: data.name }),
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || "Could not create the collection.");
        location.reload();
      } catch (error) {
        if (errorBox) { errorBox.textContent = error.message; errorBox.hidden = false; }
        submit.disabled = false;
      }
    });
  }
  document.addEventListener("DOMContentLoaded", init);
})();
