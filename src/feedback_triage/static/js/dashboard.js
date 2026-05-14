// Workspace dashboard controls.
//
// Supports density presets, custom widget visibility, and a user-driven
// layout mode where widgets can be reordered and resized.

const layout = document.querySelector("[data-dashboard-layout]");
const canvas = document.querySelector("[data-dashboard-canvas]");

if (!layout || !canvas) {
    // Not on the dashboard page.
} else {
    const densitySelect = document.getElementById("dashboard-density");
    const widgetInputs = Array.from(
        document.querySelectorAll("input[data-widget]"),
    );
    const editToggle = document.querySelector("[data-dashboard-edit-toggle]");
    const resetLayoutButton = document.querySelector(
        "[data-dashboard-reset-layout]",
    );
    const reactEditorUrl = editToggle?.dataset.reactEditorUrl || "";
    const widgets = Array.from(canvas.querySelectorAll("[data-widget-id]"));

    const workspaceSlug = layout.dataset.workspaceSlug || "default";
    const STORAGE_PREFIX = `sn.dashboard.${workspaceSlug}`;
    const DENSITY_KEY = `${STORAGE_PREFIX}.density`;
    const WIDGETS_KEY = `${STORAGE_PREFIX}.widgets`;
    const LAYOUT_KEY = `${STORAGE_PREFIX}.layout`;

    const GRID_COLUMNS = 12;
    const GRID_MAX_ROWS = 120;
    const RESIZE_MIN_ROWS = 2;
    const RESIZE_MAX_ROWS = 40;
    const RESIZE_HIT_SLOP = 12;
    const DRAG_ELEVATION = 20;
    const DRAG_START_THRESHOLD_PX = 10;
    const DRAG_SHADOW_CLASS = "sn-widget-drop-shadow";
    const CUSTOM_GRID_GAP_REM = 1.2;
    const CUSTOM_ROW_UNIT_REM = 1;

    const DEFAULT_SPANS = {
        "kpi-total-signals": { cols: 2, rows: 4 },
        "kpi-needs-action": { cols: 2, rows: 4 },
        "kpi-high-pain-signals": { cols: 2, rows: 4 },
        "kpi-median-triage-time": { cols: 2, rows: 4 },
        "kpi-net-backlog-change": { cols: 2, rows: 4 },
        "signals-over-time": { cols: 6, rows: 9 },
        "status-mix": { cols: 3, rows: 9 },
        "aging-health": { cols: 3, rows: 9 },
        "top-tags": { cols: 3, rows: 8 },
        "pain-distribution": { cols: 3, rows: 8 },
        "segment-impact": { cols: 3, rows: 8 },
        "source-breakdown": { cols: 3, rows: 8 },
        "team-workload": { cols: 8, rows: 9 },
        "backlog-needs-attention": { cols: 4, rows: 9 },
        "action-queue": { cols: 12, rows: 11 },
    };

    const MIN_SPANS = {
        "kpi-total-signals": { cols: 1, rows: 2 },
        "kpi-needs-action": { cols: 1, rows: 2 },
        "kpi-high-pain-signals": { cols: 1, rows: 2 },
        "kpi-median-triage-time": { cols: 1, rows: 2 },
        "kpi-net-backlog-change": { cols: 1, rows: 2 },
        "signals-over-time": { cols: 4, rows: 7 },
        "status-mix": { cols: 3, rows: 7 },
        "aging-health": { cols: 3, rows: 7 },
        "top-tags": { cols: 3, rows: 6 },
        "pain-distribution": { cols: 3, rows: 6 },
        "segment-impact": { cols: 3, rows: 6 },
        "source-breakdown": { cols: 3, rows: 6 },
        "team-workload": { cols: 5, rows: 8 },
        "backlog-needs-attention": { cols: 3, rows: 8 },
        "action-queue": { cols: 8, rows: 9 },
    };

    const widgetById = new Map();
    widgets.forEach((widget) => {
        const widgetId = widget.dataset.widgetId;
        if (!widgetId) return;
        widgetById.set(widgetId, widget);
    });

    const defaultOrder = Array.from(widgetById.keys());
    const DEFAULT_WIDGET_LAYOUT = buildPackedLayout(
        defaultOrder,
        DEFAULT_SPANS,
    );

    let layoutState = {
        widgets: cloneWidgetLayout(DEFAULT_WIDGET_LAYOUT),
    };
    let customLayoutEnabled = false;
    let editMode = false;
    let dragState = null;
    let resizeState = null;
    let dragShadow = null;

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

    function safeRemoveItem(key) {
        try {
            window.localStorage.removeItem(key);
        } catch {
            // Ignore storage write failures (private mode/quota).
        }
    }

    function clamp(value, min, max) {
        return Math.min(Math.max(value, min), max);
    }

    function getDefaultSpan(widgetId) {
        const defaults = DEFAULT_SPANS[widgetId];
        return {
            cols: defaults?.cols || 3,
            rows: defaults?.rows || 8,
        };
    }

    function getMinSpan(widgetId) {
        const mins = MIN_SPANS[widgetId];
        return {
            cols: mins?.cols || 1,
            rows: clamp(
                mins?.rows || RESIZE_MIN_ROWS,
                RESIZE_MIN_ROWS,
                RESIZE_MAX_ROWS,
            ),
        };
    }

    function cloneWidgetLayout(layoutMap) {
        const clone = {};
        defaultOrder.forEach((widgetId) => {
            const widget = layoutMap?.[widgetId] || {};
            clone[widgetId] = {
                col: Number(widget.col) || 1,
                row: Number(widget.row) || 1,
                cols: Number(widget.cols) || getDefaultSpan(widgetId).cols,
                rows: Number(widget.rows) || getDefaultSpan(widgetId).rows,
            };
        });
        return clone;
    }

    function normalizeWidgetGeometry(widgetId, geometry) {
        const defaults = getDefaultSpan(widgetId);
        const mins = getMinSpan(widgetId);

        const cols = clamp(
            Number(geometry?.cols) || defaults.cols,
            mins.cols,
            GRID_COLUMNS,
        );
        const rows = clamp(
            Number(geometry?.rows) || defaults.rows,
            mins.rows,
            RESIZE_MAX_ROWS,
        );
        const maxColStart = Math.max(1, GRID_COLUMNS - cols + 1);
        const maxRowStart = Math.max(1, GRID_MAX_ROWS - rows + 1);

        return {
            col: clamp(Number(geometry?.col) || 1, 1, maxColStart),
            row: clamp(Number(geometry?.row) || 1, 1, maxRowStart),
            cols,
            rows,
        };
    }

    function rectanglesOverlap(a, b) {
        return (
            a.col < b.col + b.cols &&
            a.col + a.cols > b.col &&
            a.row < b.row + b.rows &&
            a.row + a.rows > b.row
        );
    }

    function isPlacementFree(occupied, placement) {
        return occupied.every((rect) => !rectanglesOverlap(rect, placement));
    }

    function findFreePlacement(occupied, preferred) {
        const maxColStart = Math.max(1, GRID_COLUMNS - preferred.cols + 1);
        const maxRowStart = Math.max(1, GRID_MAX_ROWS - preferred.rows + 1);
        const preferredCol = clamp(preferred.col, 1, maxColStart);
        const preferredRow = clamp(preferred.row, 1, maxRowStart);

        for (let row = preferredRow; row <= maxRowStart; row += 1) {
            for (let col = preferredCol; col <= maxColStart; col += 1) {
                const candidate = {
                    col,
                    row,
                    cols: preferred.cols,
                    rows: preferred.rows,
                };
                if (isPlacementFree(occupied, candidate)) {
                    return candidate;
                }
            }
            for (let col = 1; col < preferredCol; col += 1) {
                const candidate = {
                    col,
                    row,
                    cols: preferred.cols,
                    rows: preferred.rows,
                };
                if (isPlacementFree(occupied, candidate)) {
                    return candidate;
                }
            }
        }

        for (let row = 1; row < preferredRow; row += 1) {
            for (let col = 1; col <= maxColStart; col += 1) {
                const candidate = {
                    col,
                    row,
                    cols: preferred.cols,
                    rows: preferred.rows,
                };
                if (isPlacementFree(occupied, candidate)) {
                    return candidate;
                }
            }
        }

        return {
            col: 1,
            row: maxRowStart,
            cols: preferred.cols,
            rows: preferred.rows,
        };
    }

    function resolveWidgetLayout(candidateWidgets, lockedWidgetId = null) {
        const resolved = {};
        const occupied = [];

        const isActive = (widgetId) => {
            const widget = widgetById.get(widgetId);
            return Boolean(widget && !widget.hidden);
        };
        const effectiveLockedId = isActive(lockedWidgetId)
            ? lockedWidgetId
            : null;

        if (effectiveLockedId && widgetById.has(effectiveLockedId)) {
            const lockedGeometry = normalizeWidgetGeometry(
                effectiveLockedId,
                candidateWidgets?.[effectiveLockedId] ||
                    DEFAULT_WIDGET_LAYOUT[effectiveLockedId],
            );
            resolved[effectiveLockedId] = lockedGeometry;
            occupied.push(lockedGeometry);
        }

        defaultOrder.forEach((widgetId) => {
            if (widgetId === effectiveLockedId) {
                return;
            }

            const preferred = normalizeWidgetGeometry(
                widgetId,
                candidateWidgets?.[widgetId] || DEFAULT_WIDGET_LAYOUT[widgetId],
            );

            if (!isActive(widgetId)) {
                resolved[widgetId] = preferred;
                return;
            }

            const placed = findFreePlacement(occupied, preferred);
            resolved[widgetId] = placed;
            occupied.push(placed);
        });

        return resolved;
    }

    function normalizeLayoutWidgets(candidateWidgets) {
        const normalized = {};
        defaultOrder.forEach((widgetId) => {
            normalized[widgetId] = normalizeWidgetGeometry(
                widgetId,
                candidateWidgets?.[widgetId] || DEFAULT_WIDGET_LAYOUT[widgetId],
            );
        });
        return normalized;
    }

    function collectOccupiedWidgets(layoutMap, excludedWidgetId) {
        const occupied = [];
        defaultOrder.forEach((widgetId) => {
            if (widgetId === excludedWidgetId) {
                return;
            }

            const widget = widgetById.get(widgetId);
            if (!widget || widget.hidden) {
                return;
            }

            const geometry = normalizeWidgetGeometry(
                widgetId,
                layoutMap?.[widgetId] || DEFAULT_WIDGET_LAYOUT[widgetId],
            );
            occupied.push(geometry);
        });
        return occupied;
    }

    function findNearestAvailablePlacement(widgetId, preferred, layoutMap) {
        const normalizedPreferred = normalizeWidgetGeometry(
            widgetId,
            preferred,
        );
        const occupied = collectOccupiedWidgets(layoutMap, widgetId);

        if (isPlacementFree(occupied, normalizedPreferred)) {
            return normalizedPreferred;
        }

        const maxColStart = Math.max(
            1,
            GRID_COLUMNS - normalizedPreferred.cols + 1,
        );
        const maxRowStart = Math.max(
            1,
            GRID_MAX_ROWS - normalizedPreferred.rows + 1,
        );

        let bestPlacement = null;
        let bestScore = Number.POSITIVE_INFINITY;

        for (let row = 1; row <= maxRowStart; row += 1) {
            for (let col = 1; col <= maxColStart; col += 1) {
                const candidate = {
                    col,
                    row,
                    cols: normalizedPreferred.cols,
                    rows: normalizedPreferred.rows,
                };

                if (!isPlacementFree(occupied, candidate)) {
                    continue;
                }

                const score =
                    Math.abs(col - normalizedPreferred.col) +
                    Math.abs(row - normalizedPreferred.row) * 1.75;
                if (score < bestScore) {
                    bestScore = score;
                    bestPlacement = candidate;
                }
            }
        }

        return bestPlacement || normalizedPreferred;
    }

    function buildPackedLayout(order, spanMap) {
        const packed = {};
        let cursorCol = 1;
        let cursorRow = 1;
        let rowHeight = 1;

        order.forEach((widgetId) => {
            const defaults = getDefaultSpan(widgetId);
            const mins = getMinSpan(widgetId);
            const source = spanMap?.[widgetId] || defaults;
            const cols = clamp(
                Number(source.cols) || defaults.cols,
                mins.cols,
                GRID_COLUMNS,
            );
            const rows = clamp(
                Number(source.rows) || defaults.rows,
                mins.rows,
                RESIZE_MAX_ROWS,
            );

            if (cursorCol + cols - 1 > GRID_COLUMNS) {
                cursorRow += rowHeight;
                cursorCol = 1;
                rowHeight = 1;
            }

            packed[widgetId] = {
                col: cursorCol,
                row: cursorRow,
                cols,
                rows,
            };

            cursorCol += cols;
            rowHeight = Math.max(rowHeight, rows);
        });

        return packed;
    }

    function legacyLayoutToWidgets(legacyOrder, legacySpans) {
        const preferredOrder = Array.isArray(legacyOrder)
            ? legacyOrder.filter((id) => widgetById.has(id))
            : [];
        const resolvedOrder = [
            ...preferredOrder,
            ...defaultOrder.filter((id) => !preferredOrder.includes(id)),
        ];
        const spanMap = {};
        resolvedOrder.forEach((widgetId) => {
            spanMap[widgetId] =
                legacySpans?.[widgetId] || getDefaultSpan(widgetId);
        });
        return buildPackedLayout(resolvedOrder, spanMap);
    }

    function getPlannedGridMetrics() {
        const canvasRect = canvas.getBoundingClientRect();
        const rootFontPx =
            Number.parseFloat(
                window.getComputedStyle(document.documentElement).fontSize,
            ) || 16;
        const columnGap = rootFontPx * CUSTOM_GRID_GAP_REM;
        const rowGap = rootFontPx * CUSTOM_GRID_GAP_REM;
        const rowUnit = rootFontPx * CUSTOM_ROW_UNIT_REM;
        const availableWidth =
            canvasRect.width - (GRID_COLUMNS - 1) * columnGap;
        const colUnit = availableWidth / GRID_COLUMNS;

        return {
            colUnit,
            rowUnit,
            colGap: columnGap,
            rowGap,
        };
    }

    function getGridMetrics() {
        const canvasRect = canvas.getBoundingClientRect();
        const plannedMetrics = getPlannedGridMetrics();
        if (canvas.dataset.layoutMode !== "custom") {
            return plannedMetrics;
        }

        const styles = window.getComputedStyle(canvas);
        const computedColumnGap = Number.parseFloat(styles.columnGap);
        const computedRowGap = Number.parseFloat(styles.rowGap);
        const columnGap = Number.isFinite(computedColumnGap)
            ? computedColumnGap
            : plannedMetrics.colGap;
        const rowGap = Number.isFinite(computedRowGap)
            ? computedRowGap
            : plannedMetrics.rowGap;
        const availableWidth =
            canvasRect.width - (GRID_COLUMNS - 1) * columnGap;
        const colUnit = availableWidth / GRID_COLUMNS;
        const rowUnit =
            Number.parseFloat(styles.gridAutoRows) ||
            Number.parseFloat(
                styles.getPropertyValue("--sn-widget-row-unit"),
            ) ||
            plannedMetrics.rowUnit;

        return {
            colUnit,
            rowUnit,
            colGap: columnGap,
            rowGap,
        };
    }

    function seedLayoutFromDom() {
        const canvasRect = canvas.getBoundingClientRect();
        const metrics = getPlannedGridMetrics();
        const seeded = {};

        defaultOrder.forEach((widgetId) => {
            const widget = widgetById.get(widgetId);
            if (!widget || widget.hidden) {
                return;
            }

            const rect = widget.getBoundingClientRect();
            if (rect.width <= 0 || rect.height <= 0) {
                return;
            }

            seeded[widgetId] = geometryFromRect(
                widgetId,
                rect,
                metrics,
                canvasRect,
            );
        });

        return seeded;
    }

    function geometryFromRect(widgetId, rect, metrics, canvasRect) {
        const mins = getMinSpan(widgetId);
        const colStep = metrics.colUnit + metrics.colGap;
        const rowStep = metrics.rowUnit + metrics.rowGap;

        const cols = clamp(
            Math.round((rect.width + metrics.colGap) / Math.max(colStep, 1)),
            mins.cols,
            GRID_COLUMNS,
        );
        const rows = clamp(
            Math.round((rect.height + metrics.rowGap) / Math.max(rowStep, 1)),
            mins.rows,
            RESIZE_MAX_ROWS,
        );

        const maxColStart = Math.max(1, GRID_COLUMNS - cols + 1);
        const maxRowStart = Math.max(1, GRID_MAX_ROWS - rows + 1);

        const col = clamp(
            Math.round((rect.left - canvasRect.left) / Math.max(colStep, 1)) +
                1,
            1,
            maxColStart,
        );
        const row = clamp(
            Math.round((rect.top - canvasRect.top) / Math.max(rowStep, 1)) + 1,
            1,
            maxRowStart,
        );

        return normalizeWidgetGeometry(widgetId, {
            col,
            row,
            cols,
            rows,
        });
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

    function normalizeLayoutState(candidate) {
        if (!candidate || typeof candidate !== "object") {
            return {
                widgets: cloneWidgetLayout(DEFAULT_WIDGET_LAYOUT),
            };
        }

        if (candidate.widgets && typeof candidate.widgets === "object") {
            return {
                widgets: normalizeLayoutWidgets(candidate.widgets),
            };
        }

        if (
            Array.isArray(candidate.order) ||
            (candidate.spans && typeof candidate.spans === "object")
        ) {
            const legacyWidgets = legacyLayoutToWidgets(
                candidate.order,
                candidate.spans,
            );
            return {
                widgets: normalizeLayoutWidgets(legacyWidgets),
            };
        }

        return {
            widgets: cloneWidgetLayout(DEFAULT_WIDGET_LAYOUT),
        };
    }

    function readLayoutState() {
        const raw = safeGetItem(LAYOUT_KEY);
        if (!raw) return null;
        try {
            const parsed = JSON.parse(raw);
            return normalizeLayoutState(parsed);
        } catch {
            return null;
        }
    }

    function writeLayoutState() {
        customLayoutEnabled = true;
        safeSetItem(LAYOUT_KEY, JSON.stringify(layoutState));
    }

    function resetLayoutState() {
        customLayoutEnabled = false;
        layoutState = normalizeLayoutState({});
        safeRemoveItem(LAYOUT_KEY);
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

        applyWidgetLayout();
        if (customLayoutEnabled) {
            writeLayoutState();
        }
    }

    function applyDensity(value) {
        layout.dataset.density = value;
        if (densitySelect) densitySelect.value = value;
        safeSetItem(DENSITY_KEY, value);
        applyCustomVisibility();
    }

    function applyLayoutMode() {
        canvas.dataset.layoutMode = customLayoutEnabled ? "custom" : "default";
        layout.dataset.editMode = editMode ? "true" : "false";
        if (resetLayoutButton) {
            resetLayoutButton.hidden = reactEditorUrl
                ? true
                : !customLayoutEnabled;
        }
    }

    function applyWidgetLayout() {
        defaultOrder.forEach((widgetId) => {
            const widget = widgetById.get(widgetId);
            if (!widget) return;
            const geometry = normalizeWidgetGeometry(
                widgetId,
                layoutState.widgets[widgetId] ||
                    DEFAULT_WIDGET_LAYOUT[widgetId],
            );
            layoutState.widgets[widgetId] = geometry;

            const baseSpan = getDefaultSpan(widgetId);
            const scale = clamp(
                Math.min(
                    geometry.cols / Math.max(baseSpan.cols, 1),
                    geometry.rows / Math.max(baseSpan.rows, 1),
                ),
                0.82,
                1.15,
            );

            widget.style.setProperty(
                "--widget-col-start",
                String(geometry.col),
            );
            widget.style.setProperty(
                "--widget-row-start",
                String(geometry.row),
            );
            widget.style.setProperty(
                "--widget-content-scale",
                scale.toFixed(3),
            );
            widget.style.setProperty(
                "--widget-col-span",
                String(geometry.cols),
            );
            widget.style.setProperty(
                "--widget-row-span",
                String(geometry.rows),
            );
        });
    }

    function applyWidgetPlacement(widgetId, nextGeometry) {
        const currentLayout = cloneWidgetLayout(layoutState.widgets);
        const preferred = normalizeWidgetGeometry(widgetId, nextGeometry);
        currentLayout[widgetId] = findNearestAvailablePlacement(
            widgetId,
            preferred,
            currentLayout,
        );
        layoutState.widgets = normalizeLayoutWidgets(currentLayout);
        applyWidgetLayout();
    }

    function activateCustomLayout(lockWidgetId = null) {
        if (customLayoutEnabled) {
            return;
        }

        const seededLayout = seedLayoutFromDom();
        const candidateLayout = {
            ...layoutState.widgets,
            ...seededLayout,
        };

        customLayoutEnabled = true;
        layoutState.widgets = normalizeLayoutWidgets(candidateLayout);
        applyLayoutMode();
        applyWidgetLayout();
    }

    function ensureDragShadow() {
        if (dragShadow?.isConnected) {
            return dragShadow;
        }

        const shadow = document.createElement("div");
        shadow.className = DRAG_SHADOW_CLASS;
        shadow.setAttribute("aria-hidden", "true");
        canvas.append(shadow);
        dragShadow = shadow;
        return shadow;
    }

    function showDragShadow(widgetId, geometry) {
        if (!customLayoutEnabled) {
            return;
        }

        const shadow = ensureDragShadow();
        const baseSpan = getDefaultSpan(widgetId);
        const scale = clamp(
            Math.min(
                geometry.cols / Math.max(baseSpan.cols, 1),
                geometry.rows / Math.max(baseSpan.rows, 1),
            ),
            0.82,
            1.15,
        );

        shadow.classList.add("is-visible");
        shadow.style.setProperty("--widget-col-start", String(geometry.col));
        shadow.style.setProperty("--widget-row-start", String(geometry.row));
        shadow.style.setProperty("--widget-col-span", String(geometry.cols));
        shadow.style.setProperty("--widget-row-span", String(geometry.rows));
        shadow.style.setProperty("--widget-content-scale", scale.toFixed(3));
    }

    function hideDragShadow() {
        if (!dragShadow) return;
        dragShadow.classList.remove("is-visible");
        dragShadow.style.removeProperty("--widget-col-start");
        dragShadow.style.removeProperty("--widget-row-start");
        dragShadow.style.removeProperty("--widget-col-span");
        dragShadow.style.removeProperty("--widget-row-span");
        dragShadow.style.removeProperty("--widget-content-scale");
    }

    function refreshEditButton() {
        if (!editToggle) return;
        if (reactEditorUrl) {
            editToggle.removeAttribute("aria-pressed");
            editToggle.textContent = "Edit widgets in React";
            editToggle.title = "Opens the React widget editor";
            return;
        }
        editToggle.setAttribute("aria-pressed", editMode ? "true" : "false");
        editToggle.textContent = editMode ? "Finish editing" : "Edit widgets";
    }

    function resizeCursorForDirection(direction) {
        switch (direction) {
            case "n":
            case "s":
                return "ns-resize";
            case "e":
            case "w":
                return "ew-resize";
            case "ne":
            case "sw":
                return "nesw-resize";
            case "nw":
            case "se":
                return "nwse-resize";
            default:
                return "nwse-resize";
        }
    }

    function setWidgetPointerMode(widget, mode) {
        if (!widget) return;
        if (!mode) {
            delete widget.dataset.pointerMode;
            return;
        }
        widget.dataset.pointerMode = mode;
    }

    function syncWidgetPointerModes() {
        widgetById.forEach((widget) => {
            if (!editMode) {
                delete widget.dataset.pointerMode;
                widget.style.removeProperty("--widget-resize-cursor");
                return;
            }

            if (widget.classList.contains("is-widget-resizing")) {
                return;
            }

            widget.dataset.pointerMode = "move";
        });
    }

    function getResizeDirection(widget, clientX, clientY) {
        const rect = widget.getBoundingClientRect();
        if (rect.width <= 0 || rect.height <= 0) {
            return null;
        }

        const nearLeft = clientX - rect.left <= RESIZE_HIT_SLOP;
        const nearRight = rect.right - clientX <= RESIZE_HIT_SLOP;
        const nearTop = clientY - rect.top <= RESIZE_HIT_SLOP;
        const nearBottom = rect.bottom - clientY <= RESIZE_HIT_SLOP;

        if (nearTop && nearLeft) return "nw";
        if (nearTop && nearRight) return "ne";
        if (nearBottom && nearLeft) return "sw";
        if (nearBottom && nearRight) return "se";
        if (nearLeft) return "w";
        if (nearRight) return "e";
        if (nearTop) return "n";
        if (nearBottom) return "s";
        return null;
    }

    function resolveDragPlacement(clientX, clientY) {
        if (!dragState) return null;
        if (!customLayoutEnabled) return null;

        const canvasRect = canvas.getBoundingClientRect();
        const metrics = getGridMetrics();
        const minLeft = canvasRect.left;
        const maxLeft = Math.max(
            minLeft,
            canvasRect.right - dragState.startRect.width,
        );
        const minTop = canvasRect.top;
        const maxTop = Math.max(
            minTop,
            canvasRect.bottom - dragState.startRect.height,
        );

        const desiredLeft = clientX - dragState.pointerOffsetX;
        const desiredTop = clientY - dragState.pointerOffsetY;
        const clampedLeft = clamp(desiredLeft, minLeft, maxLeft);
        const clampedTop = clamp(desiredTop, minTop, maxTop);

        const colStep = metrics.colUnit + metrics.colGap;
        const rowStep = metrics.rowUnit + metrics.rowGap;
        const maxColStart = Math.max(
            1,
            GRID_COLUMNS - dragState.startGeometry.cols + 1,
        );
        const maxRowStart = Math.max(
            1,
            GRID_MAX_ROWS - dragState.startGeometry.rows + 1,
        );
        const nextCol = clamp(
            Math.round((clampedLeft - canvasRect.left) / Math.max(colStep, 1)) +
                1,
            1,
            maxColStart,
        );
        const nextRow = clamp(
            Math.round((clampedTop - canvasRect.top) / Math.max(rowStep, 1)) +
                1,
            1,
            maxRowStart,
        );

        const candidate = {
            ...dragState.startGeometry,
            col: nextCol,
            row: nextRow,
        };
        const previewLayout = cloneWidgetLayout(layoutState.widgets);
        previewLayout[dragState.widgetId] = candidate;
        const geometry = findNearestAvailablePlacement(
            dragState.widgetId,
            candidate,
            previewLayout,
        );
        const snappedLeft =
            canvasRect.left + (geometry.col - 1) * Math.max(colStep, 1);
        const snappedTop =
            canvasRect.top + (geometry.row - 1) * Math.max(rowStep, 1);

        return {
            deltaX: snappedLeft - dragState.startRect.left,
            deltaY: snappedTop - dragState.startRect.top,
            geometry,
        };
    }

    function startDrag(event, widgetId) {
        if (!editMode || resizeState) return;
        if (event.button !== 0) return;
        event.preventDefault();

        const widget = widgetById.get(widgetId);
        if (!widget) return;

        const widgetRect = widget.getBoundingClientRect();
        const startGeometry = geometryFromRect(
            widgetId,
            widgetRect,
            getGridMetrics(),
            canvas.getBoundingClientRect(),
        );
        const pointerOffsetX = clamp(
            event.clientX - widgetRect.left,
            0,
            widgetRect.width,
        );
        const pointerOffsetY = clamp(
            event.clientY - widgetRect.top,
            0,
            widgetRect.height,
        );

        dragState = {
            widgetId,
            pointerId: event.pointerId,
            startGeometry,
            startRect: {
                left: widgetRect.left,
                top: widgetRect.top,
                width: widgetRect.width,
                height: widgetRect.height,
            },
            pointerOffsetX,
            pointerOffsetY,
            anchorPointerX: event.clientX,
            anchorPointerY: event.clientY,
            needsActivation: !customLayoutEnabled,
            engaged: false,
            dirty: false,
            pendingGeometry: startGeometry,
        };

        widget.classList.add("is-widget-dragging");
        widget.style.setProperty("z-index", String(DRAG_ELEVATION));
        widget.dataset.pointerMode = "move";

        try {
            widget.setPointerCapture(event.pointerId);
        } catch {
            // Pointer capture is optional and may fail on some elements/browsers.
        }

        document.addEventListener("pointermove", onDragMove);
        document.addEventListener("pointerup", stopDrag);
        document.addEventListener("pointercancel", stopDrag);
    }

    function onDragMove(event) {
        if (!dragState || event.pointerId !== dragState.pointerId) return;

        const draggedWidget = widgetById.get(dragState.widgetId);
        if (!draggedWidget) return;

        if (!dragState.engaged) {
            const pointerTravel = Math.hypot(
                event.clientX - dragState.anchorPointerX,
                event.clientY - dragState.anchorPointerY,
            );
            if (pointerTravel < DRAG_START_THRESHOLD_PX) {
                return;
            }

            if (dragState.needsActivation) {
                activateCustomLayout(dragState.widgetId);
                const reflowedWidget = widgetById.get(dragState.widgetId);
                if (!reflowedWidget) {
                    return;
                }
                const reflowedRect = reflowedWidget.getBoundingClientRect();
                dragState.startGeometry = geometryFromRect(
                    dragState.widgetId,
                    reflowedRect,
                    getGridMetrics(),
                    canvas.getBoundingClientRect(),
                );
                dragState.startRect = {
                    left: reflowedRect.left,
                    top: reflowedRect.top,
                    width: reflowedRect.width,
                    height: reflowedRect.height,
                };
                dragState.pointerOffsetX = clamp(
                    event.clientX - reflowedRect.left,
                    0,
                    reflowedRect.width,
                );
                dragState.pointerOffsetY = clamp(
                    event.clientY - reflowedRect.top,
                    0,
                    reflowedRect.height,
                );
                dragState.pendingGeometry = dragState.startGeometry;
                dragState.needsActivation = false;
            }

            dragState.engaged = true;
        }

        const placement = resolveDragPlacement(event.clientX, event.clientY);
        if (!placement) return;

        draggedWidget.style.transform = `translate3d(${placement.deltaX}px, ${placement.deltaY}px, 0)`;

        dragState.pendingGeometry = placement.geometry;
        showDragShadow(dragState.widgetId, dragState.pendingGeometry);
    }

    function stopDrag(event) {
        if (!dragState) return;
        if (event && event.pointerId !== dragState.pointerId) return;

        const activeDragState = dragState;
        if (activeDragState.engaged) {
            const finalPlacement = event
                ? resolveDragPlacement(event.clientX, event.clientY)
                : null;
            const finalGeometry =
                finalPlacement?.geometry || activeDragState.pendingGeometry;

            const current = normalizeWidgetGeometry(
                activeDragState.widgetId,
                layoutState.widgets[activeDragState.widgetId] ||
                    activeDragState.startGeometry,
            );
            if (
                finalGeometry &&
                (current.col !== finalGeometry.col ||
                    current.row !== finalGeometry.row ||
                    current.cols !== finalGeometry.cols ||
                    current.rows !== finalGeometry.rows)
            ) {
                applyWidgetPlacement(activeDragState.widgetId, finalGeometry);
                activeDragState.dirty = true;
            }
        }

        const widget = widgetById.get(activeDragState.widgetId);
        if (widget) {
            widget.classList.remove("is-widget-dragging");
            widget.style.removeProperty("transform");
            widget.style.removeProperty("z-index");
            setWidgetPointerMode(widget, editMode ? "move" : null);

            try {
                widget.releasePointerCapture(activeDragState.pointerId);
            } catch {
                // Pointer capture release is best-effort only.
            }
        }

        hideDragShadow();

        const shouldPersist = activeDragState.dirty;
        dragState = null;
        document.removeEventListener("pointermove", onDragMove);
        document.removeEventListener("pointerup", stopDrag);
        document.removeEventListener("pointercancel", stopDrag);
        if (shouldPersist) {
            writeLayoutState();
        }
        applyLayoutMode();
    }

    function startResize(event, widgetId, direction) {
        if (!editMode || dragState) return;
        if (event.button !== 0) return;
        event.preventDefault();

        activateCustomLayout(widgetId);

        const widget = widgetById.get(widgetId);
        if (!widget) return;

        const widgetRect = widget.getBoundingClientRect();
        const metrics = getGridMetrics();
        const startGeometry = geometryFromRect(
            widgetId,
            widgetRect,
            metrics,
            canvas.getBoundingClientRect(),
        );

        resizeState = {
            widgetId,
            pointerId: event.pointerId,
            startX: event.clientX,
            startY: event.clientY,
            startGeometry,
            metrics,
            direction,
            lastGeometry: startGeometry,
            dirty: false,
        };

        widget.classList.add("is-widget-resizing");
        widget.style.setProperty(
            "--widget-resize-cursor",
            resizeCursorForDirection(direction),
        );
        widget.dataset.pointerMode = direction;

        document.addEventListener("pointermove", onResizeMove);
        document.addEventListener("pointerup", stopResize);
        document.addEventListener("pointercancel", stopResize);
    }

    function onResizeMove(event) {
        if (!resizeState || event.pointerId !== resizeState.pointerId) return;

        const deltaX = event.clientX - resizeState.startX;
        const deltaY = event.clientY - resizeState.startY;

        const colStep =
            resizeState.metrics.colUnit + resizeState.metrics.colGap;
        const rowStep =
            resizeState.metrics.rowUnit + resizeState.metrics.rowGap;
        const colDelta = Math.round(deltaX / Math.max(colStep, 1));
        const rowDelta = Math.round(deltaY / Math.max(rowStep, 1));

        const direction = resizeState.direction;
        const start = resizeState.startGeometry;
        const mins = getMinSpan(resizeState.widgetId);

        let nextCol = start.col;
        let nextRow = start.row;
        let nextCols = start.cols;
        let nextRows = start.rows;

        if (direction.includes("e")) {
            const maxColsFromLeft = GRID_COLUMNS - start.col + 1;
            nextCols = clamp(start.cols + colDelta, mins.cols, maxColsFromLeft);
        }

        if (direction.includes("w")) {
            const rightEdge = start.col + start.cols - 1;
            const desiredLeft = start.col + colDelta;
            const desiredCols = rightEdge - desiredLeft + 1;
            nextCols = clamp(desiredCols, mins.cols, rightEdge);
            nextCol = clamp(
                rightEdge - nextCols + 1,
                1,
                GRID_COLUMNS - nextCols + 1,
            );
        }

        if (direction.includes("s")) {
            const maxRowsFromTop = GRID_MAX_ROWS - start.row + 1;
            nextRows = clamp(
                start.rows + rowDelta,
                mins.rows,
                Math.min(RESIZE_MAX_ROWS, maxRowsFromTop),
            );
        }

        if (direction.includes("n")) {
            const bottomEdge = start.row + start.rows - 1;
            const desiredTop = start.row + rowDelta;
            const desiredRows = bottomEdge - desiredTop + 1;
            nextRows = clamp(
                desiredRows,
                mins.rows,
                Math.min(RESIZE_MAX_ROWS, bottomEdge),
            );
            nextRow = clamp(
                bottomEdge - nextRows + 1,
                1,
                GRID_MAX_ROWS - nextRows + 1,
            );
        }

        const nextGeometry = normalizeWidgetGeometry(resizeState.widgetId, {
            col: nextCol,
            row: nextRow,
            cols: nextCols,
            rows: nextRows,
        });

        if (
            nextGeometry.col === resizeState.lastGeometry.col &&
            nextGeometry.row === resizeState.lastGeometry.row &&
            nextGeometry.cols === resizeState.lastGeometry.cols &&
            nextGeometry.rows === resizeState.lastGeometry.rows
        ) {
            return;
        }

        resizeState.lastGeometry = nextGeometry;
        applyWidgetPlacement(resizeState.widgetId, nextGeometry);
        resizeState.dirty = true;
    }

    function stopResize(event) {
        if (!resizeState) return;
        if (event && event.pointerId !== resizeState.pointerId) return;

        const widget = widgetById.get(resizeState.widgetId);
        if (widget) {
            widget.classList.remove("is-widget-resizing");
            widget.style.removeProperty("--widget-resize-cursor");
            setWidgetPointerMode(widget, editMode ? "move" : null);
        }

        const shouldPersist = resizeState.dirty;
        resizeState = null;
        document.removeEventListener("pointermove", onResizeMove);
        document.removeEventListener("pointerup", stopResize);
        document.removeEventListener("pointercancel", stopResize);
        if (shouldPersist) {
            writeLayoutState();
        }
        applyLayoutMode();
    }

    function bindWidgetInteractions() {
        widgetById.forEach((widget, widgetId) => {
            if (widget.dataset.widgetEditorBound === "true") {
                return;
            }
            widget.dataset.widgetEditorBound = "true";

            widget.addEventListener("pointermove", (event) => {
                if (!editMode || dragState || resizeState) return;
                const resizeDirection = getResizeDirection(
                    widget,
                    event.clientX,
                    event.clientY,
                );
                widget.dataset.pointerMode = resizeDirection || "move";
            });

            widget.addEventListener("pointerleave", () => {
                if (!editMode || dragState || resizeState) return;
                widget.dataset.pointerMode = "move";
            });

            widget.addEventListener("pointerdown", (event) => {
                if (!editMode || event.button !== 0) return;

                const resizeDirection = getResizeDirection(
                    widget,
                    event.clientX,
                    event.clientY,
                );
                if (resizeDirection) {
                    startResize(event, widgetId, resizeDirection);
                    return;
                }

                startDrag(event, widgetId);
            });
        });
    }

    function setEditMode(nextMode) {
        editMode = nextMode;

        if (!editMode) {
            stopDrag();
            stopResize();
            hideDragShadow();
            syncWidgetPointerModes();
        } else {
            syncWidgetPointerModes();
        }

        applyLayoutMode();
        refreshEditButton();
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

    const storedLayout = readLayoutState();
    if (storedLayout) {
        layoutState = storedLayout;
        customLayoutEnabled = true;
    }

    if (editToggle) {
        editToggle.addEventListener("click", () => {
            if (reactEditorUrl) {
                window.location.assign(reactEditorUrl);
                return;
            }
            setEditMode(!editMode);
        });
    }

    if (resetLayoutButton) {
        resetLayoutButton.addEventListener("click", () => {
            setEditMode(false);
            resetLayoutState();
            applyWidgetLayout();
            applyLayoutMode();
        });
    }

    bindWidgetInteractions();
    applyWidgetLayout();
    applyDensity(initialDensity);
    applyLayoutMode();
    syncWidgetPointerModes();
    refreshEditButton();
}
