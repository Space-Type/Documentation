# Client

`r-type_client` displays the game and reads the player inputs. Repository:
[Space-Type/Game-Client](https://github.com/Space-Type/Game-Client).

## Layout

```
Game-Client/
  include/rtype.hpp        aggregate header of the client
  src/main.cpp             entry point
  src/game/                Game class (main loop) and the ECS Engine type
  src/components/          ECS components (Transform, Physics, Sprite)
  src/systems/             ECS systems (Physics, Render)
  src/render/              render module: window, drawing, input, audio
  tests/render/            unit tests and manual test program of the render module
  lib/                     submodules: wrecks, raylib, vcpkg
```

## Game loop

`RType::Game::Game` owns the ECS engine and runs the main loop: each frame it
updates the systems, draws, then sleeps until the next frame, measuring time
with `std::chrono::steady_clock` (target: 120 frames per second).

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

!!! warning "Work in progress"
    The game currently opens a window with one moving spaceship. Some of its
    code still calls raylib directly instead of the render module, which is
    being migrated.

Planned: star-field background, player movement with the arrow keys through
`ActionMap`, connection to the server, display of the entities sent by the
server, four distinct player colors, sounds.

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
