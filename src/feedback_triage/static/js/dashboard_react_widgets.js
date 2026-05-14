const mount = document.getElementById("sn-react-widget-root");

if (!mount) {
    // Not on the React widgets pilot page.
} else {
    const workspaceSlug = mount.dataset.workspaceSlug || "default";
    const dashboardUrl =
        mount.dataset.dashboardUrl || `/w/${workspaceSlug}/dashboard`;

    const STORAGE_KEY = `sn.react.dashboard-layout.${workspaceSlug}.v1`;
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
            id: "kpi_strip",
            title: "KPI strip",
            body: "Fast-scan counts for total signals, needs action, and high pain.",
        },
        {
            id: "throughput",
            title: "Signals over time",
            body: "Received, triaged, and resolved trend view.",
        },
        {
            id: "status_mix",
            title: "Status mix",
            body: "Workflow distribution to expose bottlenecks.",
        },
        {
            id: "aging",
            title: "Aging / SLA",
            body: "Open-item aging buckets and high-pain SLA pressure.",
        },
        {
            id: "workload",
            title: "Team workload",
            body: "Owner-level open/high-pain/overdue workload lens.",
        },
        {
            id: "action_queue",
            title: "Action queue",
            body: "Urgency-first list for next triage actions.",
        },
    ];

    const DEFAULT_LAYOUTS = {
        lg: [
            { i: "kpi_strip", x: 0, y: 0, w: 4, h: 4, minW: 3, minH: 3 },
            { i: "throughput", x: 4, y: 0, w: 8, h: 6, minW: 4, minH: 4 },
            { i: "status_mix", x: 0, y: 4, w: 4, h: 6, minW: 3, minH: 4 },
            { i: "aging", x: 4, y: 6, w: 4, h: 6, minW: 3, minH: 4 },
            { i: "workload", x: 8, y: 6, w: 4, h: 6, minW: 3, minH: 4 },
            { i: "action_queue", x: 0, y: 12, w: 12, h: 8, minW: 8, minH: 5 },
        ],
        md: [
            { i: "kpi_strip", x: 0, y: 0, w: 4, h: 4, minW: 3, minH: 3 },
            { i: "throughput", x: 4, y: 0, w: 8, h: 6, minW: 4, minH: 4 },
            { i: "status_mix", x: 0, y: 4, w: 4, h: 6, minW: 3, minH: 4 },
            { i: "aging", x: 4, y: 6, w: 4, h: 6, minW: 3, minH: 4 },
            { i: "workload", x: 8, y: 6, w: 4, h: 6, minW: 3, minH: 4 },
            { i: "action_queue", x: 0, y: 12, w: 12, h: 8, minW: 8, minH: 5 },
        ],
        sm: [
            { i: "kpi_strip", x: 0, y: 0, w: 3, h: 4, minW: 2, minH: 3 },
            { i: "throughput", x: 0, y: 4, w: 6, h: 6, minW: 3, minH: 4 },
            { i: "status_mix", x: 0, y: 10, w: 3, h: 6, minW: 2, minH: 4 },
            { i: "aging", x: 3, y: 10, w: 3, h: 6, minW: 2, minH: 4 },
            { i: "workload", x: 0, y: 16, w: 6, h: 6, minW: 3, minH: 4 },
            { i: "action_queue", x: 0, y: 22, w: 6, h: 8, minW: 4, minH: 5 },
        ],
        xs: [
            { i: "kpi_strip", x: 0, y: 0, w: 4, h: 4, minW: 2, minH: 3 },
            { i: "throughput", x: 0, y: 4, w: 4, h: 6, minW: 2, minH: 4 },
            { i: "status_mix", x: 0, y: 10, w: 2, h: 6, minW: 2, minH: 4 },
            { i: "aging", x: 2, y: 10, w: 2, h: 6, minW: 2, minH: 4 },
            { i: "workload", x: 0, y: 16, w: 4, h: 6, minW: 2, minH: 4 },
            { i: "action_queue", x: 0, y: 22, w: 4, h: 8, minW: 2, minH: 5 },
        ],
        xxs: [
            { i: "kpi_strip", x: 0, y: 0, w: 2, h: 4, minW: 1, minH: 3 },
            { i: "throughput", x: 0, y: 4, w: 2, h: 6, minW: 1, minH: 4 },
            { i: "status_mix", x: 0, y: 10, w: 2, h: 6, minW: 1, minH: 4 },
            { i: "aging", x: 0, y: 16, w: 2, h: 6, minW: 1, minH: 4 },
            { i: "workload", x: 0, y: 22, w: 2, h: 6, minW: 1, minH: 4 },
            { i: "action_queue", x: 0, y: 28, w: 2, h: 8, minW: 1, minH: 5 },
        ],
    };

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

    function loadLayouts() {
        const raw = safeLocalStorageGet(STORAGE_KEY);
        if (!raw) {
            return cloneLayouts(DEFAULT_LAYOUTS);
        }

        try {
            const parsed = JSON.parse(raw);
            if (!parsed || typeof parsed !== "object") {
                return cloneLayouts(DEFAULT_LAYOUTS);
            }

            if (parsed.version !== 1) {
                return cloneLayouts(DEFAULT_LAYOUTS);
            }

            return fromPersistedLayouts(parsed.layouts);
        } catch {
            return cloneLayouts(DEFAULT_LAYOUTS);
        }
    }

    function saveLayouts(layouts) {
        const payload = {
            version: 1,
            layouts: toPersistedLayouts(layouts),
            savedAt: new Date().toISOString(),
        };
        safeLocalStorageSet(STORAGE_KEY, JSON.stringify(payload));
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

            function persistNow(nextLayouts, messagePrefix) {
                saveLayouts(nextLayouts);
                setSaveStatus(`${messagePrefix} ${formatTime(new Date())}`);
            }

            function queuePersist(nextLayouts) {
                if (saveTimerRef.current !== null) {
                    window.clearTimeout(saveTimerRef.current);
                }

                setSaveStatus("Saving...");
                saveTimerRef.current = window.setTimeout(() => {
                    persistNow(nextLayouts, "Saved at");
                    saveTimerRef.current = null;
                }, 320);
            }

            function handleLayoutChange(_currentLayout, allLayouts) {
                const normalized = normalizeLayouts(allLayouts);
                setLayouts(normalized);
                queuePersist(normalized);
            }

            function handleReset() {
                const defaults = cloneLayouts(DEFAULT_LAYOUTS);
                setLayouts(defaults);
                persistNow(defaults, "Reset and saved at");
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
