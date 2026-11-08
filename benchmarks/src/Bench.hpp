/*
** EPITECH PROJECT, 2026
** Project - Documentation
** File description:
** Header file for
** the benchmarks of the technical study
*/

#pragma once

#include <chrono>
#include <cstdint>
#include <string>


/**
 * Measurements quoted in the technical study. Every
 * function prints a Markdown table, so its output can
 * be pasted in the documentation as is.
 */
namespace Bench {
    // Local: no server needed
    void packetSizes();
    void serialization();
    void packetQueue();
    void ecs();

    // Against a running r-type_server
    void bandwidth(const std::string& host, std::uint16_t port, int seconds);
    void loss(const std::string& host, std::uint16_t port, int seconds, double percent);
    void fuzz(const std::string& host, std::uint16_t port, int count);

    // Average nanoseconds per call of `fn`, run `iterations` times
    template <typename Fn>
    double nanoseconds(std::size_t iterations, Fn&& fn)
    {
        auto start = std::chrono::steady_clock::now();

        for (std::size_t i = 0; i < iterations; ++i)
            fn(i);

        std::chrono::duration<double, std::nano> elapsed = std::chrono::steady_clock::now() - start;

        return elapsed.count() / static_cast<double>(iterations);
    }

    // Keeps the compiler from removing a computation whose result is unused (portable: no inline asm)
    inline volatile std::uint64_t sink = 0;

    template <typename T>
    inline void keep(T value)
    {
        sink = sink + static_cast<std::uint64_t>(value);
    }
}
