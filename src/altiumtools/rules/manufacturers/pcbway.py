"""PCBWay standard 2-layer rule pack.

All capability numbers below are traceable to PCBWay's published manufacturing
tolerances (see ``source``). Where PCBWay distinguishes "manufacturable minimum"
from "recommended / no-extra-charge", we use the value that keeps a design inside
the no-surprise-cost envelope and note the manufacturable floor in the comment.

Unit note: Altium ``.RUL`` files in this repo use mils. 1mm = 39.3701mil.
"""

from __future__ import annotations

from ...core.model import DesignRule
from ..model import RulePack
from . import register

_SOURCE = "https://www.pcbway.com/pcb_prototype/PCB_Manufacturing_tolerances.html"
_CAPTURED = "2026-06-19"


def _rule(kind: str, name: str, scope1: str, scope2: str, **constraints: str) -> DesignRule:
    """Construct a global (AnyNet) DesignRule with explicit scopes + constraints."""

    return DesignRule(
        kind=kind,
        name=name,
        scope=scope1,
        enabled=True,
        constraints={"SCOPE2EXPRESSION": scope2, **constraints},
    )


@register("pcbway")
def pcbway_standard_2layer() -> RulePack:
    rules = [
        # Min manufacturable trace 4mil(0.1mm); 6mil recommended to save cost.
        _rule(
            "Width", "Width", "All", "All",
            COMMENT="PCBWay min 4mil(0.1mm); 6mil recommended",
            MAXLIMIT="500mil", MINLIMIT="4mil", PREFEREDWIDTH="10mil",
        ),
        # Min manufacturable spacing 4mil(0.1mm).
        _rule(
            "Clearance", "Clearance", "All", "All",
            COMMENT="PCBWay min spacing 4mil(0.1mm)",
            GAP="4mil", GENERICCLEARANCE="4mil",
            IGNOREPADTOPADCLEARANCEINFOOTPRINT="TRUE", OBJECTCLEARANCES=" ",
        ),
        # Drill 0.2-6.3mm; holes <0.3mm(11.811mil) incur extra charge -> use as floor.
        _rule(
            "HoleSize", "HoleSize", "All", "All",
            COMMENT="PCBWay drill 0.2-6.3mm; <0.3mm extra charge",
            ABSOLUTEVALUES="TRUE", MAXLIMIT="248.0315mil", MINLIMIT="11.811mil",
            MAXPERCENT="80.000", MINPERCENT="20.000",
        ),
        # Min annular ring 0.15mm(6mil) -> 5.9055mil.
        _rule(
            "MinimumAnnularRing", "MinimumAnnularRing", "All", "All",
            COMMENT="PCBWay min annular ring 0.15mm(6mil)",
            MINIMUMRING="5.9055mil",
        ),
    ]
    return RulePack(
        vendor="pcbway",
        title="PCBWay standard 2-layer (1oz)",
        source=_SOURCE,
        captured=_CAPTURED,
        rules=rules,
    )
