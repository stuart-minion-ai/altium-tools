# altium-tools — Project Analysis & Strategic Roadmap

> Research + planning report. Big-picture direction first, details second.
> Author: foundational analysis, 2026-06-19. Status: **for Chris's review — decisions needed at bottom.**

---

## 0. TL;DR (and an honest reversal)

We set out to "build tools that make Altium Designer faster — smart rule planning, schematic/PCB review." After deep research into prior art, the first-principles conclusion **reverses my own previous plan** (the "write our own `.PcbDoc` binary decoder as Milestone 1" idea from the foundation commit):

1. **Parsing Altium files is a solved-ish, crowded problem.** At least **5 open-source parsers** already exist, one of them (`altium_monkey`) is *very* actively developed (last push 3 days ago) and already reads **and writes** SchDoc/SchLib/PcbDoc/PcbLib. Rebuilding a binary decoder from scratch would be **months of low-differentiation work** duplicating what KiCad's ~8,000-line C++ Altium importer and these libs already do.

2. **The genuinely underserved gap is the *review / rules-planning layer*, not the parser.** Everyone ships a parser and *maybe* a "design-review helper" as an afterthought. Nobody ships an **opinionated, curated, CI-first design-review product for Altium** the way KiBot/kicad-cli serve the KiCad world. Altium has **no official headless CLI** — so there is no `altium-cli drc` equivalent. That vacuum is our opening.

3. **License is a real wedge.** The most capable incumbents are **AGPL-3.0 / GPL-3.0** (viral copyleft — many companies legally can't touch them) or **WTFPL** (legally unusable in enterprise). We're **Apache-2.0 (permissive)**. A permissive, corporate-friendly Altium review tool is a defensible niche on its own.

**Recommended direction:** Pivot from *"another Altium parser"* to **"the open-source design-review & rule-planning layer for Altium"** — standing on existing parsers where we can, owning the **checks engine, curated rule packs, CI integration, and human-readable reports**. Our existing registry-based check architecture is *already* the right core for this; the parser is a means, not the product.

This is exactly the kind of plan-reversal your doctrine demands: the honest deliverable is the opposite of the literal "build a parser" instinct.

---

## 1. Problem space & pain points (what actually hurts)

Sourced from Altium's own docs, community posts, and the shape of existing tooling.

| # | Pain point | Why it exists | Our leverage |
|---|-----------|---------------|--------------|
| P1 | **No headless/CLI mode.** Altium automation = DelphiScript/VBScript *inside the GUI*. You can't run a review in CI, on a server, or pre-commit without a licensed Windows GUI session. | Altium is a closed Windows desktop app; scripting is in-process only. | A file-level analysis core needs **no Altium install** → runs in CI/Linux/macOS. This is the structural unlock. |
| P2 | **Review is manual & tribal.** "Did you check unconnected nets / missing designators / no clearance rule / single-pin nets / power not decoupled?" lives in senior engineers' heads and PDF checklists, not in tooling. | Altium's built-in ERC/DRC is rule-config-heavy and GUI-bound; team conventions aren't encoded. | A **registry of codified review checks** + shareable **rule packs** turns tribal knowledge into version-controlled, reviewable code. |
| P3 | **Rule setup is tedious & error-prone.** Clearance/width/via/polygon rules are hand-built per project; inconsistency across projects causes respins. | Rules live in the binary project file, edited via GUI dialogs. | **"Smart rules planning"**: generate/validate a rule set from a declarative spec (stackup, class, impedance intent) → diff against the project. |
| P4 | **Diffing & code review of PCB/sch changes is awful.** Binary files → Git shows "binary file changed." No meaningful PR review of hardware. | Proprietary binary format, no canonical text projection. | Parse → **stable normalized JSON/text projection** → real diffs, real PR comments. |
| P5 | **Vendor lock-in anxiety / interop.** Teams want to read their own data (BOM, nets, parts) without a seat for every viewer. | Format is undocumented & proprietary. | Permissive-licensed extraction that teams can embed anywhere. |

**The throughline:** Altium's closed, GUI-only automation model is the root cause. Every pain is a symptom. A **file-level, install-free, scriptable layer** is the first-principles fix — and the *review* application of that layer is where users feel value fastest.

---

## 2. Competitive landscape (prior art — researched 2026-06-19)

### 2a. Altium file parsers / libraries

| Project | Lang | License | Stars | Last push | Scope | Read/Write |
|---|---|---|---|---|---|---|
| **wavenumber-eng/altium_monkey** | Python | **AGPL-3.0** | 148 | 2026-06-16 ⚠️*active* | SchDoc/SchLib/PcbDoc/PcbLib/PrjPcb/OutJob/IntLib + render + "design-review helpers" | R **+W** |
| vadmium/python-altium | Python | WTFPL | 192 | 2022-11 (stale) | SchDoc → SVG/GUI | R |
| gsuberland/altium_js | JS | MIT | 143 | 2025-05 | SchDoc parse+render in browser (AD ≤22.5) | R |
| a3ng7n/Altium-Schematic-Parser | Python | **MIT** | 50 | 2026-01 | SchDoc → JSON (parts-list, net-list) | R |
| ChrisHoyer/pyAltiumLib | Python | (unset) | — | active | Library files (SchLib/PcbLib) read | R |
| pluots/PyAltium → `altium` (Rust) | Rust | GPL-3.0 | 10 | 2023-07 (alpha) | SchLib + binary PcbDoc (alpha) | R |
| altium-format (Rust crate) | Rust | GPL-3.0 | — | active | Read+write, "agent-friendly CLI" | R+W |

**Reading:** The schematic side is **well-covered**. The PCB binary side is **harder and less mature** (KiCad's C++ importer ~8,000 lines is the canonical reference; pastebom notes *no* solid open-source Rust PcbDoc impl). The most complete, most active lib (`altium_monkey`) is **AGPL** — powerful but a non-starter for many companies, and it positions as a *library*, not a *review product*.

### 2b. The review/CI tooling world (mostly KiCad — the gap for Altium is glaring)

| Project | Ecosystem | License | What it does | Altium? |
|---|---|---|---|---|
| INTI-CMNB/**KiBot** | KiCad | AGPL-3.0 | 723★ CI/CD: ERC/DRC, fab outputs, the gold standard | ❌ KiCad only |
| kicad-cli (official) | KiCad | GPL | Headless DRC/ERC/plot | ❌ |
| KiCad Action / **KiCad Design Review** (Marketplace) | KiCad | — | GH Action: ERC/DRC on PRs; AI review of sch/PCB/Gerber | ❌ |
| rjwalters/kicad-tools | KiCad | MIT | "AI assistant that reviews PCB designs, DRC in CI" | ❌ |
| Seeed kicad-mcp-server / kicad-mcp-pro | KiCad | — | MCP servers exposing KiCad to AI agents | ❌ |
| designGuard | KiCad | — | Desktop "spell-check for your PCB" | ❌ |

**The headline finding:** A rich ecosystem of **automated/AI design review + CI** exists for **KiCad** and *none of it* serves **Altium**, because Altium has no headless CLI to build on. **We can be "KiBot/Design-Review for Altium."** That's a clear, defensible, currently-empty position.

---

## 3. Positioning & differentiation

**What we are:** *The open-source, permissively-licensed, CI-first design-review and rule-planning layer for Altium — no Altium install required.*

**Three differentiators, in priority order:**

1. **Review as the product, not a side-effect.** Curated, documented **rule packs** (power-integrity, DFM-lite, naming/designator hygiene, net-class sanity, unconnected/single-pin nets, missing decoupling, clearance-rule presence). Each check: id, severity, rationale, fix hint, doc link. The registry we already built is the engine.
2. **Apache-2.0 permissive.** Corporate-adoptable where AGPL `altium_monkey` / GPL crates / WTFPL libs are not. This alone wins enterprise users and contributors whose employers forbid copyleft.
3. **CI-native & agent-native.** First-class GitHub Action + non-zero exit on errors (already done) + machine-readable JSON report → feeds PR comments, dashboards, and LLM reviewers (MCP server later). Altium's GUI-lock makes this uniquely valuable.

**What we deliberately are NOT (YAGNI / anti-scope-creep):**
- Not a renderer/viewer (altium_js, python-altium own that).
- Not a write/round-trip editor (altium_monkey owns that; writing proprietary binaries is a liability sink).
- Not a from-scratch PcbDoc decoder *if* we can interop. (See Decision D2.)

---

## 4. Architecture implications (how the pivot changes the build)

Our current 3-layer split is **validated** — keep it. The change is *where parsing comes from* and *where we invest*:

```
            ┌─────────────────────────────────────────────┐
            │  INPUT ADAPTERS  (pluggable parse sources)   │
            │  • native OLE core (ours) — structure+streams │
            │  • SchDoc record decode (ours, schematic)     │
            │  • adapter: a3ng7n JSON / ASCII-export / …    │  ← interop, not rebuild
            │  • (later) PcbDoc via best available source   │
            └───────────────────────┬─────────────────────┘
                                    ▼
            ┌─────────────────────────────────────────────┐
            │  NORMALIZED DESIGN MODEL  (format-agnostic)  │  ← the contract; the moat
            │  Sheet, Component, Pin, Net, Rule, …          │
            └───────────────────────┬─────────────────────┘
                                    ▼
            ┌─────────────────────────────────────────────┐
            │  APPLICATIONS                                │
            │  • Review engine + rule packs (registry)  ★  │  ← primary product
            │  • Rule planner (declarative spec → rules)    │
            │  • Diff / text-projection (PR review)         │
            │  • Reporters: text / JSON / SARIF / md        │
            └─────────────────────────────────────────────┘
```

**Key design decisions this implies:**
- **The normalized model is the moat**, not the parser. Stable, documented, well-tested. Multiple parse backends feed it; all apps consume it. A contributor can add a *check* (most common contribution) touching only the registry, never the binary code.
- **Parser = adapter pattern.** Wrap/interop with existing parsers where license allows (MIT a3ng7n is compatible; AGPL altium_monkey is **not** safe to depend on for an Apache project — avoid linking). Keep our own minimal native parse for the schematic basics so we have a permissive, dependency-light path.
- **SARIF output** unlocks GitHub code-scanning UI for free — high-leverage reporter.
- **Rule packs as data + code**, versioned, each independently testable (mirrors how our backtest/options work treats checks as first-class, gated artifacts).

---

## 5. Phased roadmap

### Phase 0 — Foundation ✅ (done)
Analysis core, registry, OLE parser, CLI, docs, CI, Apache-2.0, repo live at `stuart-minion-ai/altium-tools`.

### Phase 1 — "Make review real on schematics" (highest ROI, fully Linux-verifiable)
- Decode enough SchDoc records to populate the model with **components, pins, wires → nets** (this is the gap that makes net-based checks live, not empty).
- Ship **rule-pack v1** (8–12 curated schematic checks) with severities, rationale, fix hints.
- **SARIF + JSON + text** reporters.
- **GitHub Action** wrapping the CLI (the "KiBot-for-Altium-review" MVP).
- Gate: each check has a synthetic-fixture test; ruff+pytest green in CI.

### Phase 2 — "Smart rules planning"
- Declarative rule spec (YAML: stackup, net-classes, clearances, widths, impedance intent).
- Validate a project's existing rules against spec; **report missing/inconsistent rules** (P3).
- Generate a starter rule set from spec.

### Phase 3 — "Diff & PR review"
- Stable text projection of sch (and later PCB) → meaningful `git diff` + PR-comment bot.

### Phase 4 — PCB layer (only when justified)
- Decide build-vs-interop for `.PcbDoc` (Decision D2). Geometry/DRC checks. This is the hard, less-mature frontier — enter deliberately, with a real `.PcbDoc` fixture in hand, not speculatively.

### Phase 5 — Agent/MCP surface
- MCP server exposing review/query to LLM agents (the KiCad world already has this; Altium doesn't).

---

## 6. Risks, tradeoffs & open questions

- **R1 — Format fragility.** Altium changes binary layout across versions (altium_js caps at AD 22.5). *Mitigation:* version-tag fixtures; fail loudly with "unsupported record" rather than guessing (our existing honesty stance).
- **R2 — No real test fixtures on this Linux host / no Altium license.** We've been synthesizing OLE files. *Mitigation:* curate a small set of permissively-licensed real `.SchDoc/.PcbDoc` samples (some exist in altium-format's test data — check license before vendoring). **Need at least one real file to validate Phase 1.**
- **R3 — License contamination.** Must **not** copy code from AGPL `altium_monkey` / GPL crates into Apache repo. *Mitigation:* clean-room; reference only public format docs (KiCad importer is GPL too — read for *understanding*, don't copy code; reference the prose format write-ups instead).
- **R4 — "Yet another parser" perception.** *Mitigation:* lead every doc with *review/CI*, not parsing. Position against KiBot, not against altium_monkey.
- **R5 — altium_monkey could add a permissive review product.** It's active and broad. *Mitigation:* move fast on curated rule packs + permissive license + CI polish; that's product+legal surface they're not focused on.

---

## 7. Decisions needed from Chris 🚩

- **D1 — Endorse the pivot?** "Open-source **design-review & rule-planning layer** for Altium (Apache-2.0, CI-first)" vs. "general Altium parsing library." I strongly recommend the former.
- **D2 — Parser strategy:** (a) **own minimal permissive parser** for schematic basics (keeps us dependency-light & Apache-clean), interop with MIT a3ng7n where useful; defer PcbDoc. vs. (b) try to depend on an existing lib (license rules out the best ones). I recommend **(a)**.
- **D3 — First vertical slice:** confirm **Phase 1 = "decode SchDoc components/pins/wires→nets + rule-pack v1 + GitHub Action + SARIF."** That's the smallest thing that makes the review genuinely useful and demoable.
- **D4 — Real fixtures:** OK to source a couple of permissively-licensed real `.SchDoc` sample files for the test suite (verifying each file's license first)?

Once you pick, I'll turn the chosen phase into a bite-sized, TDD, task-by-task implementation plan and execute it green.
