"""Verified field templates for each supported ``.RUL`` rule kind.

EVERY entry in this module was extracted from a real, Altium-exported ``.RUL``
file (tests/fixtures/rul/pcbway_base.RUL). Nothing here is guessed. The
differential fidelity test (tests/test_rules_fidelity.py) re-derives these
orderings from the fixture and fails if this module drifts from ground truth.

Structure of every record:
* An 18-field common ENVELOPE (identical key order across all kinds).
* Followed by the kind-specific CONSTRAINT fields.

To add a kind you MUST capture its full field envelope from a real file and add
a round-trip test. Do not hand-author field lists from documentation -- Altium's
field set and ordering are not fully documented and guessing breaks import.
"""

from __future__ import annotations

# The common front matter, in the exact order Altium writes it.
ENVELOPE_FIELDS: tuple[str, ...] = (
    "SELECTION",
    "LAYER",
    "LOCKED",
    "POLYGONOUTLINE",
    "USERROUTED",
    "KEEPOUT",
    "UNIONINDEX",
    "RULEKIND",
    "NETSCOPE",
    "LAYERKIND",
    "SCOPE1EXPRESSION",
    "SCOPE2EXPRESSION",
    "NAME",
    "ENABLED",
    "PRIORITY",
    "COMMENT",
    "UNIQUEID",
    "DEFINEDBYLOGICALDOCUMENT",
)

# Per-kind constraint fields that follow the envelope, in verified order.
CONSTRAINT_FIELDS: dict[str, tuple[str, ...]] = {
    "Clearance": (
        "GAP",
        "GENERICCLEARANCE",
        "IGNOREPADTOPADCLEARANCEINFOOTPRINT",
        "OBJECTCLEARANCES",
    ),
    "Width": (
        "MAXLIMIT",
        "MINLIMIT",
        "PREFEREDWIDTH",  # note: Altium's real (misspelled) key
    ),
    "HoleSize": (
        "ABSOLUTEVALUES",
        "MAXLIMIT",
        "MINLIMIT",
        "MAXPERCENT",
        "MINPERCENT",
    ),
    "MinimumAnnularRing": (
        "MINIMUMRING",
    ),
    "HoleToHoleClearance": (
        "GAP",
        "ALLOWSTACKEDMICROVIAS",
    ),
    "RoutingVias": (
        "HOLEWIDTH",
        "WIDTH",
        "VIASTYLE",
        "MINHOLEWIDTH",
        "MINWIDTH",
        "MAXHOLEWIDTH",
        "MAXWIDTH",
    ),
    "SolderMaskExpansion": (
        "EXPANSION",
    ),
    "PasteMaskExpansion": (
        "EXPANSION",
    ),
    "SilkToSolderMaskClearance": (
        "MINSILKSCREENTOMASKGAP",
        "CLEARANCETOEXPOSEDCOPPER",
    ),
}

SUPPORTED_KINDS: tuple[str, ...] = tuple(CONSTRAINT_FIELDS)

# Default envelope values for GENERATED rules (the parts not derived from a
# DesignRule). Captured from the fixture's canonical records.
ENVELOPE_DEFAULTS: dict[str, str] = {
    "SELECTION": "FALSE",
    "LAYER": "TOP",
    "LOCKED": "FALSE",
    "POLYGONOUTLINE": "FALSE",
    "USERROUTED": "TRUE",
    "KEEPOUT": "FALSE",
    "UNIONINDEX": "0",
    "NETSCOPE": "AnyNet",
    "LAYERKIND": "SameLayer",
    "PRIORITY": "1",
    "COMMENT": " ",
    "DEFINEDBYLOGICALDOCUMENT": "FALSE",
}


def field_order(kind: str) -> tuple[str, ...]:
    """Full ordered field list (envelope + constraints) for a supported kind.

    Raises KeyError for unsupported kinds -- callers must check SUPPORTED_KINDS
    or handle the error rather than emit a guessed record.
    """

    return ENVELOPE_FIELDS + CONSTRAINT_FIELDS[kind]
