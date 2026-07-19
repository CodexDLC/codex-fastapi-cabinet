from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from fastapi_cabinet.contracts.widgets import TableActionMap, TableColumnMap


class CabinetPage(BaseModel):
    """Declarative management page connected to an async provider."""

    model_config = ConfigDict(frozen=True)

    key: str
    label: str
    path: str
    provider: str
    kind: str
    order: int = 100
    permission: str | None = None
    template: str | None = None


class ListPage(CabinetPage):
    kind: Literal["list"] = "list"


class DetailPage(CabinetPage):
    kind: Literal["detail"] = "detail"


class FormPage(CabinetPage):
    kind: Literal["form"] = "form"


class OperationPage(CabinetPage):
    kind: Literal["operation"] = "operation"


class FilterChoiceMap(BaseModel):
    value: str
    label: str
    selected: bool = False


class FilterFieldMap(BaseModel):
    name: str
    label: str
    value: str = ""
    input_type: Literal["text", "search", "select", "checkbox"] = "text"
    choices: list[FilterChoiceMap] = Field(default_factory=list)


class PaginationMap(BaseModel):
    page: int = Field(ge=1)
    pages: int = Field(ge=1)
    total: int = Field(ge=0)
    previous_url: str | None = None
    next_url: str | None = None


class ListPageMap(BaseModel):
    kind: Literal["list"] = "list"
    title: str
    subtitle: str | None = None
    columns: list[TableColumnMap]
    rows: list[dict[str, Any]]
    filters: list[FilterFieldMap] = Field(default_factory=list)
    pagination: PaginationMap | None = None
    row_href_key: str | None = None
    actions: list[TableActionMap] = Field(default_factory=list)
    create_url: str | None = None
    create_label: str = "Create"
    empty_message: str = "No records found."


class DetailFieldMap(BaseModel):
    label: str
    value: Any = None
    key: str | None = None


class DetailSectionMap(BaseModel):
    title: str
    fields: list[DetailFieldMap] = Field(default_factory=list)


class PageLinkMap(BaseModel):
    label: str
    url: str
    css_class: str = ""


class DetailPageMap(BaseModel):
    kind: Literal["detail"] = "detail"
    title: str
    subtitle: str | None = None
    fields: list[DetailFieldMap] = Field(default_factory=list)
    sections: list[DetailSectionMap] = Field(default_factory=list)
    actions: list[PageLinkMap] = Field(default_factory=list)
    back_url: str | None = None


class FormChoiceMap(BaseModel):
    value: str
    label: str
    selected: bool = False


class FormFieldMap(BaseModel):
    name: str
    label: str
    input_type: Literal[
        "text",
        "email",
        "password",
        "number",
        "textarea",
        "select",
        "checkbox",
        "hidden",
        "url",
    ] = "text"
    value: Any = ""
    placeholder: str = ""
    help_text: str | None = None
    required: bool = False
    disabled: bool = False
    choices: list[FormChoiceMap] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class FormPageMap(BaseModel):
    kind: Literal["form"] = "form"
    title: str
    action_url: str
    fields: list[FormFieldMap]
    method: Literal["POST", "PUT", "PATCH"] = "POST"
    subtitle: str | None = None
    submit_label: str = "Save"
    cancel_url: str | None = None
    cancel_label: str = "Cancel"
    errors: list[str] = Field(default_factory=list)


class OperationActionMap(BaseModel):
    key: str
    label: str
    action_url: str
    method: Literal["POST", "PUT", "PATCH", "DELETE"] = "POST"
    description: str | None = None
    confirmation: str | None = None
    css_class: str = ""


class OperationPageMap(BaseModel):
    kind: Literal["operation"] = "operation"
    title: str
    subtitle: str | None = None
    description: str | None = None
    actions: list[OperationActionMap] = Field(default_factory=list)
    notices: list[str] = Field(default_factory=list)


type PageMap = ListPageMap | DetailPageMap | FormPageMap | OperationPageMap
