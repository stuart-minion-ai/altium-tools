# Altium file format notes (what we know, what we don't)

This is a living reference for reverse-engineering Altium's binary files. PRs
that extend it are very welcome. Nothing here is official; it is community
knowledge plus what this repo's parser relies on.

## The container: OLE2 / CFB

`.SchDoc`, `.PcbDoc`, `.PcbLib`, `.SchLib`, and `.PrjPcb`-family binary files are
**Microsoft OLE2 Compound File Binary** documents — the same container format as
legacy `.doc`/`.xls`. This part is fully documented (MS-CFB) and parses on any OS
with [`olefile`](https://pypi.org/project/olefile/).

```bash
altium-tools inspect yourfile.SchDoc   # lists internal streams + sizes
```

A file is a small filesystem of named *streams* inside *storages* (folders).
Altium puts its data in streams like `FileHeader`, plus per-object storages.

## Schematic records (`.SchDoc`) — partially decoded ✅

Schematic objects are stored as **pipe-delimited ASCII records**:

```
|RECORD=1|LIBREFERENCE=Res2|SOURCEDESIGNATOR=R1|COMMENT=10k|...|
```

- A record begins at a `|RECORD=<n>|` token and runs until the next one.
- Fields are `|KEY=VALUE|`, keys are `[A-Z0-9_]+`, values are everything up to
  the next `|`.
- `RECORD=1` = a component/part. Useful fields:
  - `SOURCEDESIGNATOR` / `DESIGNATOR` — the reference designator (R1, U3).
  - `LIBREFERENCE` — the library symbol name.
  - `COMMENT` — value / part number shown on the schematic.
- Other record types (pins, wires, labels, junctions) have their own numbers and
  are not yet mapped into the model — **good first PRs**.

`parse_schdoc()` implements the above and maps `RECORD=1` to `Component`.

## PCB records (`.PcbDoc`) — NOT decoded yet ❌ (Milestone 1)

The PCB document stores geometry (tracks, vias, pads, polygons, components,
rules) as **binary records**, not ASCII pipe-text. These are length-prefixed
binary blobs whose layouts vary by object type and Altium version. Decoding them
is the project's headline open problem.

`parse_pcbdoc()` currently:
- validates the OLE container,
- registers the document name,
- sets `design.meta["pcb_geometry_decoded"] = "false"`.

It does **not** invent tracks/vias. When you decode a record type, map it into
`model.py` (`Net`, `DesignRule`, `Component.footprint`, …) and add a test using
a synthesized fixture.

### Known starting points for PCB decoding

- The `Board6`/`Components6`/`Nets6`/`Rules6` storages (names vary by version)
  hold the bulk of objects.
- Many object streams begin with a 4-byte little-endian length, then a record
  body. Identifying the per-type body layout is the work.
- Cross-reference open-source efforts (e.g. the `pyaltium` and various
  `altium2kicad` projects) — but verify against real files; versions differ.

## Contributing format knowledge

When you confirm a field or record layout:
1. Document it here with the exact byte offsets / field names you verified.
2. Add a parser mapping into `model.py`.
3. Add a test with a synthesized fixture (`tests/_olewriter.py`).
4. Never commit proprietary/customer design files to the repo.
