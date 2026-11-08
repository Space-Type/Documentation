# R-Type

A networked remake of the classic horizontal shoot'em up **R-Type**, built on
our own game engine. Up to four players fight waves of Bydos together: an
authoritative, multithreaded server runs the game, and each player uses a
graphical client.

This site is the developer documentation of the project: how it is built, how
its parts fit together, the network protocol, and why we made our technical
choices.

## Where to start

| You want to... | Read |
|---|---|
| Build and run the game | [Getting started](getting-started.md) |
| Understand how the project is organized | [Architecture](architecture.md) |
| Work on a part of the code | [Wrecks engine](systems/wrecks.md), [Protecs](systems/protecs.md), [Client](systems/client.md), [Server](systems/server.md) |
| Write a client or talk to the server | [Network protocol](protocol.md) |
| Know why we chose a library or a design | [Technical study](technical-study.md) |
| Know how the game handles disabilities | [Accessibility](accessibility.md) |
| Contribute | [Contributing](contributing.md) |

## Repositories

The project is split into several repositories, gathered in
[Space-Type/R-Type](https://github.com/Space-Type/R-Type) as git submodules:

| Repository | Content |
|---|---|
| [R-Type](https://github.com/Space-Type/R-Type) | Main repository: builds everything, contribution rules |
| [Game-Client](https://github.com/Space-Type/Game-Client) | `r-type_client`: rendering, input, audio and client game logic |
| [Server](https://github.com/Space-Type/Server) | `r-type_server`: authoritative game logic and networking |
| [Wrecks](https://github.com/Space-Type/Wrecks) | Our engine library, game-agnostic: ECS, events, utilities |
| [Protecs](https://github.com/Space-Type/Protecs) | Shared by the client and the server: network protocol, UDP sockets, shared components |
| [Documentation](https://github.com/Space-Type/Documentation) | This site |

!!! note "Project status"
    Stage 1 is playable from start to end with up to four players: waves of
    Bydos, the charged shot, the Dobkeratops boss, and a victory screen. More
    stages are text files away (see [Contributing](contributing.md#add-a-stage)).
    Pages describe what exists in the code, and what is not implemented yet is
    explicitly marked as **planned**.
