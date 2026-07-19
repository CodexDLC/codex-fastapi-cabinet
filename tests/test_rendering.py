from typing import ClassVar, cast

import pytest
from fastapi import Request

from fastapi_cabinet import CabinetAdmin, CabinetPage, DashboardWidget, DetailPage, MetricWidget
from fastapi_cabinet.contracts.pages import DetailPageMap
from fastapi_cabinet.contracts.providers import CabinetProvider
from fastapi_cabinet.contracts.widgets import MetricWidgetMap
from fastapi_cabinet.exceptions import CabinetProviderError
from fastapi_cabinet.rendering.page_mapper import resolve_page
from fastapi_cabinet.rendering.widget_mapper import resolve_widget


async def metric_provider(request: Request) -> MetricWidgetMap:
    return MetricWidgetMap(key="online", title="Online", value="12")


async def detail_provider(request: Request) -> DetailPageMap:
    return DetailPageMap(title=f"User {request.path_params.get('user_id', '')}")


class UsersAdmin(CabinetAdmin):
    key = "users"
    label = "Users"
    providers: ClassVar[dict[str, CabinetProvider]] = {
        "users.online": metric_provider,
        "users.detail": detail_provider,
    }


async def test_widget_provider_is_validated() -> None:
    declaration = MetricWidget(key="online", title="Online", provider="users.online")

    result = await resolve_widget(UsersAdmin(), declaration, Request({"type": "http"}))

    assert isinstance(result, MetricWidgetMap)
    assert result.value == "12"


async def test_page_provider_is_validated() -> None:
    declaration = DetailPage(
        key="detail",
        label="Detail",
        path="users/{user_id}",
        provider="users.detail",
    )
    request = Request({"type": "http", "path_params": {"user_id": "42"}})

    result = await resolve_page(UsersAdmin(), declaration, request)

    assert result.title == "User 42"


async def test_missing_provider_fails_clearly() -> None:
    declaration = MetricWidget(key="missing", title="Missing", provider="users.missing")

    with pytest.raises(CabinetProviderError, match="users.missing"):
        await resolve_widget(UsersAdmin(), declaration, Request({"type": "http"}))


async def test_invalid_provider_result_fails_clearly() -> None:
    async def invalid_provider(request: Request) -> dict[str, str]:
        return {"unexpected": "shape"}

    class InvalidAdmin(CabinetAdmin):
        key = "invalid"
        label = "Invalid"
        providers: ClassVar[dict[str, CabinetProvider]] = {
            "invalid": cast("CabinetProvider", invalid_provider)
        }

    with pytest.raises(CabinetProviderError, match="invalid 'metric'"):
        await resolve_widget(
            InvalidAdmin(),
            MetricWidget(key="invalid", title="Invalid", provider="invalid"),
            Request({"type": "http"}),
        )


async def test_unsupported_declaration_kinds_fail_clearly() -> None:
    admin = UsersAdmin()

    with pytest.raises(CabinetProviderError, match="Unsupported dashboard widget"):
        await resolve_widget(
            admin,
            DashboardWidget(key="custom", title="Custom", provider="users.online", kind="custom"),
            Request({"type": "http"}),
        )
    with pytest.raises(CabinetProviderError, match="Unsupported cabinet page"):
        await resolve_page(
            admin,
            CabinetPage(
                key="custom",
                label="Custom",
                path="custom",
                provider="users.detail",
                kind="custom",
            ),
            Request({"type": "http"}),
        )
