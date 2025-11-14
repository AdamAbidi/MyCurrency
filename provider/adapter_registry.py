from importlib import import_module
from django.conf import settings
from typing import Type
from provider.adapters.base import BaseProviderAdapter

_cache = {}

def get_adapter_class(adapter_key: str) -> Type[BaseProviderAdapter]:
    """
        Resolve an adapter class from the CURRENCY_ADAPTERS setting.

        Raises:
            LookupError: if no adapter is configured for the given key.
    """
    if adapter_key in _cache:
        return _cache[adapter_key]

    try:
        path = settings.CURRENCY_ADAPTERS[adapter_key]
    except KeyError as e:
        raise LookupError(f"No adapter configured for key '{adapter_key}'") from e

    module_path, class_name = path.split(":")
    module = import_module(module_path)
    cls = getattr(module, class_name)
    _cache[adapter_key] = cls
    return cls