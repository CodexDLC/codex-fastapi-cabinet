# Customization and security

## Override templates

Host template directories take precedence over package templates:

```python
site = CabinetSite(
    brand_name="Internal tools",
    template_directories=("src/my_project/templates",),
)
```

To replace the detail page, create:

```text
src/my_project/templates/cabinet/pages/detail.html
```

You may also pass an existing FastAPI `Jinja2Templates` instance. Its loader remains available after
the explicit override directories and before package defaults.

## Permissions

Implement the permission port:

```python
from fastapi import Request


class ProjectPermissions:
    async def can(self, request: Request, permission: str) -> bool:
        actor = request.state.actor
        return permission in actor.permissions
```

Then pass it to the site:

```python
site = CabinetSite(permission_provider=ProjectPermissions())
```

Permissions can be declared on modules, pages, widgets, sidebar items, and action routes. Hidden
navigation is not a security boundary by itself; route access is checked separately.

## Authentication and CSRF

The host application must:

- authenticate requests before they reach the cabinet;
- protect the cabinet mount from anonymous access;
- set `request.state.csrf_token` when forms require a CSRF token;
- validate that token in mutation handlers or middleware;
- authorize mutations again inside application use cases when appropriate.

Bundled forms include the CSRF value as `csrf_token`. Non-POST semantic methods are also emitted as
the `_method` field; if you use method tunnelling, install corresponding host middleware.

## Static mount

By default, assets are mounted at `<mount_path>/static`. Override this when assets are served
elsewhere:

```python
include_cabinet(
    app,
    site=site,
    mount_path="/management",
    static_mount_path="/assets/cabinet",
)
```
