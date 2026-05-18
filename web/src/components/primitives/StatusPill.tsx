import type { FeedbackStatus } from "../../types/contracts";

type StatusMeta = {
    label: string;
    tone: "info" | "warn" | "ok" | "muted" | "danger";
    icon: string;
};

const STATUS_META: Record<string, StatusMeta> = {
    new: { label: "new", tone: "info", icon: "*" },
    needs_info: { label: "needs info", tone: "warn", icon: "?" },
    reviewing: { label: "reviewing", tone: "info", icon: "~" },
    accepted: { label: "accepted", tone: "ok", icon: "+" },
    planned: { label: "planned", tone: "ok", icon: ">" },
    in_progress: { label: "in progress", tone: "ok", icon: ">" },
    shipped: { label: "shipped", tone: "ok", icon: "#" },
    closed: { label: "closed", tone: "muted", icon: "o" },
    spam: { label: "spam", tone: "danger", icon: "x" },
    rejected: { label: "rejected", tone: "muted", icon: "-" },
};

interface StatusPillProps {
    status: FeedbackStatus;
}

export function StatusPill({ status }: StatusPillProps): JSX.Element {
    const fallbackLabel = status.replaceAll("_", " ");
    const meta = STATUS_META[status] ?? {
        label: fallbackLabel,
        tone: "muted",
        icon: "o",
    };

    return (
        <span
            className={`sn-pill-status sn-pill-status--${meta.tone}`}
            data-status={status}
        >
            <span className="sn-pill-icon" aria-hidden="true">
                {meta.icon}
            </span>
            {meta.label}
        </span>
    );
}
