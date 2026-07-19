from pydantic import BaseModel, Field

from fastapi_cabinet.contracts.navigation import HeaderItem, SidebarItem


class HeaderGroup(BaseModel):
    key: str
    label: str
    items: list[HeaderItem]


class CabinetLayoutMap(BaseModel):
    mount_path: str
    static_mount_path: str
    static_version: str = "0"
    brand_name: str
    title: str
    active_module: str | None
    active_path: str = ""
    header_groups: list[HeaderGroup] = Field(default_factory=list)
    sidebar: list[SidebarItem] = Field(default_factory=list)
    sidebar_badges: dict[str, int | str] = Field(default_factory=dict)
