import { useEffect, useRef } from "react";
import type { ReactNode } from "react";

interface ModalProps {
    id: string;
    title: string;
    open: boolean;
    onClose: () => void;
    children: ReactNode;
}

export function Modal({
    id,
    title,
    open,
    onClose,
    children,
}: ModalProps): JSX.Element {
    const dialogRef = useRef<HTMLDialogElement | null>(null);
    const titleId = `${id}-title`;

    useEffect(() => {
        const dialog = dialogRef.current;
        if (!dialog) {
            return;
        }

        if (open && !dialog.open) {
            dialog.showModal();
            return;
        }

        if (!open && dialog.open) {
            dialog.close();
        }
    }, [open]);

    useEffect(() => {
        const dialog = dialogRef.current;
        if (!dialog) {
            return;
        }

        const handleClose = (): void => {
            onClose();
        };

        dialog.addEventListener("close", handleClose);
        return () => {
            dialog.removeEventListener("close", handleClose);
        };
    }, [onClose]);

    return (
        <dialog ref={dialogRef} className="sn-modal" aria-labelledby={titleId}>
            <article className="sn-card sn-stack">
                <header className="sn-card-header">
                    <h3 id={titleId}>{title}</h3>
                </header>
                <div className="sn-card-body sn-stack">
                    {children}
                    <div>
                        <button
                            type="button"
                            className="sn-button sn-button-secondary"
                            onClick={() => {
                                dialogRef.current?.close();
                            }}
                        >
                            Close
                        </button>
                    </div>
                </div>
            </article>
        </dialog>
    );
}
