import { useEffect, useState } from "react";

import {
    ApiClientError,
    getDashboardSummary,
    getAuthMe,
    getWorkspaceBySlug,
    listFeedbackPreview,
} from "../lib/apiClient";
import type {
    DashboardSummaryDto,
    FeedbackItemDto,
    MembershipDto,
    UserDto,
    WorkspaceDto,
} from "../types/contracts";

export interface RouteContextData {
    user: UserDto;
    memberships: MembershipDto[];
    membership: MembershipDto;
    workspace: WorkspaceDto;
    feedbackItems: FeedbackItemDto[];
    dashboardSummary: DashboardSummaryDto | null;
}

export type RouteContextState =
    | { state: "loading" }
    | { state: "error"; error: ApiClientError }
    | { state: "ready"; data: RouteContextData };

export interface RouteContextLoaderInput {
    workspaceSlug: string;
    workspaceNameHint: string;
    clientRelease: string;
    feedbackPreviewLimit?: number;
    includeDashboardSummary?: boolean;
}

function toApiClientError(error: unknown): ApiClientError {
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
        message: "Unable to load route context.",
    });
}

export function useRouteContextLoader(
    input: RouteContextLoaderInput,
): RouteContextState {
    const [state, setState] = useState<RouteContextState>({ state: "loading" });
    const {
        workspaceSlug,
        workspaceNameHint,
        clientRelease,
        feedbackPreviewLimit = 8,
        includeDashboardSummary = false,
    } = input;

    useEffect(() => {
        if (!workspaceSlug.trim()) {
            setState({
                state: "error",
                error: new ApiClientError({
                    status: 400,
                    code: "bad_request",
                    message: "Workspace slug is required for this route.",
                }),
            });
            return;
        }

        const abortController = new AbortController();
        setState({ state: "loading" });

        void (async () => {
            try {
                const dashboardSummaryPromise = includeDashboardSummary
                    ? getDashboardSummary(
                          workspaceSlug,
                          clientRelease,
                          abortController.signal,
                      )
                    : Promise.resolve(null);

                const [me, workspace, feedback, dashboardSummary] =
                    await Promise.all([
                        getAuthMe(clientRelease, abortController.signal),
                        getWorkspaceBySlug(
                            workspaceSlug,
                            clientRelease,
                            abortController.signal,
                        ),
                        listFeedbackPreview(
                            workspaceSlug,
                            clientRelease,
                            feedbackPreviewLimit,
                            abortController.signal,
                        ),
                        dashboardSummaryPromise,
                    ]);

                const membership = me.memberships.find(
                    (item) => item.workspace_slug === workspaceSlug,
                );

                if (!membership) {
                    throw new ApiClientError({
                        status: 404,
                        code: "workspace_not_found",
                        message: `Signed-in user is not a member of ${workspaceNameHint}.`,
                        details: { workspace_slug: workspaceSlug },
                    });
                }

                setState({
                    state: "ready",
                    data: {
                        user: me.user,
                        memberships: me.memberships,
                        membership,
                        workspace,
                        feedbackItems: feedback.items,
                        dashboardSummary,
                    },
                });
            } catch (error) {
                if (abortController.signal.aborted) {
                    return;
                }

                setState({
                    state: "error",
                    error: toApiClientError(error),
                });
            }
        })();

        return () => {
            abortController.abort();
        };
    }, [
        workspaceSlug,
        workspaceNameHint,
        clientRelease,
        feedbackPreviewLimit,
        includeDashboardSummary,
    ]);

    return state;
}
