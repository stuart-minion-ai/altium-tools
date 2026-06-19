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


def test_pcbway_width_floor_matches_published_spec():
    pack = get_pack("pcbway")
    width = next(r for r in pack.rules if r.kind == "Width")
    assert width.constraints["MINLIMIT"] == "4mil"  # PCBWay min manufacturable


def test_get_unknown_vendor_raises():
    import pytest

    with pytest.raises(KeyError):
        get_pack("does-not-exist")
