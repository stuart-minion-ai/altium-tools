# core — shared foundation (parser + model)

`core` is the **foundation every sub-project depends on, and which depends on
nothing internal**. It has two modules:

- **`core/model.py`** — format-agnostic dataclasses (`Design`, `Component`,
  `Net`, `DesignRule`, `SourceRef`). The neutral vocabulary the whole project
  speaks.
- **`core/parse.py`** — reads Altium's OLE2 binary files (`.SchDoc`/`.PcbDoc`/
  `.PcbLib`) into that model, using `olefile` (read-only).

> **Dependency rule:** sub-projects (`checks/`, `rules/`) import from
> `core.model`. They must **not** import from each other, and `core` must never
> import from them. This one-way arrow is what keeps the monorepo contributable.

## The model

```python
from altiumtools.core.model import Design, Component, Net, DesignRule, SourceRef
```

| type | purpose |
|------|---------|
| `Design`      | the whole parsed project — components, nets, rules, doc lists |
| `Component`   | designator, comment/value, footprint, library ref, pins |
| `Net`         | name + `node_count` (pins/pads on the net) |
| `DesignRule`  | normalized EDA rule: `kind`, `name`, `scope`, `constraints` |
| `SourceRef`   | `document` + `locator` — where an object came from, for actionable messages |

Anything Altium-specific a parser can map to a neutral concept belongs here; raw
unmapped record fields are preserved in each object's `.meta` so **no information
is silently dropped**.

## Parsing (the honest-scope contract)

Altium `.SchDoc`/`.PcbDoc`/`.PcbLib` are Microsoft OLE2 compound documents. The
*container* is fully documented and parses anywhere; the *record payloads* are
Altium-proprietary and only partially reverse-engineered. So `core.parse` does
exactly what it can prove, and flags the rest:

```python
from altiumtools.core.parse import inspect_ole, load, merge, UnsupportedFile

inspect_ole("main.SchDoc")   # -> {stream_path: size}  — always works, any version
load("main.SchDoc")          # -> Design (components + designators), dispatches on suffix
merge([d1, d2])              # -> one project-level Design
```

- **`inspect_ole()`** — list every internal stream + size. The bedrock every
  higher parser builds on; works on every Altium version.
- **`parse_schdoc()`** — extract the schematic's pipe-delimited `|KEY=VALUE|`
  records (components, designators, parameters). Reliable.
- **`parse_pcbdoc()`** — registers the document but sets
  `design.meta["pcb_geometry_decoded"] = "false"`. Full binary track/via/polygon
  geometry decoding is **community milestone #1** — it is *not* stubbed with
  fabricated output.

### Project-defining honesty rule

**Never emit fabricated parser output for an undecoded format.** Return
`UnsupportedFile` or a capability flag. A parser that returns guesses is worse
than one that says it can't. Mirror this in any PR review.

`olefile` is the only runtime dependency, and it is **read-only** — this project
never writes Altium binaries. Tests synthesize real OLE2 files via
`tests/_olewriter.py` (a minimal CFB writer) rather than committing proprietary
`.SchDoc`/`.PcbDoc`.
