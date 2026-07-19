# Getting started

## 1. Create a provider

A provider accepts the current FastAPI `Request` and returns one validated page or widget map.

```python
from fastapi import Request
from fastapi_cabinet import MetricWidgetMap


async def health_provider(request: Request) -> MetricWidgetMap:
    return MetricWidgetMap(
        key="health",
        title="Service health",
        value="Healthy",
    )
```

## 2. Declare a module

```python
from typing import ClassVar

from fastapi_cabinet import CabinetAdmin, CabinetProvider, MetricWidget


class OperationsAdmin(CabinetAdmin):
    key = "operations"
    label = "Operations"
    dashboard_widgets = (
        MetricWidget(key="health", title="Service health", provider="ops.health"),
    )
    providers: ClassVar[dict[str, CabinetProvider]] = {
        "ops.health": health_provider,
    }
```

Provider names are local wiring keys. Keeping a module prefix, such as `ops.`, prevents accidental
collisions and makes declarations easier to scan.

## 3. Attach it to FastAPI

```python
from fastapi import FastAPI
from fastapi_cabinet import CabinetSite, include_cabinet

app = FastAPI()
site = CabinetSite(brand_name="Operations")
site.register(OperationsAdmin)
include_cabinet(app, site=site, mount_path="/management")
```

Each `CabinetSite` owns its registry. Use one explicit site per FastAPI application when configuring
branding, permissions, or template overrides. If `site` is omitted, `include_cabinet` creates a new
application-scoped instance.

## Larger projects

A module can expose either registration convention:

```python
def register_cabinet(registry):
    registry.register(OperationsAdmin)
```

or:

```python
CABINET_ADMINS = (OperationsAdmin,)
```

Then load it explicitly:

```python
include_cabinet(
    app,
    modules=("my_project.admin.operations",),
    mount_path="/management",
)
```

Relative page and sidebar paths are resolved under the module root. Absolute paths are preserved.
