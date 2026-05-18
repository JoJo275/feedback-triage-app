import type { ReactNode } from "react";

export interface DataTableColumn<T> {
    key: string;
    header: string;
    cellClassName?: string;
    render: (row: T) => ReactNode;
}

interface DataTableProps<T> {
    caption: string;
    columns: DataTableColumn<T>[];
    rows: T[];
    getRowKey: (row: T) => string | number;
    emptyMessage: string;
}

export function DataTable<T>({
    caption,
    columns,
    rows,
    getRowKey,
    emptyMessage,
}: DataTableProps<T>): JSX.Element {
    return (
        <div className="sn-table-wrap">
            <table className="sn-table">
                <caption className="sr-only">{caption}</caption>
                <thead>
                    <tr>
                        {columns.map((column) => (
                            <th key={column.key} scope="col">
                                {column.header}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {rows.length > 0 ? (
                        rows.map((row) => (
                            <tr key={getRowKey(row)}>
                                {columns.map((column) => (
                                    <td
                                        key={column.key}
                                        className={column.cellClassName}
                                    >
                                        {column.render(row)}
                                    </td>
                                ))}
                            </tr>
                        ))
                    ) : (
                        <tr>
                            <td colSpan={columns.length}>{emptyMessage}</td>
                        </tr>
                    )}
                </tbody>
            </table>
        </div>
    );
}
