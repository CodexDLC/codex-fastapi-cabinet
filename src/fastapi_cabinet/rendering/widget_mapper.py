from typing import cast

from fastapi import Request
from pydantic import BaseModel, ValidationError

from fastapi_cabinet.contracts.admin import CabinetAdmin
from fastapi_cabinet.contracts.widgets import (
    ChartWidgetMap,
    DashboardWidget,
    ListWidgetMap,
    MetricWidgetMap,
    TableWidgetMap,
    WidgetMap,
)
from fastapi_cabinet.exceptions import CabinetProviderError


async def resolve_widgets(
    admin: CabinetAdmin,
    declarations: tuple[DashboardWidget, ...],
    request: Request,
) -> list[WidgetMap]:
    result: list[WidgetMap] = []
    for declaration in sorted(declarations, key=lambda widget: (widget.order, widget.key)):
        result.append(await resolve_widget(admin, declaration, request))
    return result


async def resolve_widget(
    admin: CabinetAdmin,
    declaration: DashboardWidget,
    request: Request,
) -> WidgetMap:
    provider = admin.providers.get(declaration.provider)
    if provider is None:
        raise CabinetProviderError(
            f"Provider {declaration.provider!r} is not registered for cabinet admin {admin.key!r}."
        )
    result = await provider(request)
    model = _model_for_kind(declaration.kind)
    try:
        return cast("WidgetMap", model.model_validate(result))
    except ValidationError as exc:
        raise CabinetProviderError(
            f"Provider {declaration.provider!r} returned an invalid {declaration.kind!r} widget map."
        ) from exc


def _model_for_kind(kind: str) -> type[BaseModel]:
    models: dict[str, type[BaseModel]] = {
        "metric": MetricWidgetMap,
        "table": TableWidgetMap,
        "list": ListWidgetMap,
        "chart": ChartWidgetMap,
    }
    try:
        return models[kind]
    except KeyError as exc:
        raise CabinetProviderError(f"Unsupported dashboard widget kind {kind!r}.") from exc
