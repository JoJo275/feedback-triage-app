// Detail page: load existing item, save partial updates, delete.

import {
    deleteFeedback,
    formatDate,
    formatDetail,
    getFeedback,
    updateFeedback,
} from "./api.js";

const form = document.getElementById("edit-form");
const loadStatus = document.getElementById("load-status");
const errorEl = document.getElementById("form-error");
const successEl = document.getElementById("form-success");
const deleteButton = document.getElementById("delete-button");

const fieldNames = ["title", "description", "source", "pain_level", "status"];

function getIdFromPath() {
    const match = window.location.pathname.match(/\/feedback\/(\d+)/);
    return match ? match[1] : null;
}

function showError(message) {
    successEl.hidden = true;
    errorEl.textContent = message;
    errorEl.hidden = false;
}

function showSuccess(message) {
    errorEl.hidden = true;
    successEl.textContent = message;
    successEl.hidden = false;
}

function clearMessages() {
    errorEl.hidden = true;
    successEl.hidden = true;
}

function clearFieldErrors() {
    for (const name of fieldNames) {
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

function populateForm(item) {
    document.getElementById("meta-id").textContent = item.id;
    document.getElementById("meta-created").textContent = formatDate(
        item.created_at,
    );
    document.getElementById("meta-updated").textContent = formatDate(
        item.updated_at,
    );
    document.getElementById("title").value = item.title;
    document.getElementById("description").value = item.description || "";
    document.getElementById("source").value = item.source;
    document.getElementById("pain_level").value = String(item.pain_level);
    document.getElementById("status").value = item.status;
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

async function load() {
    const id = getIdFromPath();
    if (!id) {
        loadStatus.hidden = true;
        showError("Invalid feedback id in URL.");
        return;
    }
    try {
        const item = await getFeedback(id);
        populateForm(item);
        loadStatus.hidden = true;
        form.hidden = false;
    } catch (err) {
        loadStatus.hidden = true;
        if (err.status === 404) {
            showError("Feedback item not found.");
        } else {
            showError(err.message || "Failed to load feedback.");
        }
    }
}

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const id = getIdFromPath();
    if (!id) return;
    clearMessages();
    clearFieldErrors();

    const saveButton = form.querySelector('button[type="submit"]');
    saveButton.disabled = true;
    try {
        const updated = await updateFeedback(id, buildPayload());
        populateForm(updated);
        showSuccess("Saved.");
    } catch (err) {
        markInvalid(err.detail);
        showError(formatDetail({ detail: err.detail }) || err.message);
    } finally {
        saveButton.disabled = false;
    }
});

deleteButton.addEventListener("click", async () => {
    const id = getIdFromPath();
    if (!id) return;
    if (!window.confirm("Delete this feedback item? This cannot be undone.")) {
        return;
    }
    clearMessages();
    deleteButton.disabled = true;
    try {
        await deleteFeedback(id);
        window.location.assign("/");
    } catch (err) {
        deleteButton.disabled = false;
        showError(err.message || "Failed to delete feedback.");
    }
});

load();
