# How to Edit Web UI Elements Yourself

A practical beginner's guide to customizing the environment dashboard's
appearance without asking Copilot every time. All visual changes happen in
**3 files** — learn which one to edit and how to see your changes live.

---

## The 3 Files That Control Appearance

| What you want to change | File to edit | Language |
| ----------------------- | ------------ | -------- |
| **Colors, spacing, fonts, borders, sizes, animations** | `tools/dev_tools/env_dashboard/static/css/style.css` | CSS |
| **Page structure, layout, what appears where** | `tools/dev_tools/env_dashboard/templates/base.html` (nav, footer) or `templates/index.html` (main content) | HTML + Jinja2 |
| **Interactive behavior** (toggles, clicks, dynamic state) | The `<script>` block in `templates/base.html` | JavaScript (Alpine.js) |

**Rule of thumb:**
- It *looks* wrong → edit CSS
- It's *in the wrong place* or *missing* → edit HTML
- It *doesn't do the right thing* when clicked → edit JavaScript

---

## How to See Changes Live

1. Start the dashboard: `hatch run dashboard:serve`
2. Open `http://127.0.0.1:8000` in your browser
3. Edit a file and save it
4. Uvicorn auto-reloads (for Python/template changes). For CSS/JS, just
   refresh the browser (Ctrl+R or Cmd+R). Sometimes you need a hard
   refresh (Ctrl+Shift+R) to bypass the browser cache.

---

## CSS Basics — Changing How Things Look

CSS (Cascading Style Sheets) controls all visual styling. Every CSS rule
has a **selector** (what to target) and **properties** (what to change):

```css
/* selector { property: value; } */
.summary-bar {
    background: #1a1a2e;     /* background color */
    border: 1px solid #333;  /* border around element */
    border-radius: 8px;      /* rounded corners */
    padding: 1rem;           /* inner spacing */
    margin-bottom: 1.5rem;   /* outer spacing below */
}
```

### Common CSS Properties You'll Use

| Property | What it does | Example |
| -------- | ------------ | ------- |
| `color` | Text color | `color: #e0e0e0;` |
| `background` | Background color/gradient | `background: #1a1a2e;` |
| `border` | Border line | `border: 2px solid #a855f7;` |
| `border-radius` | Rounded corners | `border-radius: 12px;` |
| `padding` | Space inside element | `padding: 1rem;` |
| `margin` | Space outside element | `margin: 0 auto;` (centers horizontally) |
| `font-size` | Text size | `font-size: 0.9rem;` |
| `font-weight` | Bold/normal | `font-weight: 600;` (semi-bold) |
| `width` / `max-width` | Element width | `max-width: 1400px;` |
| `display` | Layout mode | `display: flex;` or `display: grid;` |
| `gap` | Spacing between flex/grid items | `gap: 1rem;` |
| `opacity` | Transparency (0=invisible, 1=solid) | `opacity: 0.8;` |
| `box-shadow` | Shadow effect | `box-shadow: 0 2px 8px rgba(0,0,0,0.3);` |
| `transition` | Animate changes | `transition: all 0.3s ease;` |

### CSS Selectors (Targeting Elements)

| Selector | Targets | Example in our CSS |
| -------- | ------- | ------------------ |
| `.class` | Elements with that class | `.summary-bar` |
| `#id` | Element with that ID | `#summary-bar` |
| `element` | All elements of that type | `nav`, `footer` |
| `.parent .child` | Child inside parent | `.section-card header` |
| `:hover` | When mouse is over | `.section-card:hover` |
| `::before` / `::after` | Pseudo-elements | `.badge::before` |

### CSS Variables (Our Custom Properties)

Our stylesheet uses CSS variables defined in `:root` at the top of
`style.css`. Change these to affect the whole dashboard at once:

```css
:root {
    --color-pass: #22c55e;    /* green */
    --color-warn: #f59e0b;    /* amber */
    --color-fail: #ef4444;    /* red */
    --color-accent: #a855f7;  /* purple — used for highlights */
}
```

Changing `--color-accent` from `#6366f1` to `#a855f7` changes every element
that uses `var(--color-accent)` — borders, hovers, spinners, etc.

---

## How to Use Browser DevTools

**This is the most important skill for UI editing.** DevTools lets you
inspect any element, see its CSS, and **experiment live** before editing
the actual files.

### Opening DevTools

- **Chrome/Edge:** Right-click any element → "Inspect" (or F12)
- **Firefox:** Right-click → "Inspect Element" (or F12)

### The Process

1. **Right-click the element** you want to change → "Inspect"
2. DevTools opens with that element highlighted in the HTML tree
3. On the right panel, you see all CSS rules applied to it
4. **Click any CSS value** and type a new one — the page updates instantly
5. **Experiment** until it looks right
6. Copy the property/value into `style.css` and save

### DevTools Tips

- **Toggle properties** by clicking the checkbox next to them
- **Add new properties** by clicking in empty space in a rule block
- **Find which file** a style comes from — look at the filename next to each rule
  (e.g., `style.css:45` means line 45 of style.css)
- **Color picker** — click any color swatch to open a visual color picker
- **Box model** — the bottom of the Computed tab shows padding/border/margin
  as a visual diagram
- **Changes are temporary** — refreshing the page resets everything.
  Always save changes to the actual CSS file.

---

## Layout: Flexbox and Grid

The two main CSS layout systems used in our dashboard:

### Flexbox (One Direction)

```css
.summary-bar {
    display: flex;        /* items flow in a row */
    flex-wrap: wrap;      /* wrap to next line if needed */
    gap: 1rem;            /* space between items */
    align-items: center;  /* vertically center items */
    justify-content: space-between;  /* spread items out */
}
```

### CSS Grid (Two Dimensions)

```css
.sections-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
    /* auto-fill: as many columns as fit
       minmax(340px, 1fr): each column is at least 340px, grows evenly */
    gap: 1rem;
}
```

---

## Quick Recipes

### Change a Color

1. Open DevTools, inspect the element
2. Find the `color` or `background` property
3. Click the color swatch → use the picker
4. Copy the hex code (e.g., `#a855f7`) into `style.css`

### Add a Border or Glow

```css
.section-card {
    border: 1px solid #a855f7;                        /* solid purple border */
    box-shadow: 0 0 10px rgba(168, 85, 247, 0.3);    /* purple glow */
}
```

### Make Something Bigger/Smaller

Change `padding` (inner space), `margin` (outer space), `font-size`,
or `width`/`max-width`.

### Add an Animation

```css
.section-card {
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.section-card:hover {
    transform: translateY(-2px);     /* lift up slightly */
    box-shadow: 0 4px 16px rgba(168, 85, 247, 0.4);  /* stronger glow */
}
```

### Hide Something

```css
.element-to-hide { display: none; }
```

---

## When to Use HTML vs CSS

| Goal | Approach |
| ---- | -------- |
| Move element to a different position **on the page** | Edit HTML (cut/paste the element) |
| Change the **order/alignment** without moving HTML | CSS: `order`, `flex-direction`, `justify-content` |
| Add a **new section** or element | Edit HTML (add the element), then CSS for styling |
| Change **colors, fonts, spacing** | CSS only |
| Make something **respond to clicks** | JavaScript (Alpine.js `@click`) |

---

## Reference Links

- **CSS reference:** https://developer.mozilla.org/en-US/docs/Web/CSS
- **Flexbox guide:** https://css-tricks.com/snippets/css/a-guide-to-flexbox/
- **Grid guide:** https://css-tricks.com/snippets/css/complete-guide-grid/
- **PicoCSS docs:** https://picocss.com/docs
- **DevTools tutorial:** https://developer.chrome.com/docs/devtools/
