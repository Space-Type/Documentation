# Server

`r-type_server` runs the game and is the authority on everything that happens
in it. Repository: [Space-Type/Server](https://github.com/Space-Type/Server).

## Layout

```
Server/
  include/rtype.hpp           aggregate header of the server
  src/main.cpp                entry point
  src/networking/Server/      Server class: socket and main loop
  src/networking/Packet/      packet serialization (type byte + payload)
  src/networking/packets/     one folder per packet type (EntityPosition)
  src/utils/                  memory helpers, Ctrl+C handling
  lib/wrecks                  Wrecks engine (submodule)
```

## How it works today

- `Server::Builder` configures the server (host, port, optional log stream)
  and builds it. `main.cpp` listens on `0.0.0.0:5432`.
- `Server::run()` loops until the socket is closed: it receives a datagram,
  decodes it with `Packet::deserialize()` and logs its content.
- Ctrl+C is caught (`InterruptHandler`): the server closes its socket and
  shuts down cleanly.
- Packets are a `std::variant` of packet types (`PacketData`), serialized as a
  type byte followed by the payload. See the [network protocol](../protocol.md).

## Next steps

!!! warning "Work in progress"
    The server currently only receives and logs packets. The items below are
    required by the project and are being implemented.

- **Multithreading**: a network thread receives and sends packets, while the
  game loop runs at a fixed rate whatever the clients do (`pollReceive` in
  Wrecks avoids blocking forever on the socket).
- **Authoritative simulation** with the Wrecks ECS: players, Bydos spawning on
  the right of the screen, missiles, collisions, deaths.
- **Client sessions**: connection, timeout detection, and notification of the
  other clients when one disconnects or crashes.
- **Robust decoding**: every datagram is checked (size, packet type) before it
  is read, and invalid ones are dropped instead of stopping the server.
