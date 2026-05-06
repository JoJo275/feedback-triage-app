// theme.js — dormant theme switcher (PR 1.9).
//
// Wires the sidebar's #theme-switcher button to `data-theme` on the
// <html> element, persisted to localStorage under the key
// `sn-theme`. Dark-mode CSS tokens already exist in tokens.css from
// PR 1.1; this script only flips the attribute. Activating dark mode
// end-to-end (visual QA across every page, persisted per user in
// the DB) is a Phase 4 deliverable — see PR 4.1.
//
// On first paint we apply any persisted choice synchronously to
// avoid a light-then-dark flash. Falls back to `prefers-color-scheme`
// when nothing is persisted.

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

    function persist(theme) {
        try {
            window.localStorage.setItem(STORAGE_KEY, theme);
        } catch (err) {
            // localStorage disabled (private mode, quota); the theme
            // applies for this page load and re-asks next time.
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
            persist(next);
        });
    });
})();
