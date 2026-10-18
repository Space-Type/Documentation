# Server

`r-type_server` runs the game and is the authority on everything that happens
in it. Repository: [Space-Type/Server](https://github.com/Space-Type/Server).

## Layout

```
Server/
  include/rtype.hpp             aggregate header of the server
  src/main.cpp                  entry point
  src/networking/Server/        Server class: socket, network thread, main loop
  src/game/Game/                Game class: ECS engine, players, event queues
  src/game/Player/              a connected player (its address)
  src/game/EventHandler/        one handler per packet type
  src/threads/ThreadQueue.hpp   mutex-protected queue between the two threads
  src/components/, src/systems/ ECS components and systems of the server
  src/utils/                    Ctrl+C handling
  lib/wrecks, lib/protecs       submodules: engine and shared protocol
```

## How it works today

- `Server::Builder` configures the server (host, port, optional log stream)
  and builds it. `main.cpp` listens on `0.0.0.0:5432`.
- `Server::run()` starts a **network thread** that waits for datagrams
  (`pollReceive` with a 1 second timeout, so it never blocks forever) and
  pushes each one, with its sender address, into a `ThreadQueue`.
- The **main thread** sends the packets produced by the game, then decodes the
  received ones with `Packet::deserialize()` and hands them to `Game`, which
  only accepts packets from known players.
- Packet types and their serialization come from [Protecs](protecs.md), shared
  with the client. See the [network protocol](../protocol.md).
- A packet that cannot be decoded raises a `Protecs::PacketError`: the main
  loop logs it and keeps running.
- Ctrl+C is caught (`InterruptHandler`): the server closes its socket and
  shuts down cleanly.

## Next steps

!!! warning "Work in progress"
    The server receives, decodes and dispatches packets, but does not run the
    game yet. The items below are required by the project and are being
    implemented.

- **Client sessions**: a connection packet that registers the player,
  timeout detection, and notification of the other clients when one
  disconnects or crashes.
- **Game loop at a fixed rate**, whatever the clients do, running the ECS
  simulation.
- **Authoritative simulation**: players, Bydos spawning on the right of the
  screen, missiles, collisions, deaths. The client already implements these
  rules locally, and they move to the server with the network link.
- **Robust decoding**: also drop datagrams whose size is not the packet size
  (unknown packet types are already rejected).
