import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { App } from "./App";
import "./styles.css";

const mountNode = document.getElementById("sn-react-app-root");

if (!mountNode) {
    throw new Error("Missing #sn-react-app-root mount node");
}

const workspaceSlug = mountNode.dataset.workspaceSlug ?? "unknown";
const workspaceName = mountNode.dataset.workspaceName ?? "Unknown workspace";
const dashboardUrl =
    mountNode.dataset.dashboardUrl ?? `/w/${workspaceSlug}/dashboard`;
const clientRelease = mountNode.dataset.clientRelease ?? "react-phase1-shell";

createRoot(mountNode).render(
    <StrictMode>
        <App
            workspaceSlug={workspaceSlug}
            workspaceName={workspaceName}
            dashboardUrl={dashboardUrl}
            clientRelease={clientRelease}
        />
    </StrictMode>,
);
