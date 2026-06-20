"""Tests for the manufacturer rule-pack registry and built-in packs."""

from __future__ import annotations

from altiumtools.rules import emit_rul, parse_rul
from altiumtools.rules.manufacturers import available, get_pack


def test_pcbway_registered():
    assert "pcbway" in available()


def test_pcbway_pack_has_provenance():
    pack = get_pack("pcbway")
    assert pack.source.startswith("https://")
    assert pack.captured  # ISO date present
    assert pack.title


def test_pcbway_pack_only_uses_supported_kinds():
    from altiumtools.rules.fields import SUPPORTED_KINDS

    pack = get_pack("pcbway")
    for r in pack.rules:
        assert r.kind in SUPPORTED_KINDS


def test_pcbway_pack_emits_and_reparses():
    pack = get_pack("pcbway")
    data = emit_rul(pack)
    back = parse_rul(data)
    assert len(back) == len(pack.rules)
    kinds = [r["RULEKIND"] for r in back]
    assert "Width" in kinds
    assert "Clearance" in kinds
    assert "MinimumAnnularRing" in kinds


def test_pcbway_emits_routing_vias_from_published_drill_and_ring():
    """RoutingVias is the one extra kind PCBWay actually publishes numbers for:
    min drill 0.2mm(7.874mil) + min via annular ring 0.15mm -> 0.5mm(19.685mil)
    minimum pad. Locks those derived floors so a refactor can't drift them."""
    pack = get_pack("pcbway")
    via = next(r for r in pack.rules if r.kind == "RoutingVias")
    assert via.constraints["MINHOLEWIDTH"] == "7.874mil"  # 0.2mm published drill
    assert via.constraints["MINWIDTH"] == "19.685mil"  # 0.2 + 2*0.15mm ring
    assert via.constraints["VIASTYLE"] == "Through Hole"


def test_pcbway_does_not_emit_unpublished_kinds():
    """Honesty gate: kinds whose FORMAT we verified but whose NUMBERS PCBWay does
    not publish must stay out of the pack. Emitting Altium UI-default values as
    'PCBWay rules' would be the generation-side equivalent of fabricating
    decoded geometry. This test fails the moment someone guess-fills one."""
    from altiumtools.rules.manufacturers.pcbway import _OMITTED_KINDS

    pack = get_pack("pcbway")
    emitted = {r.kind for r in pack.rules}
    for kind, reason in _OMITTED_KINDS.items():
        assert kind not in emitted, f"{kind} must stay omitted: {reason}"


def test_pcbway_width_floor_matches_published_spec():
    pack = get_pack("pcbway")
    width = next(r for r in pack.rules if r.kind == "Width")
    assert width.constraints["MINLIMIT"] == "4mil"  # PCBWay min manufacturable


def test_jlcpcb_registered():
    assert "jlcpcb" in available()


def test_jlcpcb_pack_has_provenance():
    pack = get_pack("jlcpcb")
    assert pack.source.startswith("https://")
    assert pack.captured  # ISO date present
    assert pack.title


def test_jlcpcb_pack_only_uses_supported_kinds():
    from altiumtools.rules.fields import SUPPORTED_KINDS

    pack = get_pack("jlcpcb")
    for r in pack.rules:
        assert r.kind in SUPPORTED_KINDS


def test_jlcpcb_pack_emits_and_reparses():
    pack = get_pack("jlcpcb")
    data = emit_rul(pack)
    back = parse_rul(data)
    assert len(back) == len(pack.rules)
    kinds = [r["RULEKIND"] for r in back]
    assert "Width" in kinds
    assert "Clearance" in kinds
    assert "MinimumAnnularRing" in kinds


def test_jlcpcb_carries_richer_kind_set_than_pcbway():
    """JLCPCB publishes explicit numbers PCBWay does not (via geometry,
    hole-to-hole, solder-mask expansion), so it HONESTLY carries more kinds.
    This is the honesty gate working as intended -- more kinds only because the
    vendor states more numbers, never by guessing. Locks the published-only
    superset so a refactor can't silently drop a documented kind."""
    jlc = {r.kind for r in get_pack("jlcpcb").rules}
    pcb = {r.kind for r in get_pack("pcbway").rules}
    # Kinds JLCPCB publishes that PCBWay omits.
    assert "HoleToHoleClearance" in jlc
    assert "SolderMaskExpansion" in jlc
    assert {"HoleToHoleClearance", "SolderMaskExpansion"}.isdisjoint(pcb)
    # JLCPCB is a strict superset of the kinds the two share publishing on.
    assert jlc >= {"Width", "Clearance", "HoleSize", "MinimumAnnularRing", "RoutingVias"}


def test_jlcpcb_emits_via_from_explicitly_published_numbers():
    """Unlike PCBWay (where via-pad size is DERIVED), JLCPCB states min via hole
    0.15mm(5.9055mil) and min via diameter 0.25mm(9.8425mil) directly. Lock those
    published floors so a refactor can't drift them."""
    via = next(r for r in get_pack("jlcpcb").rules if r.kind == "RoutingVias")
    assert via.constraints["MINHOLEWIDTH"] == "5.9055mil"  # 0.15mm published
    assert via.constraints["MINWIDTH"] == "9.8425mil"  # 0.25mm published
    assert via.constraints["VIASTYLE"] == "Through Hole"


def test_jlcpcb_does_not_emit_unpublished_kinds():
    """Honesty gate: kinds whose FORMAT we verified but whose NUMBERS JLCPCB does
    not publish (paste-mask expansion; silk-to-MASK gap, which is not the same as
    the pad-to-silk-COPPER value JLCPCB does state) must stay out of the pack."""
    from altiumtools.rules.manufacturers.jlcpcb import _OMITTED_KINDS

    pack = get_pack("jlcpcb")
    emitted = {r.kind for r in pack.rules}
    for kind, reason in _OMITTED_KINDS.items():
        assert kind not in emitted, f"{kind} must stay omitted: {reason}"


def test_jlcpcb_width_floor_matches_published_spec():
    pack = get_pack("jlcpcb")
    width = next(r for r in pack.rules if r.kind == "Width")
    assert width.constraints["MINLIMIT"] == "4mil"  # JLCPCB 1oz min 0.10mm


def test_jlcpcb_soldermask_expansion_is_one_to_one():
    """JLCPCB states '1:1' soldermask expansion = zero. 0mil is byte-valid in
    Altium (seen in fixture). Guards against someone substituting a UI default."""
    pack = get_pack("jlcpcb")
    smt = next(r for r in pack.rules if r.kind == "SolderMaskExpansion")
    assert smt.constraints["EXPANSION"] == "0mil"


def test_jlcpcb_hole_to_hole_expresses_both_published_numbers():
    """JLCPCB publishes via-to-via 0.2mm AND pad-to-pad 0.45mm. Rather than
    collapse to the strictest single value, we emit a dual-priority pair scoped
    on the universal object-kind predicate IsVia: P1 IsVia->0.2mm wins for via
    pairs, P2 All->0.45mm governs everything else. Locks both published numbers,
    their priority ordering, and the project-independent IsVia scope (never a
    project-specific net/pad class)."""
    holes = [r for r in get_pack("jlcpcb").rules if r.kind == "HoleToHoleClearance"]
    assert len(holes) == 2
    via = next(r for r in holes if r.scope == "IsVia")
    catch_all = next(r for r in holes if r.scope == "All")
    # Via pair: published 0.2mm, highest priority so it wins the overlap.
    assert via.constraints["GAP"] == "7.874mil"  # 0.2mm
    assert via.constraints["PRIORITY"] == "1"
    assert via.constraints["SCOPE2EXPRESSION"] == "IsVia"
    # Catch-all: published 0.45mm pad/other, lower priority.
    assert catch_all.constraints["GAP"] == "17.7165mil"  # 0.45mm
    assert catch_all.constraints["PRIORITY"] == "2"
    # Scopes must be universal object-kind / global, never project-specific
    # class references a fab cannot know.
    for r in holes:
        assert "NetClass" not in r.scope and "PadClass" not in r.scope


def test_jlcpcb_dual_hole_rules_emit_and_reparse_distinctly():
    """The two HoleToHoleClearance rules must survive an emit->parse round trip
    as two distinct rules (distinct UNIQUEID/NAME), proving the dual-priority
    pattern is byte-safe and not silently deduplicated."""
    pack = get_pack("jlcpcb")
    back = parse_rul(emit_rul(pack))
    h2h = [r for r in back if r["RULEKIND"] == "HoleToHoleClearance"]
    assert len(h2h) == 2
    assert len({r["UNIQUEID"] for r in h2h}) == 2  # distinct ids
    gaps = {r["GAP"] for r in h2h}
    assert gaps == {"7.874mil", "17.7165mil"}


# --- OSH Park -------------------------------------------------------------


def test_oshpark_registered():
    assert "oshpark" in available()


def test_oshpark_pack_has_provenance():
    pack = get_pack("oshpark")
    assert pack.source.startswith("https://")
    assert pack.captured  # ISO date present
    assert pack.title


def test_oshpark_pack_only_uses_supported_kinds():
    from altiumtools.rules.fields import SUPPORTED_KINDS

    pack = get_pack("oshpark")
    for r in pack.rules:
        assert r.kind in SUPPORTED_KINDS


def test_oshpark_pack_emits_and_reparses():
    pack = get_pack("oshpark")
    data = emit_rul(pack)
    back = parse_rul(data)
    assert len(back) == len(pack.rules)
    kinds = [r["RULEKIND"] for r in back]
    assert "Width" in kinds
    assert "Clearance" in kinds
    assert "MinimumAnnularRing" in kinds


def test_oshpark_numbers_match_published_fixed_process():
    """OSH Park is a FIXED published process (no copper-weight tiers), so every
    number is a literal table cell on the official spec page. Lock the published
    2-layer values so a refactor can't drift them: 6mil trace/space, 10mil min
    drill, 260mil max drill, 5mil annular ring."""
    pack = get_pack("oshpark")
    by_kind = {r.kind: r for r in pack.rules}
    assert by_kind["Width"].constraints["MINLIMIT"] == "6mil"
    assert by_kind["Clearance"].constraints["GAP"] == "6mil"
    assert by_kind["HoleSize"].constraints["MINLIMIT"] == "10mil"
    assert by_kind["HoleSize"].constraints["MAXLIMIT"] == "260mil"
    assert by_kind["MinimumAnnularRing"].constraints["MINIMUMRING"] == "5mil"


def test_oshpark_via_pad_is_drill_plus_two_rings():
    """OSH Park states min drill (10mil) and annular ring (5mil) but not a via
    pad diameter, so the pad floor is DERIVED: 10 + 2*5 = 20mil (same published-
    inputs arithmetic the PCBWay pack uses). Min via hole = published min drill."""
    via = next(r for r in get_pack("oshpark").rules if r.kind == "RoutingVias")
    assert via.constraints["MINHOLEWIDTH"] == "10mil"  # published min drill
    assert via.constraints["MINWIDTH"] == "20mil"  # 10 + 2*5mil ring
    assert via.constraints["VIASTYLE"] == "Through Hole"


def test_oshpark_does_not_emit_unpublished_kinds():
    """Honesty gate: kinds whose FORMAT we verified but whose NUMBERS OSH Park
    does not publish as the value this rule constrains must stay omitted."""
    from altiumtools.rules.manufacturers.oshpark import _OMITTED_KINDS

    pack = get_pack("oshpark")
    emitted = {r.kind for r in pack.rules}
    for kind, reason in _OMITTED_KINDS.items():
        assert kind not in emitted, f"{kind} must stay omitted: {reason}"


def test_get_unknown_vendor_raises():
    import pytest

    with pytest.raises(KeyError):
        get_pack("does-not-exist")
