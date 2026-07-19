from collections.abc import Iterable

from fastapi_cabinet.contracts.admin import CabinetAdmin
from fastapi_cabinet.exceptions import CabinetDuplicateKeyError, CabinetRegistrationError


class CabinetRegistry:
    """Application-scoped registry of cabinet modules."""

    def __init__(self) -> None:
        self._admins: dict[str, CabinetAdmin] = {}

    def register(self, admin: type[CabinetAdmin] | CabinetAdmin) -> CabinetAdmin:
        admin_instance = admin() if isinstance(admin, type) else admin
        key = getattr(admin_instance, "key", "").strip()
        label = getattr(admin_instance, "label", "").strip()
        if not key or not label:
            raise CabinetRegistrationError("Cabinet admin must define non-empty key and label values.")
        if key in self._admins:
            raise CabinetDuplicateKeyError(f"Cabinet admin key {key!r} is already registered.")
        self._admins[key] = admin_instance
        return admin_instance

    def get(self, key: str) -> CabinetAdmin:
        return self._admins[key]

    def all(self) -> tuple[CabinetAdmin, ...]:
        return tuple(sorted(self._admins.values(), key=lambda admin: (admin.order, admin.key)))

    def keys(self) -> Iterable[str]:
        return self._admins.keys()
