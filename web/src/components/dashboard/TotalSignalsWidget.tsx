import { useId, useMemo } from "react";

import type { DashboardTotalSignalsWidgetDto } from "../../types/contracts";

interface TotalSignalsWidgetProps {
    workspaceSlug: string;
    widget: DashboardTotalSignalsWidgetDto;
}

interface SparklineCoordinate {
    x: number;
    y: number;
}

interface IncreaseMarker {
    label: "Largest increase" | "Second-largest increase";
    detail: string;
}

const CHART_WIDTH = 240;
const CHART_HEIGHT = 64;
const CHART_PADDING = 4;
const MARKER_LABELS: Array<IncreaseMarker["label"]> = [
    "Largest increase",
    "Second-largest increase",
];

function formatInteger(value: number): string {
    return new Intl.NumberFormat().format(value);
}

function formatSignedPercent(value: number): string {
    if (value > 0) {
        return `+${value}%`;
    }
    return `${value}%`;
}

function normalizeSparklinePoints(points: number[]): number[] {
    if (points.length === 0) {
        return [0, 0];
    }
    if (points.length === 1) {
        return [points[0], points[0]];
    }
    return points;
}

function toCoordinates(points: number[]): SparklineCoordinate[] {
    const maxPoint = Math.max(...points, 1);
    const width = CHART_WIDTH - CHART_PADDING * 2;
    const height = CHART_HEIGHT - CHART_PADDING * 2;
    const denominator = Math.max(points.length - 1, 1);

    return points.map((point, index) => {
        const x = CHART_PADDING + (index / denominator) * width;
        const y = CHART_PADDING + (1 - point / maxPoint) * height;
        return { x, y };
    });
}

function buildLinePath(coordinates: SparklineCoordinate[]): string {
    return coordinates
        .map((point, index) => {
            const command = index === 0 ? "M" : "L";
            return `${command} ${point.x} ${point.y}`;
        })
        .join(" ");
}

function buildAreaPath(coordinates: SparklineCoordinate[]): string {
    if (coordinates.length === 0) {
        return "";
    }

    const linePath = buildLinePath(coordinates);
    const firstPoint = coordinates[0];
    const lastPoint = coordinates[coordinates.length - 1];
    const baseline = CHART_HEIGHT - CHART_PADDING;
    return `${linePath} L ${lastPoint.x} ${baseline} L ${firstPoint.x} ${baseline} Z`;
}

function buildMarkers(
    points: number[],
    dateLabels: string[],
): IncreaseMarker[] {
    const deltas: Array<{ index: number; delta: number }> = [];
    for (let index = 1; index < points.length; index += 1) {
        const delta = points[index] - points[index - 1];
        if (delta > 0) {
            deltas.push({ index, delta });
        }
    }

    deltas.sort((left, right) => {
        if (right.delta !== left.delta) {
            return right.delta - left.delta;
        }
        return left.index - right.index;
    });

    return MARKER_LABELS.map((label, markerIndex) => {
        const match = deltas[markerIndex];
        if (!match) {
            return { label, detail: "No increase in this window" };
        }

        const dayLabel = dateLabels[match.index] ?? `Day ${match.index + 1}`;
        return {
            label,
            detail: `+${match.delta} on ${dayLabel}`,
        };
    });
}

function deltaDirectionClassName(direction: string): string {
    if (direction === "up") {
        return "sn-summary-card__delta sn-summary-card__delta--up";
    }
    if (direction === "down") {
        return "sn-summary-card__delta sn-summary-card__delta--down";
    }
    return "sn-summary-card__delta sn-summary-card__delta--flat";
}

function DeltaIcon({ direction }: { direction: string }): JSX.Element {
    if (direction === "up") {
        return (
            <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M12 3 4 11h5v10h6V11h5z" />
            </svg>
        );
    }

    if (direction === "down") {
        return (
            <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M12 21 4 13h5V3h6v10h5z" />
            </svg>
        );
    }

    return (
        <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M4 12h16v2H4z" />
        </svg>
    );
}

export function TotalSignalsWidget({
    workspaceSlug,
    widget,
}: TotalSignalsWidgetProps): JSX.Element {
    const normalizedPoints = useMemo(
        () => normalizeSparklinePoints(widget.sparkline_points),
        [widget.sparkline_points],
    );

    const dateLabels = useMemo(
        () =>
            widget.sparkline_date_labels.length === normalizedPoints.length
                ? widget.sparkline_date_labels
                : normalizedPoints.map((_, index) => `Day ${index + 1}`),
        [widget.sparkline_date_labels, normalizedPoints],
    );

    const coordinates = useMemo(
        () => toCoordinates(normalizedPoints),
        [normalizedPoints],
    );

    const linePath = useMemo(() => buildLinePath(coordinates), [coordinates]);
    const areaPath = useMemo(() => buildAreaPath(coordinates), [coordinates]);
    const markers = useMemo(
        () => buildMarkers(normalizedPoints, dateLabels),
        [normalizedPoints, dateLabels],
    );

    const gradientId = useId().replace(/:/g, "");
    const linkName = `${widget.label}: ${formatInteger(widget.value)} (${formatSignedPercent(widget.delta_pct)})`;

    return (
        <section
            className="sn-summary-card sn-summary-card--total-signals"
            data-widget-id={widget.widget_id}
        >
            <a
                className="sn-summary-card__kpi-link"
                href={`/w/${workspaceSlug}/feedback`}
                aria-label={linkName}
            >
                <div className="sn-summary-card__top">
                    <span className="sn-summary-card__title-wrap">
                        <img
                            className="sn-summary-card__title-icon"
                            src="/static/img/inbox-badge.svg"
                            alt=""
                            aria-hidden="true"
                        />
                        <span className="sn-summary-card__label">
                            {widget.label}
                        </span>
                    </span>
                </div>

                <div className="sn-summary-card__value-row">
                    <span className="sn-summary-card__value">
                        {formatInteger(widget.value)}
                    </span>
                    <span
                        className={deltaDirectionClassName(
                            widget.delta_direction,
                        )}
                    >
                        <span className="sn-summary-card__delta-icon">
                            <DeltaIcon direction={widget.delta_direction} />
                        </span>
                        <span>{formatSignedPercent(widget.delta_pct)}</span>
                        <span className="sr-only">
                            {widget.delta_direction === "up"
                                ? "Increase"
                                : widget.delta_direction === "down"
                                  ? "Decrease"
                                  : "No change"}
                        </span>
                    </span>
                </div>

                <p className="sn-summary-card__comparison">
                    {widget.comparison_label}
                </p>

                <div className="sn-summary-card__sparkline-wrap">
                    <svg
                        className="sn-summary-card__sparkline"
                        viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`}
                        role="img"
                        aria-label={`Total signals trend ${widget.comparison_label}`}
                    >
                        <defs>
                            <linearGradient
                                id={gradientId}
                                x1="0"
                                y1="0"
                                x2="0"
                                y2="1"
                            >
                                <stop
                                    className="sn-summary-card__sparkline-underfill-stop sn-summary-card__sparkline-underfill-stop--top"
                                    offset="0%"
                                />
                                <stop
                                    className="sn-summary-card__sparkline-underfill-stop sn-summary-card__sparkline-underfill-stop--mid"
                                    offset="65%"
                                />
                                <stop
                                    className="sn-summary-card__sparkline-underfill-stop sn-summary-card__sparkline-underfill-stop--base"
                                    offset="100%"
                                />
                            </linearGradient>
                        </defs>

                        <path
                            className="sn-summary-card__sparkline-underfill"
                            d={areaPath}
                            fill={`url(#${gradientId})`}
                        />
                        <path
                            className="sn-summary-card__sparkline-line"
                            d={linePath}
                            fill="none"
                        />
                        {coordinates.map((point, index) => (
                            <circle
                                key={`${point.x}-${point.y}-${index}`}
                                className="sn-summary-card__sparkline-point"
                                cx={point.x}
                                cy={point.y}
                                r="1.8"
                            />
                        ))}
                    </svg>
                </div>

                <ul className="sn-react-total-signals-markers" role="list">
                    {markers.map((marker) => (
                        <li key={marker.label}>
                            <span className="sn-react-total-signals-marker-label">
                                {marker.label}
                            </span>
                            <span className="sn-text-muted">
                                {marker.detail}
                            </span>
                        </li>
                    ))}
                </ul>
            </a>
        </section>
    );
}
