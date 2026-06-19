"""Normalized design model.

The point of this module is decoupling: parsers (which read Altium's native,
sometimes-undocumented binary formats) produce these neutral dataclasses, and
review checks consume *only* these. A contributor writing a check never touches
OLE parsing; a contributor improving the parser never touches check logic.

Keep this model format-agnostic. Anything Altium-specific that a parser can map
into a neutral concept (a net, a component, a rule) belongs here; raw record
blobs stay in `meta`.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SourceRef:
    """Where a model object came from, for actionable review messages."""

    document: str  # e.g. "main.SchDoc" or "board.PcbDoc"
    locator: str = ""  # parser-defined: stream name, record index, designator...


@dataclass
class Component:
    designator: str  # "R1", "U3"; "" if unannotated
    comment: str = ""  # value/part, e.g. "10k", "STM32F103"
    footprint: str = ""
    library_ref: str = ""
    pins: list[str] = field(default_factory=list)  # pin designators
    source: SourceRef | None = None
    meta: dict[str, str] = field(default_factory=dict)


@dataclass
class Net:
    name: str
    node_count: int = 0  # number of pins/pads on the net
    source: SourceRef | None = None
    meta: dict[str, str] = field(default_factory=dict)


@dataclass
class DesignRule:
    """A normalized EDA rule (clearance, width, etc.)."""

    kind: str  # "Clearance", "Width", "RoutingVias", ...
    name: str
    scope: str = "All"  # query/scope expression as text
    enabled: bool = True
    constraints: dict[str, str] = field(default_factory=dict)
    source: SourceRef | None = None


@dataclass
class Design:
    """The whole parsed project: the single object checks operate on."""

    name: str = ""
    schematic_docs: list[str] = field(default_factory=list)
    pcb_docs: list[str] = field(default_factory=list)
    components: list[Component] = field(default_factory=list)
    nets: list[Net] = field(default_factory=list)
    rules: list[DesignRule] = field(default_factory=list)
    meta: dict[str, str] = field(default_factory=dict)
