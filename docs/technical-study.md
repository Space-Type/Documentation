# Technical study

Why we chose our language, libraries, algorithms, data structures, storage and
security measures, compared with the alternatives. Where a choice has a
measurable cost, we **measured it on our own code**: the numbers below come
from [`benchmarks/`](https://github.com/Space-Type/Documentation/tree/main/benchmarks)
and anyone can run them again.

## Measurements

| | |
|---|---|
| Tool | `rtype_bench` (`benchmarks/` in this repository), built in Release |
| Machine | Intel Core i7-14650HX, Linux, GCC 15.2 |
| Code measured | Protecs and Wrecks of the stage 1 release (Protecs `86e12c3`), server of [Server#34](https://github.com/Space-Type/Server/pull/34) |
| Network tests | Real server and test clients on the same machine (`127.0.0.1`), server started with `--god` |
| Precision | Timings vary by about ±20 % between runs: they are rounded, and only orders of magnitude are compared |

## Language: C++23

The subject imposes C++. We use the **C++23** standard because it removes a lot
of boilerplate from an engine built on templates:

- **Concepts** describe what a system, a component or a render backend must
  provide, with readable compile errors.
- **`std::variant` and `std::visit`** model packets, components and events
  without inheritance: a packet type is the index of its alternative.
- **`std::span`, designated initializers, `std::ranges`** make low-level code
  (serialization, containers) safer and shorter.

The cost is compiler support: we need GCC 14 or newer and a recent MSVC, which
our CI checks on every pull request (Linux and Windows).

## Build system and dependencies

| Need | Choice | Alternatives considered |
|---|---|---|
| Build system generator | **CMake** | Meson, Xmake: CMake is the standard in C++, supported by every IDE and by GitHub Actions |
| Our libraries (Wrecks, Protecs) | **git submodules**, pinned to a commit | A package registry: too heavy for libraries we change every day |
| raylib | **git submodule**, built with the client | vcpkg, Conan |
| GoogleTest | **CMake `FetchContent`**, pinned to v1.17.0, only in test builds | vcpkg, Conan, system package |

We started with **vcpkg** (manifest mode) and removed it: with raylib and
GoogleTest as the only third-party libraries, a submodule and `FetchContent`
give pinned versions without a package manager to bootstrap. **Conan** needs a
Python install and profiles; **system packages** give different versions on
every machine and none on Windows.

**OpenGL and X11 stay system libraries**, as the subject allows for low-level
platform libraries: OpenGL is the graphics driver itself.

**Dependencies are cached in CI**, not fetched again on every commit:
GoogleTest is downloaded once (`actions/cache`), and on Linux `ccache` keeps
compiled objects. Measured on our CI: **99 to 100 % of the compilations** of
the second run were served from the cache.

## Graphics library: raylib

| | raylib | SFML | SDL2 |
|---|---|---|---|
| Scope | Window, 2D/3D drawing, input, audio, in one C library | Window, 2D drawing, audio, network | Window, input, audio; drawing is basic without an extra library |
| API | Simple C functions | Object-oriented C++ | C, lower level |
| Gamepad support | Built in, with a mapping database | Basic joystick API | Very good |
| Build | Small, CMake, no dependency besides OpenGL/X11 | Several dependencies (FreeType, OpenAL...) | Small |

We chose **raylib** for its simplicity and its built-in gamepad and audio
support. Its C API with global state is not idiomatic C++, so we **wrap it** in
our render module: game code only sees our classes (`Renderer`, `Input`,
`Audio`, `Resources`), and the library could be replaced without touching the
game. The wrapper also gives us testability: the systems take a backend that
satisfies a concept, and the tests use a fake one.

## Engine architecture: ECS

| | Inheritance (`Entity` → `Ship` → `Player`) | ECS |
|---|---|---|
| Adding a behaviour | New subclass, deep hierarchies | New component, run by a system |
| Combining behaviours | Multiple inheritance or duplication | Add components to an entity |
| Coupling | Rendering, physics and logic mixed in each class | Each system only reads the components it needs |
| Network replication | Each class serializes itself | Generic: an entity is a set of components, each one serialized the same way |

**How it pays off in this project:**

- **Rendering, networking and game logic stay decoupled**, as the subject asks:
  a render system only needs a position and a sprite.
- **A new enemy or boss is data.** The stage 1 boss is a list of behaviour
  components (`Armored`, `AimedBursts`, `StopAt`, `Boss`...) run by generic
  systems; a stage is a text file. No class to write.
- **Replication is generic.** An entity's shared components are a 64-bit
  signature: the protocol sends it as is (`EntityList`, `EntitySyncComponents`),
  and every component goes through the same `EntityComponentData` packet.

**Data structures in Wrecks:**

- **Signatures** are `std::bitset<64>`: checking that an entity has the
  components of a system is one bitwise operation.
- **Components** are stored in one contiguous `std::vector` per type, with two
  hash maps (`std::unordered_map`) between entities and indices.
- **Systems and components are compile-time lists** (`std::tuple`,
  templates): no virtual call, no runtime type lookup, and mistakes are
  compile errors.
- **`SequenceContainer`** is a fixed-size ring buffer indexed by tick, for
  client-side prediction: no allocation during the game.

**Measured cost** (`rtype_bench ecs`): one fixed update of the shared `Motion`
system on N moving entities, against the same work done by N heap objects with
a virtual `update()`:

| Moving entities | Wrecks ECS | Objects + virtual update |
|---|---|---|
| 100 | ~2 µs | ~0.3 µs |
| 1 000 | ~12 µs | ~3 µs |
| 10 000 | ~115 µs | ~29 µs |

Our ECS is **about 4 times slower** than a plain loop over objects. The cause is
the storage: every component access goes through a hash map lookup, where the
objects are read directly. It does not matter at our scale: a stage has about
20 entities on screen and at most a few dozen (measured below), so the update
costs about **2 µs out of the 8 333 µs** of a tick at 120 Hz (0.02 %). The
known fix, if we ever need it, is a **sparse set** (an array from entity to
index instead of a hash map), the storage used by EnTT.

## Algorithms

| Problem | Algorithm | Why |
|---|---|---|
| Time | **Fixed time step** at 120 Hz with an accumulator: the elapsed time (`steady_clock`) is added up and the simulation runs one tick per 1/120 s | The game speed never depends on the CPU or the frame rate; client and server simulate the same ticks |
| Collisions | **Axis-aligned boxes** (AABB), each shot against each enemy, sorted by distance for beams | With tens of entities, the n × m test costs less than building a spatial grid; the sort gives the R-Type rule that a beam pierces what it kills and stops on a survivor |
| Waves | Stage file **sorted by progression**, an index on the next wave | Each tick only looks at the next wave: O(1); `--start` finds the first wave with a binary search (`lower_bound`) |
| Packets by tick | **Sorted queue** (`PacketQueue`): packets wait until the simulation reaches their tick | Inputs and updates are applied at the right tick whatever their arrival order |
| Randomness in systems | **xorshift32** | Systems must be `noexcept` default constructible; the standard engines are bigger and may throw on seeding |
| Entity ids | Upper 32 bits from the clock, lower 32 bits the server entity | An id is never reused when an entity slot is, so a late packet cannot hit the wrong entity |

**Measured weak spot** (`rtype_bench queue`): `PacketQueue` decodes packets
again at every comparison of its sorted insertion. Per packet:

| Packets waiting | `PacketQueue` | Tick read once, `std::priority_queue` |
|---|---|---|
| 16 | ~140 ns | ~20 ns |
| 256 | ~340 ns | ~25 ns |
| 1 024 | ~660 ns | ~50 ns |

At about 700 packets per second per client (measured below), the queue costs
less than 0.5 ms per second: acceptable today, and an easy gain (decode the tick
once when the packet arrives) if the traffic grows.

## Networking

### UDP and our own sockets

| | UDP | TCP |
|---|---|---|
| Delivery | Not guaranteed | Guaranteed, in order |
| A lost packet | Replaced by the next update | Head-of-line blocking: everything after it waits for the retransmission |
| Fit for real-time state | Good | Poor |

The subject requires UDP for in-game communication, and it is the right tool:
a lost position is replaced 50 ms later by the next one. Our protocol never
retransmits; it repeats state (see the
[protocol](protocol.md#73-staying-consistent-over-a-lossy-network)).

For sockets, we wrote **`Protecs::Networking::UDPSocket`** over BSD sockets and
Winsock instead of using **Asio**: we need one UDP socket with polling, Asio
would add a large dependency and an asynchronous model we do not use, and
writing the wrapper is part of building our own engine.

**Threads:** the server receives datagrams on a dedicated thread, which pushes
them into the thread-safe `PacketQueue`; the main thread simulates and sends.
The client also receives on its own thread, so a slow frame never delays the
network.

### Prediction and interpolation

| Technique | In our game |
|---|---|
| **Client-side prediction** | The client runs the same movement systems as the server (shared in Protecs) on its own ship, so it moves at once when a key is pressed; the server's position then corrects it |
| **Authoritative server** | Shots, hits, deaths and scores are only computed by the server: a client cannot cheat on them |
| **Interpolation** of other entities | Not yet: other entities are drawn at their last received position, 20 times per second. Smooth enough at 120 frames per second for slow Bydos; interpolating between the two last updates (100 ms behind) is the next step if movements look jerky on a real network |
| **Lag compensation** (rewinding hits to what the shooter saw) | Not needed: shots are slow projectiles simulated by the server, not instant hits |

### Binary encoding

`rtype_bench serialization`: one `Transform` update, in our binary format and
as JSON-like text (`snprintf` / `sscanf`):

| Encoding | Bytes | Encode | Decode |
|---|---|---|---|
| Protecs binary | **31** | ~10 ns | ~14 ns |
| Text (JSON-like) | 74 | ~315 ns | ~290 ns |

The binary format is **2.4 times smaller** and **20 to 30 times faster**, and
it has no parser to attack: every field has a fixed size, checked before it is
read. **Protocol Buffers** or **FlatBuffers** would give a compact format with
schema evolution, at the cost of a code generator and a dependency; with a
dozen fixed packets, writing the encoding by hand was simpler.

### Bandwidth

`rtype_bench bandwidth`: what one client receives during stage 1, measured for
60 s (about 21 entities on screen on average, 35 at most):

| Packet | Packets/s | Bytes/s | Share |
|---|---|---|---|
| `EntityComponentData` | 693 | 18 500 | 99.3 % |
| `EntityCreate` | 4.4 | 61 | 0.3 % |
| `EntityDelete` | 3.8 | 49 | 0.3 % |
| `PlayerInput` (input requests) | 2 | 16 | 0.1 % |
| Total | **~700** | **~18.6 kB/s** | |

Every client receives the same, so the server sends about **75 kB/s for
4 players**: far below any home connection. The UDP and IPv4 headers add
28 bytes per datagram, which is as much as our average packet: the next gains
would be to **send only components that changed** and to **group several updates
in one datagram** (the 64-byte receive buffer is the limit today).

### Packet loss

`rtype_bench loss`: two clients play the same game for 40 s; one receives
everything, the other drops a share of its datagrams. We count the entities the
lossy client is wrong about, on average:

| Datagrams lost | Entities (truth) | Missing on the lossy client | Ghosts (deleted, still shown) | Ghosts with the 1 s rule |
|---|---|---|---|---|
| 0 % | 19.6 | 0 | 0 | 0 |
| 5 % | 19.7 | 1.1 | 2.2 | **0.14** |
| 10 % | 19.2 | 1.8 | 3.6 | **0.29** |
| 20 % | 19.0 | 4.1 | 7.5 | **0.60** |
| 40 % | 19.3 | 7.5 | 9.8 | **0.68** |

- A lost `EntityDelete` leaves a **ghost** on screen. Our client forgets an
  entity the server has not updated for one second (the server updates every
  entity 20 times per second): this **removes 92 to 94 % of the ghosts**.
- A lost `EntityCreate` makes an entity **missing** until the client asks for
  the entity list. The list is sent 3 entities per datagram, and each of them
  may be lost too: this is the next thing to improve.

To degrade a real link instead, as the subject's appendix suggests, the
benchmark README shows the `netem` commands.

## Storage

| Data | Format | Why |
|---|---|---|
| **Settings** (volumes, fullscreen, high contrast, key and gamepad bindings) | `key=value` text file in `%APPDATA%\r-type` or `~/.config/r-type`, at most 4 KiB | Human-readable, easy to fix or reset by hand; inputs stored by name, not by number, so a new version of the game still reads it. A broken line is skipped, a broken file gives the defaults |
| **Stages** (length, boss, enemy waves) | Text file per stage, `assets/stages/stage-<n>.waves`, at most 64 KiB | New stages without recompiling; invalid lines are logged and skipped |
| **Game state** | Server memory only | A game lasts minutes; nothing needs to survive a restart |

| Alternative | Why not (yet) |
|---|---|
| JSON or YAML | Needs a parser library for flat key-value settings |
| Binary settings file | Not editable by hand, breaks when a field is added |
| SQLite | Only worth it for persistent scores or accounts, which the game does not have |

## Security

| Risk | Measure |
|---|---|
| Malformed or oversized packets | Datagrams read into a fixed 64-byte buffer; every size checked before reading ([protocol](protocol.md#8-validation-and-security)) |
| Cheating clients | Authoritative server: clients only send inputs, the server computes positions, hits, scores |
| Strangers | Every packet but `PlayerJoin` is ignored from an address that did not join |
| Input floods | At most 50 pending inputs per player; inputs for past ticks are ignored |
| Oversized files | Settings at most 4 KiB, stage files at most 64 KiB, checked before reading |
| Address spoofing | UDP does not prove where a datagram comes from, and a player is known by its address: someone who can spoof it could send inputs in its name. They can only move or fire that ship, never change the game state. A session token in each packet, given in `PlayerId`, is the planned fix |
| Flooding | Measured below: the server keeps running and answering. Planned: a limit of datagrams per second and per address |
| Vulnerable dependencies | Pinned versions (submodule commits, GoogleTest tag), updated on purpose. For long-term monitoring, GitHub **Dependabot** alerts can watch the submodules and the GitHub Actions of the public repositories |

**Robustness, measured** (`rtype_bench fuzz`): 100 000 malformed datagrams of
five kinds (random bytes; a known type with a random payload; an `EntityList`
announcing 4 billion entries; a `PlayerJoin` with a 255-byte name; an unknown
component type), half from a stranger and half from a joined player:

| Datagrams sent | Received by the server | Crash | New player accepted afterwards | Server memory |
|---|---|---|---|---|
| 100 000 | 44 306 | **none** | yes, in < 1 ms | 5.3 → 9.4 MiB |

Writing the protocol also showed that a crashed client was never removed: the
server now pings every player each second and removes one silent for 5 seconds
([Server#49](https://github.com/Space-Type/Server/pull/49)). The test also found
weaknesses, listed with their fixes in the
[protocol](protocol.md#known-gaps-of-the-reference-implementation): there is no
limit of 4 players, player
names may hold control characters, the `EntityList` size check is 4 bytes too
lenient, the server log is written by two threads at once (lines may mix), and
the server memory keeps growing with repeated floods (about 2 to 4 MiB per
100 000 datagrams, cause under investigation).

## Documentation

| | MkDocs (Material) | Doxygen | Sphinx | Wiki |
|---|---|---|---|---|
| Source | Markdown | Code comments | reStructuredText or Markdown | Online editor |
| Navigation and search | Built in | Basic | Built in | Basic |
| Diagrams | Mermaid built in | Graphviz for classes | Extensions | Images |
| Versioned with the code | Yes | Yes | Yes | Separate |

We use **MkDocs with the Material theme**: pages are plain Markdown, the site
has navigation, search and Mermaid diagrams out of the box, and our CI
publishes it on GitHub Pages. Doxygen only documents classes and functions,
which the subject considers insufficient on its own.
