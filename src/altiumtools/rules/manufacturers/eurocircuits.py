"""Eurocircuits standard-pool rule pack (Pattern Class 6, Drill Class C).

All capability numbers below are traceable to Eurocircuits' single published
"PCB Design Classification Overview" table (see ``source``). Eurocircuits is a
metric-native EU fab; the table prints both mm and an own mil column, so where
Eurocircuits states a mil figure we use it verbatim (the same vendor's-own-mil
idiom the JLCPCB pack uses), and DERIVED values use exact conversion
(1mm = 39.3701mil) at Altium's 4-decimal mil precision.

PIN: Pattern Class 6 -- the finest design class available across ALL Eurocircuits
services (it is the last column marked "All Services"; Classes 7+ require the
premium S/DZ/RF pools) -- paired with Drill Class C and 35um/1oz base copper.
This is the strictest rule set that still manufactures in Eurocircuits' cheap
STANDARD pool, so it is the honest "standard 2-layer" profile.

Eurocircuits' classification table publishes track/space, annular ring, and a
minimum drill (Drill Class), but NOT a maximum finished hole, so HoleSize is
omitted (see ``_OMITTED_KINDS``) -- the minimum-drill datum instead flows, fully
published, into the via floor. This pack therefore carries 4 honest kinds.
"""

from __future__ import annotations

from ...core.model import DesignRule
from ..model import RulePack
from . import register

_SOURCE = "https://www.eurocircuits.com/technical-guidelines/pcb-design-guidelines/classification/"
_CAPTURED = "2026-06-19"

# Format-verified kinds we deliberately DO NOT emit for Eurocircuits, because the
# classification table states no interchangeable capability number for them.
# Format-verified does NOT license number-invention.
_OMITTED_KINDS: dict[str, str] = {
    "HoleSize": "Eurocircuits' classification table publishes a MIN production "
    "drill (Drill Class) but NO maximum finished hole diameter; the min+max-"
    "bounded HoleSize rule cannot be completed from this single source. The "
    "published min-drill datum is carried via RoutingVias instead.",
    "SolderMaskExpansion": "The classification table publishes no soldermask "
    "expansion value.",
    "PasteMaskExpansion": "Eurocircuits does not publish a paste/stencil-mask "
    "expansion value on the classification table.",
    "SilkToSolderMaskClearance": "The classification table publishes no "
    "silk-to-solder-mask clearance value.",
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


@register("eurocircuits")
def eurocircuits_standard_pool() -> RulePack:
    rules = [
        # OTW outer track width, Pattern Class 6 = 0.150mm, vendor's own 6mil.
        _rule(
            "Width", "Width", "All", "All",
            COMMENT="Eurocircuits Class 6 OTW track width 0.150mm(6mil)",
            MAXLIMIT="500mil", MINLIMIT="6mil", PREFEREDWIDTH="10mil",
        ),
        # OTT/OTP/OPP outer copper spacing, Class 6 = 0.150mm, vendor's own 6mil.
        _rule(
            "Clearance", "Clearance", "All", "All",
            COMMENT="Eurocircuits Class 6 OTT/OTP/OPP spacing 0.150mm(6mil)",
            GAP="6mil", GENERICCLEARANCE="6mil",
            IGNOREPADTOPADCLEARANCEINFOOTPRINT="TRUE", OBJECTCLEARANCES=" ",
        ),
        # OAR outer annular ring (PTH), Class 6 = 0.125mm, vendor's own 5mil.
        _rule(
            "MinimumAnnularRing", "MinimumAnnularRing", "All", "All",
            COMMENT="Eurocircuits Class 6 OAR PTH annular ring 0.125mm(5mil)",
            MINIMUMRING="5mil",
        ),
        # Via geometry, all from the published table: min via finished hole =
        # Drill Class C min PTH 0.25mm (vendor's own 10mil); max via finished
        # hole = Note A default 0.45mm (vendor's own 18mil). Via PADs DERIVED as
        # hole + 2*OAR(0.125mm): min 0.25+0.25=0.50mm(19.685mil),
        # max 0.45+0.25=0.70mm(27.5591mil). Preferred pinned to the floor.
        _rule(
            "RoutingVias", "RoutingVias", "All", "All",
            COMMENT="Eurocircuits via hole 0.25-0.45mm, pad=hole+2*OAR(0.125mm)",
            HOLEWIDTH="10mil", WIDTH="19.685mil", VIASTYLE="Through Hole",
            MINHOLEWIDTH="10mil", MINWIDTH="19.685mil",
            MAXHOLEWIDTH="18mil", MAXWIDTH="27.5591mil",
        ),
    ]
    return RulePack(
        vendor="eurocircuits",
        title="Eurocircuits standard pool (Class 6, Drill C, 1oz)",
        source=_SOURCE,
        captured=_CAPTURED,
        rules=rules,
    )
