from collections.abc import Awaitable, Callable

from fastapi import Request

from fastapi_cabinet.contracts.pages import PageMap
from fastapi_cabinet.contracts.widgets import WidgetMap

type ProviderResult = WidgetMap | PageMap
type CabinetProvider = Callable[[Request], Awaitable[ProviderResult]]
