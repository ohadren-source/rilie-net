"""

guvna.py

Shim / Brain Stitcher – Act 5 The Governor lives in multiple files:

- guvna_1.py       → Kernel + initialization (CATCH 44 blueprint loading)
- guvna_1plus.py   → Execution (process method + SOIOS emergence check)
- guvna_2.py       → fast paths, preference, social, utility
- guvna_2plus.py   → domain lenses, baseline, factory
- guvna_river.py   → The River (early lookup telemetry, no cooking)

This shim:

- Exposes Guvna and LibraryIndex to the rest of the system.
- Loads blueprint and axioms on boot.
- Binds all extension functions from guvna_2.py, guvna_2plus.py, and guvna_1plus.py onto the Guvna class.
- Wires SOIOS emergence check into process().
- Keeps api.py stable: `from guvna import Guvna, LibraryIndex` still works.

"""

from __future__ import annotations

from typing import Any, Dict, List

from guvna_1 import Guvna, LibraryIndex  # core Governor (kernel + init)
from guvna_1plus import process, _check_emergence  # execution + emergence check

from guvna_2 import (
    classify_stimulus,
    extract_ingredients_immediate,
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
# Stitch guvna_1plus (process + emergence) onto Guvna
# ---------------------------------------------------------------------------

Guvna.process = process  # type: ignore[attr-defined]
Guvna._check_emergence = _check_emergence  # type: ignore[attr-defined]

# ---------------------------------------------------------------------------
# Stitch guvna_2 fast paths onto Guvna
# ---------------------------------------------------------------------------

Guvna._extract_ingredients_immediate = extract_ingredients_immediate  # type: ignore[attr-defined]

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

Guvna.guvna_river = staticmethod(guvna_river)  # type: ignore[attr-defined]

# ---------------------------------------------------------------------------
# BOOT ASSERTION — catch missing bindings before first request hits
# ---------------------------------------------------------------------------

_required = [
    "process",
    "_check_emergence",
    "_extract_ingredients_immediate",
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
        f"Check guvna_1.py, guvna_1plus.py, guvna_2.py, guvna_2plus.py, and guvna_river.py."
    )

__all__ = ["Guvna", "LibraryIndex"]
