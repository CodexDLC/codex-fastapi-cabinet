from typing import ClassVar

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from starlette.responses import PlainTextResponse

from fastapi_cabinet import (
    ActionRoute,
    CabinetAdmin,
    CabinetSite,
    DetailFieldMap,
    DetailPage,
    DetailPageMap,
    ListPage,
    ListPageMap,
    MetricWidget,
    MetricWidgetMap,
    PaginationMap,
    SidebarItem,
    TableColumnMap,
    include_cabinet,
)
from fastapi_cabinet.contracts.providers import CabinetProvider


async def metric_provider(request: Request) -> MetricWidgetMap:
    return MetricWidgetMap(key="online", title="Online users", value="7")


async def users_provider(request: Request) -> ListPageMap:
    return ListPageMap(
        title="User management",
        columns=[TableColumnMap(key="email", label="Email")],
        rows=[{"email": "admin@example.test", "href": "/management/users/42"}],
        row_href_key="href",
        pagination=PaginationMap(page=1, pages=1, total=1),
    )


async def user_provider(request: Request) -> DetailPageMap:
    return DetailPageMap(
        title=f"User {request.path_params['user_id']}",
        fields=[DetailFieldMap(label="Role", value="Administrator")],
    )


class UsersAdmin(CabinetAdmin):
    key = "users"
    label = "Users"
    sidebar = (SidebarItem(key="list", label="All users", path="all"),)
    dashboard_widgets = (MetricWidget(key="online", title="Online users", provider="users.online"),)
    pages = (
        ListPage(key="list", label="All users", path="all", provider="users.list"),
        DetailPage(key="detail", label="User", path="{user_id}", provider="users.detail"),
    )
    providers: ClassVar[dict[str, CabinetProvider]] = {
        "users.online": metric_provider,
        "users.list": users_provider,
        "users.detail": user_provider,
    }


def build_client(site: CabinetSite | None = None) -> TestClient:
    app = FastAPI()
    active_site = site or CabinetSite()
    active_site.register(UsersAdmin)
    include_cabinet(app, modules=(), mount_path="/management", site=active_site)
    return TestClient(app)


def test_registered_dashboard_and_pages_render() -> None:
    client = build_client()

    dashboard = client.get("/management/users")
    listing = client.get("/management/users/all")
    detail = client.get("/management/users/42")

    assert dashboard.status_code == 200
    assert listing.status_code == 200
    assert "Online users" in dashboard.text
    assert 'href="/management/users/all"' in dashboard.text
    assert "admin@example.test" in listing.text
    assert "Administrator" in detail.text


def test_static_assets_are_packaged_and_mounted() -> None:
    response = build_client().get("/management/static/css/cabinet.css")

    assert response.status_code == 200
    assert ".fc-shell" in response.text


def test_sites_do_not_share_registries() -> None:
    first = CabinetSite()
    second = CabinetSite()
    first.register(UsersAdmin)

    assert [admin.key for admin in first.registry.all()] == ["users"]
    assert second.registry.all() == ()


def test_default_include_creates_application_scoped_sites() -> None:
    first = include_cabinet(FastAPI(), modules=())
    second = include_cabinet(FastAPI(), modules=())

    assert first is not second


def test_empty_site_renders_dashboard() -> None:
    app = FastAPI()
    include_cabinet(app, modules=(), site=CabinetSite(brand_name="Operations"))

    response = TestClient(app).get("/cabinet")

    assert response.status_code == 200
    assert "No management modules are available" in response.text
    assert "Operations" in response.text


def test_declared_action_dispatches_to_admin_handler() -> None:
    class ActionAdmin(CabinetAdmin):
        key = "actions"
        label = "Actions"
        actions = (ActionRoute(path="ping", method="POST", handler="ping"),)

        async def ping(self, request: Request) -> PlainTextResponse:
            return PlainTextResponse("pong")

    app = FastAPI()
    site = CabinetSite()
    site.register(ActionAdmin)
    include_cabinet(app, modules=(), site=site)

    response = TestClient(app).post("/cabinet/actions/ping")

    assert response.status_code == 200
    assert response.text == "pong"
