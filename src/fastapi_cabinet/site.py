from collections.abc import Awaitable, Callable, Sequence
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.templating import Jinja2Templates
from jinja2 import BaseLoader, ChoiceLoader, FileSystemLoader
from starlette.responses import RedirectResponse, Response

from fastapi_cabinet.contracts.admin import ActionRoute, CabinetAdmin
from fastapi_cabinet.contracts.navigation import SidebarItem
from fastapi_cabinet.contracts.pages import CabinetPage
from fastapi_cabinet.contracts.permissions import AllowAllPermissionProvider, PermissionProvider
from fastapi_cabinet.contracts.widgets import DashboardWidget
from fastapi_cabinet.exceptions import CabinetRegistrationError
from fastapi_cabinet.registry import CabinetRegistry
from fastapi_cabinet.rendering.layout_mapper import build_layout_map
from fastapi_cabinet.rendering.page_mapper import resolve_page
from fastapi_cabinet.rendering.widget_mapper import resolve_widgets
from fastapi_cabinet.runtime import action_public_path, admin_public_path, normalize_mount_path, page_public_path

_PACKAGE_DIR = Path(__file__).parent
_PACKAGE_TEMPLATE_DIR = _PACKAGE_DIR / "templates"


class CabinetSite:
    """Application-scoped cabinet composition root."""

    def __init__(
        self,
        *,
        brand_name: str = "Cabinet",
        permission_provider: PermissionProvider | None = None,
        templates: Jinja2Templates | None = None,
        template_directories: Sequence[str | Path] = (),
    ) -> None:
        self.brand_name = brand_name
        self.permission_provider = permission_provider or AllowAllPermissionProvider()
        self.registry = CabinetRegistry()
        self.templates = _build_templates(templates, template_directories)
        self.static_mount_path: str | None = None

    def register(self, admin: type[CabinetAdmin] | CabinetAdmin) -> CabinetAdmin:
        return self.registry.register(admin)

    def build_router(
        self,
        *,
        mount_path: str = "/cabinet",
        static_mount_path: str | None = None,
    ) -> APIRouter:
        mount = normalize_mount_path(mount_path)
        assets = static_mount_path or f"{mount.rstrip('/')}/static"
        router = APIRouter()

        @router.get(mount, name="cabinet:dashboard")
        async def dashboard(request: Request) -> Response:
            admins = await self._visible_admins(request)
            if admins:
                return RedirectResponse(url=admin_public_path(admins[0], mount), status_code=303)
            layout = build_layout_map(
                admins,
                mount_path=mount,
                static_mount_path=assets,
                brand_name=self.brand_name,
                active_admin=None,
                active_path=str(request.url.path),
            )
            return self.templates.TemplateResponse(
                request=request,
                name="cabinet/dashboard.html",
                context=self._context(request, layout=layout, modules=admins),
            )

        for admin in self.registry.all():
            self._register_admin_routes(router, admin, mount, assets)
        return router

    def _register_admin_routes(
        self,
        router: APIRouter,
        admin: CabinetAdmin,
        mount_path: str,
        static_mount_path: str,
    ) -> None:
        router.get(admin_public_path(admin, mount_path), name=f"cabinet:{admin.key}")(
            self._build_module_endpoint(admin, mount_path, static_mount_path)
        )

        for action in sorted(admin.actions, key=lambda item: item.path):
            handler = getattr(admin, action.handler, None)
            if not callable(handler):
                raise CabinetRegistrationError(
                    f"Cabinet admin {admin.key!r} action {action.path!r} references missing handler "
                    f"{action.handler!r}."
                )
            endpoint = self._build_action_endpoint(admin, action, handler)
            router.add_api_route(
                action_public_path(admin, action.path, mount_path),
                endpoint,
                methods=[action.method],
                name=action.name or f"cabinet:{admin.key}:action:{action.path.strip('/')}",
            )

        for page in sorted(admin.pages, key=_page_sort_key):
            router.get(
                page_public_path(admin, page, mount_path),
                name=f"cabinet:{admin.key}:page:{page.key}",
            )(self._build_page_endpoint(admin, page, mount_path, static_mount_path))

    def _build_module_endpoint(
        self,
        admin: CabinetAdmin,
        mount_path: str,
        static_mount_path: str,
    ) -> Callable[[Request], Awaitable[Response]]:
        async def module_page(request: Request) -> Response:
            await self._ensure_allowed(request, admin.permission)
            visible_admins = await self._visible_admins(request)
            sidebar = await self._visible_sidebar(request, admin.sidebar)
            widget_declarations = await self._visible_widgets(request, admin.dashboard_widgets)
            badges = await admin.get_sidebar_badges(request)
            layout = build_layout_map(
                visible_admins,
                mount_path=mount_path,
                static_mount_path=static_mount_path,
                brand_name=self.brand_name,
                active_admin=admin,
                active_path=str(request.url.path),
                sidebar=sidebar,
                sidebar_badges=badges,
            )
            return self.templates.TemplateResponse(
                request=request,
                name="cabinet/module.html",
                context=self._context(
                    request,
                    layout=layout,
                    module=admin,
                    module_context=await admin.get_dashboard_context(request),
                    widgets=await resolve_widgets(admin, widget_declarations, request),
                ),
            )

        return module_page

    def _build_page_endpoint(
        self,
        admin: CabinetAdmin,
        declaration: CabinetPage,
        mount_path: str,
        static_mount_path: str,
    ) -> Callable[[Request], Awaitable[Response]]:
        async def page_endpoint(request: Request) -> Response:
            await self._ensure_allowed(request, admin.permission)
            await self._ensure_allowed(request, declaration.permission)
            visible_admins = await self._visible_admins(request)
            sidebar = await self._visible_sidebar(request, admin.sidebar)
            layout = build_layout_map(
                visible_admins,
                mount_path=mount_path,
                static_mount_path=static_mount_path,
                brand_name=self.brand_name,
                active_admin=admin,
                active_path=str(request.url.path),
                sidebar=sidebar,
                sidebar_badges=await admin.get_sidebar_badges(request),
                title=declaration.label,
            )
            page = await resolve_page(admin, declaration, request)
            template = declaration.template or f"cabinet/pages/{declaration.kind}.html"
            return self.templates.TemplateResponse(
                request=request,
                name=template,
                context=self._context(
                    request,
                    layout=layout,
                    module=admin,
                    declaration=declaration,
                    page=page,
                ),
            )

        return page_endpoint

    def _build_action_endpoint(
        self,
        admin: CabinetAdmin,
        action: ActionRoute,
        handler: Callable[[Request], Awaitable[Response]],
    ) -> Callable[[Request], Awaitable[Response]]:
        async def action_endpoint(request: Request) -> Response:
            await self._ensure_allowed(request, admin.permission)
            await self._ensure_allowed(request, action.permission)
            return await handler(request)

        return action_endpoint

    async def _visible_admins(self, request: Request) -> tuple[CabinetAdmin, ...]:
        result: list[CabinetAdmin] = []
        for admin in self.registry.all():
            if await self._is_allowed(request, admin.permission):
                result.append(admin)
        return tuple(result)

    async def _visible_sidebar(
        self,
        request: Request,
        items: tuple[SidebarItem, ...],
    ) -> list[SidebarItem]:
        result: list[SidebarItem] = []
        for item in items:
            if await self._is_allowed(request, item.permission):
                result.append(item)
        return result

    async def _visible_widgets(
        self,
        request: Request,
        widgets: tuple[DashboardWidget, ...],
    ) -> tuple[DashboardWidget, ...]:
        result: list[DashboardWidget] = []
        for widget in widgets:
            if await self._is_allowed(request, widget.permission):
                result.append(widget)
        return tuple(result)

    async def _is_allowed(self, request: Request, permission: str | None) -> bool:
        return permission is None or await self.permission_provider.can(request, permission)

    async def _ensure_allowed(self, request: Request, permission: str | None) -> None:
        if not await self._is_allowed(request, permission):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cabinet permission denied.")

    @staticmethod
    def _context(request: Request, **values: object) -> dict[str, object]:
        return {
            "request": request,
            "csrf_token": getattr(request.state, "csrf_token", ""),
            **values,
        }


def _page_sort_key(page: CabinetPage) -> tuple[int, int, str]:
    return (page.path.count("{"), page.order, page.key)


def _build_templates(
    templates: Jinja2Templates | None,
    template_directories: Sequence[str | Path],
) -> Jinja2Templates:
    active = templates or Jinja2Templates(directory=str(_PACKAGE_TEMPLATE_DIR))
    loaders: list[BaseLoader] = [
        FileSystemLoader(str(Path(directory))) for directory in template_directories
    ]
    if templates is not None and templates.env.loader is not None:
        loaders.append(templates.env.loader)
    loaders.append(FileSystemLoader(str(_PACKAGE_TEMPLATE_DIR)))
    active.env.loader = ChoiceLoader(loaders)
    return active


cabinet_site = CabinetSite()
