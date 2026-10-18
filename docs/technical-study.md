# Technical study

Why we chose our language, libraries, algorithms and tools, compared with the
alternatives we considered. This study grows with the project.

## Language: C++23

The subject imposes C++. We use the **C++23** standard because it removes a lot
of boilerplate from an engine built on templates:

- **Concepts** describe what a system, a component or a render backend must
  provide, with readable compile errors.
- **`std::variant` and `std::visit`** model packet and event types without
  inheritance.
- **`std::span`, `std::to_array`, `std::erase_if`, deducing `this`** make
  low-level code (serialization, containers) safer and shorter.

The cost is compiler support: we need GCC 14 or newer and a recent MSVC.

## Build system and dependencies

| Need | Choice | Alternatives considered |
|---|---|---|
| Build system generator | **CMake** | Meson, Xmake: CMake is the standard in C++, supported by every IDE, by vcpkg and by GitHub Actions |
| Package manager | **vcpkg** (manifest mode, as a git submodule) | Conan: more powerful, but needs a Python install and profiles. CPM: simple, but downloads sources at configure time without binary caching |
| Our own libraries | **git submodules** (Wrecks, Protecs, components in R-Type) | A package registry: too heavy for libraries we change every day |

vcpkg needs no installation: CMake bootstraps it from the submodule on the first
configure, and installs the dependencies listed in `vcpkg.json` (for example
GoogleTest, only in test builds). Built packages are cached in
`~/.cache/vcpkg`, so later builds and CI runs do not rebuild them.

**OpenGL and X11 stay system libraries**, as the subject allows for low-level
platform libraries: OpenGL is the graphics driver itself, and raylib's GLFW
loads the system X11 libraries at runtime anyway.

## Graphics library: raylib

| | raylib | SFML | SDL2 |
|---|---|---|---|
| Scope | Window, 2D/3D drawing, input, audio, in one C library | Window, 2D drawing, audio, network | Window, input, audio; drawing is basic without an extra library |
| API | Simple C functions | Object-oriented C++ | C, lower level |
| Gamepad support | Built in, with a mapping database | Basic joystick API | Very good |
| Build | Small, CMake, no dependency besides OpenGL/X11 | Several dependencies (freetype, OpenAL...) | Small |

We chose **raylib** for its simplicity and built-in gamepad and audio support.
Its C API with global state is not idiomatic C++, so we **wrap it** in our
render module: game code only sees our classes, and the library could be
replaced without touching the game.

## Engine architecture: ECS

| | Inheritance (`Entity` → `Ship` → `Player`) | ECS |
|---|---|---|
| Adding a behavior | New subclass, deep hierarchies | New component or system |
| Combining behaviors | Multiple inheritance or duplication | Add components to an entity |
| Memory layout | Objects scattered on the heap | One packed array per component type |
| Coupling | Rendering, physics and logic mixed in each class | Each system only reads the components it needs |

The subject asks for decoupled subsystems: with an ECS, the render system only
needs a position and a sprite, and knows nothing about health or damage.

**Data structures in Wrecks:**

- **Signatures** are `std::bitset<64>`: checking that an entity has the
  components of a system is a single bitwise operation.
- **Components** are stored in a packed `std::vector` per type, with tables
  between entities and indices, so iterating is cache-friendly.
- **Systems and components are compile-time lists** (`std::tuple`,
  templates): no virtual call, no runtime type lookup, and mistakes are compile
  errors.
- **`SequenceContainer`** is a fixed-size ring buffer indexed by game tick,
  for client-side prediction: no allocation during the game.

## Networking: UDP and our own sockets

| | UDP | TCP |
|---|---|---|
| Delivery | Not guaranteed | Guaranteed, in order |
| Latency on packet loss | None: next update replaces the lost one | Head-of-line blocking: everything waits for the retransmission |
| Fit for real-time positions | Good | Poor |

The subject requires UDP for in-game communication, and it is the right tool:
a lost position is replaced by the next one. Messages that must arrive (joining
a game, a death) will get acknowledgments on top of UDP.

For sockets, we wrote **`Protecs::Networking::UDPSocket`** (in Protecs, the
library shared by the client and the server) over BSD sockets and Winsock
instead of using **Asio**: our needs are a single UDP socket with
polling, Asio would add a large dependency and an asynchronous model we do not
need, and writing the wrapper is also part of building our own engine.

## Storage

The game does not persist data yet: the state of a game only lives in the
server memory.

| Need (planned) | Options | Direction |
|---|---|---|
| Settings (key bindings, volumes, accessibility options) | Plain text file (INI/JSON), binary file | A human-readable file next to the game: easy to edit, easy to reset |
| Game content (levels, enemy waves) | Hard-coded, data files, scripts | Data files, so content can change without recompiling |
| Scores, accounts | Files, SQLite, a database server | Only if the multi-instance server is developed: SQLite is embedded and needs no server |

## Security

| Risk | Mitigation |
|---|---|
| Malformed or oversized packets | Fixed-size packets read into a fixed buffer, checked before use (see the [protocol](protocol.md#3-packet-layout)) |
| Cheating clients | Authoritative server: clients only send inputs |
| Address spoofing, flooding | Planned: session identifiers and rate limiting |
| Vulnerable dependencies | Pinned versions (vcpkg baseline, submodule commits), updated on purpose; planned: GitHub Dependabot alerts on the public repositories for long-term monitoring |

## Documentation

| | MkDocs (Material) | Doxygen | Sphinx | Wiki |
|---|---|---|---|---|
| Source | Markdown | Code comments | reStructuredText or Markdown | Online editor |
| Navigation and search | Built in | Basic | Built in | Basic |
| Versioned with the code | Yes | Yes | Yes | Separate |

We use **MkDocs with the Material theme**: pages are plain Markdown, the site
has navigation, a search bar and diagrams (Mermaid) out of the box, and it is
published automatically on GitHub Pages. Doxygen only documents classes and
functions, which the subject explicitly considers insufficient on its own.
