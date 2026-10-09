---
name: fastapi-cabinet-maintainer
description: Develop and verify the codex-fastapi-cabinet library in its source repository, including contracts, routing, rendering, packaged assets, and agent skill delivery. Use for library maintenance, not application-specific cabinet integration.
---

# FastAPI Cabinet maintainer

This repository owns the `codex-fastapi-cabinet` distribution and `fastapi_cabinet` import package.
Read only the source and guidance relevant to the requested change.

## Ownership and reading routes

- Contracts or routing: read [architecture](../../../docs/architecture.md), the affected modules in `src/fastapi_cabinet/contracts/`, and `registry.py`, `runtime.py`, or `site.py` as needed.
- Providers and rendering: read the affected `rendering/*_mapper.py` and its page/widget contracts. Providers return validated maps; application services supply their data.
- Templates or assets: read [customization](../../../docs/customization.md) and the affected `templates/cabinet/` and `static/` files. Keep Jinja rendering and template override paths; do not introduce a replacement frontend stack as a routine UI change.
- Consumer instructions or installer: read `src/fastapi_cabinet/agent_skills/resources/SKILL.md` and [delivery guide](../../../docs/agent-skills.md). Canonical consumer payload belongs under `src/fastapi_cabinet/agent_skills/resources/`; installed consumer copies and their manifests are generated, not authoring locations.
- Release preparation: inspect `pyproject.toml`, `CHANGELOG.md`, and `.github/workflows/release.yml`. The package version is derived from Git tags through hatch-vcs. A build from an untagged checkout is not proof of a release version.

Paths in backticks are relative to the repository root. This skill is project-owned guidance and is not copied into consuming applications by the library installer.

## Invariants

- Keep contracts, registry, and path logic independent of an ORM, application sessions, and product-specific services. `CabinetSite` composes the FastAPI/Jinja adapters.
- Register admins explicitly into an application-scoped registry. Preserve duplicate-key rejection and deterministic ordering. Module loading accepts `register_cabinet(registry)` or `CABINET_ADMINS`.
- Preserve mount/static path behavior and route ordering; inspect `tests/test_runtime.py` and `tests/test_site.py` when changing it.
- The host owns authentication, authorization policy, transactions, validation of mutations, and CSRF protection. The default permission provider allows access; hiding navigation never replaces endpoint checks.
- Keep public exports in `src/fastapi_cabinet/__init__.py` aligned with supported contracts. Examples and EN/RU guides describe shipped behavior, not planned features.
- Installer changes must preserve unrelated consumer files and project instructions. Test ownership, modified files, malformed manifests/markers, and filesystem failure behavior before claiming safe lifecycle support.

## Verification by affected surface

Use the development environment installed from `uv.lock` (`uv sync --frozen --extra dev --extra docs` when setup is needed). Existing `.venv` tools can be used directly without resynchronizing it.

```text
ruff check src tests examples
mypy src tests examples
pytest
mkdocs build --strict
uv build
```

The full test suite enforces 90% coverage; a focused test run alone may fail this repository-wide threshold. Map changes to `tests/test_contracts.py` / `test_registry.py`, `test_loader.py`, `test_runtime.py` / `test_site.py`, `test_rendering.py` / `test_permissions_and_templates.py`, or `test_example.py`. Use the installer lifecycle tests for skill delivery changes. For visible UI changes, add browser evidence appropriate to the change; HTML assertions alone do not prove layout.

When delivery changes, inspect wheel and sdist contents and exercise the module CLI from a wheel installed into an isolated consumer environment, outside the source checkout. Verify the bundled skill's relevant examples and reference links. Recheck the affected project and consumer guidance when workflows or APIs change.

Release workflow additionally checks distribution metadata with `twine check` and validates a `vMAJOR.MINOR.PATCH` tag whose commit belongs to `main`. Report local checks separately from hosted CI and publication. Preparing a release does not authorize tagging or publishing it.
