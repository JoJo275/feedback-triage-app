import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { PublicApp } from "./PublicApp";
import { submitPublicFeedback } from "./lib/apiClient";

vi.mock("./lib/apiClient", async () => {
    const actual =
        await vi.importActual<typeof import("./lib/apiClient")>(
            "./lib/apiClient",
        );
    return {
        ...actual,
        submitPublicFeedback: vi.fn(),
    };
});

describe("PublicApp", () => {
    it("renders roadmap payload rows", () => {
        render(
            <PublicApp
                pageKey="public_roadmap"
                legacyUrl="/w/demo-owner/roadmap/public?view=legacy"
                clientRelease="react-test"
                routePayload={{
                    workspace_slug: "demo-owner",
                    workspace_name: "Demo Owner",
                    is_empty: false,
                    columns: {
                        planned: [],
                        in_progress: [],
                        shipped: [
                            {
                                id: 7,
                                title: "Roadmap visible row",
                                type: "feature_request",
                                type_other: null,
                                tags: [],
                            },
                        ],
                    },
                }}
            />,
        );

        expect(
            screen.getByRole("heading", { name: "Demo Owner roadmap" }),
        ).toBeInTheDocument();
        expect(screen.getByText("Roadmap visible row")).toBeInTheDocument();
        expect(
            screen.getByRole("link", { name: "Open classic page" }),
        ).toBeInTheDocument();
    });

    it("submits public feedback and shows thank-you state", async () => {
        vi.mocked(submitPublicFeedback).mockResolvedValue({
            status: "accepted",
            id: 101,
        });

        render(
            <PublicApp
                pageKey="public_submit"
                legacyUrl="/w/demo-owner/submit?view=legacy"
                clientRelease="react-test"
                routePayload={{
                    workspace_slug: "demo-owner",
                    workspace_name: "Demo Owner",
                }}
            />,
        );

        fireEvent.change(screen.getByLabelText("Title"), {
            target: { value: "React public submit test" },
        });
        fireEvent.click(
            screen.getByRole("button", { name: "Submit feedback" }),
        );

        await waitFor(() => {
            expect(submitPublicFeedback).toHaveBeenCalled();
        });

        expect(
            screen.getByRole("heading", {
                name: "Thanks!",
            }),
        ).toBeInTheDocument();
    });
});
