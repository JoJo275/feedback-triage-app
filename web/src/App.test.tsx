import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { App } from "./App";

vi.mock("./hooks/useRouteContextLoader", () => ({
    useRouteContextLoader: (() => {
        const readyState = {
            state: "ready" as const,
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
                        description:
                            "Power users requested slash command support.",
                        source: "interview",
                        pain_level: 4,
                        status: "reviewing",
                        created_at: "2026-05-10T00:00:00.000000Z",
                        updated_at: "2026-05-12T00:00:00.000000Z",
                    },
                ],
                dashboardSummary: {
                    counts: {
                        total_signals: 25,
                        needs_action: 4,
                        high_pain_signals: 2,
                    },
                    intake_30d: [
                        { day: "2026-03-20", received: 0 },
                        { day: "2026-03-21", received: 1 },
                        { day: "2026-03-22", received: 1 },
                        { day: "2026-03-23", received: 2 },
                    ],
                    total_signals_widget: {
                        widget_id: "kpi-total-signals",
                        label: "Total signals",
                        value: 25,
                        delta_pct: -50,
                        delta_direction: "down",
                        comparison_label: "vs Mar 20 - Apr 18",
                        sparkline_points: [0, 1, 1, 2],
                        sparkline_date_labels: [
                            "Mar 20",
                            "Mar 21",
                            "Mar 22",
                            "Mar 23",
                        ],
                    },
                },
            },
        };

        return () => readyState;
    })(),
}));

describe("App", () => {
    it("renders phase one shell primitives", () => {
        render(
            <App
                workspaceSlug="demo-owner"
                workspaceName="Demo Owner"
                activeSection="dashboard"
                pageKey="dashboard"
                clientRelease="react-test"
            />,
        );

        expect(
            screen.getByRole("heading", {
                name: "Dashboard",
            }),
        ).toBeInTheDocument();
        expect(screen.getByText("Total signals")).toBeInTheDocument();
        expect(screen.getByText("Largest increase")).toBeInTheDocument();
        expect(screen.getByText("Second-largest increase")).toBeInTheDocument();
        expect(
            screen.getByRole("link", {
                name: /total signals/i,
            }),
        ).toHaveAttribute("href", "/w/demo-owner/feedback");
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
