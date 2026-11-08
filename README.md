# R-Type Documentation

Developer documentation of the [R-Type](https://github.com/Space-Type/R-Type)
project: architecture, systems, network protocol, technical study and
accessibility.

Published at **https://space-type.github.io/Documentation/** on every push to
`main`.

## Preview locally

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/mkdocs serve    # http://127.0.0.1:8000
```

Pages are Markdown files in `docs/`, listed in the `nav` section of
`mkdocs.yml`. The CI builds the site with `mkdocs build --strict`, so broken
links fail the build.

## Benchmarks

`benchmarks/` holds `rtype_bench`, the program that measures the numbers of the
technical study (packet sizes, encoding, ECS, bandwidth, packet loss,
malformed packets). See [benchmarks/README.md](benchmarks/README.md).
