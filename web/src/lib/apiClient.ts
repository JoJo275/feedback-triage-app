import type {
    FeedbackListEnvelope,
    FeedbackItemDto,
    MemberListResponse,
    MeResponse,
    SubmitterListEnvelope,
    WorkspaceDto,
} from "../types/contracts";
import { normalizeApiError, type NormalizedApiError } from "./errorNormalizer";
import { emitFrontendTelemetry } from "./telemetry";

const DEFAULT_CLIENT_RELEASE = "react-phase2-auth-pages";

export interface ApiRequestOptions {
    method?: "GET" | "POST" | "PATCH" | "PUT" | "DELETE";
    body?: unknown;
    headers?: HeadersInit;
    workspaceSlug?: string;
    clientRelease?: string;
    signal?: AbortSignal;
}

export interface FeedbackListQuery {
    skip?: number;
    limit?: number;
    sortBy?: string;
    status?: string;
    q?: string;
    publishedToRoadmap?: boolean;
    publishedToChangelog?: boolean;
    stale?: boolean;
}

export interface FeedbackPatchRequest {
    status?: string;
    title?: string;
    description?: string | null;
    release_note?: string | null;
    published_to_roadmap?: boolean;
    published_to_changelog?: boolean;
}

export interface WorkspacePatchRequest {
    name?: string;
    public_submit_enabled?: boolean;
}

export interface PublicFeedbackSubmitRequest {
    title: string;
    description?: string | null;
    source?: string;
    source_other?: string | null;
    pain_level: number;
    type: string;
    type_other?: string | null;
    submitter_email?: string | null;
    submitter_name?: string | null;
    website?: string;
}

export interface PublicFeedbackSubmitResponse {
    status: string;
    id?: number;
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

function currentRoute(): string {
    if (typeof window === "undefined") {
        return "unknown";
    }
    return window.location.pathname;
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
    const method = options.method ?? "GET";
    const clientRelease = options.clientRelease ?? DEFAULT_CLIENT_RELEASE;
    let response: Response;
    try {
        response = await fetch(path, {
            method,
            credentials: "same-origin",
            headers: buildHeaders(options),
            body:
                options.body === undefined
                    ? undefined
                    : JSON.stringify(options.body),
            signal: options.signal,
        });
    } catch (error) {
        const networkMessage =
            error instanceof Error ? error.message : "Network request failed.";
        const normalized: NormalizedApiError = {
            status: 0,
            code: "network_error",
            message: networkMessage,
        };
        emitFrontendTelemetry({
            event: method === "GET" ? "api_failure" : "mutation_failure",
            route: currentRoute(),
            client_release: clientRelease,
            path,
            method,
            status_code: normalized.status,
            code: normalized.code,
            message: normalized.message,
        });
        throw new ApiClientError(normalized);
    }

    const payload = await readPayload(response);

    if (!response.ok) {
        const normalized = normalizeApiError({
            status: response.status,
            payload,
            requestId: response.headers.get("x-request-id"),
        });
        emitFrontendTelemetry({
            event: method === "GET" ? "api_failure" : "mutation_failure",
            route: currentRoute(),
            client_release: clientRelease,
            path,
            method,
            status_code: normalized.status,
            code: normalized.code,
            request_id: normalized.requestId,
            message: normalized.message,
        });
        throw new ApiClientError(normalized);
    }

    return payload as T;
}

function buildFeedbackQuery(query: FeedbackListQuery): string {
    const params = new URLSearchParams();

    if (query.skip !== undefined) {
        params.set("skip", String(query.skip));
    }
    if (query.limit !== undefined) {
        params.set("limit", String(query.limit));
    }
    if (query.sortBy) {
        params.set("sort_by", query.sortBy);
    }
    if (query.status) {
        params.set("status", query.status);
    }
    if (query.q) {
        params.set("q", query.q);
    }
    if (query.publishedToRoadmap !== undefined) {
        params.set("published_to_roadmap", String(query.publishedToRoadmap));
    }
    if (query.publishedToChangelog !== undefined) {
        params.set(
            "published_to_changelog",
            String(query.publishedToChangelog),
        );
    }
    if (query.stale !== undefined) {
        params.set("stale", String(query.stale));
    }

    return params.toString();
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
    limit = 8,
    signal?: AbortSignal,
): Promise<FeedbackListEnvelope> {
    return listFeedback(
        workspaceSlug,
        clientRelease,
        {
            skip: 0,
            limit,
            sortBy: "-created_at",
        },
        signal,
    );
}

export function listFeedback(
    workspaceSlug: string,
    clientRelease: string,
    query: FeedbackListQuery = {},
    signal?: AbortSignal,
): Promise<FeedbackListEnvelope> {
    const queryString = buildFeedbackQuery(query);
    const path =
        queryString.length > 0
            ? `/api/v1/feedback?${queryString}`
            : "/api/v1/feedback";

    return apiRequest<FeedbackListEnvelope>(path, {
        workspaceSlug,
        clientRelease,
        signal,
    });
}

export function patchFeedback(
    workspaceSlug: string,
    itemId: number,
    payload: FeedbackPatchRequest,
    clientRelease: string,
    signal?: AbortSignal,
): Promise<FeedbackItemDto> {
    return apiRequest<FeedbackItemDto>(`/api/v1/feedback/${itemId}`, {
        method: "PATCH",
        workspaceSlug,
        clientRelease,
        body: payload,
        signal,
    });
}

export function listSubmitters(
    workspaceSlug: string,
    clientRelease: string,
    signal?: AbortSignal,
): Promise<SubmitterListEnvelope> {
    return apiRequest<SubmitterListEnvelope>(
        "/api/v1/submitters?skip=0&limit=100",
        {
            workspaceSlug,
            clientRelease,
            signal,
        },
    );
}

export function listWorkspaceMembers(
    slug: string,
    clientRelease: string,
    signal?: AbortSignal,
): Promise<MemberListResponse> {
    return apiRequest<MemberListResponse>(
        `/api/v1/workspaces/${encodeURIComponent(slug)}/members`,
        {
            clientRelease,
            signal,
        },
    );
}

export function patchWorkspace(
    slug: string,
    payload: WorkspacePatchRequest,
    clientRelease: string,
    signal?: AbortSignal,
): Promise<WorkspaceDto> {
    return apiRequest<WorkspaceDto>(
        `/api/v1/workspaces/${encodeURIComponent(slug)}`,
        {
            method: "PATCH",
            clientRelease,
            body: payload,
            signal,
        },
    );
}

export function submitPublicFeedback(
    slug: string,
    payload: PublicFeedbackSubmitRequest,
    clientRelease: string,
    signal?: AbortSignal,
): Promise<PublicFeedbackSubmitResponse> {
    return apiRequest<PublicFeedbackSubmitResponse>(
        `/api/v1/public/feedback/${encodeURIComponent(slug)}`,
        {
            method: "POST",
            body: payload,
            clientRelease,
            signal,
        },
    );
}
