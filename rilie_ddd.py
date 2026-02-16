"""
rilie_ddd.py — THE HOSTESS (TASTE BYPASS)
==========================================

DISCOURSE DICTATES DISCLOSURE

TASTE is temporarily bypassed — Kitchen output passes through at all levels.
When ready to restore TASTE, re-enable template selection in shape_for_disclosure().

The templates, ConversationState, and DisclosureLevel enum remain intact
so nothing downstream breaks and TASTE can be reconnected cleanly.
"""

import re
import random
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class DisclosureLevel(Enum):
    TASTE = "taste"   # Turn 1-2: invitation only (currently bypassed)
    OPEN  = "open"    # Turn 3+: real response
    FULL  = "full"


# ============================================================================
# SIMILARITY UTIL — used by deja vu detection
# ============================================================================

def _normalize_words(text: str) -> set:
    """Strip punctuation, lowercase, return word set."""
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", "", text.lower())
    return set(cleaned.split())


def _stimulus_similarity(a: str, b: str) -> float:
    """Jaccard similarity between two stimuli, 0.0-1.0."""
    wa = _normalize_words(a)
    wb = _normalize_words(b)
    if not wa or not wb:
        return 0.0
    union = wa | wb
    if not union:
        return 0.0
    return len(wa & wb) / len(union)


# ============================================================================
# CONVERSATION STATE
# ============================================================================

@dataclass
class ConversationState:
    """Track where we are in the sequence."""
    exchange_count: int = 0
    stimuli_history: List[str] = field(default_factory=list)
    response_history: List[str] = field(default_factory=list)

    # Deja vu tracking
    dejavu_count: int = 0
    dejavu_cluster_stimulus: str = ""
    dejavu_last_envelopes: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def disclosure_level(self) -> DisclosureLevel:
        """Simple sequence: turns 1-3 = TASTE, turn 4+ = OPEN.

        NOTE: exchange_count is checked BEFORE record_exchange increments it,
        so count 0 = first turn, count 1 = second turn, count 2 = third turn,
        count 3+ = OPEN.
        """
        if self.exchange_count < 3:
            return DisclosureLevel.TASTE
        return DisclosureLevel.OPEN

    @property
    def taste_turn(self) -> int:
        """Which TASTE turn are we on? (0, 1, 2, or done)"""
        if self.exchange_count == 0:
            return 0
        elif self.exchange_count == 1:
            return 1
        elif self.exchange_count == 2:
            return 2
        return 3

    def record_exchange(self, stimulus: str, response: str) -> None:
        """Record and move to next."""
        self.stimuli_history.append(stimulus)
        self.response_history.append(response)
        self.exchange_count += 1

    def record_dejavu_exchange(self, stimulus: str, response: str,
                                envelope: Optional[Dict[str, Any]] = None) -> None:
        """Record an exchange handled by the deja vu path."""
        self.stimuli_history.append(stimulus)
        self.response_history.append(response)
        self.exchange_count += 1
        if envelope:
            self.dejavu_last_envelopes.append(envelope)

    # --- Deja vu detection ---

    def check_dejavu(self, stimulus: str, threshold: float = 0.55) -> int:
        """
        Check if this stimulus is similar to recent stimuli.
        Returns deja vu count (0 = fresh, 1 = first repeat, 2+).
        """
        s = stimulus.strip()
        if not s:
            return 0

        # Check against current cluster first
        if self.dejavu_cluster_stimulus:
            sim = _stimulus_similarity(s, self.dejavu_cluster_stimulus)
            if sim >= threshold:
                self.dejavu_count += 1
                return self.dejavu_count

        # Check against recent stimuli (last 5)
        recent = self.stimuli_history[-5:] if self.stimuli_history else []
        for prev in reversed(recent):
            sim = _stimulus_similarity(s, prev)
            if sim >= threshold:
                self.dejavu_cluster_stimulus = prev
                self.dejavu_count = 1
                self.dejavu_last_envelopes = []
                return self.dejavu_count

        # Fresh stimulus — reset
        self.dejavu_count = 0
        self.dejavu_cluster_stimulus = ""
        self.dejavu_last_envelopes = []
        return 0

    def get_dejavu_self_diagnosis(self) -> str:
        """Examine her own previous envelopes to diagnose what she got wrong."""
        if not self.dejavu_last_envelopes:
            return "I don't have enough context from my last attempts to diagnose what I missed."

        gaps = []
        for env in self.dejavu_last_envelopes:
            status = str(env.get("status", "")).upper()
            baseline_as_result = env.get("baseline_used_as_result", False)
            quality = float(env.get("quality_score", 0) or 0)
            priorities = int(env.get("priorities_met", 0) or 0)

            if status == "MISE_EN_PLACE":
                gaps.append("I fell back to my safety net instead of actually thinking")
            if baseline_as_result:
                gaps.append("I leaned on a web snippet instead of giving you my own take")
            if quality < 0.3:
                gaps.append("My confidence in what I said was low")
            if priorities < 2:
                gaps.append("I wasn't hitting enough of what makes a response worth giving")

        unique_gaps = list(dict.fromkeys(gaps))
        if not unique_gaps:
            return "Looking back, I'm not sure my previous answer landed the way I wanted it to."
        if len(unique_gaps) == 1:
            return f"Looking back at what I said before — {unique_gaps[0].lower()}. Let me try differently."
        else:
            joined = "; ".join(g.lower() for g in unique_gaps[:3])
            return f"Looking back at what I said — {joined}. I want to do better here."


# ============================================================================
# DEJA VU RESPONSE BUILDER
# ============================================================================

def build_dejavu_response(stimulus: str, conversation: ConversationState,
                           dejavu_count: int) -> str:
    """
    Build the appropriate deja vu response based on count.
    STRIPPED: No templates. Just honest responses.
    """
    if dejavu_count == 1:
        return "Sounds familiar — I think I can do better. What specifically are you hoping I can sharpen?"

    elif dejavu_count == 2:
        diagnosis = conversation.get_dejavu_self_diagnosis()
        return f"{diagnosis} What angle would help you most?"

    else:
        return "I've tried a few angles here and I'm not landing it. I don't have enough depth on this yet to do it justice, but I want to. I'll be better next time."


# ============================================================================
# TASTE TEMPLATES — REMOVED (TASTE is bypassed, these aren't used)
# ============================================================================


# ============================================================================
# PUBLIC API: Build response by exchange count
# ============================================================================

def shape_for_disclosure(
    raw_result: str,
    conversation: ConversationState,
) -> str:
    """
    TASTE BYPASSED — Kitchen output passes through at ALL disclosure levels.

    Previously, TASTE turns (1-3) would intercept Kitchen output and replace
    it with Hostess templates. That interception is now disabled so the
    Kitchen's actual domain-generated responses reach the user from turn 1.

    When ready to restore TASTE behavior, uncomment the TASTE block below.
    """
    # ---------------------------------------------------------------
    # TASTE BYPASS — all turns pass through Kitchen output directly
    # ---------------------------------------------------------------
    return raw_result

    # ---------------------------------------------------------------
    # ORIGINAL TASTE LOGIC — uncomment to re-enable
    # ---------------------------------------------------------------
    # level = conversation.disclosure_level
    #
    # if level is not DisclosureLevel.TASTE:
    #     return raw_result
    #
    # taste_turn = conversation.taste_turn
    # last_stimulus = (
    #     conversation.stimuli_history[-1]
    #     if conversation.stimuli_history
    #     else raw_result
    # )
    # serious = is_serious_subject_text(last_stimulus)
    #
    # if taste_turn == 0:
    #     pool = SERIOUS_TASTE_TEMPLATES_1 if serious else TASTE_TEMPLATES_1
    # elif taste_turn == 1:
    #     pool = SERIOUS_TASTE_TEMPLATES_2 if serious else TASTE_TEMPLATES_2
    # elif taste_turn == 2:
    #     pool = SERIOUS_TASTE_TEMPLATES_2 if serious else TASTE_TEMPLATES_2
    # else:
    #     return raw_result
    #
    # if not pool:
    #     return raw_result
    #
    # return random.choice(pool)


def is_serious_subject_text(text: str) -> bool:
    """Check if text touches serious topics."""
    serious_words = [
        "death", "trauma", "abuse", "fear", "pain", "loss",
        "suicide", "disease", "war", "racism", "politics",
        "diaspora", "suffering", "grief",
    ]
    text_lower = text.lower()
    return any(word in text_lower for word in serious_words)
