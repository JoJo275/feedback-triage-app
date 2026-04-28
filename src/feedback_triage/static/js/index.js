// List page: load + render feedback items, sync filters with the URL.

import {
    deleteFeedback,
    escapeHtml,
    formatDate,
    formatDetail,
    listFeedback,
} from "./api.js";

const FILTER_KEYS = ["status", "source", "sort_by"];
const SOURCE_LABELS = {
    email: "Email",
    interview: "Interview",
    reddit: "Reddit",
    support: "Support",
    app_store: "App store",
    twitter: "Twitter",
    other: "Other",
};
const STATUS_LABELS = {
    new: "New",
    reviewing: "Reviewing",
    planned: "Planned",
    rejected: "Rejected",
};

const form = document.getElementById("filter-form");
const statusEl = document.getElementById("filter-status");
const sourceEl = document.getElementById("filter-source");
const sortEl = document.getElementById("filter-sort");
const resetButton = document.getElementById("filter-reset");
const listStatus = document.getElementById("list-status");
const listError = document.getElementById("list-error");
const listTable = document.getElementById("list-table");
const listBody = document.getElementById("list-body");
const listSummary = document.getElementById("list-summary");

function readFiltersFromUrl() {
    const params = new URLSearchParams(window.location.search);
    return {
        status: params.get("status") || "",
        source: params.get("source") || "",
        sort_by: params.get("sort_by") || "-created_at",
    };
}

function applyFiltersToForm(filters) {
    statusEl.value = filters.status;
    sourceEl.value = filters.source;
    sortEl.value = filters.sort_by;
}

function readFiltersFromForm() {
    return {
        status: statusEl.value,
        source: sourceEl.value,
        sort_by: sortEl.value || "-created_at",
    };
}

function writeFiltersToUrl(filters) {
    const params = new URLSearchParams();
    for (const key of FILTER_KEYS) {
        const value = filters[key];
        if (value && !(key === "sort_by" && value === "-created_at")) {
            params.set(key, value);
        }
    }
    const qs = params.toString();
    const url = qs
        ? `${window.location.pathname}?${qs}`
        : window.location.pathname;
    window.history.replaceState(null, "", url);
}

function showError(message) {
    listError.textContent = message;
    listError.hidden = false;
}

function clearError() {
    listError.textContent = "";
    listError.hidden = true;
}

function renderRows(items) {
    if (items.length === 0) {
        listBody.innerHTML = "";
        listTable.hidden = true;
        listStatus.textContent = "No feedback items match the current filters.";
        listStatus.hidden = false;
        return;
    }
    const html = items
        .map((item) => {
            const title = escapeHtml(item.title);
            const source = escapeHtml(
                SOURCE_LABELS[item.source] || item.source,
            );
            const status = escapeHtml(
                STATUS_LABELS[item.status] || item.status,
            );
            const created = escapeHtml(formatDate(item.created_at));
            const id = escapeHtml(item.id);
            return `
        <tr data-id="${id}">
          <td><a href="/feedback/${id}">${title}</a></td>
          <td>${source}</td>
          <td><span class="pain" aria-label="Pain level ${escapeHtml(item.pain_level)} of 5">${escapeHtml(item.pain_level)}</span></td>
          <td>${status}</td>
          <td>${created}</td>
          <td class="actions">
            <a class="button button-ghost" href="/feedback/${id}">Edit</a>
            <button type="button" class="button button-danger" data-action="delete" data-id="${id}">
              Delete
            </button>
          </td>
        </tr>
      `;
        })
        .join("");
    listBody.innerHTML = html;
    listTable.hidden = false;
    listStatus.hidden = true;
}

async function refresh() {
    const filters = readFiltersFromForm();
    writeFiltersToUrl(filters);
    clearError();
    listStatus.textContent = "Loading…";
    listStatus.hidden = false;
    listSummary.hidden = true;
    try {
        const envelope = await listFeedback(filters);
        renderRows(envelope.items);
        listSummary.textContent = `Showing ${envelope.items.length} of ${envelope.total}.`;
        listSummary.hidden = false;
    } catch (err) {
        listTable.hidden = true;
        listStatus.hidden = true;
        showError(err.message || "Failed to load feedback.");
    }
}

form.addEventListener("submit", (event) => {
    event.preventDefault();
    refresh();
});

resetButton.addEventListener("click", () => {
    applyFiltersToForm({ status: "", source: "", sort_by: "-created_at" });
    refresh();
});

listBody.addEventListener("click", async (event) => {
    const button = event.target.closest('button[data-action="delete"]');
    if (!button) return;
    const id = button.dataset.id;
    if (!id) return;
    if (!window.confirm("Delete this feedback item? This cannot be undone.")) {
        return;
    }
    button.disabled = true;
    try {
        await deleteFeedback(id);
        await refresh();
    } catch (err) {
        button.disabled = false;
        showError(formatDetail({ detail: err.detail }) || err.message);
    }
});

applyFiltersToForm(readFiltersFromUrl());
refresh();
