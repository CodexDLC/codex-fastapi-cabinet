from functools import lru_cache
from pathlib import Path

from fastapi_cabinet.contracts.admin import CabinetAdmin
from fastapi_cabinet.contracts.layout import CabinetLayoutMap, HeaderGroup
from fastapi_cabinet.contracts.navigation import HeaderItem, SidebarItem
from fastapi_cabinet.runtime import admin_public_path

_STATIC_DIR = Path(__file__).parents[1] / "static"


def build_layout_map(
    admins: tuple[CabinetAdmin, ...],
    *,
    mount_path: str,
    static_mount_path: str,
    brand_name: str,
    active_admin: CabinetAdmin | None,
    active_path: str,
    sidebar: list[SidebarItem] | None = None,
    sidebar_badges: dict[str, int | str] | None = None,
    title: str | None = None,
) -> CabinetLayoutMap:
    header = [
        HeaderItem(
            key=admin.key,
            label=admin.label,
            path=admin_public_path(admin, mount_path),
            icon=admin.icon,
            group=admin.group,
            group_label=admin.group_label,
            order=admin.order,
        )
        for admin in admins
    ]
    return CabinetLayoutMap(
        mount_path=mount_path,
        static_mount_path=static_mount_path,
        static_version=_static_version(),
        brand_name=brand_name,
        title=title or (active_admin.label if active_admin else brand_name),
        active_module=active_admin.key if active_admin else None,
        active_path=active_path,
        header_groups=_build_header_groups(header),
        sidebar=_build_sidebar(sidebar or [], active_admin, mount_path),
        sidebar_badges=sidebar_badges or {},
    )


def _build_header_groups(header: list[HeaderItem]) -> list[HeaderGroup]:
    groups: dict[str, HeaderGroup] = {}
    for item in sorted(header, key=lambda value: (value.order, value.key)):
        if item.group not in groups:
            groups[item.group] = HeaderGroup(
                key=item.group,
                label=item.group_label or item.group,
                items=[],
            )
        groups[item.group].items.append(item)
    return list(groups.values())


def _build_sidebar(
    sidebar: list[SidebarItem],
    active_admin: CabinetAdmin | None,
    mount_path: str,
) -> list[SidebarItem]:
    items = sorted(sidebar, key=lambda item: (item.order, item.key))
    if active_admin is None:
        return items
    base_path = admin_public_path(active_admin, mount_path).rstrip("/")
    return [
        item
        if item.path.startswith("/")
        else item.model_copy(update={"path": f"{base_path}/{item.path.strip('/')}"})
        for item in items
    ]


@lru_cache(maxsize=1)
def _static_version() -> str:
    mtimes: list[int] = []
    for relative in ("css/cabinet.css", "js/cabinet.js"):
        try:
            mtimes.append(int((_STATIC_DIR / relative).stat().st_mtime))
        except OSError:
            mtimes.append(0)
    return str(max(mtimes))
