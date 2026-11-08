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
  src/game/DevOptions/          --help, --god, --speed, --start, --drop-rate
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
       to every player. Every second, every player is pinged; a player silent
       for 15 seconds (crashed client, lost connection) is removed, and the
       others get its `EntityDelete`.
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

# progression  type       y       movement  loot
120            pata-pata  80      sine
240            pata-pata  80      sine      life
280            pata-pata  random  straight  life:0.5
290            pow-armor  200     straight
```

`y` is the top of the enemy in world units (0 at the top of the screen), or
`random`: `StageSpawner` then draws a new height each time the enemy appears,
between 40 and 374, so that an enemy moving along a sine stays on screen. The
draw is seeded with the clock, so it changes in every game.

Types: `pata-pata` (shoots at random, drops a life with
`Rules::LIFE_DROP_CHANCE`, 0.1) and `pow-armor` (never shoots, always drops a
Force item). `loot` is optional and changes what the enemy drops when a player
kills it: `life` or `force` always drops that item, `life:<chance>` or
`force:<chance>` with a chance from 0 to 1, `none` nothing.

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
| `Swing` | `Swinging` | A part sweeping an arc around a point of its parent, like a tail segment |
| `Enrage` | `PhaseChange` | Once its health is low enough: `BossPhase` 2, bigger bursts, faster swinging parts |
| `Loot { item, chance }` | `Looting` | Killed by a player, it may drop a bonus (`Pickup`) where it was |
| `Pickup { item }` | `Collecting` | A bonus: the player who touches it, or whose shot touches it, takes it |
| `Force` | `ForceControl`, `ForceFire` | A player's Force: level, attached (front or back) or flying |
| `ContactDamage { damage, interval }` | `ContactHits` | Hurts the enemies it touches, at most every `interval` |
| `Shield` | `Shielding` | Destroys the enemy missiles it touches |

The **Dobkeratops** (stage 1 boss) is its weak point (`Boss`, 60 `Health`,
`AimedBursts` of 3 shots every 2 s, `StopAt`, `Enrage` at 20 HP) with an
`Armored` body and a tail of 10 `Armored` segments that `Swing` in a whip-like
arc, all attached to it. At 20 HP it gets angry: bursts of 5 shots every 1.5 s,
a tail 1.5 times faster. See [Contributing](../contributing.md#add-an-enemy-or-a-boss) to add one.

## Shooting and collisions

- **Charged shot** (R-Type's Wave Cannon): a tap fires a missile; holding the
  trigger charges one level per 0.4 s (up to 5, shared in `PlayerStats::charge`);
  releasing fires a beam of that level. A beam pierces what it kills, destroys
  enemy missiles, and stops on the first enemy that survives.
- A player touched by an enemy or an enemy missile loses a life and comes back
  at its start, invulnerable for 2 seconds; at 0 lives it is out, and the
  others play on.

## Bonuses

An enemy killed by a player (a shot, or ramming it) may drop its `Loot`:
`Collisions` records the kill in the requests, then `Looting` rolls the chance
and spawns a `PICKUP_LIFE` where the enemy was. The bonus drifts left with the
background (`Flight` removes it off screen). An enemy that leaves the screen, or
is cleared with its stage, drops nothing.

`Collecting` gives the bonus to the first player whose ship touches it, or
whose shot touches it (a missile stops on it, a beam goes through). A bonus
life adds one life, up to `Rules::MAX_LIVES` (10); a player who is out takes
nothing. Clients see the new `PlayerStats::lives`.

## The Force

R-Type's attachable pod. A POW Armor drops a Force item; taking it gives a
level 1 Force attached in front of the ship, the next ones levels 2 and 3
(a bigger Force, created again as `FORCE_2`, `FORCE_3`), then 1000 points.

- `ForceControl` keeps an attached Force at the front or the back of its ship.
  The force input launches it straight ahead (backwards from the back): it
  flies 250 units or to the screen edge, then floats there. Pressed again, it
  flies back. Touching its ship, launched or not, it attaches on the side it
  touches. A player who loses a life loses the Force.
- It is invulnerable: `Shielding` destroys the enemy missiles it touches, and
  `ContactHits` takes its level in hit points from the enemies it touches,
  every 0.2 s (armored parts take nothing). A kill is a kill: score to its
  player, and the enemy's loot drops. The shared `Game::damage` is used by
  `Collisions` too.
- `ForceFire`: attached, each missile its player fires comes with 1, 2 or 3
  missiles of the Force (levels 2 and 3 fan out), forward from the front,
  backward from the back.

## Command line

```text
USAGE: r-type_server [options]

Options:
  --help           display this help and exit

Developer options (to test a level, never on a real server):
  --god            players never lose a life
  --speed <n>      the level scrolls n times faster (0 < n <= 50)
  --start <n>      the level starts at progression n (pixels of the stage background)
  --drop-rate <p>  every enemy drops its bonus with chance p (0 <= p <= 1)
```

An unknown option or a bad value prints the error and the usage, and exits
with 84.
