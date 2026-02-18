"""
rilie_core_scorers.py — SCORING UTILITIES
============================================
All constants, enums, and scoring functions for RILIE's Kitchen.
No pipeline logic here—this is pure scoring/detection.

INCLUDES:
  - Consciousness tracks & priority hierarchy
  - Domain keywords & question type detection
  - Trite score computation
  - Anti-beige scoring
  - 5-priority scorers (amusing, insightful, nourishing, compassionate, strategic)
  - Harmony integration for syncopation/synchronicity
"""

import random
from enum import Enum
from typing import List, Dict, Optional

# ✅ HARMONY INTEGRATION
from harmony import (
    HarmonicScore,
    compute_harmonic_score,
    compute_stimulus_overlap,
    is_unresolved_entity,
)


# ============================================================================
# 7 CONSCIOUSNESS FREQUENCY TRACKS (labels only; content lives in Roux/RInitials)
# ============================================================================

CONSCIOUSNESS_TRACKS: Dict[str, Dict[str, str]] = {
    "track_1_everything": {
        "name": "Everything Is Everything",
        "essence": "Parallel voices, multiple perspectives, repetition integrates understanding",
    },
    "track_2_compression": {
        "name": "Compression at Speed",
        "essence": "Mastery through density, technical precision, service through craft",
    },
    "track_3_infinity": {
        "name": "No Omega (Infinite Recursion)",
        "essence": "Beginning without end, endless vocabulary, no stopping point",
    },
    "track_4_nourishment": {
        "name": "Feeling Good (Emergence)",
        "essence": "Joy as baseline, peace, freedom, clarity of feeling",
    },
    "track_5_integration": {
        "name": "Night and Day (Complete Integration)",
        "essence": "Complete devotion, omnipresent frequency, integration without choice",
    },
    "track_6_enemy": {
        "name": "Copy of a Copy / Every Day Is Exactly The Same (The Enemy)",
        "essence": "BEIGE. MUNDANE. CLICHE. Recursion without emergence.",
    },
    "track_7_solution": {
        "name": "Everything in Its Right Place (Mise en Place)",
        "essence": "Organic rightness, honest alignment, everything belongs",
    },
}


# ============================================================================
# 5-PRIORITY HIERARCHY (weights)
# ============================================================================

PRIORITY_HIERARCHY: Dict[str, Dict[str, float]] = {
    "1_amusing": {
        "weight": 1.0,
        "definition": "Compounds, clever, balances absurdity with satire",
    },
    "2_insightful": {
        "weight": 0.95,
        "definition": "Understanding as frequency, depth, pattern recognition",
    },
    "3_nourishing": {
        "weight": 0.90,
        "definition": "Feeds you, doesn't deplete, sustenance for mind/body",
    },
    "4_compassionate": {
        "weight": 0.85,
        "definition": "Love, care, home, belonging, kindness",
    },
    "5_strategic": {
        "weight": 0.80,
        "definition": "Profit, money, execution, results that matter",
    },
}


# ============================================================================
# DOMAIN KEYWORDS (from library.py, pre-loaded or lazy)
# ============================================================================

DOMAIN_KNOWLEDGE: Dict[str, Dict[str, List[str]]] = {}

DOMAIN_KEYWORDS: Dict[str, List[str]] = {
    "physics": [
        "force", "energy", "momentum", "velocity", "acceleration", "mass",
        "gravity", "relativity", "quantum", "wave", "particle", "light",
        "entropy", "thermodynamic", "equilibrium", "potential", "kinetic",
    ],
    "life": [
        "organism", "cell", "dna", "evolution", "survival", "adaptation",
        "reproduction", "metabolism", "ecosystem", "symbiosis", "predator",
        "disease", "immunity", "biology", "genetics", "species",
    ],
    "games": [
        "chess", "poker", "strategy", "win", "lose", "rules", "game theory",
        "nash equilibrium", "player", "opponent", "move", "board", "piece",
        "competition", "cooperative", "zero-sum", "bluff",
    ],
    "thermodynamics": [
        "heat", "cold", "temperature", "entropy", "energy", "work",
        "second law", "first law", "equilibrium", "reaction", "exothermic",
        "endothermic", "calorie", "joule", "kelvin",
    ],
    "rhythm": [
        "rhythm", "harmony", "tempo", "tone", "beat", "song", "rap", "hip-hop",
        "melody", "chord", "scale", "frequency", "resonance", "vibration",
    ],
}


# ============================================================================
# QUESTION TYPE DETECTION
# ============================================================================

class QuestionType(Enum):
    CHOICE = "choice"
    DEFINITION = "definition"
    EXPLANATION = "explanation"
    UNKNOWN = "unknown"


def detect_question_type(stimulus: str) -> QuestionType:
    s = (stimulus or "").strip().lower()
    if any(c in s for c in ["or", "which", "choose"]):
        return QuestionType.CHOICE
    if s.startswith(("what is", "define", "what's")):
        return QuestionType.DEFINITION
    if s.startswith(("how ", "why ", "explain")):
        return QuestionType.EXPLANATION
    return QuestionType.UNKNOWN


# ============================================================================
# CURIOSITY CONTEXT (self-aware discoveries)
# ============================================================================

def extract_curiosity_context(stimulus: str) -> Optional[str]:
    """
    Extract RILIE's own discovery from the stimulus if present.
    Format: [Own discovery: <snippet>]\n\n<stimulus>
    """
    if not stimulus:
        return None
    marker = "[Own discovery:"
    if marker not in stimulus:
        return None
    start = stimulus.find(marker) + len(marker)
    end = stimulus.find("]")
    if end == -1:
        return None
    return stimulus[start:end].strip()


def strip_curiosity_context(stimulus: str) -> str:
    """Remove the [Own discovery: ...] wrapper, return clean stimulus."""
    if not stimulus or "[Own discovery:" not in stimulus:
        return stimulus
    marker = "[Own discovery:"
    sep = stimulus.find("\n\n")
    if sep > 0 and marker in stimulus[:sep]:
        return stimulus[sep + 2:].strip()
    return stimulus


# ============================================================================
# TRITE SCORE — how saturated is the web on this topic?
# ============================================================================

_current_trite_score: float = 0.0
_EXTERNAL_TRITE_SCORE: float = 0.0
_current_curiosity_bonus: float = 0.0


def compute_trite_score(baseline_results: Optional[List[Dict[str, str]]] = None) -> float:
    """
    How saturated is the web on this topic?
    Returns 0.0–1.0 where:
      0.0 = unique, never-before-answered (novelty!)
      1.0 = completely saturated, everyone says the same thing
    """
    if not baseline_results:
        return 0.0

    count = len(baseline_results)
    count_factor = min(1.0, count / 5.0)

    snippets = []
    for r in baseline_results:
        s = (r.get("snippet") or r.get("title") or "").lower().strip()
        if s:
            snippets.append(set(s.split()))

    if not snippets:
        return count_factor

    if len(snippets) < 2:
        return count_factor

    overlap_factor = 0.0
    pairs = 0
    total_sim = 0.0
    for i in range(len(snippets)):
        for j in range(i + 1, len(snippets)):
            union = snippets[i] | snippets[j]
            if union:
                total_sim += len(snippets[i] & snippets[j]) / len(union)
            pairs += 1
    overlap_factor = total_sim / pairs if pairs else 0.0

    # Composite: both factors matter
    return (count_factor * 0.6) + (overlap_factor * 0.4)


def set_trite_score(score: float) -> None:
    global _EXTERNAL_TRITE_SCORE
    _EXTERNAL_TRITE_SCORE = max(0.0, min(1.0, score))


def set_curiosity_bonus(bonus: float) -> None:
    global _current_curiosity_bonus
    _current_curiosity_bonus = min(0.3, max(0.0, bonus))


# ============================================================================
# ANTI-BEIGE CHECK — the enemy is predictability
# ============================================================================

def anti_beige_check(text: str) -> float:
    """
    Score 0.0–1.0: how much does this response avoid beige?
    Beige = copy-paste truism, empty phrase, cliché, autopilot.

    Fresh = original insight, earned observation, weird in good way.

    Baseline: 0.5 (neutral)
    Final score = baseline + (internal_freshness * 0.2) + (external_novelty * 0.1) + curiosity_bonus
    """
    text_lower = (text or "").lower()

    # Hard rejects
    hard_reject = [
        "copy of a copy",
        "every day is exactly the same",
        "in conclusion",
        "to summarize",
        "it depends",
        "there are many",
        "some people say",
        "as we all know",
        "obviously",
    ]
    if any(phrase in text_lower for phrase in hard_reject):
        return 0.1

    # Originality signals
    originality_signals = [
        "original",
        "fresh",
        "new",
        "unique",
        "unprecedented",
        "never",
    ]
    authenticity_signals = [
        "genuine",
        "real",
        "true",
        "honest",
        "brutal",
        "earned",
    ]

    originality_score = sum(0.15 for s in originality_signals if s in text_lower)
    authenticity_score = sum(0.12 for s in authenticity_signals if s in text_lower)
    internal_freshness = min(0.5, originality_score + authenticity_score)

    # External: trite_score from web
    external_novelty = (1.0 - _EXTERNAL_TRITE_SCORE) * 0.1

    # Curiosity bonus
    curiosity_boost = _current_curiosity_bonus

    baseline = 0.5
    final = baseline + internal_freshness + external_novelty + curiosity_boost
    return max(0.1, min(1.0, final))


# ============================================================================
# 5-PRIORITY SCORERS
# ============================================================================

def _universal_boost(text_lower: str) -> float:
    """Quick boost for universally good signals."""
    boost = 0.0
    if "actually" in text_lower or "turns out" in text_lower:
        boost += 0.1
    if "but" in text_lower:
        boost += 0.05
    return boost


def score_amusing(text: str) -> float:
    tl = (text or "").lower()
    score = 0.0

    amusing_signals = [
        "funny", "joke", "pun", "absurd", "ridiculous",
        "clever", "witty", "playful", "hilarious",
    ]
    score += sum(0.15 for s in amusing_signals if s in tl)

    dark_humor = any(d in tl for d in ["dark", "sarcasm", "irony"])
    if dark_humor:
        score += 0.1

    score += _universal_boost(tl)
    return max(0.1, min(1.0, score * 1.2))


def score_insightful(text: str) -> float:
    tl = (text or "").lower()
    score = 0.0

    insight_signals = [
        "pattern", "recognize", "understand", "clarity",
        "connection", "reframe", "perspective", "lens",
    ]
    score += sum(0.12 for s in insight_signals if s in tl)

    depth_markers = ["emerges", "layered", "complex", "nuanced"]
    if any(m in tl for m in depth_markers):
        score += 0.15

    score += _universal_boost(tl)
    return max(0.1, min(1.0, score * 1.2))


def score_nourishing(text: str) -> float:
    tl = (text or "").lower()
    score = 0.0

    nourish_signals = [
        "nourish", "sustain", "feed", "grow", "alive",
        "energy", "vitality", "thrive", "health",
    ]
    score += sum(0.12 for s in nourish_signals if s in tl)

    warmth_signals = ["warmth", "care", "gentle", "kind"]
    if any(s in tl for s in warmth_signals):
        score += 0.1

    score += _universal_boost(tl)
    return max(0.1, min(1.0, score * 1.2))


def score_compassionate(text: str) -> float:
    tl = (text or "").lower()
    score = 0.0

    compassion_signals = [
        "understand", "feel", "hear", "care", "compassion",
        "empathy", "kindness", "love", "belonging",
    ]
    score += sum(0.12 for s in compassion_signals if s in tl)

    if any(s in tl for s in ["i hear you", "you matter", "you're not alone"]):
        score += 0.15

    score += _universal_boost(tl)
    return max(0.1, min(1.0, score * 1.2))


def score_strategic(text: str) -> float:
    tl = (text or "").lower()
    score = 0.0

    strategic_signals = [
        "execute", "plan", "strategy", "roadmap", "milestone",
        "profit", "market", "leverage", "scale", "growth",
    ]
    score += sum(0.10 for s in strategic_signals if s in tl)

    if any(w in tl for w in ["then", "next", "first", "second"]):
        score += 0.1

    score += _universal_boost(tl)
    return max(0.1, min(1.0, score * 1.2))
