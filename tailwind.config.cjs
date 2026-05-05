/**
 * Tailwind config for feedback-triage-app v2.0.
 *
 * Source of truth: docs/project/spec/v2/css.md.
 * Pipeline ADR: docs/adr/058-tailwind-via-standalone-cli.md.
 *
 * Tokens are CSS custom properties declared in
 * src/feedback_triage/static/css/tokens.css. Tailwind palette names
 * resolve to var(--color-*) at runtime so [data-theme] swaps work
 * without rebuilding the CSS.
 *
 * @type {import('tailwindcss').Config}
 */
module.exports = {
    darkMode: "selector",
    content: [
        "./src/feedback_triage/templates/**/*.html",
        "./src/feedback_triage/static/**/*.html",
        "./src/feedback_triage/static/js/**/*.js",
        "./src/feedback_triage/routes/**/*.py",
    ],
    theme: {
        extend: {
            colors: {
                bg: "var(--color-bg)",
                surface: "var(--color-surface)",
                "surface-alt": "var(--color-surface-alt)",
                ink: "var(--color-text)",
                "ink-muted": "var(--color-text-muted)",
                brand: "var(--color-primary)",
                "brand-hover": "var(--color-primary-hover)",
                warn: "var(--color-warning)",
                danger: "var(--color-danger)",
                line: "var(--color-border)",
            },
            borderRadius: {
                sm: "var(--radius-sm)",
                md: "var(--radius-md)",
                lg: "var(--radius-lg)",
            },
            boxShadow: {
                sm: "var(--shadow-sm)",
            },
            fontFamily: {
                sans: [
                    "-apple-system",
                    "BlinkMacSystemFont",
                    '"Segoe UI"',
                    "Roboto",
                    '"Helvetica Neue"',
                    "Arial",
                    '"Noto Sans"',
                    "sans-serif",
                    '"Apple Color Emoji"',
                    '"Segoe UI Emoji"',
                ],
                mono: [
                    "ui-monospace",
                    "SFMono-Regular",
                    "Menlo",
                    "Consolas",
                    '"Liberation Mono"',
                    "monospace",
                ],
            },
        },
    },
    plugins: [],
};
