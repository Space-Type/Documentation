# Contributing

The full rules are in
[CONTRIBUTING.md](https://github.com/Space-Type/R-Type/blob/main/CONTRIBUTING.md).
In short:

## Workflow

1. Every task is an **issue** in the
   [project board](https://github.com/orgs/Space-Type/projects/1), with a clear
   title, acceptance criteria, a priority and a MoSCoW rank (Must, Should,
   Could).
2. Work happens on a **short-lived branch** named
   `<type>/<scope>/<topic>`, for example `feat/server/broadcast` or
   `fix/render/animations`.
3. Changes are merged into `main` through a **pull request** that closes its
   issue (`Closes #12`). `main` must always build and stay deployable.
4. Every pull request needs **one approval** from another team member. Approving
   your own pull request is forbidden, and reviews are done within 48 hours.

## Commits

Commit messages follow the Angular convention:

```
<type>(<scope>): <description>

feat(server): broadcast entity positions
fix(render): replace the friend Renderer with an opaque accessor
docs(protocol): describe the EntityPosition packet
```

Common types: `feat`, `fix`, `docs`, `test`, `refactor`, `build`, `ci`.

## Code style

- C++23, 4-space indentation, `#pragma once`, the Epitech header on every file.
- `PascalCase` for types, `camelCase` for functions, `m_` prefix for members,
  `UPPER_CASE` for constants.
- One class per folder: `src/<module>/<Class>/<Class>.{hpp,cpp}`.
- Prefer concepts and templates over virtual functions, and `noexcept` where it
  applies.
- Code, comments and documentation are written in **English**.

## Updating this documentation

Pages are Markdown files in the `docs/` folder of the
[Documentation](https://github.com/Space-Type/Documentation) repository. Add a
page in `mkdocs.yml` (`nav`) and preview it with `mkdocs serve` (see
[Getting started](getting-started.md#previewing-this-documentation)). The site
is rebuilt and published on every push to `main`.
