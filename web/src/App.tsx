import { useMemo, useState } from "react";

import { AppShell } from "./components/layout/AppShell";
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
import { ApiClientError } from "./lib/apiClient";
import type { FeedbackItemDto } from "./types/contracts";

export type ReactShellProps = {
    workspaceSlug: string;
    workspaceName: string;
    dashboardUrl: string;
    clientRelease: string;
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

function defaultStatusOptions(): FilterChipOption[] {
    return [{ value: "all", label: "All statuses" }];
}

function defaultStatusPreview(): string[] {
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

export function App({
    workspaceSlug,
    workspaceName,
    dashboardUrl,
    clientRelease,
}: ReactShellProps): JSX.Element {
    const [activeStatusFilter, setActiveStatusFilter] = useState("all");
    const [showContextModal, setShowContextModal] = useState(false);

    const routeContext = useRouteContextLoader({
        workspaceSlug,
        workspaceNameHint: workspaceName,
        clientRelease,
    });

    const statusOptions = useMemo<FilterChipOption[]>(() => {
        if (routeContext.state !== "ready") {
            return defaultStatusOptions();
        }

        const statuses = Array.from(
            new Set(routeContext.data.feedbackItems.map((item) => item.status)),
        ).sort();

        return [
            { value: "all", label: "All statuses" },
            ...statuses.map((status) => ({
                value: status,
                label: humanizeValue(status),
            })),
        ];
    }, [routeContext]);

    const filteredFeedback = useMemo(() => {
        if (routeContext.state !== "ready") {
            return [];
        }

        if (activeStatusFilter === "all") {
            return routeContext.data.feedbackItems;
        }

        return routeContext.data.feedbackItems.filter(
            (item) => item.status === activeStatusFilter,
        );
    }, [activeStatusFilter, routeContext]);

    const statusPreview = useMemo(() => {
        if (routeContext.state !== "ready") {
            return defaultStatusPreview();
        }

        const uniqueStatuses = Array.from(
            new Set(routeContext.data.feedbackItems.map((item) => item.status)),
        );
        return uniqueStatuses.length > 0
            ? uniqueStatuses
            : defaultStatusPreview();
    }, [routeContext]);

    const currentWorkspaceName =
        routeContext.state === "ready"
            ? routeContext.data.workspace.name
            : workspaceName;

    const feedbackColumns = useMemo(
        () => buildFeedbackColumns(workspaceSlug),
        [workspaceSlug],
    );

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

    return (
        <AppShell
            workspaceSlug={workspaceSlug}
            workspaceName={currentWorkspaceName}
            activeSection="dashboard"
            onSignOut={signOut}
        >
            <header className="sn-page-header">
                <div>
                    <h1 className="sn-page-header__title">
                        Dashboard (React shell canary)
                    </h1>
                    <p className="sn-page-header__description">
                        Phase 1 shared shell primitives, typed API client, and
                        route-level auth/tenant context loader.
                    </p>
                </div>
                <div className="sn-page-header__actions">
                    <a
                        className="sn-button sn-button-secondary"
                        href={dashboardUrl}
                    >
                        Classic dashboard
                    </a>
                </div>
            </header>

            <section
                className="sn-react-filter-row"
                aria-label="Preview controls"
            >
                <FilterChips
                    ariaLabel="Filter preview table by status"
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

            {routeContext.state === "loading" ? (
                <Card
                    title="Loading route context"
                    description="Fetching /api/v1/auth/me, workspace details, and preview feedback."
                >
                    <p className="sn-react-loader">
                        Loading React shell data...
                    </p>
                </Card>
            ) : null}

            {routeContext.state === "error" ? (
                <Card
                    title="Unable to load route context"
                    description="This surfaced from the typed API client and normalized envelope handler."
                >
                    {renderErrorMessage(routeContext.error)}
                    <p>
                        <a href={dashboardUrl}>Back to the classic dashboard</a>
                    </p>
                </Card>
            ) : null}

            {routeContext.state === "ready" ? (
                <>
                    <div className="sn-react-layout-grid">
                        <Card
                            title="Route context loaded"
                            description="Auth cookies and tenant scoping are validated per route."
                        >
                            <dl className="sn-react-context-list">
                                <dt>User</dt>
                                <dd>{routeContext.data.user.email}</dd>
                                <dt>Role</dt>
                                <dd>
                                    {humanizeValue(
                                        routeContext.data.membership.role,
                                    )}
                                </dd>
                                <dt>Workspace</dt>
                                <dd>{routeContext.data.workspace.name}</dd>
                                <dt>Slug</dt>
                                <dd>
                                    <span className="sn-react-inline-code">
                                        {routeContext.data.workspace.slug}
                                    </span>
                                </dd>
                                <dt>Release header</dt>
                                <dd>
                                    <span className="sn-react-inline-code">
                                        {clientRelease}
                                    </span>
                                </dd>
                            </dl>
                        </Card>

                        <Card
                            title="Status pill primitive"
                            description="Tone + icon + label rendering for workflow status values."
                        >
                            <div className="sn-react-pill-row">
                                {statusPreview.map((status) => (
                                    <StatusPill key={status} status={status} />
                                ))}
                            </div>
                        </Card>
                    </div>

                    <Card
                        title="Recent feedback"
                        description="Table primitive backed by typed /api/v1/feedback data."
                    >
                        <DataTable
                            caption="Recent feedback preview"
                            columns={feedbackColumns}
                            rows={filteredFeedback}
                            getRowKey={(item) => item.id}
                            emptyMessage="No feedback matches this status filter."
                        />
                    </Card>
                </>
            ) : null}

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
                        <dt>Preview item count</dt>
                        <dd>{routeContext.data.feedbackItems.length}</dd>
                    </dl>
                ) : (
                    <p>Route context has not loaded yet.</p>
                )}
            </Modal>
        </AppShell>
    );
}
