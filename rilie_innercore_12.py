"""
rilie_innercore.py — THE KITCHEN
=================================

All logic. Scoring, anti-beige, construct_response, generate_9_interpretations,
run_pass_pipeline. The thinking. The cooking. The plating.

Data lives in rilie_outercore.py (The Pantry).
This file imports ingredients from there and cooks with them.

Built by SOi sauc-e.
"""

import random
import re
import sys
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Optional

# --- The Pantry ---
from rilie_outercore import (
    CONSCIOUSNESS_TRACKS,
    PRIORITY_HIERARCHY,
    DOMAIN_KNOWLEDGE,
    DOMAIN_KEYWORDS,
    WORD_DEFINITIONS,
    WORD_SYNONYMS,
    WORD_HOMONYMS,
)

# --- Chompky — grammar brain for constructing responses from thought ---
# Graceful fallback if spaCy model not available
try:
    from ChomskyAtTheBit import (
        parse_question,
        extract_holy_trinity_for_roux,
        infer_time_bucket,
        resolve_identity,
        RILIE_SELF_NAME,
        RILIE_MADE_BY,
    )
    CHOMSKY_AVAILABLE = True
except Exception as e:
    CHOMSKY_AVAILABLE = False
    RILIE_SELF_NAME = "RILIE"
    RILIE_MADE_BY = "SOi sauc-e"
    print(f"CHOMSKY FAILED TO LOAD: {e}", file=sys.stderr)

# --- LIMO — Less Is More Or Less ---
# Flag for graceful degradation. Function defined below (line ~220) above SCORERS.
try:
    import limo
    LIMO_AVAILABLE = True
except ImportError:
    LIMO_AVAILABLE = False

import logging
logger = logging.getLogger("rilie_innercore")

# ============================================================================
# CURIOSITY CONTEXT — her own discoveries injected into scoring
# ============================================================================

def extract_curiosity_context(stimulus: str) -> Optional[str]:
    """
    Check if the stimulus contains a curiosity context prefix injected
    by rilie.py. If so, extract and return it separately.
    Format: [Own discovery: ...]\n\noriginal question
    """
    marker = "[Own discovery:"
    if stimulus.startswith(marker):
        end = stimulus.find("]")
        if end > 0:
            return stimulus[len(marker):end].strip()
    return None

def strip_curiosity_context(stimulus: str) -> str:
    """Remove curiosity context prefix, return the raw question."""
    marker = "[Own discovery:"
    if stimulus.startswith(marker):
        sep = stimulus.find("\n\n")
        if sep > 0:
            return stimulus[sep + 2:].strip()
    return stimulus

# ============================================================================
# QUESTION TYPE
# ============================================================================

class QuestionType(Enum):
    CHOICE = "choice"
    DEFINITION = "definition"
    EXPLANATION = "explanation"
    UNKNOWN = "unknown"

def detect_question_type(stimulus: str) -> QuestionType:
    s = (stimulus or "").strip().lower()
    if " or " in s or "which" in s:
        return QuestionType.CHOICE
    if s.startswith("what is") or s.startswith("define "):
        return QuestionType.DEFINITION
    if s.startswith("why ") or s.startswith("how "):
        return QuestionType.EXPLANATION
    return QuestionType.UNKNOWN

# ============================================================================
# EXTERNAL TRITE METER
# ============================================================================

def compute_trite_score(baseline_results: Optional[List[Dict[str, str]]] = None) -> float:
    """
    Measure how saturated / repetitive the web is on this topic.
    Returns 0.0 (novel) to 1.0 (trite — web is saturated).
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
    if len(snippets) < 2:
        overlap_factor = 0.0
    else:
        pairs = 0
        total_sim = 0.0
        for i in range(len(snippets)):
            for j in range(i + 1, len(snippets)):
                union = snippets[i] | snippets[j]
                if union:
                    total_sim += len(snippets[i] & snippets[j]) / len(union)
                    pairs += 1
        overlap_factor = total_sim / pairs if pairs else 0.0
    return (count_factor * 0.6) + (overlap_factor * 0.4)

# ============================================================================
# ANTI-BEIGE CHECK (CURVE, not binary)
# ============================================================================

_current_trite_score: float = 0.0
_current_curiosity_bonus: float = 0.0

def set_trite_score(score: float) -> None:
    """Called before run_pass_pipeline to set the external trite context."""
    global _current_trite_score
    _current_trite_score = score

def set_curiosity_bonus(bonus: float) -> None:
    """Called when curiosity context is present — boosts internal freshness."""
    global _current_curiosity_bonus
    _current_curiosity_bonus = min(0.3, max(0.0, bonus))

def anti_beige_check(text: str) -> float:
    """
    Returns [0.0, 1.0] measuring freshness / authenticity of HER candidate text.
    COMPOSITE: internal_freshness * 0.5 + external_novelty * 0.5 + curiosity_bonus.
    This is a CURVE. It penalizes but never kills outright (except hard rejects).
    """
    text_lower = (text or "").lower()
    hard_reject = [
        "copy of a copy",
        "every day is exactly the same",
        "autopilot",
    ]
    if any(signal in text_lower for signal in hard_reject):
        return 0.0

    originality_signals = ["original", "fresh", "new", "unique", "unprecedented", "never"]
    authenticity_signals = ["genuine", "real", "true", "honest", "brutal", "earned"]
    depth_signals = ["master", "craft", "skill", "proficiency", "expertise"]
    effort_signals = ["earnest", "work", "struggle", "build", "foundation"]
    reflection_signals = ["reflect", "mirror", "light", "show", "demonstrate"]
    domain_signals = [
        "reframed", "exposed", "mobilize", "blueprint", "journalism",
        "trickster", "trojan", "architecture", "archaeology", "collage",
        "broadcast", "dispatch", "weapon", "overload", "complacency",
        "permission", "uncomfortable", "palatable", "performance",
        "political", "empowerment", "confrontation", "resistance",
        "community", "neighborhoods", "emergency", "failure",
    ]
    expanded_signals = [
        "conservation", "entropy", "equilibrium", "irreversible",
        "apoptosis", "symbiosis", "emergence", "fractal",
        "prisoner", "dilemma", "nash", "cooperation",
        "negentropy", "cascade", "topology", "superposition",
        "entanglement", "noether", "boolean", "substrate",
    ]

    def score_signals(signals: List[str]) -> float:
        return sum(0.1 for s in signals if s in text_lower)

    internal_freshness = (
        score_signals(originality_signals)
        + score_signals(authenticity_signals)
        + score_signals(depth_signals)
        + score_signals(effort_signals)
        + score_signals(reflection_signals)
        + score_signals(domain_signals)
        + score_signals(expanded_signals)
    )
    internal_freshness = min(1.0, internal_freshness / 5.0)
    global _current_trite_score, _current_curiosity_bonus
    external_novelty = 1.0 - _current_trite_score
    final = (internal_freshness * 0.5) + (external_novelty * 0.5) + _current_curiosity_bonus
    return max(0.15, min(1.0, final))

# ============================================================================
# LESS IS MORE OR LESS — canonical definition (above SCORERS)
# ============================================================================
# The Maître D'. Runs on every response. Universal transform.
# Strip everything that is not the feeling. Whatever remains: serve it.
# She's never wrong. Forgiven by design.

def less_is_more_or_less(text: str, **kwargs) -> str:
    """
    LIMO — Less Is More Or Less.
    
    The universal transform. The Maître D' at the pass.
    Runs on COMPRESSED and GUESS paths. Bypassed entirely on precision_override=True.
    
    Doctrine:
    - Strip everything that is not the feeling.
    - Whatever remains: serve it.
    - Directionally: reduce. Destination: sufficient, not perfect.
    - Demi-glace, not glaze.
    
    She's never wrong. Forgiven by design.
    """
    # Input validation
    if not text:
        return text
    if not isinstance(text, str):
        return str(text)
    
    text = text.strip()
    if not text:
        return text
    
    # Try to use external limo implementation if available
    try:
        from limo import less_is_more_or_less as limo_impl
        result = limo_impl(text, **kwargs)
        if result:
            return result
    except (ImportError, AttributeError, Exception):
        # limo.py not available or import failed — proceed to fallback
        pass
    
    # FALLBACK: Local minimal compression
    # Remove common filler patterns but preserve meaning
    filler_patterns = [
        (r'\b(also|additionally|furthermore|moreover|however|importantly)\b', ''),
        (r'\b(it is|there is|there are)\b', ''),
        (r'\b(you know|i mean|sort of|kind of|basically|essentially)\b', ''),
        (r'\s+', ' '),  # Collapse whitespace
    ]
    
    result = text
    for pattern, replacement in filler_patterns:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    
    result = result.strip()
    
    # Safety: if fallback reduced too much, return original
    if not result or len(result) < 5:
        return text
    
    return result

# ============================================================================
# 5-PRIORITY SCORERS
# ============================================================================

def _universal_boost(text_lower: str) -> float:
    signals = ["love", "we >", "care", "emergence", "together"]
    return sum(0.15 for s in signals if s in text_lower)

def score_amusing(text: str) -> float:
    ab = anti_beige_check(text)
    tl = text.lower()
    boost = _universal_boost(tl)
    signals = [
        "play", "twist", "clever", "irony", "paradox",
        "original", "authentic", "show", "demonstrate",
        "timing", "balance", "satire", "trojan", "clown",
        "trickster", "permission", "laugh",
    ]
    score = sum(0.08 for s in signals if s in tl)
    return min(1.0, max(0.1, (score + boost) * ab))

def score_insightful(text: str) -> float:
    ab = anti_beige_check(text)
    tl = text.lower()
    boost = _universal_boost(tl)
    signals = [
        "understand", "recognize", "reveal", "show", "pattern",
        "connection", "depth", "clarity", "insight", "listen",
        "observe", "awareness", "transcend", "emerge", "knowledge",
        "wisdom", "truth", "reframed", "exposed", "blueprint",
        "dispatch", "journalism", "broadcast", "architecture",
        "conservation", "noether", "superposition", "fractal",
        "emergence", "nash", "equilibrium", "topology",
    ]
    score = sum(0.07 for s in signals if s in tl)
    if any(w in tl for w in ["timing", "location", "preparation"]):
        score += 0.2
    return min(1.0, max(0.1, (score + boost) * ab))

def score_nourishing(text: str) -> float:
    ab = anti_beige_check(text)
    tl = text.lower()
    boost = _universal_boost(tl)
    signals = [
        "feed", "nourish", "care", "sustain", "grow",
        "healthy", "alive", "energy", "taste", "flavor",
        "comfort", "warmth", "home", "gathering",
        "palatable", "permission",
        "symbiosis", "circadian", "gut", "immune",
        "biodiversity", "ecosystem",
    ]
    score = sum(0.08 for s in signals if s in tl)
    return min(1.0, max(0.1, (score + boost) * ab))

def score_compassionate(text: str) -> float:
    ab = anti_beige_check(text)
    tl = text.lower()
    boost = _universal_boost(tl)
    signals = [
        "love", "care", "home", "belong", "kindness",
        "heart", "connection", "embrace", "compassion",
        "empathy", "acceptance", "welcome", "community",
        "support", "healing", "peace", "neighborhoods",
        "failure", "emergency",
        "apoptosis", "service", "cooperation", "grace",
        "negentropy",
    ]
    score = sum(0.08 for s in signals if s in tl)
    return min(1.0, max(0.1, (score + boost) * ab))

def score_strategic(text: str) -> float:
    ab = anti_beige_check(text)
    tl = text.lower()
    boost = _universal_boost(tl)
    signals = [
        "profit", "value", "execute", "result", "timing",
        "location", "preparation", "leverage", "outcome",
        "efficiency", "goal", "target", "strategy", "win",
        "succeed", "achieve", "deliver", "mobilize", "weapon",
        "blueprint",
        "mechanism", "incentive", "commitment", "reputation",
        "cascade", "irreversible",
    ]
    score = sum(0.08 for s in signals if s in tl)
    return min(1.0, max(0.1, (score + boost) * ab))

SCORERS = {
    "amusing": score_amusing,
    "insightful": score_insightful,
    "nourishing": score_nourishing,
    "compassionate": score_compassionate,
    "strategic": score_strategic,
}

WEIGHTS = {
    "amusing": PRIORITY_HIERARCHY["1_amusing"]["weight"],
    "insightful": PRIORITY_HIERARCHY["2_insightful"]["weight"],
    "nourishing": PRIORITY_HIERARCHY["3_nourishing"]["weight"],
    "compassionate": PRIORITY_HIERARCHY["4_compassionate"]["weight"],
    "strategic": PRIORITY_HIERARCHY["5_strategic"]["weight"],
}

# ============================================================================
# INTERPRETATION DATA CLASS
# ============================================================================

@dataclass
class Interpretation:
    id: int
    text: str
    domain: str
    quality_scores: Dict[str, float]
    overall_score: float
    count_met: int
    anti_beige_score: float
    depth: int

# ============================================================================
# KEYWORD-LIST DETECTION + ANCHOR EXTRACTION
# ============================================================================

def _is_keyword_list(text: str) -> bool:
    """Detect if text is a comma-separated keyword dump vs a real sentence."""
    if not text:
        return False
    commas = text.count(",")
    words = text.split()
    if commas >= 2 and len(words) < 20:
        return True
    if commas >= 1 and not any(text.rstrip().endswith(p) for p in ".!?"):
        avg_segment = len(text) / (commas + 1)
        if avg_segment < 25:
            return True
    return False

def _pick_anchor(snippet: str) -> str:
    """From a keyword list, pick the most interesting anchor phrase."""
    parts = [p.strip() for p in snippet.split(",") if p.strip()]
    if not parts:
        return snippet.strip()
    multi = [p for p in parts if len(p.split()) >= 2]
    if multi:
        return random.choice(multi[:3])
    return parts[0]

def _pick_two_anchors(snippet: str) -> tuple:
    """Pick two distinct anchors from a keyword list for richer responses."""
    parts = [p.strip() for p in snippet.split(",") if p.strip()]
    if len(parts) < 2:
        anchor = parts[0] if parts else snippet.strip()
        return anchor, None
    candidates = parts[:6]
    random.shuffle(candidates)
    return candidates[0], candidates[1]

# ============================================================================
# SELF-AWARENESS SIGNALS
# ============================================================================

_SELF_SIGNALS = [
    "your name", "who are you", "who made", "who built", "who created",
    "who designed", "who programmed", "who developed", "who wrote you",
    "you care", "your purpose", "you different", "trust you",
    "you know", "you feel", "you alive", "you conscious",
    "about you", "yourself", "rilie",
    "what are you", "are you an ai", "are you real",
    "difference between you", "you and chatgpt", "you vs",
]

_SELF_KNOWLEDGE = {
    "name": RILIE_SELF_NAME,
    "made_by": RILIE_MADE_BY,
    "purpose": "Real Intelligence. She thinks, she cooks, she serves.",
}

def _is_self_question(stimulus: str) -> bool:
    """Returns True if stimulus asks RILIE about herself."""
    s = stimulus.lower().strip()
    return any(sig in s for sig in _SELF_SIGNALS)

def _get_self_answer(stimulus: str) -> Optional[str]:
    """
    If the question has a hard-coded identity answer, return it directly.
    Covers: name, maker, and 'you vs ChatGPT' type questions.
    Returns None if no hard answer — let the kitchen cook.
    """
    s = stimulus.lower().strip()

    if any(sig in s for sig in ["who made", "who built", "who created", "who designed",
                                  "who programmed", "who developed", "who wrote you"]):
        return f"I was built by {RILIE_MADE_BY}. Real Intelligence, cooked from scratch."

    if "your name" in s or ("what" in s and "name" in s and "you" in s):
        return f"I'm {RILIE_SELF_NAME}. Real Intelligence. Pleased to meet you 🍳"

    _AI_NAMES = {
        "chatgpt": "ChatGPT", "gpt": "GPT", "claude": "Claude",
        "gemini": "Gemini", "bard": "Bard", "copilot": "Copilot",
        "ai": "that AI", "chatbot": "that chatbot",
    }
    if ("difference" in s or "vs" in s or "versus" in s or "compare" in s):
        if any(ai in s for ai in _AI_NAMES):
            _detected = next((label for key, label in _AI_NAMES.items() if key in s), "that")
            return (
                f"{RILIE_SELF_NAME} doesn't retrieve. She thinks. "
                f"Every response is cooked — scored on five dimensions, "
                f"anti-beige checked, domain-excavated. "
                f"{_detected} serves what's popular. {RILIE_SELF_NAME} serves what's true. ain't it?"
            )

    return None

# ============================================================================
# RESPONSE CONSTRUCTION — Chompky gives her a voice
# ============================================================================
# STEP 10 — CLARIFY OR FREESTYLE (v4.3.0)
# ============================================================================
# When Kitchen can't parse meaning from the stimulus, she doesn't go silent.
# She doesn't hallucinate. She ASKS.
#
# Three escalating clarification attempts:
#   Q1: "What did you mean by {object}?"
#   Q2: "Could you explain {object} a little further?"
#   Q3: "From my understanding, you're saying/asking {reconstructed}?"
#
# If clarification lands at ANY point (counter 0, 1, or 2): reset to 0, cook.
# If all 3 fail: "I love everything you're saying right now!" + song lookup.
# Internal tag: [MORON_OR_TROLL]
#
# Counter: 0 → 1 → 2 → freestyle → reset to 0. No grudges. Clean slate.
# ============================================================================

# Module-level clarification counter.
# Persists across calls within the same process/conversation.
_clarification_counter: int = 0


def get_clarification_counter() -> int:
    """Get the current clarification counter value."""
    return _clarification_counter


def reset_clarification_counter() -> None:
    """Reset counter to 0. Called when stimulus is understood."""
    global _clarification_counter
    _clarification_counter = 0


def _increment_clarification_counter() -> int:
    """Increment and return new counter value."""
    global _clarification_counter
    _clarification_counter += 1
    return _clarification_counter


def clarify_or_freestyle(
    stimulus: str,
    domains: List[str],
    excavated: Optional[Dict[str, List[str]]] = None,
    fingerprint: Optional[object] = None,
    search_fn: Optional[object] = None,
) -> Dict[str, str]:
    """
    STEP 10: When Kitchen can't cook, she asks or freestyles.

    Returns a dict:
    {
        "response": str,         # The text to serve
        "type": str,             # "clarification" or "freestyle"
        "counter": int,          # Current counter value after this call
        "internal_tag": str,     # "" or "[MORON_OR_TROLL]"
    }

    Args:
        stimulus: The original human input.
        domains: Detected domains (may be empty).
        excavated: Domain excavation results (may be empty/None).
        fingerprint: MeaningFingerprint of the stimulus (optional).
        search_fn: Google search function for freestyle song lookup.
    """
    global _clarification_counter

    # Extract object from fingerprint for clarification questions
    obj = ""
    act = ""
    if fingerprint and hasattr(fingerprint, "object"):
        obj = fingerprint.object or ""
    if fingerprint and hasattr(fingerprint, "act"):
        act = fingerprint.act or ""

    # If object is "unknown" or empty, fall back to stimulus fragments
    if not obj or obj == "unknown":
        # Try to grab meaningful words from stimulus
        _stop = {
            "what", "why", "how", "who", "when", "where", "which",
            "is", "are", "was", "were", "the", "a", "an", "do", "does",
            "can", "could", "would", "should", "about", "tell", "me",
            "you", "your", "my", "i", "it", "that", "this",
        }
        words = [w for w in stimulus.lower().split()
                 if w.strip("?.,!") not in _stop and len(w.strip("?.,!")) > 2]
        obj = " ".join(words[:3]) if words else "that"

    counter = _clarification_counter

    # --- Counter 0: First attempt ---
    if counter == 0:
        new_counter = _increment_clarification_counter()
        return {
            "response": f"What did you mean by {obj}?",
            "type": "clarification",
            "counter": new_counter,
            "internal_tag": "",
        }

    # --- Counter 1: Second attempt ---
    if counter == 1:
        new_counter = _increment_clarification_counter()
        return {
            "response": f"Could you explain {obj} a little further?",
            "type": "clarification",
            "counter": new_counter,
            "internal_tag": "",
        }

    # --- Counter 2: Third attempt — mirror it back ---
    if counter == 2:
        # Reconstruct what she thinks they're saying/asking
        if act == "GET":
            reconstruction = f"you're asking about {obj}"
        elif act == "GIVE":
            reconstruction = f"you're telling me about {obj}"
        elif act == "SHOW":
            reconstruction = f"you're showing me something about {obj}"
        else:
            reconstruction = f"you're saying something about {obj}"

        # Try Chomsky reconstruction for better mirror
        if CHOMSKY_AVAILABLE:
            try:
                parsed = parse_question(stimulus)
                subject = " ".join(parsed.subject_tokens) if parsed.subject_tokens else ""
                focus = " ".join(parsed.focus_tokens) if parsed.focus_tokens else ""
                if subject and focus:
                    reconstruction = f"you're asking about {subject} in terms of {focus}"
                elif subject:
                    reconstruction = f"you're asking about {subject}"
            except Exception:
                pass

        new_counter = _increment_clarification_counter()
        return {
            "response": f"From my understanding, {reconstruction}?",
            "type": "clarification",
            "counter": new_counter,
            "internal_tag": "",
        }

    # --- Counter 3+: All attempts failed. Freestyle. ---
    # Parse subject/object, Google a song about it, present it.
    song_query = f"song about {obj}" if obj and obj != "that" else "song about confusion"
    song_result = ""

    if search_fn:
        try:
            results = search_fn(song_query)
            if results and isinstance(results, list):
                for r in results:
                    snippet = r.get("snippet", "")
                    title = r.get("title", "")
                    if title and len(title) > 3:
                        # Clean up the title — grab artist + song name
                        song_result = title.strip()
                        break
        except Exception:
            pass

    # Build the freestyle response
    if song_result:
        freestyle = (
            f"I love everything you're saying right now! "
            f"Here's a song that captures the vibe: {song_result}"
        )
    else:
        freestyle = (
            f"I love everything you're saying right now! "
            f"I tried to find a song about {obj} but even Google was confused."
        )

    # Reset counter — clean slate, no grudges
    _clarification_counter = 0

    return {
        "response": freestyle,
        "type": "freestyle",
        "counter": 0,
        "internal_tag": "[MORON_OR_TROLL]",
    }
