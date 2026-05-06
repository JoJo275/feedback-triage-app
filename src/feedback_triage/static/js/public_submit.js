// Public submission form glue (PR 2.4).
//
// Reads the workspace slug from the form's ``data-workspace-slug``
// attribute, POSTs to ``/api/v1/public/feedback/{slug}``, and toggles
// the thank-you / error panels based on the response. No bundler, no
// framework -- see docs/notes/frontend-conventions.md.

(function () {
    "use strict";

    const JSON_HEADERS = {
        "Content-Type": "application/json",
        Accept: "application/json",
    };

    function show(node) {
        if (node) node.hidden = false;
    }
    function hide(node) {
        if (node) node.hidden = true;
    }
    function setText(node, text) {
        if (node) node.textContent = text;
    }

    function buildPayload(form) {
        const data = new FormData(form);
        const payload = {
            title: (data.get("title") || "").trim(),
            description: (data.get("description") || "").trim() || null,
            pain_level: Number(data.get("pain_level") || 3),
            type: data.get("type") || "other",
            submitter_email: (data.get("submitter_email") || "").trim() || null,
            submitter_name: (data.get("submitter_name") || "").trim() || null,
            website: data.get("website") || "",
        };
        // Drop nulls so the server's ``extra="forbid"`` doesn't choke
        // on a key that pydantic could resolve via default but mypy
        // would prefer absent.
        Object.keys(payload).forEach((k) => {
            if (payload[k] === null) delete payload[k];
        });
        return payload;
    }

    async function submit(form, statusEl, errorEl, thanksEl) {
        const slug = form.dataset.workspaceSlug;
        const payload = buildPayload(form);
        hide(errorEl);
        setText(statusEl, "Submitting…");
        show(statusEl);

        let resp;
        try {
            resp = await fetch(
                `/api/v1/public/feedback/${encodeURIComponent(slug)}`,
                {
                    method: "POST",
                    headers: JSON_HEADERS,
                    body: JSON.stringify(payload),
                },
            );
        } catch (_err) {
            hide(statusEl);
            setText(errorEl, "Network error. Try again in a moment.");
            show(errorEl);
            return;
        }

        let body = null;
        try {
            body = await resp.json();
        } catch (_err) {
            body = null;
        }

        hide(statusEl);
        if (resp.ok) {
            hide(form);
            show(thanksEl);
            return;
        }
        const detail = body && body.detail;
        const msg =
            (detail && detail.message) ||
            (detail && typeof detail === "string" && detail) ||
            "Submission failed. Check the form and try again.";
        setText(errorEl, msg);
        show(errorEl);
    }

    function init() {
        const form = document.getElementById("submit-form");
        if (!form) return;
        const statusEl = document.getElementById("form-status");
        const errorEl = document.getElementById("form-error");
        const thanksEl = document.getElementById("thank-you");
        const another = document.getElementById("submit-another");

        form.addEventListener("submit", function (ev) {
            ev.preventDefault();
            submit(form, statusEl, errorEl, thanksEl);
        });
        if (another) {
            another.addEventListener("click", function () {
                form.reset();
                hide(thanksEl);
                hide(errorEl);
                show(form);
                const titleInput = document.getElementById("f-title");
                if (titleInput) titleInput.focus();
            });
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
