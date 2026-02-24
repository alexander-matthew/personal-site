---
name: "ui-designer"
description: "Apply intentional visual design updates that align with the Palantir dark theme design system."
---

# UI Designer

Use this skill when adjusting styling, layout, or visual polish.

## Design Guidance

- Respect the Palantir design system defined in `palantir.css`.
- Use CSS custom properties (`--bg-primary`, `--accent`, `--text-primary`, etc.) for all colors.
- Use JetBrains Mono for all UI text. Spacing uses the `--space-*` scale.
- Pages extend `palantir_base.html` (home) or `palantir_page.html` (content pages).
- Components: `.panel` cards, `.btn` / `.btn-primary` / `.btn-ghost` buttons, dark form inputs, accent-colored tabs.

## Workflow

1. Determine whether the page uses `palantir_base.html` or `palantir_page.html`.
2. Reuse existing CSS variables and classes before introducing new ones.
3. Verify desktop and mobile behavior (breakpoint at 768px for sidebar collapse).
4. Confirm states (hover/focus/active/disabled) remain clear.

## Quality Checks

- No visual regressions to the sidebar navigation or page layout shells.
- No inconsistent one-off spacing or color choices outside the design system.
- Styles remain understandable and maintainable.
