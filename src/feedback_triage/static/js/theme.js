// theme.js — sidebar theme switcher (PR 1.9 + PR 4.1).
//
// Wires the sidebar's #theme-switcher button to `data-theme` on the
// <html> element, persisted in two places:
//
//  1. localStorage under `sn-theme` so the next page load on the
//     same device paints the right colours synchronously, before
//     any network round-trip.
//  2. The signed-in user's `theme_preference` column via
//     `PATCH /api/v1/users/me`, so the choice follows the user
//     across devices and survives `localStorage` loss.
//
// Server persistence is fail-soft: the API call is fire-and-forget,
// non-2xx responses (including 401 when the cookie is missing or
// expired) are swallowed silently. The local change has already
// taken effect by then; the cross-device sync just won't happen.
//
// On first paint we apply any persisted choice synchronously to
// avoid a light-then-dark flash. Falls back to `prefers-color-scheme`
// when nothing is persisted. Once the page has loaded we also reach
// out to `GET /api/v1/auth/me` to reconcile a server-side preference
// that may have been set on another device — also fail-soft.

(function () {
    "use strict";

    var STORAGE_KEY = "sn-theme";
    var THEMES = ["light", "dark"];
    var root = document.documentElement;

    function readStored() {
        try {
            var raw = window.localStorage.getItem(STORAGE_KEY);
            return THEMES.indexOf(raw) >= 0 ? raw : null;
        } catch (err) {
            return null;
        }
    }

    function systemTheme() {
        if (
            window.matchMedia &&
            window.matchMedia("(prefers-color-scheme: dark)").matches
        ) {
            return "dark";
        }
        return "light";
    }

    function applyTheme(theme) {
        root.setAttribute("data-theme", theme);
        var btn = document.getElementById("theme-switcher");
        if (btn) {
            btn.setAttribute(
                "aria-pressed",
                theme === "dark" ? "true" : "false",
            );
            btn.textContent = theme === "dark" ? "Light theme" : "Dark theme";
        }
    }

    function persistLocal(theme) {
        try {
            window.localStorage.setItem(STORAGE_KEY, theme);
        } catch (err) {
            // localStorage disabled (private mode, quota); the theme
            // applies for this page load and re-asks next time.
        }
    }

    function persistRemote(theme) {
        // Fire-and-forget. We never await this and we never surface
        // failures — the local toggle has already taken effect.
        try {
            fetch("/api/v1/users/me", {
                method: "PATCH",
                headers: {
                    "Content-Type": "application/json",
                    Accept: "application/json",
                },
                credentials: "same-origin",
                body: JSON.stringify({ theme_preference: theme }),
            }).catch(function () {
                // Network error / offline / CSP block. Ignored.
            });
        } catch (err) {
            // `fetch` not available (very old browser); ignored.
        }
    }

    function reconcileFromServer() {
        // After first paint, ask the server what it thinks the
        // user's preference is and adopt that if it differs from
        // what we just rendered. Anonymous callers get a 401 and
        // we leave the local choice alone.
        try {
            fetch("/api/v1/auth/me", {
                method: "GET",
                headers: { Accept: "application/json" },
                credentials: "same-origin",
            })
                .then(function (resp) {
                    if (!resp.ok) {
                        return null;
                    }
                    return resp.json();
                })
                .then(function (data) {
                    if (!data || !data.user) {
                        return;
                    }
                    var pref = data.user.theme_preference;
                    var target = null;
                    if (pref === "light" || pref === "dark") {
                        target = pref;
                    } else if (pref === "system") {
                        target = systemTheme();
                    }
                    if (target && root.getAttribute("data-theme") !== target) {
                        applyTheme(target);
                        persistLocal(target);
                    }
                })
                .catch(function () {
                    // Ignored — see persistRemote.
                });
        } catch (err) {
            // `fetch` not available; ignored.
        }
    }

    var initial = readStored() || systemTheme();
    applyTheme(initial);

    document.addEventListener("DOMContentLoaded", function () {
        var btn = document.getElementById("theme-switcher");
        if (!btn) {
            return;
        }
        // Re-apply on DOM ready so the button label/aria-pressed are
        // correct even if the script ran before the element existed.
        applyTheme(root.getAttribute("data-theme") || initial);
        btn.addEventListener("click", function () {
            var current = root.getAttribute("data-theme") || "light";
            var next = current === "dark" ? "light" : "dark";
            applyTheme(next);
            persistLocal(next);
            persistRemote(next);
        });
        // Best-effort cross-device sync. The sidebar only renders on
        // authenticated shells, so this fetch is reasonably likely
        // to return 200; on the rare anon page that loads it the
        // 401 is swallowed.
        reconcileFromServer();
    });
})();
