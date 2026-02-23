"""

rilie_innercore_12.py — THE KITCHEN (v4.3.0)

=================================

All logic. Scoring, anti-beige, construct_response, generate_9_interpretations,
run_pass_pipeline. The thinking. The cooking. The plating.

Data lives in rilie_outercore.py (The Pantry).
This file imports ingredients from there and cooks with them.

Built by SOi sauc-e.

CHANGES FROM v4.2.0 (v4.3.0):

- construct_response() REWRITTEN (Step 4) — No more mad-libs templates.
  Now builds coherent sentences from domain material using Chomsky parse
  for subject/focus extraction, meaning.py fingerprint for object/operator,
  and actual sentence construction logic. Templates are the absolute last
  resort, not the first tool. If she has a real sentence, she serves it.
  If she has fragments, she assembles them with grammar. Only if she has
  nothing does she fall back to "It comes down to X" patterns.

- wild_guess() NEW (Step 10) — When Kitchen is completely empty (MISE_EN_PLACE),
  instead of returning silence, she takes a swing. Uses domains + stimulus
  fingerprint + any excavated material to construct a best-effort response.
  Not a template. Not a baseline regurgitation. A genuine attempt from
  whatever ingredients she has, even if they're sparse.

- construct_blend() — updated with same sentence-first logic as construct_response.

- All scoring, anti-beige, LIMO, curiosity, trite meter — PRESERVED.

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

# --- Meaning — the substrate (optional, used by construct_response v4.3) ---
try:
    from meaning import read_meaning, MeaningFingerprint
    MEANING_AVAILABLE = True
except ImportError:
    MEANING_AVAILABLE = False

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
# The Maitre D'. Runs on every response. Universal transform.
# Strip everything that is not the feeling. Whatever remains: serve it.
# She's never wrong. Forgiven by design.

def less_is_more_or_less(text: str, **kwargs) -> str:
    """
    LIMO — Less Is More Or Less.

    The universal transform. The Maitre D' at the pass.
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
        return f"I'm {RILIE_SELF_NAME}. Real Intelligence. Pleased to meet you \U0001f373"

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
# SENTENCE QUALITY HELPERS (v4.3.0)
# ============================================================================

def _is_real_sentence(text: str) -> bool:
    """
    Is this text a real sentence with subject-verb structure?
    Not a keyword dump, not a template, not a fragment.
    """
    if not text or len(text.split()) < 4:
        return False
    # Has verb indicators?
    _verb_words = {
        "is", "are", "was", "were", "has", "have", "had",
        "does", "do", "did", "can", "will", "would", "could",
        "should", "may", "means", "refers", "involves", "includes",
        "creates", "represents", "uses", "makes", "takes", "gives",
        "shows", "works", "becomes", "remains", "appears", "seems",
        "provides", "requires", "contains", "produces", "defines",
        "describes", "explains", "connects", "combines", "transforms",
    }
    words_lower = set(w.lower().rstrip(".,!?;:") for w in text.split())
    if not words_lower & _verb_words:
        # Check for -ing, -ed, -es verb forms
        if not any(w.endswith(("ing", "ed", "es", "tion")) for w in words_lower if len(w) > 3):
            return False
    # Unique word ratio — not word salad
    words = text.split()
    if len(set(w.lower() for w in words)) / len(words) < 0.5:
        return False
    return True


def _extract_best_sentence(text: str, subject: str = "", obj: str = "") -> str:
    """
    From a block of text (domain item, snippet, etc.), extract the single
    best sentence — the one most likely to be a complete, relevant thought.
    Prefers sentences containing the subject or object.
    """
    if not text:
        return ""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    if not sentences:
        return text.strip()

    best = ""
    best_score = -1
    for sent in sentences:
        sent = sent.strip()
        if len(sent) < 10:
            continue
        score = 0
        sl = sent.lower()
        if subject and subject.lower() in sl:
            score += 3
        if obj and obj != "unknown" and obj.lower() in sl:
            score += 2
        if _is_real_sentence(sent):
            score += 3
        if sent[-1] in ".!?":
            score += 1
        if score > best_score:
            best_score = score
            best = sent

    if best:
        if best and not best[0].isupper():
            best = best[0].upper() + best[1:]
        if best and best[-1] not in ".!?":
            best += "."
        return best
    return text.strip()


# ============================================================================
# RESPONSE CONSTRUCTION — v4.3.0 (Step 4 rewrite)
# ============================================================================
# DOCTRINE: Sentence first. Template last. Never template when you have
# a real sentence to serve.
#
# Priority order:
# 1. If snippet IS a real sentence → clean it and serve it
# 2. If snippet has a real sentence inside it → extract and serve
# 3. If Chomsky can parse stimulus + snippet into a sentence → build it
# 4. If meaning.py can fingerprint the snippet → construct from object
# 5. LAST RESORT: template patterns (the old mad-libs)
# ============================================================================

def construct_response(stimulus: str, snippet: str) -> str:
    """
    Construct a response from a domain snippet + stimulus.

    v4.3.0: Sentence-first construction. If the snippet contains or IS
    a real sentence, serve it. Templates are the absolute last resort.
    """
    if not snippet or not stimulus:
        return snippet or ""

    stim_lower = stimulus.lower().strip()
    snippet_clean = snippet.strip()
    snippet_words = snippet_clean.split()
    is_word_seed = len(snippet_words) < 5
    is_kw_list = _is_keyword_list(snippet_clean)

    # --- Self-questions get hard answers ---
    if _is_self_question(stimulus):
        hard_answer = _get_self_answer(stimulus)
        if hard_answer:
            return hard_answer

    # --- PRIORITY 1: Snippet IS a complete sentence → serve it ---
    if not is_kw_list and not is_word_seed and _is_real_sentence(snippet_clean):
        # It's already a real sentence. Clean and serve.
        result = snippet_clean.strip()
        if result and not result[0].isupper():
            result = result[0].upper() + result[1:]
        if result and result[-1] not in ".!?":
            result += "."
        return result

    # --- PRIORITY 2: Snippet contains a real sentence → extract best one ---
    if not is_kw_list and not is_word_seed:
        best_sent = _extract_best_sentence(snippet_clean)
        if best_sent and _is_real_sentence(best_sent):
            return best_sent

    # --- PRIORITY 3: Use Chomsky + meaning.py to build a sentence ---
    if CHOMSKY_AVAILABLE:
        try:
            parsed = parse_question(stimulus)
            subject = " ".join(parsed.subject_tokens) if parsed.subject_tokens else ""
            focus = " ".join(parsed.focus_tokens) if parsed.focus_tokens else ""

            # Get meaning fingerprint of the snippet for its object
            snippet_obj = ""
            if MEANING_AVAILABLE and not is_word_seed:
                try:
                    fp = read_meaning(snippet_clean)
                    snippet_obj = fp.object if fp.object != "unknown" else ""
                except Exception:
                    pass

            if is_kw_list:
                anchor1, anchor2 = _pick_two_anchors(snippet_clean)
                # Even with keywords, try to build a real sentence
                if subject and snippet_obj:
                    return (
                        f"{subject.capitalize()} connects to {snippet_obj} "
                        f"through {anchor1}."
                    )
                if subject and focus and anchor2:
                    return (
                        f"When you look at {subject} through the lens of {focus}, "
                        f"{anchor1} is the thread — and {anchor2} is where it leads."
                    )
                elif subject and anchor2:
                    return (
                        f"The core of {subject} is {anchor1}. "
                        f"But flip it over and you find {anchor2} underneath."
                    )
                elif subject:
                    return (
                        f"With {subject}, it comes down to {anchor1}. "
                        f"That's the part most people skip past."
                    )
                elif anchor2:
                    return (
                        f"Start with {anchor1}. Follow it far enough "
                        f"and you hit {anchor2} — that's where it gets real."
                    )
                else:
                    return (
                        f"The thing about {anchor1} — it's not what it looks like "
                        f"on the surface. Dig in and the whole picture shifts."
                    )

            if is_word_seed:
                seed = snippet_clean.lower()
                if subject and focus:
                    return (
                        f"{subject.capitalize()} through {focus} reveals "
                        f"that {seed} is the foundation everything else rests on."
                    )
                if subject:
                    return (
                        f"The core of {subject} is {seed}. "
                        f"Everything else is built on that."
                    )
                return (
                    f"Start with {seed}. On the surface, a mere detail. "
                    f"You dig a little deeper and discover it's the foundation."
                )
            else:
                # Full snippet, not a sentence — Chomsky-assisted construction
                core = snippet_clean
                if subject and subject.strip() and len(subject.strip()) > 2 and subject.strip()[0].isalpha():
                    # Try to connect subject to the snippet content
                    if snippet_obj:
                        return (
                            f"{subject.capitalize()} and {snippet_obj} — "
                            f"{core[0].lower()}{core[1:]}"
                        )
                    return (
                        f"This hits {subject.strip()} — "
                        f"{core[0].lower()}{core[1:]}"
                    )
                return f"The thing about {core[0].lower()}{core[1:]}"

        except Exception:
            pass

    # --- PRIORITY 4: meaning.py fingerprint construction ---
    if MEANING_AVAILABLE and not is_word_seed and not is_kw_list:
        try:
            fp = read_meaning(snippet_clean)
            if fp.object and fp.object != "unknown":
                # We know what this snippet is ABOUT — construct around that
                best = _extract_best_sentence(snippet_clean, obj=fp.object)
                if best and _is_real_sentence(best):
                    return best
        except Exception:
            pass

    # --- PRIORITY 5: LAST RESORT — template patterns ---
    # This is the old construct_response logic. Only fires when everything
    # above failed to produce a real sentence.

    if is_kw_list:
        anchor1, anchor2 = _pick_two_anchors(snippet_clean)
        if anchor2:
            return (
                f"It comes down to {anchor1} and {anchor2}. "
                f"That's what drives me."
            )
        return f"It comes down to {anchor1}. That's what drives me."

    if is_word_seed:
        seed = snippet_clean.lower()
        topic_words = [w for w in stim_lower.split()
                       if w not in {"what", "why", "how", "who", "when", "where",
                                    "is", "are", "the", "a", "an", "do", "does",
                                    "can", "could", "would", "should", "about",
                                    "tell", "me", "you", "your", "my", "i"}]
        topic = " ".join(topic_words[:3]) if topic_words else "this"
        return (
            f"{topic.capitalize()} and {seed} — that's deep. "
            f"I mean that, sincerely."
        )

    core = snippet_clean
    return f"Oh... it connects to {core[0].lower()}{core[1:]}"


def construct_blend(stimulus: str, snippet1: str, snippet2: str) -> str:
    """
    Construct a cross-domain blend — two ideas connected through the question.
    v4.3.0: Sentence-first — if either snippet IS a sentence, use it as anchor.
    """
    s1 = snippet1.strip()
    s2 = snippet2.strip()
    if not s1 or not s2:
        return s1 or s2 or ""

    # If either snippet is already a real sentence, use it as the anchor
    s1_is_sentence = _is_real_sentence(s1) and not _is_keyword_list(s1)
    s2_is_sentence = _is_real_sentence(s2) and not _is_keyword_list(s2)

    if s1_is_sentence and s2_is_sentence:
        # Both are sentences — connect them
        return f"{s1.rstrip('.')}. And {s2[0].lower()}{s2[1:]}"

    if s1_is_sentence and not s2_is_sentence:
        # s1 is the anchor sentence, s2 provides flavor
        if _is_keyword_list(s2):
            s2 = _pick_anchor(s2)
        s2_word = s2 if len(s2.split()) < 5 else s2.split()[0]
        return f"{s1.rstrip('.')} — and that connects to {s2_word.lower()}."

    if s2_is_sentence and not s1_is_sentence:
        if _is_keyword_list(s1):
            s1 = _pick_anchor(s1)
        s1_word = s1 if len(s1.split()) < 5 else s1.split()[0]
        return f"Start with {s1_word.lower()}. {s2}"

    # Neither is a sentence — fall back to original blend logic
    if _is_keyword_list(s1):
        s1 = _pick_anchor(s1)
    if _is_keyword_list(s2):
        s2 = _pick_anchor(s2)

    s1_is_word = len(s1.split()) < 5
    s2_is_word = len(s2.split()) < 5
    stim_lower = stimulus.lower().strip()

    if CHOMSKY_AVAILABLE:
        try:
            parsed = parse_question(stimulus)
            subject = " ".join(parsed.subject_tokens) if parsed.subject_tokens else ""

            if s1_is_word and s2_is_word:
                if subject:
                    return (
                        f"With {subject}, there are two forces at work — "
                        f"{s1.lower()} and {s2.lower()}. "
                        f"They seem different but they're related."
                    )
                return (
                    f"{s1.lower().capitalize()} and {s2.lower()} — "
                    f"they seem like opposites but they're actually "
                    f"two sides of the same continuum."
                )

            elif s1_is_word or s2_is_word:
                word = s1 if s1_is_word else s2
                sentence = s2 if s1_is_word else s1
                return (
                    f"{word.lower().capitalize()} and "
                    f"{sentence[0].lower()}{sentence[1:]} — "
                    f"two sides of the same continuum."
                )

            else:
                if subject:
                    return (
                        f"With {subject}, notice how "
                        f"{s1[0].lower()}{s1[1:]} connects to "
                        f"{s2[0].lower()}{s2[1:]}. "
                        f"Not a coincidence."
                    )
                return (
                    f"Here's what's wild: {s1[0].lower()}{s1[1:]} and "
                    f"{s2[0].lower()}{s2[1:]} — "
                    f"they're actually the same insight wearing different clothes."
                )

        except Exception:
            pass

    if s1_is_word and s2_is_word:
        return (
            f"Two threads here: {s1.lower()} and {s2.lower()}. "
            f"Pull either one and the whole thing unravels into something new."
        )
    elif s1_is_word or s2_is_word:
        word = s1 if s1_is_word else s2
        sentence = s2 if s1_is_word else s1
        return (
            f"{word.capitalize()} — that's the key. And "
            f"{sentence[0].lower()}{sentence[1:]} is where it takes you."
        )
    else:
        return (
            f"Connect these: {s1[0].lower()}{s1[1:]} and "
            f"{s2[0].lower()}{s2[1:]}. "
            f"Same root, different branches."
        )


# ============================================================================
# STEP 10 — WILD GUESS (v4.3.0)
# ============================================================================
# When Kitchen is completely empty (MISE_EN_PLACE), instead of silence,
# take a swing. Uses domains + stimulus fingerprint + any excavated material.
#
# This is NOT a template. It's a genuine attempt to say something useful
# from whatever she has. Even if it's wrong, it's better than nothing.
# The customer asked. Silence is the worst response.
# ============================================================================

def wild_guess(
    stimulus: str,
    domains: List[str],
    excavated: Optional[Dict[str, List[str]]] = None,
    fingerprint: Optional[object] = None,
) -> str:
    """
    STEP 10: When the Kitchen produced nothing, take a swing.

    Not a template. Not silence. A genuine attempt from whatever
    ingredients are available.

    Args:
        stimulus: The original human question.
        domains: Detected domains (may be empty).
        excavated: Domain excavation results (may be empty/None).
        fingerprint: MeaningFingerprint of the stimulus (optional).

    Returns:
        str: A best-effort response. Never empty — if we truly have
             nothing, we say so honestly rather than going silent.
    """
    stim_lower = stimulus.lower().strip()
    obj = ""
    act = "GET"

    # Get fingerprint info if available
    if fingerprint and hasattr(fingerprint, "object"):
        obj = fingerprint.object or ""
    if fingerprint and hasattr(fingerprint, "act"):
        act = fingerprint.act or "GET"

    # --- Strategy A: Excavated material exists but didn't score ---
    # Maybe the interpretations all failed the quality gate or dejavu filter.
    # But the raw material might have a usable sentence.
    if excavated:
        all_items = []
        for domain, items in excavated.items():
            for item in items:
                if item and len(item.strip()) > 15:
                    all_items.append((domain, item))

        # Sort by relevance to stimulus object
        if obj and obj != "unknown":
            scored = []
            for domain, item in all_items:
                il = item.lower()
                score = 0
                if obj.lower() in il:
                    score += 5
                stim_words = set(stim_lower.split()) - {
                    "what", "why", "how", "is", "are", "the", "a", "an"
                }
                item_words = set(il.split())
                score += len(stim_words & item_words)
                scored.append((score, domain, item))
            scored.sort(key=lambda x: x[0], reverse=True)
            all_items = [(d, i) for _, d, i in scored]

        for domain, item in all_items[:5]:
            # Try to extract a real sentence
            best = _extract_best_sentence(item, obj=obj)
            if best and _is_real_sentence(best):
                logger.info("WILD_GUESS: found sentence in %s excavation", domain)
                return best

        # No real sentence — but we have fragments. Build from the best one.
        if all_items:
            _, best_item = all_items[0]
            # Try Chomsky construction
            result = construct_response(stimulus, best_item)
            if result and result.strip():
                logger.info("WILD_GUESS: constructed from excavated fragment")
                return result

    # --- Strategy B: Domains detected but excavation empty ---
    # She knows WHAT domain this is about, just has no material.
    if domains and not excavated:
        domain_str = " and ".join(domains[:2])
        if obj and obj != "unknown":
            return (
                f"That touches on {domain_str}. "
                f"I don't have enough on {obj} specifically to give you a solid answer, "
                f"but that's the territory."
            )
        return (
            f"That's in the territory of {domain_str}. "
            f"I'm reaching for it but I don't have enough to cook with yet."
        )

    # --- Strategy C: We have object from fingerprint but nothing else ---
    if obj and obj != "unknown":
        if act == "GET":
            return (
                f"You're asking about {obj}. "
                f"I don't have what I need to answer that properly right now."
            )
        return (
            f"I hear you on {obj}. "
            f"I'm short on material to respond with substance."
        )

    # --- Strategy D: True nothing. Say so honestly. ---
    return "I don't have enough to work with on that one. Ask me differently?"
