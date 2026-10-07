(() => {
  document.addEventListener("DOMContentLoaded", () => {
    const modal = document.querySelector("#collection-modal");
    const form = document.querySelector("#collection-form");
    if (!modal || !form) return;
    document.querySelectorAll("[data-open-collection-modal], [data-create-kind]").forEach(button => {
      button.addEventListener("click", () => {
        if (button.dataset.createKind) form.elements.kind.value = button.dataset.createKind;
        window.LocalAcademy.openModal(modal);
      });
    });
    form.addEventListener("submit", async event => {
      event.preventDefault();
      const button = form.querySelector('button[type="submit"]');
      const error = document.querySelector("#collection-error");
      const name = form.elements.name.value.trim();
      const kind = form.elements.kind.value;
      if (!name) return;
      button.disabled = true;
      error.hidden = true;
      try {
        const response = await fetch(`/api/taxonomy/${kind}`, {
          method: "POST", headers: { "Content-Type": "application/json", Accept: "application/json" },
          body: JSON.stringify({ name }),
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || "Could not create the collection. Try again.");
        location.assign(`/collections/${kind}/${result.item.id}`);
      } catch (err) {
        error.textContent = err.message;
        error.hidden = false;
        button.disabled = false;
      }
    });
  });
})();
