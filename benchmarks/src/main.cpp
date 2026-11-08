/*
** EPITECH PROJECT, 2026
** Project - Documentation
** File description:
** Entry point of
** the benchmarks of the technical study
*/

#include "Bench.hpp"
#include <exception>
#include <iostream>
#include <string>


static constexpr const char* USAGE =
    "USAGE: rtype_bench <benchmark> [host port ...]\n"
    "\n"
    "Local benchmarks:\n"
    "  sizes                         bytes on the wire of every packet\n"
    "  serialization                 binary against text encoding\n"
    "  queue                         PacketQueue against a simple priority queue\n"
    "  ecs                           Wrecks ECS against objects with a virtual update\n"
    "\n"
    "Against a running r-type_server:\n"
    "  bandwidth <host> <port> <s>   what one client receives, by packet type\n"
    "  loss <host> <port> <s> <%>    a client dropping <%> of its datagrams against a lossless one\n"
    "  fuzz <host> <port> <n>        <n> malformed datagrams, then a new player joins\n"
    "                                (SERVER_PID=<pid> also reports the server memory)\n";

int main(int argc, char** argv)
{
    std::string name = argc > 1 ? argv[1] : "";

    try {
        if (name == "sizes")
            Bench::packetSizes();
        else if (name == "serialization")
            Bench::serialization();
        else if (name == "queue")
            Bench::packetQueue();
        else if (name == "ecs")
            Bench::ecs();
        else if (name == "bandwidth" && argc == 5)
            Bench::bandwidth(argv[2], static_cast<std::uint16_t>(std::stoi(argv[3])), std::stoi(argv[4]));
        else if (name == "loss" && argc == 6)
            Bench::loss(argv[2], static_cast<std::uint16_t>(std::stoi(argv[3])), std::stoi(argv[4]), std::stod(argv[5]));
        else if (name == "fuzz" && argc == 5)
            Bench::fuzz(argv[2], static_cast<std::uint16_t>(std::stoi(argv[3])), std::stoi(argv[4]));
        else {
            std::cerr << USAGE;
            return name == "--help" ? 0 : 84;
        }
    } catch (const std::exception& err) {
        std::cerr << "rtype_bench: " << err.what() << std::endl;
        return 84;
    }
    return 0;
}
