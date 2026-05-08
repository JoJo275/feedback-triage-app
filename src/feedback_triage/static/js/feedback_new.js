// Workspace-scoped create-feedback form.
// POSTs to /api/v1/feedback with X-Workspace-Slug, then redirects
// to the new item's detail page on success.

import { apiFetch, formatDetail } from "./api.js";
import { workspaceSlug } from "./api_v2.js";

const form = document.getElementById("feedback-new-form");
const errorEl = document.getElementById("form-error");
const statusEl = document.getElementById("form-status");

function showError(message) {
    if (!errorEl) return;
    errorEl.textContent = message;
    errorEl.hidden = false;
}

function clearError() {
    if (!errorEl) return;
    errorEl.textContent = "";
    errorEl.hidden = true;
}

function setStatus(message) {
    if (!statusEl) return;
    if (message) {
        statusEl.textContent = message;
        statusEl.hidden = false;
    } else {
        statusEl.textContent = "";
        statusEl.hidden = true;
    }
}

if (form) {
    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        clearError();
        setStatus("Saving…");

        const slug = workspaceSlug();
        const data = new FormData(form);

        const payload = {
            title: String(data.get("title") || "").trim(),
            description: String(data.get("description") || "").trim() || null,
            source: data.get("source"),
            type: data.get("type"),
            pain_level: Number(data.get("pain_level")),
            status: data.get("status"),
        };
        const priority = data.get("priority");
        if (priority) payload.priority = priority;

        if (!payload.title) {
            setStatus("");
            showError("Title is required.");
            return;
        }

        try {
            const result = await apiFetch("/api/v1/feedback", {
                method: "POST",
                body: payload,
                headers: { "X-Workspace-Slug": slug },
            });
            if (result && result.id) {
                window.location.assign(`/w/${slug}/feedback/${result.id}`);
            } else {
                window.location.assign(`/w/${slug}/inbox`);
            }
        } catch (err) {
            setStatus("");
            showError(
                err.message ||
                    formatDetail(err.detail) ||
                    "Failed to create feedback.",
            );
        }
    });
}
