import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { TotalSignalsWidget } from "./TotalSignalsWidget";

const widget = {
    widget_id: "kpi-total-signals" as const,
    label: "Total signals" as const,
    value: 25,
    delta_pct: -50,
    delta_direction: "down" as const,
    comparison_label: "vs Mar 20 - Apr 18",
    sparkline_points: [0, 1, 1, 2],
    sparkline_date_labels: ["Mar 20", "Mar 21", "Mar 22", "Mar 23"],
};

describe("TotalSignalsWidget", () => {
    it("renders stable widget contract and routes to feedback", () => {
        render(
            <TotalSignalsWidget workspaceSlug="demo-owner" widget={widget} />,
        );

        const container = document.querySelector(
            '[data-widget-id="kpi-total-signals"]',
        );
        expect(container).not.toBeNull();

        expect(screen.getByText("Total signals")).toBeInTheDocument();
        expect(screen.getByText("Largest increase")).toBeInTheDocument();
        expect(screen.getByText("Second-largest increase")).toBeInTheDocument();

        expect(
            screen.getByRole("link", {
                name: /total signals/i,
            }),
        ).toHaveAttribute("href", "/w/demo-owner/feedback");

        expect(
            screen.getByLabelText(/total signals trend vs mar 20 - apr 18/i),
        ).toBeInTheDocument();
    });
});
