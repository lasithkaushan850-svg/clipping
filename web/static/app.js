/* ClipForge — index page logic */
(() => {
    const form = document.getElementById("job-form");
    const submitBtn = document.getElementById("submit-btn");
    const btnLabel = submitBtn.querySelector(".btn-label");
    const spinner = submitBtn.querySelector(".spinner");
    const errEl = document.getElementById("form-error");
    const jobsList = document.getElementById("jobs-list");
    const refreshBtn = document.getElementById("refresh-jobs");
    const historyLink = document.getElementById("nav-history");

    /* ---- tabs (YouTube / upload) ---- */
    document.querySelectorAll(".tab").forEach((tab) => {
        tab.addEventListener("click", () => {
            document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
            tab.classList.add("active");
            const target = tab.dataset.tab;
            document.querySelectorAll(".tab-panel").forEach((p) => {
                p.classList.toggle("hidden", p.dataset.panel !== target);
            });
            // toggle required attribute so the browser only validates the visible field
            document.getElementById("youtube_url").required = target === "youtube";
            document.getElementById("video").required = target === "upload";
        });
    });

    /* ---- job creation ---- */
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        errEl.textContent = "";
        const fd = new FormData(form);
        const isUpload = !document.querySelector('[data-panel="upload"]').classList.contains("hidden");
        if (isUpload && !fd.get("video").name) {
            errEl.textContent = "Please choose a video file to upload.";
            return;
        }
        submitBtn.disabled = true;
        btnLabel.textContent = isUpload ? "Uploading…" : "Starting…";
        spinner.classList.remove("hidden");
        try {
            const resp = await fetch("/api/jobs", { method: "POST", body: fd });
            if (!resp.ok) {
                const text = await resp.text();
                throw new Error(text || `HTTP ${resp.status}`);
            }
            const job = await resp.json();
            window.location.href = `/jobs/${job.job_id}`;
        } catch (err) {
            errEl.textContent = err.message || "Failed to start job";
            submitBtn.disabled = false;
            btnLabel.textContent = "Find viral moments";
            spinner.classList.add("hidden");
        }
    });

    /* ---- recent jobs ---- */
    function fmtDuration(seconds) {
        if (!seconds) return "";
        const m = Math.floor(seconds / 60);
        const s = Math.floor(seconds % 60);
        return `${m}:${String(s).padStart(2, "0")}`;
    }
    function fmtRelative(ts) {
        const d = (Date.now() / 1000) - ts;
        if (d < 60) return "just now";
        if (d < 3600) return `${Math.floor(d/60)}m ago`;
        if (d < 86400) return `${Math.floor(d/3600)}h ago`;
        return `${Math.floor(d/86400)}d ago`;
    }
    async function loadJobs() {
        try {
            const resp = await fetch("/api/jobs");
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            const data = await resp.json();
            if (!data.jobs || data.jobs.length === 0) {
                jobsList.innerHTML = `<p class="empty">No jobs yet — paste a YouTube link above to get started.</p>`;
                return;
            }
            jobsList.innerHTML = data.jobs.map((j) => {
                const thumb = j.source_thumbnail
                    ? `style="background-image:url('${j.source_thumbnail}')"`
                    : "";
                return `
                <div class="job-card" data-href="/jobs/${j.job_id}">
                    <div class="thumb" ${thumb}></div>
                    <h3>${escapeHtml(j.source_title || "(no title)")}</h3>
                    <div class="meta">
                        <span class="status-pill ${j.status}">${j.status}</span>
                        <span>${fmtDuration(j.source_duration)}</span>
                    </div>
                    <div class="meta" style="margin-top:0.4rem">
                        <span>${j.candidate_count || 0} candidate${(j.candidate_count||0)===1?"":"s"}</span>
                        <span>${fmtRelative(j.updated_at)}</span>
                    </div>
                </div>`;
            }).join("");
            jobsList.querySelectorAll(".job-card").forEach((el) => {
                el.addEventListener("click", () => {
                    window.location.href = el.dataset.href;
                });
            });
        } catch (err) {
            jobsList.innerHTML = `<p class="empty">Couldn't load jobs: ${err.message}</p>`;
        }
    }
    function escapeHtml(s) {
        return String(s || "")
            .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
    }

    /* ---- restore a previously-saved template from the templates page ---- */
    const savedTpl = localStorage.getItem("clipforge_template");
    if (savedTpl) {
        try {
            const s = JSON.parse(savedTpl);
            if (s.aspect_ratio) form.aspect_ratio.value = s.aspect_ratio;
            if (s.caption_style) form.caption_style.value = s.caption_style;
            if (s.caption_position != null) {
                // The home form doesn't have a position field, so we just remember it.
                sessionStorage.setItem("clipforge_caption_position", String(s.caption_position));
            }
            localStorage.removeItem("clipforge_template");
        } catch {}
    }

    refreshBtn.addEventListener("click", loadJobs);
    historyLink.addEventListener("click", (e) => { e.preventDefault(); loadJobs(); });
    loadJobs();
    setInterval(loadJobs, 15000);
})();
