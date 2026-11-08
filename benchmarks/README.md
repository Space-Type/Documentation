# Benchmarks of the technical study

`rtype_bench` measures the numbers quoted in the
[technical study](../docs/technical-study.md): packet sizes, encoding speed,
the packet queue, the ECS, and the network behaviour against a real server.
Every benchmark prints a Markdown table.

## Build

```sh
git submodule update --init --recursive      # Protecs, and Wrecks inside it
cmake -S benchmarks -B benchmarks/build -DCMAKE_BUILD_TYPE=Release
cmake --build benchmarks/build
```

`benchmarks/lib/protecs` is pinned to the Protecs version the study was measured with.

## Run

```sh
./benchmarks/build/rtype_bench sizes            # bytes on the wire of every packet
./benchmarks/build/rtype_bench serialization    # binary against text encoding
./benchmarks/build/rtype_bench queue            # PacketQueue against a simple priority queue
./benchmarks/build/rtype_bench ecs              # Wrecks ECS against objects with a virtual update
```

The network benchmarks need a running server (`r-type_server --god`, so the
test players never lose):

```sh
./benchmarks/build/rtype_bench bandwidth 127.0.0.1 5432 60     # what one client receives, 60 s
./benchmarks/build/rtype_bench loss 127.0.0.1 5432 40 10       # a client losing 10 % of its datagrams
SERVER_PID=$(pgrep r-type_server) ./benchmarks/build/rtype_bench fuzz 127.0.0.1 5432 100000
```

`loss` drops the datagrams inside the benchmark (no root rights needed), on the
way from the server to the client. To degrade the real link instead, as the
subject's appendix suggests, `netem.sh` runs the server and the bandwidth
benchmark under three conditions (normal; 150 ms delay with 2 % loss and 2 %
duplication; the same limited to 5 kB/s). Only `tc` runs as root:

```sh
benchmarks/netem.sh ../Server/build/r-type_server         # optional: CLIENT_CMD="./r-type_client"
```

By hand:

```sh
sudo tc qdisc add dev lo root netem delay 150ms 20ms loss 2% duplicate 2%
sudo tc qdisc del dev lo root                                  # back to normal
```
