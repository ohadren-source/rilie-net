"""

rilie_innercore.py — Shim / Kitchen Stitcher (v4.3.0)

The real kitchen logic lives in two files:

- rilie_innercore_12.py -> core primitives:
    - QuestionType, compute_trite_score, anti_beige_check
    - construct_response, construct_blend
    - clarify_or_freestyle, clarification counter
    - Interpretation dataclass, scoring weights, etc.

- rilie_innercore_22.py -> extended pipeline:
    - detect_domains, excavate_domains
    - generate_9_interpretations
    - _apply_limo, run_pass_pipeline

This shim:
- Re-exports the public kitchen surface the rest of RILIE expects.
- Keeps callers importing from `rilie_innercore` instead of the numbered files.

"""

from __future__ import annotations
from typing import List, Dict, Optional

# Core primitives
from rilie_innercore_12 import (
    QuestionType,
    compute_trite_score,
    set_trite_score,
    set_curiosity_bonus,
    anti_beige_check,
    construct_response,
    construct_blend,
    extract_curiosity_context,
    strip_curiosity_context,
    less_is_more_or_less,
    Interpretation,
    logger,
    CHOMSKY_AVAILABLE,
    LIMO_AVAILABLE,
    # v4.3.0 — Step 10: clarification / freestyle
    clarify_or_freestyle,
    get_clarification_counter,
    reset_clarification_counter,
)

# Extended logic / pipeline
from rilie_innercore_22 import (
    detect_domains,
    excavate_domains,
    generate_9_interpretations,
    run_pass_pipeline,
)

__all__ = [
    # types
    "QuestionType",
    "Interpretation",
    # curiosity / context
    "extract_curiosity_context",
    "strip_curiosity_context",
    # trite / curiosity knobs
    "compute_trite_score",
    "set_trite_score",
    "set_curiosity_bonus",
    # scoring / construction
    "anti_beige_check",
    "construct_response",
    "construct_blend",
    "less_is_more_or_less",
    # clarification / freestyle (v4.3.0)
    "clarify_or_freestyle",
    "get_clarification_counter",
    "reset_clarification_counter",
    # domains / pipeline
    "detect_domains",
    "excavate_domains",
    "generate_9_interpretations",
    "run_pass_pipeline",
    # flags / logger
    "CHOMSKY_AVAILABLE",
    "LIMO_AVAILABLE",
    "logger",
]
