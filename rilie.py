"""
rilie.py — Shim / Brain Stitcher

Act 4 – The Restaurant lives in two files:

- rilie_foundation.py → all helper functions, utilities, database logic:
    - extract_tangents, _measurestick, _store_measurestick_signal
    - _fix_mojibake, hash_stimulus, _scrub_repetition
    - _extract_original_question, _search_banks_if_available
    - _maybe_lookup_unknown_reference
    - ConversationState, PersonModel, SearchFn types

- rilie_restaurant.py → Class RILIE with all methods:
    - __init__, process, _check_dejavu, _classify_dejavu_context
    - _dejavu_one_swing, absorb_frequency_track, reset_conversation
    - get_person_summary, main

This shim:

- Exposes RILIE to the rest of the system.
- Keeps api.py stable: `from rilie import RILIE` still works.
- Maintains clean separation: foundation (helpers) vs restaurant (orchestration).
"""

from __future__ import annotations

from rilie_foundation import (
    extract_tangents,
    _fix_mojibake,
    hash_stimulus,
    _scrub_repetition,
    _extract_original_question,
    _search_banks_if_available,
    _maybe_lookup_unknown_reference,
    _measurestick,
    _store_measurestick_signal,
    ConversationState,
    PersonModel,
    SearchFn,
)

from rilie_restaurant import RILIE

__all__ = [
    "RILIE",
    "extract_tangents",
    "_fix_mojibake",
    "hash_stimulus",
    "_scrub_repetition",
    "_extract_original_question",
    "_search_banks_if_available",
    "_maybe_lookup_unknown_reference",
    "_measurestick",
    "_store_measurestick_signal",
    "ConversationState",
    "PersonModel",
    "SearchFn",
]
