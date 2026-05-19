import { useEffect, useMemo, useState } from "react";

import { DashboardOverview } from "./components/dashboard/DashboardOverview";
import { AppShell, type AppSection } from "./components/layout/AppShell";
import { Card } from "./components/primitives/Card";
import {
    DataTable,
    type DataTableColumn,
} from "./components/primitives/DataTable";
import {
    FilterChips,
    type FilterChipOption,
} from "./components/primitives/FilterChips";
import { Modal } from "./components/primitives/Modal";
import { StatusPill } from "./components/primitives/StatusPill";
import { useRouteContextLoader } from "./hooks/useRouteContextLoader";
import {
    ApiClientError,
    listSubmitters,
    listWorkspaceMembers,
    patchFeedback,
    patchWorkspace,
} from "./lib/apiClient";
import { emitFrontendTelemetry } from "./lib/telemetry";
import type {
    FeedbackItemDto,
    FeedbackStatus,
    MemberDto,
    SubmitterDto,
    WorkspaceDto,
} from "./types/contracts";

export type AppPageKey =
    | "dashboard"
    | "inbox"
    | "feedback"
    | "roadmap"
    | "changelog"
    | "submitters"
    | "insights"
    | "settings";

export type ReactShellProps = {
    workspaceSlug: string;
    workspaceName: string;
    activeSection: AppSection;
    pageKey: AppPageKey;
    clientRelease: string;
};

type AsyncState<T> =
    | { state: "idle" }
    | { state: "loading" }
    | { state: "error"; error: ApiClientError }
    | { state: "ready"; data: T };

type RouteContextState = ReturnType<typeof useRouteContextLoader>;
type ReadyRouteContextData = Extract<
    RouteContextState,
    { state: "ready" }
>["data"];

const TRIAGE_STATUSES = new Set(["new", "needs_info", "reviewing"]);

const PAGE_TITLES: Record<AppPageKey, string> = {
    dashboard: "Dashboard",
    inbox: "Inbox",
    feedback: "Feedback",
    roadmap: "Roadmap",
    changelog: "Changelog",
    submitters: "Submitters",
    insights: "Insights",
    settings: "Settings",
};

const PAGE_DESCRIPTIONS: Record<AppPageKey, string> = {
    dashboard: "Workspace summary, routing context, and recent feedback.",
    inbox: "Triage queue with workflow status filters.",
    feedback: "Feedback archive view with broad status coverage.",
    roadmap: "Planned, in-progress, and shipped workflow lanes.",
    changelog: "Shipped items with publish toggle controls.",
    submitters: "Top submitters sorted by recent activity.",
    insights: "Status and pain-level distributions from current data.",
    settings: "Workspace profile, ownership controls, and members list.",
};

function humanizeValue(raw: string): string {
    return raw.replaceAll("_", " ");
}

function formatDateLabel(isoDatetime: string): string {
    const value = new Date(isoDatetime);
    if (Number.isNaN(value.getTime())) {
        return isoDatetime;
    }

    return value.toLocaleDateString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
    });
}

function normalizeError(error: unknown): ApiClientError {
    if (error instanceof ApiClientError) {
        return error;
    }
    if (error instanceof Error) {
        return new ApiClientError({
            status: 500,
            code: "internal_error",
            message: error.message,
        });
    }
    return new ApiClientError({
        status: 500,
        code: "internal_error",
        message: "An unexpected error occurred.",
    });
}

function defaultStatusFilter(pageKey: AppPageKey): string {
    return pageKey === "inbox" ? "triage" : "all";
}

function buildFeedbackColumns(
    workspaceSlug: string,
): DataTableColumn<FeedbackItemDto>[] {
    return [
        {
            key: "title",
            header: "Title",
            render: (item) => (
                <a href={`/w/${workspaceSlug}/feedback/${item.id}`}>
                    {item.title}
                </a>
            ),
        },
        {
            key: "status",
            header: "Status",
            render: (item) => <StatusPill status={item.status} />,
        },
        {
            key: "source",
            header: "Source",
            render: (item) => humanizeValue(item.source),
        },
        {
            key: "pain",
            header: "Pain",
            render: (item) => `${item.pain_level}/5`,
        },
        {
            key: "updated",
            header: "Updated",
            render: (item) => formatDateLabel(item.updated_at),
        },
    ];
}

function buildSubmitterColumns(
    workspaceSlug: string,
): DataTableColumn<SubmitterDto>[] {
    return [
        {
            key: "submitter",
            header: "Submitter",
            render: (item) => (
                <a href={`/w/${workspaceSlug}/submitters/${item.id}`}>
                    {item.name ?? item.email ?? "Unknown"}
                </a>
            ),
        },
        {
            key: "email",
            header: "Email",
            render: (item) => item.email ?? "-",
        },
        {
            key: "count",
            header: "Signals",
            render: (item) => String(item.submission_count),
        },
        {
            key: "lastSeen",
            header: "Last seen",
            render: (item) => formatDateLabel(item.last_seen_at),
        },
    ];
}

function defaultStatusOptions(): FilterChipOption[] {
    return [{ value: "all", label: "All statuses" }];
}

function defaultStatusPreview(): FeedbackStatus[] {
    return ["new", "needs_info", "reviewing", "accepted", "closed"];
}

function renderErrorMessage(error: ApiClientError): JSX.Element {
    return (
        <>
            <p>{error.message}</p>
            <p className="sn-react-error-meta">
                Error code:{" "}
                <span className="sn-react-inline-code">{error.code}</span>
                {error.requestId ? (
                    <>
                        {" "}
                        Request id:{" "}
                        <span className="sn-react-inline-code">
                            {error.requestId}
                        </span>
                    </>
                ) : null}
            </p>
        </>
    );
}

function deriveRoute(): string {
    if (typeof window === "undefined") {
        return "unknown";
    }
    if (window.location.pathname.trim().length === 0) {
        return "unknown";
    }
    return window.location.pathname;
}

function routeFeedbackData(routeState: RouteContextState): FeedbackItemDto[] {
    return routeState.state === "ready" ? routeState.data.feedbackItems : [];
}

export function App({
    workspaceSlug,
    workspaceName,
    activeSection,
    pageKey,
    clientRelease,
}: ReactShellProps): JSX.Element {
    const [activeStatusFilter, setActiveStatusFilter] = useState(
        defaultStatusFilter(pageKey),
    );
    const [showContextModal, setShowContextModal] = useState(false);
    const [feedbackItems, setFeedbackItems] = useState<FeedbackItemDto[]>([]);
    const [mutationNotice, setMutationNotice] = useState<string | null>(null);
    const [workspaceDraft, setWorkspaceDraft] = useState<WorkspaceDto | null>(
        null,
    );
    const [workspaceNameInput, setWorkspaceNameInput] = useState("");
    const [workspacePublicSubmit, setWorkspacePublicSubmit] = useState(false);
    const [workspaceSaving, setWorkspaceSaving] = useState(false);
    const [submittersState, setSubmittersState] = useState<
        AsyncState<SubmitterDto[]>
    >({ state: "idle" });
    const [membersState, setMembersState] = useState<AsyncState<MemberDto[]>>({
        state: "idle",
    });

    const feedbackPreviewLimit = pageKey === "dashboard" ? 12 : 100;

    const routeContext = useRouteContextLoader({
        workspaceSlug,
        workspaceNameHint: workspaceName,
        clientRelease,
        feedbackPreviewLimit,
        includeDashboardSummary: pageKey === "dashboard",
    });

    const readyRouteData =
        routeContext.state === "ready" ? routeContext.data : null;

    useEffect(() => {
        setActiveStatusFilter(defaultStatusFilter(pageKey));
    }, [pageKey]);

    useEffect(() => {
        if (readyRouteData === null) {
            setFeedbackItems([]);
            setWorkspaceDraft(null);
            setWorkspaceNameInput("");
            setWorkspacePublicSubmit(false);
            return;
        }

        setFeedbackItems(readyRouteData.feedbackItems);
        setWorkspaceDraft(readyRouteData.workspace);
        setWorkspaceNameInput(readyRouteData.workspace.name);
        setWorkspacePublicSubmit(
            readyRouteData.workspace.public_submit_enabled,
        );
    }, [readyRouteData]);

    useEffect(() => {
        if (typeof window === "undefined") {
            return;
        }

        const onError = (event: ErrorEvent): void => {
            emitFrontendTelemetry({
                event: "window_error",
                route: deriveRoute(),
                client_release: clientRelease,
                message: event.message.slice(0, 500),
            });
        };

        const onUnhandledRejection = (event: PromiseRejectionEvent): void => {
            const reason =
                event.reason instanceof Error
                    ? event.reason.message
                    : String(event.reason ?? "Unhandled rejection");
            emitFrontendTelemetry({
                event: "unhandled_rejection",
                route: deriveRoute(),
                client_release: clientRelease,
                message: reason.slice(0, 500),
            });
        };

        window.addEventListener("error", onError);
        window.addEventListener("unhandledrejection", onUnhandledRejection);
        return () => {
            window.removeEventListener("error", onError);
            window.removeEventListener(
                "unhandledrejection",
                onUnhandledRejection,
            );
        };
    }, [clientRelease]);

    const statusOptions = useMemo<FilterChipOption[]>(() => {
        if (feedbackItems.length === 0) {
            return defaultStatusOptions();
        }

        const statuses = Array.from(
            new Set(feedbackItems.map((item) => item.status)),
        ).sort();

        const options: FilterChipOption[] = [
            { value: "all", label: "All statuses" },
        ];
        if (pageKey === "inbox") {
            options.push({ value: "triage", label: "Needs triage" });
        }
        options.push(
            ...statuses.map((status) => ({
                value: status,
                label: humanizeValue(status),
            })),
        );
        return options;
    }, [feedbackItems, pageKey]);

    const filteredFeedback = useMemo<FeedbackItemDto[]>(() => {
        if (feedbackItems.length === 0) {
            return [];
        }

        if (activeStatusFilter === "all") {
            return feedbackItems;
        }

        if (activeStatusFilter === "triage") {
            return feedbackItems.filter((item) =>
                TRIAGE_STATUSES.has(item.status),
            );
        }

        return feedbackItems.filter(
            (item) => item.status === activeStatusFilter,
        );
    }, [activeStatusFilter, feedbackItems]);

    const statusPreview = useMemo(() => {
        if (feedbackItems.length === 0) {
            return defaultStatusPreview();
        }

        const uniqueStatuses = Array.from(
            new Set(feedbackItems.map((item) => item.status)),
        );
        return uniqueStatuses.length > 0
            ? uniqueStatuses
            : defaultStatusPreview();
    }, [feedbackItems]);

    const roadmapColumns = useMemo(() => {
        const grouped = new Map<string, FeedbackItemDto[]>();
        for (const status of ["planned", "in_progress", "shipped"]) {
            grouped.set(
                status,
                feedbackItems.filter((item) => item.status === status),
            );
        }
        return grouped;
    }, [feedbackItems]);

    const shippedItems = useMemo(
        () => feedbackItems.filter((item) => item.status === "shipped"),
        [feedbackItems],
    );

    const insightStatusRows = useMemo(() => {
        const counts = new Map<FeedbackStatus, number>();
        for (const item of feedbackItems) {
            counts.set(item.status, (counts.get(item.status) ?? 0) + 1);
        }
        return Array.from(counts.entries()).sort((a, b) => b[1] - a[1]);
    }, [feedbackItems]);

    const insightPainRows = useMemo(() => {
        const counts = new Map<number, number>();
        for (const item of feedbackItems) {
            counts.set(item.pain_level, (counts.get(item.pain_level) ?? 0) + 1);
        }
        return Array.from(counts.entries()).sort((a, b) => b[0] - a[0]);
    }, [feedbackItems]);

    const activeWorkspaceSlug =
        routeContext.state === "ready"
            ? routeContext.data.workspace.slug
            : workspaceSlug;

    const canEditWorkspace =
        routeContext.state === "ready" &&
        (routeContext.data.membership.role === "owner" ||
            routeContext.data.user.role === "admin");

    const readyRouteKey =
        routeContext.state === "ready"
            ? routeContext.data.workspace.slug
            : null;

    useEffect(() => {
        if (pageKey !== "submitters" || readyRouteKey === null) {
            return;
        }

        let disposed = false;
        setSubmittersState({ state: "loading" });
        void listSubmitters(readyRouteKey, clientRelease)
            .then((payload) => {
                if (!disposed) {
                    setSubmittersState({ state: "ready", data: payload.items });
                }
            })
            .catch((error: unknown) => {
                if (!disposed) {
                    setSubmittersState({
                        state: "error",
                        error: normalizeError(error),
                    });
                }
            });

        return () => {
            disposed = true;
        };
    }, [pageKey, readyRouteKey, clientRelease]);

    useEffect(() => {
        if (
            pageKey !== "settings" ||
            !canEditWorkspace ||
            readyRouteKey === null
        ) {
            return;
        }

        let disposed = false;
        setMembersState({ state: "loading" });

        void listWorkspaceMembers(readyRouteKey, clientRelease)
            .then((payload) => {
                if (!disposed) {
                    setMembersState({ state: "ready", data: payload.items });
                }
            })
            .catch((error: unknown) => {
                if (!disposed) {
                    setMembersState({
                        state: "error",
                        error: normalizeError(error),
                    });
                }
            });

        return () => {
            disposed = true;
        };
    }, [pageKey, canEditWorkspace, readyRouteKey, clientRelease]);

    const currentWorkspaceName =
        workspaceDraft !== null
            ? workspaceDraft.name
            : routeContext.state === "ready"
              ? routeContext.data.workspace.name
              : workspaceName;

    const feedbackColumns = useMemo(
        () => buildFeedbackColumns(workspaceSlug),
        [workspaceSlug],
    );
    const submitterColumns = useMemo(
        () => buildSubmitterColumns(workspaceSlug),
        [workspaceSlug],
    );

    async function moveRoadmapStatus(
        itemId: number,
        targetStatus: "planned" | "in_progress" | "shipped",
    ): Promise<void> {
        try {
            const updated = await patchFeedback(
                activeWorkspaceSlug,
                itemId,
                { status: targetStatus },
                clientRelease,
            );
            setFeedbackItems((current) =>
                current.map((item) =>
                    item.id === itemId ? { ...item, ...updated } : item,
                ),
            );
            setMutationNotice(
                `Moved item #${itemId} to ${humanizeValue(targetStatus)}.`,
            );
        } catch (error: unknown) {
            const apiError = normalizeError(error);
            setMutationNotice(
                `Could not move roadmap item: ${apiError.message}`,
            );
        }
    }

    async function toggleChangelogPublish(
        itemId: number,
        currentValue: boolean,
    ): Promise<void> {
        try {
            const updated = await patchFeedback(
                activeWorkspaceSlug,
                itemId,
                { published_to_changelog: !currentValue },
                clientRelease,
            );
            setFeedbackItems((current) =>
                current.map((item) =>
                    item.id === itemId ? { ...item, ...updated } : item,
                ),
            );
            setMutationNotice(
                !currentValue
                    ? `Published item #${itemId} to changelog.`
                    : `Unpublished item #${itemId} from changelog.`,
            );
        } catch (error: unknown) {
            const apiError = normalizeError(error);
            setMutationNotice(
                `Could not update changelog publish flag: ${apiError.message}`,
            );
        }
    }

    async function saveWorkspaceSettings(): Promise<void> {
        if (!canEditWorkspace || readyRouteKey === null) {
            return;
        }

        setWorkspaceSaving(true);
        setMutationNotice(null);
        try {
            const updated = await patchWorkspace(
                readyRouteKey,
                {
                    name: workspaceNameInput,
                    public_submit_enabled: workspacePublicSubmit,
                },
                clientRelease,
            );
            setWorkspaceDraft(updated);
            setWorkspaceNameInput(updated.name);
            setWorkspacePublicSubmit(updated.public_submit_enabled);
            setMutationNotice("Saved workspace settings.");
        } catch (error: unknown) {
            const apiError = normalizeError(error);
            setMutationNotice(
                `Could not save workspace settings: ${apiError.message}`,
            );
        } finally {
            setWorkspaceSaving(false);
        }
    }

    async function signOut(): Promise<void> {
        try {
            await fetch("/api/v1/auth/logout", {
                method: "POST",
                credentials: "same-origin",
            });
        } catch {
            // Best effort; redirect still clears the client route.
        }

        window.location.assign("/login");
    }

    function renderReadyState(routeData: ReadyRouteContextData): JSX.Element {
        switch (pageKey) {
            case "dashboard": {
                return (
                    <DashboardOverview
                        routeData={routeData}
                        clientRelease={clientRelease}
                        statusPreview={statusPreview}
                        feedbackColumns={feedbackColumns}
                        filteredFeedback={filteredFeedback}
                    />
                );
            }

            case "inbox":
            case "feedback": {
                return (
                    <>
                        <section
                            className="sn-react-filter-row"
                            aria-label="Workflow filters"
                        >
                            <FilterChips
                                ariaLabel="Filter feedback by status"
                                options={statusOptions}
                                activeValue={activeStatusFilter}
                                onChange={setActiveStatusFilter}
                            />
                            <div className="sn-react-toolbar-actions">
                                <button
                                    type="button"
                                    className="sn-button sn-button-secondary"
                                    onClick={() => {
                                        setShowContextModal(true);
                                    }}
                                >
                                    View route context
                                </button>
                            </div>
                        </section>

                        <Card
                            title={
                                pageKey === "inbox"
                                    ? "Triage queue"
                                    : "Feedback archive"
                            }
                            description="Filter, sort, and inspect feedback rows from the shared API surface."
                        >
                            <DataTable
                                caption="Feedback list"
                                columns={feedbackColumns}
                                rows={filteredFeedback}
                                getRowKey={(item) => item.id}
                                emptyMessage="No feedback matches the selected filter."
                            />
                        </Card>
                    </>
                );
            }

            case "roadmap": {
                return (
                    <section
                        className="sn-react-column-grid"
                        aria-label="Roadmap lanes"
                    >
                        {["planned", "in_progress", "shipped"].map(
                            (statusKey) => (
                                <Card
                                    key={statusKey}
                                    title={humanizeValue(statusKey)}
                                    description="Status lane"
                                >
                                    <ul className="sn-react-list" role="list">
                                        {(
                                            roadmapColumns.get(statusKey) ?? []
                                        ).map((item) => {
                                            const nextStatus =
                                                statusKey === "planned"
                                                    ? "in_progress"
                                                    : statusKey ===
                                                        "in_progress"
                                                      ? "shipped"
                                                      : null;
                                            return (
                                                <li key={item.id}>
                                                    <article className="sn-react-item-card">
                                                        <a
                                                            href={`/w/${workspaceSlug}/feedback/${item.id}`}
                                                        >
                                                            {item.title}
                                                        </a>
                                                        <p className="sn-text-muted">
                                                            Updated{" "}
                                                            {formatDateLabel(
                                                                item.updated_at,
                                                            )}
                                                        </p>
                                                        {nextStatus ? (
                                                            <button
                                                                type="button"
                                                                className="sn-button sn-button-secondary"
                                                                onClick={() => {
                                                                    void moveRoadmapStatus(
                                                                        item.id,
                                                                        nextStatus,
                                                                    );
                                                                }}
                                                            >
                                                                Move to{" "}
                                                                {humanizeValue(
                                                                    nextStatus,
                                                                )}
                                                            </button>
                                                        ) : null}
                                                    </article>
                                                </li>
                                            );
                                        })}
                                    </ul>
                                </Card>
                            ),
                        )}
                    </section>
                );
            }

            case "changelog": {
                return (
                    <Card
                        title="Shipped feedback"
                        description="Toggle publish state for shipped items."
                    >
                        <ul className="sn-react-list" role="list">
                            {shippedItems.map((item) => {
                                const isPublished =
                                    item.published_to_changelog === true;
                                return (
                                    <li key={item.id}>
                                        <article className="sn-react-item-card">
                                            <div className="sn-react-item-row">
                                                <a
                                                    href={`/w/${workspaceSlug}/feedback/${item.id}`}
                                                >
                                                    {item.title}
                                                </a>
                                                <StatusPill
                                                    status={item.status}
                                                />
                                            </div>
                                            {item.release_note ? (
                                                <p>{item.release_note}</p>
                                            ) : (
                                                <p className="sn-text-muted">
                                                    No release note yet.
                                                </p>
                                            )}
                                            <button
                                                type="button"
                                                className="sn-button sn-button-secondary"
                                                onClick={() => {
                                                    void toggleChangelogPublish(
                                                        item.id,
                                                        isPublished,
                                                    );
                                                }}
                                            >
                                                {isPublished
                                                    ? "Remove from public changelog"
                                                    : "Publish to public changelog"}
                                            </button>
                                        </article>
                                    </li>
                                );
                            })}
                        </ul>
                    </Card>
                );
            }

            case "submitters": {
                if (
                    submittersState.state === "loading" ||
                    submittersState.state === "idle"
                ) {
                    return (
                        <Card
                            title="Loading submitters"
                            description="Fetching workspace submitter activity from /api/v1/submitters."
                        >
                            <p className="sn-react-loader">
                                Loading submitter rows...
                            </p>
                        </Card>
                    );
                }

                if (submittersState.state === "error") {
                    return (
                        <Card
                            title="Unable to load submitters"
                            description="The submitters endpoint returned an error."
                        >
                            {renderErrorMessage(submittersState.error)}
                        </Card>
                    );
                }

                return (
                    <Card
                        title="Submitters"
                        description="Most recently active submitters in this workspace."
                    >
                        <DataTable
                            caption="Submitter list"
                            columns={submitterColumns}
                            rows={submittersState.data}
                            getRowKey={(item) => item.id}
                            emptyMessage="No submitters have been linked yet."
                        />
                    </Card>
                );
            }

            case "insights": {
                return (
                    <div className="sn-react-layout-grid">
                        <Card
                            title="Status distribution"
                            description="Counts from the currently loaded feedback data."
                        >
                            <ul className="sn-react-list" role="list">
                                {insightStatusRows.map(([status, count]) => (
                                    <li
                                        key={status}
                                        className="sn-react-item-row"
                                    >
                                        <StatusPill status={status} />
                                        <strong>{count}</strong>
                                    </li>
                                ))}
                            </ul>
                        </Card>

                        <Card
                            title="Pain-level histogram"
                            description="Quick bucketed counts by pain level (1-5)."
                        >
                            <ul className="sn-react-list" role="list">
                                {insightPainRows.map(([level, count]) => (
                                    <li
                                        key={level}
                                        className="sn-react-item-row"
                                    >
                                        <span>Pain {level}</span>
                                        <strong>{count}</strong>
                                    </li>
                                ))}
                            </ul>
                        </Card>
                    </div>
                );
            }

            case "settings": {
                return (
                    <div className="sn-react-layout-grid">
                        <Card
                            title="Workspace profile"
                            description="Name and public submit controls mirror the workspace settings API."
                        >
                            <form
                                className="sn-stack"
                                onSubmit={(event) => {
                                    event.preventDefault();
                                    void saveWorkspaceSettings();
                                }}
                            >
                                <label htmlFor="react-workspace-name">
                                    Workspace name
                                </label>
                                <input
                                    id="react-workspace-name"
                                    className="sn-input"
                                    type="text"
                                    value={workspaceNameInput}
                                    onChange={(event) => {
                                        setWorkspaceNameInput(
                                            event.target.value,
                                        );
                                    }}
                                    disabled={
                                        !canEditWorkspace || workspaceSaving
                                    }
                                />

                                <label
                                    className="sn-react-checkbox-row"
                                    htmlFor="react-public-submit"
                                >
                                    <input
                                        id="react-public-submit"
                                        type="checkbox"
                                        checked={workspacePublicSubmit}
                                        onChange={(event) => {
                                            setWorkspacePublicSubmit(
                                                event.target.checked,
                                            );
                                        }}
                                        disabled={
                                            !canEditWorkspace || workspaceSaving
                                        }
                                    />
                                    <span>Enable public submit form</span>
                                </label>

                                {canEditWorkspace ? (
                                    <button
                                        type="submit"
                                        className="sn-button sn-button-primary"
                                        disabled={workspaceSaving}
                                    >
                                        {workspaceSaving
                                            ? "Saving..."
                                            : "Save settings"}
                                    </button>
                                ) : (
                                    <p className="sn-text-muted">
                                        You have read-only access to this
                                        workspace.
                                    </p>
                                )}
                            </form>
                        </Card>

                        <Card
                            title="Workspace members"
                            description="Owner and team_member roles from /api/v1/workspaces/{slug}/members."
                        >
                            {membersState.state === "loading" ||
                            membersState.state === "idle" ? (
                                <p className="sn-react-loader">
                                    Loading members...
                                </p>
                            ) : null}

                            {membersState.state === "error"
                                ? renderErrorMessage(membersState.error)
                                : null}

                            {membersState.state === "ready" ? (
                                <ul className="sn-react-list" role="list">
                                    {membersState.data.map((member) => (
                                        <li
                                            key={member.user.id}
                                            className="sn-react-item-row"
                                        >
                                            <span>{member.user.email}</span>
                                            <span className="sn-react-inline-code">
                                                {member.role}
                                            </span>
                                        </li>
                                    ))}
                                </ul>
                            ) : null}
                        </Card>
                    </div>
                );
            }

            default:
                return (
                    <Card
                        title="Unsupported page"
                        description="This route key is not implemented in the React shell."
                    >
                        <p className="sn-text-muted">
                            Open a supported workspace route.
                        </p>
                    </Card>
                );
        }
    }

    return (
        <AppShell
            workspaceSlug={workspaceSlug}
            workspaceName={currentWorkspaceName}
            activeSection={activeSection}
            onSignOut={signOut}
        >
            <header className="sn-page-header">
                <div>
                    <h1 className="sn-page-header__title">
                        {PAGE_TITLES[pageKey]}
                    </h1>
                    <p className="sn-page-header__description">
                        {PAGE_DESCRIPTIONS[pageKey]}
                    </p>
                </div>
                <div className="sn-page-header__actions">
                    <button
                        type="button"
                        className="sn-button sn-button-secondary"
                        onClick={() => {
                            setShowContextModal(true);
                        }}
                    >
                        View route context
                    </button>
                </div>
            </header>

            {mutationNotice ? (
                <section className="sn-card sn-stack" aria-live="polite">
                    <p>{mutationNotice}</p>
                </section>
            ) : null}

            {routeContext.state === "loading" ? (
                <Card
                    title="Loading route context"
                    description="Fetching auth context, workspace details, and route payloads."
                >
                    <p className="sn-react-loader">
                        Loading React page data...
                    </p>
                </Card>
            ) : null}

            {routeContext.state === "error" ? (
                <Card
                    title="Unable to load route context"
                    description="The typed API client could not resolve auth + tenant context."
                >
                    {renderErrorMessage(routeContext.error)}
                </Card>
            ) : null}

            {routeContext.state === "ready"
                ? renderReadyState(routeContext.data)
                : null}

            <Modal
                id="react-route-context"
                title="Route context payload"
                open={showContextModal}
                onClose={() => {
                    setShowContextModal(false);
                }}
            >
                {routeContext.state === "ready" ? (
                    <dl className="sn-react-context-list">
                        <dt>User id</dt>
                        <dd>
                            <span className="sn-react-inline-code">
                                {routeContext.data.user.id}
                            </span>
                        </dd>
                        <dt>Membership workspace id</dt>
                        <dd>
                            <span className="sn-react-inline-code">
                                {routeContext.data.membership.workspace_id}
                            </span>
                        </dd>
                        <dt>Feedback rows loaded</dt>
                        <dd>{routeFeedbackData(routeContext).length}</dd>
                    </dl>
                ) : (
                    <p>Route context has not loaded yet.</p>
                )}
            </Modal>
        </AppShell>
    );
}
