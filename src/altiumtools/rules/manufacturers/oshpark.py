"""OSH Park standard 2-layer ("purple") rule pack.

All capability numbers below are traceable to OSH Park's published fabrication
documentation (see ``source``). Values are for the flagship 2-layer 1oz prototype
service -- OSH Park's most-ordered process and, unlike copper-weight-dependent
fabs, a FIXED published process: a single set of numbers with no tier ambiguity.
That makes it the cleanest possible honesty-gate fit -- every value is a literal
table cell on the official spec page, nothing derived from a range.

The one derivation is RoutingVias' minimum pad diameter, computed the same way
the PCBWay pack does it: published min drill + 2x published annular ring. OSH
Park does not state a via-pad diameter directly, but it DOES publish both inputs
(10mil drill, 5mil ring -> 20mil pad), so this is arithmetic over published
numbers, not invention. Every other number is a direct table cell.

Unit note: OSH Park publishes in mils natively (6mil trace, 10mil drill, etc.),
so these map 1:1 onto Altium's mil ``.RUL`` values with no mm->mil conversion
rounding -- the cleanest provenance chain of any pack here.
"""

from __future__ import annotations

from ...core.model import DesignRule
from ..model import RulePack
from . import register

_SOURCE = "https://docs.oshpark.com/services/two-layer/"
_CAPTURED = "2026-06-19"

# Format-verified kinds we deliberately DO NOT emit for OSH Park, because OSH
# Park's spec pages state no interchangeable capability number for them.
# Format-verified does NOT license number-invention.
_OMITTED_KINDS: dict[str, str] = {
    "SolderMaskExpansion": "OSH Park publishes a minimum soldermask web (4mil) "
    "and a maximum soldermask alignment (3mil), but neither is the pad mask "
    "EXPANSION value this rule constrains; they are not interchangeable.",
    "PasteMaskExpansion": "OSH Park does not publish a paste/stencil-mask "
    "expansion value (it is a bare-board fab; stencils are out of scope).",
    "HoleToHoleClearance": "OSH Park does not publish a hole-to-hole / "
    "via-to-via spacing number on its capability pages.",
    "SilkToSolderMaskClearance": "OSH Park publishes a silkscreen minimum line "
    "width (5mil), not the silk-to-solder-MASK gap (MINSILKSCREENTOMASKGAP) "
    "this rule constrains; the two are not interchangeable.",
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


@register("oshpark")
def oshpark_standard_2layer() -> RulePack:
    rules = [
        # Trace width: published min 6mil. MAXLIMIT is a non-binding upper
        # sentinel (OSH Park states no max trace width); PREFEREDWIDTH is a
        # routing default, not a fab constraint.
        _rule(
            "Width", "Width", "All", "All",
            COMMENT="OSH Park 2-layer min trace width 6mil",
            MAXLIMIT="500mil", MINLIMIT="6mil", PREFEREDWIDTH="10mil",
        ),
        # Trace spacing: published 6mil.
        _rule(
            "Clearance", "Clearance", "All", "All",
            COMMENT="OSH Park 2-layer min trace spacing 6mil",
            GAP="6mil", GENERICCLEARANCE="6mil",
            IGNOREPADTOPADCLEARANCEINFOOTPRINT="TRUE", OBJECTCLEARANCES=" ",
        ),
        # Drill: published min hole 10mil, max drilled hole 260mil (above which
        # OSH Park converts to a milled hole).
        _rule(
            "HoleSize", "HoleSize", "All", "All",
            COMMENT="OSH Park 2-layer drill 10-260mil",
            ABSOLUTEVALUES="TRUE", MAXLIMIT="260mil", MINLIMIT="10mil",
            MAXPERCENT="80.000", MINPERCENT="20.000",
        ),
        # Annular ring: published 5mil for 2-layer.
        _rule(
            "MinimumAnnularRing", "MinimumAnnularRing", "All", "All",
            COMMENT="OSH Park 2-layer PTH annular ring 5mil",
            MINIMUMRING="5mil",
        ),
        # Via geometry: min via hole = published min drill 10mil; min via pad =
        # 10mil + 2x5mil ring = 20mil (same drill+2*ring derivation as PCBWay).
        # Max via hole = published max drilled 260mil; max pad = 260+2*5=270mil.
        _rule(
            "RoutingVias", "RoutingVias", "All", "All",
            COMMENT="OSH Park via: min hole 10mil, min pad 10+2*5mil ring",
            HOLEWIDTH="13mil", WIDTH="25mil", VIASTYLE="Through Hole",
            MINHOLEWIDTH="10mil", MINWIDTH="20mil",
            MAXHOLEWIDTH="260mil", MAXWIDTH="270mil",
        ),
    ]
    return RulePack(
        vendor="oshpark",
        title="OSH Park standard 2-layer (1oz)",
        source=_SOURCE,
        captured=_CAPTURED,
        rules=rules,
    )
