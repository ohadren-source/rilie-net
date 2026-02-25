"""

guvna.py

Shim / Brain Stitcher – Act 5 The Governor lives in multiple files:

- guvna_12.py     → core class Guvna (init, process, metadata, doctrine)
- guvna_2.py      → fast paths, preference, social, utility
- guvna_2plus.py  → domain lenses, baseline, factory
- guvna_river.py  → The River (early lookup telemetry, no cooking)

This shim:

- Exposes Guvna and LibraryIndex to the rest of the system.
- Binds all extension functions from guvna_2.py and guvna_2plus.py onto the Guvna class.
- Keeps api.py stable: `from guvna import Guvna, LibraryIndex` still works.

"""

from __future__ import annotations

from typing import Any, Dict, List

from guvna_12 import Guvna, LibraryIndex  # core Governor

from guvna_2 import (
    classify_stimulus,
    handle_preference,
    respond_from_preference_rakim_track,
    respond_from_preference,
    handle_user_list,
    handle_social_glue,
    solve_arithmetic,
    solve_conversion,
    solve_spelling,
    respond_from_self,
)

from guvna_2plus import (
    apply_domain_lenses,
    get_baseline,
)

from guvna_river import guvna_river  # The River – lookup only, no Kitchen

# ---------------------------------------------------------------------------
# Stitch guvna_2 fast paths onto Guvna
# ---------------------------------------------------------------------------

Guvna._classify_stimulus = classify_stimulus  # type: ignore[attr-defined]

Guvna._handle_preference = handle_preference  # type: ignore[attr-defined]

Guvna._respond_from_preference_rakim_track = (
    respond_from_preference_rakim_track  # type: ignore[attr-defined]
)

Guvna._respond_from_preference = respond_from_preference  # type: ignore[attr-defined]

Guvna._handle_user_list = handle_user_list  # type: ignore[attr-defined]

Guvna._handle_social_glue = handle_social_glue  # type: ignore[attr-defined]

Guvna._solve_arithmetic = solve_arithmetic  # type: ignore[attr-defined]

Guvna._solve_conversion = solve_conversion  # type: ignore[attr-defined]

Guvna._solve_spelling = solve_spelling  # type: ignore[attr-defined]

Guvna._respond_from_self = respond_from_self  # type: ignore[attr-defined]

# ---------------------------------------------------------------------------
# Stitch guvna_2plus lenses + baseline onto Guvna
# ---------------------------------------------------------------------------

Guvna._apply_domain_lenses = apply_domain_lenses  # type: ignore[attr-defined]

Guvna._get_baseline = get_baseline  # type: ignore[attr-defined]

# ---------------------------------------------------------------------------
# River hook – bind as staticmethod so no extra `self` is passed
# ---------------------------------------------------------------------------

# guvna_river is defined as:
# def guvna_river(*, stimulus, meaning, get_baseline, apply_domain_lenses,
#                 compute_domain_and_factsfirst, debug_mode=False) -> Optional[Dict[str, Any]]

# In guvna_12.Guvna.process we call:
# self.guvna_river(stimulus=..., meaning=..., get_baseline=self._get_baseline, ...)

# Binding as staticmethod keeps that keyword-only signature intact.
Guvna.guvna_river = staticmethod(guvna_river)  # type: ignore[attr-defined]

# ---------------------------------------------------------------------------
# BOOT ASSERTION — catch missing bindings before first request hits
# If anything above failed silently, this explodes at deploy time not at
# turn 2 of a conversation. Railway build log will show exactly what's missing.
# ---------------------------------------------------------------------------

_required = [
    "process",
    "_classify_stimulus",
    "_handle_preference",
    "_respond_from_preference_rakim_track",
    "_respond_from_preference",
    "_handle_user_list",
    "_handle_social_glue",
    "_solve_arithmetic",
    "_solve_conversion",
    "_solve_spelling",
    "_respond_from_self",
    "_apply_domain_lenses",
    "_get_baseline",
    "guvna_river",
]

_missing = [m for m in _required if not hasattr(Guvna, m)]

if _missing:
    raise RuntimeError(
        f"GUVNA SHIM INCOMPLETE — kitchen closed before she opened.\n"
        f"Missing bindings: {_missing}\n"
        f"Check guvna_12.py, guvna_2.py, guvna_2plus.py, and guvna_river.py."
    )

__all__ = ["Guvna", "LibraryIndex"]
