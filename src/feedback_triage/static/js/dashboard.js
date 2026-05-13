// Workspace dashboard controls.
//
// Keeps the dense/medium/light/custom density presets in sync with
// dashboard layout visibility and persists user choices in localStorage.

const layout = document.querySelector("[data-dashboard-layout]");
if (!layout) {
    // Not on the dashboard page.
} else {
    const densitySelect = document.getElementById("dashboard-density");
    const widgetInputs = Array.from(
        document.querySelectorAll("input[data-widget]"),
    );

    const DENSITY_KEY = "sn.dashboard.density";
    const WIDGETS_KEY = "sn.dashboard.widgets";

    function safeGetItem(key) {
        try {
            return window.localStorage.getItem(key);
        } catch {
            return null;
        }
    }

    function safeSetItem(key, value) {
        try {
            window.localStorage.setItem(key, value);
        } catch {
            // Ignore storage write failures (private mode/quota).
        }
    }

    function readWidgetState() {
        const raw = safeGetItem(WIDGETS_KEY);
        if (!raw) return {};
        try {
            const parsed = JSON.parse(raw);
            return parsed && typeof parsed === "object" ? parsed : {};
        } catch {
            return {};
        }
    }

    function writeWidgetState() {
        const payload = {};
        widgetInputs.forEach((input) => {
            const widgetId = input.dataset.widget;
            if (widgetId) payload[widgetId] = input.checked;
        });
        safeSetItem(WIDGETS_KEY, JSON.stringify(payload));
    }

    function applyCustomVisibility() {
        const isCustom = layout.dataset.density === "custom";
        widgetInputs.forEach((input) => {
            const widgetId = input.dataset.widget;
            if (!widgetId) return;
            const section = layout.querySelector(
                `[data-widget-section="${widgetId}"]`,
            );
            if (!section) return;
            section.hidden = isCustom ? !input.checked : false;
        });
    }

    function applyDensity(value) {
        layout.dataset.density = value;
        if (densitySelect) densitySelect.value = value;
        safeSetItem(DENSITY_KEY, value);
        applyCustomVisibility();
    }

    const storedWidgets = readWidgetState();
    widgetInputs.forEach((input) => {
        const widgetId = input.dataset.widget;
        if (!widgetId) return;
        if (Object.prototype.hasOwnProperty.call(storedWidgets, widgetId)) {
            input.checked = Boolean(storedWidgets[widgetId]);
        }
        input.addEventListener("change", () => {
            writeWidgetState();
            applyCustomVisibility();
        });
    });

    const allowedDensities = densitySelect
        ? Array.from(densitySelect.options).map((option) => option.value)
        : ["dense", "medium", "light", "custom"];
    const storedDensity = safeGetItem(DENSITY_KEY);
    const initialDensity =
        storedDensity && allowedDensities.includes(storedDensity)
            ? storedDensity
            : "dense";

    if (densitySelect) {
        densitySelect.addEventListener("change", () => {
            applyDensity(densitySelect.value || "dense");
        });
    }

    applyDensity(initialDensity);
}
