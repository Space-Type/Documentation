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
- `Protecs::Networking::Packet` is the fixed-size datagram:
  `Packet::serialize(data)` writes a type byte followed by the payload, and
  `packet.deserialize()` reads it back into a `Packets::PacketData`, a
  `std::variant` of every packet type.

```cpp
namespace Net = Protecs::Networking;

Net::Packet packet = Net::Packet::serialize(Net::Packets::PlayerInput{
    .input = Net::Packets::PlayerInput::SHOOT,
    .state = Net::Packets::PlayerInput::HOLD_DOWN,
});
socket.send(packet, serverAddress);
```

The byte layout of every packet type is specified in the
[network protocol](../protocol.md).

Platform-specific code lives in `*.unix.cpp` and `*.win.cpp` files, and CMake
only compiles the ones for the current platform.

## Components

`Protecs::Components::Transform` (position, rotation, scale) and
`Protecs::Components::Motion` (velocity) are the components both programs
understand, so the server can send them to the clients.

## Errors

Every error derives from `Protecs::Error`: `NetworkError` for socket failures,
and `PacketError` (a `NetworkError`) for a packet that cannot be decoded, for
example an unknown type. Catching `Protecs::Error` is enough to drop a bad
packet and keep running.

## Tests

```sh
cmake -DCMAKE_BUILD_TYPE=DebugTests -S . -B build
cmake --build build --parallel
ctest --test-dir build --output-on-failure
```

The tests (addresses, sockets, errors) run on Linux and Windows in CI.
