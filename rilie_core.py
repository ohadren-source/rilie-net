"""
rilie_core.py — THE KITCHEN
===========================
Constants, scoring, interpretations, pass pipeline.
This is RILIE's internal brain for a single stimulus:
  1. Classify the question type (definition / explanation / choice / unknown).
  2. Detect relevant domains and excavate snippets from her internal library.
  3. Generate up to 9 candidate interpretations per depth.
  4. Score each candidate against the 5-priority hierarchy (amusing, insightful,
     nourishing, compassionate, strategic) and anti-beige gates.
  5. Across 1..max_pass, always return the best interpretation seen:
     - "COMPRESSED" for solid early answers on shallow questions.
     - "GUESS" for low-confidence but honest attempts when thresholds aren't met.
     - "MISE_EN_PLACE" only if NOTHING survives anti-beige and scoring.

Anti-beige is a CURVE, not a binary gate.  A low freshness score penalizes
but does not kill.  External trite meter scales based on how saturated the
web is on this topic.

There is NO normal courtesy-exit here; static exits live in rilie.py as
last-resort behavior after this brain has genuinely tried to think.

UPGRADES (from savage_salvage):
  - Expanded domain knowledge: physics, life, games, thermodynamics, cosmology.
  - Curiosity context injection: her own discoveries weigh into scoring.
  - Person-aware domain boosting: if she knows user interests, lean into them.
  - Library-aware domain hooks: tags from library_index can augment detection.
"""

import random
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional

# Chompky — grammar brain for constructing responses from thought
# Graceful fallback if spaCy model not available
try:
    from ChompkyAtTheBit import parse_question, extract_holy_trinity_for_roux, infer_time_bucket
    CHOMPKY_AVAILABLE = True
except Exception:
    CHOMPKY_AVAILABLE = False


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
# DOMAIN KNOWLEDGE LIBRARY (internal brain)
# ============================================================================

DOMAIN_KNOWLEDGE: Dict[str, Dict[str, List[str]]] = {
    "music": {
        "compression": ["density", "rhythm", "compression", "bars", "tight", "minimal"],
        "love": ["call", "response", "connection", "harmony", "voice", "emotion"],
        "fear": ["dissonance", "tension", "unease", "tritone", "panic", "rising"],
        "satire": ["comedy", "trojan", "truth", "clown", "expose", "laugh", "think"],
        "production": ["noise", "collage", "architecture", "intent", "sample", "layers", "archaeology", "source"],
    },
    "culture": {
        "hip_hop": ["reframe", "broadcast", "political", "street", "news", "voice", "institution"],
        "film": ["montage", "compression", "visual", "diegetic", "grounding"],
        "resistance": ["blueprint", "mobilize", "art", "trickster", "bitter", "palatable", "weapon", "complacency"],
    },
    "physics": {
        "conservation": ["conserve", "transform", "nothing lost", "symmetry", "noether"],
        "relativity": ["frozen", "energy", "matter", "equivalence", "frame", "reference", "perception", "position"],
        "quantum": ["superposition", "collapse", "observe", "entangle", "distance", "correlated", "uncertainty", "tradeoff"],
    },
    "life": {
        "biology": ["cancer", "ego", "replication", "forgot", "apoptosis", "sacrifice", "thrive"],
        "evolution": ["adapt", "change", "selection", "symbiosis", "cooperate", "compete"],
        "health": ["diversity", "stability", "monoculture", "collapse", "emergence", "simple", "recursive", "complex"],
    },
    "games": {
        "game_theory": ["dilemma", "individual", "collective", "ego", "equilibrium", "stable", "strategy"],
        "trust": ["trust", "drops", "buckets", "grace", "reputation", "cost"],
        "incentives": ["cooperate", "mirror", "memory", "commit", "burn ships", "no defect", "misaligned", "commons"],
    },
    "thermodynamics": {
        "entropy": ["entropy", "increase", "closed", "disorder", "free energy", "work", "waste", "beige"],
        "harm_repair": ["harm", "irreversible", "repair", "cost", "cascade", "failure", "topology", "propagate"],
        "catch44": ["equilibrium", "death", "far from", "ego", "entropy", "grace", "negentropy", "alive"],
    },
    "cosmology": {
        "origin": ["boolean", "tick", "zero", "one", "bootstrap", "substrate"],
        "scale": ["fractal", "scale", "pattern", "recursive", "dark", "unknown", "humility", "detect"],
    },
    "finance": {
        "density": ["density", "destiny", "signal", "conviction", "quality", "frequency", "diamond", "bronze"],
        "risk": ["accordion", "expand", "contract", "earned", "floor", "never zero", "minimum", "sizing"],
        "regime": ["regime", "normal", "chaos", "stagnation", "fear", "gradient", "wait"],
        "literacy": ["slow cook", "compound", "patience", "survival", "security", "moves", "stretch"],
        "catch44": ["sleep", "topology", "patient", "quality", "stop loss", "integrity", "conviction", "ego"],
    },
}

# Quick keyword hooks to detect which domains to lean on.
DOMAIN_KEYWORDS: Dict[str, List[str]] = {
    "music": [
        "rhythm", "harmony", "tempo", "tone", "beat", "song", "rap", "hip-hop",
        "hip hop", "album", "music", "flav", "flavor", "chuck", "bomb squad",
        "production", "satire", "lyric", "lyrics", "verse", "hook", "sample",
        "biting", "joke", "911",
    ],
    "culture": [
        "culture", "politics", "race", "media", "society", "public enemy",
        "black planet", "911 is a joke", "fight the power", "nation",
        "empowerment", "community", "african", "diaspora", "significant",
        "important", "resistance", "movement",
    ],
    # --- NEW DOMAIN KEYWORDS ---
    "physics": [
        "physics", "energy", "mass", "force", "quantum", "relativity",
        "conservation", "entropy", "momentum", "velocity", "spacetime",
        "wave", "particle", "field", "gravity", "light", "noether",
    ],
    "life": [
        "biology", "cell", "cancer", "apoptosis", "evolution", "organism",
        "ecosystem", "mutation", "dna", "gene", "immune", "health",
        "body", "gut", "circadian", "biodiversity", "symbiosis",
    ],
    "games": [
        "game theory", "prisoner", "dilemma", "nash", "trust", "cooperation",
        "incentive", "strategy", "reputation", "commitment", "mechanism",
        "free rider", "commons", "public good", "coordination",
    ],
    "thermodynamics": [
        "thermodynamics", "entropy", "heat", "energy", "equilibrium",
        "irreversible", "harm", "repair", "cascade", "damage", "restore",
        "disorder", "negentropy", "free energy",
    ],
    "cosmology": [
        "universe", "cosmology", "origin", "creation", "existence",
        "simulation", "reality", "boolean", "fractal", "scale",
        "dark energy", "big bang", "infinity", "ducksauce",
    ],
    "finance": [
        "money", "finance", "invest", "investing", "investment", "trade",
        "trading", "stock", "stocks", "market", "budget", "debt", "loan",
        "mortgage", "savings", "retirement", "portfolio", "risk",
        "density", "conviction", "dividend", "compound", "interest",
        "wealth", "income", "expense", "credit", "cheddar", "fondue",
        "financial", "crypto", "bitcoin", "etf", "401k", "ira",
        "inflation", "recession", "bull", "bear", "vix", "spy",
        "fortune", "capital", "equity", "revenue", "profit", "loss",
    ],
}


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
        # Find the double newline separating context from question
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
    Returns 0.0 (novel — web has little) to 1.0 (trite — web is saturated).

    Factors:
    - Number of results returned (more = more saturated)
    - Overlap between result snippets (high overlap = everyone says the same thing)
    """
    if not baseline_results:
        return 0.0  # No web data = zero trite, anything she says has novelty

    count = len(baseline_results)

    # Count factor: 0–2 results = low, 5+ = high
    count_factor = min(1.0, count / 5.0)

    # Overlap factor: check how similar the snippets are to each other
    snippets = []
    for r in baseline_results:
        s = (r.get("snippet") or r.get("title") or "").lower().strip()
        if s:
            snippets.append(set(s.split()))

    if len(snippets) < 2:
        overlap_factor = 0.0
    else:
        # Average pairwise Jaccard similarity
        pairs = 0
        total_sim = 0.0
        for i in range(len(snippets)):
            for j in range(i + 1, len(snippets)):
                union = snippets[i] | snippets[j]
                if union:
                    total_sim += len(snippets[i] & snippets[j]) / len(union)
                pairs += 1
        overlap_factor = total_sim / pairs if pairs else 0.0

    # Composite: weight count slightly more than overlap
    return (count_factor * 0.6) + (overlap_factor * 0.4)


# ============================================================================
# ANTI-BEIGE CHECK (CURVE, not binary)
# ============================================================================

# Thread-local-ish storage for trite score per pipeline run
_current_trite_score: float = 0.0

# Curiosity bonus: if her own discovery is relevant, boost freshness
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

    This is a COMPOSITE score:
      internal_freshness (0.0–1.0): keyword signals for originality, authenticity, depth
      external_trite (0.0–1.0): how saturated the web is (set via set_trite_score)
      curiosity_bonus (0.0–0.3): boost when her own discoveries inform the answer

    Final score = (internal_freshness * 0.5) + ((1.0 - external_trite) * 0.5) + curiosity_bonus

    When external trite is HIGH (web is saturated), she needs more internal
    freshness to clear beige.  When external trite is LOW (topic is novel),
    even a straightforward answer has value.

    IMPORTANT: This is a CURVE.  It penalizes but never kills outright.
    The score feeds into priority scorers as a multiplier, not a gate.
    """
    text_lower = (text or "").lower()

    # Hard reject patterns — these are the only binary kills.
    hard_reject = [
        "copy of a copy",
        "every day is exactly the same",
        "autopilot",
    ]
    if any(signal in text_lower for signal in hard_reject):
        return 0.0

    # Internal freshness signals
    originality_signals = ["original", "fresh", "new", "unique", "unprecedented", "never"]
    authenticity_signals = ["genuine", "real", "true", "honest", "brutal", "earned"]
    depth_signals = ["master", "craft", "skill", "proficiency", "expertise"]
    effort_signals = ["earnest", "work", "struggle", "build", "foundation"]
    reflection_signals = ["reflect", "mirror", "light", "show", "demonstrate"]

    # Domain-relevance signals — her own knowledge statements should get credit
    domain_signals = [
        "reframed", "exposed", "mobilize", "blueprint", "journalism",
        "trickster", "trojan", "architecture", "archaeology", "collage",
        "broadcast", "dispatch", "weapon", "overload", "complacency",
        "permission", "uncomfortable", "palatable", "performance",
        "political", "empowerment", "confrontation", "resistance",
        "community", "neighborhoods", "emergency", "failure",
    ]

    # New domain signals from expanded library
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

    # Composite with external trite + curiosity bonus
    global _current_trite_score, _current_curiosity_bonus
    external_novelty = 1.0 - _current_trite_score

    final = (internal_freshness * 0.5) + (external_novelty * 0.5) + _current_curiosity_bonus

    # Floor at 0.15 — nothing is truly zero unless hard-rejected above.
    # This ensures candidates always survive to be scored, just penalized.
    return max(0.15, min(1.0, final))


# ============================================================================
# 5-PRIORITY SCORERS
# ============================================================================

def _universal_boost(text_lower: str) -> float:
    # Favor tracks that encode WE, love, care, emergence.
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
        # New from expanded domains
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
        # New from expanded domains
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
        # New from expanded domains
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
        # New from expanded domains
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
# RESPONSE CONSTRUCTION — Chompky gives her a voice
# ============================================================================
# A human doesn't memorize the Library of Congress then say hello.
# She thinks about the question, finds what she knows, and CONSTRUCTS
# a response that connects her knowledge to what was asked.

def construct_response(stimulus: str, snippet: str) -> str:
    """
    Construct a response from a domain snippet + stimulus.
    
    The snippet is a SEED — could be a word, a phrase, or a sentence.
    She must BUILD a response that connects the seed to the question.
    
    If the seed is a single word or short phrase (< 5 words):
      She uses it as a concept anchor and constructs around it.
    If the seed is a full sentence:
      She restructures it through the stimulus lens.
    """
    if not snippet or not stimulus:
        return snippet or ""

    stim_lower = stimulus.lower().strip()
    snippet_clean = snippet.strip()
    snippet_words = snippet_clean.split()
    is_word_seed = len(snippet_words) < 5

    # --- Chompky-powered construction ---
    if CHOMPKY_AVAILABLE:
        try:
            parsed = parse_question(stimulus)
            subject = " ".join(parsed.subject_tokens) if parsed.subject_tokens else ""
            focus = " ".join(parsed.focus_tokens) if parsed.focus_tokens else ""

            if is_word_seed:
                # WORD MODE: The snippet is an ingredient, not a dish.
                # Build a thought connecting the stimulus to the concept.
                seed = snippet_clean.lower()
                if subject and focus:
                    return (
                        f"When you look at {subject} through the lens of {focus}, "
                        f"it comes back to {seed} — that's where the real weight is. "
                        f"Everything else is decoration."
                    )
                if subject:
                    return (
                        f"The core of {subject} is {seed}. "
                        f"Strip away everything else and that's what's left. "
                        f"That's what actually moves."
                    )
                return (
                    f"It starts with {seed}. "
                    f"That's not a detail, that's the foundation. "
                    f"Everything builds from there."
                )
            else:
                # SENTENCE MODE: Restructure through stimulus
                core = snippet_clean
                if subject:
                    return f"What makes {subject} work — {core[0].lower()}{core[1:]}"
                return f"Here's the thing — {core[0].lower()}{core[1:]}"

        except Exception:
            pass

    # --- No Chompky: build from seed ---
    if is_word_seed:
        seed = snippet_clean.lower()
        # Extract question topic from stimulus
        topic_words = [w for w in stim_lower.split()
                       if w not in {"what", "why", "how", "who", "when", "where",
                                    "is", "are", "the", "a", "an", "do", "does",
                                    "can", "could", "would", "should", "about",
                                    "tell", "me", "you", "your", "my", "i"}]
        topic = " ".join(topic_words[:3]) if topic_words else "this"

        return (
            f"With {topic}, the thing that matters most is {seed}. "
            f"Not the surface — the {seed} underneath it. "
            f"That's where the real conversation is."
        )

    # SENTENCE MODE without Chompky
    core = snippet_clean
    return f"Here's what it comes down to — {core[0].lower()}{core[1:]}"


def construct_blend(stimulus: str, snippet1: str, snippet2: str) -> str:
    """
    Construct a cross-domain blend — two ideas connected through the question.
    Handles both word-level seeds and full sentences.
    """
    s1 = snippet1.strip()
    s2 = snippet2.strip()

    if not s1 or not s2:
        return s1 or s2 or ""

    s1_is_word = len(s1.split()) < 5
    s2_is_word = len(s2.split()) < 5
    stim_lower = stimulus.lower().strip()

    if CHOMPKY_AVAILABLE:
        try:
            parsed = parse_question(stimulus)
            subject = " ".join(parsed.subject_tokens) if parsed.subject_tokens else ""

            if s1_is_word and s2_is_word:
                # Both are concept seeds — connect them
                if subject:
                    return (
                        f"With {subject}, there are two forces at work — "
                        f"{s1.lower()} and {s2.lower()}. "
                        f"They look separate but they're the same principle "
                        f"wearing different clothes. Pull one thread and the other moves."
                    )
                return (
                    f"Two things that seem unrelated: {s1.lower()} and {s2.lower()}. "
                    f"But look closer — they're connected. "
                    f"One doesn't work without the other."
                )
            elif s1_is_word or s2_is_word:
                # One word, one sentence — anchor through the word
                word = s1 if s1_is_word else s2
                sentence = s2 if s1_is_word else s1
                return (
                    f"Start with {word.lower()} — "
                    f"{sentence[0].lower()}{sentence[1:]} "
                    f"That connection is where it gets interesting."
                )
            else:
                # Both sentences
                if subject:
                    return (
                        f"Two things about {subject}: "
                        f"{s1[0].lower()}{s1[1:]}, and on the flip side, "
                        f"{s2[0].lower()}{s2[1:]}"
                    )
                return (
                    f"On one hand — {s1[0].lower()}{s1[1:]}. "
                    f"But then — {s2[0].lower()}{s2[1:]}"
                )
        except Exception:
            pass

    # No Chompky fallback
    if s1_is_word and s2_is_word:
        return (
            f"There's a connection between {s1.lower()} and {s2.lower()} "
            f"that most people miss. One feeds the other."
        )
    return f"Two sides — {s1[0].lower()}{s1[1:]}, and {s2[0].lower()}{s2[1:]}"


# ============================================================================
# DOMAIN DETECTION & EXCAVATION
# ============================================================================

def detect_domains(stimulus: str) -> List[str]:
    sl = (stimulus or "").lower()
    scores = {
        d: sum(1 for kw in kws if kw in sl)
        for d, kws in DOMAIN_KEYWORDS.items()
    }

    # Chompky boost: use holy_trinity to find domains the keywords missed
    if CHOMPKY_AVAILABLE:
        try:
            trinity = extract_holy_trinity_for_roux(stimulus)
            for word in trinity:
                wl = word.lower()
                for d, kws in DOMAIN_KEYWORDS.items():
                    if any(wl in kw or kw in wl for kw in kws):
                        scores[d] = scores.get(d, 0) + 2  # Holy trinity match = strong signal
        except Exception:
            pass

    # Sort by descending score, keep best 4
    ordered = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [d for d, _ in ordered[:4] if d in DOMAIN_KNOWLEDGE]


def excavate_domains(stimulus: str, domains: List[str]) -> Dict[str, List[str]]:
    """
    For each domain, sample a small subset of its internal statements.
    Prefers sub-domains that keyword-match the stimulus.
    """
    sl = (stimulus or "").lower()
    excavated: Dict[str, List[str]] = {}
    for domain in domains:
        if domain not in DOMAIN_KNOWLEDGE:
            excavated[domain] = []
            continue

        # Score each sub-domain by keyword overlap with stimulus
        sub_items: List[tuple] = []  # (relevance_score, item_text)
        for sub_key, items in DOMAIN_KNOWLEDGE[domain].items():
            # Sub-domain key relevance
            sub_relevance = 1 if sub_key.lower() in sl else 0
            for item in items:
                # Item-level relevance: count stimulus words in item
                item_words = set(item.lower().split())
                stim_words = set(sl.split())
                word_overlap = len(item_words & stim_words)
                score = sub_relevance * 2 + word_overlap
                sub_items.append((score, item))

        if sub_items:
            # Sort by relevance, take top 4 (more than before)
            sub_items.sort(key=lambda x: x[0], reverse=True)
            top = [item for _, item in sub_items[:4]]
            # Add 1 random for diversity
            remaining = [item for _, item in sub_items[4:]]
            if remaining:
                top.append(random.choice(remaining))
            excavated[domain] = top
        else:
            excavated[domain] = []

    # --- WORD ENRICHMENT: dictionary + synonyms for word-level ingredients ---
    # If the ingredient is a word (< 5 tokens), expand it so she has
    # more to cook with. "density" → "density (closeness, concentration, richness)"
    for domain, items in excavated.items():
        enriched = []
        for item in items:
            if len(item.split()) < 5:
                # It's a word seed — enrich it
                word = item.strip().lower()
                definition = _WORD_DEFINITIONS.get(word, "")
                synonyms = _WORD_SYNONYMS.get(word, [])
                homonyms = _WORD_HOMONYMS.get(word, [])
                parts = [item]
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


# --- Built-in word definitions and synonyms ---
# She carries a pocket dictionary. Not Wikipedia — just enough to cook with.
_WORD_DEFINITIONS: Dict[str, str] = {
    # Music
    "density": "maximum information packed into minimum space",
    "rhythm": "pattern of beats recurring in time",
    "compression": "reducing to essence without losing meaning",
    "bars": "measured units of musical time",
    "tight": "precise with zero waste",
    "minimal": "stripped to only what matters",
    "call": "an invitation that demands response",
    "response": "the answer that completes the exchange",
    "connection": "the bridge between two points",
    "harmony": "different notes working as one",
    "voice": "the instrument that carries identity",
    "emotion": "energy in motion through feeling",
    "dissonance": "tension between things that clash",
    "tension": "the pull between opposing forces",
    "comedy": "truth delivered through surprise",
    "trojan": "something hidden inside something inviting",
    "truth": "what remains when everything else is stripped",
    "expose": "to reveal what was hidden",
    "noise": "information that hasn't been organized yet",
    "collage": "fragments assembled into new meaning",
    "architecture": "intentional structure that serves purpose",
    "intent": "purpose behind the action",
    "sample": "a piece of something larger carried forward",
    "layers": "depth built by stacking",
    # Culture
    "reframe": "to change how something is seen without changing what it is",
    "broadcast": "to send signal in all directions",
    "political": "concerning who has power and how it moves",
    "street": "where theory meets lived experience",
    "institution": "a structure that outlasts the people in it",
    "blueprint": "a plan you can build from",
    "mobilize": "to turn stillness into movement",
    "trickster": "the one who breaks rules to reveal truth",
    "weapon": "any tool used to shift power",
    # Physics
    "conserve": "nothing lost only transformed",
    "transform": "to change form while preserving essence",
    "symmetry": "the pattern that stays the same when you rotate it",
    "frozen": "energy held still in a form",
    "energy": "the capacity to make change happen",
    "matter": "energy in a form you can touch",
    "equivalence": "different expressions of the same thing",
    "frame": "the perspective that determines what you see",
    "perception": "reality filtered through position",
    "superposition": "being in multiple states until forced to choose",
    "collapse": "the moment possibility becomes specific",
    "observe": "to interact with something by paying attention",
    "entangle": "connected regardless of distance",
    "uncertainty": "precision in one dimension costs precision in another",
    "tradeoff": "getting one thing by giving up another",
    # Life
    "cancer": "growth without regard for the whole",
    "ego": "self-prioritization that forgets the system",
    "sacrifice": "giving up the part for the whole",
    "adapt": "changing shape to fit new conditions",
    "symbiosis": "two things thriving because they serve each other",
    "emergence": "complex behavior from simple rules repeated",
    "recursive": "applying the same pattern at every level",
    "diversity": "strength through difference",
    "stability": "the ability to absorb shock without breaking",
    # Games
    "dilemma": "a choice where every option has cost",
    "collective": "the group acting as one",
    "equilibrium": "the point where no one gains by moving alone",
    "trust": "risk taken on the belief another will reciprocate",
    "drops": "small consistent deposits over time",
    "buckets": "large sudden losses",
    "grace": "giving more than what's owed",
    "mirror": "reflecting back what you receive",
    "memory": "the past informing present choices",
    "commit": "removing the option to retreat",
    "misaligned": "pointed in different directions",
    # Thermodynamics
    "entropy": "disorder increasing over time without input",
    "disorder": "the absence of intentional arrangement",
    "waste": "energy that did no useful work",
    "beige": "safe mediocrity that offends no one and moves no one",
    "harm": "damage that can't be fully undone",
    "irreversible": "a change that only goes one direction",
    "cascade": "one failure triggering the next",
    "propagate": "spreading through connected nodes",
    "negentropy": "order created by pumping energy into a system",
    # Cosmology
    "boolean": "the simplest possible distinction — yes or no",
    "tick": "the smallest unit of change",
    "fractal": "the same pattern at every scale",
    "scale": "the level at which you observe",
    "humility": "acknowledging what you cannot know",
    # Finance
    "destiny": "where the weight of evidence points",
    "signal": "information that predicts what comes next",
    "conviction": "certainty earned by evidence",
    "quality": "the ratio of signal to noise",
    "accordion": "expanding and contracting with conditions",
    "regime": "the current rules the system operates under",
    "chaos": "conditions where normal rules break down",
    "patience": "the willingness to wait for the right moment",
    "compound": "growth building on previous growth",
    "integrity": "alignment between what you say and what you do",
}

_WORD_SYNONYMS: Dict[str, List[str]] = {
    "density": ["concentration", "thickness", "richness", "weight"],
    "rhythm": ["pulse", "cadence", "groove", "cycle"],
    "compression": ["condensation", "distillation", "essence", "reduction"],
    "harmony": ["accord", "unity", "resonance", "blend"],
    "tension": ["friction", "pull", "strain", "charge"],
    "truth": ["reality", "authenticity", "core", "foundation"],
    "noise": ["static", "chaos", "raw signal", "unfiltered"],
    "architecture": ["structure", "framework", "design", "blueprint"],
    "energy": ["force", "drive", "capacity", "potential"],
    "transform": ["convert", "reshape", "evolve", "transmute"],
    "symmetry": ["balance", "equivalence", "mirror", "pattern"],
    "collapse": ["resolve", "crystallize", "decide", "converge"],
    "emergence": ["arising", "surfacing", "spontaneous order", "self-organization"],
    "trust": ["faith", "confidence", "reliability", "bond"],
    "grace": ["generosity", "mercy", "kindness", "gift"],
    "entropy": ["decay", "disorder", "dissipation", "degradation"],
    "cascade": ["chain reaction", "domino effect", "ripple", "avalanche"],
    "signal": ["indicator", "cue", "marker", "evidence"],
    "conviction": ["certainty", "confidence", "resolve", "commitment"],
    "patience": ["endurance", "persistence", "steady", "long game"],
    "integrity": ["wholeness", "alignment", "honesty", "consistency"],
    "ego": ["self-interest", "pride", "self-image", "vanity"],
    "sacrifice": ["surrender", "offering", "cost", "trade"],
    "adapt": ["adjust", "evolve", "flex", "pivot"],
    "diversity": ["variety", "range", "spectrum", "multiplicity"],
    "connection": ["link", "bridge", "thread", "bond"],
    "blueprint": ["plan", "template", "map", "schema"],
    "fractal": ["self-similar", "nested", "recursive", "layered"],
    "compound": ["accumulate", "snowball", "build", "stack"],
}

# --- Homonyms: same word, different meanings ---
# The polymorphic layer. This is how Ohad thinks.
# Multiple meanings in one word. She should too.
_WORD_HOMONYMS: Dict[str, List[str]] = {
    "bars": ["music: measured units of rhythm", "prison: what cages are made of", "drinking: where people gather", "legal: the bar exam"],
    "scale": ["music: sequence of notes", "size: the level you observe at", "fish: protective covering", "climbing: to ascend"],
    "bridge": ["music: the section that connects verse to chorus", "structure: what connects two shores", "guitar: where strings meet the body", "connection: what links two ideas"],
    "key": ["music: tonal center", "lock: what opens a door", "answer: the crucial element", "keyboard: what you press"],
    "beat": ["music: rhythmic pulse", "defeat: to overcome", "tired: exhausted", "patrol: a cop's route"],
    "note": ["music: a single pitch", "writing: a short message", "observe: to notice something", "money: a bill"],
    "rest": ["music: silence with duration", "sleep: to recover", "remainder: what's left over"],
    "pitch": ["music: frequency of sound", "sales: a presentation to convince", "baseball: to throw", "angle: degree of slope"],
    "record": ["music: an album", "data: a stored entry", "achievement: the best ever done", "capture: to document"],
    "track": ["music: a single song", "path: a route to follow", "monitor: to keep watch on", "racing: where you run"],
    "hook": ["music: the catchy part", "fishing: what catches", "boxing: a curved punch", "coding: a callback function"],
    "sample": ["music: a borrowed sound", "science: a specimen", "taste: a small portion to try"],
    "channel": ["music: a signal path", "water: a passage between lands", "tv: a station", "communication: a medium"],
    "wave": ["physics: energy moving through space", "ocean: water rising and falling", "greeting: a hand gesture", "trend: a cultural movement"],
    "field": ["physics: a force distribution in space", "farm: cultivated land", "expertise: a domain of knowledge", "sports: where you play"],
    "charge": ["physics: electrical property", "money: a cost", "attack: to rush forward", "responsibility: to be in charge of"],
    "bond": ["chemistry: atoms held together", "finance: a debt instrument", "connection: emotional attachment", "spy: 007"],
    "cell": ["biology: basic unit of life", "prison: a small room", "phone: mobile device", "power: battery unit"],
    "culture": ["society: shared values and practices", "biology: growing organisms in a lab", "agriculture: to cultivate"],
    "matter": ["physics: stuff with mass", "importance: it matters", "problem: what's the matter"],
    "frame": ["physics: reference point", "picture: what holds the image", "blame: to set someone up", "structure: the skeleton of something"],
    "flow": ["water: movement of liquid", "music: rhythmic delivery", "psychology: optimal state of performance", "traffic: movement through a system"],
    "drive": ["car: to operate a vehicle", "motivation: internal push", "computer: storage device", "golf: a long shot"],
    "collapse": ["physics: wave function resolving", "building: structural failure", "medical: to fall down", "folding: to make compact"],
    "foundation": ["building: what supports the structure", "philosophy: the base assumption", "makeup: the base layer", "charity: an organization that gives"],
    "deposit": ["bank: money put in", "geology: sediment laid down", "trust: something left as guarantee"],
    "fire": ["element: combustion", "work: to terminate employment", "passion: intense motivation", "weapon: to discharge"],
    "plant": ["biology: a growing organism", "factory: a manufacturing facility", "spy: to secretly place", "evidence: to fabricate"],
    "toast": ["bread: heated until crispy", "celebration: raising a glass", "done: finished or ruined"],
    "patient": ["medical: someone receiving care", "virtue: willing to wait", "steady: unhurried and calm"],
    "gravity": ["physics: the force of attraction", "seriousness: the weight of a situation"],
    "volume": ["sound: loudness level", "book: a single tome", "space: amount of three-dimensional space", "quantity: amount"],
    "current": ["water: flow direction", "electricity: flow of charge", "time: happening now", "awareness: up to date"],
    "resolution": ["conflict: settling a dispute", "screen: pixel density", "decision: a firm commitment", "music: tension releasing to rest"],
    "minor": ["music: a sad-sounding key", "age: not yet adult", "importance: of lesser significance"],
    "major": ["music: a bright-sounding key", "military: a rank", "importance: significant", "college: area of study"],
    "sharp": ["music: a half step up", "blade: able to cut", "mind: quick and intelligent", "image: clear and defined"],
    "flat": ["music: a half step down", "surface: level and even", "tire: deflated", "apartment: a dwelling"],
}


# ============================================================================
# INTERPRETATION GENERATION
# ============================================================================

def generate_9_interpretations(
    stimulus: str,
    excavated: Dict[str, List[str]],
    depth: int,
    domains: Optional[List[str]] = None,
) -> List[Interpretation]:
    """
    Generate up to 9 internal candidate interpretations by:
    - Emitting single-domain statements.
    - Blending across domains when possible.
    """
    interpretations: List[Interpretation] = []
    idx = 0

    # Single-domain items — CONSTRUCTED, not shelf-served.
    # KNOWN CANNED FRAGMENTS — if these appear, it's a script not generation
    _CANNED_MARKERS = [
        "the way i understand it",
        "the way i see it",
        "what it comes down to",
        "the thing about",
        "what makes",
        "the reason is",
        "the way it works",
        "the person behind",
        "what happened with",
        "where",
        "goes from here",
    ]

    def _originality_multiplier(text: str, domain: str) -> float:
        """
        Rig the game. Stack the deck. Stand on the scale.
        Generated > Searched > Canned. Always.
        """
        t = text.lower().strip()
        is_canned = any(t.startswith(marker) for marker in _CANNED_MARKERS)
        if is_canned:
            return 0.5
        if domain.startswith("roux") or "[roux:" in t:
            return 2.0
        if "_" in domain and domain.count("_") >= 1:
            return 2.5
        return 3.0

    # ------------------------------------------------------------------
    # RELEVANCE: Did she answer what was asked?
    # Domain match count + tone alignment
    # ------------------------------------------------------------------
    stimulus_domains = set(domains) if domains else set()  # domains detected from stimulus
    try:
        from guvna import detect_tone_from_stimulus
        stimulus_tone = detect_tone_from_stimulus(stimulus)
    except ImportError:
        stimulus_tone = "insightful"

    # Tone keywords for matching response tone to stimulus tone
    _TONE_WORDS = {
        "amusing": {"funny", "humor", "laugh", "joke", "absurd", "ironic", "haha", "lol"},
        "insightful": {"because", "reason", "means", "actually", "truth", "real", "works"},
        "nourishing": {"grow", "learn", "build", "create", "teach", "develop", "nurture"},
        "compassionate": {"feel", "hurt", "care", "understand", "hear", "support", "sorry"},
        "strategic": {"plan", "move", "step", "leverage", "position", "execute", "next"},
    }

    def _relevance_score(text: str, domain: str) -> float:
        """
        Relevance = domain match + tone alignment.
        0 matched domains = 0. 2+ = high. Tone close = bonus.
        """
        # Domain match
        response_domains = set()
        if domain:
            for d in domain.split("_"):
                response_domains.add(d)
        domain_overlap = len(response_domains & stimulus_domains)

        if domain_overlap == 0 and stimulus_domains:
            domain_score = 0.1  # Almost nothing — wrong topic
        elif domain_overlap == 1:
            domain_score = 0.6
        elif domain_overlap >= 2:
            domain_score = 1.0
        else:
            domain_score = 0.3  # No stimulus domains detected

        # Tone alignment
        t_lower = text.lower()
        tone_words = _TONE_WORDS.get(stimulus_tone, set())
        tone_hits = sum(1 for tw in tone_words if tw in t_lower)
        tone_score = min(1.0, tone_hits * 0.25)  # 4 hits = max

        return (domain_score * 0.7) + (tone_score * 0.3)

    # ------------------------------------------------------------------
    # RESONANCE: Flow = Skill × Challenge
    # Response depth must match question depth
    # ------------------------------------------------------------------
    def _resonance_score(text: str) -> float:
        """
        Flow = Skill × Challenge.
        Simple question + simple answer = flow.
        Complex question + complex answer = flow.
        Mismatch = penalty.
        """
        # Estimate question complexity (challenge)
        stim_words = len(stimulus.split())
        stim_questions = stimulus.count("?")
        challenge = min(1.0, (stim_words / 30) + (stim_questions * 0.2))

        # Estimate response complexity (skill)
        resp_words = len(text.split())
        resp_has_structure = 1.0 if any(c in text for c in ["—", ":", ";"]) else 0.0
        skill = min(1.0, (resp_words / 40) + (resp_has_structure * 0.1))

        # Flow = closeness of skill to challenge
        # Perfect match = 1.0, big gap = low
        gap = abs(skill - challenge)
        return max(0.1, 1.0 - gap)

    # ------------------------------------------------------------------
    # COMBINED SCORE: originality × relevance × resonance
    # ------------------------------------------------------------------
    def _final_score(raw_overall: float, text: str, domain: str) -> float:
        orig = _originality_multiplier(text, domain)
        relev = _relevance_score(text, domain)
        reson = _resonance_score(text)
        return raw_overall * orig * relev * reson

    for domain, items in excavated.items():
        for item in items[:4]:
            text = construct_response(stimulus, item)
            anti = anti_beige_check(text)
            scores = {k: fn(text) for k, fn in SCORERS.items()}
            count = sum(1 for v in scores.values() if v > 0.3)
            raw_overall = sum(scores[k] * WEIGHTS[k] for k in scores) / 4.5
            overall = _final_score(raw_overall, text, domain)
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

    # Cross-domain blends.
    attempts = 0
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
        i1 = random.choice(excavated[d1])
        i2 = random.choice(excavated[d2])
        text = construct_blend(stimulus, i1, i2)
        anti = anti_beige_check(text)
        scores = {k: fn(text) for k, fn in SCORERS.items()}
        count = sum(1 for v in scores.values() if v > 0.3)
        raw_overall = sum(scores[k] * WEIGHTS[k] for k in scores) / 4.5
        blend_domain = f"{d1}_{d2}"
        overall = _final_score(raw_overall, text, blend_domain)
        interpretations.append(
            Interpretation(
                id=depth * 1000 + idx,
                text=text,
                domain=f"{d1}_{d2}",
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
# PASS PIPELINE — the actual cooking
# ============================================================================

def run_pass_pipeline(
    stimulus: str,
    disclosure_level: str,
    max_pass: int = 3,
    baseline_results: Optional[List[Dict[str, str]]] = None,
    prior_responses: Optional[List[str]] = None,
) -> Dict:
    """
    Run interpretation passes.  Called only at OPEN or FULL disclosure.

    Now accepts baseline_results so it can compute the external trite meter.
    Also detects and applies curiosity context if present in the stimulus.

    ANTI-DÉJÀ-VU GATE:
    She is forbidden to produce déjà vu in others.
    Any candidate too similar to her own recent responses is rejected.
    She can *notice* the user repeating — that's internal context.
    But she never repeats herself. Rather silence than repetition.
    """
    # Check for curiosity context and extract it
    curiosity_ctx = extract_curiosity_context(stimulus)
    clean_stimulus = strip_curiosity_context(stimulus)

    # Set the external trite score for this run
    trite = compute_trite_score(baseline_results)
    set_trite_score(trite)

    # Set curiosity bonus if her own discoveries are informing this answer
    if curiosity_ctx:
        set_curiosity_bonus(0.15)  # Moderate boost for self-discovered knowledge
    else:
        set_curiosity_bonus(0.0)

    question_type = detect_question_type(clean_stimulus)
    domains = detect_domains(clean_stimulus)

    # --- Anti-déjà-vu: build word sets from her recent responses ---
    _prior_word_sets: List[set] = []
    if prior_responses:
        for pr in prior_responses[-5:]:  # Last 5 responses
            words = set(re.sub(r"[^a-zA-Z0-9\s]", "", pr.lower()).split())
            _prior_word_sets.append(words)

    def _is_dejavu(candidate_text: str) -> bool:
        """Return True if candidate is too similar to any recent response."""
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

    # --- ROUX INJECTION: If Roux found something, feed it to the Kitchen ---
    # Roux material arrives as "[ROUX: ...]\n\n{question}" in the stimulus.
    # Extract it and inject as a domain source so the Kitchen has fresh food.
    roux_match = re.match(r"\[ROUX:\s*(.*?)\]\s*\n", clean_stimulus, re.DOTALL)
    if roux_match:
        roux_text = roux_match.group(1).strip()
        if roux_text:
            # Split into sentences for multiple candidates
            roux_items = [s.strip() for s in re.split(r'[.!?]+', roux_text) if s.strip() and len(s.strip()) > 10]
            if roux_items:
                excavated["roux"] = roux_items[:5]  # Cap at 5 fresh ingredients
            # Clean the stimulus so downstream doesn't see the ROUX prefix
            clean_stimulus = re.sub(r"\[ROUX:.*?\]\s*\n*", "", clean_stimulus, flags=re.DOTALL).strip()

    # --- SOi DOMAIN MAP: Pull wisdom from the 93 tracks ---
    # The domain map has 364 assignments across all tracks.
    # get_human_wisdom returns fourth-wall-safe human translations.
    try:
        from soi_domain_map import get_human_wisdom, DOMAIN_INDEX
        # Use the detected domains AND try broader keyword matching
        soi_domains = [d for d in domains if d in DOMAIN_INDEX]
        # Also check for SOi-specific domains not in DOMAIN_KEYWORDS
        sl = clean_stimulus.lower()
        for soi_domain in DOMAIN_INDEX:
            if soi_domain in sl and soi_domain not in soi_domains:
                soi_domains.append(soi_domain)
        if soi_domains:
            wisdom = get_human_wisdom(soi_domains, max_tracks=6)
            if wisdom:
                # Inject track wisdom as a new domain "catch44" in excavated
                if "catch44" in excavated:
                    excavated["catch44"].extend(wisdom)
                else:
                    excavated["catch44"] = wisdom
    except ImportError:
        pass  # SOi domain map not available — proceed with old domains

    hard_cap = 3  # Dayenu. That is enough.
    max_pass = max(1, min(max_pass, hard_cap))

    # Slightly limit depth for OPEN vs FULL, but never to zero.
    if disclosure_level == "open":
        max_pass = min(max_pass, 3)

    best_global: Interpretation | None = None
    # DEBUG: collect all candidates across all passes for the audit trail
    _debug_all_candidates: List[Dict] = []
    _debug_dejavu_killed: List[Dict] = []
    _debug_passes: List[Dict] = []

    for current_pass in range(1, max_pass + 1):
        depth = current_pass - 1
        nine = generate_9_interpretations(clean_stimulus, excavated, depth, domains=domains)

        if not nine:
            _debug_passes.append({"pass": current_pass, "candidates": 0, "note": "empty"})
            continue

        # Log all candidates for this pass
        pass_candidates = []
        for i in nine:
            dejavu = _is_dejavu(i.text)
            entry = {
                "id": i.id,
                "domain": i.domain,
                "text": i.text[:120],
                "overall_score": round(i.overall_score, 4),
                "count_met": i.count_met,
                "anti_beige": round(i.anti_beige_score, 3),
                "dejavu_blocked": dejavu,
            }
            pass_candidates.append(entry)
            _debug_all_candidates.append(entry)
            if dejavu:
                _debug_dejavu_killed.append(entry)

        # Thresholds — she doesn't need to be Oscar Wilde. Just not trite.
        filtered = [
            i
            for i in nine
            if (i.overall_score > (0.06 if current_pass == 1 else 0.09)
                or i.count_met >= 1)
            and not _is_dejavu(i.text)  # ANTI-DÉJÀ-VU GATE
        ]

        # If anti-déjà-vu rejected everything, take the LEAST similar one.
        # She must respond. Silence is a moment, not a destination.
        if not filtered and nine:
            def _dejavu_score(text: str) -> float:
                """Lower = less similar to prior responses = better."""
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

            # Sort by least déjà vu, pick the freshest
            ranked = sorted(nine, key=lambda x: _dejavu_score(x.text))
            filtered = [ranked[0]]

        _debug_passes.append({
            "pass": current_pass,
            "candidates": len(nine),
            "survived_filter": len(filtered),
            "dejavu_killed": sum(1 for c in pass_candidates if c["dejavu_blocked"]),
        })

        if filtered:
            best = max(filtered, key=lambda x: (x.count_met, x.overall_score))
        else:
            # No filtered candidates; still pick something for global best.
            best = max(nine, key=lambda x: x.overall_score)

        if (best_global is None) or (best.overall_score > best_global.overall_score):
            best_global = best

        # For shallow question types and early passes, compress quickly.
        if current_pass <= 2 and question_type in {
            QuestionType.UNKNOWN,
            QuestionType.CHOICE,
            QuestionType.DEFINITION,
        }:
            # BUILD DEBUG AUDIT
            debug_audit = _build_debug_audit(
                clean_stimulus, domains, best, _debug_all_candidates,
                _debug_dejavu_killed, _debug_passes, "COMPRESSED"
            )
            return {
                "stimulus": clean_stimulus,
                "result": best.text,
                "quality_score": best.overall_score,
                "priorities_met": best.count_met,
                "anti_beige_score": best.anti_beige_score,
                "status": "COMPRESSED",
                "depth": depth,
                "pass": current_pass,
                "disclosure_level": disclosure_level,
                "trite_score": trite,
                "curiosity_informed": bool(curiosity_ctx),
                "domains_used": domains,
                "domain": best.domain,
                "debug_audit": debug_audit,
            }

    # After all passes, if we saw *any* candidates, return the global best as GUESS.
    if best_global is not None:
        debug_audit = _build_debug_audit(
            clean_stimulus, domains, best_global, _debug_all_candidates,
            _debug_dejavu_killed, _debug_passes, "GUESS"
        )
        return {
            "stimulus": clean_stimulus,
            "result": best_global.text,
            "quality_score": best_global.overall_score,
            "priorities_met": best_global.count_met,
            "anti_beige_score": best_global.anti_beige_score,
            "status": "GUESS",
            "depth": best_global.depth,
            "pass": max_pass,
            "disclosure_level": disclosure_level,
            "trite_score": trite,
            "curiosity_informed": bool(curiosity_ctx),
            "domains_used": domains,
            "domain": best_global.domain,
            "debug_audit": debug_audit,
        }

    # Absolute fallback: nothing survived. She's silent.
    debug_audit = _build_debug_audit(
        clean_stimulus, domains, None, _debug_all_candidates,
        _debug_dejavu_killed, _debug_passes, "MISE_EN_PLACE"
    )
    return {
        "stimulus": clean_stimulus,
        "result": "",
        "quality_score": 0.0,
        "priorities_met": 0,
        "anti_beige_score": 0.0,
        "status": "MISE_EN_PLACE",
        "depth": max_pass - 1,
        "pass": max_pass,
        "disclosure_level": disclosure_level,
        "trite_score": trite,
        "curiosity_informed": bool(curiosity_ctx),
        "domains_used": domains,
        "domain": "",
        "debug_audit": debug_audit,
    }


def _build_debug_audit(
    stimulus: str,
    domains: List[str],
    winner: Optional['Interpretation'],
    all_candidates: List[Dict],
    dejavu_killed: List[Dict],
    passes: List[Dict],
    status: str,
) -> Dict:
    """
    DEBUG MODE: She defends every response.
    This is her receipt. Her work shown. Her pick justified.
    If she can't defend it, the pick is wrong.
    """
    audit = {
        "stimulus": stimulus,
        "domains_detected": domains,
        "status": status,
        "passes": passes,
        "total_candidates": len(all_candidates),
        "dejavu_killed_count": len(dejavu_killed),
        "dejavu_killed": dejavu_killed[:5],  # Show up to 5
        "all_candidates": sorted(
            all_candidates,
            key=lambda x: x.get("overall_score", 0),
            reverse=True,
        )[:9],  # Top 9 by score
    }

    if winner:
        audit["winner"] = {
            "text": winner.text,
            "domain": winner.domain,
            "overall_score": round(winner.overall_score, 4),
            "count_met": winner.count_met,
            "anti_beige": round(winner.anti_beige_score, 3),
        }
        # DEFENSE: Why this one?
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
