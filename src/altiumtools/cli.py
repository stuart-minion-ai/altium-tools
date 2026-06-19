"""Command-line interface for altium-tools.

Subcommands:
  inspect <file>          List OLE streams in an Altium binary file.
  review  <file>...       Run review checks; exit non-zero if errors found.
  checks                  List all registered review checks.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

# Importing builtin registers the bundled checks as a side effect.
from . import __version__
from .checks import Severity, all_checks, run_checks
from .checks import builtin as _builtin  # noqa: F401  (registration side effect)
from .parse import UnsupportedFile, inspect_ole, load, merge

_SEV_ORDER = {Severity.INFO: 0, Severity.WARNING: 1, Severity.ERROR: 2}


def _cmd_inspect(args: argparse.Namespace) -> int:
    try:
        streams = inspect_ole(args.file)
    except UnsupportedFile as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    for name, size in sorted(streams.items()):
        print(f"{size:>10}  {name}")
    print(f"\n{len(streams)} streams", file=sys.stderr)
    return 0


def _cmd_checks(_args: argparse.Namespace) -> int:
    for meta in all_checks():
        print(f"{meta.id}  [{meta.default_severity.value:<7}]  {meta.title}")
    return 0


def _cmd_review(args: argparse.Namespace) -> int:
    designs = []
    for f in args.file:
        try:
            designs.append(load(f))
        except UnsupportedFile as e:
            print(f"warning: skipping {f}: {e}", file=sys.stderr)
    if not designs:
        print("error: no parseable input files", file=sys.stderr)
        return 2

    design = merge(designs)
    findings = sorted(
        run_checks(design, select=args.select or None),
        key=lambda x: (-_SEV_ORDER[x.severity], x.check_id),
    )

    errors = warnings = 0
    for f in findings:
        errors += f.severity is Severity.ERROR
        warnings += f.severity is Severity.WARNING
        loc = f" ({f.source.document}:{f.source.locator})" if f.source else ""
        line = f"{f.severity.value.upper():<7} {f.check_id}{loc}: {f.message}"
        if f.hint:
            line += f"\n          -> {f.hint}"
        print(line)

    print(
        f"\n{len(findings)} findings: {errors} error(s), {warnings} warning(s)",
        file=sys.stderr,
    )
    return 1 if errors else 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="altium-tools", description=__doc__)
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    ins = sub.add_parser("inspect", help="list OLE streams in an Altium file")
    ins.add_argument("file")
    ins.set_defaults(func=_cmd_inspect)

    chk = sub.add_parser("checks", help="list registered review checks")
    chk.set_defaults(func=_cmd_checks)

    rev = sub.add_parser("review", help="run review checks over Altium files")
    rev.add_argument("file", nargs="+")
    rev.add_argument(
        "--select", action="append", help="only run these check IDs (repeatable)"
    )
    rev.set_defaults(func=_cmd_review)

    return p


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
