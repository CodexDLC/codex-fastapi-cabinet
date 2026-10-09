# Project guidance

For work on this library, read
[fastapi-cabinet-maintainer](.agents/skills/fastapi-cabinet-maintainer/SKILL.md).
Load only its references relevant to the task.

The project maintainer skill belongs in `.agents/skills/`. The consumer skill shipped
with the Python distribution belongs in `src/fastapi_cabinet/agent_skills/resources/`.
Maintain consumer instructions in that canonical source; do not install a generated
consumer copy over this repository's maintainer guidance.
