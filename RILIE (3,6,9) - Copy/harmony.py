# harmony.py
# ===========================================================================
# SYNCOPATION & SYNCHRONICITY — The Two Axes of Harmony
# ===========================================================================
# Two words. Both positive. Alchemy determines the balance.
#
# Syncopation   = the unexpected beat. Surprise, tension, off-rhythm insight.
# Synchronicity = meaningful alignment. Tuned to the user's frequency.
# Harmony       = geometric mean of both. The destination.
#
# BEIGE   = both low.  Track 6. The enemy.
# CHAOS   = high syncopation, low synchronicity. Clever but lost.
# DRONE   = low syncopation, high synchronicity. Tracking but boring.
# HARMONY = both high. That's the target.
# ===========================================================================

import random
import logging
from dataclasses import dataclass
from typing import Optional, List, Dict

# ✅ MEANING INTEGRATION — Weight informs synchronicity
from meaning import MeaningFingerprint

logger = logging.getLogger("harmony")


# ---------------------------------------------------------------------------
# THE SCORE
# ---------------------------------------------------------------------------

@dataclass
class HarmonicScore:
    """The dual-axis score for every interpretation RILIE generates."""
    syncopation: float = 0.0    # 0.0 = predictable, 1.0 = unexpected brilliance
    synchronicity: float = 0.0  # 0.0 = disconnected, 1.0 = perfectly tuned
    harmony: float = 0.0        # composite — the destination

    def compute_harmony(self) -> float:
        """
        Harmony is the geometric mean — if EITHER axis is zero, harmony collapses.
        Floor at 0.1 (dignity), ceiling at 1.0.
        """
        raw = (self.syncopation * self.synchronicity) ** 0.5
        self.harmony = max(0.1, min(1.0, raw))
        return self.harmony


# ---------------------------------------------------------------------------
# SYNCOPATION — the unexpected beat
# ---------------------------------------------------------------------------

SYNCOPATION_SIGNALS: Dict[str, float] = {
    # Cross-domain leaps
    "reframed": 0.12, "trojan": 0.12, "architecture": 0.10,
    "archaeology": 0.10, "collage": 0.10, "trickster": 0.12,
    # Originality markers
    "original": 0.08, "fresh": 0.08, "unprecedented": 0.10,
    "unique": 0.08, "never": 0.06,
    # Tension / paradox / wit
    "paradox": 0.12, "irony": 0.10, "twist": 0.10,
    "clever": 0.08, "absurd": 0.08, "satire": 0.10,
    # Depth surprises (scientific terms in non-science contexts)
    "entropy": 0.10, "emergence": 0.12, "fractal": 0.10,
    "superposition": 0.12, "topology": 0.10, "nash": 0.10,
    "apoptosis": 0.12, "negentropy": 0.12, "noether": 0.10,
    # Anti-beige hard signals
    "earned": 0.08, "brutal": 0.08, "honest": 0.06,
}

SYNCOPATION_PENALTIES: List[str] = [
    "copy of a copy", "every day is exactly the same", "autopilot",
    "it depends", "there are many", "some people say",
    "in conclusion", "to summarize", "as we all know",
]


def score_syncopation(text: str, trite_score: float = 0.0,
                       cross_domain: bool = False) -> float:
    """
    How unexpected / off-beat is this response?
    """
    tl = (text or "").lower()

    if any(p in tl for p in SYNCOPATION_PENALTIES):
        return 0.1

    raw = sum(w for s, w in SYNCOPATION_SIGNALS.items() if s in tl)

    if cross_domain:
        raw += 0.15

    raw -= trite_score * 0.2

    return max(0.1, min(1.0, raw * 2.5))


# ---------------------------------------------------------------------------
# SYNCHRONICITY — meaningful alignment
# ---------------------------------------------------------------------------

SYNCHRONICITY_SIGNALS: Dict[str, float] = {
    "understand": 0.08, "recognize": 0.08, "connection": 0.10,
    "pattern": 0.08, "clarity": 0.08, "depth": 0.06,
    "care": 0.08, "listen": 0.08, "observe": 0.06,
    "welcome": 0.06, "belong": 0.08, "home": 0.06,
    "nourish": 0.08, "sustain": 0.06, "feed": 0.06,
    "grow": 0.06, "alive": 0.06,
    "timing": 0.10, "preparation": 0.10, "location": 0.08,
    "leverage": 0.08, "execute": 0.06,
    "emergence": 0.10, "integration": 0.10, "symbiosis": 0.10,
    "cooperation": 0.08, "together": 0.08,
}


def score_synchronicity(text: str,
                         person_interests: Optional[List[str]] = None,
                         domains_matched: int = 0,
                         stimulus_overlap: float = 0.0,
                         curiosity_informed: bool = False) -> float:
    """
    How aligned / tuned-in is this response to the user?
    """
    tl = (text or "").lower()

    raw = sum(w for s, w in SYNCHRONICITY_SIGNALS.items() if s in tl)

    if person_interests:
        raw += sum(0.12 for i in person_interests if i in tl)

    raw += min(0.2, domains_matched * 0.08)
    raw += stimulus_overlap * 0.15

    if curiosity_informed:
        raw += 0.15

    return max(0.1, min(1.0, raw * 2.0))


# ---------------------------------------------------------------------------
# HARMONY — the destination
# ---------------------------------------------------------------------------

def compute_harmonic_score(
    text: str,
    trite_score: float = 0.0,
    cross_domain: bool = False,
    person_interests: Optional[List[str]] = None,
    domains_matched: int = 0,
    stimulus_overlap: float = 0.0,
    curiosity_informed: bool = False,
    meaning_fingerprint: Optional[MeaningFingerprint] = None,  # ✅ MEANING
) -> HarmonicScore:
    """
    Master function: both axes + harmony.
    Now informed by meaning weight to calibrate synchronicity.
    """
    syn = score_syncopation(text, trite_score, cross_domain)
    sync = score_synchronicity(
        text, person_interests, domains_matched,
        stimulus_overlap, curiosity_informed
    )
    
    # ✅ MEANING WEIGHT boosts synchronicity if the input matters
    if meaning_fingerprint and meaning_fingerprint.is_heavy():
        sync += 0.15  # Heavy inputs deserve more resonant responses
    
    # ✅ MEANING GAP guides the response direction
    if meaning_fingerprint and meaning_fingerprint.gap:
        # If there's an identified gap, boost sync (we know what they need)
        sync += 0.1
    
    # Clamp synchronicity
    sync = min(1.0, sync)
    
    h = HarmonicScore(syncopation=syn, synchronicity=sync)
    h.compute_harmony()
    return h


def compute_stimulus_overlap(stimulus: str, response: str) -> float:
    """What fraction of the user's meaningful words appear in the response?"""
    STOP = {"i", "me", "my", "you", "your", "the", "a", "an", "is", "are",
            "was", "were", "it", "its", "in", "on", "at", "to", "for", "of",
            "and", "or", "but", "not", "so", "if", "do", "does", "did",
            "what", "why", "how", "who", "when", "where", "this", "that",
            "with", "from", "about", "can", "will", "would", "should"}
    stim_words = {w for w in (stimulus or "").lower().split()
                  if w not in STOP and len(w) > 2}
    if not stim_words:
        return 0.0
    resp_lower = (response or "").lower()
    hits = sum(1 for w in stim_words if w in resp_lower)
    return hits / len(stim_words)


# ---------------------------------------------------------------------------
# RESONANCE — conversational acknowledgments (synchronicity without stimulus)
# ---------------------------------------------------------------------------

ACKNOWLEDGMENTS = {
    "oh for sure", "for sure", "yeah", "yep", "yup", "nice", "cool",
    "that's true", "true", "right", "exactly", "totally", "absolutely",
    "i feel that", "word", "bet", "facts", "100", "dope", "fire",
    "oh wow", "interesting", "hmm", "makes sense", "got it", "gotcha",
    "fair enough", "no doubt", "say less", "i hear you", "same",
    "oh ok", "ok cool", "alright", "that makes sense", "good point",
    "oh nice", "oh shit", "damn", "wow", "real talk", "respect",
    "that's dope", "love that", "i like that", "that's fire",
}

QUESTION_STARTERS = {"what", "why", "how", "who", "where", "when",
                     "is", "can", "do", "does", "did", "will", "would",
                     "should", "could", "tell", "explain", "describe"}


def is_resonance(text: str) -> bool:
    """
    Detect conversational acknowledgments. These are POSITIVE —
    the user is vibing, not asking. Amplify, don't crash.
    """
    s = (text or "").lower().strip().rstrip("!.?~,")
    if s in ACKNOWLEDGMENTS:
        return True
    words = s.split()
    if len(words) <= 3 and words and words[0] not in QUESTION_STARTERS:
        if any(ack in s for ack in ACKNOWLEDGMENTS):
            return True
    return False


RESONANCE_CONTINUE = [
    "I'm glad that landed. Want to go deeper, or shift gears?",
    "Good. There's more here if you want it. Or take us somewhere new.",
    "That connected. What's next?",
    "I hear you. Where should we take this?",
    "Good. What's next?",
    "I'm with you. What are you thinking?",
]

RESONANCE_CONTINUE_TOPIC = [
    "I'm glad that landed. Want to go deeper on {topic}, or shift gears?",
    "Good. There's more in {topic} if you want it. Or take us somewhere new.",
    "That connected. More on {topic}, or something else?",
]


def get_resonance_response(last_topic: Optional[str] = None) -> str:
    """Pick a resonance continuation response."""
    if last_topic:
        return random.choice(RESONANCE_CONTINUE_TOPIC).format(topic=last_topic)
    return random.choice(RESONANCE_CONTINUE)


# ---------------------------------------------------------------------------
# FREQUENCY FALLBACK — unresolved entities need external tuning
# ---------------------------------------------------------------------------

def is_unresolved_entity(stimulus: str, domains_found: list) -> bool:
    """
    Short input + no domain matches = proper noun / entity.
    Needs Google as a tuning fork to find the frequency.
    """
    if domains_found:
        return False
    words = (stimulus or "").strip().split()
    return 0 < len(words) <= 6
