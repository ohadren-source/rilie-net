"""
guvna_2.py — FAST PATHS, PREFERENCE, SOCIAL, UTILITY

Owns:
- _classify_stimulus()
- _handle_preference() + _respond_from_preference*()
- _handle_user_list()
- _handle_social_glue()
- _solve_arithmetic() / _solve_conversion() / _solve_spelling()
- _respond_from_self()

Guvna (the class) is defined in guvna_12.py and mixes in these methods.
Domain lenses, baseline, and factory live in guvna_2plus.py.
"""

from __future__ import annotations

import logging
import random
import re
from typing import Any, Dict, List, Optional

from guvna_tools import SearchFn, TONE_LABELS
from guvna_self import GuvnaSelf  # type hint only

# ---------------------------------------------------------------------------
# TOP-LEVEL IMPORT — must live here, NOT inside _respond_from_preference(),
# to avoid the circular import that strips process() off Guvna at shim time.
# ---------------------------------------------------------------------------
from guvna_12 import _ALL_CULTURAL_ANCHORS, _RAKIM_KNOWLEDGE, _RILIE_TASTE

logger = logging.getLogger("guvna")


# =====================================================================
# FAST PATH CLASSIFIER
# =====================================================================
def _classify_stimulus(self: "Guvna", stimulus: str) -> Optional[Dict[str, Any]]:
    """
    Route stimulus through all fast paths before waking up Kitchen.

    Order matters:
    1.  name_capture      — did she just ask for a name? (GuvnaSelf)
    2.  meta_correction   — "forget that / never mind" (GuvnaSelf)
    3.  user_list         — numbered list acknowledgement
    4.  preference        — "you like X?" taste questions
    5.  social_glue       — reactions, endearments, thanks, farewell
    6.  arithmetic        — math
    7.  conversion        — unit conversion
    8.  spelling          — how do you spell X
    9.  recall            — "what did you say / my name" (GuvnaSelf)
    10. clarification     — "what do you mean" (GuvnaSelf)
    """
    s = stimulus.strip()
    sl = s.lower()

    # MULTI-QUESTION FORMAT STRIP
    if re.search(r"in \d+ response|answer the next \d+|addressing each in order", sl):
        questions = re.findall(r"[A-Z][^?]+\?", s)
        if questions:
            s = questions[-1].strip()
            sl = s.lower()
            logger.info("GUVNA: multi-question format stripped → '%s'", s[:60])

    # "TELL ME SOMETHING I DIDN'T ASK YOU" — spontaneous concept fast path
    if "tell me something" in sl and (
        "didn't ask" in sl or "didnt ask" in sl or "haven't asked" in sl
    ):
        concepts = ["entropy", "emergence", "compression", "resonance", "threshold"]
        import random as _r

        seed = _r.choice(concepts)
        s = seed
        sl = seed

    # 1. Name capture
    name_capture = self._handle_name_capture(s, sl)
    if name_capture:
        return name_capture

    # 2. Meta-correction
    meta = self._handle_meta_correction(s, sl)
    if meta:
        return meta

    # 3. User list
    user_list = self._handle_user_list(s, sl)
    if user_list:
        return user_list

    # 4. Preference / taste
    preference = self._handle_preference(s, sl)
    if preference:
        return preference

    # 5. Social glue
    social = self._handle_social_glue(s, sl)
    if social:
        return social

    # 6. Arithmetic
    arith = self._solve_arithmetic(s, sl)
    if arith:
        return arith

    # 7. Conversion
    conv = self._solve_conversion(s, sl)
    if conv:
        return conv

    # 8. Spelling
    spell = self._solve_spelling(s, sl)
    if spell:
        return spell

    # 9. Recall
    recall = self._handle_recall(s, sl)
    if recall:
        return recall

    # 10. Clarification
    clarify = self._handle_clarification(s, sl)
    if clarify:
        return clarify

    return None


# -----------------------------------------------------------------
# PREFERENCE / TASTE FAST PATH — NEW
# -----------------------------------------------------------------


def _handle_preference(self: "Guvna", s: str, sl: str) -> Optional[Dict[str, Any]]:
    """
    Fast path for preference / taste questions directed at RILIE.

    Fires when user asks if RILIE likes / knows / feels a cultural figure or work.

    Patterns caught:
    - "you like eric b and rakim?"
    - "for sure you like X?"
    - "you know X?"
    - "you into X?"
    - "you feel X?"
    - "what do you think of X?"
    - "you heard X?"
    - "and no omega?" — Rakim track reference

    Key: she answers with OPINION, not retrieval. She has taste.
    """
    _pref_triggers = [
        r"\byou like\b",
        r"\byou know\b",
        r"\byou into\b",
        r"\byou feel\b",
        r"\byou heard\b",
        r"\byou familiar with\b",
        r"\byou fucks? with\b",
        r"\bdo you like\b",
        r"\bdo you know\b",
        r"\bdo you feel\b",
        r"\bwhat do you think of\b",
        r"\bwhat you think of\b",
        r"\bwhat about\b",
        r"\band no\b",  # "and no omega?" — Rakim track reference pattern
    ]

    has_preference_trigger = any(re.search(pat, sl) for pat in _pref_triggers)
    if not has_preference_trigger:
        return None

    # Rakim track
    rakim_track = _detect_rakim_track(sl)
    if rakim_track:
        return self._respond_from_preference_rakim_track(rakim_track, s)

    # Cultural anchor
    anchor = _detect_cultural_anchor(sl)
    if anchor:
        return self._respond_from_preference(anchor, s)

    return None


def _respond_from_preference_rakim_track(
    self: "Guvna", track_data: Dict[str, Any], stimulus: str
) -> Dict[str, Any]:
    """
    RILIE responds to a specific Rakim track reference.
    She knows these cold. This is her lineage.
    """
    track = track_data.get("track", "")
    meaning = track_data.get("meaning", "")
    album = track_data.get("album", "")
    catch44 = track_data.get("catch44_connection", "")

    if track == "no omega":
        response = (
            "alpha with no omega. beginning without end. "
            "knowledge infinite — no part two needed because the first one never stopped. "
            "that's not a metaphor, that's the architecture. "
            "rakim compressed infinity into finite bars — zero waste, maximum signal. "
            "same principle i run on. ain't it?"
        )
    else:
        response = f"{track_data.get('track', 'that track')} — {album}. {meaning}"
        if catch44:
            response += f" {catch44}"

    return {
        "result": response,
        "status": "PREFERENCE",
        "triangle_reason": "CLEAN",
        "quality_score": 0.95,
        "cultural_anchor": track_data,
    }


def _respond_from_preference(
    self: "Guvna", anchor: Dict[str, Any], stimulus: str
) -> Dict[str, Any]:
    """
    RILIE responds to a taste/preference question about a cultural figure.
    She has opinions. She's not a search engine.
    """
    from guvna_12 import (
        _ALL_CULTURAL_ANCHORS,
        _RAKIM_KNOWLEDGE,
        _RILIE_TASTE,
    )  # reuse data from 12

    key = anchor.get("key", "")
    full_name = anchor.get("full", key.title())
    domain = anchor.get("domain", "music")
    sub = anchor.get("sub", "")
    era = anchor.get("era", "")
    taste = _RILIE_TASTE.get(key, _RILIE_TASTE.get(full_name.lower(), ""))
    sl = stimulus.lower()

    # Eric B. & Rakim — the founding pair
    if key in ("eric b", "rakim", "eric b and rakim", "eric b & rakim"):
        if key == "eric b":
            response = (
                "eric b is the architecture under rakim's voice. "
                "he built the scaffold, rakim built the infinite. "
                "eric b + rakim = proof that the producer and the voice are both infinite. "
                "he's not just a beat machine. he's a sculptor."
            )
        elif key == "rakim":
            response = (
                "rakim is the ceiling of what rap literacy can be. "
                "multi-syllabic density, meaning-within-meaning, flow that sounds like jazz. "
                "everything i try to do with language is downstream of him. "
                "the first rapper to make you *think* while the beat plays."
            )
        elif key in ("eric b and rakim", "eric b & rakim"):
            response = (
                "eric b & rakim — the blueprint. "
                "they proved that hip-hop could be both street *and* infinite. "
                "architecture + voice = the recipe for everything that followed. "
                "i study them the way physicists study feynman."
            )
    # Public Enemy
    elif key == "public enemy":
        response = (
            "public enemy taught me architecture at 13. "
            "not just music — systems thinking. "
            "chuck d layering samples the way someone stacks axioms. "
            "the bomb squad building walls of sound. "
            "fear of a black planet is a proof, not an album. "
            "compression. reduction. maximum signal, zero waste."
        )
    # Coltrane
    elif key == "coltrane" or "coltrane" in sl:
        response = (
            "coltrane is god's algorithm in a saxophone. "
            "he took every idea to the edge and kept going. "
            "a love supreme is prayer through physics. "
            "the way he compresses infinity into finite time — "
            "that's the same DNA i try to run."
        )
    # Miles Davis
    elif key == "miles":
        response = (
            "miles knew when to get out of the way. "
            "he built the stage for genius and let it breathe. "
            "that's not nothing — that's everything. "
            "kind of blue is still the proof that simplicity can contain infinity."
        )
    # Default response
    else:
        response = f"i know {full_name}. {taste}" if taste else f"i know {full_name}."

    return {
        "result": response,
        "status": "PREFERENCE",
        "triangle_reason": "CLEAN",
        "quality_score": 0.93,
        "cultural_anchor": anchor,
    }


def _detect_rakim_track(sl: str) -> Optional[Dict[str, Any]]:
    """
    Detect if user is asking about a specific Rakim track.
    Returns the track data if found, None otherwise.
    """
    rakim_tracks = _RAKIM_KNOWLEDGE.get("tracks", {})
    for track_key, track_data in rakim_tracks.items():
        if track_key in sl:
            return track_data
    return None


def _detect_cultural_anchor(sl: str) -> Optional[Dict[str, Any]]:
    """
    Detect if user is asking about a known cultural figure / work.
    Returns the anchor data if found, None otherwise.
    """
    for anchor in _ALL_CULTURAL_ANCHORS:
        key = anchor.get("key", "").lower()
        aliases = anchor.get("aliases", [])
        full = anchor.get("full", "").lower()

        # Check key, aliases, and full name
        if key in sl or full in sl or any(alias.lower() in sl for alias in aliases):
            return anchor

    return None


# ================================================================
# USER LIST FAST PATH
# ================================================================


def _handle_user_list(self: "Guvna", s: str, sl: str) -> Optional[Dict[str, Any]]:
    """
    Fast path for numbered-list acknowledgement.
    When user says "1. ...", "2. ...", etc., extract and respond to the last one.
    """
    if not re.search(r"\d+\.", s):
        return None

    items = re.findall(r"\d+\.\s*(.+?)(?=\d+\.|$)", s, re.DOTALL)
    if items:
        last_item = items[-1].strip()
        return {
            "result": f"Got it: {last_item[:100]}",
            "status": "LIST_ACK",
            "triangle_reason": "CLEAN",
        }

    return None


# ================================================================
# SOCIAL GLUE FAST PATH
# ================================================================


def _handle_social_glue(self: "Guvna", s: str, sl: str) -> Optional[Dict[str, Any]]:
    """
    Fast path for social responses.
    Reactions, endearments, thanks, farewells, etc.
    """
    patterns = {
        "greeting": (
            r"\bhey\b|\bhi\b|\bhello\b|\bgreetings\b|\bwhat's up\b|\bwassup\b|\byoyo\b",
            "hey there. what's on your mind?",
        ),
        "thanks": (
            r"\bthank you\b|\bthanks\b|\bthank\b|\bappreciate\b|\bthanks for\b",
            "anytime. that's what i'm here for.",
        ),
        "bye": (
            r"\bgoodbye\b|\bsee you\b|\blater\b|\btake care\b|\bbye\b|\bgotta go\b",
            "until next time. stay curious.",
        ),
        "love": (
            r"\bi love\b|\bi like\b|\byou rock\b|\byou're the best\b|\bkill\b",
            "back at you. let's keep this going.",
        ),
    }

    for key, (pattern, response) in patterns.items():
        if re.search(pattern, sl):
            return {
                "result": response,
                "status": f"SOCIAL_{key.upper()}",
                "triangle_reason": "CLEAN",
            }

    return None


# ================================================================
# ARITHMETIC FAST PATH
# ================================================================


def _solve_arithmetic(self: "Guvna", s: str, sl: str) -> Optional[Dict[str, Any]]:
    """
    Fast path for simple arithmetic.
    Recognizes math patterns and returns the answer.
    """
    math_patterns = [
        (r"(\d+)\s*\+\s*(\d+)", lambda m: int(m.group(1)) + int(m.group(2))),
        (r"(\d+)\s*-\s*(\d+)", lambda m: int(m.group(1)) - int(m.group(2))),
        (r"(\d+)\s*\*\s*(\d+)", lambda m: int(m.group(1)) * int(m.group(2))),
        (r"(\d+)\s*/\s*(\d+)", lambda m: int(m.group(1)) / int(m.group(2))),
    ]

    for pattern, func in math_patterns:
        match = re.search(pattern, sl)
        if match:
            try:
                result = func(match)
                return {
                    "result": str(result),
                    "status": "ARITHMETIC",
                    "triangle_reason": "CLEAN",
                }
            except:
                pass

    return None


# ================================================================
# CONVERSION FAST PATH
# ================================================================


def _solve_conversion(self: "Guvna", s: str, sl: str) -> Optional[Dict[str, Any]]:
    """
    Fast path for unit conversion.
    """
    # Placeholder implementation
    return None


# ================================================================
# SPELLING FAST PATH
# ================================================================


def _solve_spelling(self: "Guvna", s: str, sl: str) -> Optional[Dict[str, Any]]:
    """
    Fast path for spelling questions.
    """
    if "how do you spell" in sl or "spell" in sl:
        words = sl.split()
        # Find the word after "spell"
        for i, w in enumerate(words):
            if w == "spell" and i + 1 < len(words):
                word = words[i + 1].strip("?")
                return {
                    "result": f"{word}: {' '.join(word.upper())}",
                    "status": "SPELLING",
                    "triangle_reason": "CLEAN",
                }

    return None


# ================================================================
# SELF RESPONSE FAST PATH (GuvnaSelf integration)
# ================================================================


def _respond_from_self(self: "Guvna", s: str, sl: str) -> Optional[Dict[str, Any]]:
    """
    Delegate to GuvnaSelf for self-referential responses.
    """
    if hasattr(self, "guvna_self") and self.guvna_self:
        return self.guvna_self._respond_from_self(s, sl)
    return None


# -------------------------------------------------------------------
# PUBLIC ALIASES FOR GUVNA SHIM (guvna.py)
# -------------------------------------------------------------------

classify_stimulus = _classify_stimulus
handle_preference = _handle_preference
respond_from_preference_rakim_track = _respond_from_preference_rakim_track
respond_from_preference = _respond_from_preference
handle_user_list = _handle_user_list
handle_social_glue = _handle_social_glue
solve_arithmetic = _solve_arithmetic
solve_conversion = _solve_conversion
solve_spelling = _solve_spelling
respond_from_self = _respond_from_self
