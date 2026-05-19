import { type FormEvent, useMemo, useRef, useState } from "react";

import {
    ApiClientError,
    submitPublicFeedback,
    type PublicFeedbackSubmitRequest,
} from "./lib/apiClient";

export type PublicPageKey =
    | "landing"
    | "public_submit"
    | "public_roadmap"
    | "public_changelog";

export interface PublicAppProps {
    pageKey: PublicPageKey;
    clientRelease: string;
    routePayload: unknown;
}

type DemoStatus =
    | "new"
    | "needs_info"
    | "reviewing"
    | "planned"
    | "in_progress"
    | "shipped";

interface DemoItem {
    id: number;
    title: string;
    status: DemoStatus;
    priority: "low" | "medium" | "high";
    pain: number;
}

interface LandingPayload {
    primary_workspace_slug: string | null;
}

interface SubmitPayload {
    workspace_slug: string;
    workspace_name: string;
}

interface PublicRoadmapTag {
    name: string;
    slug: string;
    color: string;
}

interface PublicRoadmapItem {
    id: number;
    title: string;
    type: string;
    type_other: string | null;
    tags: PublicRoadmapTag[];
}

interface PublicRoadmapPayload {
    workspace_slug: string;
    workspace_name: string;
    columns: {
        planned: PublicRoadmapItem[];
        in_progress: PublicRoadmapItem[];
        shipped: PublicRoadmapItem[];
    };
    is_empty: boolean;
}

interface PublicChangelogEntry {
    id: number;
    title: string;
    release_note: string | null;
    shipped_at_iso: string;
    shipped_at_label: string;
}

interface PublicChangelogPayload {
    workspace_slug: string;
    workspace_name: string;
    entries: PublicChangelogEntry[];
}

const DEMO_SEED: DemoItem[] = [
    {
        id: 1,
        title: "Add CSV export of feedback",
        status: "new",
        priority: "medium",
        pain: 3,
    },
    {
        id: 2,
        title: "Mobile sidebar collapses on tap",
        status: "needs_info",
        priority: "low",
        pain: 2,
    },
    {
        id: 3,
        title: "Bug: tag chips wrap oddly on Safari",
        status: "reviewing",
        priority: "high",
        pain: 4,
    },
    {
        id: 4,
        title: "Email digest of weekly intake",
        status: "planned",
        priority: "medium",
        pain: 3,
    },
    {
        id: 5,
        title: "Dark mode for the dashboard",
        status: "in_progress",
        priority: "low",
        pain: 2,
    },
    {
        id: 6,
        title: "Onboarding tour for new owners",
        status: "new",
        priority: "low",
        pain: 1,
    },
    {
        id: 7,
        title: "Slow load on the inbox over 1k items",
        status: "reviewing",
        priority: "high",
        pain: 5,
    },
    {
        id: 8,
        title: "Webhook for status changes",
        status: "needs_info",
        priority: "medium",
        pain: 3,
    },
    {
        id: 9,
        title: "Deletion is too easy to fat-finger",
        status: "new",
        priority: "medium",
        pain: 4,
    },
    {
        id: 10,
        title: "Add markdown to release notes",
        status: "shipped",
        priority: "low",
        pain: 2,
    },
];

const STATUS_FORWARD: Record<DemoStatus, DemoStatus> = {
    new: "needs_info",
    needs_info: "reviewing",
    reviewing: "planned",
    planned: "in_progress",
    in_progress: "shipped",
    shipped: "new",
};

const STATUS_LABEL: Record<DemoStatus, string> = {
    new: "New",
    needs_info: "Needs info",
    reviewing: "Reviewing",
    planned: "Planned",
    in_progress: "In progress",
    shipped: "Shipped",
};

const DEMO_STATUS_TONE: Record<DemoStatus, "info" | "warn" | "ok"> = {
    new: "info",
    needs_info: "warn",
    reviewing: "info",
    planned: "ok",
    in_progress: "ok",
    shipped: "ok",
};

const TYPE_LABELS: Record<string, string> = {
    bug: "Bug",
    feature_request: "Feature request",
    complaint: "Complaint",
    praise: "Praise",
    question: "Question",
    other: "Other",
};

function asRecord(value: unknown): Record<string, unknown> {
    if (value === null || typeof value !== "object") {
        return {};
    }
    return value as Record<string, unknown>;
}

function parseLandingPayload(payload: unknown): LandingPayload {
    const record = asRecord(payload);
    const rawSlug = record.primary_workspace_slug;
    return {
        primary_workspace_slug:
            typeof rawSlug === "string" && rawSlug.length > 0 ? rawSlug : null,
    };
}

function parseSubmitPayload(payload: unknown): SubmitPayload {
    const record = asRecord(payload);
    return {
        workspace_slug:
            typeof record.workspace_slug === "string"
                ? record.workspace_slug
                : "",
        workspace_name:
            typeof record.workspace_name === "string"
                ? record.workspace_name
                : "Workspace",
    };
}

function parseRoadmapTag(raw: unknown): PublicRoadmapTag | null {
    const record = asRecord(raw);
    if (typeof record.name !== "string") {
        return null;
    }
    return {
        name: record.name,
        slug: typeof record.slug === "string" ? record.slug : "",
        color: typeof record.color === "string" ? record.color : "slate",
    };
}

function parseRoadmapItem(raw: unknown): PublicRoadmapItem | null {
    const record = asRecord(raw);
    if (typeof record.id !== "number" || typeof record.title !== "string") {
        return null;
    }

    const rawTags = Array.isArray(record.tags) ? record.tags : [];
    const tags: PublicRoadmapTag[] = [];
    for (const entry of rawTags) {
        const tag = parseRoadmapTag(entry);
        if (tag !== null) {
            tags.push(tag);
        }
    }

    return {
        id: record.id,
        title: record.title,
        type: typeof record.type === "string" ? record.type : "other",
        type_other:
            typeof record.type_other === "string" ? record.type_other : null,
        tags,
    };
}

function parseRoadmapColumn(raw: unknown): PublicRoadmapItem[] {
    if (!Array.isArray(raw)) {
        return [];
    }

    const items: PublicRoadmapItem[] = [];
    for (const entry of raw) {
        const item = parseRoadmapItem(entry);
        if (item !== null) {
            items.push(item);
        }
    }
    return items;
}

function parseRoadmapPayload(payload: unknown): PublicRoadmapPayload {
    const record = asRecord(payload);
    const rawColumns = asRecord(record.columns);
    const planned = parseRoadmapColumn(rawColumns.planned);
    const inProgress = parseRoadmapColumn(rawColumns.in_progress);
    const shipped = parseRoadmapColumn(rawColumns.shipped);

    return {
        workspace_slug:
            typeof record.workspace_slug === "string"
                ? record.workspace_slug
                : "",
        workspace_name:
            typeof record.workspace_name === "string"
                ? record.workspace_name
                : "Workspace",
        columns: {
            planned,
            in_progress: inProgress,
            shipped,
        },
        is_empty:
            typeof record.is_empty === "boolean"
                ? record.is_empty
                : planned.length + inProgress.length + shipped.length === 0,
    };
}

function parseChangelogEntry(raw: unknown): PublicChangelogEntry | null {
    const record = asRecord(raw);
    if (
        typeof record.id !== "number" ||
        typeof record.title !== "string" ||
        typeof record.shipped_at_iso !== "string" ||
        typeof record.shipped_at_label !== "string"
    ) {
        return null;
    }

    return {
        id: record.id,
        title: record.title,
        release_note:
            typeof record.release_note === "string"
                ? record.release_note
                : null,
        shipped_at_iso: record.shipped_at_iso,
        shipped_at_label: record.shipped_at_label,
    };
}

function parseChangelogPayload(payload: unknown): PublicChangelogPayload {
    const record = asRecord(payload);
    const entries: PublicChangelogEntry[] = [];
    const rawEntries = Array.isArray(record.entries) ? record.entries : [];

    for (const entry of rawEntries) {
        const parsed = parseChangelogEntry(entry);
        if (parsed !== null) {
            entries.push(parsed);
        }
    }

    return {
        workspace_slug:
            typeof record.workspace_slug === "string"
                ? record.workspace_slug
                : "",
        workspace_name:
            typeof record.workspace_name === "string"
                ? record.workspace_name
                : "Workspace",
        entries,
    };
}

function renderPublicHeader(primaryWorkspaceSlug: string | null): JSX.Element {
    return (
        <header className="sn-public-header">
            <a
                className="sn-public-header__brand"
                href="/"
                aria-label="SignalNest home"
            >
                <img
                    src="/static/img/wordmark.svg"
                    alt="SignalNest"
                    width={156}
                    height={28}
                />
            </a>
            <nav className="sn-public-header__nav" aria-label="Primary">
                <ul role="list">
                    {primaryWorkspaceSlug ? (
                        <li>
                            <a
                                className="sn-button sn-button-primary"
                                href={`/w/${primaryWorkspaceSlug}/dashboard`}
                            >
                                Go to dashboard
                            </a>
                        </li>
                    ) : (
                        <>
                            <li>
                                <a href="/login">Log in</a>
                            </li>
                            <li>
                                <a
                                    className="sn-button sn-button-primary"
                                    href="/signup"
                                >
                                    Start free
                                </a>
                            </li>
                        </>
                    )}
                </ul>
            </nav>
        </header>
    );
}

function renderPublicFooter(): JSX.Element {
    return (
        <footer
            className="sn-public-footer"
            aria-labelledby="public-footer-heading"
        >
            <h2 id="public-footer-heading" className="sr-only">
                Site footer
            </h2>
            <div className="sn-public-footer__inner sn-content-gutter">
                <div className="sn-public-footer__meta">
                    <img
                        className="sn-public-footer__wordmark"
                        src="/static/img/wordmark.svg"
                        alt="SignalNest"
                        width={120}
                        height={22}
                    />
                    <p className="sn-public-footer__tagline">
                        Capture the noise. Find the signal.
                    </p>
                </div>
                <nav
                    className="sn-public-footer__nav"
                    aria-label="Legal and contact"
                >
                    <ul role="list">
                        <li>
                            <a href="/privacy">Privacy</a>
                        </li>
                        <li>
                            <a href="/terms">Terms</a>
                        </li>
                        <li>
                            <a
                                href="https://github.com/JoJo275/feedback-triage-app"
                                rel="noopener noreferrer"
                                target="_blank"
                            >
                                GitHub
                            </a>
                        </li>
                        <li>
                            <a href="mailto:hello@signalnest.app">Contact</a>
                        </li>
                    </ul>
                </nav>
                <p className="sn-public-footer__byline">
                    Built as a full-stack portfolio project, usable as a real
                    app.
                </p>
            </div>
        </footer>
    );
}

function renderTypeLabel(type: string, typeOther: string | null): string {
    if (type === "other" && typeOther) {
        return typeOther;
    }
    return TYPE_LABELS[type] ?? type;
}

function normalizeApiError(error: unknown): ApiClientError {
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
        message: "Submission failed. Check the form and try again.",
    });
}

function buildSubmitPayload(formData: FormData): PublicFeedbackSubmitRequest {
    const payload: PublicFeedbackSubmitRequest = {
        title: String(formData.get("title") ?? "").trim(),
        description: String(formData.get("description") ?? "").trim() || null,
        pain_level: Number(formData.get("pain_level") ?? 3),
        type: String(formData.get("type") ?? "other"),
        submitter_email:
            String(formData.get("submitter_email") ?? "").trim() || null,
        submitter_name:
            String(formData.get("submitter_name") ?? "").trim() || null,
        website: String(formData.get("website") ?? ""),
    };

    if (!payload.description) {
        delete payload.description;
    }
    if (!payload.submitter_email) {
        delete payload.submitter_email;
    }
    if (!payload.submitter_name) {
        delete payload.submitter_name;
    }
    if (!payload.website) {
        delete payload.website;
    }

    return payload;
}

function LandingPage({
    primaryWorkspaceSlug,
}: {
    primaryWorkspaceSlug: string | null;
}): JSX.Element {
    const [query, setQuery] = useState("");
    const [items, setItems] = useState<DemoItem[]>(
        DEMO_SEED.map((item) => ({ ...item })),
    );

    const filtered = useMemo(() => {
        const normalized = query.trim().toLowerCase();
        if (!normalized) {
            return items;
        }
        return items.filter((item) =>
            item.title.toLowerCase().includes(normalized),
        );
    }, [items, query]);

    return (
        <>
            {renderPublicHeader(primaryWorkspaceSlug)}

            <main id="main">
                <section className="sn-hero sn-content-gutter">
                    <div className="sn-hero__panel sn-stack">
                        <p className="sn-hero__eyebrow">
                            Built for product teams shipping weekly
                        </p>
                        <h1>SignalNest</h1>
                        <p className="sn-hero__tagline">
                            <em>Capture the noise. Find the signal.</em>
                        </p>
                        <p className="sn-hero__lede">
                            A feedback triage app for turning user requests,
                            bugs, and product ideas into clear next steps.
                        </p>
                        <p className="sn-hero__ctas">
                            {primaryWorkspaceSlug ? (
                                <>
                                    <a
                                        className="sn-button sn-button-primary"
                                        href={`/w/${primaryWorkspaceSlug}/dashboard`}
                                    >
                                        Go to dashboard
                                    </a>
                                    <a
                                        className="sn-button sn-button-secondary"
                                        href="#demo"
                                    >
                                        See the demo
                                    </a>
                                </>
                            ) : (
                                <>
                                    <a
                                        className="sn-button sn-button-primary"
                                        href="/signup"
                                    >
                                        Start free
                                    </a>
                                    <a
                                        className="sn-button sn-button-secondary"
                                        href="#demo"
                                    >
                                        Try the demo
                                    </a>
                                </>
                            )}
                        </p>
                        <ul className="sn-hero__metrics" role="list">
                            <li>
                                <strong>8 workflow views</strong>
                                <span>
                                    Dashboard, inbox, roadmap, changelog, and
                                    more
                                </span>
                            </li>
                            <li>
                                <strong>Typed API contracts</strong>
                                <span>
                                    React UI reads the same `/api/v1` envelope
                                    as the backend tests
                                </span>
                            </li>
                            <li>
                                <strong>Fast triage loop</strong>
                                <span>
                                    Capture, prioritize, route, and ship from
                                    one workspace shell
                                </span>
                            </li>
                        </ul>
                    </div>
                </section>

                <section
                    className="sn-section sn-content-gutter sn-stack"
                    aria-labelledby="landing-value-heading"
                >
                    <header className="sn-stack">
                        <h2 id="landing-value-heading">
                            Run feedback like an operating system
                        </h2>
                        <p className="sn-text-muted">
                            SignalNest keeps intake, triage, planning, and
                            release visibility in one focused workflow.
                        </p>
                    </header>
                    <div className="sn-grid-3">
                        <article className="sn-card sn-value-card sn-stack">
                            <h3>Capture everything</h3>
                            <p className="sn-text-muted">
                                Intake from public forms, support signals, and
                                interviews without losing source context.
                            </p>
                        </article>
                        <article className="sn-card sn-value-card sn-stack">
                            <h3>Triage with urgency</h3>
                            <p className="sn-text-muted">
                                Prioritize by pain and status so the next action
                                queue stays clear every day.
                            </p>
                        </article>
                        <article className="sn-card sn-value-card sn-stack">
                            <h3>Ship with transparency</h3>
                            <p className="sn-text-muted">
                                Move approved work to roadmap and changelog
                                views without copy-pasting between tools.
                            </p>
                        </article>
                    </div>
                </section>

                <section
                    className="sn-section sn-section--workflow sn-content-gutter sn-stack"
                    aria-labelledby="landing-workflow-heading"
                >
                    <header className="sn-stack">
                        <h2 id="landing-workflow-heading">
                            From signal to shipped, visibly
                        </h2>
                    </header>
                    <ul className="sn-workflow-strip" role="list">
                        <li>
                            <span className="sn-pill-status sn-pill-status--info">
                                Capture
                            </span>
                        </li>
                        <li aria-hidden="true">{"->"}</li>
                        <li>
                            <span className="sn-pill-status sn-pill-status--warn">
                                Triage
                            </span>
                        </li>
                        <li aria-hidden="true">{"->"}</li>
                        <li>
                            <span className="sn-pill-status sn-pill-status--ok">
                                Plan
                            </span>
                        </li>
                        <li aria-hidden="true">{"->"}</li>
                        <li>
                            <span className="sn-pill-status sn-pill-status--ok">
                                Ship
                            </span>
                        </li>
                    </ul>
                </section>

                <section
                    className="sn-section sn-content-gutter sn-stack"
                    aria-labelledby="landing-features-heading"
                >
                    <header className="sn-stack">
                        <h2 id="landing-features-heading">
                            One workspace, full feedback loop
                        </h2>
                    </header>
                    <ul className="sn-feature-grid" role="list">
                        <li>
                            Inbox queue for new, needs info, and reviewing
                            states
                        </li>
                        <li>Roadmap and changelog publishing controls</li>
                        <li>Submitter and workspace-member visibility</li>
                        <li>Insights on status distribution and pain trends</li>
                        <li>Public submission form per workspace slug</li>
                        <li>
                            Server-side auth + tenancy with typed React
                            contracts
                        </li>
                    </ul>
                </section>

                <section
                    id="demo"
                    className="sn-section sn-content-gutter sn-stack"
                    aria-labelledby="demo-heading"
                >
                    <header className="sn-stack">
                        <h2 id="demo-heading">Try it - no signup required</h2>
                        <p className="sn-text-muted">
                            Search the list, bump a status, and watch the row
                            update. Refreshing the page resets the demo.
                        </p>
                    </header>
                    <div id="landing-demo" className="sn-card sn-demo-card">
                        <div className="sn-card-body sn-stack">
                            <label
                                htmlFor="landing-demo-search"
                                className="sn-label"
                            >
                                Search
                            </label>
                            <input
                                id="landing-demo-search"
                                type="search"
                                className="sn-input"
                                placeholder="Type to filter..."
                                autoComplete="off"
                                value={query}
                                onChange={(event) => {
                                    setQuery(event.target.value);
                                }}
                            />
                            <div className="sn-table-wrap">
                                <table className="sn-table">
                                    <thead>
                                        <tr>
                                            <th scope="col">Title</th>
                                            <th scope="col">Status</th>
                                            <th scope="col">Priority</th>
                                            <th scope="col">Pain</th>
                                            <th scope="col">
                                                <span className="sr-only">
                                                    Actions
                                                </span>
                                            </th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {filtered.map((item) => {
                                            const dots =
                                                "●".repeat(item.pain) +
                                                "○".repeat(5 - item.pain);
                                            return (
                                                <tr key={item.id}>
                                                    <td>{item.title}</td>
                                                    <td>
                                                        <span
                                                            className={`sn-pill-status sn-pill-status--${DEMO_STATUS_TONE[item.status]}`}
                                                        >
                                                            {
                                                                STATUS_LABEL[
                                                                    item.status
                                                                ]
                                                            }
                                                        </span>
                                                    </td>
                                                    <td>
                                                        <span
                                                            className={`sn-pill-priority sn-pill-priority--${item.priority}`}
                                                        >
                                                            {item.priority}
                                                        </span>
                                                    </td>
                                                    <td>
                                                        <span
                                                            className="sn-pain-dots"
                                                            aria-label={`Pain ${item.pain} of 5`}
                                                        >
                                                            {dots}
                                                        </span>
                                                    </td>
                                                    <td>
                                                        <button
                                                            type="button"
                                                            className="sn-button sn-button-secondary"
                                                            onClick={() => {
                                                                setItems(
                                                                    (current) =>
                                                                        current.map(
                                                                            (
                                                                                candidate,
                                                                            ) =>
                                                                                candidate.id ===
                                                                                item.id
                                                                                    ? {
                                                                                          ...candidate,
                                                                                          status: STATUS_FORWARD[
                                                                                              candidate
                                                                                                  .status
                                                                                          ],
                                                                                      }
                                                                                    : candidate,
                                                                        ),
                                                                );
                                                            }}
                                                        >
                                                            Bump status
                                                        </button>
                                                    </td>
                                                </tr>
                                            );
                                        })}
                                    </tbody>
                                </table>
                            </div>
                            {filtered.length === 0 ? (
                                <p className="sn-text-muted">No items match.</p>
                            ) : null}
                        </div>
                    </div>
                </section>

                {renderPublicFooter()}
            </main>
        </>
    );
}

function PublicSubmitPage({
    workspaceSlug,
    workspaceName,
    clientRelease,
}: {
    workspaceSlug: string;
    workspaceName: string;
    clientRelease: string;
}): JSX.Element {
    const formRef = useRef<HTMLFormElement | null>(null);
    const [statusMessage, setStatusMessage] = useState<string | null>(null);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);
    const [submitted, setSubmitted] = useState(false);
    const [submitting, setSubmitting] = useState(false);

    async function onSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
        event.preventDefault();
        if (submitting) {
            return;
        }

        const form = event.currentTarget;
        const payload = buildSubmitPayload(new FormData(form));
        setErrorMessage(null);
        setStatusMessage("Submitting...");
        setSubmitting(true);

        try {
            await submitPublicFeedback(workspaceSlug, payload, clientRelease);
            setSubmitted(true);
            setStatusMessage(null);
        } catch (error: unknown) {
            const apiError = normalizeApiError(error);
            setStatusMessage(null);
            setErrorMessage(apiError.message);
        } finally {
            setSubmitting(false);
        }
    }

    if (!workspaceSlug) {
        return (
            <main id="main" className="sn-page-shell">
                <div className="sn-content-gutter sn-stack">
                    <section className="sn-card sn-stack">
                        <h1>Submit feedback</h1>
                        <p className="sn-text-danger">
                            Workspace context is missing for this route.
                        </p>
                    </section>
                </div>
            </main>
        );
    }

    return (
        <main id="main" className="sn-page-shell">
            <div className="sn-content-gutter sn-stack">
                <header className="sn-stack">
                    <h1>Submit feedback</h1>
                    <p className="sn-text-muted">
                        Share an idea, bug, or pain point with the{" "}
                        {workspaceName} team.
                    </p>
                </header>

                {!submitted ? (
                    <form
                        id="submit-form"
                        ref={formRef}
                        className="sn-card sn-stack"
                        noValidate
                        onSubmit={(event) => {
                            void onSubmit(event);
                        }}
                    >
                        {statusMessage ? (
                            <p
                                id="form-status"
                                className="sn-text-muted"
                                role="status"
                                aria-live="polite"
                            >
                                {statusMessage}
                            </p>
                        ) : null}

                        {errorMessage ? (
                            <p
                                id="form-error"
                                className="sn-text-danger"
                                role="alert"
                            >
                                {errorMessage}
                            </p>
                        ) : null}

                        <div className="sn-form-row">
                            <label htmlFor="f-title">Title</label>
                            <input
                                id="f-title"
                                name="title"
                                type="text"
                                required
                                maxLength={200}
                                autoComplete="off"
                            />
                        </div>

                        <div className="sn-form-row">
                            <label htmlFor="f-description">
                                Details{" "}
                                <span className="sn-text-muted">
                                    (optional)
                                </span>
                            </label>
                            <textarea
                                id="f-description"
                                name="description"
                                rows={5}
                                maxLength={5000}
                            />
                        </div>

                        <div className="sn-form-row">
                            <label htmlFor="f-pain">
                                How painful is this? (1 = minor, 5 = blocking)
                            </label>
                            <input
                                id="f-pain"
                                name="pain_level"
                                type="number"
                                min={1}
                                max={5}
                                required
                                defaultValue={3}
                            />
                        </div>

                        <fieldset className="sn-form-row">
                            <legend>Type</legend>
                            {[
                                ["bug", "Bug"],
                                ["feature_request", "Feature request"],
                                ["question", "Question"],
                                ["praise", "Praise"],
                                ["other", "Other"],
                            ].map(([value, label]) => (
                                <label className="sn-radio" key={value}>
                                    <input
                                        type="radio"
                                        name="type"
                                        value={value}
                                        defaultChecked={value === "other"}
                                    />
                                    <span>{label}</span>
                                </label>
                            ))}
                        </fieldset>

                        <div className="sn-form-row">
                            <label htmlFor="f-email">
                                Your email{" "}
                                <span className="sn-text-muted">
                                    (optional, lets us follow up)
                                </span>
                            </label>
                            <input
                                id="f-email"
                                name="submitter_email"
                                type="email"
                                maxLength={320}
                                autoComplete="email"
                            />
                        </div>

                        <div className="sn-form-row">
                            <label htmlFor="f-name">
                                Your name{" "}
                                <span className="sn-text-muted">
                                    (optional)
                                </span>
                            </label>
                            <input
                                id="f-name"
                                name="submitter_name"
                                type="text"
                                maxLength={120}
                                autoComplete="name"
                            />
                        </div>

                        <div className="sn-honeypot" aria-hidden="true">
                            <label htmlFor="f-website">
                                Leave this field empty.
                            </label>
                            <input
                                id="f-website"
                                name="website"
                                type="text"
                                tabIndex={-1}
                                autoComplete="off"
                            />
                        </div>

                        <div className="sn-form-actions">
                            <button
                                type="submit"
                                className="sn-button sn-button-primary"
                                disabled={submitting}
                            >
                                {submitting
                                    ? "Submitting..."
                                    : "Submit feedback"}
                            </button>
                        </div>
                    </form>
                ) : null}

                {submitted ? (
                    <section id="thank-you" className="sn-card sn-stack">
                        <h2>Thanks!</h2>
                        <p>
                            Your feedback was received and the team will take a
                            look.
                        </p>
                        <p>
                            <button
                                type="button"
                                id="submit-another"
                                className="sn-button sn-button-secondary"
                                onClick={() => {
                                    formRef.current?.reset();
                                    setErrorMessage(null);
                                    setStatusMessage(null);
                                    setSubmitted(false);
                                }}
                            >
                                Submit another
                            </button>
                        </p>
                    </section>
                ) : null}
            </div>
        </main>
    );
}

function PublicRoadmapPage({
    payload,
}: {
    payload: PublicRoadmapPayload;
}): JSX.Element {
    return (
        <main
            id="main"
            className="sn-page-shell"
            data-workspace-slug={payload.workspace_slug}
        >
            <div className="sn-content-gutter sn-stack">
                <header className="sn-stack">
                    <h1>{payload.workspace_name} roadmap</h1>
                    <p className="sn-text-muted">
                        What we are working on, in plain view.
                    </p>
                </header>

                {payload.is_empty ? (
                    <p className="sn-empty-state">
                        <strong>Nothing on the public roadmap yet.</strong>
                        <span>Check back soon.</span>
                    </p>
                ) : (
                    <div className="sn-roadmap-board sn-grid-12">
                        {[
                            ["planned", "Planned"],
                            ["in_progress", "In progress"],
                            ["shipped", "Recently shipped"],
                        ].map(([columnKey, title]) => {
                            const key =
                                columnKey as keyof PublicRoadmapPayload["columns"];
                            const column = payload.columns[key];
                            return (
                                <section
                                    key={columnKey}
                                    className="sn-roadmap-column"
                                    aria-labelledby={`col-${columnKey}-h`}
                                >
                                    <header className="sn-roadmap-column__header">
                                        <h2 id={`col-${columnKey}-h`}>
                                            {title}
                                        </h2>
                                        <span className="sn-count-chip">
                                            {column.length}
                                        </span>
                                    </header>
                                    {column.length > 0 ? (
                                        <ul className="sn-stack" role="list">
                                            {column.map((item) => (
                                                <li
                                                    key={item.id}
                                                    className="sn-card sn-roadmap-card"
                                                    data-id={item.id}
                                                >
                                                    <h3 className="sn-roadmap-card__title">
                                                        {item.title}
                                                    </h3>
                                                    <p className="sn-roadmap-card__meta">
                                                        <span
                                                            className="sn-pill sn-pill--type"
                                                            data-type={
                                                                item.type
                                                            }
                                                        >
                                                            {renderTypeLabel(
                                                                item.type,
                                                                item.type_other,
                                                            )}
                                                        </span>
                                                    </p>
                                                    {item.tags.length > 0 ? (
                                                        <ul
                                                            className="sn-tag-row"
                                                            role="list"
                                                        >
                                                            {item.tags.map(
                                                                (tag) => (
                                                                    <li
                                                                        key={`${item.id}-${tag.slug}-${tag.name}`}
                                                                    >
                                                                        <span
                                                                            className={`sn-tag-chip sn-tag-chip--${tag.color}`}
                                                                        >
                                                                            {
                                                                                tag.name
                                                                            }
                                                                        </span>
                                                                    </li>
                                                                ),
                                                            )}
                                                        </ul>
                                                    ) : null}
                                                </li>
                                            ))}
                                        </ul>
                                    ) : (
                                        <p className="sn-text-muted sn-roadmap-column__empty">
                                            Nothing here yet.
                                        </p>
                                    )}
                                </section>
                            );
                        })}
                    </div>
                )}
            </div>
        </main>
    );
}

function PublicChangelogPage({
    payload,
}: {
    payload: PublicChangelogPayload;
}): JSX.Element {
    return (
        <main
            id="main"
            className="sn-page-shell"
            data-workspace-slug={payload.workspace_slug}
        >
            <div className="sn-content-gutter sn-stack">
                <header className="sn-stack">
                    <h1>{payload.workspace_name} changelog</h1>
                    <p className="sn-text-muted">
                        Recent improvements, in shipping order.
                    </p>
                </header>

                {payload.entries.length > 0 ? (
                    <ol className="sn-changelog sn-stack" role="list">
                        {payload.entries.map((entry) => (
                            <li
                                key={entry.id}
                                className="sn-card sn-changelog-entry"
                                data-id={entry.id}
                            >
                                <header className="sn-changelog-entry__header">
                                    <time
                                        dateTime={entry.shipped_at_iso}
                                        className="sn-changelog-entry__date"
                                    >
                                        {entry.shipped_at_label}
                                    </time>
                                    <h2 className="sn-changelog-entry__title">
                                        {entry.title}
                                    </h2>
                                </header>
                                {entry.release_note ? (
                                    <p className="sn-changelog-entry__note">
                                        {entry.release_note}
                                    </p>
                                ) : null}
                            </li>
                        ))}
                    </ol>
                ) : (
                    <p className="sn-empty-state">
                        <strong>Nothing shipped yet.</strong>
                        <span>The first release notes will appear here.</span>
                    </p>
                )}
            </div>
        </main>
    );
}

export function PublicApp({
    pageKey,
    clientRelease,
    routePayload,
}: PublicAppProps): JSX.Element {
    switch (pageKey) {
        case "landing": {
            const payload = parseLandingPayload(routePayload);
            return (
                <LandingPage
                    primaryWorkspaceSlug={payload.primary_workspace_slug}
                />
            );
        }

        case "public_submit": {
            const payload = parseSubmitPayload(routePayload);
            return (
                <PublicSubmitPage
                    workspaceSlug={payload.workspace_slug}
                    workspaceName={payload.workspace_name}
                    clientRelease={clientRelease}
                />
            );
        }

        case "public_roadmap": {
            const payload = parseRoadmapPayload(routePayload);
            return <PublicRoadmapPage payload={payload} />;
        }

        case "public_changelog": {
            const payload = parseChangelogPayload(routePayload);
            return <PublicChangelogPage payload={payload} />;
        }

        default:
            return (
                <main id="main" className="sn-page-shell">
                    <div className="sn-content-gutter sn-stack">
                        <section className="sn-card sn-stack">
                            <h1>Unsupported page</h1>
                            <p className="sn-text-muted">
                                This public React route is not implemented.
                            </p>
                        </section>
                    </div>
                </main>
            );
    }
}
