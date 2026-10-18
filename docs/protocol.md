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
| `u16` | 2 bytes | unsigned integer, **little-endian** |
| `u32` | 4 bytes | unsigned integer, **little-endian** |
| `f32` | 4 bytes | IEEE 754 single precision float, **little-endian** |
| `bits64` | 8 bytes | 64 flags: flag `i` is bit `i % 8` (least significant first) of byte `i / 8`, which is a little-endian `u64` |

All multi-byte values are little-endian. Fields are packed: there is no
padding between them.

## 3. Packet layout

Every packet has the same fixed size: **24 bytes**.

| Offset | Size | Field | Description |
|---|---|---|---|
| 0 | 1 | `type` | Packet type (see section 4) |
| 1 | 23 | `payload` | Type-specific fields, then zero padding up to 24 bytes |

- A sender MUST fill unused payload bytes with zeros.
- A receiver MUST drop a datagram whose size is not exactly 24 bytes.
- A receiver MUST drop a packet whose `type` is unknown, or whose enumerated
  fields hold an unknown value.
- A receiver MUST NOT stop, crash or allocate memory based on the content of an
  invalid packet: invalid packets are silently ignored (and MAY be logged).

## 4. Packet types

| Type | Name | Direction | Purpose |
|---|---|---|---|
| `0` | `EntityAddComponent` | server → client | A component was added to an entity |
| `1` | `EntityPosition` | server → client | Position of an entity |
| `2` | `EntityRemoveComponent` | server → client | A component was removed from an entity |
| `3` | `EntitySyncComponents` | both | Compare the components of an entity with the server |
| `4` | `PlayerInput` | client → server | A player pressed or released a control |

!!! info "Status"
    These packets are defined and serialized by [Protecs](systems/protecs.md).
    The server decodes them, but does not act on them yet.

Component types are identified by a `u16`: the index of the component in the
list of components shared by the client and the server. This list will be
fixed in this document together with the connection handshake.

### 4.1 `EntityAddComponent` (type 0)

| Offset | Size | Type | Field | Description |
|---|---|---|---|---|
| 0 | 1 | `u8` | `type` | `0` |
| 1 | 4 | `u32` | `entity` | Entity identifier, chosen by the server |
| 5 | 2 | `u16` | `componentType` | Component added to the entity |
| 7 | 17 | | padding | Zeros |

### 4.2 `EntityPosition` (type 1)

Position of an entity in the game world.

| Offset | Size | Type | Field | Description |
|---|---|---|---|---|
| 0 | 1 | `u8` | `type` | `1` |
| 1 | 4 | `u32` | `entity` | Entity identifier, chosen by the server |
| 5 | 4 | `f32` | `x` | Horizontal position, in world units |
| 9 | 4 | `f32` | `y` | Vertical position, in world units |
| 13 | 11 | | padding | Zeros |

The world unit is not fixed by the protocol yet. The planned convention is the
client's virtual resolution: `x` from `0` (left) to `1920` (right), and `y` from
`0` (top) to `1080` (bottom).

Example: entity `7` at `(100.0, 540.0)`:

```
01 07 00 00 00 00 00 c8 42 00 00 07 44 00 00 00 00 00 00 00 00 00 00 00
^^ ^^^^^^^^^^^ ^^^^^^^^^^^ ^^^^^^^^^^^ ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
type  entity      x=100.0     y=540.0              padding
```

### 4.3 `EntityRemoveComponent` (type 2)

| Offset | Size | Type | Field | Description |
|---|---|---|---|---|
| 0 | 1 | `u8` | `type` | `2` |
| 1 | 4 | `u32` | `entity` | Entity identifier |
| 5 | 2 | `u16` | `componentType` | Component removed from the entity |
| 7 | 17 | | padding | Zeros |

### 4.4 `EntitySyncComponents` (type 3)

| Offset | Size | Type | Field | Description |
|---|---|---|---|---|
| 0 | 1 | `u8` | `type` | `3` |
| 1 | 4 | `u32` | `entity` | Entity identifier |
| 5 | 8 | `bits64` | `signature` | Flag `i` is set when the entity has component type `i` |
| 13 | 11 | | padding | Zeros |

A client sends its signature of an entity to check it. The server answers with
the same packet holding **its** signature, and, if they differ, sends the
missing changes as `EntityAddComponent` and `EntityRemoveComponent` packets.

### 4.5 `PlayerInput` (type 4)

| Offset | Size | Type | Field | Description |
|---|---|---|---|---|
| 0 | 1 | `u8` | `type` | `4` |
| 1 | 1 | `u8` | `input` | `0` up, `1` down, `2` left, `3` right, `4` shoot |
| 2 | 1 | `u8` | `state` | `0` pressed (held down), `1` released |
| 3 | 21 | | padding | Zeros |

Example: the player releases the fire button:

```
04 04 01 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
```

## 5. Planned packets

!!! info "Not implemented yet"
    The packets below are being designed with the server, and their layout is
    subject to change. They will get their own type number and layout table
    once implemented.

| Name | Direction | Purpose |
|---|---|---|
| `Connect` / `Accept` | client → server / server → client | Join a game, receive a player identifier |
| `Spawn` / `Destroy` | server → client | An entity (player, Bydo, missile) appears or is destroyed, with its kind |
| `Heartbeat` | both | Keeps the session alive, detects crashed clients |
| `Disconnect` | both | A player leaves, other clients are notified |

## 6. Security considerations

- Packets have a **fixed size** and are read into a fixed-size buffer: a
  datagram cannot make a peer read or allocate more than 24 bytes.
- The server is the **authority**: it never trusts a position or an event sent
  by a client, only its inputs.
- UDP source addresses can be spoofed: the planned `Connect` handshake will
  give each client an identifier that later packets must carry.
- A client that floods the server SHOULD be dropped (planned rate limiting).

## 7. Implementation notes

- The reference implementation is [Protecs](systems/protecs.md):
  `src/networking/Packet` (type byte and dispatch) and one folder per packet
  type in `src/networking/packets/`.
- The packet size is `sizeof(Protecs::Networking::Packets::PacketData)`, the
  variant of all packet types: 24 bytes on x86-64. Adding a larger packet type
  changes it, and this document must then be updated.
- The type byte is the index of the packet in that variant: reordering the
  variant changes the type numbers, and this document must then be updated.
- Fields are copied with `memcpy`, in host byte order. On every supported
  platform (x86-64 Linux and Windows) this is little-endian, as required by
  section 2.
- Unknown packet types raise a `Protecs::PacketError`, which the server logs
  before dropping the packet. The datagram size check of section 3 is not
  applied yet (see the [server page](systems/server.md#next-steps)).
