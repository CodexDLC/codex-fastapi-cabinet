# Composition

`fastapi_cabinet` exports `CabinetAdmin`, `CabinetSite`, `include_cabinet`, page and widget declarations, and validated view maps. A provider is an async callable taking `fastapi.Request` and returning a page or widget map. A declaration's `provider` string must exist in its admin class's `providers` mapping. Relative page and sidebar paths resolve under the module root.

Minimal application (serve with an ASGI server such as optional `uvicorn`):

```python
from typing import ClassVar

from fastapi import FastAPI, Request
from fastapi_cabinet import (
    CabinetAdmin, CabinetProvider, CabinetSite, MetricWidget, MetricWidgetMap,
    include_cabinet,
)


async def health(request: Request) -> MetricWidgetMap:
    return MetricWidgetMap(key="health", title="Health", value="OK")


class OperationsAdmin(CabinetAdmin):
    key = "operations"
    label = "Operations"
    dashboard_widgets = (
        MetricWidget(key="health", title="Health", provider="operations.health"),
    )
    providers: ClassVar[dict[str, CabinetProvider]] = {
        "operations.health": health,
    }


app = FastAPI()
site = CabinetSite(brand_name="Operations")
site.register(OperationsAdmin)
include_cabinet(app, site=site, mount_path="/management")
```

For list, detail, form, or operation pages, declare `ListPage`, `DetailPage`, `FormPage`, or `OperationPage`, then return the matching `*PageMap` from its provider. For larger projects, pass module import paths to `include_cabinet(modules=(...))`; modules can expose `register_cabinet(registry)` or `CABINET_ADMINS`. Inspect the installed `fastapi_cabinet/contracts/pages.py` and `widgets.py` for current view-map fields.
