---
name: "ui-component-builder"
description: "Build or refactor UI components with solid structure, accessibility, and responsive behavior while matching the Palantir dark theme design system."
---

# UI Component Builder

Use this skill when implementing or refactoring UI components/pages.

## Workflow

1. Identify the template chain (`palantir_base.html` or `palantir_page.html`).
2. Define component structure and states first.
3. Implement with semantic HTML and accessible interactions.
4. Use CSS custom properties from `palantir.css` for all theming.
5. Add responsive behavior (sidebar collapses at 768px) and validate across breakpoints.
6. Reuse existing styles/utilities before adding new patterns.

## Requirements

- Use the Palantir design system: dark backgrounds, light blue accent, monospace typography.
- Include focus/hover/disabled states for interactive controls.
- Avoid unnecessary framework-style abstractions for simple pages.
- Keep code maintainable and consistent with surrounding files.
