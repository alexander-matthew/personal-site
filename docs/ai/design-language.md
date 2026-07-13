# Design Language: "Gravure"

The site's visual identity, v2. Replaces the "Palantir" dark-dashboard look while
keeping its CSS-variable architecture. Inspired by paper-design shaders (halftone,
dither, dot-grid effects) and editorial poster layouts: enormous high-contrast serif
display type on near-black, with imagery rendered through a **halftone/dither process**
in an ice-blue duotone. Named after photogravure — the printing process that turned
classical art into dot patterns.

**The one-line brief:** a printed art poster that happens to be a live web page.
Black paper, white ink, ice-blue plates.

---

## 1. Palette

Three colors only — black, white, light blue — plus greys derived from them.
Everything cool-toned (blue-tinted, never warm).

| Token | Value | Role |
|---|---|---|
| `--ink` / `--bg-primary` | `#060709` | Page background. Near-black, cool. |
| `--bg-surface` | `#0c0f14` | Raised surfaces (cards, nav scrim). |
| `--bg-elevated` | `#12161d` | Dialogs, hover fills. |
| `--paper` | `#f2f6fb` | The "white ink". Headline + primary emphasis color. |
| `--ice` | `#a9d2ff` | Pale blue. Halftone highlight plate, gradient words, large tinted fields. |
| `--accent` | `#4da6ff` | Signal blue. Links, interactive states, focus rings. (Unchanged from v1 — mini-apps inherit.) |
| `--accent-hover` | `#7fc0ff` | Link/button hover. |
| `--accent-glow` | `rgba(77,166,255,0.15)` | Glows, selection washes. |
| `--text-primary` | `#e8eef6` | Body text (brighter than v1 — this is a poster, not a dashboard). |
| `--text-secondary` | `#93a0b0` | Supporting text. |
| `--text-muted` | `#55606e` | Captions, disabled. |
| `--border-subtle` | `#161b23` | Hairlines. |
| `--border-default` | `#232b37` | Component borders. |
| `--border-bright` | `#334050` | Hover borders. |
| `--duotone-deep` | `#0d1b2e` | Halftone shadow plate (blue-black). |

Semantic colors (`--color-success/warning/error`) keep their v1 values — apps only.

**Rules:** No purples, no warm greys, no gradients except `--paper → --ice` on display
type. Large flat black fields are a feature — don't fill space with panels.

## 2. Typography

Three faces, three jobs:

| Token | Face | Job |
|---|---|---|
| `--font-display` | `'Bodoni Moda'` (Google Fonts, variable opsz/wght, italic too) | Display only: hero name, page titles, section numerals, pull quotes. Never body text. |
| `--font-sans` | `'Inter'` | Body copy, nav, buttons, forms. |
| `--font-mono` | `'JetBrains Mono'` | Eyebrow labels, captions, data, code, and all mini-app internals (games/dashboards stay terminal-flavored). |

Google Fonts `<link>` must include: `Bodoni+Moda:ital,opsz,wght@0,6..96,400..800;1,6..96,400..800`,
plus the existing Inter and JetBrains Mono sets.

**Display type treatment (the signature look):**
- Page titles: `font-family: var(--font-display); font-weight: 450–550;`
  `font-size: clamp(48px, 9vw, 128px);` `line-height: 0.95; letter-spacing: -0.01em;`
  color `--paper`. Home hero goes bigger: `clamp(64px, 14vw, 200px)`.
- Optional accent: one word (or trailing letters) in the ice gradient:
  `.display-ice { background: linear-gradient(180deg, var(--paper), var(--ice) 70%); -webkit-background-clip: text; background-clip: text; color: transparent; }`
- Display type may overlap/underlap halftone canvases (see §4). Text must remain
  real selectable text, not baked into canvas.

**Eyebrow labels** (replaces v1 `.sidebar-label` energy — used above every section):
`.eyebrow { font-family: var(--font-mono); font-size: 11px; letter-spacing: 0.25em; text-transform: uppercase; color: var(--text-muted); }`
An eyebrow + huge serif heading is the standard section opener sitewide.

Body: Inter 15px/1.65, `--text-primary`. Max measure `65ch`.

## 3. Layout & chrome

**The sidebar is gone.** Global chrome becomes a slim editorial top bar:

- `.topnav` — sticky, full-width, `height: 64px`, background `rgba(6,7,9,0.85)` +
  `backdrop-filter: blur(12px)`, bottom border `--border-subtle`. Contents:
  - Left: wordmark `Alexander` — `--font-display`, italic, 22px, `--paper`.
  - Center/right: nav links in Inter 13px, `--text-secondary`, hover `--paper`,
    active `--paper` with a 2px `--accent` underline offset 6px. Links: About,
    Projects, Blog, Resume, News, Diary. (Apps live on /projects — no dropdown.)
  - Far right: one pill button (`.btn-pill`) linking to GitHub.
- Mobile (<768px): links collapse behind the existing hamburger pattern into a
  full-screen black overlay menu — nav links set in display serif, 32px, stacked.
  Reuse the `#hamburger` / overlay JS hooks in `palantir.js` (update selectors).
- `main` content: single column, `max-width: 1100px`, generous vertical rhythm
  (`--space-2xl` between sections). No default page panel/border — pages are
  posters, not consoles. `.page-container` loses its box styling and becomes a
  plain width-constrained column; `page_title` renders as eyebrow-less display serif.
- Footer (new, all pages, in base template): two small captions at opposite corners,
  mono 11px `--text-muted` — left: `© {{ year }} Alexander`, right: GitHub / LinkedIn
  links. Mirrors the reference's corner-caption device.

**Buttons:** `.btn-pill` — `border-radius: 999px; padding: 10px 22px;` Inter 13px
medium. Default: `--paper` background, `--ink` text; inverts on hover (transparent
bg, `--paper` border+text). Ghost variant: 1px `--border-default` border, transparent,
text `--text-primary`, hover border `--accent`. Radius elsewhere: 2px max — the pill
is the only round thing (that contrast is deliberate).

**Focus:** all interactive elements get `outline: 2px solid var(--accent); outline-offset: 3px`
on `:focus-visible`.

## 4. The halftone engine (signature element)

`app/static/js/halftone.js` — a zero-dependency vanilla renderer that mimics the
paper-shaders dither/halftone family. One class:

```js
Halftone.mount(canvas, {
  source,            // (ctx2d, w, h, t) => void  — draws greyscale scene each frame
                     //  OR an HTMLImageElement (static)
  cell: 6,           // px per halftone cell (device-independent)
  style: 'dot',      // 'dot' (round dots, radius ∝ luminance)
                     //  | 'bayer' (4x4 ordered dither, square pixels — the "dust" look)
  plates: { shadow: '#0d1b2e', mid: '#4da6ff', light: '#a9d2ff', paper: '#f2f6fb' },
                     // luminance buckets darkest→lightest; background transparent
  fps: 30,           // animated sources only
  animate: true,     // false = render one frame (also forced by prefers-reduced-motion)
})
```

Implementation notes:
- Render `source` to an offscreen canvas at `1/cell` scale, read pixels once per
  frame via `getImageData`, then stamp dots/pixels on the visible canvas. This is
  fast enough at cell≥5 without WebGL.
- Luminance → plate color + dot radius (0 → nothing, 1 → 0.62*cell radius, slight
  per-cell deterministic jitter (hash of x,y) so grids don't moiré).
- `IntersectionObserver` pauses offscreen canvases; `prefers-reduced-motion` renders
  a single static frame; `resize` re-rasterizes (debounced).
- Expose procedural sources on `Halftone.sources`: `orb` (the v1 icosahedron
  wireframe redrawn filled/shaded so it dithers like a sphere with facets),
  `waves` (layered sine bands), `columns` (vertical fluted-glass gradient bands).

**Where it appears** (restraint: max one animated halftone per page):
- Home hero: full-bleed `orb` behind the giant name (dot style, cell 7).
- Page headers (about/projects/blog/resume/news): a short banner strip (~180px)
  with a *static* `waves` or `columns` render — quiet, no animation.
- 404: full-screen static `bayer` noise field.

## 5. Component vocabulary

- **Section opener:** eyebrow + display heading, then content. Sections separated
  by whitespace alone (no rules) — except tabular/list content which may use
  `--border-subtle` hairlines between rows.
- **Project/feed rows** (home, projects): borderless rows, title in display serif
  28px, description Inter `--text-secondary`, tags as mono 10px uppercase tokens
  separated by `·` (no pill backgrounds). Hover: title turns `--accent`, row
  indents 8px (200ms ease).
- **Cards** (only where a grid is truly needed): `--bg-surface`, 1px `--border-subtle`,
  radius 2px, no shadow. Hover: border `--border-bright`.
- **Tags:** inline mono text, `--text-muted`, no backgrounds.
- **Tabs, dialogs, forms:** keep v1 structure/classes, restyled by the new tokens;
  dialogs get radius 2px and a 1px `--border-default`.
- **Tables/data (mini-apps):** unchanged structurally; they inherit tokens.

## 6. Motion

- One orchestrated page-load moment on home only: name fades up (0.3s delay),
  halftone orb fades in (0.8s), corner captions last (1.4s). Elsewhere: content
  loads static; feed rows keep the existing IntersectionObserver reveal.
- Hover micro-interactions ≤200ms. No parallax, no scroll-jacking.
- `@media (prefers-reduced-motion: reduce)`: all animation off, halftones static.

## 7. Mini-apps (blackjack, sudoku, weather, spotify, tools, deckard)

They keep their layouts and mono-terminal character — they read as "plates" inside
the poster site. Work needed is an audit, not a redesign: replace any hardcoded
hex colors with tokens, ensure headings use the new page-title pattern (display
serif), buttons adopt `.btn-pill` or ghost style, and remove borders/glows that
fight the flat-poster look.

## 8. Quality floor

- Responsive to 360px. Test 360 / 768 / 1280.
- Contrast: body text ≥ 7:1, secondary ≥ 4.5:1 on `--ink` (the values above pass).
- Keyboard: visible focus everywhere, hamburger operable, dialogs trap focus as in v1.
- No external requests beyond Google Fonts (CSP). No new npm deps, no build step.
- Every page must render acceptably with JS disabled (canvases are decoration only).
