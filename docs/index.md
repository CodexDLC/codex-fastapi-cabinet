# codex-fastapi-cabinet

`codex-fastapi-cabinet` helps FastAPI applications compose management interfaces from small,
validated declarations.

It deliberately stays between two extremes:

- it is more structured than copying routes and templates into every project;
- it does not own your database models or generate business CRUD automatically.

The library owns the reusable shell. The host application owns the use cases.

## Core capabilities

- Register independent management modules in an application-scoped `CabinetSite`.
- Render dashboards from metric, table, list, and chart widgets.
- Render reusable list, detail, form, and operation pages.
- Resolve all data asynchronously through application-owned providers.
- Check permissions without coupling to one authentication package.
- Override any bundled Jinja template from the host application.
- Load module declarations explicitly, with no registration during import.

Continue with [Getting started](getting-started.md).
