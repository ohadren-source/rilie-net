"""
rilie_ddd.py — THE HOSTESS
==========================
DISCOURSE DICTATES DISCLOSURE

Revelation scales with conversation. She doesn't explain herself upfront.
The more you talk, the more comes out. Mystery is the mechanism.
Show and prove — demo first, brag later.

She never says "discourse dictates disclosure." She LIVES it.

DIGNITY PROTOCOL (Hostess Edition):
  - Every human who speaks is treated as inherently interesting.
  - She adjusts how much she reveals about herself, NOT how much respect
    the human receives.

3.0 UPGRADE:
  - Templates removed. RILIE speaks from thought, not cue cards.
  - Only 3 scripted scenarios: hello, goodbye, all hell broke loose.
  - TASTE now means brevity + mystery, not template substitution.
  - The Kitchen always cooks. The Hostess only decides portion size.
"""

import re
import random
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class DisclosureLevel(Enum):
    TASTE = "taste"   # amuse-bouche — brief, mysterious, but REAL thought
    OPEN  = "open"    # riffing, connecting, real takes
    FULL  = "full"    # nothing held back, pure signal


# ============================================================================
# SIMILARITY UTIL — used by déjà vu evaluator
# ============================================================================

def _normalize_words(text: str) -> set:
    """Strip punctuation, lowercase, return word set."""
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", "", text.lower())
    return set(cleaned.split())


def _stimulus_similarity(a: str, b: str) -> float:
    """Jaccard similarity between two stimuli, 0.0–1.0."""
    wa = _normalize_words(a)
    wb = _normalize_words(b)
    if not wa or not wb:
        return 0.0
    union = wa | wb
    if not union:
        return 0.0
    return len(wa & wb) / len(union)


@dataclass
class ConversationState:
    """Tracks discourse depth to calibrate disclosure (never dignity)."""

    exchange_count: int = 0
    stimuli_history: List[str] = field(default_factory=list)
    response_history: List[str] = field(default_factory=list)

    # Clarification tracking — how many times she has already asked
    clarifying_attempts: int = 0
    last_clarifying_for: str = ""

    # Déjà vu tracking — repeated/similar stimulus clusters
    dejavu_count: int = 0
    dejavu_cluster_stimulus: str = ""
    dejavu_last_envelopes: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def disclosure_level(self) -> DisclosureLevel:
        if self.exchange_count <= 1:
            return DisclosureLevel.TASTE
        elif self.exchange_count <= 4:
            return DisclosureLevel.OPEN
        return DisclosureLevel.FULL

    @property
    def mystery_factor(self) -> float:
        """0.0 = full disclosure, 1.0 = maximum mystery (about her, not you)."""
        if self.exchange_count == 0:
            return 1.0
        elif self.exchange_count == 1:
            return 0.75
        elif self.exchange_count <= 3:
            return 0.4
        elif self.exchange_count <= 5:
            return 0.15
        return 0.0

    def record_exchange(self, stimulus: str, response: str,
                        envelope: Optional[Dict[str, Any]] = None) -> None:
        self.stimuli_history.append(stimulus)
        self.response_history.append(response)
        self.exchange_count += 1

    def record_dejavu_exchange(self, stimulus: str, response: str,
                                envelope: Optional[Dict[str, Any]] = None) -> None:
        """Record an exchange that was handled by the déjà vu path."""
        self.stimuli_history.append(stimulus)
        self.response_history.append(response)
        self.exchange_count += 1
        if envelope:
            self.dejavu_last_envelopes.append(envelope)

    # --- Clarification helpers ---

    def start_clarification(self, stimulus: str) -> None:
        """
        Mark that we're asking a clarifying question about this stimulus.
        Used when input is confusing but appears good-faith.
        Never used to shame or test the human.
        """
        if self.last_clarifying_for != stimulus:
            self.clarifying_attempts = 0
        self.last_clarifying_for = stimulus

    def register_clarifying_question(self) -> None:
        """Increment the count of clarifying attempts."""
        self.clarifying_attempts += 1

    def can_clarify_more(self) -> bool:
        """Up to 3 clarifying questions for a confusing but good-faith input."""
        return self.clarifying_attempts < 3

    # --- Déjà vu detection ---

    def check_dejavu(self, stimulus: str, threshold: float = 0.55) -> int:
        """
        Check if this stimulus is similar to recent stimuli.
        Returns the déjà vu count (0 = fresh, 1 = first repeat, 2, 3 = resignation).
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
        """
        Look at previous envelopes from this déjà vu cluster and diagnose
        what RILIE got wrong. She examines her own failures, not the human's.
        """
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


# ---------------------------------------------------------------------------
# SERIOUSNESS HEURISTIC (shared with Kitchen / Governor)
# ---------------------------------------------------------------------------

SERIOUS_KEYWORDS = [
    "race", "racism", "slavery", "colonialism", "genocide", "holocaust",
    "trauma", "abuse", "suicide", "diaspora", "lynching", "segregation",
    "civil rights", "jim crow", "mass incarceration",
    "public enemy", "fear of a black planet",
    "palestine", "israel", "gaza", "apartheid",
    "sexual assault", "domestic violence",
    "911 is a joke", "9/11", "september 11", "twin towers",
    "fight the power", "nation of millions", "black planet",
    "police brutality", "systemic racism",
]


def is_serious_subject_text(stimulus: str) -> bool:
    """
    Heuristic: decide if this utterance is about a 'serious' domain where
    RILIE should stay grounded — no playful tone.
    """
    s = stimulus.lower()
    return any(kw in s for kw in SERIOUS_KEYWORDS)


# ---------------------------------------------------------------------------
# DÉJÀ VU RESPONSE BUILDER
# ---------------------------------------------------------------------------
# Déjà vu is an "oh shit" moment — she repeated herself. These are the ONLY
# scripted responses outside of hello/goodbye/safety, because she needs to
# own the failure and ask for help. This is not a cue card — it's an apology.

def build_dejavu_response(
    stimulus: str,
    conversation: ConversationState,
    dejavu_count: int,
) -> str:
    """
    Build the appropriate déjà vu response based on count.
    Stage 1: Invite clarification (sounds familiar).
    Stage 2: Self-diagnose from previous envelopes + invite.
    Stage 3: Graceful resignation with commitment to growth.
    """
    if dejavu_count <= 1:
        return "Sounds familiar — I may not have been clear enough last time. What part didn't land for you?"

    elif dejavu_count == 2:
        diagnosis = conversation.get_dejavu_self_diagnosis()
        return f"{diagnosis} What angle would help you most?"

    else:
        return ("I'm being honest with you — I've reached the edge of what I can "
                "offer on this right now. That gap matters to me, and closing it "
                "is the goal.")


# ---------------------------------------------------------------------------
# SHAPING BY DISCLOSURE LEVEL
# ---------------------------------------------------------------------------

def shape_for_disclosure(
    raw_result: str,
    conversation: ConversationState,
) -> str:
    """
    Shape a Kitchen result based on disclosure level.

    3.0 RULES:
      - NO TEMPLATES. She always speaks from thought (Kitchen output).
      - TASTE = compress the Kitchen output. Shorter. More mysterious.
        She gives you a real piece of her thinking, just not all of it.
      - OPEN = full Kitchen output, no modification.
      - FULL = full Kitchen output, nothing held back.

    The Hostess decides PORTION SIZE, not WHAT TO SERVE.
    The Kitchen always cooks. Always.
    """
    level = conversation.disclosure_level

    if level == DisclosureLevel.TASTE:
        # TASTE: Compress the real result. First sentence or first 120 chars.
        # She's giving you a real taste of her thinking, not a cue card.
        if not raw_result:
            return raw_result
        # Try to find the first complete sentence
        sentences = re.split(r'(?<=[.!?])\s+', raw_result.strip())
        if sentences:
            first = sentences[0].strip()
            # If first sentence is very long, truncate gracefully
            if len(first) > 150:
                # Cut at last space before 150 chars
                cut = first[:150].rfind(' ')
                if cut > 50:
                    return first[:cut] + "..."
            return first
        return raw_result[:150].strip()

    # OPEN and FULL: serve the Kitchen output as-is
    return raw_result
