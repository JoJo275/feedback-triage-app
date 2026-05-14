const mount = document.getElementById("sn-react-widget-root");

if (!mount) {
    // Not on the React widgets pilot page.
} else {
    const workspaceSlug = mount.dataset.workspaceSlug || "default";
    const dashboardUrl =
        mount.dataset.dashboardUrl || `/w/${workspaceSlug}/dashboard`;

    const STORAGE_KEY = `sn.react.dashboard-layout.${workspaceSlug}.v1`;
    const LEGACY_LAYOUT_KEY = `sn.dashboard.${workspaceSlug}.layout`;
    const BREAKPOINTS = {
        lg: 1200,
        md: 996,
        sm: 768,
        xs: 480,
        xxs: 0,
    };
    const BREAKPOINT_ORDER = ["lg", "md", "sm", "xs", "xxs"];
    const COLS = {
        lg: 12,
        md: 12,
        sm: 6,
        xs: 4,
        xxs: 2,
    };

    const WIDGETS = [
        {
            id: "kpi-total-signals",
            title: "Total signals",
            body: "Workspace-wide intake volume.",
        },
        {
            id: "kpi-needs-action",
            title: "Needs action",
            body: "New and in-flight triage workload.",
        },
        {
            id: "kpi-high-pain-signals",
            title: "High pain signals",
            body: "Most painful feedback concentration.",
        },
        {
            id: "kpi-median-triage-time",
            title: "Median triage time",
            body: "Created to triage update median.",
        },
        {
            id: "kpi-net-backlog-change",
            title: "Net backlog change",
            body: "Received minus resolved over the current window.",
        },
        {
            id: "signals-over-time",
            title: "Signals over time",
            body: "Received, triaged, and resolved trend view.",
        },
        {
            id: "status-mix",
            title: "Status mix",
            body: "Workflow distribution and bottleneck visibility.",
        },
        {
            id: "aging-health",
            title: "Aging / SLA",
            body: "Open-item age and SLA pressure.",
        },
        {
            id: "top-tags",
            title: "Top tags",
            body: "Most frequent themes and unresolved counts.",
        },
        {
            id: "pain-distribution",
            title: "Pain distribution",
            body: "Low, medium, and high pain distribution.",
        },
        {
            id: "segment-impact",
            title: "Segment impact",
            body: "Where high-pain impact is concentrated.",
        },
        {
            id: "source-breakdown",
            title: "Source breakdown",
            body: "Channel contribution by intake source.",
        },
        {
            id: "team-workload",
            title: "Team workload",
            body: "Owner-level open, high pain, and overdue work.",
        },
        {
            id: "backlog-needs-attention",
            title: "Backlog / needs attention",
            body: "Urgent categories needing immediate review.",
        },
        {
            id: "action-queue",
            title: "Action queue",
            body: "Urgency-first list for next triage actions.",
        },
    ];

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

    function scaleCols(cols, breakpointCols) {
        return clamp(
            Math.round((cols / 12) * breakpointCols),
            1,
            breakpointCols,
        );
    }

    function buildDefaultLayoutForBreakpoint(breakpoint) {
        const breakpointCols = COLS[breakpoint] || 12;
        let cursorX = 0;
        let cursorY = 0;
        let rowHeight = 0;

        return WIDGETS.map((widget) => {
            const baseSpan = DEFAULT_SPANS[widget.id] || { cols: 3, rows: 8 };
            const minSpan = MIN_SPANS[widget.id] || { cols: 1, rows: 2 };

            const minW = scaleCols(minSpan.cols, breakpointCols);
            const w = clamp(
                scaleCols(baseSpan.cols, breakpointCols),
                minW,
                breakpointCols,
            );
            const minH = clamp(minSpan.rows, 1, 30);
            const h = clamp(baseSpan.rows, minH, 30);

            if (cursorX + w > breakpointCols) {
                cursorX = 0;
                cursorY += rowHeight;
                rowHeight = 0;
            }

            const item = {
                i: widget.id,
                x: cursorX,
                y: cursorY,
                w,
                h,
                minW,
                minH,
            };

            cursorX += w;
            rowHeight = Math.max(rowHeight, h);
            return item;
        });
    }

    function buildDefaultLayouts() {
        const layouts = {};
        BREAKPOINT_ORDER.forEach((breakpoint) => {
            layouts[breakpoint] = buildDefaultLayoutForBreakpoint(breakpoint);
        });
        return layouts;
    }

    const DEFAULT_LAYOUTS = buildDefaultLayouts();

    const REACT_URL = "https://esm.sh/react@18.2.0";
    const REACT_DOM_CLIENT_URL =
        "https://esm.sh/react-dom@18.2.0/client?external=react@18.2.0";
    const REACT_GRID_LAYOUT_URL =
        "https://esm.sh/react-grid-layout@1.4.4?external=react@18.2.0,react-dom@18.2.0";

    function clamp(value, min, max) {
        return Math.min(Math.max(value, min), max);
    }

    function asInt(value, fallback) {
        const numeric = Number(value);
        if (!Number.isFinite(numeric)) {
            return fallback;
        }
        return Math.trunc(numeric);
    }

    function safeLocalStorageGet(key) {
        try {
            return window.localStorage.getItem(key);
        } catch {
            return null;
        }
    }

    function safeLocalStorageSet(key, value) {
        try {
            window.localStorage.setItem(key, value);
        } catch {
            // Ignore private mode and quota failures.
        }
    }

    function cloneLayouts(layouts) {
        return JSON.parse(JSON.stringify(layouts));
    }

    function defaultLayoutFor(breakpoint, widgetId) {
        const rows = DEFAULT_LAYOUTS[breakpoint] || [];
        const found = rows.find((row) => row.i === widgetId);
        if (found) {
            return found;
        }
        return { i: widgetId, x: 0, y: 0, w: 2, h: 4, minW: 1, minH: 1 };
    }

    function normalizeLayoutItem(breakpoint, item, fallback) {
        const maxCols = COLS[breakpoint] || 12;
        const width = clamp(asInt(item.w, fallback.w), 1, maxCols);
        const height = clamp(asInt(item.h, fallback.h), 1, 30);
        const maxX = Math.max(0, maxCols - width);

        return {
            i: String(item.i || fallback.i),
            x: clamp(asInt(item.x, fallback.x), 0, maxX),
            y: Math.max(0, asInt(item.y, fallback.y)),
            w: width,
            h: height,
            minW: clamp(asInt(item.minW, fallback.minW || 1), 1, maxCols),
            minH: clamp(asInt(item.minH, fallback.minH || 1), 1, 30),
        };
    }

    function fromPersistedLayouts(rawLayouts) {
        const normalized = {};

        BREAKPOINT_ORDER.forEach((breakpoint) => {
            const rows = Array.isArray(rawLayouts?.[breakpoint])
                ? rawLayouts[breakpoint]
                : [];
            const persistedById = new Map();

            rows.forEach((row) => {
                if (!row || typeof row.id !== "string") {
                    return;
                }
                persistedById.set(row.id, row);
            });

            normalized[breakpoint] = WIDGETS.map((widget) => {
                const fallback = defaultLayoutFor(breakpoint, widget.id);
                const persisted = persistedById.get(widget.id);
                if (!persisted) {
                    return normalizeLayoutItem(breakpoint, fallback, fallback);
                }
                return normalizeLayoutItem(
                    breakpoint,
                    {
                        i: widget.id,
                        x: persisted.x,
                        y: persisted.y,
                        w: persisted.w,
                        h: persisted.h,
                        minW: fallback.minW,
                        minH: fallback.minH,
                    },
                    fallback,
                );
            });
        });

        return normalized;
    }

    function toPersistedLayouts(layouts) {
        const persisted = {};
        BREAKPOINT_ORDER.forEach((breakpoint) => {
            const rows = Array.isArray(layouts?.[breakpoint])
                ? layouts[breakpoint]
                : [];
            persisted[breakpoint] = rows.map((row) => ({
                id: String(row.i),
                x: asInt(row.x, 0),
                y: asInt(row.y, 0),
                w: asInt(row.w, 1),
                h: asInt(row.h, 1),
            }));
        });
        return persisted;
    }

    function normalizeLayouts(layouts) {
        return fromPersistedLayouts(toPersistedLayouts(layouts));
    }

    function firstAvailableBreakpoint(layouts, preferredBreakpoint = "lg") {
        if (
            Array.isArray(layouts?.[preferredBreakpoint]) &&
            layouts[preferredBreakpoint].length > 0
        ) {
            return preferredBreakpoint;
        }

        const fallback = BREAKPOINT_ORDER.find(
            (breakpoint) =>
                Array.isArray(layouts?.[breakpoint]) &&
                layouts[breakpoint].length > 0,
        );

        return fallback || "lg";
    }

    function toLegacyLayoutState(layouts, preferredBreakpoint = "lg") {
        const sourceBreakpoint = firstAvailableBreakpoint(
            layouts,
            preferredBreakpoint,
        );
        const sourceRows = Array.isArray(layouts?.[sourceBreakpoint])
            ? layouts[sourceBreakpoint]
            : [];
        const byId = new Map(sourceRows.map((row) => [String(row.i), row]));
        const widgets = {};

        WIDGETS.forEach((widget) => {
            const fallback = defaultLayoutFor("lg", widget.id);
            const source = byId.get(widget.id) || fallback;
            const normalized = normalizeLayoutItem(
                "lg",
                {
                    i: widget.id,
                    x: source.x,
                    y: source.y,
                    w: source.w,
                    h: source.h,
                    minW: fallback.minW,
                    minH: fallback.minH,
                },
                fallback,
            );

            widgets[widget.id] = {
                col: normalized.x + 1,
                row: normalized.y + 1,
                cols: normalized.w,
                rows: normalized.h,
            };
        });

        return { widgets };
    }

    function fromLegacyLayoutState(layoutState) {
        if (!layoutState || typeof layoutState !== "object") {
            return null;
        }

        if (!layoutState.widgets || typeof layoutState.widgets !== "object") {
            return null;
        }

        const lgRows = WIDGETS.map((widget) => {
            const fallback = defaultLayoutFor("lg", widget.id);
            const source = layoutState.widgets?.[widget.id];

            if (!source || typeof source !== "object") {
                return normalizeLayoutItem("lg", fallback, fallback);
            }

            return normalizeLayoutItem(
                "lg",
                {
                    i: widget.id,
                    x: asInt(source.col, fallback.x + 1) - 1,
                    y: asInt(source.row, fallback.y + 1) - 1,
                    w: source.cols,
                    h: source.rows,
                    minW: fallback.minW,
                    minH: fallback.minH,
                },
                fallback,
            );
        });

        return fromPersistedLayouts({
            lg: lgRows.map((row) => ({
                id: row.i,
                x: row.x,
                y: row.y,
                w: row.w,
                h: row.h,
            })),
        });
    }

    function loadLayouts() {
        const raw = safeLocalStorageGet(STORAGE_KEY);
        if (raw) {
            try {
                const parsed = JSON.parse(raw);
                if (
                    parsed &&
                    typeof parsed === "object" &&
                    parsed.version === 1
                ) {
                    return fromPersistedLayouts(parsed.layouts);
                }
            } catch {
                // Ignore malformed payload and continue to legacy fallback.
            }
        }

        const legacyRaw = safeLocalStorageGet(LEGACY_LAYOUT_KEY);
        if (legacyRaw) {
            try {
                const legacyParsed = JSON.parse(legacyRaw);
                const fromLegacy = fromLegacyLayoutState(legacyParsed);
                if (fromLegacy) {
                    return fromLegacy;
                }
            } catch {
                // Ignore malformed legacy payload.
            }
        }

        return cloneLayouts(DEFAULT_LAYOUTS);
    }

    function saveLayouts(layouts, preferredBreakpoint = "lg") {
        const payload = {
            version: 1,
            layouts: toPersistedLayouts(layouts),
            savedAt: new Date().toISOString(),
        };
        safeLocalStorageSet(STORAGE_KEY, JSON.stringify(payload));

        const legacyLayoutState = toLegacyLayoutState(
            layouts,
            preferredBreakpoint,
        );
        safeLocalStorageSet(
            LEGACY_LAYOUT_KEY,
            JSON.stringify(legacyLayoutState),
        );
    }

    function formatTime(date) {
        return date.toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
        });
    }

    function renderError(message) {
        const wrapper = document.createElement("p");
        wrapper.className = "sn-text-muted";
        wrapper.textContent = message;
        mount.replaceChildren(wrapper);
    }

    async function bootstrap() {
        let ReactModule;
        let ReactDomClientModule;
        let ReactGridLayoutModule;

        try {
            [ReactModule, ReactDomClientModule, ReactGridLayoutModule] =
                await Promise.all([
                    import(REACT_URL),
                    import(REACT_DOM_CLIENT_URL),
                    import(REACT_GRID_LAYOUT_URL),
                ]);
        } catch (error) {
            renderError(
                "Unable to load React dependencies for this pilot surface.",
            );
            console.error(error);
            return;
        }

        const React = ReactModule.default || ReactModule;
        const createRoot = ReactDomClientModule.createRoot;
        const Responsive =
            ReactGridLayoutModule.Responsive ||
            ReactGridLayoutModule.default?.Responsive;
        const WidthProvider =
            ReactGridLayoutModule.WidthProvider ||
            ReactGridLayoutModule.default?.WidthProvider;

        if (!createRoot || !Responsive || !WidthProvider) {
            renderError(
                "React widgets pilot failed to initialize: invalid grid exports.",
            );
            return;
        }

        const { useEffect, useMemo, useRef, useState } = React;
        const h = React.createElement;
        const ResponsiveGridLayout = WidthProvider(Responsive);

        function WidgetsApp() {
            const [editMode, setEditMode] = useState(false);
            const [layouts, setLayouts] = useState(() => loadLayouts());
            const [breakpoint, setBreakpoint] = useState("lg");
            const [saveStatus, setSaveStatus] = useState("Loaded from storage");
            const saveTimerRef = useRef(null);

            const currentLayoutPreview = useMemo(() => {
                const persisted = toPersistedLayouts(layouts);
                return JSON.stringify(persisted[breakpoint] || [], null, 2);
            }, [layouts, breakpoint]);

            function persistNow(
                nextLayouts,
                messagePrefix,
                targetBreakpoint = breakpoint,
            ) {
                saveLayouts(nextLayouts, targetBreakpoint);
                setSaveStatus(`${messagePrefix} ${formatTime(new Date())}`);
            }

            function queuePersist(nextLayouts, targetBreakpoint = breakpoint) {
                if (saveTimerRef.current !== null) {
                    window.clearTimeout(saveTimerRef.current);
                }

                setSaveStatus("Saving...");
                saveTimerRef.current = window.setTimeout(() => {
                    persistNow(nextLayouts, "Saved at", targetBreakpoint);
                    saveTimerRef.current = null;
                }, 320);
            }

            function handleLayoutChange(_currentLayout, allLayouts) {
                const normalized = normalizeLayouts(allLayouts);
                setLayouts(normalized);
                queuePersist(normalized, breakpoint);
            }

            function handleReset() {
                const defaults = cloneLayouts(DEFAULT_LAYOUTS);
                setLayouts(defaults);
                persistNow(defaults, "Reset and saved at", "lg");
            }

            useEffect(
                () => () => {
                    if (saveTimerRef.current !== null) {
                        window.clearTimeout(saveTimerRef.current);
                    }
                },
                [],
            );

            const widgetCards = WIDGETS.map((widget) =>
                h(
                    "article",
                    {
                        key: widget.id,
                        className: "sn-react-widget-card",
                    },
                    [
                        h(
                            "header",
                            {
                                className: "sn-react-widget-card__header",
                                key: "header",
                            },
                            [
                                h(
                                    "button",
                                    {
                                        type: "button",
                                        className:
                                            "sn-react-widget__drag-handle",
                                        "aria-label": `Drag ${widget.title}`,
                                        title: "Drag widget",
                                        key: "drag",
                                    },
                                    "::",
                                ),
                                h(
                                    "h3",
                                    {
                                        className:
                                            "sn-react-widget-card__title",
                                        key: "title",
                                    },
                                    widget.title,
                                ),
                            ],
                        ),
                        h(
                            "p",
                            {
                                className: "sn-react-widget-card__body",
                                key: "body",
                            },
                            widget.body,
                        ),
                    ],
                ),
            );

            return h(
                "div",
                {
                    className: "sn-react-widget-surface",
                    "data-edit-mode": String(editMode),
                },
                [
                    h(
                        "div",
                        {
                            className: "sn-react-widget-toolbar",
                            key: "toolbar",
                        },
                        [
                            h(
                                "button",
                                {
                                    type: "button",
                                    className: "sn-button sn-button-primary",
                                    onClick: () =>
                                        setEditMode((value) => !value),
                                    key: "toggle",
                                },
                                editMode ? "Exit edit mode" : "Edit widgets",
                            ),
                            h(
                                "button",
                                {
                                    type: "button",
                                    className: "sn-button sn-button-secondary",
                                    onClick: handleReset,
                                    key: "reset",
                                },
                                "Reset layout",
                            ),
                            h(
                                "button",
                                {
                                    type: "button",
                                    className: "sn-button sn-button-secondary",
                                    onClick: () =>
                                        persistNow(layouts, "Saved at"),
                                    key: "save",
                                },
                                "Save now",
                            ),
                            h(
                                "button",
                                {
                                    type: "button",
                                    className: "sn-button sn-button-primary",
                                    onClick: () => {
                                        persistNow(layouts, "Saved at");
                                        window.location.assign(dashboardUrl);
                                    },
                                    key: "save-return",
                                },
                                "Save and return",
                            ),
                            h(
                                "a",
                                {
                                    href: dashboardUrl,
                                    className: "sn-button sn-button-secondary",
                                    key: "back",
                                },
                                "Classic dashboard",
                            ),
                            h(
                                "span",
                                {
                                    className:
                                        "sn-react-widget-toolbar__status",
                                    key: "status",
                                    role: "status",
                                },
                                `${saveStatus} · ${breakpoint.toUpperCase()} breakpoint`,
                            ),
                        ],
                    ),
                    h(
                        ResponsiveGridLayout,
                        {
                            key: "grid",
                            className: "sn-react-grid",
                            layouts,
                            breakpoints: BREAKPOINTS,
                            cols: COLS,
                            rowHeight: 28,
                            margin: [12, 12],
                            containerPadding: [0, 0],
                            isDraggable: editMode,
                            isResizable: editMode,
                            allowOverlap: false,
                            preventCollision: true,
                            compactType: "vertical",
                            draggableHandle: ".sn-react-widget__drag-handle",
                            onLayoutChange: handleLayoutChange,
                            onBreakpointChange: (nextBreakpoint) =>
                                setBreakpoint(nextBreakpoint),
                        },
                        widgetCards,
                    ),
                    h(
                        "section",
                        { className: "sn-react-widget-json", key: "json" },
                        [
                            h(
                                "h3",
                                {
                                    className: "sn-react-widget-json__title",
                                    key: "title",
                                },
                                "Current saved layout shape",
                            ),
                            h(
                                "p",
                                {
                                    className: "sn-text-muted",
                                    key: "description",
                                },
                                "Saved as { id, x, y, w, h } per breakpoint.",
                            ),
                            h("pre", { key: "payload" }, currentLayoutPreview),
                        ],
                    ),
                ],
            );
        }

        const root = createRoot(mount);
        root.render(h(WidgetsApp));
    }

    bootstrap();
}
