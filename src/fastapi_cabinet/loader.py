from collections.abc import Sequence
from importlib import import_module
from inspect import signature
from types import ModuleType

from fastapi_cabinet.contracts.admin import CabinetAdmin
from fastapi_cabinet.exceptions import CabinetModuleLoadError
from fastapi_cabinet.registry import CabinetRegistry

type CabinetModuleRef = str | ModuleType


def load_cabinet_modules(
    modules: Sequence[CabinetModuleRef],
    registry: CabinetRegistry,
) -> tuple[ModuleType, ...]:
    """Load modules through an explicit hook or a CABINET_ADMINS declaration."""

    loaded: list[ModuleType] = []
    for ref in modules:
        try:
            module = import_module(ref) if isinstance(ref, str) else ref
        except ImportError as exc:
            raise CabinetModuleLoadError(f"Could not import cabinet module {ref!r}.") from exc

        hook = getattr(module, "register_cabinet", None)
        declarations = getattr(module, "CABINET_ADMINS", None)
        if hook is not None:
            _call_registration_hook(module, hook, registry)
        elif declarations is not None:
            _register_declarations(module, declarations, registry)
        else:
            raise CabinetModuleLoadError(
                f"Cabinet module {module.__name__!r} must expose register_cabinet(registry) or CABINET_ADMINS."
            )
        loaded.append(module)
    return tuple(loaded)


def _call_registration_hook(module: ModuleType, hook: object, registry: CabinetRegistry) -> None:
    if not callable(hook):
        raise CabinetModuleLoadError(
            f"Cabinet module {module.__name__!r} defines register_cabinet, but it is not callable."
        )
    try:
        parameters = signature(hook).parameters
    except (TypeError, ValueError) as exc:
        raise CabinetModuleLoadError(
            f"Cabinet module {module.__name__!r} has an invalid register_cabinet hook."
        ) from exc
    if len(parameters) != 1:
        raise CabinetModuleLoadError(
            f"Cabinet module {module.__name__!r} register_cabinet hook must accept exactly one registry."
        )
    hook(registry)


def _register_declarations(module: ModuleType, declarations: object, registry: CabinetRegistry) -> None:
    if not isinstance(declarations, (tuple, list)):
        raise CabinetModuleLoadError(f"Cabinet module {module.__name__!r} CABINET_ADMINS must be a sequence.")
    for declaration in declarations:
        if not isinstance(declaration, CabinetAdmin) and not (
            isinstance(declaration, type) and issubclass(declaration, CabinetAdmin)
        ):
            raise CabinetModuleLoadError(
                f"Cabinet module {module.__name__!r} contains a non-CabinetAdmin declaration."
            )
        registry.register(declaration)
