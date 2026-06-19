# Architecture

altium-tools is a **monorepo of decoupled sub-projects** that all sit on one
shared foundation. The "大项目分多个小项目" structure is made literal by the
`src/altiumtools/` folder layout: a `core/` foundation everything depends on,
plus one folder per sub-project (`checks/`, `rules/`, …future). Each sub-project
depends **only on `core/`**, never on a sibling — so a review-check author and a
rule-generator author never step on each other, and Altium-version weirdness
stays quarantined in one place.

## Repo folder structure

```
altium-tools/                     ← single repo  (remote: stuart-minion-ai/altium-tools)
├── src/altiumtools/
│   ├── core/                     ── FOUNDATION  (shared, depends on nothing internal)
│   │   ├── model.py              ·  normalized Design dataclasses (olefile-free boundary type)
│   │   └── parse.py              ·  Altium OLE2 binary → Design  (inspect_ole/parse_schdoc/load/merge)
│   │
│   ├── checks/                   ── SUB-PROJECT ①  "design review"   (depends on core/)
│   │   ├── __init__.py           ·  the @register registry + run_checks  (contributor extension point)
│   │   └── builtin.py            ·  bundled SCH###/PCB### checks
│   │
│   ├── rules/                    ── SUB-PROJECT ②  ".RUL rule generator"   (depends on core/)
│   │   ├── model.py              ·  RulePack (provenance wrapper around core DesignRule)
│   │   ├── fields.py · emit.py · parse.py
│   │   └── manufacturers/        ·  per-fab packs (pcbway.py, …) — same registry pattern as checks/
│   │
│   ├── cli.py                    ── umbrella dispatcher:  altium-tools <inspect|review|checks|rules>
│   └── __init__.py               ·  __version__
│
├── tests/                        ── _olewriter.py (synthesizes OLE2 fixtures) + one test_*.py per sub-project
├── docs/                         ── ARCHITECTURE / ALTIUM_FILE_FORMAT / ROADMAP / RULE_GENERATOR_PLAN
├── .github/                      ── CI (ruff + pytest) + issue/PR templates
└── pyproject.toml                ── single installable, console-script `altium-tools`
```

Adding a new sub-project (e.g. `netlist/`, `bom/`, `gerber/`) = add one folder
under `src/altiumtools/`, depend on `core/`, register a CLI verb in `cli.py`,
add `tests/test_<name>.py`. No existing sub-project changes.

## Dependency layers

```
 ┌─────────────────────────────────────────────────────────────┐
 │ Altium binary files: .SchDoc / .PcbDoc / .PcbLib            │
 │ (Microsoft OLE2 compound documents)                         │
 └───────────────┬─────────────────────────────────────────────┘
                 │  core/parse.py
                 │  • inspect_ole(): list streams (always works)
                 │  • parse_schdoc(): pipe-record → components
                 │  • parse_pcbdoc(): container only (geometry TODO)
                 ▼
 ┌─────────────────────────────────────────────────────────────┐
 │ Normalized Design model  (core/model.py)                    │
 │   Design { components[], nets[], rules[], schematic_docs[],  │
 │            pcb_docs[], meta }                                │
 │   Component / Net / DesignRule / SourceRef                   │
 │   → format-agnostic. No olefile types past this line.        │
 └───────┬─────────────────────────────────────────┬───────────┘
         │  checks/run_checks(design, select=...)   │  rules/emit_rul(pack)
         ▼                                          ▼
 ┌──────────────────────────┐        ┌──────────────────────────────┐
 │ SUB-PROJECT ① checks/    │        │ SUB-PROJECT ② rules/         │
 │  @register("SCH001",…)   │        │  RulePack → .RUL (byte-exact, │
 │  → yields Finding         │        │  provenance-gated)            │
 │  pure: no I/O, no mutate  │        │  manufacturers/ registry      │
 └───────────┬──────────────┘        └───────────────┬──────────────┘
             │                cli.py                  │
             ▼                                        ▼
 ┌─────────────────────────────────────────────────────────────┐
 │ CLI / report / CI gate                                      │
 │   inspect · review (exit!=0 on error) · checks · rules      │
 └─────────────────────────────────────────────────────────────┘
```

## Invariants

1. **Every sub-project depends on `core/`; sub-projects never depend on each
   other.** This is what lets the contribution paths (add-a-check vs
   add-a-manufacturer vs improve-parser) stay independent.
2. **`core/model` is format-agnostic.** No `olefile` objects, no raw Altium
   record dicts in the typed fields. Unmapped data goes into `.meta` so nothing
   is lost but nothing leaks either.
3. **Checks are pure.** Given a `Design` they yield `Finding`s; no I/O, no
   mutation. Trivially testable, safely runnable in any order / in parallel.
4. **Stable IDs.** A shipped check ID (`SCH###`/`PCB###`) doesn't change meaning;
   downstream users filter and gate CI on specific IDs.
5. **Honesty over coverage.** Unsupported formats report "unsupported" or set a
   capability flag (`design.meta["pcb_geometry_decoded"] == "false"`). We never
   emit fabricated geometry/data — on the generation side, never ship a `.RUL`
   rule kind whose full field set hasn't been round-tripped byte-for-byte against
   a real Altium export.

## Why a registry (and not a big if/else)

Same reason ruff/eslint scale: dozens of tiny, independent rules behind one
registry, each discoverable, each individually selectable, each separately
tested. Adding a rule (or a manufacturer pack) is additive — no existing code
changes — which keeps PRs small and review easy.

## Testing strategy

- Check logic is tested against hand-built `Design` objects (no files needed).
- Parser logic is tested against **synthesized** OLE2 files (`tests/_olewriter.py`)
  so the binary path is genuinely exercised on every OS in CI without committing
  proprietary sample files.
- Rule generation is tested by **byte-exact differential round-trip** against a
  vendored real Altium `.RUL` export (`tests/fixtures/rul/`).

## Future: splitting into independently-installable packages

Today this is **one** installable (`pip install altium-tools`, one version, one
CI). The folder boundaries above are deliberately drawn so that, once a
sub-project needs its own release cadence, it can be promoted to a standalone
distribution **without moving code across sub-project lines** — e.g. a uv
workspace where `core/`→`altium-core`, `rules/`→`altium-rules` (text-only, can
drop the `olefile` dep), `checks/`→`altium-review`. Until a real release need
exists, a single package is simpler and YAGNI wins. The structure already pays
for that option; we just don't exercise it prematurely.
