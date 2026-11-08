/*
** EPITECH PROJECT, 2026
** Project - Documentation
** File description:
** Implementation for
** the local benchmarks (no server)
*/

#include "Bench.hpp"
#include <protecs.hpp>
#include <wrecks/ecs.hpp>
#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <queue>
#include <random>
#include <tuple>
#include <utility>
#include <vector>


namespace {
    namespace Packets = Protecs::Networking::Packets;
    namespace Components = Protecs::Components;
    using Protecs::Networking::Packet;

    constexpr std::size_t RAW_SIZE = std::tuple_size_v<decltype(Packet::raw)>;

    // As many entities as the server puts in one EntityList packet (Server: ENTITY_LIST_MAX)
    constexpr std::size_t ENTITY_LIST_MAX = (RAW_SIZE - 1 - Packets::EntityList::partialPackedSize())
                                          / (sizeof(Protecs::NetworkEntity) + sizeof(Protecs::Signature));

    Packets::EntityComponentData transformData(Protecs::Tick tick)
    {
        return {
            .simulationTick = tick,
            .entity = 42,
            .component = Components::Transform{ .position = { 123.5F, 67.25F }, .rotation = 0.0F, .scale = 1.0F },
        };
    }
}


void Bench::packetSizes()
{
    Packets::EntityList fullList = { .simulationTick = 1, .entities = {} };

    for (std::size_t i = 0; i < ENTITY_LIST_MAX; ++i)
        fullList.entities.emplace_back(i, Protecs::Signature().set(5));

    auto component = [](const char* name, Components::Variant value) {
        return std::pair<std::string, Packets::PacketData>{
            std::string("EntityComponentData (") + name + ")",
            Packets::EntityComponentData{ .simulationTick = 1, .entity = 1, .component = value },
        };
    };

    std::vector<std::pair<std::string, Packets::PacketData>> samples = {
        { "EntityCreate", Packets::EntityCreate{ .simulationTick = 1, .id = 1, .type = Packets::EntityCreate::PLAYER } },
        { "EntityDelete", Packets::EntityDelete{ .simulationTick = 1, .id = 1 } },
        { "EntityList (1 entity)", Packets::EntityList{ .simulationTick = 1, .entities = { { 1, Protecs::Signature().set(5) } } } },
        { "EntityList (" + std::to_string(ENTITY_LIST_MAX) + " entities, the most per packet)", fullList },
        { "EntityRemoveComponent", Packets::EntityRemoveComponent{ .simulationTick = 1, .entity = 1, .type = 2 } },
        { "EntitySyncComponents", Packets::EntitySyncComponents{ .simulationTick = 1, .entity = 1, .signature = {} } },
        { "Ping", Packets::Ping{} },
        { "PlayerId", Packets::PlayerId{ .id = 1 } },
        { "PlayerInput", Packets::PlayerInput{ .simulationTick = 1, .sequence = 0, .input = Packets::PlayerInput::UP, .state = Packets::PlayerInput::HOLD_DOWN } },
        { "PlayerJoin (5-character name)", Packets::PlayerJoin::fromStr("alice") },
        { "PlayerJoin (32-character name, the longest)", Packets::PlayerJoin::fromStr(std::string(32, 'a')) },
        { "PlayerLeave", Packets::PlayerLeave{} },
        { "TickSync", Packets::TickSync{} },
        component("Level", Components::Level{ .progression = 1, .stage = 1 }),
        component("Movement", Components::Movement{}),
        component("PathFinding", Components::PathFinding{}),
        component("PlayerInput", Components::PlayerInput{}),
        component("PlayerStats", Components::PlayerStats{}),
        component("Transform", Components::Transform{}),
        component("Velocity", Components::Velocity{}),
        component("PlayerName, 5 characters", Components::PlayerName::fromStr("alice")),
        component("Health", Components::Health{}),
    };

    std::cout << "| Packet | Bytes on the wire |\n|---|---|\n";
    for (const auto& [name, data] : samples)
        std::cout << "| " << name << " | " << Packet::serialize(data).filled << " |\n";
    std::cout << "\nReceive buffer (largest datagram read): " << RAW_SIZE << " bytes\n";
}

/**
 * Our binary encoding of a Transform update against the
 * same values written as text (what a JSON- or text-based
 * protocol would send), both ways.
 */
void Bench::serialization()
{
    constexpr std::size_t ITERATIONS = 2'000'000;

    auto data = transformData(1000);
    Packet packet = Packet::serialize(data);
    double binaryOut = nanoseconds(ITERATIONS, [&](std::size_t i) {
        data.simulationTick = static_cast<Protecs::Tick>(i);
        keep(Packet::serialize(data).filled);
    });
    double binaryIn = nanoseconds(ITERATIONS, [&](std::size_t) {
        keep(std::get<Packets::EntityComponentData>(packet.deserialize()).simulationTick);
    });

    char text[128];
    auto writeText = [&](std::size_t i) {
        return std::snprintf(text, sizeof(text), "{\"type\":\"component\",\"tick\":%zu,\"entity\":42,\"transform\":[%.9g,%.9g,%.9g,%.9g]}",
                             i, 123.5, 67.25, 0.0, 1.0);
    };
    int textSize = writeText(1000);
    double textOut = nanoseconds(ITERATIONS, [&](std::size_t i) { keep(writeText(i)); });
    double textIn = nanoseconds(ITERATIONS, [&](std::size_t) {
        unsigned long tick = 0;
        unsigned long long entity = 0;
        float x = 0, y = 0, rotation = 0, scale = 0;

        keep(std::sscanf(text, "{\"type\":\"component\",\"tick\":%lu,\"entity\":%llu,\"transform\":[%f,%f,%f,%f]}",
                         &tick, &entity, &x, &y, &rotation, &scale));
    });

    std::cout << "| Encoding of one Transform update | Bytes | Encode (ns) | Decode (ns) |\n|---|---|---|---|\n";
    std::cout << "| Protecs binary | " << packet.filled << " | " << binaryOut << " | " << binaryIn << " |\n";
    std::cout << "| Text (JSON-like, snprintf / sscanf) | " << textSize << " | " << textOut << " | " << textIn << " |\n";
}

/**
 * PacketQueue sorts the packets by simulation tick, and
 * deserializes them to compare two of them. Measured
 * against a priority queue that reads the tick once.
 */
void Bench::packetQueue()
{
    std::mt19937 random(7);

    std::cout << "| Packets queued | PacketQueue (ns per packet) | Tick read once, std::priority_queue (ns per packet) |\n|---|---|---|\n";
    for (std::size_t count : { 16U, 64U, 256U, 1024U }) {
        std::vector<Packet> packets;

        for (std::size_t i = 0; i < count; ++i)
            packets.push_back(Packet::serialize(transformData(random() % 1000)));

        constexpr std::size_t ROUNDS = 50;
        Protecs::Networking::Address address = Protecs::Networking::Address::construct("127.0.0.1", 1);

        double queue = nanoseconds(ROUNDS, [&](std::size_t) {
            Protecs::Networking::PacketQueue queue;

            for (const auto& packet : packets)
                queue.push(address, packet);
            while (auto element = queue.pop(UINT32_MAX))
                keep(element->second.filled);
        }) / static_cast<double>(count);

        double simple = nanoseconds(ROUNDS, [&](std::size_t) {
            using Element = std::pair<Protecs::Tick, std::size_t>;
            std::priority_queue<Element, std::vector<Element>, std::greater<>> queue;

            for (std::size_t i = 0; i < packets.size(); ++i)
                queue.emplace(std::get<Packets::EntityComponentData>(packets[i].deserialize()).simulationTick, i);
            while (!queue.empty()) {
                keep(packets[queue.top().second].filled);
                queue.pop();
            }
        }) / static_cast<double>(count);

        std::cout << "| " << count << " | " << queue << " | " << simple << " |\n";
    }
}


namespace {
    // The object-oriented alternative to an ECS: one heap object per entity, a virtual update
    struct GameObject {
        virtual ~GameObject() = default;
        virtual void update() = 0;
    };

    struct Mover : GameObject {
        Components::Transform transform{};
        Components::Velocity velocity{};

        void update() override
        {
            // Same work as Protecs::Systems::Motion
            transform.position += velocity.position;
            velocity.position.x *= 0.95F;
            velocity.position.y *= 0.95F;
        }
    };

    using Engine = Wrecks::ECS::Engine<Protecs::Systems::Tuple, Components::Manager>;
}

/**
 * One fixed update of the shared Motion system on N moving
 * entities, against the same work done by N heap objects
 * with a virtual update.
 */
void Bench::ecs()
{
    std::cout << "| Moving entities | Wrecks ECS, Motion system (µs per update) | Objects + virtual update (µs per update) |\n|---|---|---|\n";
    for (std::size_t count : { 100U, 1000U, 10000U }) {
        constexpr std::size_t UPDATES = 2000;
        auto engine = std::make_unique<Engine>();
        std::vector<std::unique_ptr<GameObject>> objects;

        for (std::size_t i = 0; i < count; ++i) {
            auto entity = engine->createEntity();

            engine->addComponent(entity, Components::Transform{ .position = { 1.0F, 2.0F }, .rotation = 0.0F, .scale = 1.0F });
            engine->addComponent(entity, Components::Velocity{ .position = { 1000.0F, 1000.0F }, .angular = 0.0F });

            auto object = std::make_unique<Mover>();
            object->velocity.position = { 1000.0F, 1000.0F };
            objects.push_back(std::move(object));
        }

        double ecsTime = nanoseconds(UPDATES, [&](std::size_t) { engine->fixedUpdate(Protecs::FIXED_UPDATE_RATE); }) / 1000.0;
        double objectTime = nanoseconds(UPDATES, [&](std::size_t) {
            for (auto& object : objects)
                object->update();
        }) / 1000.0;

        keep(static_cast<std::uint64_t>(static_cast<Mover&>(*objects[0]).transform.position.x));
        std::cout << "| " << count << " | " << ecsTime << " | " << objectTime << " |\n";
    }
}
