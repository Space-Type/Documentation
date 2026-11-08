# Getting started

## Requirements

Supported platforms: **Linux** and **Windows**. Both are built and tested in CI
on every pull request.

### Linux

- A C++23 compiler (GCC 14 or newer)
- CMake 3.20 or newer, and git
- OpenGL and X11 development packages, used by raylib:

```sh
# Fedora
sudo dnf install mesa-libGL-devel libX11-devel libXrandr-devel libXinerama-devel libXcursor-devel libXi-devel
# Ubuntu
sudo apt install libgl1-mesa-dev libx11-dev libxrandr-dev libxinerama-dev libxcursor-dev libxi-dev
```

### Windows

- Visual Studio 2022 with the "Desktop development with C++" workload (MSVC,
  which also provides CMake)
- git

Every other dependency comes with the sources (git submodules) or is fetched by
the build: see [Technical study](technical-study.md#build-system-and-dependencies).

## Build

```sh
git clone --recursive https://github.com/Space-Type/R-Type.git
cd R-Type
cmake -S . -B build
cmake --build build --parallel
```

`r-type_server` and `r-type_client` are written at the root of the repository,
with the client assets next to them. If the repository was cloned without
`--recursive`, run `git submodule update --init --recursive` first.

On Windows, Visual Studio builds several configurations from the same build
folder: pick one with `--config`; the binaries are `r-type_server.exe` and
`r-type_client.exe`:

```sh
cmake --build build --config Release --parallel
```

## Run

```sh
./r-type_server                                # listens on UDP port 5432
./r-type_client -h 127.0.0.1 -p 5432 -n Alice  # each option is optional
```

The client opens on the **connection screen**, filled with the options
(defaults: `127.0.0.1`, `5432`, `Player`): change them if needed, then
**Connect**. Up to four players play the same game; the first one starts the
level, and when everyone has left, the next player starts it over.

| Program | Options |
|---|---|
| `r-type_client` | `-h <host>`, `-p <port>`, `-n <name>`, `--help` |
| `r-type_server` | `--help`, and developer options to test a stage: `--god` (players never lose a life), `--speed <n>` (the level scrolls `n` times faster), `--start <n>` (start at progression `n`), `--drop-rate <p>` (every enemy drops a bonus life with chance `p`) |

The client finds its `assets/` folder next to the executable (or in the parent
and grandparent folders), and the server its `assets/stages/` folder from the
current directory or one of its parents, so both can be started from anywhere
in the repository.

### Controls

| Action | Keyboard | Gamepad |
|---|---|---|
| Move | Arrow keys | D-pad or left stick |
| Shoot | Space: tap for a missile, **hold to charge** and release for a beam | A |
| Pause menu (settings, quit) | Escape | Start |
| Menus | Arrows, Enter, Escape | D-pad, A, B |

Every game control can be changed in **Settings > Controls**; see
[Accessibility](accessibility.md) for the other settings.

### Playing

- Clear the waves of Bydos while the stage scrolls; the **boss** waits at the
  end of stage 1. Kill its weak point, the creature in its chest.
- Each player has **3 lives** (hearts in the top-left corner). A player with no
  life left is out, and the others play on.
- Killed enemies sometimes drop a **red heart**: touch it or shoot it for one
  more life (up to 10).
- After the last stage, every player sees the **victory** screen with their
  score.

## Working on one component

Each component is a standalone CMake project and can be built on its own, for
example the client:

```sh
git clone --recursive https://github.com/Space-Type/Game-Client.git
cd Game-Client
cmake -S . -B build && cmake --build build --parallel

# Unit tests (no window, no audio device needed)
cmake -DCMAKE_BUILD_TYPE=DebugTests -S . -B build-tests
cmake --build build-tests --parallel
ctest --test-dir build-tests --output-on-failure
```

Wrecks, Protecs and the client run their unit tests with GoogleTest in a
dedicated `DebugTests` build type, so regular builds never download or compile
the test framework.

## Previewing this documentation

```sh
git clone https://github.com/Space-Type/Documentation.git
cd Documentation
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/mkdocs serve    # http://127.0.0.1:8000
```
