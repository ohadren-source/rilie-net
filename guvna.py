"""
guvna.py — Shim / Brain Stitcher

Act 5 – The Governor lives in two files:

- guvna_12.py  → core class Guvna(GuvnaSelf): __init__, process, metadata, doctrine
- guvna_22.py  → extension methods: fast paths, preference, domain lenses, baseline

This shim:

- Exposes Guvna and LibraryIndex to the rest of the system.
- Binds all extension functions from guvna_22.py onto the Guvna class.
- Keeps api.py stable: `from guvna import Guvna, LibraryIndex` still works.
"""

from __future__ import annotations

from guvna_12 import Guvna, LibraryIndex
from guvna_22 import (
    _classify_stimulus,
    _handle_preference,
    _respond_from_preference_rakim_track,
    _respond_from_preference,
    _handle_user_list,
    _handle_social_glue,
    _solve_arithmetic,
    _solve_conversion,
    _solve_spelling,
    _respond_from_self,
    _apply_domain_lenses,
    _get_baseline,
)

# ---------------------------------------------------------------------------
# Bind extension methods onto the Guvna class
# ---------------------------------------------------------------------------

Guvna._classify_stimulus = _classify_stimulus          # type: ignore[attr-defined]
Guvna._handle_preference = _handle_preference          # type: ignore[attr-defined]
Guvna._respond_from_preference_rakim_track = _respond_from_preference_rakim_track  # type: ignore[attr-defined]
Guvna._respond_from_preference = _respond_from_preference  # type: ignore[attr-defined]
Guvna._handle_user_list = _handle_user_list            # type: ignore[attr-defined]
Guvna._handle_social_glue = _handle_social_glue        # type: ignore[attr-defined]
Guvna._solve_arithmetic = _solve_arithmetic            # type: ignore[attr-defined]
Guvna._solve_conversion = _solve_conversion            # type: ignore[attr-defined]
Guvna._solve_spelling = _solve_spelling                # type: ignore[attr-defined]
Guvna._respond_from_self = _respond_from_self          # type: ignore[attr-defined]
Guvna._apply_domain_lenses = _apply_domain_lenses      # type: ignore[attr-defined]
Guvna._get_baseline = _get_baseline                    # type: ignore[attr-defined]

__all__ = ["Guvna", "LibraryIndex"]
