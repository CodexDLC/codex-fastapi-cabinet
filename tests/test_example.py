from examples.basic_app import app
from fastapi.testclient import TestClient


def test_basic_example_is_runnable() -> None:
    client = TestClient(app)

    dashboard = client.get("/management/users")
    listing = client.get("/management/users/all")
    detail = client.get("/management/users/1")

    assert dashboard.status_code == 200
    assert "Registered users" in dashboard.text
    assert listing.status_code == 200
    assert "operator@example.test" in listing.text
    assert detail.status_code == 200
    assert "Administrator" in detail.text
