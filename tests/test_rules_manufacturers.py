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


def test_get_unknown_vendor_raises():
    import pytest

    with pytest.raises(KeyError):
        get_pack("does-not-exist")
