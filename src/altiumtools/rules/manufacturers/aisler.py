"""AISLER standard 2-layer rule pack.

All capability numbers below are traceable to AISLER's published design rules
for its most-ordered profile -- 2 Layer, 1.6mm, 35um copper, HASL finish (see
``source``). AISLER is a metric-native EU fab, so the published values are
metric; the mil figures here are exact conversions (1mm = 39.3701mil) emitted at
Altium's 4-decimal mil precision, matching the repo's mil-based ``.RUL`` idiom.

AISLER publishes explicit via annular-ring and hole-to-hole (min drill spacing)
numbers, so this pack honestly carries 7 kinds, like JLCPCB. Each kind is
carried only because AISLER states a number for it -- never by guessing. Where
AISLER publishes an annular ring rather than a finished via diameter, the via
pad is DERIVED as drill + 2*ring (the same honest derivation PCBWay uses), and
the comment records the published inputs.
"""

from __future__ import annotations

from ...core.model import DesignRule
from ..model import RulePack
from . import register

_SOURCE = "https://community.aisler.net/t/2-layer-1-6-mm-35-m-hasl-design-rules/3735"
_CAPTURED = "2026-06-19"

# Format-verified kinds we deliberately DO NOT emit for AISLER, because AISLER's
# design-rule page states no interchangeable capability number for them.
# Format-verified does NOT license number-invention.
_OMITTED_KINDS: dict[str, str] = {
    "PasteMaskExpansion": "AISLER does not publish a paste/stencil-mask "
    "expansion value on its PCB design-rule page.",
    "SilkToSolderMaskClearance": "AISLER publishes silkscreen-to-pad spacing "
    "(125um), which is a silk-to-COPPER clearance, not the silk-to-solder-MASK "
    "gap this rule constrains (MINSILKSCREENTOMASKGAP); not interchangeable.",
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


@register("aisler")
def aisler_standard_2layer() -> RulePack:
    rules = [
        # Min track width 0.2mm(7.874mil) published for 35um HASL.
        _rule(
            "Width", "Width", "All", "All",
            COMMENT="AISLER min tracewidth 0.2mm(7.874mil), 35um HASL",
            MAXLIMIT="500mil", MINLIMIT="7.874mil", PREFEREDWIDTH="10mil",
        ),
        # Min copper-to-copper spacing 0.15mm(5.9055mil).
        _rule(
            "Clearance", "Clearance", "All", "All",
            COMMENT="AISLER min copper/copper spacing 0.15mm(5.9055mil)",
            GAP="5.9055mil", GENERICCLEARANCE="5.9055mil",
            IGNOREPADTOPADCLEARANCEINFOOTPRINT="TRUE", OBJECTCLEARANCES=" ",
        ),
        # PTH drill 0.5-5.6mm. 0.5mm=19.685mil, 5.6mm=220.4726mil.
        _rule(
            "HoleSize", "HoleSize", "All", "All",
            COMMENT="AISLER PTH drill 0.5-5.6mm",
            ABSOLUTEVALUES="TRUE", MAXLIMIT="220.4726mil", MINLIMIT="19.685mil",
            MAXPERCENT="80.000", MINPERCENT="20.000",
        ),
        # PTH annular ring >=0.3mm(11.811mil).
        _rule(
            "MinimumAnnularRing", "MinimumAnnularRing", "All", "All",
            COMMENT="AISLER PTH annular ring >=0.3mm(11.811mil)",
            MINIMUMRING="11.811mil",
        ),
        # Via geometry: AISLER states min via drill 0.3mm(11.811mil), max via
        # drill 0.45mm(17.7165mil) and min via annular ring 0.2mm. Via pads are
        # DERIVED drill + 2*ring: min 0.3+2*0.2=0.7mm(27.5591mil), max
        # 0.45+2*0.2=0.85mm(33.4646mil). Preferred pinned to the published floor.
        _rule(
            "RoutingVias", "RoutingVias", "All", "All",
            COMMENT="AISLER via drill 0.3-0.45mm, annular ring 0.2mm",
            HOLEWIDTH="11.811mil", WIDTH="27.5591mil", VIASTYLE="Through Hole",
            MINHOLEWIDTH="11.811mil", MINWIDTH="27.5591mil",
            MAXHOLEWIDTH="17.7165mil", MAXWIDTH="33.4646mil",
        ),
        # Min drill spacing 0.3mm(11.811mil) -- AISLER's published hole-to-hole.
        _rule(
            "HoleToHoleClearance", "HoleToHoleClearance", "All", "All",
            COMMENT="AISLER min drill spacing 0.3mm(11.811mil)",
            GAP="11.811mil", ALLOWSTACKEDMICROVIAS="TRUE", PRIORITY="1",
        ),
        # Suggested soldermask expansion 0.05mm(1.9685mil) per published spec.
        _rule(
            "SolderMaskExpansion", "SolderMaskExpansion", "All", "All",
            COMMENT="AISLER suggested soldermask expansion 0.05mm(1.9685mil)",
            EXPANSION="1.9685mil",
        ),
    ]
    return RulePack(
        vendor="aisler",
        title="AISLER standard 2-layer (1.6mm, 35um, HASL)",
        source=_SOURCE,
        captured=_CAPTURED,
        rules=rules,
    )
