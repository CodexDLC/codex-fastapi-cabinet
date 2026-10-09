# codex-fastapi-cabinet

Composable, server-rendered administration interfaces for FastAPI sites and APIs.

The library provides the management shell, routing, navigation, generic pages, dashboard widgets,
permissions port, Jinja templates, and static assets. Your FastAPI application keeps ownership of
authentication, authorization rules, database access, transactions, and business operations.

> Status: alpha. The public API is usable, but may evolve before `1.0`.

## What it provides

- application-scoped admin registry;
- independent mount path, such as `/cabinet` or `/management`;
- generic list, detail, form, and operation pages;
- metric, table, list, and chart dashboard widgets;
- async application-owned data providers;
- permission checks for modules, pages, widgets, navigation, and actions;
- overridable Jinja templates and packaged responsive CSS;
- explicit module discovery without import-time registration side effects.

## Installation

```bash
pip install codex-fastapi-cabinet
```

For local development:

```bash
uv sync --extra dev --extra docs
```

## Quick start

```python
from typing import ClassVar

from fastapi import FastAPI, Request

from fastapi_cabinet import (
    CabinetAdmin,
    CabinetProvider,
    CabinetSite,
    ListPage,
    ListPageMap,
    MetricWidget,
    MetricWidgetMap,
    SidebarItem,
    TableColumnMap,
    include_cabinet,
)


async def user_count(request: Request) -> MetricWidgetMap:
    return MetricWidgetMap(
        key="users-total",
        title="Users",
        value="42",
        subtitle="Registered accounts",
    )


async def user_list(request: Request) -> ListPageMap:
    return ListPageMap(
        title="Users",
        columns=[
            TableColumnMap(key="email", label="Email"),
            TableColumnMap(key="status", label="Status"),
        ],
        rows=[
            {
                "email": "admin@example.test",
                "status": "active",
                "href": "/management/users/1",
            }
        ],
        row_href_key="href",
    )


class UsersAdmin(CabinetAdmin):
    key = "users"
    label = "Users"
    sidebar = (SidebarItem(key="all", label="All users", path="all"),)
    dashboard_widgets = (
        MetricWidget(key="users-total", title="Users", provider="users.count"),
    )
    pages = (
        ListPage(key="all", label="All users", path="all", provider="users.list"),
    )
    providers: ClassVar[dict[str, CabinetProvider]] = {
        "users.count": user_count,
        "users.list": user_list,
    }


app = FastAPI()
site = CabinetSite(brand_name="My service")
site.register(UsersAdmin)
include_cabinet(app, site=site, mount_path="/management")
```

Run the complete example:

```bash
uvicorn examples.basic_app:app --reload
```

Then open `http://127.0.0.1:8000/management`.

## Boundaries

`codex-fastapi-cabinet` is a composition toolkit, not an ORM-aware CRUD generator. Providers return
validated view models, so the same cabinet can sit over SQLAlchemy, another database layer, an HTTP
API, or an in-memory service without coupling the library to any of them.

The host application must secure the cabinet mount and provide real permission checks. The default
permission provider allows every declared permission and is intended only when access control is
enforced outside the library.

## Documentation

- [English documentation](docs/index.md)
- [Русская документация](docs/ru/index.md)
- [Architecture and extension boundaries](docs/architecture.md)
- [Template customization](docs/customization.md)
- [Optional offline agent skill](docs/agent-skills.md)

## Development

```bash
ruff check src tests examples
mypy src tests examples
pytest
python -m build
```

## License

Apache License 2.0. See [LICENSE](LICENSE).
