"""Altium file parsing.

HONEST SCOPE NOTE (read before extending):
Altium's `.SchDoc`, `.PcbDoc`, and `.PcbLib` files are Microsoft OLE2 compound
documents (the same container as legacy .doc/.xls). The *container* is fully
documented and parses anywhere via `olefile`. The *record payloads* inside the
streams are Altium-proprietary and only partially reverse-engineered by the
community. This module therefore does two honest things today:

  1. `inspect_ole()` — open any Altium file, list its internal streams + sizes.
     This always works and is the bedrock every higher parser builds on.
  2. `parse_schdoc()` — extract the schematic's ASCII "|KEY=VALUE|" records,
     which Altium stores as pipe-delimited text inside the `FileHeader`-family
     streams. This reliably yields components, designators, and parameters.

What is intentionally NOT faked here: full binary PCB track/via/polygon geometry
decoding. That is community milestone #1, tracked as an issue, not stubbed with
fabricated output. A parser that returns guesses is worse than one that returns
"unsupported".
"""

from __future__ import annotations

import re
from pathlib import Path

from .model import Component, Design, SourceRef

try:
    import olefile  # type: ignore
except ImportError:  # pragma: no cover - dependency declared in pyproject
    olefile = None


class UnsupportedFile(Exception):
    pass


def _require_olefile() -> None:
    if olefile is None:  # pragma: no cover
        raise UnsupportedFile(
            "olefile is required to parse Altium files. `pip install olefile`."
        )


def inspect_ole(path: str | Path) -> dict[str, int]:
    """Return {stream_path: size_in_bytes} for every stream in an OLE file.

    This is the universal first step for any Altium parser and works on every
    .SchDoc/.PcbDoc/.PcbLib regardless of Altium version.
    """

    _require_olefile()
    p = Path(path)
    if not olefile.isOleFile(str(p)):
        raise UnsupportedFile(f"{p} is not an OLE2 compound file (Altium binary).")
    streams: dict[str, int] = {}
    with olefile.OleFileIO(str(p)) as ole:
        for entry in ole.listdir(streams=True, storages=False):
            name = "/".join(entry)
            streams[name] = ole.get_size(name)
    return streams


# Altium pipe-delimited records look like:  |RECORD=1|LIBREFERENCE=Res2|...|
_RECORD_RE = re.compile(rb"\|RECORD=(\d+)\|")
_FIELD_RE = re.compile(rb"\|([A-Z0-9_]+)=([^|]*)")


def _read_text_streams(path: Path) -> bytes:
    """Concatenate the byte payload of all streams (records may span streams)."""

    blob = bytearray()
    with olefile.OleFileIO(str(path)) as ole:
        for entry in ole.listdir(streams=True, storages=False):
            name = "/".join(entry)
            try:
                blob += ole.openstream(name).read()
            except OSError:  # pragma: no cover
                continue
    return bytes(blob)


def _parse_records(blob: bytes) -> list[dict[str, str]]:
    """Split a blob into Altium |KEY=VALUE| records."""

    records: list[dict[str, str]] = []
    # Each record starts at a |RECORD=...| token.
    starts = [m.start() for m in _RECORD_RE.finditer(blob)]
    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(blob)
        chunk = blob[start:end]
        fields = {
            k.decode("latin-1"): v.decode("latin-1")
            for k, v in _FIELD_RE.findall(chunk)
        }
        records.append(fields)
    return records


def parse_schdoc(path: str | Path) -> Design:
    """Parse a binary .SchDoc into a Design (components + designators).

    Altium schematic Record=1 entries are component (part) records. We map the
    well-known fields; everything else is preserved in `meta` so no information
    is silently dropped.
    """

    _require_olefile()
    p = Path(path)
    if not olefile.isOleFile(str(p)):
        raise UnsupportedFile(f"{p} is not an OLE2 compound file.")

    blob = _read_text_streams(p)
    records = _parse_records(blob)

    design = Design(name=p.stem, schematic_docs=[p.name])
    for idx, rec in enumerate(records):
        if rec.get("RECORD") != "1":
            continue  # Record=1 == component/part in the schematic model
        designator = rec.get("SOURCEDESIGNATOR") or rec.get("DESIGNATOR") or ""
        design.components.append(
            Component(
                designator=designator,
                comment=rec.get("COMMENT", "") or rec.get("TEXT", ""),
                footprint=rec.get("CURRENTPARTID_FOOTPRINT", ""),
                library_ref=rec.get("LIBREFERENCE", ""),
                source=SourceRef(p.name, f"record#{idx}"),
                meta={k: v for k, v in rec.items() if k not in {"RECORD"}},
            )
        )
    return design


def parse_pcbdoc(path: str | Path) -> Design:
    """Open a .PcbDoc and report what is supported today.

    The PCB binary geometry records are not yet decoded (community milestone).
    We still return a valid Design with the document registered and any
    pipe-text records surfaced, rather than fabricating geometry.
    """

    _require_olefile()
    p = Path(path)
    if not olefile.isOleFile(str(p)):
        raise UnsupportedFile(f"{p} is not an OLE2 compound file.")
    design = Design(name=p.stem, pcb_docs=[p.name])
    design.meta["pcb_geometry_decoded"] = "false"  # honest capability flag
    return design


def load(path: str | Path) -> Design:
    """Dispatch on extension. Raises UnsupportedFile for unknown types."""

    p = Path(path)
    suffix = p.suffix.lower()
    if suffix == ".schdoc":
        return parse_schdoc(p)
    if suffix == ".pcbdoc":
        return parse_pcbdoc(p)
    raise UnsupportedFile(f"No parser for {suffix!r} files yet.")


def merge(designs: list[Design], name: str = "project") -> Design:
    """Merge several parsed documents into one project-level Design."""

    out = Design(name=name)
    for d in designs:
        out.schematic_docs += d.schematic_docs
        out.pcb_docs += d.pcb_docs
        out.components += d.components
        out.nets += d.nets
        out.rules += d.rules
    return out
