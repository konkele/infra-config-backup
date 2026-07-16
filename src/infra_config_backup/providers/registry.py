from typing import Dict, Type

_PROVIDER_REGISTRY: Dict[str, type] = {}


def provider(name: str):
    def wrapper(cls):
        _PROVIDER_REGISTRY[name] = cls
        return cls
    return wrapper


def get_provider(name: str):
    if name not in _PROVIDER_REGISTRY:
        raise KeyError(f"Unknown provider: {name}")
    return _PROVIDER_REGISTRY[name]