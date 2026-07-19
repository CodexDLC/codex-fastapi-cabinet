# Architecture

The package follows a small hexagonal composition model.

## Kernel

`contracts/`, `registry.py`, and `runtime.py` define stable declarations, validated render maps,
registration, and URL rules. They do not know about a database, ORM, or concrete authentication
system.

## Application ports

The host supplies:

- providers that read data and return page/widget maps;
- a permission provider implementing `can(request, permission)`;
- action handlers that execute mutations;
- optional dashboard context and sidebar badge values.

These ports keep business behavior in the application where its transactions and policies live.

## FastAPI and Jinja adapters

`CabinetSite` composes the registry into FastAPI routes. Rendering mappers validate provider results
before bundled Jinja templates receive them. `include_cabinet` mounts the router and packaged static
assets.

```text
FastAPI request
    -> CabinetSite route
    -> permission port
    -> host provider / action
    -> validated page or widget map
    -> Jinja adapter
    -> HTML response
```

## Intentional non-goals

- ORM model introspection;
- implicit CRUD mutations;
- owning user sessions or authentication;
- replacing application services;
- import-time global registration;
- embedding game- or product-specific screens in the core package.

Product-specific modules belong in the consuming project's frontend/admin package and use this
library as their shared shell.
