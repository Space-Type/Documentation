# Architecture

R-Type follows a **client / authoritative server** model: clients send the
player inputs, the server simulates the game and is the only one to decide what
happens (spawns, hits, deaths), and clients display the result.

## Layers

Both programs are built on **Wrecks**, our game-agnostic engine library, and on
**Protecs**, the library they share for everything specific to R-Type's
network (protocol, sockets, shared components). Each program keeps rendering,
networking and game logic in separate subsystems.

```mermaid
flowchart TB
    subgraph Client["r-type_client"]
        direction TB
        CGame["Game logic<br/>(ECS systems: controls, physics,<br/>shooting, collisions, star-field)"]
        CRender["Render module<br/>window, 2D drawing, input, audio"]
        CNet["Networking<br/>(planned)"]
        CGame --> CRender
        CGame --> CNet
    end

    subgraph Server["r-type_server"]
        direction TB
        SGame["Game logic<br/>(players, event queues;<br/>simulation in progress)"]
        SNet["Networking<br/>Server, network thread"]
        SGame --> SNet
    end

    subgraph Wrecks["Wrecks engine (library)"]
        direction LR
        ECS["ECS<br/>entities, components, systems"]
        Events["Events<br/>event manager"]
    end

    subgraph Protecs["Protecs (shared library)"]
        direction LR
        Proto["Protocol<br/>packets, serialization"]
        PNet["Sockets<br/>UDPSocket, Address"]
    end

    Raylib[("raylib<br/>(third party)")]

    CRender --> Raylib
    CGame --> ECS
    SGame --> ECS
    CNet --> Proto
    CNet --> PNet
    SNet --> Proto
    SNet --> PNet
    CNet <-. "UDP, binary protocol" .-> SNet
```

| Layer | Role | Where |
|---|---|---|
| Game logic | Entities and their behavior, as ECS systems | Client `src/systems`, server `src/game` (in progress) |
| Render module | Window, drawing, input and audio behind our own API: game code never includes raylib | Client `src/render` |
| Networking | Receiving and sending packets | Server `src/networking`, client (planned) |
| Protocol | Packet types, binary serialization, cross-platform UDP sockets, components shared by both programs | Protecs |
| Engine | ECS, events and utilities, with no knowledge of R-Type | Wrecks |

## Decoupling rules

- **The render module only knows how to draw.** It receives positions and
  handles (`TextureId`, `FontId`...), never game rules. Game code reaches it
  through concepts (`RendererBackend`, `InputBackend`, `AudioBackend`), so
  systems can be tested with fake implementations.
- **ECS components are plain data.** Library objects (textures, sounds) stay
  in the render module, and components only store handles to them.
- **The server has the final word.** The client may predict local movement,
  but anything that matters for the game (deaths, pickups) comes from the
  server.
- **Time is driven by clocks, not by the CPU speed.** Game loops measure
  elapsed time with `std::chrono::steady_clock`, and every speed is multiplied
  by the time elapsed since the previous frame.
- **Logic and drawing are separate stages.** Each frame runs the state systems
  (`engine.update()`), then the render systems (`engine.render()`): a render
  system only reads the state, it never changes it.

## Repositories and build

```mermaid
flowchart LR
    RType["R-Type<br/>(main repository)"]
    Client["Game-Client"]
    Server["Server"]
    Docs["Documentation"]
    Wrecks["Wrecks"]
    Protecs["Protecs"]
    Raylib["raylib"]
    Vcpkg["vcpkg"]

    RType --> Client
    RType --> Server
    RType --> Docs
    Client --> Wrecks
    Client --> Protecs
    Client --> Raylib
    Client --> Vcpkg
    Server --> Wrecks
    Server --> Protecs
```

Every arrow is a git submodule. The root `CMakeLists.txt` of R-Type builds
each component as a **standalone CMake project** (`ExternalProject`): each one
keeps its own Wrecks and Protecs versions and toolchain (vcpkg for the client), which also
lets every component be developed and tested on its own.
