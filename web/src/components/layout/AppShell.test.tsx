import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { AppShell } from "./AppShell";

describe("AppShell", () => {
    it("renders phase one shell primitives", () => {
        render(
            <AppShell
                workspaceSlug="demo-owner"
                workspaceName="Demo Owner"
                activeSection="dashboard"
                inboxBadge={3}
                onSignOut={vi.fn()}
            >
                <section className="sn-card">
                    <div className="sn-card-header">
                        <h2>Snapshot body</h2>
                    </div>
                    <div className="sn-card-body">
                        <p>Shared shell parity snapshot.</p>
                    </div>
                </section>
            </AppShell>,
        );

        expect(
            screen.getByRole("link", { name: "Demo Owner" }),
        ).toHaveAttribute("href", "/w/demo-owner/dashboard");
        expect(
            screen.getByText(/dashboard/i, {
                selector: ".sn-app-header__breadcrumb",
            }),
        ).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Sign out" })).toBeInTheDocument();
        expect(
            screen.getByRole("link", { name: "Saved views" }),
        ).toHaveAttribute("href", "/w/demo-owner/insights");
        expect(
            screen.getByRole("link", { name: "+ New signal" }),
        ).toHaveAttribute("href", "/w/demo-owner/feedback/new");
        expect(screen.getByText("3")).toHaveClass("sn-sidebar-badge");
    });

    it("shows workspace switcher when multiple memberships are available", () => {
        const { getByRole } = render(
            <AppShell
                workspaceSlug="demo-owner"
                workspaceName="Demo Owner"
                activeSection="dashboard"
                workspaceMemberships={[
                    {
                        workspace_id: "4677f519-0b9a-4c74-9958-f6fef70ded66",
                        workspace_slug: "demo-owner",
                        workspace_name: "Demo Owner",
                        role: "owner",
                    },
                    {
                        workspace_id: "5877f519-0b9a-4c74-9958-f6fef70ded66",
                        workspace_slug: "demo-team",
                        workspace_name: "Demo Team",
                        role: "team_member",
                    },
                ]}
                onSignOut={vi.fn()}
            >
                <section className="sn-card">
                    <div className="sn-card-header">
                        <h2>Workspace switch test</h2>
                    </div>
                    <div className="sn-card-body">
                        <p>Switcher should render.</p>
                    </div>
                </section>
            </AppShell>,
        );

        expect(
            getByRole("combobox", { name: "Switch workspace" }),
        ).toBeInTheDocument();
    });
});
