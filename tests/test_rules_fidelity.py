"""Differential format-fidelity tests for the .RUL generator.

The honesty gate in one test file: take the REAL, Altium-exported fixture, parse
each record, render it back, and assert byte-for-byte equality. If our field
order, terminator handling, or encoding drifts from what Altium actually writes,
these tests go red. This is the smoke test that substitutes for "I tested it in
Altium" -- we diff against Altium's own output instead.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from altiumtools.core.model import DesignRule
from altiumtools.rules import emit_rul, parse_rul
from altiumtools.rules.emit import render_record, stable_uniqueid
from altiumtools.rules.fields import (
    CONSTRAINT_FIELDS,
    ENVELOPE_FIELDS,
    SUPPORTED_KINDS,
    field_order,
)
from altiumtools.rules.model import RulePack

FIXTURE = Path(__file__).parent / "fixtures" / "rul" / "pcbway_base.RUL"


def _raw_lines() -> list[str]:
    text = FIXTURE.read_bytes().decode("latin-1")
    return [ln for ln in text.split("\n") if ln.strip()]


def _records_by_kind() -> dict[str, tuple[str, dict[str, str]]]:
    """First raw line + parsed record for each supported kind in the fixture."""

    raw = _raw_lines()
    parsed = parse_rul(FIXTURE.read_bytes())
    out: dict[str, tuple[str, dict[str, str]]] = {}
    for line, rec in zip(raw, parsed, strict=True):
        kind = rec.get("RULEKIND", "")
        if kind in SUPPORTED_KINDS and kind not in out:
            out[kind] = (line, rec)
    return out


def test_fixture_present_and_nonempty():
    assert FIXTURE.exists()
    assert len(_raw_lines()) == 46


def test_all_supported_kinds_present_in_fixture():
    have = {rec.get("RULEKIND") for rec in parse_rul(FIXTURE.read_bytes())}
    missing = set(SUPPORTED_KINDS) - have
    assert not missing, f"supported kinds absent from fixture: {sorted(missing)}"


@pytest.mark.parametrize("kind", SUPPORTED_KINDS)
def test_parse_preserves_full_field_envelope(kind):
    """Parsed record's key sequence == verified template order, exactly."""

    by_kind = _records_by_kind()
    assert kind in by_kind, f"{kind} not exercised by fixture"
    _, rec = by_kind[kind]
    assert tuple(rec.keys()) == field_order(kind)


@pytest.mark.parametrize("kind", SUPPORTED_KINDS)
def test_render_reproduces_real_record_byte_for_byte(kind):
    """parse -> render round-trips the real Altium line exactly (incl ¶)."""

    by_kind = _records_by_kind()
    line, rec = by_kind[kind]
    assert render_record(kind, rec) == line


def test_envelope_is_18_fields():
    assert len(ENVELOPE_FIELDS) == 18


def test_no_constraint_field_collides_with_envelope():
    env = set(ENVELOPE_FIELDS)
    for kind, fields in CONSTRAINT_FIELDS.items():
        assert env.isdisjoint(fields), f"{kind} constraint overlaps envelope"


def test_emit_rul_roundtrips_through_parse():
    """A generated pack parses back to the same kinds/names we put in."""

    rules = [
        DesignRule(
            kind="Width",
            name="Width",
            scope="All",
            enabled=True,
            constraints={
                "SCOPE2EXPRESSION": "All",
                "MAXLIMIT": "500mil",
                "MINLIMIT": "8mil",
                "PREFEREDWIDTH": "10mil",
            },
        ),
        DesignRule(
            kind="SolderMaskExpansion",
            name="SolderMaskExpansion",
            scope="All",
            enabled=True,
            constraints={"SCOPE2EXPRESSION": "All", "EXPANSION": "1.9685mil"},
        ),
    ]
    pack = RulePack(vendor="pcbway", rules=rules)
    data = emit_rul(pack)
    back = parse_rul(data)
    assert [r["RULEKIND"] for r in back] == ["Width", "SolderMaskExpansion"]
    assert back[0]["MINLIMIT"] == "8mil"
    assert tuple(back[0].keys()) == field_order("Width")


def test_emit_is_deterministic():
    rule = DesignRule(
        kind="SolderMaskExpansion",
        name="SME",
        scope="All",
        enabled=True,
        constraints={"SCOPE2EXPRESSION": "All", "EXPANSION": "2mil"},
    )
    pack = RulePack(vendor="pcbway", rules=[rule])
    assert emit_rul(pack) == emit_rul(pack)


def test_stable_uniqueid_shape():
    uid = stable_uniqueid("Width", "Width", "All")
    assert len(uid) == 8
    assert uid.isalpha() and uid.isupper()


def test_unknown_constraint_field_rejected():
    from altiumtools.rules.emit import IncompleteRecord

    rule = DesignRule(
        kind="SolderMaskExpansion",
        name="x",
        scope="All",
        enabled=True,
        constraints={"EXPANSION": "2mil", "BOGUS": "1"},
    )
    with pytest.raises(IncompleteRecord):
        emit_rul(RulePack(vendor="v", rules=[rule]))
