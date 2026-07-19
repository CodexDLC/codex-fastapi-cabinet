from typing import ClassVar

from fastapi import FastAPI, Request

from fastapi_cabinet import (
    CabinetAdmin,
    CabinetProvider,
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

USERS = [
    {"id": 1, "email": "admin@example.test", "role": "Administrator", "status": "active"},
    {"id": 2, "email": "operator@example.test", "role": "Operator", "status": "active"},
]


async def user_count(request: Request) -> MetricWidgetMap:
    return MetricWidgetMap(
        key="users-total",
        title="Registered users",
        value=str(len(USERS)),
        subtitle="Example in-memory data",
        span=1,
    )


async def user_list(request: Request) -> ListPageMap:
    return ListPageMap(
        title="Users",
        subtitle="A generic list page supplied by the library",
        columns=[
            TableColumnMap(key="email", label="Email"),
            TableColumnMap(key="role", label="Role"),
            TableColumnMap(key="status", label="Status"),
        ],
        rows=[
            {
                **user,
                "href": f"/management/users/{user['id']}",
            }
            for user in USERS
        ],
        row_href_key="href",
        pagination=PaginationMap(page=1, pages=1, total=len(USERS)),
    )


async def user_detail(request: Request) -> DetailPageMap:
    user_id = int(request.path_params["user_id"])
    user = next(item for item in USERS if item["id"] == user_id)
    return DetailPageMap(
        title=str(user["email"]),
        subtitle="A generic detail page supplied by the library",
        back_url="/management/users/all",
        fields=[
            DetailFieldMap(label="Role", value=user["role"]),
            DetailFieldMap(label="Status", value=user["status"]),
        ],
    )


class UsersAdmin(CabinetAdmin):
    key = "users"
    label = "Users"
    group_label = "Site"
    sidebar = (SidebarItem(key="all", label="All users", path="all"),)
    dashboard_widgets = (
        MetricWidget(key="users-total", title="Registered users", provider="users.count"),
    )
    pages = (
        ListPage(key="all", label="All users", path="all", provider="users.list"),
        DetailPage(key="detail", label="User", path="{user_id}", provider="users.detail"),
    )
    providers: ClassVar[dict[str, CabinetProvider]] = {
        "users.count": user_count,
        "users.list": user_list,
        "users.detail": user_detail,
    }


app = FastAPI(title="FastAPI Cabinet example")
cabinet = CabinetSite(brand_name="Example control room")
cabinet.register(UsersAdmin)
include_cabinet(app, site=cabinet, mount_path="/management")
