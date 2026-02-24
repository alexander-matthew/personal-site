---
name: "ui-designer"
description: "Apply intentional visual design updates that align with the repository’s current UI systems (Win98 primary, legacy theme where applicable)."
---

# UI Designer

Use this skill when adjusting styling, layout, or visual polish.

## Design Guidance

- Respect the active design system for the target template chain.
- For Win98 pages, keep visual motifs consistent (`win98.css`, window chrome, taskbar metaphors).
- For legacy pages (`base.html` chain), preserve existing theme behavior.
- Prioritize alignment, spacing consistency, and readable hierarchy.

## Workflow

1. Determine whether the page is in Win98 or legacy chain.
2. Reuse existing variables/classes before introducing new ones.
3. Verify desktop and mobile behavior.
4. Confirm states (hover/focus/active/disabled) remain clear.

## Quality Checks

- No visual regressions to shared navigation/layout shells.
- No inconsistent one-off spacing or color choices.
- Styles remain understandable and maintainable.
