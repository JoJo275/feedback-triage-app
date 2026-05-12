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
        node.textContent =
            typeof msg === "string" && msg.trim() ? msg : "Request failed.";
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

    function detailObjectToText(detail) {
        if (!detail || typeof detail !== "object") return "";
        if (typeof detail.message === "string" && detail.message.trim()) {
            return detail.message;
        }
        if (typeof detail.msg === "string" && detail.msg.trim()) {
            return detail.msg;
        }
        try {
            return JSON.stringify(detail);
        } catch (_) {
            return "";
        }
    }

    function detailToText(detail) {
        if (!detail) return "";
        if (typeof detail === "string") return detail;
        if (Array.isArray(detail)) {
            return detail
                .map(function (entry) {
                    if (!entry) return "";
                    if (typeof entry === "string") return entry;
                    if (typeof entry !== "object") return String(entry);

                    const loc = Array.isArray(entry.loc)
                        ? entry.loc
                              .filter(function (part) {
                                  return part !== "body";
                              })
                              .join(".")
                        : "";
                    const msg =
                        typeof entry.msg === "string"
                            ? entry.msg
                            : detailObjectToText(entry);
                    return loc && msg ? loc + ": " + msg : msg;
                })
                .filter(Boolean)
                .join("; ");
        }
        if (typeof detail === "object") {
            return detailObjectToText(detail);
        }
        return String(detail);
    }

    function errorMessageFromPayload(payload, fallback) {
        const detail =
            payload && Object.prototype.hasOwnProperty.call(payload, "detail")
                ? payload.detail
                : payload;
        const message = detailToText(detail);
        return message || fallback;
    }

    function setPasswordToggleState(toggle, input, reveal) {
        input.type = reveal ? "text" : "password";
        toggle.textContent = reveal ? "Hide" : "Show";
        toggle.setAttribute("aria-pressed", reveal ? "true" : "false");
        toggle.setAttribute(
            "aria-label",
            reveal ? "Hide password" : "Show password",
        );
    }

    function resetPasswordToggles(scope) {
        if (!scope) return;
        const toggles = scope.querySelectorAll("[data-password-toggle]");
        toggles.forEach(function (node) {
            if (!(node instanceof HTMLButtonElement)) return;
            const targetId = node.getAttribute("data-target-input");
            if (!targetId) return;
            const input = document.getElementById(targetId);
            if (!(input instanceof HTMLInputElement)) return;
            setPasswordToggleState(node, input, false);
        });
    }

    function bindPasswordToggles() {
        const toggles = document.querySelectorAll("[data-password-toggle]");
        toggles.forEach(function (node) {
            if (!(node instanceof HTMLButtonElement)) return;
            const targetId = node.getAttribute("data-target-input");
            if (!targetId) return;
            const input = document.getElementById(targetId);
            if (!(input instanceof HTMLInputElement)) return;

            setPasswordToggleState(node, input, input.type === "text");
            node.addEventListener("click", function () {
                setPasswordToggleState(node, input, input.type === "password");
                input.focus();
            });
        });
    }

    function bindLogin() {
        const form = document.getElementById("login-form");
        if (!form) return;
        const errorNode = document.getElementById("login-error");
        form.addEventListener("submit", async function (event) {
            event.preventDefault();
            if (errorNode) {
                errorNode.hidden = true;
            }
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
            showError(
                errorNode,
                errorMessageFromPayload(result.data, "Sign-in failed."),
            );
        });
    }

    function bindSignup() {
        const form = document.getElementById("signup-form");
        if (!form) return;
        const errorNode = document.getElementById("signup-error");
        const successNode = document.getElementById("signup-success");
        form.addEventListener("submit", async function (event) {
            event.preventDefault();
            if (errorNode) {
                errorNode.hidden = true;
            }
            if (successNode) {
                successNode.hidden = true;
            }
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
                resetPasswordToggles(form);
                return;
            }
            showError(
                errorNode,
                errorMessageFromPayload(result.data, "Sign-up failed."),
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
            if (errorNode) {
                errorNode.hidden = true;
            }
            if (successNode) {
                successNode.hidden = true;
            }
            const result = await postJson("/api/v1/auth/reset-password", {
                token: form.token.value,
                new_password: form.new_password.value,
            });
            if (result.ok) {
                showSuccess(successNode);
                form.reset();
                return;
            }
            showError(
                errorNode,
                errorMessageFromPayload(result.data, "Reset failed."),
            );
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
        bindPasswordToggles();
        bindLogin();
        bindSignup();
        bindForgot();
        bindReset();
        bindVerify();
    });
})();
