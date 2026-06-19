"""Tests for the Altium OLE parser.

We synthesize a real OLE2 compound file containing Altium-style pipe-delimited
records, so the parser path is genuinely exercised end-to-end on Linux without
needing a proprietary sample file.
"""

from __future__ import annotations

from pathlib import Path

import olefile
import pytest

from altiumtools.parse import (
    UnsupportedFile,
    inspect_ole,
    load,
    parse_schdoc,
)


def _write_ole_with_records(path: Path, payload: bytes) -> None:
    """Create a minimal valid OLE2 file with one stream named 'FileHeader'.

    olefile is read-only, so we build the container with the stdlib by writing a
    tiny compound file. To keep the test dependency-free we instead use the
    `compoundfiles`-free approach: olefile can't write, so we craft via a known
    helper if available; otherwise skip. In practice we generate it with a small
    pure-python OLE writer embedded here.
    """

    from _olewriter import write_ole  # local helper (tests dir on sys.path)

    write_ole(path, {"FileHeader": payload})


SAMPLE = (
    b"|RECORD=1|LIBREFERENCE=Res2|SOURCEDESIGNATOR=R1|COMMENT=10k|"
    b"|RECORD=1|LIBREFERENCE=Cap|SOURCEDESIGNATOR=C1|COMMENT=100n|"
    b"|RECORD=2|SOMETHINGELSE=ignore|"
)


def test_inspect_and_parse_schdoc(tmp_path: Path):
    f = tmp_path / "main.SchDoc"
    _write_ole_with_records(f, SAMPLE)

    # The file we wrote must be a valid OLE file.
    assert olefile.isOleFile(str(f))

    streams = inspect_ole(f)
    assert any("FileHeader" in name for name in streams)

    design = parse_schdoc(f)
    desigs = {c.designator for c in design.components}
    assert desigs == {"R1", "C1"}
    r1 = next(c for c in design.components if c.designator == "R1")
    assert r1.comment == "10k"
    assert r1.library_ref == "Res2"
    assert design.schematic_docs == ["main.SchDoc"]


def test_load_dispatch(tmp_path: Path):
    f = tmp_path / "main.SchDoc"
    _write_ole_with_records(f, SAMPLE)
    d = load(f)
    assert len(d.components) == 2


def test_unsupported_extension(tmp_path: Path):
    f = tmp_path / "x.kicad_pcb"
    f.write_text("not altium")
    with pytest.raises(UnsupportedFile):
        load(f)


def test_non_ole_rejected(tmp_path: Path):
    f = tmp_path / "fake.SchDoc"
    f.write_text("plain text, not OLE")
    with pytest.raises(UnsupportedFile):
        parse_schdoc(f)
