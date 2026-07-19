from fastapi_cabinet import (
    DetailFieldMap,
    DetailPage,
    DetailPageMap,
    FormFieldMap,
    FormPage,
    FormPageMap,
    ListPage,
    ListPageMap,
    OperationActionMap,
    OperationPage,
    OperationPageMap,
    PaginationMap,
    TableColumnMap,
)


def test_page_declarations_have_stable_kinds() -> None:
    assert ListPage(key="list", label="List", path="items", provider="items.list").kind == "list"
    assert DetailPage(key="detail", label="Detail", path="items/{item_id}", provider="items.detail").kind == "detail"
    assert FormPage(key="create", label="Create", path="items/new", provider="items.create").kind == "form"
    assert OperationPage(key="ops", label="Operations", path="items/ops", provider="items.ops").kind == "operation"


def test_page_maps_validate_common_management_shapes() -> None:
    listing = ListPageMap(
        title="Users",
        columns=[TableColumnMap(key="email", label="Email")],
        rows=[{"email": "admin@example.test"}],
        pagination=PaginationMap(page=1, pages=1, total=1),
    )
    detail = DetailPageMap(
        title="User",
        fields=[DetailFieldMap(label="Email", value="admin@example.test")],
    )
    form = FormPageMap(
        title="Create user",
        action_url="/admin/users/create",
        fields=[FormFieldMap(name="email", label="Email", input_type="email", required=True)],
    )
    operation = OperationPageMap(
        title="Maintenance",
        actions=[OperationActionMap(key="reindex", label="Reindex", action_url="/admin/users/reindex")],
    )

    assert listing.pagination is not None
    assert listing.pagination.total == 1
    assert detail.fields[0].label == "Email"
    assert form.fields[0].required is True
    assert operation.actions[0].method == "POST"
