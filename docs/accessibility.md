# Accessibility

The game and its documentation must be usable by people with disabilities.
This page lists what exists and what is planned, by category.

## Physical and motor disabilities

| Feature | Status |
|---|---|
| **Remappable controls**: every game action can be bound to any key, mouse button, gamepad button or stick (`ActionMap` in the render module) | Engine support available, settings screen planned |
| **Gamepad support**, including analog sticks and triggers | Available in the render module |
| Several bindings for the same action (for example arrows and WASD) | Available |
| Game speed and difficulty settings, so fast reactions are not required | Planned |
| Hold-to-fire option instead of repeated presses | Planned |

## Visual disabilities

| Feature | Status |
|---|---|
| **Player colors chosen for color blindness**: the four players are told apart by shape or pattern as well as by color | Planned |
| Scalable interface and text (the game uses a virtual resolution, so it scales with the window) | Available in the render module |
| High-contrast mode for missiles and enemies | Planned |

## Hearing disabilities

| Feature | Status |
|---|---|
| **Separate volumes** for music and sound effects | Available in the render module |
| Visual cues for important sounds (incoming enemy, hit taken) | Planned |
| The game never relies on sound alone to convey information | Design rule |

## Mental and cognitive disabilities

| Feature | Status |
|---|---|
| Simple, consistent controls and menus | Design rule |
| Pause at any time (in local games) and adjustable difficulty | Planned |
| Key names shown to the player in plain words ("Left Shift", "Keypad 7") | Available (`keyName`) |

## Documentation

- The documentation is plain text with headings, tables and a search bar,
  readable by screen readers, with light and dark themes.
- Diagrams are written as text (Mermaid) and explained in the text around them.
