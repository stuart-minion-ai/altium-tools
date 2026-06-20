# manufacturers — fab rule-pack registry

This is the **contributor extension point for PCB manufacturers**. Adding a fab is
the same shape as adding a review check in [`../../checks/`](../../checks/): write
**one function** that returns a verified `RulePack`, decorate it with `@register`,
and it shows up automatically in `altium-tools rules list` / `rules generate`.

No new file format, no parser, no extra dependency.

## The 3-step recipe

### 1. Write the pack file

Create `src/altiumtools/rules/manufacturers/<vendor>.py`:

```python
"""<Vendor> standard FR4 rule pack.

Every number below is traceable to <Vendor>'s published capability document
(see _SOURCE). Document any unit conversions you do.
"""
from __future__ import annotations

from ...core.model import DesignRule
from ..model import RulePack
from . import register

_SOURCE = "https://vendor.example/capabilities"   # REQUIRED
_CAPTURED = "2026-06-19"                            # REQUIRED ISO date

# Format-verified kinds you intentionally DO NOT emit because the fab publishes
# no interchangeable number for them. Format-verified does NOT license invention.
_OMITTED_KINDS: dict[str, str] = {
    "PasteMaskExpansion": "<Vendor> does not publish a paste-mask expansion.",
}


@register("<vendor>")
def vendor_standard_fr4() -> RulePack:
    rules = [
        DesignRule(
            kind="Width", name="Width", scope="All", enabled=True,
            constraints={
                "SCOPE2EXPRESSION": "All",
                "COMMENT": "<Vendor> min trace width 5mil (1oz)",
                "MINLIMIT": "5mil", "MAXLIMIT": "500mil", "PREFEREDWIDTH": "10mil",
            },
        ),
        # ... only kinds you can SOURCE, with the fab's PUBLISHED numbers ...
    ]
    return RulePack(
        vendor="<vendor>",
        title="<Vendor> standard 2-layer (1oz)",
        source=_SOURCE,
        captured=_CAPTURED,
        rules=rules,
    )
```

Use `seeed.py` as the reference example — it shows mixed-unit conversion, a
derived via pad (`hole + 2×ring`), and a well-documented `_OMITTED_KINDS`.

### 2. Register the import

Add one line to `manufacturers/__init__.py` (kept at the bottom of the file, in
alphabetical order with the others):

```python
from . import myfab as _myfab  # noqa: E402,F401
```

### 3. Add tests

Mirror an existing block in `tests/test_rules_manufacturers.py`: assert the pack
builds, has `source`/`captured`, emits the expected kinds, and round-trips
(`parse_rul(emit_rul(pack))`).

Then:

```bash
.venv/bin/ruff check .
.venv/bin/python -m pytest -q
altium-tools rules list          # your fab should appear
altium-tools rules generate myfab -o /tmp/myfab.RUL
```

## The two-layer honesty gate (mandatory)

A PR that violates either layer will be rejected — this rule is project-defining.

1. **Format layer.** Only emit a rule *kind* whose complete field envelope was
   captured from a real Altium-exported `.RUL` fixture, with a passing round-trip
   test. Don't invent fields.
2. **Data layer.** Only emit numbers the fab **officially publishes**. If a kind
   isn't sourceable for your fab, **omit it** and record why in `_OMITTED_KINDS`.
   Never map a published number onto a *different* rule kind because the names
   look similar (e.g. solder-mask *dam/sliver* ≠ solder-mask *expansion/swell*).

Every pack **must** set `source` (URL/document) and `captured` (ISO date). The
CLI surfaces both so users can verify rules against the fab's current spec, and
packs are validated at registration time, so a typo'd constraint key fails loudly
here rather than producing a bad `.RUL`.

## Registry API

```python
from altiumtools.rules.manufacturers import available, get_pack, register

available()          # -> sorted list of registered vendor ids
get_pack("pcbway")   # -> RulePack (raises KeyError if unknown)
```
