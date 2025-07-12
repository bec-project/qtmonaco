"""Platform-specific resource loading for qtmonaco."""

import platform
import sys
import warnings
from typing import Optional


def load_platform_resources() -> bool:
    """
    Load the appropriate Monaco RCC file for the current platform.

    Returns:
        bool: True if resources were loaded successfully, False otherwise.
    """
    current_platform = platform.system().lower()

    # Map platform names to resource modules
    platform_modules = {
        "darwin": "qtmonaco._monaco_rcc_macos",
        "linux": "qtmonaco._monaco_rcc_linux",
    }

    # Try to load platform-specific resources first
    if current_platform in platform_modules:
        try:
            module_name = platform_modules[current_platform]
            __import__(module_name)
            print(f"Loaded {current_platform} platform resources")
            return True
        except ImportError as e:
            warnings.warn(
                f"Could not load platform-specific resources for {current_platform}: {e}. "
                f"Trying fallback options."
            )

    # Fallback: try to load any available platform resources
    fallback_order = ["qtmonaco._monaco_rcc_macos", "qtmonaco._monaco_rcc_linux"]

    for fallback_module in fallback_order:
        try:
            __import__(fallback_module)
            warnings.warn(
                f"Using fallback resources from {fallback_module} "
                f"(current platform: {current_platform})"
            )
            return True
        except ImportError:
            continue

    # Final fallback: try legacy module name
    try:
        import qtmonaco._monaco_rcc

        warnings.warn("Using legacy resource module")
        return True
    except ImportError:
        pass

    raise ImportError(
        f"No Monaco resources available for platform '{current_platform}'. "
        f"Available modules: {list(platform_modules.values())}"
    )


# Automatically load resources when module is imported
_resources_loaded = False


def ensure_resources_loaded():
    """Ensure that Monaco resources are loaded exactly once."""
    global _resources_loaded
    if not _resources_loaded:
        load_platform_resources()
        _resources_loaded = True
