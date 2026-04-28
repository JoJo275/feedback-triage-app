// Create page: submit form, redirect to detail on success.

import { createFeedback, formatDetail } from "./api.js";

const form = document.getElementById("create-form");
const errorEl = document.getElementById("form-error");

const fields = ["title", "description", "source", "pain_level", "status"];

function clearFieldErrors() {
    for (const name of fields) {
        const el = document.getElementById(name);
        if (el) el.removeAttribute("aria-invalid");
    }
}

function markInvalid(detail) {
    if (!Array.isArray(detail)) return;
    for (const item of detail) {
        if (!Array.isArray(item.loc)) continue;
        const field = item.loc[item.loc.length - 1];
        const el = document.getElementById(field);
        if (el) el.setAttribute("aria-invalid", "true");
    }
}

function showError(message) {
    errorEl.textContent = message;
    errorEl.hidden = false;
}

function clearError() {
    errorEl.textContent = "";
    errorEl.hidden = true;
}

function buildPayload() {
    const data = new FormData(form);
    const description = (data.get("description") || "").trim();
    return {
        title: (data.get("title") || "").trim(),
        description: description === "" ? null : description,
        source: data.get("source"),
        pain_level: Number(data.get("pain_level")),
        status: data.get("status"),
    };
}

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearError();
    clearFieldErrors();

    const submitButton = form.querySelector('button[type="submit"]');
    submitButton.disabled = true;
    try {
        const created = await createFeedback(buildPayload());
        window.location.assign(`/feedback/${created.id}`);
    } catch (err) {
        submitButton.disabled = false;
        markInvalid(err.detail);
        showError(formatDetail({ detail: err.detail }) || err.message);
    }
});
