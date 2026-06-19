"""Data model for a generated set of manufacturer design rules.

We deliberately reuse ``altiumtools.model.DesignRule`` (kind/name/scope/enabled/
constraints) rather than inventing a parallel type -- a generated rule and a
parsed rule are the same concept. ``RulePack`` adds only the provenance metadata
that makes a generated ``.RUL`` auditable: which manufacturer it targets, where
the capability numbers came from, and when they were captured.

Provenance is not decoration. The honesty gate forbids shipping fabricated fab
capability numbers, so every pack records its ``source`` (URL / document) and
``captured`` (ISO date). The CLI surfaces these so a user can verify the rules
against the fab's current spec.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..model import DesignRule


@dataclass
class RulePack:
    """An ordered set of design rules for one manufacturer profile."""

    vendor: str  # machine id, e.g. "pcbway"
    title: str = ""  # human label, e.g. "PCBWay 2-layer 1oz standard"
    source: str = ""  # provenance: URL or document the numbers came from
    captured: str = ""  # ISO date the capability data was captured/verified
    rules: list[DesignRule] = field(default_factory=list)
    meta: dict[str, str] = field(default_factory=dict)

    def kinds(self) -> list[str]:
        """Distinct rule kinds in this pack, in first-seen order."""

        seen: dict[str, None] = {}
        for r in self.rules:
            seen.setdefault(r.kind, None)
        return list(seen)
