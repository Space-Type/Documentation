# Client

`r-type_client` displays the game and reads the player inputs. Repository:
[Space-Type/Game-Client](https://github.com/Space-Type/Game-Client).

## Layout

```
Game-Client/
  include/rtype.hpp        aggregate header of the client
  src/main.cpp             entry point
  src/game/                Game class (main loop), Controls, ECS Engine type
  src/components/          ECS components (plain data)
  src/systems/             ECS systems, one folder each
  src/render/              render module: window, drawing, input, audio, asset paths
  assets/                  sprites and sounds
  tests/render/            unit tests and manual test program of the render module
  lib/                     submodules: wrecks, protecs, raylib, vcpkg
```

## Game loop

`RType::Game::Game` owns the window, the render resources, the audio, the
controls and the ECS engine, and runs the main loop (target: 120 frames per
second). Each frame:

1. Measure the time elapsed since the previous frame with
   `std::chrono::steady_clock` (capped at 0.1 s, so a stall never teleports
   entities). Every speed is in virtual pixels per second and multiplied by it.
2. `engine.update()` runs the **state** systems (game logic).
3. `Dead::flush()` deletes the entities killed during the update, and
   `Shoot::flush()` creates the bullets fired during it: creating or deleting
   entities while the engine iterates over them would be unsafe.
4. `engine.render()` runs the **render** systems between `beginFrame()` and
   `endFrame()`.
5. Sleep until the next frame.

## Systems

Systems run in the order of the `Systems` tuple (`src/systems/Systems.hpp`).

| System | Stage | Needs | Role |
|---|---|---|---|
| `Controllable` | state | `Controllable`, `Physics` | Turns the player's actions into acceleration, and sets `Shooter::wantsToShoot` |
| `Physics` | state | `Transform`, `Physics` | Applies the velocity with frame-rate independent damping, keeps the entity on screen |
| `RandomMovement` | state | `Transform`, `HasRandomMovement`, `Sprite` | Moves enemies to the left with random vertical changes |
| `Shoot` | state | `Transform`, `Hitbox`, `Shooter` | Fires bullets after a cooldown (players on demand, enemies automatically) and plays the shot sound |
| `Projectile` | state | `Transform`, `Hitbox`, `Projectile` | Moves bullets, kills them when they leave the screen |
| `Collision` | state | `Transform`, `Hitbox`, `Projectile` | Box overlap between a bullet and the entities of the other team that have `Health`: damage, hit sound, death |
| `Starfield` | state | `Transform`, `Star` | Scrolls the stars to the left, puts them back on the right at a random height |
| `StarRender` | render | `Transform`, `Star` | Draws the stars as small squares, behind the sprites |
| `Render` | render | `Transform`, `Sprite` | Draws the sprites |
| `Dead` | state | `Dead` | Collects the entities to delete at the end of the update |

The star-field has three layers (far stars are smaller, dimmer and slower) to
give a parallax effect.

## Controls

`src/game/Controls` defines the game actions (`Up`, `Down`, `Left`, `Right`,
`Shoot`) and `defaultControls()`: arrows and Space on the keyboard, D-pad, left
stick and A on a gamepad. `Game` owns the `Controls` (an `ActionMap<Action>`)
and the `Controllable` system only asks whether an action is held, so bindings
can be changed at runtime without touching the systems.

## Assets

`RType::Render::assetPath("sounds/enemy_hit.wav")` returns the path of a file of
the `assets/` folder, searched next to the executable, then in its parent and
grandparent folders (`build/`, `build/Release/`). The client therefore works
whatever its working directory.

## Render module

The render module (`src/render`, namespace `RType::Render`) wraps raylib behind
our own API. Game code includes `<rtype/render.hpp>` and never `raylib.h`.

| Class | Role |
|---|---|
| `Window` | The game window. Everything is drawn in a fixed **virtual resolution** (1920x1080 by default), then scaled and letterboxed into the real window |
| `Resources` | Loads textures and fonts, caches them by path and returns **handles** (`TextureId`, `FontId`) |
| `Renderer` | Draws sprites (sprite-sheet frames, pivot, rotation, flip, tint), scrolling backgrounds (star-field), shapes and text |
| `Input` | Keyboard, mouse (in virtual coordinates) and gamepad |
| `ActionMap<Action>` | Binds game actions to keys, buttons and axes, remappable at runtime |
| `Audio` | Sounds and streamed music, with master, music and effects volumes |

Key rules:

- ECS components store **handles**, never raylib objects, so they can be
  copied and moved freely by the ECS containers.
- Only one `Window` and one `Audio` may exist at a time. Unknown handles are
  ignored, and without an audio device every audio call is a silent no-op.
- The module never paces time: the game loop does.

The full guide, with code examples, is in the client repository:
[`src/render/README.md`](https://github.com/Space-Type/Game-Client/blob/main/src/render/README.md).

## Current state and next steps

!!! info "Playable locally"
    The client runs a complete local game: a scrolling star-field, the
    player's ship, five enemies that move and shoot back, bullets, collisions,
    deaths, and sounds for shots and hits. It does not talk to the server yet:
    this game logic runs on the client for now, and moves to the server with
    the network link.

Next steps:

- Connection to the server through [Protecs](protecs.md): send the player's
  actions (`PlayerInput`), display the entities sent by the server.
- Enemies spawning randomly on the right of the screen, decided by the server.
- Four visually distinct players (colors chosen for color blindness, see
  [Accessibility](../accessibility.md)).
- A settings screen for key bindings and volumes.

## Build and test

```sh
cmake -S . -B build && cmake --build build --parallel

cmake -DCMAKE_BUILD_TYPE=DebugTests -S . -B build-tests
cmake --build build-tests --parallel
ctest --test-dir build-tests --output-on-failure
```

The unit tests never open a window or an audio device, so they run in CI. A
manual test program (`render_manual_test` target, see the module guide) checks
rendering, input and audio by eye.
