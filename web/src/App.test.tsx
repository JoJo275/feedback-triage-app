import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { App } from "./App";

describe("App", () => {
    it("renders phase zero readiness text", () => {
        render(
            <App
                workspaceSlug="demo-owner"
                workspaceName="Demo Owner"
                dashboardUrl="/w/demo-owner/dashboard"
            />,
        );

        expect(
            screen.getByRole("heading", { name: "React dashboard shell" }),
        ).toBeInTheDocument();
        expect(
            screen.getByText("Phase 0 foundation ready"),
        ).toBeInTheDocument();
        expect(
            screen.getByRole("link", { name: "Back to the classic dashboard" }),
        ).toHaveAttribute("href", "/w/demo-owner/dashboard");
    });
});
