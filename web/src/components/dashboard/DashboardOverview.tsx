import { Card } from "../primitives/Card";
import { DataTable, type DataTableColumn } from "../primitives/DataTable";
import { StatusPill } from "../primitives/StatusPill";

import type { RouteContextData } from "../../hooks/useRouteContextLoader";
import type {
    DashboardTotalSignalsWidgetDto,
    FeedbackItemDto,
    FeedbackStatus,
} from "../../types/contracts";
import { TotalSignalsWidget } from "./TotalSignalsWidget";

interface DashboardOverviewProps {
    routeData: RouteContextData;
    clientRelease: string;
    statusPreview: FeedbackStatus[];
    feedbackColumns: DataTableColumn<FeedbackItemDto>[];
    filteredFeedback: FeedbackItemDto[];
}

const EMPTY_WIDGET: DashboardTotalSignalsWidgetDto = {
    widget_id: "kpi-total-signals",
    label: "Total signals",
    value: 0,
    delta_pct: 0,
    delta_direction: "flat",
    comparison_label: "vs prior period",
    sparkline_points: Array.from({ length: 30 }, () => 0),
    sparkline_date_labels: Array.from(
        { length: 30 },
        (_, index) => `Day ${index + 1}`,
    ),
};

const ACTIONABLE_STATUSES = new Set<FeedbackStatus>([
    "new",
    "needs_info",
    "reviewing",
]);
const CLOSED_STATUSES = new Set<FeedbackStatus>(["shipped", "closed", "spam"]);
const FOURTEEN_DAYS_IN_MS = 14 * 24 * 60 * 60 * 1000;
const STATUS_RANK: Record<string, number> = {
    new: 0,
    needs_info: 1,
    reviewing: 2,
    accepted: 3,
    planned: 4,
    in_progress: 5,
    shipped: 6,
    closed: 7,
    spam: 8,
    rejected: 9,
};

function toTimestamp(isoDatetime: string): number {
    const parsed = Date.parse(isoDatetime);
    if (Number.isNaN(parsed)) {
        return 0;
    }
    return parsed;
}

function formatDateRangeLabel(dayIso: string): string {
    const parsed = new Date(dayIso);
    if (Number.isNaN(parsed.getTime())) {
        return dayIso;
    }
    return parsed.toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
    });
}

function buildPolylinePoints(values: number[]): string {
    if (values.length === 0) {
        return "";
    }

    const denominator = Math.max(values.length - 1, 1);
    const maxValue = Math.max(...values, 1);

    return values
        .map((value, index) => {
            const x = (index / denominator) * 100;
            const y = 100 - (value / maxValue) * 100;
            return `${x},${y}`;
        })
        .join(" ");
}

export function DashboardOverview({
    routeData,
    clientRelease,
    statusPreview,
    feedbackColumns,
    filteredFeedback,
}: DashboardOverviewProps): JSX.Element {
    const widget =
        routeData.dashboardSummary?.total_signals_widget ?? EMPTY_WIDGET;

    const counts = routeData.dashboardSummary?.counts;
    const nowTimestamp = Date.now();

    const queueRows = [...filteredFeedback]
        .sort((left, right) => {
            if (right.pain_level !== left.pain_level) {
                return right.pain_level - left.pain_level;
            }

            const leftRank = STATUS_RANK[left.status] ?? 99;
            const rightRank = STATUS_RANK[right.status] ?? 99;
            if (leftRank !== rightRank) {
                return leftRank - rightRank;
            }

            return toTimestamp(right.updated_at) - toTimestamp(left.updated_at);
        })
        .slice(0, 8);

    const triageCount = filteredFeedback.filter((item) =>
        ACTIONABLE_STATUSES.has(item.status),
    ).length;
    const highPainCount = filteredFeedback.filter(
        (item) => item.pain_level >= 4,
    ).length;
    const reviewingCount = filteredFeedback.filter(
        (item) => item.status === "reviewing",
    ).length;
    const shippedCount = filteredFeedback.filter(
        (item) => item.status === "shipped",
    ).length;

    const unassignedCount = filteredFeedback.filter(
        (item) =>
            item.assignee_user_id === null && !CLOSED_STATUSES.has(item.status),
    ).length;
    const staleActionableCount = filteredFeedback.filter(
        (item) =>
            ACTIONABLE_STATUSES.has(item.status) &&
            nowTimestamp - toTimestamp(item.created_at) > FOURTEEN_DAYS_IN_MS,
    ).length;

    const totalSignals = counts?.total_signals ?? filteredFeedback.length;
    const needsAction = counts?.needs_action ?? triageCount;
    const highPainSignals = counts?.high_pain_signals ?? highPainCount;

    const statusCounts = new Map<FeedbackStatus, number>();
    for (const item of filteredFeedback) {
        statusCounts.set(item.status, (statusCounts.get(item.status) ?? 0) + 1);
    }

    const orderedStatuses = statusPreview.filter((status) =>
        statusCounts.has(status),
    );
    const extraStatuses = Array.from(statusCounts.keys()).filter(
        (status) => !orderedStatuses.includes(status),
    );
    const statusOrder = [...orderedStatuses, ...extraStatuses];

    const statusMixRows = statusOrder.map((status) => {
        const count = statusCounts.get(status) ?? 0;
        const percent =
            totalSignals > 0 ? Math.round((count / totalSignals) * 100) : 0;
        return { status, count, percent };
    });

    const intakeSeries = routeData.dashboardSummary?.intake_30d ?? [];
    const throughputPoints = intakeSeries.map((point) => point.received);
    const throughputPolyline = buildPolylinePoints(throughputPoints);
    const throughputStart =
        intakeSeries.length > 0
            ? formatDateRangeLabel(intakeSeries[0].day)
            : null;
    const throughputEnd =
        intakeSeries.length > 0
            ? formatDateRangeLabel(intakeSeries[intakeSeries.length - 1].day)
            : null;

    return (
        <section
            className="sn-dashboard-layout"
            data-density="dense"
            data-edit-mode="false"
        >
            <div className="sn-dashboard-canvas" data-layout-mode="default">
                <section
                    className="sn-summary-row"
                    aria-label="Summary metrics"
                >
                    <TotalSignalsWidget
                        workspaceSlug={routeData.workspace.slug}
                        widget={widget}
                    />

                    <section
                        className="sn-summary-card"
                        data-widget-id="kpi-needs-action"
                    >
                        <span className="sn-summary-card__label">
                            Needs action
                        </span>
                        <span className="sn-summary-card__count">
                            {needsAction}
                        </span>
                        <span className="sn-summary-card__delta">
                            New + needs info + reviewing
                        </span>
                    </section>

                    <section
                        className="sn-summary-card"
                        data-widget-id="kpi-high-pain"
                    >
                        <span className="sn-summary-card__label">
                            High pain signals
                        </span>
                        <span className="sn-summary-card__count">
                            {highPainSignals}
                        </span>
                        <span className="sn-summary-card__delta">
                            Pain level 4 or 5
                        </span>
                    </section>

                    <section
                        className="sn-summary-card"
                        data-widget-id="kpi-reviewing"
                    >
                        <span className="sn-summary-card__label">
                            Reviewing now
                        </span>
                        <span className="sn-summary-card__count">
                            {reviewingCount}
                        </span>
                        <span className="sn-summary-card__delta">
                            Active triage stage
                        </span>
                    </section>

                    <section
                        className="sn-summary-card"
                        data-widget-id="kpi-shipped"
                    >
                        <span className="sn-summary-card__label">Shipped</span>
                        <span className="sn-summary-card__count">
                            {shippedCount}
                        </span>
                        <span className="sn-summary-card__delta">
                            Closed this cycle
                        </span>
                    </section>
                </section>

                <section
                    className="sn-work-row"
                    aria-label="Operational workbench"
                >
                    <Card
                        title="Action queue"
                        description="Urgency-first view of feedback that needs product attention."
                        className="sn-dashboard-queue"
                    >
                        <nav
                            className="sn-dashboard-queue__quick-views"
                            aria-label="Action queue quick views"
                        >
                            <a
                                className="sn-dashboard-queue__link"
                                href={`/w/${routeData.workspace.slug}/inbox?status=new`}
                            >
                                New ({statusCounts.get("new") ?? 0})
                            </a>
                            <a
                                className="sn-dashboard-queue__link"
                                href={`/w/${routeData.workspace.slug}/inbox?status=needs_info`}
                            >
                                Needs info (
                                {statusCounts.get("needs_info") ?? 0})
                            </a>
                            <a
                                className="sn-dashboard-queue__link"
                                href={`/w/${routeData.workspace.slug}/feedback?status=reviewing`}
                            >
                                Reviewing ({reviewingCount})
                            </a>
                            <a
                                className="sn-dashboard-queue__link"
                                href={`/w/${routeData.workspace.slug}/feedback?status=shipped`}
                            >
                                Shipped ({shippedCount})
                            </a>
                        </nav>
                        <div className="sn-dashboard-queue__table-wrap">
                            <DataTable
                                caption="Action queue"
                                columns={feedbackColumns}
                                rows={queueRows}
                                getRowKey={(item) => item.id}
                                emptyMessage="No feedback is available yet."
                            />
                        </div>
                    </Card>

                    <aside
                        className="sn-attention-panel"
                        aria-labelledby="sn-dashboard-attention-title"
                    >
                        <h2
                            id="sn-dashboard-attention-title"
                            className="sn-attention-panel__title"
                        >
                            Needs attention
                        </h2>
                        <ul className="sn-attention-panel__list" role="list">
                            <li>
                                <a
                                    href={`/w/${routeData.workspace.slug}/inbox?status=new`}
                                >
                                    <span className="sn-attention-panel__count">
                                        {statusCounts.get("new") ?? 0}
                                    </span>
                                    <span>New signals to triage</span>
                                </a>
                            </li>
                            <li>
                                <a
                                    href={`/w/${routeData.workspace.slug}/inbox?status=needs_info`}
                                >
                                    <span className="sn-attention-panel__count">
                                        {statusCounts.get("needs_info") ?? 0}
                                    </span>
                                    <span>Waiting on follow-up details</span>
                                </a>
                            </li>
                            <li>
                                <a
                                    href={`/w/${routeData.workspace.slug}/feedback?stale=true`}
                                >
                                    <span className="sn-attention-panel__count">
                                        {staleActionableCount}
                                    </span>
                                    <span>Older than 14 days in triage</span>
                                </a>
                            </li>
                            <li>
                                <a
                                    href={`/w/${routeData.workspace.slug}/feedback?published_to_changelog=false`}
                                >
                                    <span className="sn-attention-panel__count">
                                        {unassignedCount}
                                    </span>
                                    <span>Unassigned open signals</span>
                                </a>
                            </li>
                        </ul>
                        <a
                            className="sn-button sn-button-secondary sn-attention-panel__cta"
                            href={`/w/${routeData.workspace.slug}/inbox`}
                        >
                            Open inbox
                        </a>
                    </aside>
                </section>

                <section
                    className="sn-dashboard-duo-row"
                    aria-label="Dashboard health"
                >
                    <Card
                        title="Signals over time"
                        description="30-day intake trend from /api/v1/dashboard/summary."
                    >
                        {throughputPoints.length > 1 ? (
                            <>
                                <svg
                                    className="sn-throughput-chart"
                                    viewBox="0 0 100 100"
                                    role="img"
                                    aria-label="Signals received over the last 30 days"
                                >
                                    <polyline
                                        className="sn-throughput-line sn-throughput-line--received"
                                        fill="none"
                                        points={throughputPolyline}
                                    />
                                </svg>
                                <p className="sn-sparkline__caption sn-text-muted">
                                    {throughputStart} - {throughputEnd}
                                </p>
                            </>
                        ) : (
                            <p className="sn-text-muted">
                                More intake history will appear here after
                                additional activity.
                            </p>
                        )}
                    </Card>

                    <Card
                        title="Workflow status mix"
                        description="Distribution across active workflow statuses."
                    >
                        {statusMixRows.length > 0 ? (
                            <ul className="sn-status-mix" role="list">
                                {statusMixRows.map((row) => (
                                    <li key={row.status}>
                                        <div className="sn-status-mix__meta">
                                            <StatusPill status={row.status} />
                                            <span>
                                                {row.count} ({row.percent}%)
                                            </span>
                                        </div>
                                        <span className="sn-status-mix__meter">
                                            <span
                                                className="sn-status-mix__fill"
                                                style={{
                                                    width: `${Math.max(
                                                        row.percent,
                                                        row.count > 0 ? 4 : 0,
                                                    )}%`,
                                                }}
                                            />
                                        </span>
                                    </li>
                                ))}
                            </ul>
                        ) : (
                            <p className="sn-text-muted">
                                No status data is available yet.
                            </p>
                        )}
                    </Card>
                </section>

                <section
                    className="sn-dashboard-duo-row"
                    aria-label="Route context and release information"
                >
                    <Card
                        title="Route context loaded"
                        description="Auth, workspace scope, and release metadata for this dashboard route."
                    >
                        <dl className="sn-react-context-list">
                            <dt>User</dt>
                            <dd>{routeData.user.email}</dd>
                            <dt>Role</dt>
                            <dd>
                                {routeData.membership.role.replaceAll("_", " ")}
                            </dd>
                            <dt>Workspace</dt>
                            <dd>{routeData.workspace.name}</dd>
                            <dt>Release header</dt>
                            <dd>
                                <span className="sn-react-inline-code">
                                    {clientRelease}
                                </span>
                            </dd>
                        </dl>
                    </Card>

                    <Card
                        title="Workflow labels"
                        description="Current status vocabulary used by this workspace."
                    >
                        <div className="sn-react-pill-row">
                            {statusPreview.map((status) => (
                                <StatusPill key={status} status={status} />
                            ))}
                        </div>
                        <ul className="sn-metric-list" role="list">
                            <li>
                                <span>Needs action</span>
                                <strong>{triageCount}</strong>
                            </li>
                            <li>
                                <span>High pain open</span>
                                <strong>{highPainCount}</strong>
                            </li>
                            <li>
                                <span>Total signals</span>
                                <strong>{totalSignals}</strong>
                            </li>
                        </ul>
                    </Card>
                </section>
            </div>
        </section>
    );
}
