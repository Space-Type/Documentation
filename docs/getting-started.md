# Getting started

## Requirements

Supported platform: **Linux**. Windows support is in progress (Wrecks already
builds and passes its tests on Windows in CI).

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

## Run

```sh
./r-type_server    # listens on UDP port 5432
./r-type_client
```

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
