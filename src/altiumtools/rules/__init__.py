"""Altium design-rule (.RUL) generation.

WHY THIS IS A SEPARATE PACKAGE FROM ``altiumtools.core.parse``:
``parse.py`` decodes Altium's OLE2 *binary* documents (.SchDoc/.PcbDoc). A
``.RUL`` file is a different animal entirely: it is plain ISO-8859 text, one
design rule per line, ``KEY=VALUE`` pairs joined by ``|``, each record
terminated by the pilcrow byte ``0xB6`` (rendered ``¶``) then ``\n``. Because it
never touches OLE, it lives here and reuses none of the OLE machinery.

HONESTY GATE (read before adding a rule kind):
We only emit rule kinds whose *complete field envelope* we have captured from a
real, Altium-exported ``.RUL`` file (see ``tests/fixtures/rul/``). Each supported
kind has a round-trip test proving parse->emit reproduces the original record's
field envelope byte-for-byte (only values/UNIQUEID differ). A kind we have not
verified is NOT emitted with guessed fields -- it is simply absent. A generator
that emits a plausible-but-wrong rule is worse than one that omits it.
"""

from __future__ import annotations

from .emit import emit_rul
from .model import RulePack
from .parse import RECORD_TERMINATOR, parse_rul

__all__ = ["RulePack", "emit_rul", "parse_rul", "RECORD_TERMINATOR"]
