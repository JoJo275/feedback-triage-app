export type ReactShellProps = {
    workspaceSlug: string;
    workspaceName: string;
    dashboardUrl: string;
};

export function App({
    workspaceSlug,
    workspaceName,
    dashboardUrl,
}: ReactShellProps): JSX.Element {
    return (
        <main className="sn-react-shell" aria-labelledby="react-shell-heading">
            <header className="sn-react-shell__header">
                <h1 id="react-shell-heading">React dashboard shell</h1>
                <p>
                    Workspace <strong>{workspaceName}</strong> (
                    <code>{workspaceSlug}</code>) is served by a Vite-built
                    React bundle from <code>/static/app/</code>.
                </p>
            </header>
            <section
                className="sn-react-shell__card"
                aria-label="Phase 0 status"
            >
                <h2>Phase 0 foundation ready</h2>
                <ul>
                    <li>Bundle is loaded through FastAPI manifest lookup.</li>
                    <li>This page is behind auth and tenant scoping.</li>
                    <li>
                        Legacy dashboard remains the default production route.
                    </li>
                </ul>
                <p>
                    <a href={dashboardUrl}>Back to the classic dashboard</a>
                </p>
            </section>
        </main>
    );
}
