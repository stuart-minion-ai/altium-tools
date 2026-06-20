# checks — schematic/PCB review engine

A **linter for Altium designs**. `checks` is a registry of small, independent
review rules (like ruff/eslint) that run over a parsed design and emit `Finding`s
with stable IDs. It exits non-zero on errors, so it drops straight into CI.

Pure Python, runs on any OS.

## Quick start (CLI)

```console
$ altium-tools review board/main.SchDoc
ERROR   SCH002: Designator 'R1' used by 2 components.
          -> Re-annotate; duplicate designators break netlist/BOM.
WARNING SCH003 (main.SchDoc:record#7): C4 has no value/comment.
          -> Set the Comment/Value parameter.
2 findings: 1 error(s), 1 warning(s)
```

```console
# review several files together (they're merged into one design):
$ altium-tools review main.SchDoc power.SchDoc board.PcbDoc

# run only specific checks (repeatable):
$ altium-tools review main.SchDoc --select SCH001 --select SCH002

# list every registered check:
$ altium-tools checks
PCB001  [error  ]  Components missing a footprint
PCB002  [warning]  Single-node nets (likely unconnected)
RUL001  [warning]  No clearance design rule defined
SCH001  [error  ]  Components missing a designator
SCH002  [error  ]  Duplicate designators
SCH003  [warning]  Components missing a value/comment
```

**Exit codes:** `0` = no errors (warnings/info allowed), `1` = at least one
error finding, `2` = no parseable input. Use it as a CI gate.

## Built-in checks

| ID | severity | what it catches |
|----|----------|-----------------|
| `SCH001` | error   | Components with no real designator (`R?` / blank) |
| `SCH002` | error   | Duplicate designators (breaks netlist/BOM) |
| `SCH003` | warning | Passives (R/C/L) with no value/comment |
| `PCB001` | error   | Components with no footprint (can't be placed) |
| `PCB002` | warning | Single-node nets (likely unconnected) |
| `RUL001` | warning | PCB present but no Clearance design rule defined |

**ID convention:** `SCH###` schematic-level · `PCB###` board-level ·
`RUL###` design-rule planning.

## Add a check in ~10 lines

A check is one pure function that takes an immutable `Design` and **yields**
`Finding`s. It must not mutate the design or do I/O. Decorate it with a unique,
stable ID and it's picked up automatically.

```python
# add to src/altiumtools/checks/builtin.py (or your own module)
from collections.abc import Iterable

from ..core.model import Design
from . import Finding, Severity, register


@register("SCH010", "Net names should be uppercase", Severity.INFO)
def net_names_uppercase(design: Design) -> Iterable[Finding]:
    for net in design.nets:
        if net.name != net.name.upper():
            yield Finding(
                "SCH010",
                Severity.INFO,
                f"Net {net.name!r} is not uppercase.",
                net.source,                       # optional: file:locator in output
                hint="Rename to an uppercase net label.",
            )
```

Then verify:

```bash
.venv/bin/ruff check .
.venv/bin/python -m pytest -q
altium-tools checks            # SCH010 should appear
```

## API surface

```python
from altiumtools.checks import (
    register,     # decorator: @register(id, title, default_severity)
    Finding,      # frozen: check_id, severity, message, source?, hint
    Severity,     # INFO | WARNING | ERROR
    all_checks,   # -> sorted list[CheckMeta]
    run_checks,   # run_checks(design, select=None) -> Iterator[Finding]
    Report,       # findings + .errors / .warnings / .worst()
)
```

This package depends only on `core.model` (never on `core.parse`), so writing a
check never drags in binary-parsing concerns.
