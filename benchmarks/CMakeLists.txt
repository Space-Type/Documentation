##
## EPITECH PROJECT, 2026
## Project - Documentation
## File description:
## Build file of the benchmarks
## of the technical study
##

cmake_minimum_required(VERSION 3.15)

project(RType-Benchmarks LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 23)

if (NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# Protecs brings Wrecks (its own submodule)
add_subdirectory(lib/protecs)

add_executable(rtype_bench
    src/main.cpp
    src/Bench.hpp
    src/Local.cpp
    src/Network.cpp)

target_include_directories(rtype_bench PRIVATE lib/protecs/include
                                       PRIVATE lib/protecs/lib/wrecks/include)

target_link_libraries(rtype_bench PRIVATE protecs wrecks)

if (WIN32)
    target_compile_definitions(rtype_bench PRIVATE WIN32_LEAN_AND_MEAN NOMINMAX NOGDI)
endif()
