from typing import cast

from fastapi import Request
from pydantic import BaseModel, ValidationError

from fastapi_cabinet.contracts.admin import CabinetAdmin
from fastapi_cabinet.contracts.pages import (
    CabinetPage,
    DetailPageMap,
    FormPageMap,
    ListPageMap,
    OperationPageMap,
    PageMap,
)
from fastapi_cabinet.exceptions import CabinetProviderError


async def resolve_page(admin: CabinetAdmin, declaration: CabinetPage, request: Request) -> PageMap:
    provider = admin.providers.get(declaration.provider)
    if provider is None:
        raise CabinetProviderError(
            f"Provider {declaration.provider!r} is not registered for cabinet admin {admin.key!r}."
        )
    result = await provider(request)
    model = _model_for_kind(declaration.kind)
    try:
        return cast("PageMap", model.model_validate(result))
    except ValidationError as exc:
        raise CabinetProviderError(
            f"Provider {declaration.provider!r} returned an invalid {declaration.kind!r} page map."
        ) from exc


def _model_for_kind(kind: str) -> type[BaseModel]:
    models: dict[str, type[BaseModel]] = {
        "list": ListPageMap,
        "detail": DetailPageMap,
        "form": FormPageMap,
        "operation": OperationPageMap,
    }
    try:
        return models[kind]
    except KeyError as exc:
        raise CabinetProviderError(f"Unsupported cabinet page kind {kind!r}.") from exc
