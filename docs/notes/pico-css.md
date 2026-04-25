# Pico CSS

## What is Pico CSS?

[Pico CSS](https://picocss.com/) is a **minimal, classless CSS framework**
that provides a clean default styling for semantic HTML elements — without
requiring you to add CSS classes to your markup.

## Key characteristics

| Aspect | Detail |
|--------|--------|
| **Philosophy** | Style semantic HTML directly (`<article>`, `<nav>`, `<table>`) instead of adding utility classes |
| **Size** | ~10 KB minified + gzipped (vs ~23 KB for Bootstrap) |
| **Classes** | Mostly classless — elements get styled by their HTML tag name |
| **Dark mode** | Built-in via `[data-theme="dark"]` attribute on `<html>` |
| **Customisation** | CSS custom properties (variables) for colors, fonts, spacing |
| **Grid** | Simple `.grid` class for column layouts, otherwise relies on native CSS |
| **Components** | Covers forms, tables, buttons, cards, modals, progress bars, tooltips |
| **JavaScript** | None — pure CSS with no JS dependencies |
| **Build step** | None required — single CSS file, CDN, or npm package |

## How it differs from other frameworks

### vs Bootstrap / Tailwind

- **Bootstrap** gives you a large library of pre-built components
  (`btn btn-primary`, `card`, `modal`) that require specific class names
  and often JS plugins. Heavy and opinionated about structure.
- **Tailwind** is a utility-first framework where you compose styles inline
  (`class="flex items-center p-4 bg-blue-500"`). Requires a build step
  (PostCSS/JIT compiler). Very flexible but verbose markup.
- **Pico** sits in between: no classes needed for basic styling, but much
  less pre-built than Bootstrap. It's "write semantic HTML and it looks
  good" rather than "compose classes to build a design."

### vs Classless frameworks (Water.css, MVP.css, new.css)

Pico is in the **classless family** but larger and more feature-rich than
pure classless micro-frameworks. It adds a few optional classes
(`.grid`, `.container`, `role="button"`) for layout while keeping the
classless core philosophy.

## How this project uses Pico CSS

The environment dashboard (`tools/dev_tools/env_dashboard/`) uses Pico as
the **base styling layer**:

1. **Pico provides the foundation** — default element styles for tables,
   forms, buttons, inputs, details/summary, articles, etc.
2. **Custom CSS extends it** — `static/css/style.css` (~1600+ lines) adds
   dashboard-specific components: sidebar, topbar, section cards, terminal
   panel, accent themes, and responsive layout.
3. **CSS variables bridge the two** — Pico's variables are extended with
   dashboard-specific ones (`--color-accent`, `--sidebar-width`, etc.)!

The practical effect: most HTML in the Jinja2 templates uses **semantic
elements** (`<table>`, `<article>`, `<details>`) and gets reasonable
styling for free from Pico. Custom classes are added only for
dashboard-specific layout and behavior.

## Is it like choosing a "pre-set library"?

**Yes, partially.** Pico is a pre-set of default styles and conventions:

- It decides what `<button>`, `<table>`, `<input>`, etc. look like
- It provides a color system via CSS variables
- It includes dark mode support out of the box
- It has opinions about spacing, typography, and border radius

But unlike Bootstrap, it doesn't impose a component model or require
specific HTML structures. You write standard HTML and Pico makes it look
presentable.

**Think of it as:** semantic HTML → Pico adds "good defaults" → your custom
CSS adds "specific design."

## Resources

- Official site: <https://picocss.com/>
- GitHub: <https://github.com/picocss/pico>
- Docs: <https://picocss.com/docs>
- Class-light components: <https://picocss.com/docs/classless>
