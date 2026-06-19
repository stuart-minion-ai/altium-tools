# Manufacturer Rule-Pack → Altium `.RUL` Generator — Implementation Plan

> **For Hermes:** Use subagent-driven-development to implement task-by-task. TDD, ruff+pytest green per task.

**Goal:** Build an importable Altium design-rules generator: curate major PCB manufacturers' fab capabilities into versioned rule packs (YAML), and emit native Altium `.RUL` files a user imports directly via *Design Rules ► Import Rules*. No Altium install, runs on Linux.

**Architecture:** New `rules/` application layer on top of the existing normalized model + CLI. `manufacturers/*.yaml` (data) → `RulePack` model → `emit_rul()` writer (pure Python text) → `.RUL` file. Two new CLI verbs: `rules list` and `rules generate`.

**Tech Stack:** Python 3.11, existing `altiumtools` package, pyyaml, pytest, ruff.

---

## 0. The decisive feasibility finding (why this is buildable on Linux)

**A `.RUL` file is plain pipe-delimited ASCII text — NOT OLE2, NOT binary.** Verified 2026-06-19 against a real `Fermium/Open-Altium-Rules/pcbway_base.RUL`:

- File is `ISO-8859 text`. One rule = one newline-terminated line of `|KEY=VALUE|` fields — the **same record grammar the project already parses for SchDoc**.
- 46 rule records covering all kinds (Clearance, Width, HoleSize, MinimumAnnularRing, HoleToHoleClearance, SolderMaskExpansion, RoutingVias, ComponentClearance, …).
- Example `Width` record:
  ```
  SELECTION=FALSE|LAYER=TOP|LOCKED=FALSE|POLYGONOUTLINE=FALSE|USERROUTED=TRUE|KEEPOUT=FALSE|UNIONINDEX=0|RULEKIND=Width|NETSCOPE=AnyNet|LAYERKIND=SameLayer|SCOPE1EXPRESSION=All|SCOPE2EXPRESSION=All|NAME=Width|ENABLED=TRUE|PRIORITY=1|COMMENT= |UNIQUEID=TYQKTGJP|DEFINEDBYLOGICALDOCUMENT=FALSE|MAXLIMIT=500mil|MINLIMIT=8mil|PREFEREDWIDTH=10mil
  ```
- **Consequence:** we can WRITE importable `.RUL` files in pure Python (string emit, no OLE writer needed). This is the opposite of the PcbDoc-geometry problem — fully decoded, low-risk, Linux-verifiable. This validates the product as genuinely shippable, not advisory-only.

**Import UX for the end user:** Altium PCB editor → PCB Rules and Constraints Editor → right-click *Design Rules* ► *Import Rules* → pick our `.RUL`. Confirmed against Altium KB + Constraints Editor docs.

**Honesty guard (project rule):** we only emit rule kinds whose full field set we've captured from a real reference file. Every templated rule kind must have a round-trip test (emit → re-parse → field equality). Rule kinds we haven't verified are NOT emitted — no guessing at field layouts.

---

## 1. Scope of v1 (YAGNI)

**In:** the DFM rule kinds every fab specifies and every board needs — the high-value, low-ambiguity set:
- `Clearance` (electrical), `Width` (min/pref/max), `HoleSize` (min/max drill), `MinimumAnnularRing`, `HoleToHoleClearance`, `RoutingVias` (via dia/hole), `SolderMaskExpansion`, `PasteMaskExpansion`, `SilkToSolderMaskClearance`.

**Manufacturers (rule packs) v1:** JLCPCB, PCBWay, OSH Park, Seeed Fusion — start with **JLCPCB + PCBWay** (most-used, public capability tables), structured so adding a fab = adding one YAML file.

**Out (defer):** impedance/diff-pair stackup math, per-net-class scoping UI, advanced RF rules, GUI. v1 emits AnyNet/All-scoped global rules (matches how fab base packs ship).

---

## 2. Data provenance rule (load-bearing — first principles, not docs-trust)

Manufacturer numbers come from each fab's **published capability table**, captured into the YAML with a `source:` URL and `captured:` date per pack. Capability tables drift — packs carry a version + date, and the plan includes a `scripts/refresh_capabilities.md` checklist. We do NOT hardcode a number without a cited source field. Where a fab quotes process-class tiers (e.g. JLCPCB 1oz vs 2oz, 5mil vs 3.5mil), v1 encodes the **standard/cheapest tier** and notes the tighter tier in a YAML comment.

---

## 3. Files

```
src/altiumtools/
  rules/
    __init__.py
    pack.py          # RulePack, RuleSpec dataclasses + YAML loader
    emit.py          # RulePack -> .RUL text (pure Python)
    fields.py        # per-RULEKIND field templates (verified from real .RUL)
  manufacturers/
    jlcpcb.yaml
    pcbway.yaml
    oshpark.yaml
    seeed.yaml
  cli.py             # + `rules list`, `rules generate`
tests/
  test_emit_rul.py           # round-trip: emit -> parse_rul -> field equality
  test_rule_packs.py         # every yaml loads, has source+date, values sane
  fixtures/pcbway_base.RUL   # real reference (Apache-compatible? verify license)
docs/
  RULE_GENERATOR_PLAN.md     # this file
```

`parse.py` gains `parse_rul(text)->list[dict]` (trivial reuse of existing record splitter) used only by tests to prove round-trip.

---

## 4. Tasks (bite-sized, TDD)

### Task 1: `parse_rul` + reference fixture
- Vendor a real `.RUL` as `tests/fixtures/` ONLY if license permits (Fermium repo — check LICENSE; if not Apache-compatible, regenerate an equivalent fixture from captured field templates instead of committing theirs).
- Add `parse_rul(text)` to `parse.py`: split on newlines, each line → `{KEY:VALUE}` dict via existing field regex.
- Test: parse fixture → assert ≥1 `RULEKIND=Width` record with `MINLIMIT`, `MAXLIMIT`, `PREFEREDWIDTH`.

### Task 2: field templates (`fields.py`)
- For each in-scope RULEKIND, a template dict of the full verified field set with placeholders. Captured from the real file (Width/Clearance/HoleSize/… shown in §0).
- Test: every template has the mandatory envelope fields (`RULEKIND, NETSCOPE, LAYERKIND, SCOPE1EXPRESSION, NAME, ENABLED, PRIORITY, UNIQUEID`).

### Task 3: `RulePack` model + loader (`pack.py`)
- Dataclasses: `RuleSpec(kind, params:dict, scope, priority)`, `RulePack(name, vendor, source, captured, units, rules:list[RuleSpec])`.
- `load_pack(path)` reads YAML → RulePack; validates required meta (`source`, `captured`).
- Test: load a tiny inline YAML → assert meta + rule count.

### Task 4: `emit_rul` writer (`emit.py`)
- `emit_rul(pack)->str`: for each RuleSpec, fill the matching template, generate a stable `UNIQUEID` (8 upper-alnum, deterministic from name+kind so re-gen is diff-stable), join fields with `|`, one record per line, trailing newline. Latin-1 safe.
- **Round-trip test (the honesty gate):** build a pack with Width{min:8mil,pref:10mil,max:500mil} → `emit_rul` → `parse_rul` → assert emitted record's fields equal intended values. Repeat per in-scope kind.

### Task 5: JLCPCB + PCBWay YAML packs
- Author `manufacturers/jlcpcb.yaml` and `pcbway.yaml` from each fab's published capability page (source URL + date in meta). Encode the in-scope rule kinds.
- Test: both load, every numeric within sane bounds (e.g. min trace ≥ 2mil & ≤ 20mil), units consistent.

### Task 6: CLI `rules list` / `rules generate`
- `altium-tools rules list` → table of bundled packs (vendor, version, date, #rules).
- `altium-tools rules generate jlcpcb -o jlcpcb.RUL` → writes file; `--units mil|mm`.
- Test: invoke generate into tmp path → file exists, `parse_rul` of output yields expected kinds; exit 0.

### Task 7: OSH Park + Seeed packs + docs
- Two more YAMLs. README section "Generate fab rules" with the import-into-Altium steps + screenshot-free textual walkthrough. CONTRIBUTING gains "add-a-manufacturer" path (mirrors add-a-check).

### Task 8: end-to-end verify + green gate
- `.venv/bin/ruff check . && .venv/bin/python -m pytest -q` green.
- Exercise CLI for real: generate all 4 packs, parse each back, assert kind coverage. Print the generated JLCPCB `.RUL` head as evidence.

---

## 5. Validation
- Round-trip equality per rule kind (emit→parse) is the core correctness proof on Linux.
- **Real-Altium import validation is the one thing we CANNOT do headless on Linux.** Flag for Chris: either (a) accept community validation via a GitHub issue template "import-tested on AD version X", or (b) Chris/someone imports one generated `.RUL` on a Windows Altium seat once to confirm. Until then, README states "format-validated against real exported `.RUL`; community import-confirmation tracked in #N." No fabricated "tested in Altium" claim.

## 6. Risks
- **R1 license of reference fixture** → don't commit a copyleft/WTFPL `.RUL`; regenerate our own equivalent. (Mitigated in Task 1.)
- **R2 capability-table drift** → versioned packs + `source`/`captured` meta + refresh checklist.
- **R3 process-tier ambiguity** → encode standard tier, comment the advanced tier; document the choice.
- **R4 Altium version field variance** → templates captured from one real file may miss version-specific optional fields; emit the verified envelope only, fail loud on unknown requested kind.

## 7. Open questions for Chris
- Q1 Confirm v1 manufacturer set (JLCPCB, PCBWay, OSH Park, Seeed) and priority order.
- Q2 Is there a Windows Altium seat available for a one-time import smoke-test, or do we ship "format-validated, import-community-confirmed"?
- Q3 v1 scope = global AnyNet/All rules only (defer net-class scoping)? Recommended yes.

---

## 8. Extensibility, intelligence & distribution (design — added 2026-06-19)

### 8.1 Two axes of "extensible" — keep them separate
- **Data extensibility (open by drop-in file):**
  - *Add a manufacturer* = drop one `manufacturers/<fab>.yaml` (meta + rule values). No code.
  - *Add a rule kind* = add one verified template to `fields.py` + one round-trip test. Mirrors the existing `checks/` registry pattern (add-ONE-function contributor path). The honesty gate (only emit kinds with a captured real field set) is what keeps this open without letting contributors guess field layouts.
- **Distribution extensibility (how it reaches the user):** the 3-tier ladder below.

### 8.2 The plugin ladder (grounded in Altium's actual extension mechanisms)
Verified: Altium exposes (a) a scripting API — `IPCB_Board`/`IPCB_Rule` can add/delete/modify rules (examples in `\Examples\Scripts\Delphiscript\PCB`), and (b) a compiled Extensions system (DXP Developer: register→install→publish, needs Delphi/C# DLL + SDK + signing, Windows-only to build).

| Tier | Artifact | "Install" UX | Build cost | Where it runs | Verdict |
|---|---|---|---|---|---|
| **T0** | `.RUL` text file | GUI: *Design Rules ► Import Rules* | **zero** (pure Python, Linux) | any AD | **ship v1** |
| **T1** | DelphiScript script-project (`.PrjScr` + `.pas`) bundling the pack | Add via *DXP » Scripting System* or Preferences → appears as a menu item "Generate Fab Rules" | low (text `.pas`, **no compile, no SDK**) | any AD | **v2 — the real "installable plugin" sweet spot** |
| **T2** | Compiled DXP Extension (`.DllExtension`) + auto-update feed | Extensions & Updates → install | **high** (Windows+Delphi/C#, SDK, signing, publish) | any AD | **defer** unless real demand |

**Load-bearing architecture rule: brain in Python, dumb shell in Altium.** All intelligence (manufacturer data, tier selection, board-aware tuning, DFM checks) lives in the Linux-testable Python core. The Altium-side artifact is THIN: T0 = just data; T1 = a ~50-line DelphiScript that calls Import (or applies rules via `IPCB_Board`) on the bundled `.RUL`. **Never put rule logic in DelphiScript** — it's untestable on Linux and violates the project's honesty/testability discipline. T1 doesn't reimplement the brain; it ships the brain's *output* + a thin trigger.

### 8.3 Intelligence layer (`智能化`) — only what adds real, testable value
All Python, all unit-testable on Linux. Ordered by value/effort:
1. **Capability reconciliation engine** (highest value): fab capability matrix + board params (layer count, copper weight, target min feature) → auto-select the correct **process tier** and emit the matching rule values, flagging any infeasible request. Turns flat packs into board-aware packs. Fully testable.
2. **DFM pre-check / `rules check`**: parse the design → compare against the chosen fab pack → report violations *before* the fab rejects the order. **Honest bound:** SchDoc is decoded; PcbDoc *geometry* is NOT (`pcb_geometry_decoded=false`) — so geometric DFM is limited to what the parser actually exposes (net classes, layer stack where present). We surface the capability flag, never fake geometry. This is the natural bridge to the existing `checks/` registry (a new check family: `DFM###`).
3. **Multi-fab comparison**: "passes JLCPCB, violates PCBWay min annular ring (6mil vs 5mil)." Pure pack-diff, trivial once packs exist.
4. **LLM-assisted capability ingestion** (the "smart data" angle, with a hard honesty gate): an offline helper scrapes a fab's published capability page → drafts a YAML pack → **a human confirms `source` URL + `captured` date before it ships.** Never auto-publish a scraped number. This keeps ingestion fast without breaking provenance (§2).
5. **Explainable rules**: each emitted rule carries its `source`/tier in the pack so `rules generate --explain` can justify every value.

---

## 9. The smart smoke-test (Q2, re-derived)

**The one thing we cannot do headless on Linux is run Altium.** Don't fake it (Wine is unreliable for AD; no free Altium in CI). Instead **invert the question**: don't ask "does Altium accept our file?" — prove "our file is structurally indistinguishable from a file Altium itself exported."

- **Differential testing against Altium-authored `.RUL` (primary, Linux-native):** build a corpus of real `.RUL` files *exported by Altium* (OSH Park publishes an official one; Open-Altium-Rules; any fab-published `.RUL`). Have our generator reproduce the equivalent pack → diff field-by-field. **Pass criterion:** the *only* deltas are values, `UNIQUEID`, and whitespace — the per-kind field envelope is byte-identical to Altium's own output. That is strong format-fidelity evidence **without a Windows seat**, and it runs in CI on every commit.
- **T1 self-test DelphiScript (community-confirmable, one-shot):** ship a tiny script that, on a real seat, *imports our `.RUL` → re-exports → reports rule count + any parser error*. One community member runs it once and pastes the output into a GitHub issue template ("import-tested on AD version X"). This converts the unverifiable claim into a cheap, auditable community check.
- **Honest README wording (no fabricated claim):** *"Format-validated by differential test against Altium-exported `.RUL` files; live-import community-confirmed on AD vX (issue #N)."* Never "tested in Altium" until §two above actually returns green from a real seat.

### Q4 (new) — distribution target for v2
After v1 (T0) ships, build T1 (DelphiScript installable) or stop at T0 + the differential smoke-test? Recommended: **ship T0, prove it with the §9 differential test, then do T1.** Skip T2 unless someone asks.
