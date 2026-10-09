---
name: codex-fastapi-cabinet
description: Build or maintain a FastAPI management UI using codex-fastapi-cabinet. Use for its cabinet modules, pages, widgets, providers, routing, or templates; skip unrelated FastAPI work.
---

# codex-fastapi-cabinet

Check the installed package version and source before changing a consumer project:

```bash
python -c "from importlib.metadata import version; import fastapi_cabinet; print(version('codex-fastapi-cabinet')); print(fastapi_cabinet.__file__)"
```

This managed skill describes the package version installed by the project command. After upgrading the package, run `python -m fastapi_cabinet.agent_skills update --project <project-directory>` to refresh it.

- For a module, async provider, page, widget, or application mount, read [composition](references/composition.md).
- For permissions, actions, forms, template overrides, and host security, read [integration](references/integration.md).

The library owns its shell, view maps, templates, and routing. The application owns authentication, permission decisions, persistence, transactions, and business operations. Keep application policies in project-owned skills; do not edit this installed skill or its manifest. Inspect package source and documentation when a reference does not cover the needed API.
