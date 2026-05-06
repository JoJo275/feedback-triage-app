// Feedback detail "case file" page.
//
// Hydrates the shell rendered by `templates/pages/feedback_detail.html`
// from the v2 API: GET /api/v1/feedback/{id} for the item, …/notes
// for the note thread, /api/v1/tags for the tag picker. Status and
// priority changes round-trip via PATCH; tag membership uses the
// POST /api/v1/feedback/{id}/tags replace endpoint (PR 2.2).

import { escapeHtml, formatDate } from "./api.js";
import {
    createNote,
    deleteNote,
    formatDetail,
    getFeedbackV2,
    listNotes,
    listTags,
    patchFeedbackV2,
    replaceTags,
    workspaceSlug,
} from "./api_v2.js";

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
const PRIORITY_TONES = {
    low: "info",
    medium: "warn",
    high: "danger",
    critical: "danger",
};

const main = document.getElementById("main");
const slug = workspaceSlug();
const itemId = main ? Number(main.dataset.feedbackId) : 0;

const titleEl = document.getElementById("detail-title");
const typeEl = document.getElementById("detail-type");
const statusWrap = document.getElementById("detail-status-wrap");
const priorityWrap = document.getElementById("detail-priority-wrap");
const painEl = document.getElementById("detail-pain");
const errorEl = document.getElementById("detail-error");
const descEl = document.getElementById("detail-description");
const sourceEl = document.getElementById("detail-source");
const createdEl = document.getElementById("detail-created");
const updatedEl = document.getElementById("detail-updated");
const tagsList = document.getElementById("detail-tags");
const tagSelect = document.getElementById("tag-add-select");
const tagAddForm = document.getElementById("tag-add-form");
const submitterEl = document.getElementById("detail-submitter");
const statusSelect = document.getElementById("status-select");
const prioritySelect = document.getElementById("priority-select");
const toggleRoadmap = document.getElementById("toggle-roadmap");
const toggleChangelog = document.getElementById("toggle-changelog");
const notesList = document.getElementById("notes-list");
const notesForm = document.getElementById("notes-form");
const notesInput = document.getElementById("notes-input");
const notesError = document.getElementById("notes-error");
const timelineEntries = document.getElementById("timeline-entries");

const state = {
    item: null,
    tags: [],
    notes: [],
};

function showError(message) {
    errorEl.textContent = message;
    errorEl.hidden = false;
}

function clearError() {
    errorEl.textContent = "";
    errorEl.hidden = true;
}

function renderItem() {
    const item = state.item;
    if (!item) return;
    titleEl.textContent = item.title;
    typeEl.textContent = item.type;
    typeEl.dataset.state = "ok";
    const statusTone = STATUS_TONES[item.status] || "muted";
    statusWrap.innerHTML = `<span class="sn-pill-status sn-pill-status--${statusTone}" data-status="${escapeHtml(item.status)}">${escapeHtml(STATUS_LABELS[item.status] || item.status)}</span>`;
    if (item.priority) {
        const tone = PRIORITY_TONES[item.priority] || "muted";
        priorityWrap.innerHTML = `<span class="sn-pill-priority sn-pill-priority--${tone}">${escapeHtml(item.priority)}</span>`;
    } else {
        priorityWrap.innerHTML = `<span class="sn-pill-priority sn-pill-priority--unset" aria-label="No priority set">—</span>`;
    }
    const pain = Math.max(0, Math.min(5, Number(item.pain_level) || 0));
    painEl.textContent = "●".repeat(pain) + "○".repeat(5 - pain);
    painEl.setAttribute("aria-label", `Pain level ${pain} of 5`);
    descEl.textContent = item.description || "(No description provided.)";
    sourceEl.textContent = item.source;
    createdEl.textContent = formatDate(item.created_at);
    updatedEl.textContent = formatDate(item.updated_at);
    statusSelect.value = item.status;
    prioritySelect.value = item.priority || "";
    toggleRoadmap.checked = !!item.published_to_roadmap;
    toggleChangelog.checked = !!item.published_to_changelog;
    submitterEl.textContent = item.submitter_id
        ? `Submitter id ${item.submitter_id}`
        : "No known submitter.";
}

function renderTagOptions() {
    if (!tagSelect) return;
    tagSelect.innerHTML =
        `<option value="">Pick a tag…</option>` +
        state.tags
            .map(
                (t) =>
                    `<option value="${escapeHtml(t.id)}">${escapeHtml(t.name)}</option>`,
            )
            .join("");
}

function renderTagsList() {
    // The current item doesn't include tag membership; PR 2.2 keeps
    // tag-replace as POST-only. Until the API surfaces feedback tags
    // on GET, the chip area shows a hint. Wired so PR 2.6 can drop
    // in a real list.
    tagsList.innerHTML = `<li class="sn-text-muted">Tag membership shows after a refresh of the v2 feedback response (PR 2.6).</li>`;
}

function renderNotes() {
    if (state.notes.length === 0) {
        notesList.innerHTML = `<li class="sn-notes-panel__placeholder">No notes yet.</li>`;
        return;
    }
    notesList.innerHTML = state.notes
        .map(
            (n) => `
        <li class="sn-notes-panel__entry" data-note-id="${escapeHtml(n.id)}">
          <header class="sn-notes-panel__entry-header">
            <span>${escapeHtml(formatDate(n.created_at))}</span>
            <button type="button" class="sn-button sn-button-ghost" data-action="delete-note" data-id="${escapeHtml(n.id)}">Delete</button>
          </header>
          <p>${escapeHtml(n.body)}</p>
        </li>`,
        )
        .join("");
}

function renderTimeline() {
    // The timeline view is read-only and currently rebuilt from the
    // few timestamps the API exposes today. A dedicated audit log
    // is an explicit follow-up (see schema.md — workflow_history).
    if (!state.item) return;
    const entries = [];
    entries.push({
        when: state.item.created_at,
        text: "Item created",
    });
    if (state.item.updated_at !== state.item.created_at) {
        entries.push({
            when: state.item.updated_at,
            text: `Last updated (status: ${state.item.status})`,
        });
    }
    timelineEntries.innerHTML = entries
        .map(
            (e) => `
        <li class="sn-timeline__entry">
          <time datetime="${escapeHtml(e.when)}">${escapeHtml(formatDate(e.when))}</time>
          <span>${escapeHtml(e.text)}</span>
        </li>`,
        )
        .join("");
}

async function loadItem() {
    try {
        state.item = await getFeedbackV2(slug, itemId);
        renderItem();
        renderTimeline();
    } catch (err) {
        showError(formatDetail({ detail: err.detail }) || err.message);
    }
}

async function loadTags() {
    try {
        const env = await listTags(slug);
        state.tags = env.items || [];
        renderTagOptions();
        renderTagsList();
    } catch {
        // Tag picker is not load-bearing; an error here just leaves
        // the dropdown empty.
    }
}

async function loadNotes() {
    try {
        const env = await listNotes(slug, itemId);
        state.notes = env.items || [];
        renderNotes();
    } catch (err) {
        notesError.textContent =
            formatDetail({ detail: err.detail }) || err.message;
        notesError.hidden = false;
    }
}

async function patch(payload) {
    clearError();
    try {
        state.item = await patchFeedbackV2(slug, itemId, payload);
        renderItem();
        renderTimeline();
    } catch (err) {
        showError(formatDetail({ detail: err.detail }) || err.message);
    }
}

if (slug && itemId) {
    statusSelect.addEventListener("change", () => {
        void patch({ status: statusSelect.value });
    });
    prioritySelect.addEventListener("change", () => {
        void patch({ priority: prioritySelect.value || null });
    });
    toggleRoadmap.addEventListener("change", () => {
        void patch({ published_to_roadmap: toggleRoadmap.checked });
    });
    toggleChangelog.addEventListener("change", () => {
        void patch({ published_to_changelog: toggleChangelog.checked });
    });

    notesForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        const body = notesInput.value.trim();
        if (!body) return;
        notesError.hidden = true;
        try {
            const note = await createNote(slug, itemId, body);
            state.notes.push(note);
            notesInput.value = "";
            renderNotes();
        } catch (err) {
            notesError.textContent =
                formatDetail({ detail: err.detail }) || err.message;
            notesError.hidden = false;
        }
    });

    notesList.addEventListener("click", async (event) => {
        const button = event.target.closest(
            'button[data-action="delete-note"]',
        );
        if (!button) return;
        const id = button.dataset.id;
        if (!id) return;
        if (!window.confirm("Delete this note?")) return;
        try {
            await deleteNote(slug, itemId, id);
            state.notes = state.notes.filter((n) => n.id !== id);
            renderNotes();
        } catch (err) {
            notesError.textContent =
                formatDetail({ detail: err.detail }) || err.message;
            notesError.hidden = false;
        }
    });

    tagAddForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        const tagId = tagSelect.value;
        if (!tagId) return;
        try {
            // Replace endpoint takes the *full* tag set; without
            // GET-side membership we send just the picked tag. PR 2.6
            // upgrades this to a true add/remove once feedback
            // responses include their tag list.
            await replaceTags(slug, itemId, [tagId]);
        } catch (err) {
            showError(formatDetail({ detail: err.detail }) || err.message);
        }
    });

    void loadItem();
    void loadTags();
    void loadNotes();
}
