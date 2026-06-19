"""Tests for the `rules` CLI verbs."""

from __future__ import annotations

from altiumtools.cli import main
from altiumtools.rules import parse_rul


def test_rules_list_runs(capsys):
    rc = main(["rules", "list"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "pcbway" in out
    assert "source:" in out


def test_rules_generate_to_file(tmp_path, capsys):
    out = tmp_path / "pcbway.RUL"
    rc = main(["rules", "generate", "pcbway", "-o", str(out)])
    assert rc == 0
    assert out.exists()
    records = parse_rul(out.read_bytes())
    assert len(records) >= 4
    assert {"Width", "Clearance", "MinimumAnnularRing"} <= {
        r["RULEKIND"] for r in records
    }
    # File terminates with the structural pilcrow on each line.
    raw = out.read_bytes().decode("latin-1")
    assert "\xb6\n" in raw


def test_rules_generate_unknown_vendor(capsys):
    rc = main(["rules", "generate", "nope"])
    err = capsys.readouterr().err
    assert rc == 2
    assert "unknown manufacturer" in err
