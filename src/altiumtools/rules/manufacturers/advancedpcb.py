"""Advanced Circuits / AdvancedPCB (APCT) standard 2-layer rule pack.

All capability numbers below are traceable to AdvancedPCB's two published
capability pages (see ``_SOURCE`` and the citations on each rule). Advanced
Circuits is an imperial-native US fab, so the published values are inches and
the mil figures here are exact conversions (1in = 1000mil) -- no rounding noise.

PIN: the "Standard" service column, 2-layer, 1oz outer copper -- Advanced
Circuits' everyday process, the honest analogue of the other packs' standard
profiles. The finer "Advanced"/"Development" columns require premium services.

Advanced Circuits publishes a via annular ring, a min+max finished hole, a
hole-to-hole edge spacing, and a soldermask swell, so this pack honestly carries
7 kinds, like JLCPCB and AISLER. Where the fab publishes an annular ring rather
than a finished via diameter, the via pad is DERIVED as drill + 2*ring (the same
honest derivation PCBWay/AISLER use), and the comment records the published
inputs.
"""

from __future__ import annotations

from ...core.model import DesignRule
from ..model import RulePack
from . import register

# Primary source; the tolerances page (annular ring, hole min/max, mask swell)
# is cited inline on each rule that draws from it.
_SOURCE = "https://www.advancedpcb.com/en-us/resources/manufacturing-capabilities/"
_TOLERANCES = "https://www.advancedpcb.com/en-us/resources/tolerances/"
_CAPTURED = "2026-06-19"

# Format-verified kinds we deliberately DO NOT emit for Advanced Circuits,
# because its capability pages state no interchangeable number for them.
# Format-verified does NOT license number-invention.
_OMITTED_KINDS: dict[str, str] = {
    "PasteMaskExpansion": "Advanced Circuits publishes a SOLDER-mask swell "
    "(0.005in over pad), not a paste/stencil-mask expansion; not interchangeable.",
    "SilkToSolderMaskClearance": "Advanced Circuits publishes a silkscreen min "
    "line width (0.005in), which is a line width, not the silk-to-solder-mask "
    "gap this rule constrains; not interchangeable.",
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


@register("advancedpcb")
def advancedpcb_standard_2layer() -> RulePack:
    rules = [
        # Outer layer width, 1oz Standard = 0.0055in (5.5mil).
        _rule(
            "Width", "Width", "All", "All",
            COMMENT="AdvancedPCB Standard outer width 1oz 0.0055in(5.5mil)",
            MAXLIMIT="500mil", MINLIMIT="5.5mil", PREFEREDWIDTH="10mil",
        ),
        # Outer layer space, 1oz Standard = 0.0055in (5.5mil).
        _rule(
            "Clearance", "Clearance", "All", "All",
            COMMENT="AdvancedPCB Standard outer space 1oz 0.0055in(5.5mil)",
            GAP="5.5mil", GENERICCLEARANCE="5.5mil",
            IGNOREPADTOPADCLEARANCEINFOOTPRINT="TRUE", OBJECTCLEARANCES=" ",
        ),
        # Finished hole: min 0.004in(4mil), max 0.250in(250mil) -- tolerances
        # page (larger holes are routed). Genuinely min+max bounded.
        _rule(
            "HoleSize", "HoleSize", "All", "All",
            COMMENT="AdvancedPCB finished hole 0.004-0.250in (tolerances page)",
            ABSOLUTEVALUES="TRUE", MAXLIMIT="250mil", MINLIMIT="4mil",
            MAXPERCENT="80.000", MINPERCENT="20.000",
        ),
        # Via annular ring 0.005in(5mil) -- tolerances page ("Pad Size/Annular
        # Ring": pad >= +0.010in over finished hole for vias -> ring 0.005in).
        _rule(
            "MinimumAnnularRing", "MinimumAnnularRing", "All", "All",
            COMMENT="AdvancedPCB via annular ring 0.005in(5mil) (tolerances page)",
            MINIMUMRING="5mil",
        ),
        # Via geometry: smallest mechanical PTH via 0.0059in(5.9mil) Standard
        # (capabilities); max via hole = 0.250in(250mil) published max PTH
        # finished hole. Via PADs DERIVED drill + 2*ring(0.005in):
        # min 0.0059+0.010=0.0159in(15.9mil), max 0.250+0.010=0.260in(260mil).
        _rule(
            "RoutingVias", "RoutingVias", "All", "All",
            COMMENT="AdvancedPCB via hole 0.0059-0.250in, pad=hole+2*ring(0.005in)",
            HOLEWIDTH="5.9mil", WIDTH="15.9mil", VIASTYLE="Through Hole",
            MINHOLEWIDTH="5.9mil", MINWIDTH="15.9mil",
            MAXHOLEWIDTH="250mil", MAXWIDTH="260mil",
        ),
        # Min hole-to-hole edge for PTH, Standard = 0.012in(12mil) (capabilities).
        _rule(
            "HoleToHoleClearance", "HoleToHoleClearance", "All", "All",
            COMMENT="AdvancedPCB min hole-to-hole edge PTH 0.012in(12mil)",
            GAP="12mil", ALLOWSTACKEDMICROVIAS="TRUE", PRIORITY="1",
        ),
        # Soldermask swell 0.005in over pad = 0.0025in/side -> expansion 2.5mil
        # (tolerances page "Soldermask Swell").
        _rule(
            "SolderMaskExpansion", "SolderMaskExpansion", "All", "All",
            COMMENT="AdvancedPCB soldermask swell 0.0025in/side(2.5mil)",
            EXPANSION="2.5mil",
        ),
    ]
    return RulePack(
        vendor="advancedpcb",
        title="Advanced Circuits / AdvancedPCB Standard (2-layer, 1oz)",
        source=_SOURCE,
        captured=_CAPTURED,
        rules=rules,
    )
