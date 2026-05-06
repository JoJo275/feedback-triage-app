// Submitter detail page (PR 2.6).
//
// Shell template ships an empty form + table; this module loads the
// submitter via `/api/v1/submitters/{id}` and the recent feedback
// via `/api/v1/feedback?submitter_id={id}` (api.md — Submitters).

import { apiFetch, escapeHtml, formatDate, formatDetail } from "./api.js";
import { listFeedbackV2, workspaceSlug } from "./api_v2.js";

const STATUS_LABELS = {
    new: "New",
    needs_info: "Needs info",
    reviewing: "Reviewing",
    accepted: "Accepted",
    planned: "Planned",
    in_progress: "In progress",
    shipped: "Shipped",
    closed: "Closed",
    spam: "Spam",
    rejected: "Rejected",
};
const STATUS_TONES = {
    new: "info",
    needs_info: "warn",
    reviewing: "info",
    accepted: "ok",
    planned: "ok",
    in_progress: "ok",
    shipped: "ok",
    closed: "muted",
    spam: "danger",
    rejected: "muted",
};

const main = document.getElementById("main");
const slug = workspaceSlug();
const submitterId = main ? main.dataset.submitterId : "";

const displayName = document.getElementById("submitter-display-name");
const emailEl = document.getElementById("submitter-email");
const detailError = document.getElementById("detail-error");
const form = document.getElementById("submitter-form");
const nameInput = document.getElementById("submitter-name");
const notesInput = document.getElementById("submitter-internal-notes");
const formStatus = document.getElementById("form-status");
const recentStatus = document.getElementById("recent-status");
const recentTable = document.getElementById("recent-table");
const recentBody = document.getElementById("recent-body");
const recentEmpty = document.getElementById("recent-empty");

function showDetailError(message) {
    detailError.textContent = message;
    detailError.hidden = false;
}

function getSubmitter(slug, id) {
    return apiFetch(`/api/v1/submitters/${encodeURIComponent(id)}`, {
        headers: { "X-Workspace-Slug": slug },
    });
}

function patchSubmitter(slug, id, payload) {
    return apiFetch(`/api/v1/submitters/${encodeURIComponent(id)}`, {
        method: "PATCH",
        body: payload,
        headers: { "X-Workspace-Slug": slug },
    });
}

async function loadProfile() {
    try {
        const submitter = await getSubmitter(slug, submitterId);
        displayName.textContent =
            submitter.name || submitter.email || "Submitter";
        emailEl.textContent = submitter.email || "No email on file.";
        nameInput.value = submitter.name || "";
        notesInput.value = submitter.internal_notes || "";
    } catch (err) {
        showDetailError(formatDetail({ detail: err.detail }) || err.message);
    }
}

function renderRecent(items) {
    if (items.length === 0) {
        recentTable.hidden = true;
        recentStatus.hidden = true;
        recentEmpty.hidden = false;
        return;
    }
    recentEmpty.hidden = true;
    const html = items
        .map((item) => {
            const id = escapeHtml(item.id);
            const title = escapeHtml(item.title);
            const tone = STATUS_TONES[item.status] || "muted";
            const label = escapeHtml(STATUS_LABELS[item.status] || item.status);
            const created = escapeHtml(formatDate(item.created_at));
            const href = `/w/${escapeHtml(slug)}/feedback/${id}`;
            return `
        <tr data-id="${id}">
          <td><a href="${href}">${title}</a></td>
          <td><span class="sn-pill-status sn-pill-status--${tone}">${label}</span></td>
          <td>${created}</td>
        </tr>`;
        })
        .join("");
    recentBody.innerHTML = html;
    recentTable.hidden = false;
    recentStatus.hidden = true;
}

async function loadRecent() {
    try {
        const env = await listFeedbackV2(slug, {
            submitter_id: submitterId,
            limit: 50,
        });
        renderRecent(env.items);
    } catch (err) {
        recentStatus.textContent =
            formatDetail({ detail: err.detail }) || err.message;
    }
}

if (form && slug && submitterId) {
    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        formStatus.hidden = true;
        try {
            const updated = await patchSubmitter(slug, submitterId, {
                name: nameInput.value.trim() || null,
                internal_notes: notesInput.value.trim() || null,
            });
            displayName.textContent =
                updated.name || updated.email || "Submitter";
            formStatus.textContent = "Saved.";
            formStatus.hidden = false;
        } catch (err) {
            formStatus.textContent =
                formatDetail({ detail: err.detail }) || err.message;
            formStatus.hidden = false;
        }
    });
    void loadProfile();
    void loadRecent();
}
