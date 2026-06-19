# Architecture

altium-tools is three decoupled layers. The decoupling is the whole point: it
lets a check author and a parser author work without stepping on each other, and
it keeps Altium-version-specific weirdness quarantined in one place.

```
 ┌─────────────────────────────────────────────────────────────┐
 │ Altium binary files: .SchDoc / .PcbDoc / .PcbLib            │
 │ (Microsoft OLE2 compound documents)                         │
 └───────────────┬─────────────────────────────────────────────┘
                 │  parse.py
                 │  • inspect_ole(): list streams (always works)
                 │  • parse_schdoc(): pipe-record → components
                 │  • parse_pcbdoc(): container only (geometry TODO)
                 ▼
 ┌─────────────────────────────────────────────────────────────┐
 │ Normalized Design model  (model.py)                         │
 │   Design { components[], nets[], rules[], schematic_docs[],  │
 │            pcb_docs[], meta }                                │
 │   Component / Net / DesignRule / SourceRef                   │
 │   → format-agnostic. No olefile types past this line.        │
 └───────────────┬─────────────────────────────────────────────┘
                 │  checks/run_checks(design, select=...)
                 ▼
 ┌─────────────────────────────────────────────────────────────┐
 │ Review-check registry  (checks/)                            │
 │   @register("SCH001", ...) -> yields Finding                │
 │   Pure functions. No I/O, no mutation. Stable IDs.          │
 └───────────────┬─────────────────────────────────────────────┘
                 │  cli.py
                 ▼
 ┌─────────────────────────────────────────────────────────────┐
 │ CLI / report / CI gate                                      │
 │   inspect · review (exit!=0 on error) · checks              │
 └─────────────────────────────────────────────────────────────┘
```

## Invariants

1. **Parsers depend on `model`; checks depend on `model`. They never depend on
   each other.** This is what lets the two contribution paths stay independent.
2. **`model` is format-agnostic.** No `olefile` objects, no raw Altium record
   dicts in the typed fields. Unmapped data goes into `.meta` so nothing is lost
   but nothing leaks either.
3. **Checks are pure.** Given a `Design` they yield `Finding`s; they perform no
   I/O and never mutate the design. This makes them trivially testable and
   safely runnable in any order / in parallel.
4. **Stable check IDs.** Once an ID ships it doesn't change meaning — downstream
   users filter and gate CI on specific IDs.
5. **Honesty over coverage.** Unsupported formats report "unsupported" or set a
   capability flag (`design.meta["pcb_geometry_decoded"] == "false"`). We never
   emit fabricated geometry/data to look more complete.

## Why a registry (and not a big if/else)

Same reason ruff/eslint scale: dozens of tiny, independent rules behind one
registry, each discoverable, each individually selectable, each separately
tested. Adding a rule is additive — no existing code changes — which keeps PRs
small and review easy.

## Testing strategy

- Check logic is tested against hand-built `Design` objects (no files needed).
- Parser logic is tested against **synthesized** OLE2 files (`tests/_olewriter.py`)
  so the binary path is genuinely exercised on every OS in CI without committing
  proprietary sample files.
