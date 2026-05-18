import { describe, expect, it } from "vitest";

import { normalizeApiError } from "./errorNormalizer";

describe("normalizeApiError", () => {
    it("normalizes the spec-style error envelope", () => {
        const normalized = normalizeApiError({
            status: 429,
            payload: {
                error: {
                    code: "rate_limited",
                    message: "Slow down.",
                    details: { retry_after_seconds: 60 },
                },
            },
            requestId: "req-123",
        });

        expect(normalized.status).toBe(429);
        expect(normalized.code).toBe("rate_limited");
        expect(normalized.message).toBe("Slow down.");
        expect(normalized.details).toEqual({ retry_after_seconds: 60 });
        expect(normalized.requestId).toBe("req-123");
    });

    it("normalizes legacy detail string payloads", () => {
        const normalized = normalizeApiError({
            status: 404,
            payload: {
                detail: "Not found.",
                request_id: "req-legacy",
            },
        });

        expect(normalized.code).toBe("not_found");
        expect(normalized.message).toBe("Not found.");
        expect(normalized.requestId).toBe("req-legacy");
    });

    it("formats pydantic-style validation lists", () => {
        const normalized = normalizeApiError({
            status: 422,
            payload: {
                detail: [
                    {
                        loc: ["body", "title"],
                        msg: "Field required",
                        type: "missing",
                    },
                    {
                        loc: ["body", "pain_level"],
                        msg: "Input should be less than or equal to 5",
                        type: "less_than_equal",
                    },
                ],
            },
        });

        expect(normalized.code).toBe("validation_error");
        expect(normalized.message).toContain("title: Field required");
        expect(normalized.message).toContain(
            "pain_level: Input should be less than or equal to 5",
        );
    });

    it("falls back when payload is plain text", () => {
        const normalized = normalizeApiError({
            status: 500,
            payload: "gateway timeout",
        });

        expect(normalized.code).toBe("internal_error");
        expect(normalized.message).toBe("gateway timeout");
    });
});
