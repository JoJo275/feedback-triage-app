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
});
