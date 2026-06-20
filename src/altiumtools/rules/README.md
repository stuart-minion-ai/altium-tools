# rules — Altium `.RUL` design-rule generator

Generate an **importable Altium design-rule file** (`.RUL`) preloaded with a PCB
manufacturer's published fabrication limits (min trace width, clearance, hole
sizes, annular rings, via geometry, …). Pick your fab, generate, and import the
rules straight into your board — no more transcribing a capability table by hand.

Pure Python, runs on any OS, **no Altium install required** to generate the file.

---

## What a `.RUL` file is

A `.RUL` is **plain ISO-8859 text** — one design rule per line, `KEY=VALUE` pairs
joined by `|`, each record terminated by the pilcrow byte `0xB6` (`¶`). It is a
completely different format from Altium's OLE2 binary `.SchDoc`/`.PcbDoc`, which
is why this lives in its own package and shares none of the OLE machinery.

## Quick start (CLI)

List the manufacturer packs that ship today:

```console
$ altium-tools rules list
advancedpcb     Advanced Circuits / AdvancedPCB Standard (2-layer, 1oz)
                source: https://www.advancedpcb.com/.../manufacturing-capabilities/ (captured 2026-06-19)
                7 rules: Width, Clearance, HoleSize, MinimumAnnularRing, RoutingVias, HoleToHoleClearance, SolderMaskExpansion
aisler          AISLER standard 2-layer (1.6mm, 35um, HASL)        7 rules
eurocircuits    Eurocircuits standard pool (Class 6, Drill C, 1oz) 4 rules
jlcpcb          JLCPCB standard 2-layer (1oz)                      8 rules
oshpark         OSH Park standard 2-layer (1oz)                    5 rules
pcbway          PCBWay standard 2-layer (1oz)                      5 rules
seeed           Seeed Fusion standard FR4 (2-layer, 1oz)           6 rules
```

Generate a `.RUL` for your fab:

```console
$ altium-tools rules generate jlcpcb -o jlcpcb.RUL
wrote 8 rules to jlcpcb.RUL  (import into Altium: Design > Rules > right-click > Import Rules)

# omit -o (or use -o -) to write the .RUL to stdout instead:
$ altium-tools rules generate seeed > seeed.RUL
```

## Import into Altium Designer

1. Open your PCB document in Altium Designer.
2. **Design ▸ Rules…** to open the *PCB Rules and Constraints Editor*.
3. Right-click the root **Design Rules** node ▸ **Import Rules…**.
4. Select the generated `.RUL` file and choose which rule classes to import.
5. Review priorities/scopes, then **Apply**. Re-run DRC.

> The generated rules are global (`AnyNet`, scope `All`/`All`) starting points
> sized to the fab's *minimums*. Tighten scopes (e.g. per net class) and adjust
> priorities to suit your board before relying on DRC.

## Supported manufacturers

| id | profile | rules |
|----|---------|-------|
| `jlcpcb`       | JLCPCB standard 2-layer (1oz)                      | 8 |
| `advancedpcb`  | Advanced Circuits / AdvancedPCB (2-layer, 1oz)     | 7 |
| `aisler`       | AISLER standard 2-layer (1.6mm, 35µm, HASL)        | 7 |
| `seeed`        | Seeed Fusion standard FR4 (2-layer, 1oz)           | 6 |
| `oshpark`      | OSH Park standard 2-layer (1oz)                    | 5 |
| `pcbway`       | PCBWay standard 2-layer (1oz)                      | 5 |
| `eurocircuits` | Eurocircuits standard pool (Class 6, Drill C, 1oz) | 4 |

Run `altium-tools rules list` for the authoritative, always-current set plus each
pack's **source URL and capture date**.

## The honesty gate (why rule counts differ)

Packs do **not** all carry the same rule kinds, and that is deliberate:

1. **Format layer** — we only emit a rule *kind* whose complete field envelope
   was captured from a real, Altium-exported `.RUL` (`tests/fixtures/rul/`). A
   round-trip test proves `parse → emit` reproduces the original record
   byte-for-byte (only values/`UNIQUEID` differ). Unverified kinds are absent,
   never emitted with guessed fields.
2. **Data layer** — we only emit numbers the fab **officially publishes**. A kind
   we can't source for a given fab is omitted and recorded in that pack's
   `_OMITTED_KINDS` with the reason (e.g. Seeed publishes a solder-mask *dam/
   sliver* width, which is **not** the pad solder-mask *expansion* this rule
   constrains — so it is omitted rather than mis-mapped).

A generator that emits a plausible-but-wrong rule is worse than one that omits it.

## Programmatic use

```python
from altiumtools.rules import emit_rul
from altiumtools.rules.manufacturers import available, get_pack

print(available())            # ['advancedpcb', 'aisler', 'eurocircuits', ...]
pack = get_pack("pcbway")     # -> RulePack(vendor, title, source, captured, rules)
data: bytes = emit_rul(pack)  # ready-to-import .RUL bytes
open("pcbway.RUL", "wb").write(data)
```

`parse_rul(bytes) -> list[DesignRule]` round-trips a `.RUL` back into the model.

## Add a manufacturer pack (contributors)

One file + one decorator — see
[`manufacturers/README.md`](manufacturers/README.md) for the full guide. In short:

```python
# src/altiumtools/rules/manufacturers/myfab.py
from ...core.model import DesignRule
from ..model import RulePack
from . import register

@register("myfab")
def myfab_standard() -> RulePack:
    return RulePack(
        vendor="myfab",
        title="MyFab standard 2-layer (1oz)",
        source="https://myfab.example/capabilities",  # REQUIRED
        captured="2026-06-19",                          # REQUIRED ISO date
        rules=[
            DesignRule(kind="Width", name="Width", scope="All", enabled=True,
                       constraints={"SCOPE2EXPRESSION": "All", "MINLIMIT": "5mil",
                                    "MAXLIMIT": "500mil", "PREFEREDWIDTH": "10mil"}),
            # ... only kinds you can source, with published numbers ...
        ],
    )
```

Then register the import in `manufacturers/__init__.py` and add tests. Every pack
**must** set `source` and `captured`; packs are validated at registration time,
so a typo'd constraint key fails loudly instead of producing a bad `.RUL`.
