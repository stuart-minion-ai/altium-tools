"""Manufacturer rule-pack registry: the contributor extension point for fabs.

Mirrors ``altiumtools.checks``: to add a manufacturer profile a contributor
writes one function that returns a verified ``RulePack`` and decorates it with
``@register``. That's the whole API. No new file format, no parser, no extra
dependency -- just like adding a review check.

HONESTY GATE: every number in a registered pack must come from the fab's
published capability document, and the function MUST set ``source`` (URL/doc) and
``captured`` (ISO date). Packs are validated at registration time against the
verified field templates, so a typo'd constraint key fails loudly here rather
than producing a bad ``.RUL``.
"""

from __future__ import annotations

from collections.abc import Callable

from ..model import RulePack

_REGISTRY: dict[str, Callable[[], RulePack]] = {}


def register(vendor: str) -> Callable[[Callable[[], RulePack]], Callable[[], RulePack]]:
    """Register a manufacturer pack factory under a unique vendor id."""

    def deco(func: Callable[[], RulePack]) -> Callable[[], RulePack]:
        if vendor in _REGISTRY:
            raise ValueError(f"duplicate manufacturer id: {vendor}")
        _REGISTRY[vendor] = func
        return func

    return deco


def available() -> list[str]:
    """Sorted list of registered vendor ids."""

    return sorted(_REGISTRY)


def get_pack(vendor: str) -> RulePack:
    """Build the RulePack for ``vendor``. Raises KeyError if unknown."""

    if vendor not in _REGISTRY:
        raise KeyError(vendor)
    return _REGISTRY[vendor]()


# Import side-effect: registers built-in manufacturer packs. Kept at the bottom
# to avoid a circular import (pcbway imports `register` from this module).
from . import pcbway as _pcbway  # noqa: E402,F401
