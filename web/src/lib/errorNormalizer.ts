export interface NormalizedApiError {
    status: number;
    code: string;
    message: string;
    details?: unknown;
    requestId?: string;
}

export interface NormalizeApiErrorInput {
    status: number;
    payload: unknown;
    requestId?: string | null;
    fallbackMessage?: string;
}

const STATUS_CODE_FALLBACK: Record<number, string> = {
    400: "bad_request",
    401: "auth_required",
    403: "forbidden",
    404: "not_found",
    409: "conflict",
    410: "gone",
    413: "payload_too_large",
    422: "validation_error",
    429: "rate_limited",
    500: "internal_error",
    503: "service_unavailable",
};

const STATUS_MESSAGE_FALLBACK: Record<number, string> = {
    400: "Request was invalid.",
    401: "Authentication is required.",
    403: "You do not have access to this resource.",
    404: "Resource was not found.",
    409: "Request conflicts with the current state.",
    410: "Requested resource is no longer available.",
    413: "Request payload is too large.",
    422: "Request validation failed.",
    429: "Too many requests. Please try again shortly.",
    500: "Something went wrong. Please try again.",
    503: "Service is temporarily unavailable.",
};

function isRecord(value: unknown): value is Record<string, unknown> {
    return typeof value === "object" && value !== null;
}

function readString(value: unknown): string | null {
    return typeof value === "string" && value.trim().length > 0 ? value : null;
}

function fallbackCode(status: number): string {
    return STATUS_CODE_FALLBACK[status] ?? "request_failed";
}

function fallbackMessage(status: number, explicit: string | undefined): string {
    return (
        explicit ??
        STATUS_MESSAGE_FALLBACK[status] ??
        `Request failed (${status}).`
    );
}

function humanizeValidationList(value: unknown[]): string {
    const parts = value
        .map((entry) => {
            if (!isRecord(entry)) {
                return "";
            }

            const msg = readString(entry.msg) ?? "Validation error";
            const locRaw = entry.loc;
            if (!Array.isArray(locRaw)) {
                return msg;
            }

            const loc = locRaw
                .filter((segment) => typeof segment === "string")
                .filter((segment) => segment !== "body")
                .join(".");

            return loc.length > 0 ? `${loc}: ${msg}` : msg;
        })
        .filter((piece) => piece.length > 0);

    if (parts.length > 0) {
        return parts.join("; ");
    }

    return "Request validation failed.";
}

function normalizeFromLegacyDetail(
    status: number,
    detail: unknown,
): Omit<NormalizedApiError, "status" | "requestId"> {
    if (typeof detail === "string") {
        return {
            code: fallbackCode(status),
            message: detail,
        };
    }

    if (Array.isArray(detail)) {
        return {
            code: "validation_error",
            message: humanizeValidationList(detail),
            details: detail,
        };
    }

    if (isRecord(detail)) {
        const code = readString(detail.code);
        const message = readString(detail.message);

        if (code && message) {
            return {
                code,
                message,
                details: detail.details,
            };
        }

        const serialized = JSON.stringify(detail);
        return {
            code: fallbackCode(status),
            message: serialized,
            details: detail,
        };
    }

    return {
        code: fallbackCode(status),
        message: fallbackMessage(status, undefined),
    };
}

export function normalizeApiError(
    input: NormalizeApiErrorInput,
): NormalizedApiError {
    const { status, payload, fallbackMessage: customFallback } = input;

    let code = fallbackCode(status);
    let message = fallbackMessage(status, customFallback);
    let details: unknown;
    let requestId = readString(input.requestId ?? undefined) ?? undefined;

    if (isRecord(payload)) {
        const payloadRequestId = readString(payload.request_id);
        if (payloadRequestId) {
            requestId = payloadRequestId;
        }

        const modernError = payload.error;
        if (isRecord(modernError)) {
            code = readString(modernError.code) ?? code;
            message = readString(modernError.message) ?? message;
            details = modernError.details;
        } else if (Object.prototype.hasOwnProperty.call(payload, "detail")) {
            const normalized = normalizeFromLegacyDetail(
                status,
                payload.detail,
            );
            code = normalized.code;
            message = normalized.message;
            details = normalized.details;
        }
    } else if (typeof payload === "string" && payload.trim().length > 0) {
        message = payload;
    }

    return {
        status,
        code,
        message,
        details,
        requestId,
    };
}
