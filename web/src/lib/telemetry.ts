export type FrontendTelemetryEvent =
    | "api_failure"
    | "mutation_failure"
    | "window_error"
    | "unhandled_rejection";

export interface FrontendTelemetryPayload {
    event: FrontendTelemetryEvent;
    route: string;
    client_release: string;
    path?: string;
    method?: string;
    status_code?: number;
    code?: string;
    request_id?: string;
    message?: string;
}

const FRONTEND_TELEMETRY_ENDPOINT = "/api/v1/frontend-events";

export function emitFrontendTelemetry(payload: FrontendTelemetryPayload): void {
    const body = JSON.stringify(payload);

    if (typeof navigator !== "undefined" && "sendBeacon" in navigator) {
        try {
            const blob = new Blob([body], { type: "application/json" });
            if (navigator.sendBeacon(FRONTEND_TELEMETRY_ENDPOINT, blob)) {
                return;
            }
        } catch {
            // Fallback to fetch below.
        }
    }

    try {
        const pending = fetch(FRONTEND_TELEMETRY_ENDPOINT, {
            method: "POST",
            credentials: "same-origin",
            headers: { "Content-Type": "application/json" },
            body,
            keepalive: true,
        });
        void Promise.resolve(pending).catch(() => {
            // Telemetry must never break user flows.
        });
    } catch {
        // Telemetry must never break user flows.
    }
}
