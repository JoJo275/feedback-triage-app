// v2 API helpers. Workspace-scoped: every call sends the
// `X-Workspace-Slug` header so the FastAPI tenancy resolver locks
// the request to the correct tenant (docs/project/spec/v2/api.md).

import { apiFetch, formatDetail } from "./api.js";

export function workspaceSlug(root = document) {
    const main = root.querySelector("[data-workspace-slug]");
    return main ? main.dataset.workspaceSlug : "";
}

function withSlug(slug, init = {}) {
    const headers = { ...(init.headers || {}), "X-Workspace-Slug": slug };
    return { ...init, headers };
}

export function listFeedbackV2(slug, params) {
    const qs = new URLSearchParams();
    for (const [k, v] of Object.entries(params || {})) {
        if (v !== "" && v !== null && v !== undefined) qs.set(k, v);
    }
    const suffix = qs.toString() ? `?${qs.toString()}` : "";
    return apiFetch(`/api/v1/feedback${suffix}`, withSlug(slug));
}

export function getFeedbackV2(slug, id) {
    return apiFetch(
        `/api/v1/feedback/${encodeURIComponent(id)}`,
        withSlug(slug),
    );
}

export function patchFeedbackV2(slug, id, payload) {
    return apiFetch(
        `/api/v1/feedback/${encodeURIComponent(id)}`,
        withSlug(slug, { method: "PATCH", body: payload }),
    );
}

export function deleteFeedbackV2(slug, id) {
    return apiFetch(
        `/api/v1/feedback/${encodeURIComponent(id)}`,
        withSlug(slug, { method: "DELETE" }),
    );
}

export function listNotes(slug, id) {
    return apiFetch(
        `/api/v1/feedback/${encodeURIComponent(id)}/notes`,
        withSlug(slug),
    );
}

export function createNote(slug, id, body) {
    return apiFetch(
        `/api/v1/feedback/${encodeURIComponent(id)}/notes`,
        withSlug(slug, { method: "POST", body: { body } }),
    );
}

export function deleteNote(slug, id, noteId) {
    return apiFetch(
        `/api/v1/feedback/${encodeURIComponent(id)}/notes/${encodeURIComponent(noteId)}`,
        withSlug(slug, { method: "DELETE" }),
    );
}

export function replaceTags(slug, id, tagIds) {
    return apiFetch(
        `/api/v1/feedback/${encodeURIComponent(id)}/tags`,
        withSlug(slug, { method: "POST", body: { tag_ids: tagIds } }),
    );
}

export function listTags(slug) {
    return apiFetch(`/api/v1/tags`, withSlug(slug));
}

export { formatDetail };
