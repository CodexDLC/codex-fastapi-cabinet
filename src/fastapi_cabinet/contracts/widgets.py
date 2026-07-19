from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class DashboardWidget(BaseModel):
    """Declarative widget connected to an async provider."""

    model_config = ConfigDict(frozen=True)

    key: str
    title: str
    provider: str
    kind: str
    order: int = 100
    permission: str | None = None
    span: int = Field(default=1, ge=1, le=4)


class MetricWidget(DashboardWidget):
    kind: Literal["metric"] = "metric"
    icon: str = ""


class TableWidget(DashboardWidget):
    kind: Literal["table"] = "table"


class ListWidget(DashboardWidget):
    kind: Literal["list"] = "list"


class ChartWidget(DashboardWidget):
    kind: Literal["chart"] = "chart"
    chart_type: Literal["bar", "line", "pie", "doughnut"] = "bar"


class MetricWidgetMap(BaseModel):
    kind: Literal["metric"] = "metric"
    key: str
    title: str
    value: str
    subtitle: str | None = None
    trend: str | None = None
    icon: str = ""
    span: int = Field(default=1, ge=1, le=4)


class TableColumnMap(BaseModel):
    key: str
    label: str
    align: Literal["left", "center", "right"] = "left"


class TableActionMap(BaseModel):
    key: str
    label: str
    action_url: str
    method: Literal["POST", "PUT", "PATCH", "DELETE"] = "POST"
    css_class: str = ""
    permission: str | None = None


class TableWidgetMap(BaseModel):
    kind: Literal["table"] = "table"
    key: str
    title: str
    columns: list[TableColumnMap]
    rows: list[dict[str, Any]]
    row_href_key: str | None = None
    actions: list[TableActionMap] = Field(default_factory=list)
    empty_message: str = "No data."
    span: int = Field(default=1, ge=1, le=4)


class ListWidgetMap(BaseModel):
    kind: Literal["list"] = "list"
    key: str
    title: str
    items: list[str] = Field(default_factory=list)
    empty_message: str = "No data."
    span: int = Field(default=1, ge=1, le=4)


class ChartDatasetMap(BaseModel):
    label: str
    data: list[float]
    color: str | None = None


class ChartWidgetMap(BaseModel):
    kind: Literal["chart"] = "chart"
    key: str
    title: str
    chart_type: Literal["bar", "line", "pie", "doughnut"]
    labels: list[str]
    datasets: list[ChartDatasetMap]
    height: int = Field(default=280, ge=120, le=1200)
    span: int = Field(default=1, ge=1, le=4)


type WidgetMap = MetricWidgetMap | TableWidgetMap | ListWidgetMap | ChartWidgetMap
