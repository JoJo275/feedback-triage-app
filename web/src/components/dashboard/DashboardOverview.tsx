import { Card } from "../primitives/Card";
import { DataTable, type DataTableColumn } from "../primitives/DataTable";
import { StatusPill } from "../primitives/StatusPill";

import type { RouteContextData } from "../../hooks/useRouteContextLoader";
import type {
    DashboardTotalSignalsWidgetDto,
    FeedbackItemDto,
} from "../../types/contracts";
import { TotalSignalsWidget } from "./TotalSignalsWidget";

interface DashboardOverviewProps {
    routeData: RouteContextData;
    clientRelease: string;
    statusPreview: string[];
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

export function DashboardOverview({
    routeData,
    clientRelease,
    statusPreview,
    feedbackColumns,
    filteredFeedback,
}: DashboardOverviewProps): JSX.Element {
    const widget =
        routeData.dashboardSummary?.total_signals_widget ?? EMPTY_WIDGET;

    return (
        <>
            <div className="sn-react-layout-grid">
                <TotalSignalsWidget
                    workspaceSlug={routeData.workspace.slug}
                    widget={widget}
                />

                <Card
                    title="Route context loaded"
                    description="Auth cookies and tenant scoping are validated per route."
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
                    title="Workflow status mix"
                    description="Quick preview of feedback status labels from the current payload."
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
                description="Most recent feedback rows from /api/v1/feedback."
            >
                <DataTable
                    caption="Recent feedback"
                    columns={feedbackColumns}
                    rows={filteredFeedback}
                    getRowKey={(item) => item.id}
                    emptyMessage="No feedback is available yet."
                />
            </Card>
        </>
    );
}
