# Accessibility

The game and its documentation must be usable by people with motor, visual,
hearing and cognitive disabilities. This page lists what the game offers today
and what is planned, by need. Everything marked **available** is in the client
or the server and can be tried in the game.

## Settings at a glance

All settings are in **Settings** (main menu, or **Escape** / **Start** during a
game), are applied at once, and are **saved** in a text file
(`~/.config/r-type/settings.cfg`, or `%APPDATA%\r-type\settings.cfg` on
Windows) when the player leaves the settings screen.

| Page | Settings |
|---|---|
| Audio & display | Master, music and effects volumes; fullscreen |
| Controls | A keyboard / mouse binding and a gamepad binding for each action, reset to defaults |
| Accessibility | High contrast |

## Motor disabilities

| Feature | Status |
|---|---|
| **Remappable controls**: each action (up, down, left, right, shoot) has a keyboard or mouse binding and a gamepad binding, chosen by pressing the new input | Available |
| **Conflicts are shown**: an input bound to two actions is marked with `(!)` and explained under the table, not only coloured | Available |
| **Keyboard and gamepad at the same time**, with the D-pad or the left stick | Available |
| **Menus fully usable without a mouse**: arrows or D-pad to move and change values, Enter or A to confirm, Escape or B to go back | Available |
| **No rapid pressing**: holding Shoot charges a powerful beam (released when the button is let go), so one press and hold replaces repeated tapping | Available |
| **Pause menu** at any time (Escape / Start) | Available. It is a menu over the game: in a network game, the others keep playing |
| A slower game (lower enemy and missile speeds) for players with slower reactions | Planned. Today, the server option `--speed` only changes how fast the level scrolls (for example `--speed 0.5` makes the waves come half as fast); it is a server setting, not a player one |

## Visual disabilities

| Feature | Status |
|---|---|
| **High contrast mode**: a thick outline around every ship and enemy, white for players and orange for enemies, over the sprites and the busy stage backgrounds | Available (Settings > Accessibility) |
| **Player names above the ships**: the four players are told apart by their name, not only by the colour of their ship | Available |
| **Information never conveyed by colour alone**: lives are a number of hearts (and the last one blinks), the boss health bar also shows `hp / max`, the selected menu item has a thick border and a `>` marker | Available |
| **Readable interface**: light text on a dark background with a contrast ratio of at least 4.5:1 (checked by a unit test for every interface colour) | Available |
| **The game scales with the window**: a fixed virtual resolution is scaled to any window size or to fullscreen, text included | Available |
| Colour-blind palettes for the ships | Planned (names and outlines already make the ships distinct) |

## Hearing disabilities

Every sound of the game has a visual equivalent, so the game can be played
muted:

| Sound | What is shown |
|---|---|
| Shot, charged beam | The missile or the beam, and the charge growing in front of the ship |
| Enemy hit, but not killed | The enemy blinks |
| Explosion (enemy, boss, ship) | An explosion animation |
| Life lost | Explosion, the ship blinks, one heart less in the HUD |
| Start of a stage | "LEVEL n" in big letters |
| Boss getting angry (alarm) | "WARNING" in big letters, and the boss flashes |
| Stage cleared | "STAGE CLEAR" in big letters with every player's score |
| End of the game | "Victory" (green) or "Game over" (red) screen, with the score |

| Feature | Status |
|---|---|
| **Separate volumes** for music and sound effects, and a master volume | Available |
| Subtitles for music cues | Not needed: there are no spoken lines |

## Cognitive disabilities

| Feature | Status |
|---|---|
| **Simple controls**: four directions and one button | Available |
| **Short, consistent menus**, with a hint line on every screen ("Arrows / D-pad: Move and change   Escape / B: Back") | Available |
| **Clear feedback**: big announcements at the start and end of each stage, a visible charge level, a boss health bar with numbers | Available |
| **Forgiving play**: a ship that loses a life comes back invulnerable for 2 seconds (it blinks meanwhile); a player out of lives sees "Game over" while the others play on | Available |
| Difficulty levels | Planned |

## The documentation

| Feature | Status |
|---|---|
| Light and dark themes, following the system setting | Available |
| Built-in search, and a table of contents on every page | Available |
| Plain English, short sentences, tables instead of long paragraphs | Our writing rule |
| Diagrams also described in the text, so they are not needed to understand a page | Our writing rule |
| Works with the browser zoom and screen readers (semantic HTML from MkDocs Material) | Available |
