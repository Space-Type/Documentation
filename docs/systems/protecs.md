# Protecs

**Protecs** is the library shared by the client and the server for everything
specific to R-Type's network: the protocol, the sockets and the components both
programs exchange. [Wrecks](wrecks.md) stays a game-agnostic engine, and
Protecs holds what both programs must agree on.

Repository: [Space-Type/Protecs](https://github.com/Space-Type/Protecs).

## Using it

Each component adds it as a git submodule and links its CMake target:

```cmake
add_subdirectory(lib/protecs)
target_link_libraries(r-type_server PUBLIC protecs)
```

Include everything with `#include <protecs.hpp>`, or one module with
`<protecs/networking.hpp>`, `<protecs/components.hpp>`, `<protecs/errors.hpp>`,
`<protecs/utils.hpp>`.

## Networking

- `Protecs::Networking::UDPSocket` wraps BSD sockets (Linux) and Winsock
  (Windows) behind one class: `open(host, port)`, `send()`, `receive()`,
  `pollReceive(timeout)` to wait for data without blocking forever, and
  `setNonBlocking()`.
- `Protecs::Networking::Address` is an IPv4 address and port. It is comparable
  and hashable, so the server can index its players by address.
- `Protecs::Networking::Packet` is one datagram: `Packet::serialize(data)`
  writes a type byte followed by the payload (at most 64 bytes in all), and
  `packet.deserialize()` reads it back into a `Packets::PacketData`, a
  `std::variant` of the 12 packet types. Every size is checked before it is
  read; a bad packet throws a `SerializationError`.
- `Protecs::Networking::PacketQueue` is a thread-safe queue sorted by
  simulation tick: the network thread pushes, the main thread pops the packets
  whose tick has come.

```cpp
namespace Net = Protecs::Networking;

Net::Packet packet = Net::Packet::serialize(Net::Packets::PlayerInput{
    .simulationTick = serverTick,
    .sequence = 0,
    .input = Net::Packets::PlayerInput::TRIGGER,
    .state = Net::Packets::PlayerInput::HOLD_DOWN,
});
socket.send(packet, serverAddress);
```

The byte layout of every packet type is specified in the
[network protocol](../protocol.md).

Platform-specific code lives in `*.unix.cpp` and `*.win.cpp` files, and CMake
only compiles the ones for the current platform.

## Components and systems

The **shared components** are the ones the server replicates to the clients.
Their order in `Components::Manager` is their number on the wire, so new ones
are added at the end:

| Component | Content |
|---|---|
| `Level` | Stage, progression, `won` |
| `Movement`, `PathFinding` | Movement direction and speed, path finding |
| `PlayerInput` | Held inputs of a player |
| `PlayerStats` | Slot (colour), lives, score, charge level |
| `Transform` | Position, rotation, scale |
| `Velocity` | Velocity |
| `PlayerName` | Name (32 bytes at most) |
| `Health` | Hit points and their maximum |

The **shared systems** (`Motion`, `Movement`, `PathFinding`, `PlayerMovement`,
`PlayerBounds`) move entities the same way on both sides, so the client can
predict its own ship while waiting for the server.

The **simulation rate** (`Protecs::FIXED_UPDATE_RATE`, 120 ticks per second)
and the size of the world (`MAP_MAX_X` × `MAP_MAX_Y`, 800 × 450 units) are also
defined here, so both programs agree on them.

## Errors

Every error derives from `Protecs::Error`: `NetworkError` for socket failures,
`PacketError` for an invalid packet, and `SerializationError` for one that
cannot be encoded or decoded (unknown type, too short, length out of range).
Catching `Protecs::Error` is enough to drop a bad packet and keep running.

## Tests

```sh
cmake -DCMAKE_BUILD_TYPE=DebugTests -S . -B build
cmake --build build --parallel
ctest --test-dir build --output-on-failure
```

The tests (every packet and component, the packet queue, addresses, sockets,
errors) run on Linux and Windows in CI on every pull request; `./coverage.sh`
reports the coverage (98 % of the lines).
