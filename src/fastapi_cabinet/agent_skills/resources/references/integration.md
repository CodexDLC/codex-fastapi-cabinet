# Host integration and security

The host FastAPI app must authenticate requests before cabinet access, guard the cabinet mount, and supply real permission checks. Pass a `PermissionProvider` implementation to `CabinetSite(permission_provider=...)`; its async `can(request, permission)` decides each named permission. The default provider allows declared permissions, so it is suitable only when the host already enforces access.

Declare permissions on admin modules, pages, widgets, sidebar items, and `ActionRoute` entries as needed. Navigation hiding is only presentation; cabinet routes check permission independently. Keep mutation authorization in application use cases too.

Form providers return `FormPageMap`. The host must set `request.state.csrf_token` when a form needs a token and validate it on mutation. Forms emit `csrf_token` and an `_method` field for semantic non-POST methods; method tunnelling needs host middleware. Implement action handlers on the admin class and bind them through `ActionRoute`; inspect `fastapi_cabinet/contracts/admin.py` and `site.py` for current signatures.

Override templates by passing `template_directories` to `CabinetSite`; for example a host file at `src/my_project/templates/cabinet/pages/detail.html` overrides the packaged detail page. Explicit host directories take precedence over a supplied `Jinja2Templates` loader, then package defaults. Keep generated paths under the cabinet mount unless an absolute path is intended. See the installed package's `docs/customization.md` when available.
