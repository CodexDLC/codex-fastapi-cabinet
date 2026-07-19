from typing import ClassVar, Literal

from fastapi import Request
from pydantic import BaseModel, ConfigDict
from starlette.responses import Response

from fastapi_cabinet.contracts.navigation import SidebarItem
from fastapi_cabinet.contracts.pages import CabinetPage
from fastapi_cabinet.contracts.providers import CabinetProvider
from fastapi_cabinet.contracts.widgets import DashboardWidget


class ActionRoute(BaseModel):
    """Route declaration bound to a method on a CabinetAdmin instance."""

    model_config = ConfigDict(frozen=True)

    path: str
    method: Literal["POST", "PUT", "PATCH", "DELETE"]
    handler: str
    permission: str | None = None
    name: str | None = None


class CabinetAdmin:
    """Static module declaration plus application-owned async providers."""

    key: ClassVar[str]
    label: ClassVar[str]
    icon: ClassVar[str] = ""
    path: ClassVar[str | None] = None
    group: ClassVar[str] = "main"
    group_label: ClassVar[str] = ""
    order: ClassVar[int] = 100
    permission: ClassVar[str | None] = None

    sidebar: ClassVar[tuple[SidebarItem, ...]] = ()
    dashboard_widgets: ClassVar[tuple[DashboardWidget, ...]] = ()
    pages: ClassVar[tuple[CabinetPage, ...]] = ()
    providers: ClassVar[dict[str, CabinetProvider]] = {}
    actions: ClassVar[tuple[ActionRoute, ...]] = ()

    async def get_dashboard_context(self, request: Request) -> dict[str, object]:
        return {}

    async def get_sidebar_badges(self, request: Request) -> dict[str, int | str]:
        return {}

    async def dispatch_action(self, request: Request) -> Response:
        raise NotImplementedError
