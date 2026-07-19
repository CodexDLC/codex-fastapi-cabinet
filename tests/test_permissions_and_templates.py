from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from fastapi_cabinet import CabinetAdmin, CabinetSite, DetailPage, DetailPageMap, include_cabinet


class DenyPermissions:
    async def can(self, request: Request, permission: str) -> bool:
        return False


async def detail_provider(request: Request) -> DetailPageMap:
    return DetailPageMap(title="Default detail")


class SecureAdmin(CabinetAdmin):
    key = "secure"
    label = "Secure"
    permission = "secure.view"
    pages = (DetailPage(key="detail", label="Detail", path="detail", provider="secure.detail"),)
    providers = {"secure.detail": detail_provider}


def test_admin_permission_is_enforced() -> None:
    app = FastAPI()
    site = CabinetSite(permission_provider=DenyPermissions())
    site.register(SecureAdmin)
    include_cabinet(app, modules=(), site=site)

    assert TestClient(app).get("/cabinet/secure").status_code == 403


def test_host_template_directory_overrides_package_template(tmp_path: Path) -> None:
    override = tmp_path / "cabinet" / "pages"
    override.mkdir(parents=True)
    override.joinpath("detail.html").write_text("HOST: {{ page.title }}", encoding="utf-8")

    app = FastAPI()
    site = CabinetSite(template_directories=(tmp_path,))
    site.register(SecureAdmin)
    include_cabinet(app, modules=(), site=site)

    response = TestClient(app).get("/cabinet/secure/detail")

    assert response.status_code == 200
    assert response.text == "HOST: Default detail"
