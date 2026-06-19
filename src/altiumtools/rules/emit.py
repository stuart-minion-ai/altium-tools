"""Render design rules back into Altium ``.RUL`` bytes.

Two layers:

* ``render_record`` is the low-level, fidelity-critical primitive: given a kind
  and a COMPLETE value mapping, it writes the fields in the verified order with
  the structural ``¶`` terminator. It refuses to emit if the value keys do not
  exactly match the verified template -- a missing or extra field means we would
  produce a record Altium might reject, so we raise instead of guessing.
* ``emit_rul`` is the product-level entry point: it turns a ``RulePack`` of
  neutral ``DesignRule`` objects into importable ``.RUL`` bytes, filling the
  common envelope from defaults and deriving a stable ``UNIQUEID`` per rule.
"""

from __future__ import annotations

from ..core.model import DesignRule
from .fields import ENVELOPE_DEFAULTS, SUPPORTED_KINDS, field_order
from .model import RulePack
from .parse import RECORD_TERMINATOR

_ENCODING = "latin-1"
_UID_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
_UID_LEN = 8


class UnsupportedRuleKind(ValueError):
    """Raised when asked to emit a rule kind we have not verified."""


class IncompleteRecord(ValueError):
    """Raised when a record's fields don't match the verified template."""


def stable_uniqueid(*parts: str) -> str:
    """Deterministic 8-char A-Z id, matching Altium's UNIQUEID shape.

    Deterministic so regenerating the same pack yields byte-identical output
    (clean diffs, reproducible builds). Not required to be globally unique --
    Altium reassigns ids on import; this only needs to be stable and well-formed.
    """

    h = 1469598103934665603  # FNV-1a 64-bit offset basis
    for p in parts:
        for b in p.encode(_ENCODING, "replace"):
            h ^= b
            h = (h * 1099511628211) & 0xFFFFFFFFFFFFFFFF
    out = []
    for _ in range(_UID_LEN):
        out.append(_UID_ALPHABET[h % 26])
        h //= 26
    return "".join(out)


def render_record(kind: str, values: dict[str, str]) -> str:
    """Render one rule line (including the ``¶`` terminator, no newline).

    ``values`` must contain exactly the keys of ``field_order(kind)``. This
    strictness is the fidelity guarantee: we never silently drop or invent a
    field.
    """

    if kind not in SUPPORTED_KINDS:
        raise UnsupportedRuleKind(kind)
    order = field_order(kind)
    expected = set(order)
    got = set(values)
    if got != expected:
        missing = expected - got
        extra = got - expected
        raise IncompleteRecord(
            f"{kind}: missing={sorted(missing)} extra={sorted(extra)}"
        )
    parts = [f"{key}={values[key]}" for key in order]
    return "|".join(parts) + RECORD_TERMINATOR


def _values_for_rule(rule: DesignRule) -> dict[str, str]:
    """Build the full ordered value mapping for a generated DesignRule."""

    if rule.kind not in SUPPORTED_KINDS:
        raise UnsupportedRuleKind(rule.kind)

    scope2 = rule.constraints.get("SCOPE2EXPRESSION", rule.scope)
    derived: dict[str, str] = {
        "RULEKIND": rule.kind,
        "SCOPE1EXPRESSION": rule.scope,
        "SCOPE2EXPRESSION": scope2,
        "NAME": rule.name,
        "ENABLED": "TRUE" if rule.enabled else "FALSE",
        "UNIQUEID": stable_uniqueid(rule.kind, rule.name, rule.scope),
    }
    # Layered: defaults < derived < explicit constraints (caller wins).
    merged = {**ENVELOPE_DEFAULTS, **derived, **rule.constraints}
    order = field_order(rule.kind)
    # Keep only template fields, in template order. Any constraint key that is
    # NOT part of the template is rejected by render_record below as 'extra',
    # surfacing typos instead of silently dropping them.
    extra = set(rule.constraints) - set(order)
    if extra:
        raise IncompleteRecord(
            f"{rule.kind}: unknown constraint field(s) {sorted(extra)}"
        )
    missing = set(order) - set(merged)
    if missing:
        raise IncompleteRecord(
            f"{rule.kind}: rule '{rule.name}' is missing required field(s) "
            f"{sorted(missing)}"
        )
    return {key: merged[key] for key in order}


def emit_rul(pack: RulePack) -> bytes:
    """Serialize a RulePack to importable ``.RUL`` bytes (latin-1).

    Records are newline-separated; the file ends with a trailing newline, as
    Altium-exported files do.
    """

    lines = []
    for rule in pack.rules:
        values = _values_for_rule(rule)
        lines.append(render_record(rule.kind, values))
    text = "\n".join(lines) + "\n"
    return text.encode(_ENCODING)
