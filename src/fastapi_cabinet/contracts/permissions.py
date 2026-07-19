from typing import Protocol

from fastapi import Request


class PermissionProvider(Protocol):
    """Application-owned authorization port."""

    async def can(self, request: Request, permission: str) -> bool: ...


class AllowAllPermissionProvider:
    """Convenient default for apps that secure the whole mount externally."""

    async def can(self, request: Request, permission: str) -> bool:
        return True
