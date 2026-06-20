"""Seeed Fusion (Seeed Studio) standard FR4 rule pack.

All capability numbers below are traceable to Seeed Studio's published "Standard
Seeed Fusion PCB Service Specification" (FR4 substrate, 1oz outer copper; see
``_SOURCE``). Seeed's spec is MIXED-unit ("Units: mm or mil as specified"), so
each value is converted from the unit Seeed states as primary:

  * trace width/spacing are published imperial ("4/4 mil") -> emitted as-is;
  * drill/hole diameters are published metric ("0.2 - 5.8 mm") -> exact mil
    conversion (1mm = 39.3701mil);
  * annular rings and hole-to-hole spacings are published imperial with a
    rounded metric in parentheses ("0.152 mm (6 mil)", "0.1 mm (4 mil)",
    "0.3 mm (12 mil)") -> the clean imperial figure is emitted, since the metric
    is the rounded form (6mil = 0.1524mm, Seeed truncates to 0.152mm).

Seeed publishes a solder-mask DAM/sliver minimum (>=0.1mm), which is a mask
sliver width, NOT a pad solder-mask expansion/swell -- and the format layer has
no sliver kind -- so Seeed honestly carries 6 kinds (one fewer than AISLER,
which does publish a mask expansion). Where Seeed publishes a via annular ring
rather than a finished via pad, the via pad is DERIVED as hole + 2*ring (the same
honest derivation the AISLER/PCBWay packs use), and the comment records the
published inputs.
"""

from __future__ import annotations

from ...core.model import DesignRule
from ..model import RulePack
from . import register

_SOURCE = "https://support.seeed.cc/portal/en/kb/articles/fusion-pcb-specification"
_CAPTURED = "2026-06-19"

# Format-verified kinds we deliberately DO NOT emit for Seeed, because Seeed's
# specification states no interchangeable capability number for them.
# Format-verified does NOT license number-invention.
_OMITTED_KINDS: dict[str, str] = {
    "SolderMaskExpansion": "Seeed publishes a solder-mask DAM/sliver minimum "
    "(>=0.1mm green), which is a mask sliver width, not the pad solder-mask "
    "expansion/swell this rule constrains; not interchangeable.",
    "PasteMaskExpansion": "Seeed does not publish a paste/stencil-mask expansion "
    "value in its Fusion PCB specification.",
    "SilkToSolderMaskClearance": "Seeed publishes a pad-to-silkscreen clearance "
    "(0.1524mm/6mil), which is a silk-to-COPPER clearance, not the silk-to-"
    "solder-MASK gap this rule constrains; not interchangeable.",
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


@register("seeed")
def seeed_standard_fr4() -> RulePack:
    rules = [
        # Min trace width 4mil (1oz), Seeed's published imperial trace spec.
        _rule(
            "Width", "Width", "All", "All",
            COMMENT="Seeed Fusion min trace width 4mil (1oz)",
            MAXLIMIT="500mil", MINLIMIT="4mil", PREFEREDWIDTH="10mil",
        ),
        # Min trace spacing 4mil (1oz), Seeed's published imperial spacing spec.
        _rule(
            "Clearance", "Clearance", "All", "All",
            COMMENT="Seeed Fusion min trace spacing 4mil (1oz)",
            GAP="4mil", GENERICCLEARANCE="4mil",
            IGNOREPADTOPADCLEARANCEINFOOTPRINT="TRUE", OBJECTCLEARANCES=" ",
        ),
        # PTH finished hole 0.2-5.8mm (metric spec). 0.2mm=7.874mil,
        # 5.8mm=228.3466mil. Genuinely min+max bounded.
        _rule(
            "HoleSize", "HoleSize", "All", "All",
            COMMENT="Seeed Fusion PTH hole 0.2-5.8mm (metric spec)",
            ABSOLUTEVALUES="TRUE", MAXLIMIT="228.3466mil", MINLIMIT="7.874mil",
            MAXPERCENT="80.000", MINPERCENT="20.000",
        ),
        # PTH annular ring 6mil (Seeed "0.152mm (6mil)" -> clean imperial; via
        # ring 4mil is used in the RoutingVias derivation below).
        _rule(
            "MinimumAnnularRing", "MinimumAnnularRing", "All", "All",
            COMMENT="Seeed Fusion PTH annular ring 6mil (via ring 4mil)",
            MINIMUMRING="6mil",
        ),
        # Via geometry: Seeed via holes 0.2-0.5mm (metric) = 7.874-19.685mil and
        # via annular ring 4mil ("0.1mm (4mil)"). Via PADs DERIVED hole + 2*ring:
        # min 7.874+2*4=15.874mil, max 19.685+2*4=27.685mil.
        _rule(
            "RoutingVias", "RoutingVias", "All", "All",
            COMMENT="Seeed Fusion via hole 0.2-0.5mm, annular ring 4mil",
            HOLEWIDTH="7.874mil", WIDTH="15.874mil", VIASTYLE="Through Hole",
            MINHOLEWIDTH="7.874mil", MINWIDTH="15.874mil",
            MAXHOLEWIDTH="19.685mil", MAXWIDTH="27.685mil",
        ),
        # Min distance between plated holes: vias 12mil ("0.3mm (12mil)"),
        # PTH 18mil ("0.45mm (18mil)"). Global floor pinned to the via minimum.
        _rule(
            "HoleToHoleClearance", "HoleToHoleClearance", "All", "All",
            COMMENT="Seeed Fusion hole-to-hole via 12mil (PTH 18mil)",
            GAP="12mil", ALLOWSTACKEDMICROVIAS="TRUE", PRIORITY="1",
        ),
    ]
    return RulePack(
        vendor="seeed",
        title="Seeed Fusion standard FR4 (2-layer, 1oz)",
        source=_SOURCE,
        captured=_CAPTURED,
        rules=rules,
    )
