# Server

`r-type_server` runs the game and is the authority on everything that happens
in it: positions, shots, hits, scores, lives, stages. Repository:
[Space-Type/Server](https://github.com/Space-Type/Server).

## Layout

```text
Server/
  src/main.cpp                  entry point: command line, then Server::Builder
  src/game/Server/              socket, receive thread, main loop
  src/game/Game/                Game: ECS engine, players, level, network updates
  src/game/Requests/            entities the systems ask to create or delete
  src/game/Blueprints/          enemies and bosses as lists of components
  src/game/Waves/               stage files: parsing and loading
  src/game/DevOptions/          --help, --god, --speed, --start
  src/game/Rules.hpp            gameplay constants (speeds, sizes, lives...)
  src/components/               server-only components
  src/systems/                  server systems, listed in Tuple.hpp
  src/utils/Logger/             logger
  assets/stages/                stage-<n>.waves
  lib/wrecks, lib/protecs       submodules: engine and shared protocol
```

## Main loop

- `Server::run()` starts a **receive thread** that waits for datagrams
  (`pollReceive` with a 1 second timeout, so it never blocks forever) and pushes
  each one, with its sender address, into a thread-safe `PacketQueue`.
- The **main thread** sends the packets produced by the game, then calls
  `Game::update(dt)`:
    1. Packets up to the current tick are decoded and handled. A packet that
       cannot be decoded is logged and dropped. Only `PlayerJoin` is accepted
       from an unknown address.
    2. The simulation runs **120 fixed ticks per second** (`fixedUpdate`), then
       applies the systems' requests (entities to create and delete).
    3. **20 times per second**, every shared component of every entity is sent
       to every player.
- Ctrl+C is caught: the server closes its socket and shuts down cleanly.

See the [architecture](../architecture.md#a-tick-on-the-server) for the order of
the systems, and the [protocol](../protocol.md) for the packets.

## Players and the level

- A player is an entity with a `Player` component (address, name), created on
  `PlayerJoin`. It gets the shared components of a ship (`Transform`,
  `Velocity`, `PlayerInput`, `PlayerName`, `PlayerStats` with the first free
  slot `0` to `3`) and a server-only `Body` (hitbox).
- Inputs (`PlayerInput` packets) go to the player's `InputBuffer` (50 at most)
  and are applied at their tick.
- The **level** is an entity created when the first player joins, with the
  shared `Level` (stage, progression, won) and the server-only `LevelState`.
  When the last player leaves, the level and everything left are deleted: the
  next player starts over.

## Stages

A stage is a text file, `assets/stages/stage-<n>.waves`, loaded at start-up for
every `n` from 1 until a file is missing:

```text
length 3797          # progression where the scrolling stops (pixels of stage-<n>.png)
boss   dobkeratops   # blueprint of the boss; without it, the stage ends at its length

# progression  type       y    movement
120            pata-pata  80   sine
```

1. `Scrolling` advances `Level::progression` (30 background pixels per second)
   up to `length`.
2. `StageSpawner` creates each wave when the level reaches it, then the boss.
3. `BossDefeat` clears the stage when the boss's weak point dies: enemies and
   enemy missiles go away.
4. `StageTransition` waits 4 seconds ("STAGE CLEAR" on the clients), then
   starts stage `n + 1`, or sets `Level::won` after the last stage.

Files are at most 64 KiB; an invalid line is logged with its number and
skipped, so a broken file never stops the server.

## Enemies and bosses

Gameplay is made of **behaviour components** run by generic systems, so an
enemy or a boss is a **blueprint** (`src/game/Blueprints`), not a class:

| Component | System | Behaviour |
|---|---|---|
| `Body` | `Flight`, `Collisions` | Hitbox, velocity, flight pattern (straight or sine) |
| `Enemy { reward }` | `Collisions` | Hit by player shots, hurts players, points for the killer |
| `Health` (shared) | `Collisions` | Hit points; a missile deals 1, a beam 2 to 6 |
| `Armored` | `Collisions` | Absorbs shots without damage |
| `StopAt { x }` | `Flight` | Enters from the right, then stays at `x` |
| `RandomShots` | `Shooting` | Fires a missile at random intervals |
| `AimedBursts` | `BurstFire` | Fires bursts at the nearest player, once stopped |
| `Attached { parent }` | `Attachment` | A part follows its parent and dies with it |
| `Boss` | `BossDefeat` | Its death clears the stage |

The **Dobkeratops** (stage 1 boss) is its weak point (`Boss`, 60 `Health`,
`AimedBursts` of 3 shots every 2 s, `StopAt`) with an `Armored` body attached
to it. See [Contributing](../contributing.md#add-an-enemy-or-a-boss) to add one.

## Shooting and collisions

- **Charged shot** (R-Type's Wave Cannon): a tap fires a missile; holding the
  trigger charges one level per 0.4 s (up to 5, shared in `PlayerStats::charge`);
  releasing fires a beam of that level. A beam pierces what it kills, destroys
  enemy missiles, and stops on the first enemy that survives.
- A player touched by an enemy or an enemy missile loses a life and comes back
  at its start, invulnerable for 2 seconds; at 0 lives it is out, and the
  others play on.

## Command line

```text
USAGE: r-type_server [options]

Options:
  --help           display this help and exit

Developer options (to test a level, never on a real server):
  --god            players never lose a life
  --speed <n>      the level scrolls n times faster (0 < n <= 50)
  --start <n>      the level starts at progression n (pixels of the stage background)
```

An unknown option or a bad value prints the error and the usage, and exits
with 84.

## Known gaps

Listed with their planned fixes in the
[protocol](../protocol.md#known-gaps-of-the-reference-implementation): no
timeout for a crashed client, no limit of 4 players, unfiltered names.
