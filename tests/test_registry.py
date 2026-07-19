import pytest

from fastapi_cabinet import CabinetAdmin, CabinetRegistry
from fastapi_cabinet.exceptions import CabinetDuplicateKeyError, CabinetRegistrationError


class UsersAdmin(CabinetAdmin):
    key = "users"
    label = "Users"


def test_registry_registers_and_sorts_admins() -> None:
    class LaterAdmin(CabinetAdmin):
        key = "later"
        label = "Later"
        order = 200

    registry = CabinetRegistry()
    registry.register(LaterAdmin)
    registered = registry.register(UsersAdmin)

    assert registry.get("users") is registered
    assert [admin.key for admin in registry.all()] == ["users", "later"]


def test_registry_rejects_duplicate_keys() -> None:
    registry = CabinetRegistry()
    registry.register(UsersAdmin)

    with pytest.raises(CabinetDuplicateKeyError, match="users"):
        registry.register(UsersAdmin)


def test_registry_rejects_missing_identity() -> None:
    class InvalidAdmin(CabinetAdmin):
        key = ""
        label = ""

    with pytest.raises(CabinetRegistrationError):
        CabinetRegistry().register(InvalidAdmin)
