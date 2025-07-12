from .monaco import Monaco
from .platform_resources import ensure_resources_loaded

# Ensure resources are loaded when the package is imported
ensure_resources_loaded()

__all__ = ["Monaco", "ensure_resources_loaded"]
