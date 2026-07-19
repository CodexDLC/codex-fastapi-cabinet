class CabinetError(Exception):
    """Base error for cabinet configuration and rendering failures."""


class CabinetRegistrationError(CabinetError):
    """Raised when an admin declaration cannot be registered."""


class CabinetDuplicateKeyError(CabinetRegistrationError):
    """Raised when two admin declarations use the same key."""


class CabinetModuleLoadError(CabinetError):
    """Raised when a configured cabinet module cannot be loaded."""


class CabinetProviderError(CabinetError):
    """Raised when a provider cannot be resolved or returns an invalid map."""
