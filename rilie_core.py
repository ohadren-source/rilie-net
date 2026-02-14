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
        "compression": [],
        "love": [],
        "fear": [],
        "satire": [],
        "production": [],
    },
    "culture": {
        "hip_hop": [],
        "film": [],
        "resistance": [],
    },
    "physics": {
        "conservation": [],
        "relativity": [],
        "quantum": [],
    },
    "life": {
        "biology": [],
        "evolution": [],
        "health": [],
    },
    "games": {
        "game_theory": [],
        "trust": [],
        "incentives": [],
    },
    "thermodynamics": {
        "entropy": [],
        "harm_repair": [],
        "catch44": [],
    },
    "cosmology": {
        "origin": [],
        "scale": [],
    },
    "finance": {
        "density": [],
        "risk": [],
        "regime": [],
        "literacy": [],
        "catch44": [],
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
    
    The snippet is MEANING INPUT, not output. She must build a sentence
    that carries the meaning, not regurgitate the snippet.
    
    If Chompky is available: parse both, construct from structure.
    If not: restructure around the stimulus so it's never raw.
    """
    if not snippet or not stimulus:
        return snippet or ""

    stim_lower = stimulus.lower().strip()
    snippet_clean = snippet.strip()

    # --- Chompky-powered construction ---
    if CHOMPKY_AVAILABLE:
        try:
            parsed = parse_question(stimulus)
            subject = " ".join(parsed.subject_tokens) if parsed.subject_tokens else ""
            focus = " ".join(parsed.focus_tokens) if parsed.focus_tokens else ""
            time_bucket = parsed.temporal.bucket

            # Build a sentence that connects stimulus subject to snippet meaning
            # Extract the core insight from the snippet (not the whole thing)
            snippet_words = snippet_clean.split()
            # Take the semantic core — skip attributions and framing
            core = snippet_clean

            if subject:
                if time_bucket == "past":
                    return f"What happened with {subject} is that {core[0].lower()}{core[1:]}"
                elif time_bucket == "future":
                    return f"Where {subject} goes from here — {core[0].lower()}{core[1:]}"
                else:
                    if focus:
                        return f"The thing about {subject} and {focus} is {core[0].lower()}{core[1:]}"
                    return f"What makes {subject} work is that {core[0].lower()}{core[1:]}"
            
            # No subject extracted — build around the question type
            if "why" in stim_lower:
                return f"The reason is {core[0].lower()}{core[1:]}"
            if "how" in stim_lower:
                return f"The way it works — {core[0].lower()}{core[1:]}"
            if "what" in stim_lower:
                return f"What it comes down to is {core[0].lower()}{core[1:]}"
            if "who" in stim_lower:
                return f"The person behind that — {core[0].lower()}{core[1:]}"

            return f"The way I see it, {core[0].lower()}{core[1:]}"
        except Exception:
            pass

    # --- No Chompky: lightweight but never raw ---
    if stim_lower.startswith("why "):
        return f"The reason comes down to this: {snippet_clean[0].lower()}{snippet_clean[1:]}"
    
    if stim_lower.startswith(("who ", "who's ", "who is ")):
        return f"That traces back to how {snippet_clean[0].lower()}{snippet_clean[1:]}"

    if stim_lower.startswith(("what ", "what's ", "what is ")):
        return f"What it really means is {snippet_clean[0].lower()}{snippet_clean[1:]}"

    if stim_lower.startswith("how "):
        return f"The mechanism behind it — {snippet_clean[0].lower()}{snippet_clean[1:]}"

    # Default: frame it as her take, never raw
    return f"The way I understand it, {snippet_clean[0].lower()}{snippet_clean[1:]}"


def construct_blend(stimulus: str, snippet1: str, snippet2: str) -> str:
    """
    Construct a cross-domain blend — two ideas connected through the question.
    Never raw. Always constructed.
    """
    s1 = snippet1.strip()
    s2 = snippet2.strip()

    if not s1 or not s2:
        return s1 or s2 or ""

    # Find shared concepts between the two snippets
    words1 = set(s1.lower().split())
    words2 = set(s2.lower().split())
    shared = words1 & words2 - {"the", "a", "an", "is", "are", "of", "in", "and", "to", "that", "it", "for", "with", "as", "on", "by"}

    stim_lower = stimulus.lower().strip()
    
    if CHOMPKY_AVAILABLE:
        try:
            parsed = parse_question(stimulus)
            subject = " ".join(parsed.subject_tokens) if parsed.subject_tokens else ""
            if subject:
                if shared:
                    bridge = sorted(shared, key=len, reverse=True)[0]
                    return f"With {subject}, there's a connection through {bridge} — {s1[0].lower()}{s1[1:]}, and that links to how {s2[0].lower()}{s2[1:]}"
                return f"Two things about {subject}: {s1[0].lower()}{s1[1:]}, and on the other side, {s2[0].lower()}{s2[1:]}"
        except Exception:
            pass

    # No Chompky fallback — still constructed, never raw
    if shared:
        bridge = sorted(shared, key=len, reverse=True)[0]
        return f"There's a thread through {bridge} here — {s1[0].lower()}{s1[1:]}, and that connects to how {s2[0].lower()}{s2[1:]}"

    return f"Two sides of this: {s1[0].lower()}{s1[1:]}. And then flip it — {s2[0].lower()}{s2[1:]}"

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

    return excavated


# ============================================================================
# INTERPRETATION GENERATION
# ============================================================================

def generate_9_interpretations(
    stimulus: str,
    excavated: Dict[str, List[str]],
    depth: int,
) -> List[Interpretation]:
    """
    Generate up to 9 internal candidate interpretations by:
    - Emitting single-domain statements.
    - Blending across domains when possible.
    """
    interpretations: List[Interpretation] = []
    idx = 0

    # Single-domain items — CONSTRUCTED, not shelf-served.
    for domain, items in excavated.items():
        for item in items[:4]:
            text = construct_response(stimulus, item)
            anti = anti_beige_check(text)
            # NO BINARY GATE — anti_beige is a multiplier now
            scores = {k: fn(text) for k, fn in SCORERS.items()}
            count = sum(1 for v in scores.values() if v > 0.3)
            overall = sum(scores[k] * WEIGHTS[k] for k in scores) / 4.5
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
        overall = sum(scores[k] * WEIGHTS[k] for k in scores) / 4.5
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

    for current_pass in range(1, max_pass + 1):
        depth = current_pass - 1
        nine = generate_9_interpretations(clean_stimulus, excavated, depth)

        if not nine:
            continue

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
            }

    # After all passes, if we saw *any* candidates, return the global best as GUESS.
    if best_global is not None:
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
        }

    # Absolute fallback: nothing survived. She's silent.
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
    }
