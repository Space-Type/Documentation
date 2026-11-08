# Wrecks engine

**Wrecks** is our engine library, written in C++23 and shared by the client and
the server. It knows nothing about R-Type: it provides the building blocks
(ECS, events, utilities) that both programs use. Everything specific to
R-Type's network lives in [Protecs](protecs.md).

Repository: [Space-Type/Wrecks](https://github.com/Space-Type/Wrecks). Include
everything with `#include <wrecks.hpp>`, or one module with
`<wrecks/ecs.hpp>`, `<wrecks/events.hpp>`, `<wrecks/utils.hpp>`...

## ECS

The Entity-Component-System pattern separates **data** (components) from
**behavior** (systems):

- An **entity** is just an identifier (`Wrecks::ECS::Entity`, a 32-bit integer).
- A **component** is a plain struct attached to an entity (position, velocity,
  sprite...). Any movable type can be a component.
- A **system** runs on every entity that has a given set of components.

The engine is configured **at compile time** with the list of its systems and
components:

```cpp
struct Transform { float x; float y; };
struct Physics { float velocityX; float velocityY; };

using Components = Wrecks::ECS::ComponentManager<Transform, Physics>;

class Movement {
    void* m_Engine = nullptr;

    public:
        // Runs in engine.fixedUpdate(dt); systems of a stage run by increasing order
        static constexpr Wrecks::ECS::SystemAttributes ATTRIBUTES = {
            .stage = Wrecks::ECS::SystemAttributes::FIXED_UPDATE,
            .order = 10,
        };

        static constexpr Wrecks::Signature signature() noexcept
        {
            return Wrecks::Signature()
                .set(Components::index<Transform>())
                .set(Components::index<Physics>());
        }

        void setEngine(void* engine) noexcept { m_Engine = engine; }
        void operator()(Wrecks::ECS::Entity entity, Wrecks::DeltaTime dt);   // called for each matching entity
};

using Engine = Wrecks::ECS::Engine<std::tuple<Movement>, Components>;

Engine engine;
Wrecks::ECS::Entity ship = engine.createEntity();
engine.addComponent(ship, Transform{0.0F, 0.0F});
engine.addComponent(ship, Physics{1.0F, 0.0F});
engine.fixedUpdate(std::chrono::duration<double>(1.0 / 120.0));    // runs Movement on the ship
```

How it works:

- Each entity has a **signature**, a `std::bitset<64>` with one bit per
  component type (so at most 64 component types). A system declares the
  signature it needs, and the engine iterates over the entities whose
  signature matches.
- Each component type is stored in its own **packed array**
  (`ComponentContainer`), with hash maps between entities and indices. Walking
  over the components is cache-friendly; reaching the component of a given
  entity costs a hash map lookup ([measured](../technical-study.md#engine-architecture-ecs)).
- Deleted entity identifiers are **recycled** for new entities.
- Systems and components are resolved with templates and concepts: there is no
  virtual call and no runtime type lookup. A missing component or a system that
  does not meet the `System` concept is a **compile error**.
- Every system declares a **stage** and an **order** (`ATTRIBUTES`):
  `UPDATE` systems run in `engine.update(dt)` (once per frame),
  `FIXED_UPDATE` systems in `engine.fixedUpdate(dt)` (at the fixed simulation
  rate) and `RENDER` systems in `engine.render(dt)`. Within a stage, systems
  are sorted by order at compile time.

## Events

`Wrecks::Events::EventManager` is a simple publish/subscribe mechanism:
receivers subscribe to the manager, and `sendEvent()` forwards an event to
every subscriber. Events are a `std::variant` of event types, so adding an
event type is checked at compile time.

## Utilities

- `Wrecks::Utils::SequenceContainer<T, N>` is a fixed-size ring buffer indexed
  by game tick, meant for client-side prediction and server reconciliation
  (replaying inputs since a given tick).
- Type-list helpers (`IndexOf`, `ElementIndex`, `ContainsType`) and filtered
  iterators, used by the ECS to resolve components at compile time.

The networking module that Wrecks used to provide (`UDPSocket`, `Address`)
moved to [Protecs](protecs.md), so Wrecks stays independent from the game.

## Errors

Every error thrown by Wrecks derives from `Wrecks::Error`, so callers can catch
them all at once.

## Tests

```sh
cmake -DCMAKE_BUILD_TYPE=DebugTests -S . -B build
cmake --build build --parallel
ctest --test-dir build --output-on-failure
./coverage.sh    # build, test and coverage report (gcovr)
```

The tests run on Linux and Windows on every push to `main` (GitHub Actions).
