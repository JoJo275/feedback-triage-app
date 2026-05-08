// Auth-page form glue.
//
// Each page binds the same script and conditionally wires whichever
// form id it owns. We keep this Vanilla JS + Fetch — no bundler, no
// framework, no globals beyond what the page elements ask for. See
// docs/notes/frontend-conventions.md.
//
// State-class toggling only: the script flips ``hidden``/``role``
// on existing elements; it never builds DOM beyond text content.

(function () {
    "use strict";

    const SAFE_REDIRECT = "/";
    const JSON_HEADERS = {
        "Content-Type": "application/json",
        Accept: "application/json",
    };

    function showError(node, msg) {
        if (!node) return;
        node.textContent = msg;
        node.hidden = false;
    }

    function showSuccess(node) {
        if (!node) return;
        node.hidden = false;
    }

    async function postJson(path, body) {
        const resp = await fetch(path, {
            method: "POST",
            headers: JSON_HEADERS,
            credentials: "same-origin",
            body: JSON.stringify(body),
        });
        let data = null;
        try {
            data = await resp.json();
        } catch (_) {
            // 204 / empty body — leave as null
        }
        return { ok: resp.ok, status: resp.status, data };
    }

    function bindLogin() {
        const form = document.getElementById("login-form");
        if (!form) return;
        const errorNode = document.getElementById("login-error");
        form.addEventListener("submit", async function (event) {
            event.preventDefault();
            errorNode.hidden = true;
            const result = await postJson("/api/v1/auth/login", {
                email: form.email.value,
                password: form.password.value,
            });
            if (result.ok) {
                // Prefer landing the user on their workspace dashboard
                // so they don't have to type the route into the URL bar.
                // Fall back to "/" if the response didn't include any
                // memberships (shouldn't happen for normal users, but
                // failing closed keeps the auth happy-path safe).
                const memberships =
                    (result.data && result.data.memberships) || [];
                if (memberships.length > 0) {
                    const slug = memberships[0].workspace_slug;
                    window.location.assign("/w/" + slug + "/dashboard");
                } else {
                    window.location.assign(SAFE_REDIRECT);
                }
                return;
            }
            const detail =
                (result.data && result.data.detail) || "Sign-in failed.";
            showError(errorNode, detail);
        });
    }

    function bindSignup() {
        const form = document.getElementById("signup-form");
        if (!form) return;
        const errorNode = document.getElementById("signup-error");
        const successNode = document.getElementById("signup-success");
        form.addEventListener("submit", async function (event) {
            event.preventDefault();
            errorNode.hidden = true;
            successNode.hidden = true;
            const body = {
                email: form.email.value,
                password: form.password.value,
            };
            const wsName = form.workspace_name.value.trim();
            if (wsName) body.workspace_name = wsName;
            const result = await postJson("/api/v1/auth/signup", body);
            if (result.ok) {
                showSuccess(successNode);
                form.reset();
                return;
            }
            const detail =
                (result.data && result.data.detail) || "Sign-up failed.";
            showError(
                errorNode,
                typeof detail === "string" ? detail : "Sign-up failed.",
            );
        });
    }

    function bindForgot() {
        const form = document.getElementById("forgot-form");
        if (!form) return;
        const successNode = document.getElementById("forgot-success");
        form.addEventListener("submit", async function (event) {
            event.preventDefault();
            successNode.hidden = true;
            await postJson("/api/v1/auth/forgot-password", {
                email: form.email.value,
            });
            // No-enumeration: always show the same neutral message.
            showSuccess(successNode);
            form.reset();
        });
    }

    function bindReset() {
        const form = document.getElementById("reset-form");
        if (!form) return;
        const errorNode = document.getElementById("reset-error");
        const successNode = document.getElementById("reset-success");
        form.addEventListener("submit", async function (event) {
            event.preventDefault();
            errorNode.hidden = true;
            successNode.hidden = true;
            const result = await postJson("/api/v1/auth/reset-password", {
                token: form.token.value,
                new_password: form.new_password.value,
            });
            if (result.ok) {
                showSuccess(successNode);
                form.reset();
                return;
            }
            const detail =
                (result.data && result.data.detail) || "Reset failed.";
            showError(errorNode, detail);
        });
    }

    async function bindVerify() {
        const node = document.getElementById("verify-status");
        if (!node) return;
        const successNode = document.getElementById("verify-success");
        const errorNode = document.getElementById("verify-error");
        const token = node.dataset.token || "";
        if (!token) {
            node.hidden = true;
            errorNode.hidden = false;
            return;
        }
        const result = await postJson("/api/v1/auth/verify-email", {
            token: token,
        });
        node.hidden = true;
        if (result.ok) {
            successNode.hidden = false;
        } else {
            errorNode.hidden = false;
        }
    }

    document.addEventListener("DOMContentLoaded", function () {
        bindLogin();
        bindSignup();
        bindForgot();
        bindReset();
        bindVerify();
    });
})();
