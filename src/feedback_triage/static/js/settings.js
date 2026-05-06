// Settings page logic (PR 2.5).
//
// One module wires four independent forms against the existing
// /api/v1 endpoints so the owner can rename the workspace, toggle
// the public-submit kill switch, invite/remove members, and run
// tag CRUD without leaving the page.
//
// Owner-only sections are gated server-side by the template; this
// script defensively no-ops if their DOM nodes aren't present, so
// non-owner pages don't throw while booting.

import { apiFetch, escapeHtml, formatDate } from "./api.js";
import { workspaceSlug } from "./api_v2.js";

const slug = workspaceSlug();
const main = document.getElementById("main");
const isOwner = main && main.dataset.isOwner === "true";

const statusEl = document.getElementById("settings-status");
const errorEl = document.getElementById("settings-error");

function showStatus(message) {
    if (!statusEl) return;
    statusEl.textContent = message;
    statusEl.hidden = false;
    if (errorEl) errorEl.hidden = true;
}

function showError(err) {
    if (!errorEl) return;
    errorEl.textContent = (err && err.message) || "Something went wrong.";
    errorEl.hidden = false;
    if (statusEl) statusEl.hidden = true;
}

function clearMessages() {
    if (statusEl) statusEl.hidden = true;
    if (errorEl) errorEl.hidden = true;
}

// ---------------------------------------------------------------------------
// Workspace info
// ---------------------------------------------------------------------------

const workspaceForm = document.getElementById("workspace-form");
if (workspaceForm && isOwner) {
    workspaceForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        clearMessages();
        const name = document.getElementById("workspace-name").value.trim();
        if (!name) {
            showError(new Error("Name must not be blank."));
            return;
        }
        try {
            const updated = await apiFetch(
                `/api/v1/workspaces/${encodeURIComponent(slug)}`,
                { method: "PATCH", body: { name } },
            );
            showStatus(`Workspace renamed to "${updated.name}".`);
        } catch (err) {
            showError(err);
        }
    });
}

// ---------------------------------------------------------------------------
// Public-submit toggle
// ---------------------------------------------------------------------------

const publicSubmitForm = document.getElementById("public-submit-form");
if (publicSubmitForm) {
    publicSubmitForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        clearMessages();
        const enabled = document.getElementById("public-submit-toggle").checked;
        try {
            await apiFetch(`/api/v1/workspaces/${encodeURIComponent(slug)}`, {
                method: "PATCH",
                body: { public_submit_enabled: enabled },
            });
            showStatus(
                enabled
                    ? "Public submission form is now open."
                    : "Public submission form is now closed.",
            );
        } catch (err) {
            showError(err);
        }
    });
}

// ---------------------------------------------------------------------------
// Members
// ---------------------------------------------------------------------------

const membersTable = document.getElementById("members-table");
const membersBody = document.getElementById("members-body");
const membersStatus = document.getElementById("members-status");
const inviteForm = document.getElementById("invite-form");

function renderMembers(items) {
    if (!membersBody || !membersTable) return;
    membersBody.innerHTML = "";
    if (items.length === 0) {
        membersTable.hidden = true;
        if (membersStatus) {
            membersStatus.textContent = "No members yet.";
            membersStatus.hidden = false;
        }
        return;
    }
    for (const m of items) {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${escapeHtml(m.user.email)}</td>
            <td>${escapeHtml(m.role)}</td>
            <td>${escapeHtml(formatDate(m.joined_at))}</td>
            <td>
                <button
                    type="button"
                    class="sn-button sn-button--danger"
                    data-action="remove-member"
                    data-user-id="${escapeHtml(m.user.id)}"
                >Remove</button>
            </td>`;
        membersBody.appendChild(tr);
    }
    membersTable.hidden = false;
    if (membersStatus) membersStatus.hidden = true;
}

async function loadMembers() {
    if (!membersTable) return;
    try {
        const data = await apiFetch(
            `/api/v1/workspaces/${encodeURIComponent(slug)}/members`,
        );
        renderMembers(data.items || []);
    } catch (err) {
        if (membersStatus) {
            membersStatus.textContent =
                (err && err.message) || "Failed to load members.";
        }
    }
}

if (membersBody) {
    membersBody.addEventListener("click", async (event) => {
        const target = event.target;
        if (
            !(target instanceof HTMLElement) ||
            target.dataset.action !== "remove-member"
        )
            return;
        const userId = target.dataset.userId;
        if (!userId) return;
        clearMessages();
        try {
            await apiFetch(
                `/api/v1/workspaces/${encodeURIComponent(slug)}/members/${encodeURIComponent(userId)}`,
                { method: "DELETE" },
            );
            showStatus("Member removed.");
            await loadMembers();
        } catch (err) {
            showError(err);
        }
    });
}

if (inviteForm) {
    inviteForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        clearMessages();
        const email = document.getElementById("invite-email").value.trim();
        const role = document.getElementById("invite-role").value;
        if (!email) {
            showError(new Error("Email is required."));
            return;
        }
        try {
            await apiFetch(
                `/api/v1/workspaces/${encodeURIComponent(slug)}/invitations`,
                { method: "POST", body: { email, role } },
            );
            showStatus(`Invitation sent to ${email}.`);
            inviteForm.reset();
        } catch (err) {
            showError(err);
        }
    });
}

// ---------------------------------------------------------------------------
// Tags
// ---------------------------------------------------------------------------

const tagsTable = document.getElementById("tags-table");
const tagsBody = document.getElementById("tags-body");
const tagsStatus = document.getElementById("tags-status");
const tagForm = document.getElementById("tag-form");

function renderTags(items) {
    if (!tagsBody || !tagsTable) return;
    tagsBody.innerHTML = "";
    if (items.length === 0) {
        tagsTable.hidden = true;
        if (tagsStatus) {
            tagsStatus.textContent = "No tags yet.";
            tagsStatus.hidden = false;
        }
        return;
    }
    for (const t of items) {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${escapeHtml(t.name)}</td>
            <td><code>${escapeHtml(t.slug)}</code></td>
            <td>${escapeHtml(t.color)}</td>
            <td>
                <button
                    type="button"
                    class="sn-button sn-button--danger"
                    data-action="remove-tag"
                    data-tag-id="${escapeHtml(t.id)}"
                >Delete</button>
            </td>`;
        tagsBody.appendChild(tr);
    }
    tagsTable.hidden = false;
    if (tagsStatus) tagsStatus.hidden = true;
}

async function loadTags() {
    if (!tagsTable) return;
    try {
        const data = await apiFetch(`/api/v1/tags`, {
            headers: { "X-Workspace-Slug": slug },
        });
        renderTags(data.items || []);
    } catch (err) {
        if (tagsStatus) {
            tagsStatus.textContent =
                (err && err.message) || "Failed to load tags.";
        }
    }
}

if (tagsBody) {
    tagsBody.addEventListener("click", async (event) => {
        const target = event.target;
        if (
            !(target instanceof HTMLElement) ||
            target.dataset.action !== "remove-tag"
        )
            return;
        const tagId = target.dataset.tagId;
        if (!tagId) return;
        clearMessages();
        try {
            await apiFetch(`/api/v1/tags/${encodeURIComponent(tagId)}`, {
                method: "DELETE",
                headers: { "X-Workspace-Slug": slug },
            });
            showStatus("Tag deleted.");
            await loadTags();
        } catch (err) {
            showError(err);
        }
    });
}

if (tagForm) {
    tagForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        clearMessages();
        const name = document.getElementById("tag-name").value.trim();
        const tagSlug = document.getElementById("tag-slug").value.trim();
        const color = document.getElementById("tag-color").value;
        if (!name || !tagSlug) {
            showError(new Error("Name and slug are required."));
            return;
        }
        try {
            await apiFetch(`/api/v1/tags`, {
                method: "POST",
                headers: { "X-Workspace-Slug": slug },
                body: { name, slug: tagSlug, color },
            });
            showStatus(`Tag "${name}" created.`);
            tagForm.reset();
            document.getElementById("tag-color").value = "slate";
            await loadTags();
        } catch (err) {
            showError(err);
        }
    });
}

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------

if (isOwner) {
    loadMembers();
    loadTags();
}
