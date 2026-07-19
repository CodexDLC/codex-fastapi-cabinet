from pydantic import BaseModel, ConfigDict


class SidebarItem(BaseModel):
    """A navigation item shown inside the active admin module."""

    model_config = ConfigDict(frozen=True)

    key: str
    label: str
    path: str
    icon: str = ""
    badge_key: str | None = None
    order: int = 100
    permission: str | None = None


class HeaderItem(BaseModel):
    """A top-level registered admin module."""

    model_config = ConfigDict(frozen=True)

    key: str
    label: str
    path: str
    icon: str = ""
    group: str = "main"
    group_label: str = ""
    order: int = 100
