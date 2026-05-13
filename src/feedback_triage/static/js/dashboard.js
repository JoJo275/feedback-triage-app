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
    const widgets = Array.from(canvas.querySelectorAll("[data-widget-id]"));

    const workspaceSlug = layout.dataset.workspaceSlug || "default";
    const STORAGE_PREFIX = `sn.dashboard.${workspaceSlug}`;
    const DENSITY_KEY = `${STORAGE_PREFIX}.density`;
    const WIDGETS_KEY = `${STORAGE_PREFIX}.widgets`;
    const LAYOUT_KEY = `${STORAGE_PREFIX}.layout`;

    const GRID_COLUMNS = 12;
    const GRID_MAX_ROWS = 120;
    const RESIZE_MIN_ROWS = 3;
    const RESIZE_MAX_ROWS = 40;
    const RESIZE_HIT_SLOP = 12;
    const DRAG_ELEVATION = 20;
    const DRAG_START_THRESHOLD_PX = 10;
    const DRAG_APPLY_DELAY_MS = 85;

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
        "kpi-total-signals": { cols: 2, rows: 4 },
        "kpi-needs-action": { cols: 2, rows: 4 },
        "kpi-high-pain-signals": { cols: 2, rows: 4 },
        "kpi-median-triage-time": { cols: 2, rows: 4 },
        "kpi-net-backlog-change": { cols: 2, rows: 4 },
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

        if (lockedWidgetId && widgetById.has(lockedWidgetId)) {
            const lockedGeometry = normalizeWidgetGeometry(
                lockedWidgetId,
                candidateWidgets?.[lockedWidgetId] ||
                    DEFAULT_WIDGET_LAYOUT[lockedWidgetId],
            );
            resolved[lockedWidgetId] = lockedGeometry;
            occupied.push(lockedGeometry);
        }

        defaultOrder.forEach((widgetId) => {
            if (widgetId === lockedWidgetId) {
                return;
            }

            const preferred = normalizeWidgetGeometry(
                widgetId,
                candidateWidgets?.[widgetId] || DEFAULT_WIDGET_LAYOUT[widgetId],
            );
            const placed = findFreePlacement(occupied, preferred);
            resolved[widgetId] = placed;
            occupied.push(placed);
        });

        return resolved;
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

    function getGridMetrics() {
        const canvasRect = canvas.getBoundingClientRect();
        const styles = window.getComputedStyle(canvas);
        const columnGap = Number.parseFloat(styles.columnGap) || 0;
        const rowGap = Number.parseFloat(styles.rowGap) || 0;
        const availableWidth =
            canvasRect.width - (GRID_COLUMNS - 1) * columnGap;
        const colUnit = availableWidth / GRID_COLUMNS;
        const rowUnit =
            Number.parseFloat(
                styles.getPropertyValue("--sn-widget-row-unit"),
            ) || 18;

        return {
            colUnit,
            rowUnit,
            colGap: columnGap,
            rowGap,
        };
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
                widgets: resolveWidgetLayout(candidate.widgets),
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
                widgets: resolveWidgetLayout(legacyWidgets),
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
            resetLayoutButton.hidden = !customLayoutEnabled;
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
        currentLayout[widgetId] = normalizeWidgetGeometry(
            widgetId,
            nextGeometry,
        );
        layoutState.widgets = resolveWidgetLayout(currentLayout, widgetId);
        applyWidgetLayout();
    }

    function refreshEditButton() {
        if (!editToggle) return;
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

    function startDrag(event, widgetId) {
        if (!editMode || resizeState) return;
        if (event.button !== 0) return;
        event.preventDefault();

        const widget = widgetById.get(widgetId);
        if (!widget) return;

        const startGeometry = normalizeWidgetGeometry(
            widgetId,
            layoutState.widgets[widgetId] || DEFAULT_WIDGET_LAYOUT[widgetId],
        );

        dragState = {
            widgetId,
            pointerId: event.pointerId,
            startX: event.clientX,
            startY: event.clientY,
            startGeometry,
            metrics: getGridMetrics(),
            engaged: false,
            dirty: false,
            pendingCol: startGeometry.col,
            pendingRow: startGeometry.row,
            lastAppliedAt: 0,
        };

        widget.classList.add("is-widget-dragging");
        widget.style.setProperty("z-index", String(DRAG_ELEVATION));
        widget.dataset.pointerMode = "move";

        document.addEventListener("pointermove", onDragMove);
        document.addEventListener("pointerup", stopDrag);
        document.addEventListener("pointercancel", stopDrag);
    }

    function onDragMove(event) {
        if (!dragState || event.pointerId !== dragState.pointerId) return;

        const draggedWidget = widgetById.get(dragState.widgetId);
        if (!draggedWidget) return;

        const deltaX = event.clientX - dragState.startX;
        const deltaY = event.clientY - dragState.startY;
        draggedWidget.style.transform = `translate3d(${deltaX}px, ${deltaY}px, 0)`;

        if (
            !dragState.engaged &&
            Math.hypot(deltaX, deltaY) < DRAG_START_THRESHOLD_PX
        ) {
            return;
        }
        dragState.engaged = true;

        const colStep = dragState.metrics.colUnit + dragState.metrics.colGap;
        const rowStep = dragState.metrics.rowUnit + dragState.metrics.rowGap;
        const colDelta = Math.round(deltaX / Math.max(colStep, 1));
        const rowDelta = Math.round(deltaY / Math.max(rowStep, 1));

        const maxColStart = Math.max(
            1,
            GRID_COLUMNS - dragState.startGeometry.cols + 1,
        );
        const maxRowStart = Math.max(
            1,
            GRID_MAX_ROWS - dragState.startGeometry.rows + 1,
        );
        const nextCol = clamp(
            dragState.startGeometry.col + colDelta,
            1,
            maxColStart,
        );
        const nextRow = clamp(
            dragState.startGeometry.row + rowDelta,
            1,
            maxRowStart,
        );

        dragState.pendingCol = nextCol;
        dragState.pendingRow = nextRow;

        const now = performance.now();
        if (now - dragState.lastAppliedAt < DRAG_APPLY_DELAY_MS) {
            return;
        }

        dragState.lastAppliedAt = now;
        applyWidgetPlacement(dragState.widgetId, {
            ...dragState.startGeometry,
            col: nextCol,
            row: nextRow,
        });
        dragState.dirty = true;
    }

    function stopDrag(event) {
        if (!dragState) return;
        if (event && event.pointerId !== dragState.pointerId) return;

        if (dragState.engaged) {
            const current = normalizeWidgetGeometry(
                dragState.widgetId,
                layoutState.widgets[dragState.widgetId] ||
                    dragState.startGeometry,
            );
            if (
                current.col !== dragState.pendingCol ||
                current.row !== dragState.pendingRow
            ) {
                applyWidgetPlacement(dragState.widgetId, {
                    ...current,
                    col: dragState.pendingCol,
                    row: dragState.pendingRow,
                });
                dragState.dirty = true;
            }
        }

        const widget = widgetById.get(dragState.widgetId);
        if (widget) {
            widget.classList.remove("is-widget-dragging");
            widget.style.removeProperty("transform");
            widget.style.removeProperty("z-index");
            setWidgetPointerMode(widget, editMode ? "move" : null);
        }

        const shouldPersist = dragState.dirty;
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

        const widget = widgetById.get(widgetId);
        if (!widget) return;

        const startGeometry = normalizeWidgetGeometry(
            widgetId,
            layoutState.widgets[widgetId] || DEFAULT_WIDGET_LAYOUT[widgetId],
        );
        const metrics = getGridMetrics();

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
            syncWidgetPointerModes();
        } else {
            customLayoutEnabled = true;
            writeLayoutState();
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
