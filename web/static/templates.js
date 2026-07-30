/* ClipForge — templates page */
(() => {
    const grid = document.getElementById("tpl-grid");
    fetch("/api/templates")
        .then((r) => r.json())
        .then((data) => {
            if (!data.templates || data.templates.length === 0) {
                grid.innerHTML = `<p class="empty">No templates available.</p>`;
                return;
            }
            grid.innerHTML = data.templates.map((t) => `
                <div class="tpl-card" data-id="${t.id}">
                    <h3>${t.name}</h3>
                    <p class="desc">${t.description}</p>
                    <div class="chips">
                        <span class="chip">📐 ${t.settings.aspect_ratio}</span>
                        <span class="chip">Aa ${t.settings.caption_style}</span>
                        <span class="chip">↑ ${t.settings.caption_position}% from bottom</span>
                    </div>
                    <button class="apply">Use this template</button>
                </div>
            `).join("");
            grid.querySelectorAll(".tpl-card").forEach((card) => {
                card.querySelector(".apply").addEventListener("click", () => {
                    // Save the chosen template in localStorage and redirect home,
                    // where the form will read it back.
                    const id = card.dataset.id;
                    const tpl = data.templates.find((t) => t.id === id);
                    if (tpl) {
                        localStorage.setItem("clipforge_template", JSON.stringify(tpl.settings));
                    }
                    window.location.href = "/";
                });
            });
        })
        .catch((err) => {
            grid.innerHTML = `<p class="empty">Couldn't load templates: ${err.message}</p>`;
        });
})();
