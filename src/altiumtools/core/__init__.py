"""core: the shared, format-agnostic foundation every sub-project builds on.

This sub-package holds the two layers that have NO knowledge of any specific
analysis or generation feature:

  - ``model``  — normalized, olefile-free design dataclasses (Design, Component,
                 Net, DesignRule, SourceRef). The boundary type that every other
                 sub-project (checks/, rules/) speaks.
  - ``parse``  — Altium OLE2 binary -> ``model`` (inspect_ole, parse_schdoc,
                 load, merge). Depends on ``model`` only.

Sub-projects depend on ``core``; ``core`` depends on nothing internal. Keeping it
isolated is what lets the review engine and the rule generator evolve (and one
day ship as independent packages) without entangling each other.
"""

from __future__ import annotations
