from types import ModuleType

import pytest

from fastapi_cabinet import CabinetAdmin, CabinetRegistry
from fastapi_cabinet.exceptions import CabinetModuleLoadError
from fastapi_cabinet.loader import load_cabinet_modules


class UsersAdmin(CabinetAdmin):
    key = "users"
    label = "Users"


def test_loader_supports_registration_hook() -> None:
    module = ModuleType("hook_module")

    def register_cabinet(registry: CabinetRegistry) -> None:
        registry.register(UsersAdmin)

    module.__dict__["register_cabinet"] = register_cabinet
    registry = CabinetRegistry()

    assert load_cabinet_modules((module,), registry) == (module,)
    assert registry.get("users").label == "Users"


def test_loader_supports_declarations() -> None:
    module = ModuleType("declarations_module")
    module.__dict__["CABINET_ADMINS"] = [UsersAdmin]
    registry = CabinetRegistry()

    load_cabinet_modules((module,), registry)

    assert registry.all()[0].key == "users"


@pytest.mark.parametrize(
    ("attribute", "value", "match"),
    [
        ("none", None, "must expose"),
        ("register_cabinet", "not-callable", "not callable"),
        ("CABINET_ADMINS", "not-a-sequence", "must be a sequence"),
        ("CABINET_ADMINS", [object()], "non-CabinetAdmin"),
    ],
)
def test_loader_rejects_invalid_modules(attribute: str, value: object, match: str) -> None:
    module = ModuleType(f"invalid_{attribute}")
    if attribute != "none":
        setattr(module, attribute, value)

    with pytest.raises(CabinetModuleLoadError, match=match):
        load_cabinet_modules((module,), CabinetRegistry())


def test_loader_rejects_hook_with_wrong_signature() -> None:
    module = ModuleType("bad_signature")

    def register_cabinet() -> None:
        return None

    module.__dict__["register_cabinet"] = register_cabinet

    with pytest.raises(CabinetModuleLoadError, match="exactly one"):
        load_cabinet_modules((module,), CabinetRegistry())


def test_loader_wraps_import_error() -> None:
    with pytest.raises(CabinetModuleLoadError, match="Could not import"):
        load_cabinet_modules(("module_that_does_not_exist_anywhere",), CabinetRegistry())
