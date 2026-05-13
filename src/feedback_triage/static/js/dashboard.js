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
    const RESIZE_MIN_ROWS = 3;
    const RESIZE_MAX_ROWS = 40;
    const RESIZE_HIT_SLOP = 12;
    const DRAG_ELEVATION = 20;

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

    const widgetById = new Map();
    widgets.forEach((widget) => {
        const widgetId = widget.dataset.widgetId;
        if (!widgetId) return;
        widgetById.set(widgetId, widget);
    });

    const defaultOrder = Array.from(widgetById.keys());
    const defaultSpans = defaultOrder.reduce((accumulator, widgetId) => {
        accumulator[widgetId] = {
            cols: DEFAULT_SPANS[widgetId]?.cols || 3,
            rows: DEFAULT_SPANS[widgetId]?.rows || 8,
        };
        return accumulator;
    }, {});
    let layoutState = {
        order: [...defaultOrder],
        spans: JSON.parse(JSON.stringify(defaultSpans)),
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
                order: [...defaultOrder],
                spans: JSON.parse(JSON.stringify(defaultSpans)),
            };
        }

        const providedOrder = Array.isArray(candidate.order)
            ? candidate.order.filter((id) => widgetById.has(id))
            : [];
        const finalOrder = [
            ...providedOrder,
            ...defaultOrder.filter((id) => !providedOrder.includes(id)),
        ];

        const candidateSpans =
            candidate.spans && typeof candidate.spans === "object"
                ? candidate.spans
                : {};

        const finalSpans = {};
        defaultOrder.forEach((widgetId) => {
            const defaults = DEFAULT_SPANS[widgetId] || { cols: 3, rows: 8 };
            const stored = candidateSpans[widgetId];
            const cols = clamp(
                Number(stored?.cols) || defaults.cols,
                1,
                GRID_COLUMNS,
            );
            const rows = clamp(
                Number(stored?.rows) || defaults.rows,
                RESIZE_MIN_ROWS,
                RESIZE_MAX_ROWS,
            );
            finalSpans[widgetId] = {
                cols,
                rows,
            };
        });

        return {
            order: finalOrder,
            spans: finalSpans,
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
        layoutState.order.forEach((widgetId, index) => {
            const widget = widgetById.get(widgetId);
            if (!widget) return;
            const span = layoutState.spans[widgetId] || { cols: 3, rows: 8 };
            const cols = clamp(span.cols, 1, GRID_COLUMNS);
            const rows = clamp(span.rows, RESIZE_MIN_ROWS, RESIZE_MAX_ROWS);
            widget.style.setProperty("--widget-order", String(index + 1));
            widget.style.setProperty("--widget-col-span", String(cols));
            widget.style.setProperty("--widget-row-span", String(rows));
        });
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

    function reorderWidget(widgetId, targetWidgetId, placeAfter) {
        const currentOrder = [...layoutState.order];
        const sourceIndex = currentOrder.indexOf(widgetId);
        const targetIndex = currentOrder.indexOf(targetWidgetId);

        if (sourceIndex < 0 || targetIndex < 0 || sourceIndex === targetIndex) {
            return;
        }

        currentOrder.splice(sourceIndex, 1);
        const adjustedTarget =
            sourceIndex < targetIndex ? targetIndex - 1 : targetIndex;
        const insertionIndex = placeAfter ? adjustedTarget + 1 : adjustedTarget;
        currentOrder.splice(insertionIndex, 0, widgetId);
        layoutState.order = currentOrder;
        applyWidgetLayout();
    }

    function getClosestDropTarget(widgetId, clientX, clientY) {
        let closest = null;

        layoutState.order.forEach((candidateId) => {
            if (candidateId === widgetId) return;

            const candidate = widgetById.get(candidateId);
            if (!candidate || candidate.hidden) return;

            const rect = candidate.getBoundingClientRect();
            if (rect.width <= 0 || rect.height <= 0) return;

            const centerX = rect.left + rect.width / 2;
            const centerY = rect.top + rect.height / 2;
            const distance = Math.hypot(clientX - centerX, clientY - centerY);

            if (!closest || distance < closest.distance) {
                closest = {
                    widgetId: candidateId,
                    rect,
                    centerX,
                    centerY,
                    distance,
                };
            }
        });

        return closest;
    }

    function startDrag(event, widgetId) {
        if (!editMode || resizeState) return;
        if (event.button !== 0) return;
        event.preventDefault();

        const widget = widgetById.get(widgetId);
        if (!widget) return;

        dragState = {
            widgetId,
            pointerId: event.pointerId,
            startX: event.clientX,
            startY: event.clientY,
            lastTargetId: null,
            lastPlaceAfter: null,
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
        if (draggedWidget) {
            const deltaX = event.clientX - dragState.startX;
            const deltaY = event.clientY - dragState.startY;
            draggedWidget.style.transform = `translate3d(${deltaX}px, ${deltaY}px, 0)`;
        }

        const target = getClosestDropTarget(
            dragState.widgetId,
            event.clientX,
            event.clientY,
        );
        if (!target) return;

        const normalizedX =
            (event.clientX - target.centerX) / Math.max(target.rect.width, 1);
        const normalizedY =
            (event.clientY - target.centerY) / Math.max(target.rect.height, 1);
        const placeAfter =
            Math.abs(normalizedX) > Math.abs(normalizedY)
                ? normalizedX >= 0
                : normalizedY >= 0;

        if (
            target.widgetId !== dragState.lastTargetId ||
            placeAfter !== dragState.lastPlaceAfter
        ) {
            reorderWidget(dragState.widgetId, target.widgetId, placeAfter);
            dragState.lastTargetId = target.widgetId;
            dragState.lastPlaceAfter = placeAfter;
        }
    }

    function stopDrag(event) {
        if (!dragState) return;
        if (event && event.pointerId !== dragState.pointerId) return;

        const widget = widgetById.get(dragState.widgetId);
        if (widget) {
            widget.classList.remove("is-widget-dragging");
            widget.style.removeProperty("transform");
            widget.style.removeProperty("z-index");
            setWidgetPointerMode(widget, editMode ? "move" : null);
        }

        dragState = null;
        document.removeEventListener("pointermove", onDragMove);
        document.removeEventListener("pointerup", stopDrag);
        document.removeEventListener("pointercancel", stopDrag);
        writeLayoutState();
        applyLayoutMode();
    }

    function startResize(event, widgetId, direction) {
        if (!editMode || dragState) return;
        if (event.button !== 0) return;
        event.preventDefault();

        const widget = widgetById.get(widgetId);
        if (!widget) return;

        const span = layoutState.spans[widgetId] || { cols: 3, rows: 8 };
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

        resizeState = {
            widgetId,
            pointerId: event.pointerId,
            startX: event.clientX,
            startY: event.clientY,
            startCols: span.cols,
            startRows: span.rows,
            colUnit,
            rowUnit,
            colGap: columnGap,
            rowGap,
            direction,
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

        const colStep = resizeState.colUnit + resizeState.colGap;
        const rowStep = resizeState.rowUnit + resizeState.rowGap;
        const colDelta = Math.round(deltaX / Math.max(colStep, 1));
        const rowDelta = Math.round(deltaY / Math.max(rowStep, 1));

        const direction = resizeState.direction;
        const horizontalFactor = direction.includes("w")
            ? -1
            : direction.includes("e")
              ? 1
              : 0;
        const verticalFactor = direction.includes("n")
            ? -1
            : direction.includes("s")
              ? 1
              : 0;

        const nextCols =
            horizontalFactor === 0
                ? resizeState.startCols
                : clamp(
                      resizeState.startCols + horizontalFactor * colDelta,
                      1,
                      GRID_COLUMNS,
                  );
        const nextRows =
            verticalFactor === 0
                ? resizeState.startRows
                : clamp(
                      resizeState.startRows + verticalFactor * rowDelta,
                      RESIZE_MIN_ROWS,
                      RESIZE_MAX_ROWS,
                  );

        layoutState.spans[resizeState.widgetId] = {
            cols: nextCols,
            rows: nextRows,
        };
        applyWidgetLayout();
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

        resizeState = null;
        document.removeEventListener("pointermove", onResizeMove);
        document.removeEventListener("pointerup", stopResize);
        document.removeEventListener("pointercancel", stopResize);
        writeLayoutState();
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
