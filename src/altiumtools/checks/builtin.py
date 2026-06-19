"""Built-in schematic/PCB review checks.

These are real, useful checks AND the contributor template. Each is small,
independent, pure, and has a stable ID. Copy one to add your own, then it is
picked up automatically (see altiumtools.checks.builtin loading in cli).

ID convention:
  SCH### schematic-level   PCB### board-level   RUL### design-rule planning
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable

from ..core.model import Design
from . import Finding, Severity, register


@register("SCH001", "Components missing a designator", Severity.ERROR)
def missing_designator(design: Design) -> Iterable[Finding]:
    for c in design.components:
        d = c.designator.strip()
        if not d or d.endswith("?"):  # "R?" = un-annotated in Altium
            yield Finding(
                "SCH001",
                Severity.ERROR,
                f"Component has no real designator (comment={c.comment!r}).",
                c.source,
                hint="Run Tools > Annotate Schematics to assign designators.",
            )


@register("SCH002", "Duplicate designators", Severity.ERROR)
def duplicate_designators(design: Design) -> Iterable[Finding]:
    counts = Counter(
        c.designator.strip() for c in design.components if c.designator.strip()
    )
    for desig, n in counts.items():
        if n > 1:
            yield Finding(
                "SCH002",
                Severity.ERROR,
                f"Designator {desig!r} used by {n} components.",
                hint="Re-annotate; duplicate designators break netlist/BOM.",
            )


@register("SCH003", "Components missing a value/comment", Severity.WARNING)
def missing_value(design: Design) -> Iterable[Finding]:
    # Passives without a value are almost always a mistake.
    passive_prefixes = ("R", "C", "L")
    for c in design.components:
        d = c.designator.strip()
        if d[:1] in passive_prefixes and not c.comment.strip():
            yield Finding(
                "SCH003",
                Severity.WARNING,
                f"{d} has no value/comment.",
                c.source,
                hint="Set the Comment/Value parameter.",
            )


@register("PCB001", "Components missing a footprint", Severity.ERROR)
def missing_footprint(design: Design) -> Iterable[Finding]:
    for c in design.components:
        if not c.footprint.strip():
            yield Finding(
                "PCB001",
                Severity.ERROR,
                f"{c.designator or '<no designator>'} has no footprint; cannot be placed.",
                c.source,
                hint="Add a PCB footprint model to the component.",
            )


@register("PCB002", "Single-node nets (likely unconnected)", Severity.WARNING)
def single_node_nets(design: Design) -> Iterable[Finding]:
    for net in design.nets:
        if net.node_count == 1:
            yield Finding(
                "PCB002",
                Severity.WARNING,
                f"Net {net.name!r} has only one node (floating/unconnected?).",
                net.source,
                hint="Verify the connection or add a no-ERC marker if intentional.",
            )


@register("RUL001", "No clearance design rule defined", Severity.WARNING)
def no_clearance_rule(design: Design) -> Iterable[Finding]:
    if design.pcb_docs and not any(r.kind == "Clearance" for r in design.rules):
        yield Finding(
            "RUL001",
            Severity.WARNING,
            "PCB present but no Clearance rule found.",
            hint="Define a Clearance rule before routing; relying on defaults is risky.",
        )
