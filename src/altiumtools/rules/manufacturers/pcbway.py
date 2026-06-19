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

# Rule kinds whose .RUL FORMAT we have verified byte-for-byte, but which we
# deliberately DO NOT emit for PCBWay because PCBWay's published manufacturing-
# tolerances page does not state a capability number for them. Format-verified
# does NOT license number-invention: emitting these with Altium's UI-default
# values (the values seen in the captured fixture) would be the generation-side
# equivalent of fabricating decoded geometry. A pack only carries a kind whose
# number is traceable to the vendor spec. Revisit if PCBWay publishes these.
_OMITTED_KINDS: dict[str, str] = {
    "HoleToHoleClearance": "PCBWay tolerances page states no min hole-to-hole gap.",
    "SolderMaskExpansion": "PCBWay does not publish a solder-mask expansion value.",
    "PasteMaskExpansion": "PCBWay does not publish a paste-mask expansion value.",
    "SilkToSolderMaskClearance": "PCBWay publishes min silk char width, not a "
    "silk-to-mask clearance; the two are not interchangeable.",
}


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
        # Routing via geometry. PCBWay publishes min drill 0.2mm(7.874mil) and
        # min via annular ring 0.15mm(6mil) -> a 0.2mm hole needs a 0.2+2*0.15 =
        # 0.5mm(19.685mil) pad. Preferred sizes bumped one cost tier (0.3mm hole
        # / 0.6mm pad) since holes <0.3mm incur extra charge. Max = drill ceiling
        # 6.3mm(248.0315mil) hole / 6.6mm(259.8425mil) pad.
        _rule(
            "RoutingVias", "RoutingVias", "All", "All",
            COMMENT="PCBWay min drill 0.2mm + via ring 0.15mm; <0.3mm extra charge",
            HOLEWIDTH="11.811mil", WIDTH="23.622mil", VIASTYLE="Through Hole",
            MINHOLEWIDTH="7.874mil", MINWIDTH="19.685mil",
            MAXHOLEWIDTH="248.0315mil", MAXWIDTH="259.8425mil",
        ),
    ]
    return RulePack(
        vendor="pcbway",
        title="PCBWay standard 2-layer (1oz)",
        source=_SOURCE,
        captured=_CAPTURED,
        rules=rules,
    )
