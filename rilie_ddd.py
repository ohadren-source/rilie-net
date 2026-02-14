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
        """Simple sequence: 1-2 = TASTE, 3+ = OPEN."""
        if self.exchange_count <= 1:
            return DisclosureLevel.TASTE
        elif self.exchange_count == 2:
            return DisclosureLevel.TASTE
        return DisclosureLevel.OPEN
    
    @property
    def taste_turn(self) -> int:
        """Which TASTE turn are we on? (0, 1, or done)"""
        if self.exchange_count <= 1:
            return 0  # First TASTE
        elif self.exchange_count == 2:
            return 1  # Second TASTE
        return 2      # OFF to speech
    
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
    Shape by disclosure level based on EXCHANGE COUNT, not conditions.
    
    Simple sequence:
      Exchange 0-1: TASTE turn 1 (invitation)
      Exchange 2: TASTE turn 2 (invitation)
      Exchange 3+: OPEN (actual response through speech pipeline)
    """
    
    level = conversation.disclosure_level
    taste_turn = conversation.taste_turn
    
    # TASTE TURN 1 (exchange 0)
    if taste_turn == 0:
        serious = is_serious_subject_text(raw_result)
        templates = SERIOUS_TASTE_TEMPLATES_1 if serious else TASTE_TEMPLATES_1
        used = set(conversation.response_history)
        available = [t for t in templates if t not in used]
        if not available:
            available = templates
        return random.choice(available)
    
    # TASTE TURN 2 (exchange 1)
    elif taste_turn == 1:
        serious = is_serious_subject_text(raw_result)
        templates = SERIOUS_TASTE_TEMPLATES_2 if serious else TASTE_TEMPLATES_2
        used = set(conversation.response_history)
        available = [t for t in templates if t not in used]
        if not available:
            available = templates
        return random.choice(available)
    
    # OPEN LEVEL (exchange 2+) — OFF to speech pipeline
    else:
        # Return raw_result; it goes through speech pipeline
        return raw_result


def is_serious_subject_text(text: str) -> bool:
    """Check if text touches serious topics."""
    serious_words = [
        "death", "trauma", "abuse", "fear", "pain", "loss",
        "suicide", "disease", "war", "racism", "politics",
        "diaspora", "suffering", "grief",
    ]
    text_lower = text.lower()
    return any(word in text_lower for word in serious_words)
