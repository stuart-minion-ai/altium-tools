# Contributing to altium-tools

Thanks for helping make Altium easier to use! This project is built to be
contributed to. There are two main ways to help, and they are decoupled so you
can pick one without learning the other.

## Ground rules

- Be friendly. This is a community project.
- Keep changes small and focused; one logical change per PR.
- Every code change ships with a test. CI must be green.
- Run `ruff check . && ruff format . && pytest` before pushing.
- No fabricated parser output. If a format isn't decoded yet, return
  "unsupported" / a capability flag — never guesses. An honest gap beats a
  plausible-looking lie.

## Dev setup

```bash
git clone <your-fork-url>
cd altium-tools
python -m venv .venv && source .venv/bin/activate   # or: uv venv
pip install -e ".[dev]"                              # or: uv pip install -e ".[dev]"
pytest -q
ruff check .
```

## Path A — add a review check (no binary parsing needed)

This is the easiest first contribution.

1. Open `src/altiumtools/checks/builtin.py` (or add a new module imported by it).
2. Write a function that takes a `Design` and yields `Finding`s. Decorate it
   with `@register("ID", "title", default_severity)`.
   - IDs: `SCH###` schematic, `PCB###` board, `RUL###` rule planning, `BOM###`.
   - Pick the next free number in that family.
   - Checks must be **pure**: no I/O, no mutation of the design.
3. Add a test in `tests/test_checks.py` (positive *and* negative case).
4. `pytest -q && ruff check .`, then open a PR.

See the [README "Add a check"](README.md#add-a-check-in-10-lines) snippet.

## Path B — improve the Altium file parser

Decoding more of Altium's binary formats is the highest-impact work. The OLE2
container already parses (`inspect_ole`); the open problem is the record
payloads, especially in `.PcbDoc`.

1. Read [docs/ALTIUM_FILE_FORMAT.md](docs/ALTIUM_FILE_FORMAT.md) for what's known.
2. Use `altium-tools inspect yourfile.PcbDoc` to see streams.
3. Map decoded data into the neutral `core/model.py` dataclasses — never leak
   Altium-specific record shapes past the parser boundary.
4. Add a test. We synthesize OLE files in tests via `tests/_olewriter.py` so you
   don't need a proprietary sample committed to the repo. Do **not** commit real
   customer design files.

## Commit / PR conventions

- Conventional-ish messages: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`.
- Reference an issue when one exists.
- PRs need a green CI run and at least one maintainer review.

## Code of Conduct

Be respectful and constructive. Harassment of any kind is not tolerated.
