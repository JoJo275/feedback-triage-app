import type { ReactNode } from "react";

import type { MembershipDto } from "../../types/contracts";

export type AppSection =
    | "dashboard"
    | "inbox"
    | "feedback"
    | "submitters"
    | "roadmap"
    | "changelog"
    | "insights"
    | "settings";

interface AppShellProps {
    workspaceSlug: string;
    workspaceName: string;
    activeSection: AppSection;
    workspaceMemberships?: MembershipDto[];
    inboxBadge?: number;
    children: ReactNode;
    onSignOut: () => Promise<void> | void;
}

interface NavLink {
    key: AppSection;
    label: string;
}

const NAV_LINKS: NavLink[] = [
    { key: "dashboard", label: "Dashboard" },
    { key: "inbox", label: "Inbox" },
    { key: "feedback", label: "Feedback" },
    { key: "submitters", label: "Submitters" },
    { key: "roadmap", label: "Roadmap" },
    { key: "changelog", label: "Changelog" },
    { key: "insights", label: "Insights" },
    { key: "settings", label: "Settings" },
];

export function AppShell({
    workspaceSlug,
    workspaceName,
    activeSection,
    workspaceMemberships,
    inboxBadge,
    children,
    onSignOut,
}: AppShellProps): JSX.Element {
    const dashboardUrl = `/w/${workspaceSlug}/dashboard`;
    const feedbackUrl = `/w/${workspaceSlug}/feedback`;
    const activeSectionLabel =
        NAV_LINKS.find((link) => link.key === activeSection)?.label ??
        "Dashboard";
    const workspaceOptions = workspaceMemberships ?? [];
    const showWorkspaceSwitcher = workspaceOptions.length > 1;

    return (
        <div className="sn-app-shell">
            <aside className="sn-sidebar" aria-label="Workspace navigation">
                <a
                    className="sn-sidebar__brand"
                    href={dashboardUrl}
                    aria-label="SignalNest dashboard home"
                >
                    <span
                        className="sn-sidebar__brand-mark"
                        aria-hidden="true"
                    />
                    <span className="sn-sidebar__brand-label">SignalNest</span>
                </a>

                <a
                    className="sn-sidebar__create"
                    href={`/w/${workspaceSlug}/feedback/new`}
                    title="New feedback"
                >
                    <span aria-hidden="true">+</span>
                    <span>New feedback</span>
                </a>

                <nav className="sn-sidebar-nav" aria-label="Sections">
                    <ul role="list">
                        {NAV_LINKS.map((link) => {
                            const href = `/w/${workspaceSlug}/${link.key}`;
                            const isCurrent = link.key === activeSection;
                            const showBadge =
                                link.key === "inbox" &&
                                typeof inboxBadge === "number" &&
                                inboxBadge > 0;

                            return (
                                <li key={link.key}>
                                    <a
                                        href={href}
                                        aria-current={
                                            isCurrent ? "page" : undefined
                                        }
                                        title={link.label}
                                    >
                                        <span>{link.label}</span>
                                        {showBadge ? (
                                            <span
                                                className="sn-sidebar-badge"
                                                aria-label={`${inboxBadge} pending`}
                                            >
                                                {inboxBadge}
                                            </span>
                                        ) : null}
                                    </a>
                                </li>
                            );
                        })}
                    </ul>
                </nav>

                <div className="sn-sidebar-footer">
                    <button
                        type="button"
                        id="theme-switcher"
                        className="sn-theme-switcher"
                        aria-label="Toggle color theme"
                        aria-pressed="false"
                    >
                        Theme
                    </button>
                    <a
                        className="sn-button sn-button-ghost"
                        href="/"
                        title="Back to home"
                    >
                        Home
                    </a>
                    <button
                        type="button"
                        id="sn-signout"
                        className="sn-button sn-button-ghost"
                        title="Sign out"
                        onClick={() => {
                            void onSignOut();
                        }}
                    >
                        Sign out
                    </button>
                </div>
            </aside>

            <main id="main" className="sn-page-shell">
                <header
                    className="sn-app-header"
                    aria-label={`${activeSectionLabel} controls`}
                >
                    <p className="sn-app-header__breadcrumb">
                        <a href={dashboardUrl}>{workspaceName}</a>
                        {" . "}
                        {activeSectionLabel}
                    </p>
                    <form
                        className="sn-app-header__search"
                        role="search"
                        action={feedbackUrl}
                        method="get"
                    >
                        <label
                            className="sr-only"
                            htmlFor="react-dashboard-search"
                        >
                            Search feedback
                        </label>
                        <input
                            id="react-dashboard-search"
                            className="sn-input sn-dashboard-search"
                            name="q"
                            type="search"
                            placeholder="Search signals..."
                        />
                    </form>
                    <div className="sn-app-header__actions">
                        {showWorkspaceSwitcher ? (
                            <div className="sn-react-workspace-switcher">
                                <label
                                    className="sr-only"
                                    htmlFor="sn-workspace-switcher"
                                >
                                    Switch workspace
                                </label>
                                <select
                                    id="sn-workspace-switcher"
                                    className="sn-input"
                                    value={workspaceSlug}
                                    aria-label="Switch workspace"
                                    onChange={(event) => {
                                        const nextWorkspaceSlug =
                                            event.target.value;
                                        if (
                                            !nextWorkspaceSlug ||
                                            nextWorkspaceSlug === workspaceSlug
                                        ) {
                                            return;
                                        }
                                        window.location.assign(
                                            `/w/${nextWorkspaceSlug}/dashboard`,
                                        );
                                    }}
                                >
                                    {workspaceOptions.map((membership) => (
                                        <option
                                            key={membership.workspace_slug}
                                            value={membership.workspace_slug}
                                        >
                                            {membership.workspace_name}
                                        </option>
                                    ))}
                                </select>
                            </div>
                        ) : null}
                        <a
                            className="sn-button sn-button-secondary"
                            href={`/w/${workspaceSlug}/insights`}
                        >
                            Saved views
                        </a>
                        <a
                            className="sn-button sn-button-primary"
                            href={`/w/${workspaceSlug}/feedback/new`}
                        >
                            + New signal
                        </a>
                    </div>
                </header>

                <div className="sn-content-gutter sn-stack">{children}</div>

                <footer className="sn-content-gutter sn-react-shell-footer">
                    <p className="sn-text-muted">
                        Phase 1 React shell canary route. APIs and auth cookies
                        are served by FastAPI.
                    </p>
                </footer>
            </main>
        </div>
    );
}
