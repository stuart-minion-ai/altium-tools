# AGENTS.md — altium-tools (open-source repo dev context)

Auto-loaded when an agent works in this repo. This is the **public** open-source
project; keep it clean for outside contributors. For channel/firewall rules see
`../AGENTS.md` and `../SCOPE.md` (workspace root) — those are private and NOT
part of this repo.

## What this is
`altiumtools` — OS-independent tooling to analyze Altium Designer artifacts
(`.SchDoc`/`.PcbDoc`/`.PcbLib`/`.SchLib`) on any OS, because Altium files are
Microsoft OLE2 compound documents parseable in pure Python (no Altium install).
Apache-2.0, src-layout, hatchling, console script `altium-tools`.

## Architecture (3 decoupled layers — keep them decoupled)
1. `src/altiumtools/parse.py` — olefile (READ-ONLY) → records → model.
   `inspect_ole()` always works. `parse_schdoc()` decodes pipe-delimited ASCII
   records (`|RECORD=1|SOURCEDESIGNATOR=R1|...`). `parse_pcbdoc()` = container
   only; sets meta `pcb_geometry_decoded=false` — PCB binary geometry is
   deliberately NOT faked (community Milestone 1). Depends on `model` only.
2. `src/altiumtools/model.py` — format-agnostic dataclasses (Design/Component/
   Net/DesignRule/SourceRef). No olefile types leak past here; unmapped → `.meta`.
3. `src/altiumtools/checks/` — a registry (like ruff/eslint). Contributors add ONE
   `@register("SCH001", ...)` pure function yielding `Finding`s. Depends on
   `model`, NOT on `parse`. **Subpackage → import `from ..model` (two dots).**
4. `src/altiumtools/cli.py` — `inspect` / `review` (exit≠0 on error = CI gate) /
   `checks`. The two contribution paths (add-a-check vs improve-parser) are
   independent by design.

## Honesty rule (project-defining)
Never emit fabricated parser output for undecoded formats. Return "unsupported"
or a capability flag. A parser that returns guesses is worse than one that says
it can't. Mirror this in any PR review.

## Dev workflow
- venv: `.venv` (uv, py3.11). Tests: `.venv/bin/python -m pytest -q` (13 green).
  Lint: `.venv/bin/ruff check .`. Both must pass before commit.
- olefile is read-only → tests synthesize real OLE2 files via `tests/_olewriter.py`
  (minimal CFB writer). Do NOT commit proprietary `.SchDoc`/`.PcbDoc` (gitignored).
- Remote: `stuart-minion-ai/altium-tools` (HTTPS, gh logged in as that account).
- Next real work: Milestone 1 (PCB geometry record decoding) + schematic netlist
  extraction (wires→nets→node_count) to light up PCB002 on real data.
