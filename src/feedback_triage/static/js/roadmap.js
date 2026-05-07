// Roadmap kanban -- management view (PR 3.3).
//
// Hydrates `templates/pages/roadmap.html` from the v2 list API
// filtered to the three roadmap statuses. Cards expose:
//   * keyboard prev/next buttons that cycle status across the columns
//     (planned -> in_progress -> shipped),
//   * native HTML5 drag-and-drop for pointer users (drop on a column
//     dispatches the same status PATCH),
//   * a "Public roadmap" toggle that flips
//     `published_to_roadmap` via the same PATCH endpoint.
//
// Reduced-motion users (prefers-reduced-motion: reduce) get the
// keyboard buttons only -- the dragstart handler short-circuits.

import { escapeHtml, formatDetail } from "./api.js";
import {
    listFeedbackV2,
    patchFeedbackV2,
    workspaceSlug,
} from "./api_v2.js";

const COLUMNS = ["planned", "in_progress", "shipped"];
const TYPE_LABELS = {
    bug: "Bug",
    feature_request: "Feature request",
    complaint: "Complaint",
    praise: "Praise",
    question: "Question",
    other: "Other",
};
const PRIORITY_LABELS = {
    low: "Low",
    medium: "Medium",
    high: "High",
    critical: "Critical",
};
const PRIORITY_TONES = {
    low: "info",
    medium: "warn",
    high: "danger",
    critical: "danger",
};

const slug = workspaceSlug();
const board = document.getElementById("kanban-board");
const statusEl = document.getElementById("board-status");
const errorEl = document.getElementById("board-error");
const cardTemplate = document.getElementById("kanban-card-template");
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

// In-memory mirror of the rendered cards keyed by feedback id; the
// move/toggle handlers consult this to compute the next status and
// to persist the optimistic update on PATCH success.
const itemsById = new Map();

function showError(message) {
    errorEl.textContent = message;
    errorEl.hidden = false;
}

function clearError() {
    errorEl.hidden = true;
    errorEl.textContent = "";
}

function columnRoot(key) {
    return board.querySelector(`[data-column="${key}"]`);
}

function renderTags(card, tags) {
    const list = card.querySelector('[data-field="tags"]');
    list.innerHTML = "";
    for (const tag of tags || []) {
        const chip = document.createElement("li");
        const color = tag.color || "slate";
        chip.innerHTML =
            `<span class="sn-tag-chip sn-tag-chip--${escapeHtml(color)}" ` +
            `data-tag-slug="${escapeHtml(tag.slug)}">` +
            `<span class="sn-tag-chip__label">${escapeHtml(tag.name)}</span>` +
            `</span>`;
        list.appendChild(chip);
    }
}

function renderCard(item) {
    const fragment = cardTemplate.content.cloneNode(true);
    const card = fragment.querySelector(".sn-kanban-card");
    card.id = `kanban-card-${item.id}`;
    card.dataset.id = String(item.id);
    card.dataset.status = item.status;
    card.dataset.published = item.published_to_roadmap ? "true" : "false";

    card.querySelector('[data-field="title"]').textContent = item.title;

    const typePill = card.querySelector('[data-field="type-pill"]');
    typePill.dataset.type = item.type;
    typePill.textContent =
        item.type === "other" && item.type_other
            ? item.type_other
            : TYPE_LABELS[item.type] || item.type;

    const priorityPill = card.querySelector('[data-field="priority-pill"]');
    if (item.priority) {
        priorityPill.hidden = false;
        priorityPill.classList.add(`sn-pill-priority--${PRIORITY_TONES[item.priority] || "muted"}`);
        priorityPill.textContent = PRIORITY_LABELS[item.priority] || item.priority;
    }

    renderTags(card, item.tags);

    const toggle = card.querySelector('[data-action="toggle-publish"]');
    toggle.checked = !!item.published_to_roadmap;

    return card;
}

function placeCard(card, status) {
    const column = columnRoot(status);
    if (!column) return;
    column.querySelector('[data-field="cards"]').appendChild(card);
    refreshColumn(status);
}

function refreshColumn(status) {
    const column = columnRoot(status);
    if (!column) return;
    const cards = column.querySelector('[data-field="cards"]');
    const empty = column.querySelector('[data-field="empty"]');
    const count = column.querySelector('[data-field="count"]');
    const n = cards.children.length;
    count.textContent = String(n);
    empty.hidden = n > 0;
}

async function loadItems() {
    statusEl.hidden = false;
    statusEl.textContent = "Loading…";
    clearError();
    try {
        // The list endpoint accepts a single status filter, so we fetch
        // each column in parallel. Page size cap keeps this O(1) HTTP
        // round-trips no matter how many shipped items exist.
        const responses = await Promise.all(
            COLUMNS.map((s) =>
                listFeedbackV2(slug, {
                    status: s,
                    limit: 100,
                    sort_by: "-updated_at",
                }),
            ),
        );
        for (const [i, resp] of responses.entries()) {
            for (const item of resp.items) {
                itemsById.set(item.id, item);
                placeCard(renderCard(item), COLUMNS[i]);
            }
        }
        board.hidden = false;
        statusEl.hidden = true;
    } catch (err) {
        statusEl.hidden = true;
        showError(formatDetail(err.detail) || err.message);
    }
}

async function patchAndApply(id, body) {
    try {
        const updated = await patchFeedbackV2(slug, id, body);
        itemsById.set(updated.id, updated);
        const card = document.getElementById(`kanban-card-${id}`);
        if (!card) return updated;
        // If the status changed, move the DOM node across columns.
        if (card.dataset.status !== updated.status) {
            const previous = card.dataset.status;
            card.dataset.status = updated.status;
            card.remove();
            refreshColumn(previous);
            placeCard(card, updated.status);
        }
        card.dataset.published = updated.published_to_roadmap ? "true" : "false";
        const toggle = card.querySelector('[data-action="toggle-publish"]');
        toggle.checked = !!updated.published_to_roadmap;
        return updated;
    } catch (err) {
        showError(formatDetail(err.detail) || err.message);
        throw err;
    }
}

function moveByOffset(card, offset) {
    const current = COLUMNS.indexOf(card.dataset.status);
    if (current === -1) return;
    const target = current + offset;
    if (target < 0 || target >= COLUMNS.length) return;
    patchAndApply(Number(card.dataset.id), { status: COLUMNS[target] });
}

board.addEventListener("click", (ev) => {
    const card = ev.target.closest(".sn-kanban-card");
    if (!card) return;
    const action = ev.target.dataset.action;
    if (action === "move-prev") moveByOffset(card, -1);
    if (action === "move-next") moveByOffset(card, 1);
});

board.addEventListener("change", (ev) => {
    if (ev.target.dataset.action !== "toggle-publish") return;
    const card = ev.target.closest(".sn-kanban-card");
    if (!card) return;
    patchAndApply(Number(card.dataset.id), {
        published_to_roadmap: ev.target.checked,
    });
});

// Drag-and-drop -- skipped under prefers-reduced-motion.
if (!reduceMotion) {
    board.addEventListener("dragstart", (ev) => {
        const card = ev.target.closest(".sn-kanban-card");
        if (!card) return;
        ev.dataTransfer.setData("text/plain", card.dataset.id);
        ev.dataTransfer.effectAllowed = "move";
    });
    board.addEventListener("dragover", (ev) => {
        const column = ev.target.closest(".sn-kanban-column");
        if (!column) return;
        ev.preventDefault();
        ev.dataTransfer.dropEffect = "move";
    });
    board.addEventListener("drop", (ev) => {
        const column = ev.target.closest(".sn-kanban-column");
        if (!column) return;
        ev.preventDefault();
        const id = Number(ev.dataTransfer.getData("text/plain"));
        if (!id) return;
        const targetStatus = column.dataset.column;
        const card = document.getElementById(`kanban-card-${id}`);
        if (!card || card.dataset.status === targetStatus) return;
        patchAndApply(id, { status: targetStatus });
    });
}

if (slug) {
    loadItems();
} else {
    showError("Workspace slug missing -- reload the page.");
}
