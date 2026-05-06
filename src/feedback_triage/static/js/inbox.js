// Inbox / feedback list page logic.
//
// The shell template (`templates/pages/inbox.html`) ships with empty
// containers and a `data-page-mode` flag (inbox vs feedback). This
// module reads the URL query string, populates the filter form,
// fetches the list + summary counts from the v2 API, and writes the
// results back into the table. Filters round-trip through
// `history.replaceState` so a refresh / share link reproduces the
// same view.

import { escapeHtml, formatDate } from "./api.js";
import { listFeedbackV2, workspaceSlug, formatDetail } from "./api_v2.js";

const FILTER_KEYS = ["q", "status", "type", "priority", "source", "sort_by"];
const SOURCE_LABELS = {
    email: "Email",
    interview: "Interview",
    reddit: "Reddit",
    support: "Support",
    app_store: "App store",
    twitter: "Twitter",
    web_form: "Web form",
    other: "Other",
};
const TYPE_LABELS = {
    bug: "Bug",
    feature_request: "Feature",
    complaint: "Complaint",
    praise: "Praise",
    question: "Question",
    other: "Other",
};
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
const INBOX_DEFAULT_STATUSES = ["new", "needs_info", "reviewing"];
const STALE_STATUSES = new Set(["new", "needs_info"]);
const STALE_THRESHOLD_MS = 14 * 24 * 60 * 60 * 1000;

function isStale(item) {
    // Mirrors `services.stale_detector.is_stale` server-side: items in
    // {new, needs_info} older than 14 days. The badge is purely a
    // visual cue; the source of truth is the SQL clause used by the
    // `stale=true` filter and the summary card count.
    if (!STALE_STATUSES.has(item.status)) return false;
    const created = Date.parse(item.created_at);
    if (Number.isNaN(created)) return false;
    return Date.now() - created > STALE_THRESHOLD_MS;
}

const main = document.getElementById("main");
const slug = workspaceSlug();
const pageMode = main ? main.dataset.pageMode : "inbox";

const form = document.getElementById("filter-form");
const inputs = {
    q: document.getElementById("filter-q"),
    status: document.getElementById("filter-status"),
    type: document.getElementById("filter-type"),
    priority: document.getElementById("filter-priority"),
    source: document.getElementById("filter-source"),
    sort_by: document.getElementById("filter-sort"),
};
const resetButton = document.getElementById("filter-reset");
const listStatus = document.getElementById("list-status");
const listError = document.getElementById("list-error");
const listTable = document.getElementById("list-table");
const listBody = document.getElementById("list-body");
const listSummary = document.getElementById("list-summary");
const emptyState = document.getElementById("empty-state");
const countChip = document.getElementById("result-count-chip");

function readFiltersFromUrl() {
    const params = new URLSearchParams(window.location.search);
    const out = {};
    for (const key of FILTER_KEYS) {
        out[key] = params.get(key) || "";
    }
    if (!out.sort_by) out.sort_by = "-created_at";
    return out;
}

function applyFiltersToForm(filters) {
    for (const key of FILTER_KEYS) {
        if (inputs[key]) inputs[key].value = filters[key] || "";
    }
}

function readFiltersFromForm() {
    const out = {};
    for (const key of FILTER_KEYS) {
        out[key] = inputs[key] ? inputs[key].value : "";
    }
    if (!out.sort_by) out.sort_by = "-created_at";
    return out;
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

function paramsForFetch(filters) {
    // The v2 list endpoint takes a single `status` param, so the
    // inbox default ("new + needs_info + reviewing") is rendered by
    // running three queries in parallel and merging counts. The full
    // list view scopes to whatever the user picked.
    const out = {};
    for (const key of FILTER_KEYS) {
        if (filters[key]) out[key] = filters[key];
    }
    return out;
}

function renderRows(items) {
    if (items.length === 0) {
        listBody.innerHTML = "";
        listTable.hidden = true;
        listStatus.hidden = true;
        emptyState.hidden = false;
        return;
    }
    emptyState.hidden = true;
    const html = items
        .map((item) => {
            const id = escapeHtml(item.id);
            const title = escapeHtml(item.title);
            const type = escapeHtml(TYPE_LABELS[item.type] || item.type);
            const statusLabel = escapeHtml(
                STATUS_LABELS[item.status] || item.status,
            );
            const statusTone = STATUS_TONES[item.status] || "muted";
            const priorityLabel = item.priority
                ? escapeHtml(item.priority)
                : "—";
            const priorityTone = item.priority
                ? PRIORITY_TONES[item.priority] || "muted"
                : "unset";
            const pain = Math.max(0, Math.min(5, Number(item.pain_level) || 0));
            const dots = "●".repeat(pain) + "○".repeat(5 - pain);
            const source = escapeHtml(
                SOURCE_LABELS[item.source] || item.source,
            );
            const created = escapeHtml(formatDate(item.created_at));
            const staleBadge = isStale(item)
                ? ` <span class="sn-stale-badge" title="No activity for over 14 days">Stale</span>`
                : "";
            return `
        <tr data-id="${id}"${isStale(item) ? ' data-stale="true"' : ""}>
          <td><a href="/w/${escapeHtml(slug)}/feedback/${id}">${title}</a>${staleBadge}</td>
          <td>${type}</td>
          <td><span class="sn-pill-status sn-pill-status--${statusTone}">${statusLabel}</span></td>
          <td><span class="sn-pill-priority sn-pill-priority--${priorityTone}">${priorityLabel}</span></td>
          <td><span class="sn-pain-dots" aria-label="Pain level ${pain} of 5">${dots}</span></td>
          <td>${source}</td>
          <td>${created}</td>
        </tr>`;
        })
        .join("");
    listBody.innerHTML = html;
    listTable.hidden = false;
    listStatus.hidden = true;
}

async function fetchSummary() {
    // Five summary card counts. Each card is a tiny list query with
    // `limit=1` so we only pay for the count aggregate; the v2
    // envelope returns `total` independent of the page slice.
    const queries = [
        { card: "new", params: { status: "new", limit: 1 } },
        { card: "needs_info", params: { status: "needs_info", limit: 1 } },
        { card: "reviewing", params: { status: "reviewing", limit: 1 } },
        {
            card: "high_priority",
            params: { priority: "high", limit: 1 },
        },
        // Stale = items >14 days old in {new, needs_info}. The
        // server-side filter is implemented in
        // `services/stale_detector.py` and exposed as `stale=true`
        // on `GET /api/v1/feedback`.
        { card: "stale", params: { stale: "true", limit: 1 } },
    ];
    const results = await Promise.allSettled(
        queries.map((q) => listFeedbackV2(slug, q.params)),
    );
    queries.forEach((q, i) => {
        const el = document.querySelector(`[data-summary-count="${q.card}"]`);
        if (!el) return;
        const result = results[i];
        if (result.status === "fulfilled") {
            el.textContent = String(result.value.total);
        } else {
            el.textContent = "—";
        }
    });
}

async function refresh() {
    const filters = readFiltersFromForm();
    writeFiltersToUrl(filters);
    clearError();
    listStatus.textContent = "Loading…";
    listStatus.hidden = false;
    listSummary.hidden = true;
    emptyState.hidden = true;
    countChip.hidden = true;

    // Inbox default: when the user hasn't picked a status, query
    // each of the three triage statuses and merge by created_at.
    let envelopes;
    const params = paramsForFetch(filters);
    try {
        if (pageMode === "inbox" && !filters.status) {
            const merged = await Promise.all(
                INBOX_DEFAULT_STATUSES.map((s) =>
                    listFeedbackV2(slug, { ...params, status: s }),
                ),
            );
            const items = merged
                .flatMap((env) => env.items)
                .sort(
                    (a, b) =>
                        new Date(b.created_at).getTime() -
                        new Date(a.created_at).getTime(),
                );
            const total = merged.reduce((acc, env) => acc + env.total, 0);
            envelopes = { items, total };
        } else {
            envelopes = await listFeedbackV2(slug, params);
        }
        renderRows(envelopes.items);
        listSummary.textContent = `Showing ${envelopes.items.length} of ${envelopes.total}.`;
        listSummary.hidden = false;
        countChip.textContent = `${envelopes.total} item${envelopes.total === 1 ? "" : "s"}`;
        countChip.hidden = false;
    } catch (err) {
        listTable.hidden = true;
        listStatus.hidden = true;
        emptyState.hidden = true;
        showError(formatDetail({ detail: err.detail }) || err.message);
    }
}

if (form && slug) {
    form.addEventListener("submit", (event) => {
        event.preventDefault();
        refresh();
    });
    resetButton.addEventListener("click", () => {
        applyFiltersToForm({
            q: "",
            status: "",
            type: "",
            priority: "",
            source: "",
            sort_by: "-created_at",
        });
        refresh();
    });

    applyFiltersToForm(readFiltersFromUrl());
    void fetchSummary();
    void refresh();
}
