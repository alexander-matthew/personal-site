---
name: palantir-theme
description: Reference for the Palantir dark theme design system used across the site
---

# Palantir Theme Design System

## Color Palette

### Backgrounds
- `--bg-primary: #0a0a0f` - Page background
- `--bg-surface: #141419` - Cards, sidebar, panels
- `--bg-elevated: #1a1a22` - Elevated elements (buttons, inputs)

### Borders
- `--border-subtle: #1e1e2e` - Dividers, separators
- `--border-default: #2a2a3a` - Card borders, inputs
- `--border-bright: #3a3a4a` - Hover states

### Accent
- `--accent: #4da6ff` - Primary accent (links, active states)
- `--accent-hover: #6ab8ff` - Hover state
- `--accent-glow: rgba(77,166,255,0.15)` - Background glow

### Text
- `--text-primary: #e0e0e0` - Body text
- `--text-secondary: #888` - Labels, descriptions
- `--text-muted: #555` - Disabled, hints

### Semantic
- `--color-success: #4ade80` - Green
- `--color-warning: #fbbf24` - Yellow
- `--color-error: #f87171` - Red

## Typography

- **Primary**: JetBrains Mono (Google Fonts) for all UI
- **Fallback**: Inter for long prose if needed
- **Base size**: 15px
- Sizes: `--font-size-xs` (11px), `--font-size-sm` (13px), base (15px), `--font-size-lg` (18px), `--font-size-xl` (24px)

## Component Patterns

### Panel (Card)
```html
<div class="panel">
    <div class="panel-header">Title</div>
    <p>Content</p>
</div>
```
Add `.panel-accent` for left accent border.

### Buttons
```html
<button class="btn">Default</button>
<button class="btn btn-primary">Primary</button>
<button class="btn btn-ghost">Ghost</button>
```

### Tabs
```html
<div class="tabs">
    <button class="tab-btn active">Tab 1</button>
    <button class="tab-btn">Tab 2</button>
</div>
<div>
    <div class="tab-panel active">Content 1</div>
    <div class="tab-panel">Content 2</div>
</div>
```

### Tags
```html
<span class="tag">Python</span>
```

### Project Card
```html
<a href="/link" class="project-card">
    <h3>Title</h3>
    <p>Description</p>
    <div class="tags"><span class="tag">Tag</span></div>
</a>
```

### Dialog
Use `window.showDialog(title, message)` or `window.showConfirm(title, message, onConfirm)`.

## Template Chain

1. `palantir_base.html` - Root: sidebar nav, mobile hamburger, Google Fonts
2. `palantir_page.html` - Page wrapper: `.page-container` with `{% block page_title %}` and `{% block page_content %}`

### Template Blocks
- `{% block title %}` - HTML `<title>`
- `{% block head %}` - Extra CSS/meta in `<head>`
- `{% block main %}` - Main content area
- `{% block scripts %}` - Page-specific JS
- `{% block page_title %}` - Page heading (palantir_page only)
- `{% block page_content %}` - Page content (palantir_page only)

## Navigation Structure

Sidebar with ASCII logo, organized in sections:
1. Core pages: About, Projects, Blog, Resume
2. Mini-apps: Spotify, Blackjack, Sudoku, Weather
3. Other: News
4. Footer: GitHub, LinkedIn

## Do's and Don'ts

**Do:**
- Use CSS custom properties for all colors
- Use `.panel` for card-like containers
- Use `.btn` classes for all buttons
- Keep monospace typography consistent
- Use `::before` content for decorative `>` prefixes

**Don't:**
- Use bright/saturated colors outside the accent palette
- Use sans-serif fonts for UI elements
- Add 3D bevels, gradients, or skeuomorphic effects
- Use Win98 class names or patterns
