# altium-tools

Open-source tooling to make **Altium Designer** faster and easier to use —
intelligent design-rule planning, schematic/PCB design review, and analysis of
Altium files on **any operating system** (no Altium install required for the
analysis core).

> Status: **alpha**, foundation release. The architecture is in place and the
> review engine + an honest Altium OLE parser work today on Linux/macOS/Windows.
> Full binary PCB geometry decoding is the first community milestone — see
> [Roadmap](#roadmap). We deliberately ship "unsupported" over fabricated output.

---

## Why this exists

Altium Designer is powerful but Windows-only and GUI-heavy. A lot of valuable
work — checking a schematic for missing designators, duplicate references,
unfootprinted parts, or planning a sane set of design rules before routing —
is **mechanical and automatable**. This project builds that automation as a
clean, OS-independent Python core so it can run in CI, in scripts, and one day
inside Altium itself via a thin extension.

## What works today

- **`inspect`** — open any `.SchDoc` / `.PcbDoc` / `.PcbLib` (they are OLE2
  compound files) and list their internal streams. Works everywhere.
- **`review`** — parse a schematic and run an extensible set of review checks
  (missing/duplicate designators, missing values, missing footprints,
  single-node nets, missing clearance rule). Exits non-zero on errors, so it
  drops straight into CI.
- **`checks`** — list every registered review check.
- **`rules`** — generate an importable Altium `.RUL` design-rule file preloaded
  with a PCB manufacturer's published fab limits (7 fabs ship today: JLCPCB,
  PCBWay, Seeed, AISLER, OSH Park, Advanced Circuits, Eurocircuits). Import
  straight into Altium via *Design ▸ Rules ▸ Import Rules*.

```console
$ altium-tools inspect board/main.SchDoc
      1024  FileHeader
        96  Storage/Data
2 streams

$ altium-tools review board/main.SchDoc
ERROR   SCH002: Designator 'R1' used by 2 components.
          -> Re-annotate; duplicate designators break netlist/BOM.
WARNING SCH003 (main.SchDoc:record#7): C4 has no value/comment.
          -> Set the Comment/Value parameter.
2 findings: 1 error(s), 1 warning(s)

$ altium-tools checks
PCB001  [error  ]  Components missing a footprint
PCB002  [warning]  Single-node nets (likely unconnected)
RUL001  [warning]  No clearance design rule defined
SCH001  [error  ]  Components missing a designator
SCH002  [error  ]  Duplicate designators
SCH003  [warning]  Components missing a value/comment

$ altium-tools rules generate jlcpcb -o jlcpcb.RUL
wrote 8 rules to jlcpcb.RUL  (import into Altium: Design > Rules > right-click > Import Rules)
```

## Install

```bash
pip install -e ".[dev]"   # from a clone, with test deps
# or just the runtime:
pip install -e .
```

Requires Python ≥ 3.10. The only runtime dependency is
[`olefile`](https://pypi.org/project/olefile/).

## Architecture

Three decoupled layers — this is what makes the project easy to contribute to:

```
  Altium files (.SchDoc/.PcbDoc, OLE2 binary)
        │   core/parse.py  (olefile → records)
        ▼
  Normalized Design model   (core/model.py)   ← format-agnostic dataclasses
        │   run_checks()                  │   emit_rul()
        ▼                                 ▼
  Review checks registry    (checks/)   Rule generator (rules/)
        │   ← sub-projects: each depends only on core/, add one function
        ▼
  CLI / report / CI gate    (cli.py)
```

A contributor writing a new review rule never touches binary parsing. A
contributor improving the parser never touches rule logic. See
[CONTRIBUTING.md](CONTRIBUTING.md) and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

### Sub-project guides

Each layer has its own README with usage + contributor recipes:

- [`src/altiumtools/core/`](src/altiumtools/core/README.md) — shared model + Altium OLE parser (the foundation).
- [`src/altiumtools/checks/`](src/altiumtools/checks/README.md) — schematic/PCB review engine (`review`, `checks`).
- [`src/altiumtools/rules/`](src/altiumtools/rules/README.md) — `.RUL` design-rule generator (`rules`).
  - [`rules/manufacturers/`](src/altiumtools/rules/manufacturers/README.md) — how to add a fab rule-pack.

### Add a check in ~10 lines

```python
from altiumtools.core.model import Design
from altiumtools.checks import Finding, Severity, register

@register("SCH010", "Net names should be uppercase", Severity.INFO)
def net_names_uppercase(design: Design):
    for net in design.nets:
        if net.name != net.name.upper():
            yield Finding("SCH010", Severity.INFO,
                          f"Net {net.name!r} is not uppercase.")
```

## Roadmap

- [ ] **Milestone 1 — PCB geometry decoding.** Decode `.PcbDoc` binary records
      (tracks, vias, pads, polygons, rules) into the model. *This is the big
      community lift; the OLE container already parses.*
- [ ] Schematic netlist extraction (wires → nets → node counts).
- [ ] Rule-planning assistant: suggest clearance/width rule sets from net
      classes and stackup.
- [ ] BOM checks (DNP consistency, missing MPN, duplicate part numbers).
- [ ] In-Altium extension (DelphiScript/.NET) that shells out to this core.

## Contributing

Issues and PRs welcome — this is built to be contributed to. Start with
[CONTRIBUTING.md](CONTRIBUTING.md). Good first issues: add a review check, or
help reverse-engineer a PCB record type (documented in
[docs/ALTIUM_FILE_FORMAT.md](docs/ALTIUM_FILE_FORMAT.md)).

## License

[Apache-2.0](LICENSE).
