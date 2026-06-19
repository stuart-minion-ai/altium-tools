"""JLCPCB standard 2-layer rule pack.

All capability numbers below are traceable to JLCPCB's published PCB
manufacturing capabilities (see ``source``). Values are for the 2-layer, 1oz
outer-copper profile -- JLCPCB's most-ordered prototype service -- because its
min track/space (0.10mm) is copper-weight dependent and we must pin one weight.

JLCPCB publishes a richer capability table than PCBWay, so this pack honestly
carries MORE rule kinds (7 vs 5): JLCPCB states explicit numbers for via
geometry, hole-to-hole spacing, and solder-mask expansion that PCBWay does not.
This is the honesty gate working as intended -- a kind is carried only where the
vendor states a number, never by guessing.

Unit note: Altium ``.RUL`` files in this repo use mils. 1mm = 39.3701mil. Altium
emits mil values at 4-decimal precision (e.g. 0.25mm -> 9.8425mil).
"""

from __future__ import annotations

from ...core.model import DesignRule
from ..model import RulePack
from . import register

_SOURCE = "https://jlcpcb.com/capabilities/pcb-capabilities"
_CAPTURED = "2026-06-19"

# Format-verified kinds we deliberately DO NOT emit for JLCPCB, because JLCPCB's
# capabilities page states no interchangeable capability number for them.
# Format-verified does NOT license number-invention.
_OMITTED_KINDS: dict[str, str] = {
    "PasteMaskExpansion": "JLCPCB does not publish a paste/stencil-mask "
    "expansion value on its PCB capabilities page.",
    "SilkToSolderMaskClearance": "JLCPCB publishes pad-to-silkscreen (0.15mm), "
    "which is a silk-to-COPPER clearance, not the silk-to-solder-MASK gap this "
    "rule constrains (MINSILKSCREENTOMASKGAP); the two are not interchangeable.",
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


@register("jlcpcb")
def jlcpcb_standard_2layer() -> RulePack:
    rules = [
        # Min track width/spacing 0.10mm(4mil) at 1oz outer copper (JLCPCB's own
        # mil figure). Heavier copper widens this; 2oz=6.5mil, etc.
        _rule(
            "Width", "Width", "All", "All",
            COMMENT="JLCPCB 1oz min 0.10mm(4mil); wider for heavier copper",
            MAXLIMIT="500mil", MINLIMIT="4mil", PREFEREDWIDTH="10mil",
        ),
        # Min spacing 0.10mm(4mil) at 1oz (JLCPCB: "0.10/0.10 mm (4/4 mil)").
        _rule(
            "Clearance", "Clearance", "All", "All",
            COMMENT="JLCPCB 1oz min spacing 0.10mm(4mil)",
            GAP="4mil", GENERICCLEARANCE="4mil",
            IGNOREPADTOPADCLEARANCEINFOOTPRINT="TRUE", OBJECTCLEARANCES=" ",
        ),
        # Drill 0.15-6.3mm for 2-layer (JLCPCB drills 0.15mm on 2-layer, finer
        # than PCBWay's 0.2mm floor). 0.15mm=5.9055mil, 6.3mm=248.0315mil.
        _rule(
            "HoleSize", "HoleSize", "All", "All",
            COMMENT="JLCPCB 2-layer drill 0.15-6.3mm",
            ABSOLUTEVALUES="TRUE", MAXLIMIT="248.0315mil", MINLIMIT="5.9055mil",
            MAXPERCENT="80.000", MINPERCENT="20.000",
        ),
        # PTH annular ring >=0.20mm(7.874mil) -- larger than PCBWay's 0.15mm.
        _rule(
            "MinimumAnnularRing", "MinimumAnnularRing", "All", "All",
            COMMENT="JLCPCB PTH annular ring >=0.20mm(7.874mil)",
            MINIMUMRING="7.874mil",
        ),
        # Via geometry: JLCPCB states min via hole 0.15mm(5.9055mil) / min via
        # diameter 0.25mm(9.8425mil) EXPLICITLY (no derivation needed). Preferred
        # bumped to a robust 0.3mm hole / 0.6mm pad above the published floor;
        # max = drill ceiling 6.3mm hole(248.0315mil) / 6.6mm pad(259.8425mil).
        _rule(
            "RoutingVias", "RoutingVias", "All", "All",
            COMMENT="JLCPCB min via hole 0.15mm / min via dia 0.25mm",
            HOLEWIDTH="11.811mil", WIDTH="23.622mil", VIASTYLE="Through Hole",
            MINHOLEWIDTH="5.9055mil", MINWIDTH="9.8425mil",
            MAXHOLEWIDTH="248.0315mil", MAXWIDTH="259.8425mil",
        ),
        # Hole-to-hole spacing. JLCPCB publishes via-to-via 0.2mm AND
        # pad-to-pad 0.45mm. A single global (AnyNet/All) rule cannot express
        # both without pad-class scoping (deferred, YAGNI), so we use the more
        # restrictive 0.45mm(17.7165mil) -- guarantees manufacturability for any
        # hole pair; via-only 0.2mm relaxation needs a future pad-class scope.
        _rule(
            "HoleToHoleClearance", "HoleToHoleClearance", "All", "All",
            COMMENT="JLCPCB pad hole-to-hole 0.45mm (via-only 0.2mm needs scoping)",
            GAP="17.7165mil", ALLOWSTACKEDMICROVIAS="TRUE",
        ),
        # Solder-mask expansion 1:1 (JLCPCB: "Soldermask Expansion 1:1") = zero
        # expansion, mask opening equals copper pad. 0mil is a byte-valid Altium
        # value (seen in fixture). 1:1 is JLCPCB's stated process.
        _rule(
            "SolderMaskExpansion", "SolderMaskExpansion", "All", "All",
            COMMENT="JLCPCB soldermask expansion 1:1 (zero)",
            EXPANSION="0mil",
        ),
    ]
    return RulePack(
        vendor="jlcpcb",
        title="JLCPCB standard 2-layer (1oz)",
        source=_SOURCE,
        captured=_CAPTURED,
        rules=rules,
    )
