"""Parse Altium ``.RUL`` files into ordered field records.

Ground truth (verified against tests/fixtures/rul/pcbway_base.RUL, an
Altium-exported file):

* Encoding is ISO-8859-1 (latin-1). High bytes appear (e.g. the 0xB6 pilcrow).
* One design rule per line. Lines are separated by ``\n`` only (no ``\r``).
* Within a line, fields are ``KEY=VALUE`` joined by ``|``. CRUCIALLY the FIRST
  field has NO leading ``|`` (a line begins ``SELECTION=FALSE|LAYER=TOP|...``).
  This is exactly why ``altiumtools.core.parse._FIELD_RE`` -- which requires a leading
  ``|`` before every key -- must NOT be reused here: it would silently drop the
  first field of every rule.
* The last field's VALUE carries a trailing record terminator: the pilcrow byte
  ``0xB6`` (``¶``). We strip it on parse and re-append it on emit so the byte
  layout round-trips exactly.

Field order is preserved (dict insertion order) because Altium writes a stable
ordering and the differential fidelity test compares key sequences, not just
key sets.
"""

from __future__ import annotations

# Altium terminates each .RUL record with this byte before the newline.
RECORD_TERMINATOR = "\xb6"  # the pilcrow ¶ (0xB6 in latin-1)

_ENCODING = "latin-1"


def _split_record(line: str) -> dict[str, str]:
    """Split one ``.RUL`` line into an ordered {KEY: VALUE} mapping.

    The trailing record terminator (``¶``), if present on the final value, is
    stripped -- it is structural, not part of the data.
    """

    record: dict[str, str] = {}
    parts = line.split("|")
    for part in parts:
        if "=" not in part:
            # Defensive: Altium never emits a pipe-section without '='; if it
            # ever does we keep it visible rather than silently dropping data.
            if part:
                record[part] = ""
            continue
        key, value = part.split("=", 1)
        record[key] = value
    # Strip the structural terminator off whichever value carries it.
    if record:
        last_key = next(reversed(record))
        if record[last_key].endswith(RECORD_TERMINATOR):
            record[last_key] = record[last_key][: -len(RECORD_TERMINATOR)]
    return record


def parse_rul(data: bytes | str) -> list[dict[str, str]]:
    """Parse ``.RUL`` bytes (or text) into a list of ordered field records.

    Blank lines are skipped. Field order within each record is preserved.
    """

    text = data.decode(_ENCODING) if isinstance(data, bytes) else data
    records: list[dict[str, str]] = []
    for line in text.split("\n"):
        if not line.strip():
            continue
        records.append(_split_record(line))
    return records
