// Shared API helpers for the Feedback Triage frontend.
// Same-origin JSON calls; no cookies, no third-party libraries.

const API_BASE = "/api/v1/feedback";

/**
 * Call the JSON API and return the parsed body.
 *
 * Throws an Error whose `.status` and `.detail` carry the server response
 * so callers can render a useful message.
 */
export async function apiFetch(path, { method = "GET", body, headers } = {}) {
    const init = {
        method,
        headers: { Accept: "application/json", ...(headers || {}) },
    };
    if (body !== undefined) {
        init.headers["Content-Type"] = "application/json";
        init.body = JSON.stringify(body);
    }

    const response = await fetch(path, init);

    if (response.status === 204) {
        return null;
    }

    const text = await response.text();
    let payload = null;
    if (text) {
        try {
            payload = JSON.parse(text);
        } catch {
            payload = { detail: text };
        }
    }

    if (!response.ok) {
        const err = new Error(
            formatDetail(payload) || `Request failed (${response.status})`,
        );
        err.status = response.status;
        err.detail = payload && payload.detail;
        throw err;
    }
    return payload;
}

/** Best-effort string from a FastAPI/Pydantic error body. */
export function formatDetail(payload) {
    if (!payload) return "";
    const detail = payload.detail;
    if (!detail) return "";
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
        return detail
            .map((d) => {
                const loc = Array.isArray(d.loc)
                    ? d.loc.filter((x) => x !== "body").join(".")
                    : "";
                return loc ? `${loc}: ${d.msg}` : d.msg;
            })
            .filter(Boolean)
            .join("; ");
    }
    return JSON.stringify(detail);
}

export function listFeedback(params) {
    const qs = new URLSearchParams();
    for (const [k, v] of Object.entries(params || {})) {
        if (v !== "" && v !== null && v !== undefined) qs.set(k, v);
    }
    const suffix = qs.toString() ? `?${qs.toString()}` : "";
    return apiFetch(`${API_BASE}${suffix}`);
}

export function getFeedback(id) {
    return apiFetch(`${API_BASE}/${encodeURIComponent(id)}`);
}

export function createFeedback(payload) {
    return apiFetch(API_BASE, { method: "POST", body: payload });
}

export function updateFeedback(id, payload) {
    return apiFetch(`${API_BASE}/${encodeURIComponent(id)}`, {
        method: "PATCH",
        body: payload,
    });
}

export function deleteFeedback(id) {
    return apiFetch(`${API_BASE}/${encodeURIComponent(id)}`, {
        method: "DELETE",
    });
}

export function formatDate(iso) {
    if (!iso) return "";
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    return d.toLocaleString();
}

export function escapeHtml(value) {
    if (value === null || value === undefined) return "";
    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}
