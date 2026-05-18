import type {
    FeedbackListEnvelope,
    MeResponse,
    WorkspaceDto,
} from "../types/contracts";
import { normalizeApiError, type NormalizedApiError } from "./errorNormalizer";

const DEFAULT_CLIENT_RELEASE = "react-phase1-shell";

export interface ApiRequestOptions {
    method?: "GET" | "POST" | "PATCH" | "PUT" | "DELETE";
    body?: unknown;
    headers?: HeadersInit;
    workspaceSlug?: string;
    clientRelease?: string;
    signal?: AbortSignal;
}

export class ApiClientError extends Error {
    readonly status: number;
    readonly code: string;
    readonly details?: unknown;
    readonly requestId?: string;

    constructor(normalized: NormalizedApiError) {
        super(normalized.message);
        this.name = "ApiClientError";
        this.status = normalized.status;
        this.code = normalized.code;
        this.details = normalized.details;
        this.requestId = normalized.requestId;
    }
}

function buildHeaders(options: ApiRequestOptions): Headers {
    const headers = new Headers(options.headers);

    if (!headers.has("Accept")) {
        headers.set("Accept", "application/json");
    }

    if (options.body !== undefined && !headers.has("Content-Type")) {
        headers.set("Content-Type", "application/json");
    }

    if (options.workspaceSlug) {
        headers.set("X-Workspace-Slug", options.workspaceSlug);
    }

    headers.set(
        "x-client-release",
        options.clientRelease ?? DEFAULT_CLIENT_RELEASE,
    );

    return headers;
}

async function readPayload(response: Response): Promise<unknown> {
    if (response.status === 204) {
        return null;
    }

    const raw = await response.text();
    if (raw.length === 0) {
        return null;
    }

    try {
        return JSON.parse(raw) as unknown;
    } catch {
        return raw;
    }
}

export async function apiRequest<T>(
    path: string,
    options: ApiRequestOptions = {},
): Promise<T> {
    const response = await fetch(path, {
        method: options.method ?? "GET",
        credentials: "same-origin",
        headers: buildHeaders(options),
        body:
            options.body === undefined
                ? undefined
                : JSON.stringify(options.body),
        signal: options.signal,
    });

    const payload = await readPayload(response);

    if (!response.ok) {
        throw new ApiClientError(
            normalizeApiError({
                status: response.status,
                payload,
                requestId: response.headers.get("x-request-id"),
            }),
        );
    }

    return payload as T;
}

export function getAuthMe(
    clientRelease: string,
    signal?: AbortSignal,
): Promise<MeResponse> {
    return apiRequest<MeResponse>("/api/v1/auth/me", {
        clientRelease,
        signal,
    });
}

export function getWorkspaceBySlug(
    slug: string,
    clientRelease: string,
    signal?: AbortSignal,
): Promise<WorkspaceDto> {
    return apiRequest<WorkspaceDto>(
        `/api/v1/workspaces/${encodeURIComponent(slug)}`,
        {
            clientRelease,
            signal,
        },
    );
}

export function listFeedbackPreview(
    workspaceSlug: string,
    clientRelease: string,
    signal?: AbortSignal,
): Promise<FeedbackListEnvelope> {
    const params = new URLSearchParams({
        skip: "0",
        limit: "8",
        sort_by: "-created_at",
    });

    return apiRequest<FeedbackListEnvelope>(
        `/api/v1/feedback?${params.toString()}`,
        {
            workspaceSlug,
            clientRelease,
            signal,
        },
    );
}
