import { render } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { AppShell } from "./AppShell";

describe("AppShell", () => {
    it("matches the authenticated shell snapshot", () => {
        const { container } = render(
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

        expect(container.firstChild).toMatchSnapshot();
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
