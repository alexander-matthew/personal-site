# Windows 98 UI Redesign

## Overview

Complete UI refactor to make the personal website look and feel like Windows 98. The home page becomes a desktop with icons, and all apps open as Win98-styled windows with a persistent taskbar.

## Key Decisions

1. **Classic Desktop** - Icons on teal background, Start button in taskbar
2. **Full Win98 reskin** - All apps completely restyled with gray backgrounds, beveled buttons, system fonts
3. **Replace navbar/footer** - Start menu for navigation, taskbar replaces footer, no dark/light toggle
4. **All apps as desktop icons** - Every section gets an icon, Start menu duplicates them
5. **Page-based navigation** - No dragging, clicking icon loads new page styled as Win98 window
6. **Persistent taskbar** - Start button, clock, current app indicator on every page
7. **Classic teal background** - #008080, the iconic Win98 default

## Desktop Icons

- My Computer → About
- My Documents → Blog
- Projects (folder)
- Spotify
- Blackjack
- Sudoku
- Weather
- PR Review
- News
- Resume
- Recycle Bin (decorative)

## Window Structure

```
┌─────────────────────────────────────────────────┐
│ [icon] Page Title                    [_][□][X] │  ← Title bar (blue gradient)
├─────────────────────────────────────────────────┤
│ File  Edit  View  Help                          │  ← Menu bar (optional)
├─────────────────────────────────────────────────┤
│                                                 │
│              App content here                   │  ← Content area (gray bg)
│                                                 │
└─────────────────────────────────────────────────┘
├─────────────────────────────────────────────────┤
│ [Start]     │ [Current App]  │12:34            │  ← Taskbar
└─────────────────────────────────────────────────┘
```

## Color Palette

- Teal desktop: #008080
- Window gray: #c0c0c0
- Title bar blue: #000080 → #1084d0 (gradient)
- Button highlight: #ffffff
- Button shadow: #808080
- Button dark: #000000
- Text: #000000
- Disabled text: #808080

## UI Components

- **Buttons**: 3D beveled, light gray face, outset border
- **Inputs**: White background, inset border
- **Panels**: Etched groupboxes, inset/raised panels
- **Tabs**: Raised tab buttons with connected active state
- **Typography**: MS Sans Serif, Tahoma, Arial fallback, 11-12px base

## Implementation Phases

1. Foundation (win98.css, base template, taskbar)
2. Window template (chrome, controls)
3. Static pages (About, Resume, Blog, News, Projects)
4. Interactive apps (Blackjack, Sudoku, Weather)
5. Complex apps (Spotify, PR Review, Tools)
6. Polish (icons, easter eggs)
