/* ClipForge — job detail page logic */
(() => {
    const jobId = document.body.dataset.jobId;
    const state = { job: null, pollTimer: null };

    /* ---- DOM refs ---- */
    const titleEl = document.getElementById("job-title");
    const subEl = document.getElementById("job-sub");
    const statusEl = document.getElementById("job-status");
    const phaseEl = document.getElementById("job-phase");
    const progressEl = document.getElementById("job-progress");
    const fillEl = document.getElementById("progress-fill");
    const thumbEl = document.getElementById("job-thumb");
    const deleteBtn = document.getElementById("delete-job");
    const candSection = document.getElementById("candidates-section");
    const candList = document.getElementById("cand-list");
    const candCount = document.getElementById("cand-count");
    const bulkStyle = document.getElementById("bulk-style");
    const selectTop3 = document.getElementById("select-top-3");
    const selectAllBtn = document.getElementById("select-all");
    const renderBtn = document.getElementById("render-btn");
    const renderCount = document.getElementById("render-count");
    const renderedSection = document.getElementById("rendered-section");
    const renderedList = document.getElementById("rendered-list");
    const logPre = document.getElementById("log-pre");
    const modal = document.getElementById("player-modal");
    const modalVideo = document.getElementById("modal-video");
    const modalMeta = document.getElementById("modal-meta");
    const modalClose = document.getElementById("modal-close");

    function fmtDuration(seconds) {
        if (!seconds) return "0:00";
        const m = Math.floor(seconds / 60);
        const s = Math.floor(seconds % 60);
        return `${m}:${String(s).padStart(2, "0")}`;
    }
    function fmtTime(seconds) {
        if (!seconds) return "0:00";
        const m = Math.floor(seconds / 60);
        const s = Math.floor(seconds % 60);
        return `${m}:${String(s).padStart(2, "0")}`;
    }
    function escapeHtml(s) {
        return String(s || "")
            .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
    }
    function scoreClass(score) {
        if (score >= 70) return "high";
        if (score >= 50) return "mid";
        return "low";
    }

    /* ---- polling ---- */
    async function fetchJob() {
        try {
            const resp = await fetch(`/api/jobs/${jobId}`);
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            state.job = await resp.json();
            render();
        } catch (err) {
            phaseEl.textContent = `Error: ${err.message}`;
        }
    }
    async function fetchLog() {
        try {
            const resp = await fetch(`/api/jobs/${jobId}/log`);
            if (resp.ok) {
                const txt = await resp.text();
                logPre.textContent = txt || "(no log yet)";
                logPre.scrollTop = logPre.scrollHeight;
            }
        } catch {}
    }

    function render() {
        const j = state.job;
        if (!j) return;
        titleEl.textContent = j.source_title || (j.source_kind === "upload" ? "Uploaded video" : "YouTube video");
        const dur = j.source_duration ? ` · ${fmtDuration(j.source_duration)}` : "";
        const ch = j.source_channel ? `${j.source_channel}` : "";
        subEl.textContent = `${ch}${dur}`;
        statusEl.textContent = j.status;
        statusEl.className = `status-pill ${j.status}`;
        phaseEl.textContent = j.phase || "";
        progressEl.textContent = `${j.progress || 0}%`;
        fillEl.style.width = `${j.progress || 0}%`;
        if (j.source_thumbnail) thumbEl.style.backgroundImage = `url('${j.source_thumbnail}')`;

        if (j.status === "ready" || j.status === "rendering" || j.status === "completed") {
            candSection.hidden = false;
            renderCandidates();
        }
        if (j.status === "rendering" || j.status === "completed") {
            renderedSection.hidden = false;
            renderRendered();
        }
        if (j.status === "failed" && j.error) {
            phaseEl.textContent = `Failed: ${j.error}`;
        }
    }

    function renderCandidates() {
        const j = state.job;
        if (!j.candidates || j.candidates.length === 0) {
            candList.innerHTML = `<p class="empty">No viral candidates passed the minimum score. Try lowering the minimum score in the home page form.</p>`;
            candCount.textContent = "(0)";
            renderBtn.disabled = true;
            return;
        }
        candCount.textContent = `(${j.candidates.length})`;
        candList.innerHTML = j.candidates.map((c) => {
            const cls = scoreClass(c.score);
            const styles = ["hormozi","mrbeast","karaoke","minimal","bounce","classic"];
            const styleOpts = styles.map(s =>
                `<option value="${s}" ${s === (c.caption_style || "hormozi") ? "selected" : ""}>${s}</option>`
            ).join("");
            return `
            <div class="cand" data-id="${c.id}">
                <div class="check" data-id="${c.id}"></div>
                <div class="info">
                    <h3>${escapeHtml(c.title)}</h3>
                    <p class="hook">"${escapeHtml(c.hook_sentence || "")}"</p>
                    <p class="reason">${escapeHtml(c.virality_reason || "")}</p>
                    <p class="snippet">${escapeHtml(c.snippet || "")}</p>
                </div>
                <div>
                    <div class="time">${fmtTime(c.start)} → ${fmtTime(c.end)}</div>
                    <div class="duration">${fmtTime(c.duration)} · ${c.render_status || "pending"}</div>
                </div>
                <div class="score ${cls}">
                    <div class="num">${c.score}</div>
                    <div class="label">success rate</div>
                    <select class="style" data-id="${c.id}" style="margin-top:0.4rem">${styleOpts}</select>
                </div>
            </div>`;
        }).join("");

        candList.querySelectorAll(".check").forEach((el) => {
            el.addEventListener("click", (e) => {
                e.stopPropagation();
                const card = el.closest(".cand");
                card.classList.toggle("selected");
                updateRenderCount();
            });
        });
        candList.querySelectorAll(".style").forEach((el) => {
            el.addEventListener("click", (e) => e.stopPropagation());
            el.addEventListener("change", async (e) => {
                const id = el.dataset.id;
                const cand = j.candidates.find((c) => c.id === id);
                if (cand) {
                    cand.caption_style = el.value;
                    // Save back to server
                    await fetch(`/api/jobs/${jobId}/render`, {
                        method: "POST",
                        headers: {"Content-Type": "application/json"},
                        body: JSON.stringify({candidate_ids: [], settings: {}}),
                    }).catch(() => {});
                }
            });
        });
        candList.querySelectorAll(".cand").forEach((el) => {
            el.addEventListener("click", () => el.querySelector(".check").click());
        });
        updateRenderCount();
    }

    function updateRenderCount() {
        const n = candList.querySelectorAll(".cand.selected").length;
        renderCount.textContent = n;
        renderBtn.disabled = n === 0 || state.job?.status === "rendering";
    }

    function renderRendered() {
        const j = state.job;
        const done = (j.candidates || []).filter((c) => c.captioned_clip_path || c.rendered_clip_path);
        if (done.length === 0) {
            renderedList.innerHTML = `<p class="empty">No clips rendered yet.</p>`;
            return;
        }
        renderedList.innerHTML = done.map((c) => {
            const dlUrl = `/api/jobs/${jobId}/clips/${c.id}/download?captioned=true`;
            const prevUrl = `/api/jobs/${jobId}/clips/${c.id}/preview?captioned=true`;
            const noCapDl = `/api/jobs/${jobId}/clips/${c.id}/download?captioned=false`;
            return `
            <div class="rendered-item">
                <video src="${prevUrl}" controls muted playsinline preload="metadata"></video>
                <div class="title">${escapeHtml(c.title)}</div>
                <div class="muted">${c.caption_style || "hormozi"} captions · ${fmtTime(c.duration)}</div>
                <div class="row">
                    <a class="download" href="${dlUrl}" download>⬇ Download MP4</a>
                </div>
                <div class="row">
                    <a class="preview-btn" href="${prevUrl}" target="_blank">Open in new tab</a>
                    <a class="preview-btn" href="${noCapDl}" download>Without captions</a>
                </div>
            </div>`;
        }).join("");
    }

    /* ---- actions ---- */
    selectTop3.addEventListener("click", () => {
        candList.querySelectorAll(".cand").forEach((el, idx) => {
            el.classList.toggle("selected", idx < 3);
        });
        updateRenderCount();
    });
    selectAllBtn.addEventListener("click", () => {
        const all = candList.querySelectorAll(".cand").length;
        const sel = candList.querySelectorAll(".cand.selected").length;
        const shouldSelect = sel < all;
        candList.querySelectorAll(".cand").forEach((el) => {
            el.classList.toggle("selected", shouldSelect);
        });
        updateRenderCount();
    });
    bulkStyle.addEventListener("change", () => {
        const v = bulkStyle.value;
        if (!v) return;
        candList.querySelectorAll(".cand .style").forEach((sel) => {
            sel.value = v;
            const id = sel.dataset.id;
            const cand = state.job.candidates.find((c) => c.id === id);
            if (cand) cand.caption_style = v;
        });
        bulkStyle.value = "";
    });
    renderBtn.addEventListener("click", async () => {
        const ids = [...candList.querySelectorAll(".cand.selected")].map((el) => el.dataset.id);
        if (ids.length === 0) return;
        renderBtn.disabled = true;
        renderBtn.textContent = "Rendering…";
        try {
            const resp = await fetch(`/api/jobs/${jobId}/render`, {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({candidate_ids: ids}),
            });
            if (!resp.ok) throw new Error(await resp.text());
        } catch (err) {
            alert(`Render failed to start: ${err.message}`);
            renderBtn.disabled = false;
        }
    });
    deleteBtn.addEventListener("click", async () => {
        if (!confirm("Delete this job and all its files? This cannot be undone.")) return;
        await fetch(`/api/jobs/${jobId}`, { method: "DELETE" });
        window.location.href = "/";
    });

    /* ---- modal ---- */
    modalClose.addEventListener("click", () => {
        modal.classList.add("hidden");
        modalVideo.pause();
        modalVideo.removeAttribute("src");
    });
    modal.addEventListener("click", (e) => {
        if (e.target === modal) modalClose.click();
    });

    /* ---- start polling ---- */
    fetchJob();
    fetchLog();
    state.pollTimer = setInterval(() => {
        fetchJob();
        fetchLog();
    }, 2000);
    if (state.job && state.job.status === "completed") {
        clearInterval(state.pollTimer);
    }
    // Stop polling once completed
    const origFetch = fetchJob;
    const checkDone = setInterval(() => {
        if (state.job && (state.job.status === "completed" || state.job.status === "failed")) {
            clearInterval(state.pollTimer);
            clearInterval(checkDone);
        }
    }, 3000);
})();
