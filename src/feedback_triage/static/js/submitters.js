// Submitters list page (PR 2.6).
//
// Shell template ships an empty table; this module fetches the
// `/api/v1/submitters` envelope, renders rows, and supports the
// search input via the `q` query parameter. Filters round-trip to
// the URL so a refresh / share link reproduces the same view.

import { apiFetch, escapeHtml, formatDate, formatDetail } from "./api.js";
import { workspaceSlug } from "./api_v2.js";

const main = document.getElementById("main");
const slug = workspaceSlug();
const form = document.getElementById("submitter-search-form");
const qInput = document.getElementById("submitter-q");
const listStatus = document.getElementById("list-status");
const listError = document.getElementById("list-error");
const listTable = document.getElementById("list-table");
const listBody = document.getElementById("list-body");
const listSummary = document.getElementById("list-summary");
const emptyState = document.getElementById("empty-state");
const countChip = document.getElementById("result-count-chip");

function listSubmitters(slug, params) {
    const qs = new URLSearchParams();
    for (const [k, v] of Object.entries(params || {})) {
        if (v !== "" && v !== null && v !== undefined) qs.set(k, v);
    }
    const suffix = qs.toString() ? `?${qs.toString()}` : "";
    return apiFetch(`/api/v1/submitters${suffix}`, {
        headers: { "X-Workspace-Slug": slug },
    });
}

function readQFromUrl() {
    const params = new URLSearchParams(window.location.search);
    return params.get("q") || "";
}

function writeQToUrl(q) {
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    const qs = params.toString();
    const url = qs
        ? `${window.location.pathname}?${qs}`
        : window.location.pathname;
    window.history.replaceState(null, "", url);
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
            const name = escapeHtml(item.name || "—");
            const email = escapeHtml(item.email || "—");
            const count = Number(item.submission_count || 0);
            const lastSeen = escapeHtml(formatDate(item.last_seen_at));
            const href = `/w/${escapeHtml(slug)}/submitters/${id}`;
            return `
        <tr data-id="${id}">
          <td><a href="${href}">${name}</a></td>
          <td>${email}</td>
          <td>${count}</td>
          <td>${lastSeen}</td>
        </tr>`;
        })
        .join("");
    listBody.innerHTML = html;
    listTable.hidden = false;
    listStatus.hidden = true;
}

async function refresh() {
    const q = qInput ? qInput.value.trim() : "";
    writeQToUrl(q);
    listError.hidden = true;
    listError.textContent = "";
    listStatus.textContent = "Loading…";
    listStatus.hidden = false;
    listSummary.hidden = true;
    emptyState.hidden = true;
    countChip.hidden = true;
    try {
        const env = await listSubmitters(slug, q ? { q } : {});
        renderRows(env.items);
        listSummary.textContent = `Showing ${env.items.length} of ${env.total}.`;
        listSummary.hidden = false;
        countChip.textContent = `${env.total} submitter${env.total === 1 ? "" : "s"}`;
        countChip.hidden = false;
    } catch (err) {
        listTable.hidden = true;
        listStatus.hidden = true;
        emptyState.hidden = true;
        listError.textContent =
            formatDetail({ detail: err.detail }) || err.message;
        listError.hidden = false;
    }
}

if (form && slug && main) {
    form.addEventListener("submit", (event) => {
        event.preventDefault();
        refresh();
    });
    qInput.addEventListener("input", () => {
        // Live-search debounced lightly so the URL doesn't churn.
        clearTimeout(qInput._t);
        qInput._t = setTimeout(refresh, 200);
    });
    qInput.value = readQFromUrl();
    void refresh();
}
