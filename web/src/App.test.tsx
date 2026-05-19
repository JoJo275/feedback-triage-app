import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { App } from "./App";

vi.mock("./hooks/useRouteContextLoader", () => ({
    useRouteContextLoader: () => ({
        state: "ready",
        data: {
            user: {
                id: "9e9a7f73-f9f4-43d7-a4fe-8aef72fcf688",
                email: "owner@example.com",
                is_verified: true,
                role: "team_member",
                theme_preference: "light",
                created_at: "2026-05-01T00:00:00.000000Z",
            },
            membership: {
                workspace_id: "4677f519-0b9a-4c74-9958-f6fef70ded66",
                workspace_slug: "demo-owner",
                workspace_name: "Demo Owner",
                role: "owner",
            },
            workspace: {
                id: "4677f519-0b9a-4c74-9958-f6fef70ded66",
                slug: "demo-owner",
                name: "Demo Owner",
                is_demo: false,
                public_submit_enabled: true,
                created_at: "2026-05-01T00:00:00.000000Z",
            },
            feedbackItems: [
                {
                    id: 101,
                    title: "Search needs keyboard shortcuts",
                    description: "Power users requested slash command support.",
                    source: "interview",
                    pain_level: 4,
                    status: "reviewing",
                    created_at: "2026-05-10T00:00:00.000000Z",
                    updated_at: "2026-05-12T00:00:00.000000Z",
                },
            ],
        },
    }),
}));

describe("App", () => {
    it("renders phase one shell primitives", () => {
        render(
            <App
                workspaceSlug="demo-owner"
                workspaceName="Demo Owner"
                activeSection="dashboard"
                pageKey="dashboard"
                legacyUrl="/w/demo-owner/dashboard?view=legacy"
                clientRelease="react-test"
            />,
        );

        expect(
            screen.getByRole("heading", {
                name: "Dashboard",
            }),
        ).toBeInTheDocument();
        expect(screen.getByText("Route context loaded")).toBeInTheDocument();
        expect(
            screen.getByRole("heading", { name: "Recent feedback" }),
        ).toBeInTheDocument();
        expect(
            screen.getByRole("link", {
                name: "Search needs keyboard shortcuts",
            }),
        ).toBeInTheDocument();
    });
});
