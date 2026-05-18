import type { ReactNode } from "react";

interface CardProps {
    title: string;
    description?: string;
    actions?: ReactNode;
    children: ReactNode;
    className?: string;
}

function joinClassNames(...parts: Array<string | undefined>): string {
    return parts.filter((part): part is string => Boolean(part)).join(" ");
}

export function Card({
    title,
    description,
    actions,
    children,
    className,
}: CardProps): JSX.Element {
    return (
        <section className={joinClassNames("sn-card", className)}>
            <header className="sn-card-header">
                <div>
                    <h2>{title}</h2>
                    {description ? (
                        <p className="sn-text-muted">{description}</p>
                    ) : null}
                </div>
                {actions ? <div>{actions}</div> : null}
            </header>
            <div className="sn-card-body sn-stack">{children}</div>
        </section>
    );
}
