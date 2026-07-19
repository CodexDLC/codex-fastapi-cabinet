from fastapi_cabinet import CabinetAdmin, CabinetRegistry, DetailPage
from fastapi_cabinet.runtime import (
    action_public_path,
    admin_public_path,
    admin_route_path,
    normalize_mount_path,
    page_public_path,
    resolve_active_admin,
)


class UsersAdmin(CabinetAdmin):
    key = "users"
    label = "Users"


def test_paths_follow_custom_mount() -> None:
    admin = UsersAdmin()

    assert normalize_mount_path("management/") == "/management"
    assert admin_public_path(admin, "/management") == "/management/users"
    assert admin_route_path(admin, "/management") == "/users"


def test_absolute_admin_path_is_preserved() -> None:
    class ReportsAdmin(CabinetAdmin):
        key = "reports"
        label = "Reports"
        path = "/ops/reports"

    assert admin_public_path(ReportsAdmin(), "/management") == "/ops/reports"
    assert admin_route_path(ReportsAdmin(), "/management") == "/ops/reports"


def test_child_paths_are_relative_to_admin() -> None:
    page = DetailPage(key="detail", label="Detail", path="/{item_id}/", provider="items.detail")

    assert page_public_path(UsersAdmin(), page, "/management") == "/management/users/{item_id}"
    assert action_public_path(UsersAdmin(), "/archive/", "/management") == "/management/users/archive"


def test_active_admin_uses_longest_path_match() -> None:
    class AuditAdmin(CabinetAdmin):
        key = "audit"
        label = "Audit"
        path = "/management/users/audit"

    registry = CabinetRegistry()
    registry.register(UsersAdmin)
    registry.register(AuditAdmin)

    active = resolve_active_admin("/management/users/audit/events", registry, "/management")

    assert active is not None
    assert active.key == "audit"
    assert resolve_active_admin("/public", registry, "/management") is None
