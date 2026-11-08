/*
** EPITECH PROJECT, 2026
** Project - Documentation
** File description:
** Implementation for
** the benchmarks against a running server
*/

#include "Bench.hpp"
#include <protecs.hpp>
#include <algorithm>
#include <fstream>
#include <iostream>
#include <map>
#include <optional>
#include <random>
#include <stdexcept>
#include <thread>
#include <unordered_map>


namespace {
    namespace Packets = Protecs::Networking::Packets;
    using Protecs::Networking::Address;
    using Protecs::Networking::Packet;
    using Protecs::Networking::UDPSocket;
    using Clock = std::chrono::steady_clock;

    // A player as the protocol sees it: a socket that joined the game
    class Connection {
        UDPSocket m_Socket;
        Address m_Server;

        public:
            Connection(const std::string& host, std::uint16_t port)
                : m_Socket("0.0.0.0", 0)
                , m_Server(Address::construct(host, port))
            {
            }

            ~Connection() { send(Packets::PlayerLeave{}); }

            void send(Packets::PacketData&& data) { m_Socket.send(Packet::serialize(data), m_Server); }

            void sendRaw(const std::uint8_t* bytes, std::size_t size)
            {
                Packet packet = {};

                size = std::min(size, packet.raw.size());
                std::copy_n(bytes, size, packet.raw.begin());
                packet.filled = size;
                m_Socket.send(packet, m_Server);
            }

            // The next datagram within `timeoutMs`, if any. A Ping is answered, as a client must
            std::optional<Packet> receive(int timeoutMs)
            {
                if (!m_Socket.pollReceive(timeoutMs))
                    return std::nullopt;

                Packet packet = {};

                m_Socket.receive(packet);
                try {
                    if (std::holds_alternative<Packets::Ping>(packet.deserialize()))
                        send(Packets::Ping{});
                } catch (const std::exception&) {
                }
                return packet;
            }

            // Joins as `name`: true once the server answered with a PlayerId
            bool join(const std::string& name, std::chrono::milliseconds timeout = std::chrono::seconds(3))
            {
                auto deadline = Clock::now() + timeout;

                send(Packets::PlayerJoin::fromStr(name));
                while (Clock::now() < deadline) {
                    auto packet = receive(100);

                    if (!packet)
                        continue;
                    try {
                        if (std::holds_alternative<Packets::PlayerId>(packet->deserialize()))
                            return true;
                    } catch (const std::exception&) {
                    }
                }
                return false;
            }
    };

    std::string_view packetName(const Packets::PacketData& data)
    {
        return std::visit([](const auto& packet) { return std::decay_t<decltype(packet)>::packetName(); }, data);
    }

    double secondsSince(Clock::time_point start)
    {
        return std::chrono::duration<double>(Clock::now() - start).count();
    }

    /**
     * The entities a client believes exist, as the real client
     * learns them: EntityCreate, EntityDelete, EntityList, and
     * an EntityList request for data about an unknown entity.
     */
    struct EntityTracker {
        std::unordered_map<Protecs::NetworkEntity, Clock::time_point> lastUpdate;

        // Returns true when the client would ask for the entity list
        bool handle(const Packets::PacketData& data)
        {
            auto now = Clock::now();

            if (auto* create = std::get_if<Packets::EntityCreate>(&data))
                lastUpdate[create->id] = now;
            else if (auto* remove = std::get_if<Packets::EntityDelete>(&data))
                lastUpdate.erase(remove->id);
            else if (auto* list = std::get_if<Packets::EntityList>(&data))
                for (const auto& [id, signature] : list->entities)
                    lastUpdate[id] = now;
            else if (auto* component = std::get_if<Packets::EntityComponentData>(&data)) {
                auto it = lastUpdate.find(component->entity);

                if (it == lastUpdate.end())
                    return true;
                it->second = now;
            }
            return false;
        }

        // Entities known, optionally only those updated within the last second (client: Freshness)
        bool knows(Protecs::NetworkEntity id, bool fresh) const
        {
            auto it = lastUpdate.find(id);

            return it != lastUpdate.end() && (!fresh || Clock::now() - it->second <= std::chrono::seconds(1));
        }
    };

    std::size_t residentKiB(int pid)
    {
        std::ifstream status("/proc/" + std::to_string(pid) + "/status");
        std::string key;

        while (status >> key) {
            std::size_t value = 0;

            if (key == "VmRSS:" && status >> value)
                return value;
        }
        return 0;
    }
}


/**
 * What one client receives from the server, by packet type,
 * while it plays (the server sends the same to every client).
 */
void Bench::bandwidth(const std::string& host, std::uint16_t port, int seconds)
{
    Connection client(host, port);

    if (!client.join("bandwidth"))
        throw std::runtime_error("no answer from the server");

    std::map<std::string_view, std::pair<std::size_t, std::size_t>> byType;  // packets, bytes
    EntityTracker tracker;
    std::size_t samples = 0;
    std::size_t entitySum = 0;
    std::size_t entityMax = 0;
    auto start = Clock::now();
    auto nextSample = start;

    while (secondsSince(start) < seconds) {
        if (auto packet = client.receive(10)) {
            try {
                auto data = packet->deserialize();
                auto& [count, bytes] = byType[packetName(data)];

                ++count;
                bytes += packet->filled;
                if (tracker.handle(data))
                    client.send(Packets::EntityList{});
            } catch (const std::exception&) {
            }
        }
        if (Clock::now() >= nextSample) {
            nextSample += std::chrono::milliseconds(100);
            ++samples;
            entitySum += tracker.lastUpdate.size();
            entityMax = std::max(entityMax, tracker.lastUpdate.size());
        }
    }

    std::size_t totalPackets = 0;
    std::size_t totalBytes = 0;

    for (const auto& [name, value] : byType) {
        totalPackets += value.first;
        totalBytes += value.second;
    }

    std::cout << "Entities known by the client: " << static_cast<double>(entitySum) / static_cast<double>(samples)
              << " on average, " << entityMax << " at most\n\n";
    std::cout << "| Packet | Packets/s | Bytes/s | Share of the bytes |\n|---|---|---|---|\n";
    for (const auto& [name, value] : byType)
        std::cout << "| " << name << " | " << static_cast<double>(value.first) / seconds << " | "
                  << static_cast<double>(value.second) / seconds << " | "
                  << 100.0 * static_cast<double>(value.second) / static_cast<double>(totalBytes) << " % |\n";
    std::cout << "| **Total** | " << static_cast<double>(totalPackets) / seconds << " | "
              << static_cast<double>(totalBytes) / seconds << " | 100 % |\n";
}

/**
 * Two clients play at the same time: one receives every
 * datagram, the other drops `percent` % of them (as on a
 * lossy link). Compares what they believe exists, with
 * and without the client rule that forgets an entity the
 * server stopped updating for a second (Freshness).
 */
void Bench::loss(const std::string& host, std::uint16_t port, int seconds, double percent)
{
    Connection reference(host, port);
    Connection lossy(host, port);

    if (!reference.join("reference") || !lossy.join("lossy"))
        throw std::runtime_error("no answer from the server");

    std::mt19937 random(11);
    std::bernoulli_distribution drop(percent / 100.0);
    EntityTracker referenceTracker;
    EntityTracker lossyTracker;
    std::size_t received = 0;
    std::size_t dropped = 0;
    double samples = 0;
    double ghosts = 0;
    double ghostsFresh = 0;
    double missing = 0;
    double entities = 0;
    auto start = Clock::now();
    auto nextSample = start + std::chrono::seconds(2);  // both clients got their first entity list

    auto pump = [](Connection& connection, EntityTracker& tracker, auto&& keep) {
        while (auto packet = connection.receive(0)) {
            if (!keep())
                continue;
            try {
                if (tracker.handle(packet->deserialize()))
                    connection.send(Packets::EntityList{});
            } catch (const std::exception&) {
            }
        }
    };

    while (secondsSince(start) < seconds) {
        pump(reference, referenceTracker, [] { return true; });
        pump(lossy, lossyTracker, [&] {
            bool lost = drop(random);

            (lost ? dropped : received)++;
            return !lost;
        });
        std::this_thread::sleep_for(std::chrono::milliseconds(2));

        if (Clock::now() < nextSample)
            continue;
        nextSample += std::chrono::milliseconds(100);
        ++samples;
        entities += static_cast<double>(referenceTracker.lastUpdate.size());
        for (const auto& [id, time] : lossyTracker.lastUpdate) {
            ghosts += !referenceTracker.knows(id, false);
            ghostsFresh += lossyTracker.knows(id, true) && !referenceTracker.knows(id, false);
        }
        for (const auto& [id, time] : referenceTracker.lastUpdate)
            missing += !lossyTracker.knows(id, false);
    }

    std::cout << "| " << percent << " % | " << 100.0 * static_cast<double>(dropped) / static_cast<double>(dropped + received)
              << " % | " << entities / samples << " | " << missing / samples << " | " << ghosts / samples
              << " | " << ghostsFresh / samples << " |\n";
}

/**
 * Sends `count` malformed datagrams of several kinds, from a
 * stranger and from a joined player, then checks that the
 * server still answers a new player. With the server pid,
 * also reports its memory before and after (Linux).
 */
void Bench::fuzz(const std::string& host, std::uint16_t port, int count)
{
    const char* pidText = std::getenv("SERVER_PID");
    int pid = pidText ? std::atoi(pidText) : 0;
    std::size_t memoryBefore = pid ? residentKiB(pid) : 0;
    Connection stranger(host, port);
    Connection player(host, port);

    if (!player.join("fuzzer"))
        throw std::runtime_error("no answer from the server");

    std::mt19937 random(3);
    std::uniform_int_distribution<int> byte(0, 255);
    std::uniform_int_distribution<int> kind(0, 4);
    std::vector<std::uint8_t> datagram;
    auto start = Clock::now();

    for (int i = 0; i < count; ++i) {
        std::size_t size = std::uniform_int_distribution<std::size_t>(0, 512)(random);

        datagram.assign(size, 0);
        for (auto& value : datagram)
            value = static_cast<std::uint8_t>(byte(random));
        switch (kind(random)) {
            case 0:  // random bytes, any size
                break;
            case 1:  // a known packet type with a random payload
                if (!datagram.empty())
                    datagram[0] %= std::variant_size_v<Packets::PacketData>;
                break;
            case 2:  // EntityList announcing more entities than the datagram holds
                datagram.assign({ 3, 0, 0, 0, 0, 0xFF, 0xFF, 0xFF, 0xFF });
                break;
            case 3:  // PlayerJoin with a name length of 255
                datagram.assign({ 9, 255, 'a', 'b' });
                break;
            default:  // EntityComponentData with an unknown component type
                datagram.assign({ 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0xFF, 0xFF, 1, 2, 3 });
                break;
        }
        (i % 2 ? player : stranger).sendRaw(datagram.data(), datagram.size());
        player.receive(0);
        if (i % 20 == 19)  // ~20 000 datagrams per second: the socket buffers do not overflow, the server gets them
            std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }

    double sendSeconds = secondsSince(start);
    std::this_thread::sleep_for(std::chrono::seconds(1));

    auto joinStart = Clock::now();
    Connection newcomer(host, port);
    bool answered = newcomer.join("after-fuzz", std::chrono::seconds(10));
    double joinMs = secondsSince(joinStart) * 1000.0;

    std::cout << "| Malformed datagrams | Sent in | Server answers a new player | Join time | Server memory before → after |\n|---|---|---|---|---|\n";
    std::cout << "| " << count << " | " << sendSeconds << " s | " << (answered ? "yes" : "**no**") << " | " << joinMs << " ms | ";
    if (pid)
        std::cout << memoryBefore << " KiB → " << residentKiB(pid) << " KiB |\n";
    else
        std::cout << "(set SERVER_PID) |\n";
}
