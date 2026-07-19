# Быстрый старт

## 1. Создайте провайдер

Провайдер получает текущий `Request` FastAPI и возвращает проверяемую модель страницы или виджета.

```python
from fastapi import Request
from fastapi_cabinet import MetricWidgetMap


async def health_provider(request: Request) -> MetricWidgetMap:
    return MetricWidgetMap(
        key="health",
        title="Состояние сервиса",
        value="Работает",
    )
```

## 2. Объявите модуль

```python
from typing import ClassVar

from fastapi_cabinet import CabinetAdmin, CabinetProvider, MetricWidget


class OperationsAdmin(CabinetAdmin):
    key = "operations"
    label = "Операции"
    dashboard_widgets = (
        MetricWidget(key="health", title="Состояние", provider="ops.health"),
    )
    providers: ClassVar[dict[str, CabinetProvider]] = {
        "ops.health": health_provider,
    }
```

## 3. Подключите его к FastAPI

```python
from fastapi import FastAPI
from fastapi_cabinet import CabinetSite, include_cabinet

app = FastAPI()
site = CabinetSite(brand_name="Управление")
site.register(OperationsAdmin)
include_cabinet(app, site=site, mount_path="/management")
```

У каждого `CabinetSite` собственный реестр. Если `site` не передан, `include_cabinet` создаст новый
экземпляр для этого приложения.

## Разделение модулей

Модуль проекта может предоставить функцию:

```python
def register_cabinet(registry):
    registry.register(OperationsAdmin)
```

или декларацию:

```python
CABINET_ADMINS = (OperationsAdmin,)
```

После этого модуль загружается явно:

```python
include_cabinet(app, modules=("my_project.admin.operations",))
```

Относительные пути страниц и бокового меню разрешаются от корня модуля. Абсолютные пути сохраняются.
