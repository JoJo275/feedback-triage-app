import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { App, type AppPageKey } from "./App";
import { PublicApp, type PublicPageKey } from "./PublicApp";
import type { AppSection } from "./components/layout/AppShell";
import "./styles.css";

const APP_SECTIONS: AppSection[] = [
    "dashboard",
    "inbox",
    "feedback",
    "submitters",
    "roadmap",
    "changelog",
    "insights",
    "settings",
];

const AUTH_PAGE_KEYS: AppPageKey[] = [
    "dashboard",
    "inbox",
    "feedback",
    "roadmap",
    "changelog",
    "submitters",
    "insights",
    "settings",
];

const PUBLIC_PAGE_KEYS: PublicPageKey[] = [
    "landing",
    "public_submit",
    "public_roadmap",
    "public_changelog",
];

type RoutePageKey = AppPageKey | PublicPageKey;

function parseSection(raw: string): AppSection {
    return APP_SECTIONS.includes(raw as AppSection)
        ? (raw as AppSection)
        : "dashboard";
}

function parsePageKey(raw: string): RoutePageKey {
    if (AUTH_PAGE_KEYS.includes(raw as AppPageKey)) {
        return raw as AppPageKey;
    }
    if (PUBLIC_PAGE_KEYS.includes(raw as PublicPageKey)) {
        return raw as PublicPageKey;
    }
    return "dashboard";
}

function isAuthenticatedPageKey(pageKey: RoutePageKey): pageKey is AppPageKey {
    return AUTH_PAGE_KEYS.includes(pageKey as AppPageKey);
}

function parseRoutePayload(): unknown {
    const node = document.getElementById("sn-react-route-payload");
    if (!node) {
        return null;
    }

    const raw = node.textContent ?? "";
    if (!raw.trim()) {
        return null;
    }

    try {
        return JSON.parse(raw) as unknown;
    } catch {
        return null;
    }
}

function defaultLegacyUrl(
    pageKey: RoutePageKey,
    workspaceSlug: string,
): string {
    switch (pageKey) {
        case "landing":
            return "/";
        case "public_submit":
            return `/w/${workspaceSlug}/submit`;
        case "public_roadmap":
            return `/w/${workspaceSlug}/roadmap/public`;
        case "public_changelog":
            return `/w/${workspaceSlug}/changelog/public`;
        default:
            return `/w/${workspaceSlug}/${pageKey}`;
    }
}

const mountNode = document.getElementById("sn-react-app-root");

if (!mountNode) {
    throw new Error("Missing #sn-react-app-root mount node");
}

const workspaceSlug = mountNode.dataset.workspaceSlug ?? "unknown";
const workspaceName = mountNode.dataset.workspaceName ?? "Unknown workspace";
const activeSection = parseSection(
    mountNode.dataset.activeSection ?? "dashboard",
);
const pageKey = parsePageKey(mountNode.dataset.pageKey ?? activeSection);
const legacyUrl =
    mountNode.dataset.legacyUrl ?? defaultLegacyUrl(pageKey, workspaceSlug);
const clientRelease =
    mountNode.dataset.clientRelease ?? "react-phase3-public-pages";
const routePayload = parseRoutePayload();

createRoot(mountNode).render(
    <StrictMode>
        {isAuthenticatedPageKey(pageKey) ? (
            <App
                workspaceSlug={workspaceSlug}
                workspaceName={workspaceName}
                activeSection={activeSection}
                pageKey={pageKey}
                legacyUrl={legacyUrl}
                clientRelease={clientRelease}
            />
        ) : (
            <PublicApp
                pageKey={pageKey}
                legacyUrl={legacyUrl}
                clientRelease={clientRelease}
                routePayload={routePayload}
            />
        )}
    </StrictMode>,
);
