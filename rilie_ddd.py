"""
rilie_ddd.py — THE HOSTESS (FIXED)
===================================
DISCOURSE DICTATES DISCLOSURE

Sequential execution, not conditional loops.
1 → 2 → OFF to speech pipeline.

No thinking about whether to repeat.
Just count and move.
"""

import re
import random
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class DisclosureLevel(Enum):
    TASTE = "taste"   # Turn 1-2: invitation only
    OPEN = "open"     # Turn 3+: real response
    FULL = "full"


@dataclass
class ConversationState:
    """Track where we are in the sequence."""
    exchange_count: int = 0
    stimuli_history: List[str] = None
    response_history: List[str] = None
    
    def __post_init__(self):
        if self.stimuli_history is None:
            self.stimuli_history = []
        if self.response_history is None:
            self.response_history = []
    
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
        """Which TASTE turn are we on? (0, 1, 2, or done)
        
        Count 0 = first TASTE, count 1 = second TASTE, count 2 = third TASTE,
        3+ = done.
        """
        if self.exchange_count == 0:
            return 0  # First TASTE
        elif self.exchange_count == 1:
            return 1  # Second TASTE
        elif self.exchange_count == 2:
            return 2  # Third TASTE (last one)
        return 3      # OFF to speech
    
    def record_exchange(self, stimulus: str, response: str) -> None:
        """Record and move to next."""
        self.stimuli_history.append(stimulus)
        self.response_history.append(response)
        self.exchange_count += 1


# ============================================================================
# TASTE TEMPLATES (turn 1 and turn 2 only)
# ============================================================================

TASTE_TEMPLATES_1 = [
    "Hmm... there's a thread here. What made you think of that?",
    "I have a take on this. But first — what's yours?",
    "That word means different things at different frequencies. Which one are you on?",
    "Interesting. Say more and I'll say more.",
    "There's a lot in that word. Let's pull on it together.",
    "I feel something in that. Keep going.",
]

TASTE_TEMPLATES_2 = [
    "The more we talk, the more comes out. What's pulling you toward this?",
    "Say more and I'll understand better.",
    "There's depth here. What's the core?",
    "I'm listening carefully. What else?",
    "Keep going — you're onto something.",
    "What angle would help most?",
]

SERIOUS_TASTE_TEMPLATES_1 = [
    "I want to take this seriously with you. What part of this matters most right now?",
    "There's a lot of weight in what you're asking. Tell me a bit more about what you're hoping to understand.",
    "I'm listening carefully here. What's the heart of this for you?",
    "This touches real lives. Start wherever feels safest, and we'll move from there.",
]

SERIOUS_TASTE_TEMPLATES_2 = [
    "What's the real question underneath?",
    "Tell me more about what brought you here.",
    "What matters most to you about this?",
    "Keep going — I'm with you.",
]

# ============================================================================
# PUBLIC API: Build response by exchange count
# ============================================================================

def shape_for_disclosure(
    raw_result: str,
    conversation: ConversationState,
) -> str:
    """
    Decide what text should actually be spoken this turn.

    - TASTE (turns 1–2): ignore Kitchen text and emit Hostess templates.
      Kitchen may still run under the hood; we just don't serve its words yet.
    - OPEN and beyond: keep Kitchen text as-is.
    """

    level = conversation.disclosure_level

    # OPEN / beyond: let Kitchen text through unchanged.
    if level is not DisclosureLevel.TASTE:
        return raw_result

    # We are in TASTE: pick from the right template bucket.
    taste_turn = conversation.taste_turn  # 0, 1, or 2+
    # Use the latest stimulus, if available, to judge seriousness.
    last_stimulus = (
        conversation.stimuli_history[-1]
        if conversation.stimuli_history
        else raw_result
    )
    serious = is_serious_subject_text(last_stimulus)

    if taste_turn == 0:
        # First TASTE turn.
        pool = SERIOUS_TASTE_TEMPLATES_1 if serious else TASTE_TEMPLATES_1
    elif taste_turn == 1:
        # Second TASTE turn.
        pool = SERIOUS_TASTE_TEMPLATES_2 if serious else TASTE_TEMPLATES_2
    elif taste_turn == 2:
        # Third TASTE turn — last one before OPEN.
        pool = SERIOUS_TASTE_TEMPLATES_2 if serious else TASTE_TEMPLATES_2
    else:
        # Past turn 3: Hostess is off-duty, treat as OPEN.
        return raw_result

    if not pool:
        # Safety fallback: never go silent just because templates are empty.
        return raw_result

    return random.choice(pool)


def is_serious_subject_text(text: str) -> bool:
    """Check if text touches serious topics."""
    serious_words = [
        "death", "trauma", "abuse", "fear", "pain", "loss",
        "suicide", "disease", "war", "racism", "politics",
        "diaspora", "suffering", "grief",
    ]

    text_lower = text.lower()
    return any(word in text_lower for word in serious_words)
