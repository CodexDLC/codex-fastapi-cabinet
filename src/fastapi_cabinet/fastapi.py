from collections.abc import Sequence
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from fastapi_cabinet.loader import CabinetModuleRef, load_cabinet_modules
from fastapi_cabinet.runtime import normalize_mount_path
from fastapi_cabinet.site import CabinetSite


def include_cabinet(
    app: FastAPI,
    *,
    modules: Sequence[CabinetModuleRef] = (),
    mount_path: str = "/cabinet",
    static_mount_path: str | None = None,
    site: CabinetSite | None = None,
) -> CabinetSite:
    """Load modules and attach one cabinet site to a FastAPI application."""

    active_site = site or CabinetSite()
    if modules:
        load_cabinet_modules(modules, active_site.registry)
    mount = normalize_mount_path(mount_path)
    assets = static_mount_path or f"{mount.rstrip('/')}/static"
    active_site.static_mount_path = assets
    app.include_router(active_site.build_router(mount_path=mount, static_mount_path=assets))

    static_dir = Path(__file__).parent / "static"
    app.mount(
        assets,
        StaticFiles(directory=static_dir),
        name=f"fastapi_cabinet_static_{id(active_site)}",
    )
    return active_site
