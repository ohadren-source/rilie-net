"""
rilie_innercore.py — THE KITCHEN
=================================
All logic. Scoring, anti-beige, construct_response, generate_9_interpretations,
run_pass_pipeline. The thinking. The cooking. The plating.

Data lives in rilie_outercore.py (The Pantry).
This file imports ingredients from there and cooks with them.

Built by SOi sauc-e.

v2.1 SURGERY (drain-capping):
  FIX 1 — COMPRESSED gate removed for UNKNOWN; only CHOICE/DEFINITION compress early.
  FIX 2 — Template strings added to _CANNED_MARKERS so they score 0.5× not 3.0×.
  FIX 3 — QuestionType.FACTUAL added; factual/list questions route to BASELINE_WIN.
  FIX 4 — Chomsky subject sanitized; function words rejected as subjects in construct_response.
  FIX 5 — Baseline advantage raised to 1.4× for FACTUAL questions.
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

# ============================================================================
# CURIOSITY CONTEXT
# ============================================================================

def extract_curiosity_context(stimulus: str) -> Optional[str]:
    marker = "[Own discovery:"
    if stimulus.startswith(marker):
        end = stimulus.find("]")
        if end > 0:
            return stimulus[len(marker):end].strip()
    return None

def strip_curiosity_context(stimulus: str) -> str:
    marker = "[Own discovery:"
    if stimulus.startswith(marker):
        sep = stimulus.find("\n\n")
        if sep > 0:
            return stimulus[sep + 2:].strip()
    return stimulus

# ============================================================================
# QUESTION TYPE
# FIX 3: Added FACTUAL enum — list/name/lookup questions route to baseline
# ============================================================================

class QuestionType(Enum):
    CHOICE      = "choice"
    DEFINITION  = "definition"
    EXPLANATION = "explanation"
    FACTUAL     = "factual"
    UNKNOWN     = "unknown"

# Signals that a question wants a factual list or lookup answer
_FACTUAL_SIGNALS = [
    "can you name", "name some", "name a few", "name the",
    "list some", "list the", "list a few",
    "give me some", "give me a list", "give me examples",
    "what are some", "what are the", "who are some", "who are the",
    "can you list", "do you know any", "any examples",
    "look them up", "look it up", "search for",
]

def detect_question_type(stimulus: str) -> QuestionType:
    s = (stimulus or "").strip().lower()
    # FACTUAL check first — must run before UNKNOWN catch-all
    if any(sig in s for sig in _FACTUAL_SIGNALS):
        return QuestionType.FACTUAL
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
    global _current_trite_score
    _current_trite_score = score

def set_curiosity_bonus(bonus: float) -> None:
    global _current_curiosity_bonus
    _current_curiosity_bonus = min(0.3, max(0.0, bonus))

def anti_beige_check(text: str) -> float:
    text_lower = (text or "").lower()

    hard_reject = [
        "copy of a copy",
        "every day is exactly the same",
        "autopilot",
    ]
    if any(signal in text_lower for signal in hard_reject):
        return 0.0

    originality_signals  = ["original", "fresh", "new", "unique", "unprecedented", "never"]
    authenticity_signals = ["genuine", "real", "true", "honest", "brutal", "earned"]
    depth_signals        = ["master", "craft", "skill", "proficiency", "expertise"]
    effort_signals       = ["earnest", "work", "struggle", "build", "foundation"]
    reflection_signals   = ["reflect", "mirror", "light", "show", "demonstrate"]
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
    "amusing":       score_amusing,
    "insightful":    score_insightful,
    "nourishing":    score_nourishing,
    "compassionate": score_compassionate,
    "strategic":     score_strategic,
}

WEIGHTS = {
    "amusing":       PRIORITY_HIERARCHY["1_amusing"]["weight"],
    "insightful":    PRIORITY_HIERARCHY["2_insightful"]["weight"],
    "nourishing":    PRIORITY_HIERARCHY["3_nourishing"]["weight"],
    "compassionate": PRIORITY_HIERARCHY["4_compassionate"]["weight"],
    "strategic":     PRIORITY_HIERARCHY["5_strategic"]["weight"],
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
    parts = [p.strip() for p in snippet.split(",") if p.strip()]
    if not parts:
        return snippet.strip()
    multi = [p for p in parts if len(p.split()) >= 2]
    if multi:
        return random.choice(multi[:3])
    return parts[0]

def _pick_two_anchors(snippet: str) -> tuple:
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
    "name":    RILIE_SELF_NAME,
    "made_by": RILIE_MADE_BY,
    "purpose": "Real Intelligence. She thinks, she cooks, she serves.",
}

def _is_self_question(stimulus: str) -> bool:
    s = stimulus.lower().strip()
    return any(sig in s for sig in _SELF_SIGNALS)

def _get_self_answer(stimulus: str) -> Optional[str]:
    s = stimulus.lower().strip()
    if any(sig in s for sig in ["who made", "who built", "who created", "who designed",
                                 "who programmed", "who developed", "who wrote you"]):
        return f"I was built by {RILIE_MADE_BY}. Real Intelligence, cooked from scratch."
    if "your name" in s or ("what" in s and "name" in s and "you" in s):
        return f"I'm {RILIE_SELF_NAME}. Real Intelligence. Pleased to meet you 🍳"
    if (("difference" in s or "vs" in s or "versus" in s or "compare" in s) and
            any(ai in s for ai in ["chatgpt", "gpt", "claude", "gemini", "ai", "chatbot"])):
        return (
            f"{RILIE_SELF_NAME} doesn't retrieve. She thinks. "
            f"Every response is cooked — scored on five dimensions, "
            f"anti-beige checked, domain-excavated. "
            f"ChatGPT serves what's popular. {RILIE_SELF_NAME} serves what's true."
        )
    return None

# ============================================================================
# SUBJECT SANITIZER
# FIX 4: Reject function words / pronouns as Chomsky subjects in construct_response.
# If subject is a junk word, extract content topic directly from stimulus instead.
# ============================================================================

_JUNK_SUBJECTS = {
    "i", "you", "we", "they", "he", "she", "it", "me", "us", "them",
    "like", "just", "get", "go", "do", "be", "have", "say", "make",
    "rilie", "that", "this", "there", "here", "what", "who", "which",
}

def _extract_content_subject(stimulus: str) -> str:
    """
    Fallback subject extractor: grab the most meaningful content noun
    from the stimulus when Chomsky returns a junk subject.
    Skips stopwords, question words, and short tokens.
    Returns '' if nothing useful found.
    """
    STOPWORDS = {
        "what", "why", "how", "who", "when", "where", "is", "are", "the",
        "a", "an", "do", "does", "can", "could", "would", "should", "about",
        "tell", "me", "you", "your", "my", "i", "we", "they", "it", "he",
        "she", "and", "or", "but", "for", "to", "of", "in", "on", "at",
        "with", "like", "just", "now", "yes", "no", "ok", "okay", "please",
        "some", "any", "that", "this", "have", "had", "has", "be", "been",
        "them", "us", "so", "if", "up", "out", "as", "by", "from", "into",
    }
    words = re.sub(r"[^A-Za-z0-9\s]", " ", stimulus).split()
    for w in words:
        if len(w) > 2 and w.lower() not in STOPWORDS:
            return w
    return ""

def _sanitize_subject(subject: str, stimulus: str) -> str:
    """
    Returns subject if it's a real content word.
    Falls back to _extract_content_subject if it's junk.
    """
    if not subject or subject.lower().strip() in _JUNK_SUBJECTS:
        return _extract_content_subject(stimulus)
    return subject

# ============================================================================
# RESPONSE CONSTRUCTION
# ============================================================================

def construct_response(stimulus: str, snippet: str) -> str:
    if not snippet or not stimulus:
        return snippet or ""

    stim_lower     = stimulus.lower().strip()
    snippet_clean  = snippet.strip()
    snippet_words  = snippet_clean.split()
    is_word_seed   = len(snippet_words) < 5
    is_kw_list     = _is_keyword_list(snippet_clean)

    # --- SELF-AWARENESS GATE ---
    if _is_self_question(stimulus):
        hard_answer = _get_self_answer(stimulus)
        if hard_answer:
            return hard_answer
        if is_kw_list:
            anchor1, anchor2 = _pick_two_anchors(snippet_clean)
            if anchor2:
                return f"It comes down to {anchor1} and {anchor2}. That's what drives me."
            return f"It comes down to {anchor1}. That's what drives me."
        if is_word_seed:
            seed = snippet_clean.lower()
            return f"For me it's {seed}. Everything else is built on that."
        return snippet_clean

    # --- KEYWORD LIST PATH ---
    if is_kw_list:
        anchor1, anchor2 = _pick_two_anchors(snippet_clean)
        if CHOMSKY_AVAILABLE:
            try:
                parsed  = parse_question(stimulus)
                raw_sub = " ".join(parsed.subject_tokens) if parsed.subject_tokens else ""
                subject = _sanitize_subject(raw_sub, stimulus)  # FIX 4
                focus   = " ".join(parsed.focus_tokens) if parsed.focus_tokens else ""

                if subject and focus and anchor2:
                    return (
                        f"When it comes to {subject}, {anchor1} is the thread "
                        f"— and {anchor2} is where it leads."
                    )
                elif subject and anchor2:
                    return (
                        f"The core of {subject} is {anchor1}. "
                        f"Flip it over and you find {anchor2} underneath."
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
            except Exception:
                pass

        # No Chomsky fallback for keyword lists
        topic_words = [w for w in stim_lower.split()
                       if w not in {"what", "why", "how", "who", "when", "where",
                                    "is", "are", "the", "a", "an", "do", "does",
                                    "can", "could", "would", "should", "about",
                                    "tell", "me", "you", "your", "my", "i"}]
        topic = " ".join(topic_words[:3]) if topic_words else "this"
        if anchor2:
            return (
                f"With {topic}, think about {anchor1} — "
                f"then notice how {anchor2} changes the whole equation."
            )
        return f"The heart of {topic} is {anchor1}. Everything else orbits around that."

    # --- WORD SEED + FULL SENTENCE PATH ---
    if CHOMSKY_AVAILABLE:
        try:
            parsed  = parse_question(stimulus)
            raw_sub = " ".join(parsed.subject_tokens) if parsed.subject_tokens else ""
            subject = _sanitize_subject(raw_sub, stimulus)  # FIX 4
            focus   = " ".join(parsed.focus_tokens) if parsed.focus_tokens else ""

            if is_word_seed:
                seed = snippet_clean.lower()
                if subject and focus:
                    return (
                        f"{subject.capitalize()} — when you focus on {focus}, "
                        f"{seed} stops being background noise and becomes the whole signal."
                    )
                if subject:
                    return (
                        f"The core of {subject} is {seed}. "
                        f"It's all about essence, ain't it?"
                    )
                return (
                    f"Start with {seed}. On the surface, a mere detail. "
                    f"Dig a little deeper and it's the foundation :)"
                )
            else:
                core = snippet_clean
                if subject and subject.strip() and len(subject.strip()) > 2 and subject.strip()[0].isalpha():
                    return (
                        f"This hits on {subject.strip()}... "
                        f"{core[0].lower()}{core[1:]} — worth exploring if you're game"
                    )
                return f"The thing about {core[0].lower()}{core[1:]}"
        except Exception:
            pass

    # --- No Chomsky fallback ---
    if is_word_seed:
        seed = snippet_clean.lower()
        topic_words = [w for w in stim_lower.split()
                       if w not in {"what", "why", "how", "who", "when", "where",
                                    "is", "are", "the", "a", "an", "do", "does",
                                    "can", "could", "would", "should", "about",
                                    "tell", "me", "you", "your", "my", "i"}]
        topic = " ".join(topic_words[:3]) if topic_words else "this"
        return f"Interesting... {topic}... {seed}... that's deep. I mean that, sincerely."

    core = snippet_clean
    return f"Oh... it connects to {core[0].lower()}{core[1:]}"


def construct_blend(stimulus: str, snippet1: str, snippet2: str) -> str:
    s1 = snippet1.strip()
    s2 = snippet2.strip()
    if not s1 or not s2:
        return s1 or s2 or ""

    if _is_keyword_list(s1):
        s1 = _pick_anchor(s1)
    if _is_keyword_list(s2):
        s2 = _pick_anchor(s2)

    s1_is_word = len(s1.split()) < 5
    s2_is_word = len(s2.split()) < 5

    if CHOMSKY_AVAILABLE:
        try:
            parsed  = parse_question(stimulus)
            raw_sub = " ".join(parsed.subject_tokens) if parsed.subject_tokens else ""
            subject = _sanitize_subject(raw_sub, stimulus)  # FIX 4

            if s1_is_word and s2_is_word:
                if subject:
                    return (
                        f"With {subject}, there are two forces at work — "
                        f"{s1.lower()} and {s2.lower()}. "
                        f"They seem different but they're related... huh..."
                    )
                return (
                    f"That tracks... {s1.lower()} and {s2.lower()} "
                    f"seem like opposites at first and then you realize "
                    f"they're actually 2 sides of the same continuum. "
                    f"Light bulb went off/on hehe 💡!"
                )
            elif s1_is_word or s2_is_word:
                word     = s1 if s1_is_word else s2
                sentence = s2 if s1_is_word else s1
                return (
                    f"That tracks... {word.lower()} and "
                    f"{sentence[0].lower()}{sentence[1:]} "
                    f"seem like opposites at first and then you realize "
                    f"they're actually 2 sides of the same continuum. "
                    f"Light bulb went off/on hehe 💡!"
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

    # No Chomsky fallback
    if s1_is_word and s2_is_word:
        return (
            f"Two threads here: {s1.lower()} and {s2.lower()}. "
            f"Pull either one and the whole thing unravels into something new."
        )
    elif s1_is_word or s2_is_word:
        word     = s1 if s1_is_word else s2
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
# DOMAIN DETECTION & EXCAVATION
# ============================================================================

def detect_domains(stimulus: str) -> List[str]:
    sl = (stimulus or "").lower()
    scores = {
        d: sum(1 for kw in kws if kw in sl)
        for d, kws in DOMAIN_KEYWORDS.items()
    }
    if CHOMSKY_AVAILABLE:
        try:
            trinity = extract_holy_trinity_for_roux(stimulus)
            for word in trinity:
                wl = word.lower()
                for d, kws in DOMAIN_KEYWORDS.items():
                    if any(wl in kw or kw in wl for kw in kws):
                        scores[d] = scores.get(d, 0) + 2
        except Exception:
            pass
    ordered = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [d for d, _ in ordered[:4] if d in DOMAIN_KNOWLEDGE]

def excavate_domains(stimulus: str, domains: List[str]) -> Dict[str, List[str]]:
    sl = (stimulus or "").lower()
    excavated: Dict[str, List[str]] = {}
    for domain in domains:
        if domain not in DOMAIN_KNOWLEDGE:
            excavated[domain] = []
            continue
        sub_items: List[tuple] = []
        for sub_key, items in DOMAIN_KNOWLEDGE[domain].items():
            sub_relevance = 1 if sub_key.lower() in sl else 0
            for item in items:
                item_words  = set(item.lower().split())
                stim_words  = set(sl.split())
                word_overlap = len(item_words & stim_words)
                score = sub_relevance * 2 + word_overlap
                sub_items.append((score, item))
        if sub_items:
            sub_items.sort(key=lambda x: x[0], reverse=True)
            top       = [item for _, item in sub_items[:4]]
            remaining = [item for _, item in sub_items[4:]]
            if remaining:
                top.append(random.choice(remaining))
            excavated[domain] = top
        else:
            excavated[domain] = []

    # Word enrichment
    for domain, items in excavated.items():
        enriched = []
        for item in items:
            if len(item.split()) < 5:
                word       = item.strip().lower()
                definition = WORD_DEFINITIONS.get(word, "")
                synonyms   = WORD_SYNONYMS.get(word, [])
                homonyms   = WORD_HOMONYMS.get(word, [])
                parts      = [item]
                if definition:
                    parts.append(definition)
                if synonyms:
                    parts.append("also: " + ", ".join(synonyms[:4]))
                if homonyms:
                    parts.append("other meanings: " + "; ".join(homonyms[:3]))
                enriched.append(" — ".join(parts))
            else:
                enriched.append(item)
        excavated[domain] = enriched
    return excavated

# ============================================================================
# INTERPRETATION GENERATION
# ============================================================================

# FIX 2: Expanded _CANNED_MARKERS to include the actual template strings
# that were scoring 3.0× (generated) when they should score 0.5× (canned).
_CANNED_MARKERS = [
    # original markers
    "the way i understand it",
    "the way i see it",
    "what it comes down to",
    "the thing about",
    "what makes",
    "the reason is",
    "the way it works",
    "the person behind",
    "what happened with",
    "goes from here",
    # FIX 2: template strings produced by construct_response / construct_blend
    "when you look at",
    "when it comes to",
    "this hits on",
    "this hits rilie",
    "this hits they",
    "this hits ",
    "gotcha.. ",
    "gotcha you",
    "let's explore",
    "through the lens of",
    "that tracks...",
    "light bulb went off",
    "two threads here",
    "pull either one",
    "here's what's wild",
    "they're actually the same insight",
    "same root, different branches",
    "not a coincidence",
]

def _originality_multiplier(text: str, domain: str) -> float:
    """Generated > Searched > Canned. Always."""
    t = text.lower().strip()
    # FIX 2: check contains as well as startswith for mid-string templates
    is_canned = any(t.startswith(marker) or marker in t for marker in _CANNED_MARKERS)
    if is_canned:
        return 0.5
    if domain.startswith("roux") or "[roux:" in t:
        return 2.0
    if "_" in domain and domain.count("_") >= 1:
        return 2.5
    return 3.0

def generate_9_interpretations(
    stimulus: str,
    excavated: Dict[str, List[str]],
    depth: int,
    domains: Optional[List[str]] = None,
) -> List[Interpretation]:
    """Generate up to 9 internal candidate interpretations."""

    stimulus_domains = set(domains) if domains else set()

    try:
        from guvna import detect_tone_from_stimulus
        stimulus_tone = detect_tone_from_stimulus(stimulus)
    except ImportError:
        stimulus_tone = "insightful"

    _TONE_WORDS = {
        "amusing":       {"funny", "humor", "laugh", "joke", "absurd", "ironic", "haha", "lol"},
        "insightful":    {"because", "reason", "means", "actually", "truth", "real", "works"},
        "nourishing":    {"grow", "learn", "build", "create", "teach", "develop", "nurture"},
        "compassionate": {"feel", "hurt", "care", "understand", "hear", "support", "sorry"},
        "strategic":     {"plan", "move", "step", "leverage", "position", "execute", "next"},
    }

    def _relevance_score(text: str, domain: str) -> float:
        response_domains = set()
        if domain:
            for d in domain.split("_"):
                response_domains.add(d)
        domain_overlap = len(response_domains & stimulus_domains)
        if domain_overlap == 0 and stimulus_domains:
            domain_score = 0.1
        elif domain_overlap == 1:
            domain_score = 0.6
        elif domain_overlap >= 2:
            domain_score = 1.0
        else:
            domain_score = 0.3
        t_lower    = text.lower()
        tone_words = _TONE_WORDS.get(stimulus_tone, set())
        tone_hits  = sum(1 for tw in tone_words if tw in t_lower)
        tone_score = min(1.0, tone_hits * 0.25)
        return (domain_score * 0.7) + (tone_score * 0.3)

    def _resonance_score(text: str) -> float:
        stim_words      = len(stimulus.split())
        stim_questions  = stimulus.count("?")
        challenge       = min(1.0, (stim_words / 30) + (stim_questions * 0.2))
        resp_words      = len(text.split())
        resp_has_struct = 1.0 if any(c in text for c in ["—", ":", ";"]) else 0.0
        skill           = min(1.0, (resp_words / 40) + (resp_has_struct * 0.1))
        gap             = abs(skill - challenge)
        return max(0.1, 1.0 - gap)

    def _final_score(raw_overall: float, text: str, domain: str) -> float:
        orig  = _originality_multiplier(text, domain)
        relev = _relevance_score(text, domain)
        reson = _resonance_score(text)
        return raw_overall * orig * relev * reson

    interpretations: List[Interpretation] = []
    idx = 0

    for domain, items in excavated.items():
        for item in items[:4]:
            text  = construct_response(stimulus, item)
            anti  = anti_beige_check(text)
            scores = {k: fn(text) for k, fn in SCORERS.items()}
            count  = sum(1 for v in scores.values() if v > 0.3)
            raw_overall = sum(scores[k] * WEIGHTS[k] for k in scores) / 4.5
            overall     = _final_score(raw_overall, text, domain)
            interpretations.append(
                Interpretation(
                    id=depth * 1000 + idx,
                    text=text,
                    domain=domain,
                    quality_scores=scores,
                    overall_score=overall,
                    count_met=count,
                    anti_beige_score=anti,
                    depth=depth,
                )
            )
            idx += 1

    attempts    = 0
    domain_keys = list(excavated.keys())
    while len(interpretations) < 9 and attempts < 20:
        attempts += 1
        if len(domain_keys) < 2:
            break
        d1 = random.choice(domain_keys)
        d2 = random.choice(domain_keys)
        if d1 == d2:
            continue
        if not excavated.get(d1) or not excavated.get(d2):
            continue
        i1   = random.choice(excavated[d1])
        i2   = random.choice(excavated[d2])
        text = construct_blend(stimulus, i1, i2)
        anti = anti_beige_check(text)
        scores = {k: fn(text) for k, fn in SCORERS.items()}
        count  = sum(1 for v in scores.values() if v > 0.3)
        raw_overall  = sum(scores[k] * WEIGHTS[k] for k in scores) / 4.5
        blend_domain = f"{d1}_{d2}"
        overall      = _final_score(raw_overall, text, blend_domain)
        interpretations.append(
            Interpretation(
                id=depth * 1000 + idx,
                text=text,
                domain=blend_domain,
                quality_scores=scores,
                overall_score=overall,
                count_met=count,
                anti_beige_score=anti,
                depth=depth,
            )
        )
        idx += 1

    return interpretations[:9]

# ============================================================================
# PASS PIPELINE
# ============================================================================

def run_pass_pipeline(
    stimulus: str,
    disclosure_level: str,
    max_pass: int = 3,
    baseline_results: Optional[List[Dict[str, str]]] = None,
    prior_responses: Optional[List[str]] = None,
    baseline_text: str = "",
) -> Dict:
    """
    Run interpretation passes. Called only at OPEN or FULL disclosure.

    LEAN 3-STEP PIPELINE:
      1. Google baseline arrives via baseline_text (from Guvna)
      2. Internal domain match + SOi comparison runs here
      3. Best score wins — baseline or Kitchen candidate

    ANTI-DÉJÀ-VU GATE:
      Any candidate too similar to her own recent responses is rejected.
    """

    curiosity_ctx  = extract_curiosity_context(stimulus)
    clean_stimulus = strip_curiosity_context(stimulus)

    trite = compute_trite_score(baseline_results)
    set_trite_score(trite)

    if curiosity_ctx:
        set_curiosity_bonus(0.15)
    else:
        set_curiosity_bonus(0.0)

    question_type = detect_question_type(clean_stimulus)
    domains       = detect_domains(clean_stimulus)

    # FIX 3: FACTUAL questions → go straight to baseline if we have one
    if question_type == QuestionType.FACTUAL and baseline_text:
        clean_bl = _clean_baseline_text(baseline_text)
        if clean_bl:
            bl_scores   = {k: fn(clean_bl) for k, fn in SCORERS.items()}
            bl_overall  = sum(bl_scores[k] * WEIGHTS[k] for k in bl_scores) / 4.5
            bl_overall *= 1.4  # FIX 5: strong baseline advantage for factual
            debug_audit = _build_debug_audit(
                clean_stimulus, domains, None, [], [], [],
                "BASELINE_WIN"
            )
            return {
                "stimulus":         clean_stimulus,
                "result":           clean_bl,
                "quality_score":    bl_overall,
                "priorities_met":   sum(1 for v in bl_scores.values() if v > 0.3),
                "anti_beige_score": anti_beige_check(clean_bl),
                "status":           "BASELINE_WIN",
                "depth":            0,
                "pass":             1,
                "disclosure_level": disclosure_level,
                "trite_score":      trite,
                "curiosity_informed": bool(curiosity_ctx),
                "domains_used":     domains,
                "domain":           "google_baseline",
                "debug_audit":      debug_audit,
            }

    # Anti-déjà-vu
    _prior_word_sets: List[set] = []
    if prior_responses:
        for pr in prior_responses[-5:]:
            words = set(re.sub(r"[^a-zA-Z0-9\s]", "", pr.lower()).split())
            _prior_word_sets.append(words)

    def _is_dejavu(candidate_text: str) -> bool:
        if not _prior_word_sets or not candidate_text:
            return False
        cand_words = set(re.sub(r"[^a-zA-Z0-9\s]", "", candidate_text.lower()).split())
        if len(cand_words) < 3:
            return False
        for prior_words in _prior_word_sets:
            if not prior_words:
                continue
            overlap = cand_words & prior_words
            smaller = min(len(cand_words), len(prior_words))
            if smaller > 0 and len(overlap) / smaller > 0.6:
                return True
        return False

    excavated = excavate_domains(clean_stimulus, domains)

    # ROUX INJECTION
    roux_match = re.match(r"\[ROUX:\s*(.*?)\]\s*\n", clean_stimulus, re.DOTALL)
    if roux_match:
        roux_text = roux_match.group(1).strip()
        if roux_text:
            roux_items = [s.strip() for s in re.split(r'[.!?]+', roux_text)
                          if s.strip() and len(s.strip()) > 10]
            if roux_items:
                excavated["roux"] = roux_items[:5]
        clean_stimulus = re.sub(r"\[ROUX:.*?\]\s*\n*", "", clean_stimulus, flags=re.DOTALL).strip()

    # SOi DOMAIN MAP
    try:
        from soi_domain_map import get_human_wisdom, DOMAIN_INDEX
        soi_domains = [d for d in domains if d in DOMAIN_INDEX]
        sl = clean_stimulus.lower()
        for soi_domain in DOMAIN_INDEX:
            if soi_domain in sl and soi_domain not in soi_domains:
                soi_domains.append(soi_domain)
        if soi_domains:
            wisdom = get_human_wisdom(soi_domains, max_tracks=6)
            if wisdom:
                if "catch44" in excavated:
                    excavated["catch44"].extend(wisdom)
                else:
                    excavated["catch44"] = wisdom
    except ImportError:
        pass

    hard_cap = 3
    max_pass = max(1, min(max_pass, hard_cap))
    if disclosure_level == "open":
        max_pass = min(max_pass, 3)

    best_global: Optional[Interpretation] = None
    _debug_all_candidates: List[Dict] = []
    _debug_dejavu_killed:  List[Dict] = []
    _debug_passes:         List[Dict] = []

    for current_pass in range(1, max_pass + 1):
        depth = current_pass - 1
        nine  = generate_9_interpretations(clean_stimulus, excavated, depth, domains=domains)

        if not nine:
            _debug_passes.append({"pass": current_pass, "candidates": 0, "note": "empty"})
            continue

        pass_candidates = []
        for i in nine:
            dejavu = _is_dejavu(i.text)
            entry  = {
                "id":            i.id,
                "domain":        i.domain,
                "text":          i.text[:120],
                "overall_score": round(i.overall_score, 4),
                "count_met":     i.count_met,
                "anti_beige":    round(i.anti_beige_score, 3),
                "dejavu_blocked": dejavu,
            }
            pass_candidates.append(entry)
            _debug_all_candidates.append(entry)
            if dejavu:
                _debug_dejavu_killed.append(entry)

        filtered = [
            i for i in nine
            if (i.overall_score > (0.06 if current_pass == 1 else 0.09)
                or i.count_met >= 1)
            and not _is_dejavu(i.text)
        ]

        if not filtered and nine:
            def _dejavu_score(text: str) -> float:
                if not _prior_word_sets or not text:
                    return 0.0
                cand_words = set(re.sub(r"[^a-zA-Z0-9\s]", "", text.lower()).split())
                if len(cand_words) < 3:
                    return 0.0
                best_overlap = 0.0
                for pw in _prior_word_sets:
                    if not pw:
                        continue
                    overlap = cand_words & pw
                    smaller = min(len(cand_words), len(pw))
                    if smaller > 0:
                        best_overlap = max(best_overlap, len(overlap) / smaller)
                return best_overlap
            ranked   = sorted(nine, key=lambda x: _dejavu_score(x.text))
            filtered = [ranked[0]]

        _debug_passes.append({
            "pass":             current_pass,
            "candidates":       len(nine),
            "survived_filter":  len(filtered),
            "dejavu_killed":    sum(1 for c in pass_candidates if c["dejavu_blocked"]),
        })

        if filtered:
            best = max(filtered, key=lambda x: (x.count_met, x.overall_score))
        else:
            best = max(nine, key=lambda x: x.overall_score)

        if (best_global is None) or (best.overall_score > best_global.overall_score):
            best_global = best

        # FIX 1: COMPRESSED only for CHOICE and DEFINITION — NOT UNKNOWN.
        # UNKNOWN questions need full passes; they're the creative territory.
        if current_pass <= 2 and question_type in {
            QuestionType.CHOICE,
            QuestionType.DEFINITION,
        }:
            debug_audit = _build_debug_audit(
                clean_stimulus, domains, best, _debug_all_candidates,
                _debug_dejavu_killed, _debug_passes, "COMPRESSED"
            )
            return {
                "stimulus":         clean_stimulus,
                "result":           best.text,
                "quality_score":    best.overall_score,
                "priorities_met":   best.count_met,
                "anti_beige_score": best.anti_beige_score,
                "status":           "COMPRESSED",
                "depth":            depth,
                "pass":             current_pass,
                "disclosure_level": disclosure_level,
                "trite_score":      trite,
                "curiosity_informed": bool(curiosity_ctx),
                "domains_used":     domains,
                "domain":           best.domain,
                "debug_audit":      debug_audit,
            }

    # ==================================================================
    # FINAL TALLY — baseline is the bar to beat
    # ==================================================================

    def _clean_baseline_text(bl: str) -> str:
        if not bl:
            return ""
        import html
        bl = html.unescape(bl)
        bl = re.sub(r"<[^>]+>", "", bl)
        bl = re.sub(r"\s+", " ", bl).strip()
        if len(bl) > 300:
            bl = bl[:300]
            for sep in [". ", "! ", "? "]:
                idx = bl.rfind(sep)
                if idx > 50:
                    bl = bl[:idx + 1]
                    break
            else:
                bl = bl.rsplit(" ", 1)[0]
        return bl

    if best_global is not None:
        best_score = best_global.overall_score
        clean_bl   = _clean_baseline_text(baseline_text)

        if clean_bl:
            bl_scores  = {k: fn(clean_bl) for k, fn in SCORERS.items()}
            bl_overall = sum(bl_scores[k] * WEIGHTS[k] for k in bl_scores) / 4.5
            bl_overall *= 1.03  # Standard 3% baseline edge

            if bl_overall > best_score:
                debug_audit = _build_debug_audit(
                    clean_stimulus, domains, best_global, _debug_all_candidates,
                    _debug_dejavu_killed, _debug_passes, "BASELINE_WIN"
                )
                return {
                    "stimulus":         clean_stimulus,
                    "result":           clean_bl,
                    "quality_score":    bl_overall,
                    "priorities_met":   sum(1 for v in bl_scores.values() if v > 0.3),
                    "anti_beige_score": anti_beige_check(clean_bl),
                    "status":           "BASELINE_WIN",
                    "depth":            0,
                    "pass":             max_pass,
                    "disclosure_level": disclosure_level,
                    "trite_score":      trite,
                    "curiosity_informed": bool(curiosity_ctx),
                    "domains_used":     domains,
                    "domain":           "google_baseline",
                    "debug_audit":      debug_audit,
                }

        # Kitchen beat the baseline (or no baseline)
        debug_audit = _build_debug_audit(
            clean_stimulus, domains, best_global, _debug_all_candidates,
            _debug_dejavu_killed, _debug_passes, "GUESS"
        )
        return {
            "stimulus":         clean_stimulus,
            "result":           best_global.text,
            "quality_score":    best_global.overall_score,
            "priorities_met":   best_global.count_met,
            "anti_beige_score": best_global.anti_beige_score,
            "status":           "GUESS",
            "depth":            best_global.depth,
            "pass":             max_pass,
            "disclosure_level": disclosure_level,
            "trite_score":      trite,
            "curiosity_informed": bool(curiosity_ctx),
            "domains_used":     domains,
            "domain":           best_global.domain,
            "debug_audit":      debug_audit,
        }

    # Absolute fallback
    clean_bl = _clean_baseline_text(baseline_text)
    if clean_bl:
        debug_audit = _build_debug_audit(
            clean_stimulus, domains, None, _debug_all_candidates,
            _debug_dejavu_killed, _debug_passes, "BASELINE_FALLBACK"
        )
        return {
            "stimulus":         clean_stimulus,
            "result":           clean_bl,
            "quality_score":    0.3,
            "priorities_met":   0,
            "anti_beige_score": 0.5,
            "status":           "BASELINE_FALLBACK",
            "depth":            0,
            "pass":             max_pass,
            "disclosure_level": disclosure_level,
            "trite_score":      trite,
            "curiosity_informed": bool(curiosity_ctx),
            "domains_used":     domains,
            "domain":           "google_baseline",
            "debug_audit":      debug_audit,
        }

    debug_audit = _build_debug_audit(
        clean_stimulus, domains, None, _debug_all_candidates,
        _debug_dejavu_killed, _debug_passes, "MISE_EN_PLACE"
    )
    return {
        "stimulus":         clean_stimulus,
        "result":           "",
        "quality_score":    0.0,
        "priorities_met":   0,
        "anti_beige_score": 0.0,
        "status":           "MISE_EN_PLACE",
        "depth":            max_pass - 1,
        "pass":             max_pass,
        "disclosure_level": disclosure_level,
        "trite_score":      trite,
        "curiosity_informed": bool(curiosity_ctx),
        "domains_used":     domains,
        "domain":           "",
        "debug_audit":      debug_audit,
    }


def _build_debug_audit(
    stimulus: str,
    domains: List[str],
    winner: Optional[Interpretation],
    all_candidates: List[Dict],
    dejavu_killed: List[Dict],
    passes: List[Dict],
    status: str,
) -> Dict:
    """
    DEBUG MODE: She defends every response.
    This is her receipt. Her work shown. Her pick justified.
    """
    audit = {
        "stimulus":           stimulus,
        "domains_detected":   domains,
        "status":             status,
        "passes":             passes,
        "total_candidates":   len(all_candidates),
        "dejavu_killed_count": len(dejavu_killed),
        "dejavu_killed":      dejavu_killed[:5],
        "all_candidates":     sorted(
            all_candidates,
            key=lambda x: x.get("overall_score", 0),
            reverse=True,
        )[:9],
    }

    if winner:
        audit["winner"] = {
            "text":          winner.text,
            "domain":        winner.domain,
            "overall_score": round(winner.overall_score, 4),
            "count_met":     winner.count_met,
            "anti_beige":    round(winner.anti_beige_score, 3),
        }
        reasons = []
        if winner.overall_score > 0:
            reasons.append(f"Scored {winner.overall_score:.4f} (highest surviving)")
        if winner.count_met > 0:
            reasons.append(f"Met {winner.count_met}/5 priorities")
        if winner.anti_beige_score > 0.5:
            reasons.append(f"Anti-beige {winner.anti_beige_score:.2f} (fresh)")
        if winner.domain:
            reasons.append(f"Domain: {winner.domain}")
        if not reasons:
            reasons.append("Last resort — all others worse or blocked")
        audit["defense"] = reasons
    else:
        audit["winner"] = None
        audit["defense"] = ["NO CANDIDATES SURVIVED. All gates rejected everything."]

    return audit
