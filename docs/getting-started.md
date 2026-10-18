# Getting started

## Requirements

Supported platforms: **Linux** and **Windows**. Both are built in CI on every
pull request.

### Linux

- A C++23 compiler (GCC 14 or newer)
- CMake 3.20 or newer
- git, curl, zip, unzip, tar and pkg-config, used by vcpkg to bootstrap itself
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

Every other dependency is fetched by the build: see
[Technical study](technical-study.md#build-system-and-dependencies).

## Build

```sh
git clone --recursive https://github.com/Space-Type/R-Type.git
cd R-Type
cmake -S . -B build
cmake --build build --parallel
```

`r-type_server` and `r-type_client` are written at the root of the repository,
with the client assets next to them. If the repository was cloned without
`--recursive`, the first `cmake` fetches the submodules itself.

On Windows, Visual Studio builds several configurations from the same build
folder: pick one with `--config`, and the binaries are `r-type_server.exe` and
`r-type_client.exe`:

```sh
cmake -S . -B build
cmake --build build --config Release --parallel
```

## Run

```sh
./r-type_server    # listens on UDP port 5432
./r-type_client
```

The client finds its `assets/` folder next to the executable (or in the parent
and grandparent folders), so it can be started from any directory.

| Action | Keyboard | Gamepad |
|---|---|---|
| Move | Arrow keys | D-pad or left stick |
| Shoot (hold to keep firing) | Space | A |

!!! note
    The client and the server do not talk to each other yet: the client runs
    a local game for now (see [Client](systems/client.md#current-state-and-next-steps)).

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

Wrecks and the client run their unit tests with GoogleTest in a dedicated
`DebugTests` build type, so regular builds never download or compile the test
framework.

## Previewing this documentation

```sh
git clone https://github.com/Space-Type/Documentation.git
cd Documentation
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/mkdocs serve    # http://127.0.0.1:8000
```
