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


def test_get_unknown_vendor_raises():
    import pytest

    with pytest.raises(KeyError):
        get_pack("does-not-exist")
