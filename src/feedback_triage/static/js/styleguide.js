// styleguide.js -- preset theme switcher for /styleguide (PR 4.2).
//
// Per ADR 056, the styleguide page exhibits four named token presets:
// `production` (default + locked production look), `basic`, `unique`,
// and `crazy`. The switcher flips a `data-theme="preset-<name>"`
// attribute on the page's `<main>` element; CSS custom properties
// declared under matching selectors in `tokens.css` cascade to every
// child component, so no element-specific styling is needed.
//
// Choice persists to `localStorage` under `styleguide-theme`. The
// preference is page-local: never sent to the server, never read by
// any other route, never set on `<html>` (so it cannot collide with
// the global light/dark switch in `theme.js`).

(function () {
    "use strict";

    var STORAGE_KEY = "styleguide-theme";
    var PRESETS = ["production", "basic", "unique", "crazy"];
    var DEFAULT_PRESET = "production";

    function isValid(preset) {
        return PRESETS.indexOf(preset) >= 0;
    }

    function readStored() {
        try {
            var raw = window.localStorage.getItem(STORAGE_KEY);
            return isValid(raw) ? raw : null;
        } catch (err) {
            return null;
        }
    }

    function persist(preset) {
        try {
            window.localStorage.setItem(STORAGE_KEY, preset);
        } catch (err) {
            // localStorage disabled (private mode, quota): the
            // preset still applies for this page load.
        }
    }

    function apply(main, preset) {
        if (!isValid(preset)) {
            preset = DEFAULT_PRESET;
        }
        main.setAttribute("data-theme", "preset-" + preset);
    }

    function syncRadios(fieldset, preset) {
        var inputs = fieldset.querySelectorAll('input[type="radio"]');
        for (var i = 0; i < inputs.length; i += 1) {
            inputs[i].checked = inputs[i].value === preset;
        }
    }

    function init() {
        var main = document.getElementById("main");
        var fieldset = document.getElementById("sg-preset-switcher");
        if (!main || !fieldset) {
            return;
        }

        var initial = readStored() || DEFAULT_PRESET;
        apply(main, initial);
        syncRadios(fieldset, initial);

        fieldset.addEventListener("change", function (event) {
            var target = event.target;
            if (
                !target ||
                target.name !== "styleguide-theme" ||
                !isValid(target.value)
            ) {
                return;
            }
            apply(main, target.value);
            persist(target.value);
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
