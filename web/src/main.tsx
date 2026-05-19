import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { App, type AppPageKey } from "./App";
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

const APP_PAGE_KEYS: AppPageKey[] = [
    "dashboard",
    "inbox",
    "feedback",
    "roadmap",
    "changelog",
    "submitters",
    "insights",
    "settings",
];

function parseSection(raw: string): AppSection {
    return APP_SECTIONS.includes(raw as AppSection)
        ? (raw as AppSection)
        : "dashboard";
}

function parsePageKey(raw: string): AppPageKey {
    return APP_PAGE_KEYS.includes(raw as AppPageKey)
        ? (raw as AppPageKey)
        : "dashboard";
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
    mountNode.dataset.legacyUrl ?? `/w/${workspaceSlug}/${pageKey}`;
const clientRelease =
    mountNode.dataset.clientRelease ?? "react-phase2-auth-pages";

createRoot(mountNode).render(
    <StrictMode>
        <App
            workspaceSlug={workspaceSlug}
            workspaceName={workspaceName}
            activeSection={activeSection}
            pageKey={pageKey}
            legacyUrl={legacyUrl}
            clientRelease={clientRelease}
        />
    </StrictMode>,
);
