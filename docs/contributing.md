# Contributing

The full rules are in
[CONTRIBUTING.md](https://github.com/Space-Type/R-Type/blob/main/CONTRIBUTING.md).
This page sums them up, then shows how to make the most common changes.

## Workflow

1. Every task is an **issue** in the
   [project board](https://github.com/orgs/Space-Type/projects/1), with a clear
   title, acceptance criteria, a priority and a MoSCoW rank (Must, Should,
   Could). A task found while working on another one gets its own
   **sub-issue**.
2. Work happens on a **short-lived branch** of the component's repository,
   named `<type>/<scope>/<topic>`, for example `feat/server/broadcast` or
   `fix/render/animations`. Never develop in R-Type itself: change the
   component, then update its submodule in R-Type.
3. Changes reach `main` through a **pull request** that uses the template,
   closes its issues (`Closes #12`) and passes the **CI** (build and tests on
   Linux and Windows). `main` must always build and stay deployable.
4. Every pull request needs **one approval** from another team member.
   Approving your own pull request is forbidden, and reviews are done within
   48 hours.
5. A big change is a series of **small commits** that each build: reviewers
   read a pull request commit by commit.

## Commits

Commit messages follow the Angular convention:

```text
<type>(<scope>): <description>

feat(systems): add the stage 1 boss
fix(build): build the server on Windows despite the windows.h macros
docs(protocol): describe the EntityList packet
```

Common types: `feat`, `fix`, `docs`, `test`, `refactor`, `build`, `ci`.

## Code style

- C++23, 4-space indentation, `#pragma once`, the Epitech header on every file.
- `PascalCase` for types, `camelCase` for functions, `m_` prefix for members,
  `UPPER_CASE` for constants.
- One class per folder: `src/<module>/<Class>/<Class>.{hpp,cpp}`.
- Prefer concepts and templates over virtual functions, and `noexcept` where it
  applies.
- Platform-specific files are named `Name.unix.cpp` and `Name.win.cpp`.
- Code, comments and documentation are written in **English**.

## Tests

| Repository | Command |
|---|---|
| Wrecks, Protecs | `cmake -DCMAKE_BUILD_TYPE=DebugTests -S . -B build && cmake --build build && ctest --test-dir build`, coverage with `./coverage.sh` |
| Game-Client | `cmake -DCMAKE_BUILD_TYPE=DebugTests -S . -B build-tests && cmake --build build-tests && ctest --test-dir build-tests` (headless: no window needed) |
| Server | Build, then play a stage with the developer options (below) |

Tests use **GoogleTest**. A bug fixed should come with a test that failed before
the fix.

**Developer options of the server**, to test a stage quickly (never on a real
server, they are logged as a warning):

```sh
./r-type_server --god --start 3700    # invincible players, start just before the stage 1 boss
./r-type_server --speed 10            # the level scrolls 10 times faster
```

## How to...

### Add a stage

1. Add its background as `assets/stages/stage-<n>.png` in Game-Client (240
   pixels high).
2. Write `assets/stages/stage-<n>.waves` in the Server:

    ```text
    length 4000          # where the scrolling stops (pixels of the background)
    boss   dobkeratops   # optional: without a boss, the stage ends at its length

    # progression  type       y    movement
    600            pata-pata  120  sine
    630            pata-pata  120  sine
    ```

3. That's all: the server loads every `stage-<n>.waves` it finds, and goes on
   to stage `n` when stage `n - 1` is cleared. Invalid lines are logged and
   skipped.

### Add an enemy or a boss

1. **Protecs**: add its kind at the **end** of `EntityCreate::EntityType`, so
   the existing values do not change.
2. **Server**: write its blueprint in `src/game/Blueprints/Blueprints.cpp`: a
   `SpawnRequest` with its size, speed and **behaviour components**:

    | Component | Behaviour |
    |---|---|
    | `Enemy { reward }` | Hit by player shots, hurts players, gives points |
    | `Health` | Hit points (shared with clients) |
    | `Armored` | Absorbs shots without damage |
    | `StopAt { x }` | Enters from the right, then stays at `x` |
    | `RandomShots { min, max }` | Fires at random intervals |
    | `AimedBursts { ... }` | Fires bursts at the nearest player |
    | `Boss` | Its death clears the stage |

    Parts of a big enemy go in `parts`: they follow it and die with it. A boss
    is named in the `BOSSES` table, so stage files can use it.
3. **Client**: give its kind a sprite in `Session::initSprite`, with a sprite
   sheet function from `src/game/SpriteSheets`.
4. A behaviour that no component covers is a new component and a new system:
   a system has a `signature()`, `setEngine()` and `operator()(entity, dt)`,
   and is added to `src/systems/Tuple.hpp` with its order.

### Add a shared component or a packet

1. Add it in **Protecs**, at the **end** of `Components::Manager` or of
   `Packets::PacketData`: its index is its number on the wire, so the existing
   numbers must not change.
2. Give it `serialize`, `deserialize` and `packedSize`. `deserialize` must check
   every size **before** reading (see
   [Validation and security](protocol.md#8-validation-and-security)), and the
   packet must stay within 64 bytes.
3. Test serialization, deserialization, a too small buffer and invalid values;
   keep the coverage of Protecs above 98 % of the lines.
4. Document it in the [protocol](protocol.md) and in `rfc/build_rfc.py`
   (then run `python3 rfc/build_rfc.py` to regenerate the RFC text), and
   update the Protecs submodule in the client and the server.

### Add a client setting

1. Add the value to `Preferences` (`src/game/Preferences`) with its
   `key=value` name, and a widget to a page of the `Settings` scene.
2. It is saved with the other settings when the player leaves the settings
   screen, and read at start-up (an unknown or invalid value is ignored).

## Updating this documentation

Pages are Markdown files in the `docs/` folder of the
[Documentation](https://github.com/Space-Type/Documentation) repository. Add a
page in `mkdocs.yml` (`nav`) and preview it with `mkdocs serve` (see
[Getting started](getting-started.md#previewing-this-documentation)). The site
is rebuilt and published on every push to `main`. Diagrams are written in
[Mermaid](https://mermaid.js.org/), in the page itself; describe them in the text
too.
