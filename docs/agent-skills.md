# Agent skill for consuming projects

The Python package includes an optional offline skill for coding agents working on a FastAPI application that uses `codex-fastapi-cabinet`. Install it into an existing project with the Python environment where this package is installed:

```bash
python -m fastapi_cabinet.agent_skills install --project /path/to/project
python -m fastapi_cabinet.agent_skills status --project /path/to/project
```

On Windows, replace `/path/to/project` with a project path such as `D:\work\my-app`. The command requires `--project`. Normal library use does not require installing the skill.

The installer copies a compact router and focused API references to `.agents/skills/codex-fastapi-cabinet/`, records the installed package version and SHA-256 hashes in `.manifest.json`, and adds a delimited link in the project's root `AGENTS.md`. Existing project instructions outside that block remain intact. The payload comes from the installed package; no network access or running FastAPI application is needed.

After upgrading the Python package, refresh the skill separately:

```bash
python -m fastapi_cabinet.agent_skills update --project /path/to/project
python -m fastapi_cabinet.agent_skills status --project /path/to/project
```

To remove only the managed content:

```bash
python -m fastapi_cabinet.agent_skills delete --project /path/to/project
```

`status` exits `0` only when the installed files and marker match the package payload and manifest. An absent, stale, modified, or corrupt installation exits `1`. `install` is safe to repeat when current. `update` and `delete` refuse to overwrite or remove a locally modified or missing managed file; move custom instructions into a separate project skill and restore or back up the edited file before retrying. New payload files cannot overwrite unowned files. Symlinks and Windows reparse points on managed paths are rejected. Writes are staged with in-process rollback for ordinary failures; there is no crash or concurrent-process transaction guarantee.

The installed skill describes public library mechanisms. Keep application-specific authentication, data access, and business rules in project-owned instructions. Do not edit the copied skill or its manifest to customize library guidance.
