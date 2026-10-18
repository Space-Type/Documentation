# Network protocol

**Status:** draft, version 0. This document describes the binary protocol
between `r-type_client` and `r-type_server`. It is precise enough to write a
new client, and it grows with the implementation.

The key words **MUST**, **MUST NOT**, **SHOULD** and **MAY** are to be
interpreted as described in [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119).

## 1. Transport

- All in-game communication uses **UDP**. There is no TCP connection.
- The server listens on **UDP port 5432**, on every interface (`0.0.0.0`).
- One datagram carries exactly **one packet**.
- UDP does not guarantee delivery, order or uniqueness: a peer MUST NOT assume
  that every packet arrives, or arrives once, or in order.

## 2. Data types

| Type | Size | Encoding |
|---|---|---|
| `u8` | 1 byte | unsigned integer |
| `u32` | 4 bytes | unsigned integer, **little-endian** |
| `f32` | 4 bytes | IEEE 754 single precision float, **little-endian** |

All multi-byte values are little-endian. Fields are packed: there is no
padding between them.

## 3. Packet layout

Every packet has the same fixed size: **16 bytes**.

| Offset | Size | Field | Description |
|---|---|---|---|
| 0 | 1 | `type` | Packet type (see section 4) |
| 1 | 15 | `payload` | Type-specific fields, then zero padding up to 16 bytes |

- A sender MUST fill unused payload bytes with zeros.
- A receiver MUST drop a datagram whose size is not exactly 16 bytes.
- A receiver MUST drop a packet whose `type` is unknown.
- A receiver MUST NOT stop, crash or allocate memory based on the content of an
  invalid packet: invalid packets are silently ignored (and MAY be logged).

## 4. Packet types

| Type | Name | Direction | Status |
|---|---|---|---|
| `0` | `EntityPosition` | both | implemented |

### 4.1 `EntityPosition` (type 0)

Position of an entity in the game world.

| Offset | Size | Type | Field | Description |
|---|---|---|---|---|
| 0 | 1 | `u8` | `type` | `0` |
| 1 | 4 | `u32` | `entity` | Entity identifier, chosen by the server |
| 5 | 4 | `f32` | `x` | Horizontal position, in world units |
| 9 | 4 | `f32` | `y` | Vertical position, in world units |
| 13 | 3 | | padding | Zeros |

The world unit is not fixed by the protocol yet. The planned convention is the
client's virtual resolution: `x` from `0` (left) to `1920` (right), and `y` from
`0` (top) to `1080` (bottom).

Example: entity `7` at `(100.0, 540.0)`:

```
00 07 00 00 00 00 00 c8 42 00 00 07 44 00 00 00
^^ ^^^^^^^^^^^ ^^^^^^^^^^^ ^^^^^^^^^^^ ^^^^^^^^
type  entity      x=100.0     y=540.0   padding
```

## 5. Planned packets

!!! info "Not implemented yet"
    The packets below are being designed with the server, and their layout is
    subject to change. They will get their own type number and layout table
    once implemented.

| Name | Direction | Purpose |
|---|---|---|
| `Connect` / `Accept` | client → server / server → client | Join a game, receive a player identifier |
| `Input` | client → server | Pressed directions and fire button, with the client tick |
| `Spawn` / `Destroy` | server → client | An entity (player, Bydo, missile) appears or is destroyed |
| `Heartbeat` | both | Keeps the session alive, detects crashed clients |
| `Disconnect` | both | A player leaves, other clients are notified |

## 6. Security considerations

- Packets have a **fixed size** and are read into a fixed-size buffer: a
  datagram cannot make a peer read or allocate more than 16 bytes.
- The server is the **authority**: it never trusts a position or an event sent
  by a client, only its inputs.
- UDP source addresses can be spoofed: the planned `Connect` handshake will
  give each client an identifier that later packets must carry.
- A client that floods the server SHOULD be dropped (planned rate limiting).

## 7. Implementation notes

- The reference implementation is in the server repository:
  `src/networking/Packet` (type byte and dispatch) and
  `src/networking/packets/EntityPosition`.
- The current implementation copies the fields with `memcpy`, in host byte
  order. On every supported platform (x86-64 Linux and Windows) this is
  little-endian, as required by section 2.
- The current server does not yet apply all the receiver rules of section 3
  (size check, unknown type): this is part of the robust decoding planned on
  the [server page](systems/server.md#next-steps).
