import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiClientError, apiRequest } from "./apiClient";

function jsonResponse(
    payload: unknown,
    status = 200,
    headers: HeadersInit = {},
): Response {
    return new Response(JSON.stringify(payload), {
        status,
        headers: {
            "Content-Type": "application/json",
            ...headers,
        },
    });
}

describe("apiRequest", () => {
    const fetchMock = vi.fn();

    beforeEach(() => {
        fetchMock.mockReset();
        vi.stubGlobal("fetch", fetchMock as unknown as typeof fetch);
    });

    it("sends credentials and workspace/release headers", async () => {
        fetchMock.mockResolvedValueOnce(jsonResponse({ ok: true }));

        const payload = await apiRequest<{ ok: boolean }>("/api/v1/example", {
            workspaceSlug: "demo-owner",
            clientRelease: "react-test",
        });

        expect(payload).toEqual({ ok: true });
        expect(fetchMock).toHaveBeenCalledTimes(1);

        const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
        const headers = init.headers as Headers;

        expect(init.credentials).toBe("same-origin");
        expect(headers.get("Accept")).toBe("application/json");
        expect(headers.get("X-Workspace-Slug")).toBe("demo-owner");
        expect(headers.get("x-client-release")).toBe("react-test");
    });

    it("returns null for 204 responses", async () => {
        fetchMock.mockResolvedValueOnce(new Response(null, { status: 204 }));

        const payload = await apiRequest<null>("/api/v1/auth/logout", {
            method: "POST",
        });

        expect(payload).toBeNull();
    });

    it("throws ApiClientError for normalized API failures", async () => {
        fetchMock.mockResolvedValueOnce(
            jsonResponse(
                {
                    error: {
                        code: "rate_limited",
                        message: "Slow down.",
                        details: { retry_after_seconds: 60 },
                    },
                },
                429,
                { "x-request-id": "req-429" },
            ),
        );

        try {
            await apiRequest("/api/v1/feedback");
            throw new Error("Expected apiRequest to throw");
        } catch (error) {
            expect(error).toBeInstanceOf(ApiClientError);
            const apiError = error as ApiClientError;
            expect(apiError.status).toBe(429);
            expect(apiError.code).toBe("rate_limited");
            expect(apiError.message).toBe("Slow down.");
            expect(apiError.requestId).toBe("req-429");
        }
    });
});
