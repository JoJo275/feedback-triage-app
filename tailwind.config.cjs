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
    /**
     * PR 4.5 chrome classes that templates have not yet adopted.
     * Without these here Tailwind would drop the rules during purge.
     * Remove a pattern once the matching template lands.
     */
    safelist: [
        { pattern: /^sn-app-shell(__\w+)?$/ },
        { pattern: /^sn-app-header(__\w+)?$/ },
        { pattern: /^sn-page-header(__\w+)?$/ },
        { pattern: /^sn-summary-(row|card)(__\w+)?(--\w+)?$/ },
        { pattern: /^sn-work-row$/ },
        { pattern: /^sn-attention-panel(__\w+)?$/ },
        { pattern: /^sn-drawer(-rail|-backdrop)?(__\w+)?$/ },
        { pattern: /^sn-pill-status--(info|warn|ok|muted|danger)$/ },
        { pattern: /^sn-pill-priority--(low|medium|high|critical)$/ },
        { pattern: /^sn-fx-hover-lift$/ },
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
