"""Review-check framework: the contributor extension point.

To add a new schematic/PCB review check, a contributor writes one function and
decorates it with @register. That's the whole API surface. Checks receive an
immutable Design and yield Findings. They must not mutate the design or do I/O.

This mirrors how linters (ruff, eslint) scale: many small, independent rules
behind one registry, each with a stable ID so results are filterable and CI can
gate on severity.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass, field
from enum import Enum

from ..core.model import Design, SourceRef


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class Finding:
    check_id: str  # stable, e.g. "SCH001"
    severity: Severity
    message: str
    source: SourceRef | None = None
    hint: str = ""  # suggested fix, optional


@dataclass
class CheckMeta:
    id: str
    title: str
    func: Callable[[Design], Iterable[Finding]]
    default_severity: Severity


_REGISTRY: dict[str, CheckMeta] = {}


def register(
    check_id: str,
    title: str,
    default_severity: Severity = Severity.WARNING,
) -> Callable[[Callable[[Design], Iterable[Finding]]], Callable[[Design], Iterable[Finding]]]:
    """Decorator registering a review check under a unique, stable ID."""

    def deco(
        func: Callable[[Design], Iterable[Finding]],
    ) -> Callable[[Design], Iterable[Finding]]:
        if check_id in _REGISTRY:
            raise ValueError(f"duplicate check id: {check_id}")
        _REGISTRY[check_id] = CheckMeta(check_id, title, func, default_severity)
        return func

    return deco


def all_checks() -> list[CheckMeta]:
    return sorted(_REGISTRY.values(), key=lambda c: c.id)


def run_checks(
    design: Design,
    select: Iterable[str] | None = None,
) -> Iterator[Finding]:
    """Run all (or a selected subset of) registered checks over a design."""

    selected = set(select) if select is not None else None
    for meta in all_checks():
        if selected is not None and meta.id not in selected:
            continue
        yield from meta.func(design)


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)

    @property
    def errors(self) -> int:
        return sum(1 for f in self.findings if f.severity is Severity.ERROR)

    @property
    def warnings(self) -> int:
        return sum(1 for f in self.findings if f.severity is Severity.WARNING)

    def worst(self) -> Severity:
        if any(f.severity is Severity.ERROR for f in self.findings):
            return Severity.ERROR
        if any(f.severity is Severity.WARNING for f in self.findings):
            return Severity.WARNING
        return Severity.INFO
