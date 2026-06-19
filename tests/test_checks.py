"""Tests for the review-check framework and built-in checks."""

from __future__ import annotations

from altiumtools.checks import Report, Severity, run_checks
from altiumtools.checks import builtin as _builtin  # noqa: F401
from altiumtools.core.model import Component, Design, DesignRule, Net


def _ids(design: Design) -> list[str]:
    return [f.check_id for f in run_checks(design)]


def test_missing_designator_flagged():
    d = Design(components=[Component(designator="R?", comment="10k")])
    assert "SCH001" in _ids(d)


def test_duplicate_designator_flagged():
    d = Design(
        components=[
            Component(designator="R1", comment="10k", footprint="0402"),
            Component(designator="R1", comment="1k", footprint="0402"),
        ]
    )
    assert "SCH002" in _ids(d)


def test_missing_value_only_for_passives():
    d = Design(
        components=[
            Component(designator="R5", footprint="0402"),  # passive, no value -> flag
            Component(designator="U1", footprint="QFP", comment=""),  # IC, ok
        ]
    )
    ids = _ids(d)
    assert "SCH003" in ids
    # Exactly one SCH003 (the resistor, not the IC).
    assert sum(1 for f in run_checks(d) if f.check_id == "SCH003") == 1


def test_missing_footprint_flagged():
    d = Design(components=[Component(designator="C1", comment="100n")])
    assert "PCB001" in _ids(d)


def test_single_node_net_flagged():
    d = Design(nets=[Net(name="NetR1_1", node_count=1)])
    assert "PCB002" in _ids(d)


def test_no_clearance_rule_flagged_when_pcb_present():
    d = Design(pcb_docs=["b.PcbDoc"])
    assert "RUL001" in _ids(d)
    # With a clearance rule present, it is not flagged.
    d2 = Design(
        pcb_docs=["b.PcbDoc"],
        rules=[DesignRule(kind="Clearance", name="c", constraints={"gap": "0.2mm"})],
    )
    assert "RUL001" not in _ids(d2)


def test_clean_design_has_no_findings():
    d = Design(
        components=[
            Component(designator="R1", comment="10k", footprint="0402"),
            Component(designator="U1", comment="STM32", footprint="LQFP48"),
        ],
    )
    assert _ids(d) == []


def test_report_severity_aggregation():
    d = Design(components=[Component(designator="", comment="x")])  # SCH001 + PCB001
    rep = Report(list(run_checks(d)))
    assert rep.errors >= 1
    assert rep.worst() is Severity.ERROR


def test_check_select_filters():
    d = Design(components=[Component(designator="R?", comment="")])
    only = [f.check_id for f in run_checks(d, select={"SCH001"})]
    assert set(only) == {"SCH001"}
