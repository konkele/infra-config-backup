"""
Providers are registered via import side effects.
No dynamic loading.
"""

from . import pfsense  # noqa
from . import portainer  # noqa
from . import truenas_ws  # noqa
from . import unifi  # noqa

from .registry import provider, get_provider

__all__ = ["provider", "get_provider"]