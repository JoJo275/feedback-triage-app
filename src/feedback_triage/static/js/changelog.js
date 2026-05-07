// Management changelog -- inline release-note editor (PR 3.3).
//
// Hydrates `templates/pages/changelog.html` from the v2 list API
// filtered to `status=shipped`, ordered most-recent first. Each row
// surfaces:
//   * a 280-char textarea bound to `release_note` -- saves on blur
//     and on submit (Enter inside the textarea is ignored, the form
//     is submitted via the implicit submit button absence; Ctrl/Cmd+
//     Enter forces an explicit save),
//   * a "Publish to changelog" toggle bound to
//     `published_to_changelog`.
//
// Both fields round-trip via PATCH /api/v1/feedback/{id}.

import { escapeHtml, formatDate } from "./api.js";
import {
    formatDetail,
    listFeedbackV2,
    patchFeedbackV2,
    workspaceSlug,
} from "./api_v2.js";

const slug = workspaceSlug();
const list = document.getElementById("changelog-list");
const statusEl = document.getElementById("changelog-status");
const errorEl = document.getElementById("changelog-error");
const emptyEl = document.getElementById("changelog-empty");
const template = document.getElementById("release-note-template");

function showError(message) {
    errorEl.textContent = message;
    errorEl.hidden = false;
}

function clearError() {
    errorEl.hidden = true;
    errorEl.textContent = "";
}

function setRowStatus(form, message, tone) {
    const status = form.querySelector('[data-field="status"]');
    status.textContent = message;
    status.classList.toggle("sn-text-danger", tone === "danger");
    if (message) {
        // Clear after a short delay so the live region doesn't accumulate.
        setTimeout(() => {
            if (status.textContent === message) status.textContent = "";
        }, 3000);
    }
}

function renderRow(item) {
    const fragment = template.content.cloneNode(true);
    const row = fragment.querySelector("li");
    row.id = `changelog-row-${item.id}`;
    row.dataset.id = String(item.id);

    const form = row.querySelector("form");
    form.dataset.id = String(item.id);

    const date = item.updated_at ? new Date(item.updated_at) : null;
    const dateEl = form.querySelector('[data-field="date"]');
    if (date) {
        const iso = item.updated_at;
        dateEl.innerHTML = `<time datetime="${escapeHtml(iso)}">${escapeHtml(formatDate(iso))}</time>`;
    }

    form.querySelector('[data-field="title"]').textContent = item.title;

    const textarea = form.querySelector('[data-field="release-note"]');
    textarea.value = item.release_note || "";
    textarea.dataset.lastValue = textarea.value;

    const toggle = form.querySelector('[data-action="toggle-publish"]');
    toggle.checked = !!item.published_to_changelog;

    return row;
}

async function saveReleaseNote(form) {
    const id = Number(form.dataset.id);
    const textarea = form.querySelector('[data-field="release-note"]');
    const next = textarea.value;
    if (next === textarea.dataset.lastValue) return;
    setRowStatus(form, "Saving…", "muted");
    try {
        const updated = await patchFeedbackV2(slug, id, {
            release_note: next ? next : null,
        });
        textarea.dataset.lastValue = updated.release_note || "";
        setRowStatus(form, "Saved.", "muted");
    } catch (err) {
        setRowStatus(form, formatDetail(err.detail) || err.message, "danger");
    }
}

async function togglePublish(form, checkbox) {
    const id = Number(form.dataset.id);
    setRowStatus(form, "Saving…", "muted");
    try {
        await patchFeedbackV2(slug, id, {
            published_to_changelog: checkbox.checked,
        });
        setRowStatus(form, "Saved.", "muted");
    } catch (err) {
        // Revert the toggle if the server rejected it.
        checkbox.checked = !checkbox.checked;
        setRowStatus(form, formatDetail(err.detail) || err.message, "danger");
    }
}

async function loadItems() {
    statusEl.hidden = false;
    statusEl.textContent = "Loading…";
    clearError();
    try {
        const resp = await listFeedbackV2(slug, {
            status: "shipped",
            limit: 100,
            sort_by: "-updated_at",
        });
        list.innerHTML = "";
        if (resp.items.length === 0) {
            statusEl.hidden = true;
            emptyEl.hidden = false;
            return;
        }
        for (const item of resp.items) {
            list.appendChild(renderRow(item));
        }
        list.hidden = false;
        statusEl.hidden = true;
    } catch (err) {
        statusEl.hidden = true;
        showError(formatDetail(err.detail) || err.message);
    }
}

list.addEventListener(
    "blur",
    (ev) => {
        if (ev.target.dataset.field !== "release-note") return;
        const form = ev.target.closest("form");
        if (form) saveReleaseNote(form);
    },
    true, // capture -- focusout is the bubbling counterpart but blur
    // doesn't bubble, so capture phase delegation is required.
);

list.addEventListener("change", (ev) => {
    if (ev.target.dataset.action !== "toggle-publish") return;
    const form = ev.target.closest("form");
    if (form) togglePublish(form, ev.target);
});

list.addEventListener("submit", (ev) => {
    ev.preventDefault();
    const form = ev.target.closest("form");
    if (form) saveReleaseNote(form);
});

if (slug) {
    loadItems();
} else {
    showError("Workspace slug missing -- reload the page.");
}
