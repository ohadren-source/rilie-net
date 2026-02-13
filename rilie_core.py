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
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional


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
    "neuroscience": {
        "compression": [
            "Signal compression via synaptic pruning — unused connections eliminated",
            "Memory consolidation as dimensional reduction in neural manifolds",
            "Information theory: reduce redundancy while preserving signal integrity",
        ],
        "love": [
            "Bonding circuits show how WE > I through care over time",
            "Secure attachment patterns form the base layer of healthy relating",
        ],
        "fear": [
            "Threat detection: rapid discrimination of danger vs safety",
            "Extinction learning: fear decreases when prediction error is safe",
        ],
    },
    "music": {
        "compression": [
            "Rhythmic density: maximum information in minimal bar count",
            "Harmonic compression: tight voice-leading to pack emotion",
        ],
        "love": [
            "Call and response as musical structure of connection",
            "Major-seventh harmony carrying bittersweet romantic tension",
        ],
        "fear": [
            "Tritone and dissonance as universal triggers for unease",
            "Rising tempo mimicking physiological panic escalation",
        ],
        "satire": [
            "Flavor Flav used comedy as a Trojan horse — the clock, the hype, the clowning — to deliver truths that a straight face couldn't",
            "911 Is a Joke exposed emergency response failure in Black neighborhoods by making you laugh first, then making you think",
            "Satire in hip-hop works because it gives the listener permission to engage with uncomfortable truth through rhythm",
        ],
        "production": [
            "Bomb Squad production built dense, noisy collages — media overload as art form",
            "Sample layering as cultural archaeology — every chop carries the weight of its source",
            "The wall of noise wasn't chaos, it was architecture — every siren and scream placed with intent",
        ],
    },
    "psychology": {
        "compression": [
            "Cognitive load: working-memory limits on simultaneous thoughts",
            "Defense mechanisms as affect compression under stress",
        ],
        "love": [
            "Attachment styles: secure, anxious, avoidant, disorganized",
            "Vulnerability as prerequisite for intimacy and self-expansion",
        ],
        "fear": [
            "Catastrophizing: over-weighting worst-case possibilities",
            "Social anxiety: fear of judgment from the imagined crowd",
        ],
    },
    "culture": {
        "hip_hop": [
            "Public Enemy reframed hip-hop as political broadcast, not just party music",
            "Chuck D's voice carried news at street-level when institutions failed",
            "Flavor Flav embodied the trickster archetype — making bitter truth palatable through performance",
            "Fear of a Black Planet was sonic journalism — every track a dispatch from the front lines of American racism",
        ],
        "film": [
            "Montage as compression at speed in visual storytelling",
            "Diegetic sound grounding abstract ideas in physical worlds",
        ],
        "resistance": [
            "Fight the Power wasn't just a song — it was a blueprint for how art mobilizes communities",
            "It Takes a Nation of Millions showed that an album could function as both entertainment and education simultaneously",
            "The Bomb Squad's production on Fear of a Black Planet turned information overload into a weapon against complacency",
        ],
    },

    # --- NEW DOMAINS (matching library_index engines) ---

    "physics": {
        "conservation": [
            "Conservation laws: energy, momentum, charge — nothing is created or destroyed, only transformed",
            "Symmetry underlies every conservation law — Noether's theorem is the universe's own compression algorithm",
            "The arrow of time flows one direction — entropy increases, and that's the cost of every transaction",
        ],
        "relativity": [
            "Mass-energy equivalence: E=mc² means matter is just frozen energy waiting to move",
            "Frame of reference determines what you observe — position shapes perception, in physics and in life",
            "Spacetime curves around mass — influence bends the fabric, doesn't just travel through it",
        ],
        "quantum": [
            "Superposition: both states exist until observation collapses the wave function — Catch 44's Track 0",
            "Entanglement: separated particles stay correlated — connection doesn't require proximity",
            "Uncertainty principle: the more precisely you know position, the less you know momentum — you can't pin everything down",
        ],
    },
    "life": {
        "biology": [
            "Cancer is a cell that forgot ego → 0 — it prioritizes self-replication over the organism",
            "Apoptosis: programmed cell death is the ultimate service — dying so the whole can thrive",
            "Ecosystem stability depends on biodiversity — monocultures collapse, diversity sustains",
        ],
        "evolution": [
            "Natural selection isn't survival of the fittest — it's survival of the most adapted to change",
            "Symbiosis: cooperation is as fundamental to evolution as competition",
            "Emergence: complex behavior arises from simple rules applied recursively — ants, brains, markets",
        ],
        "health": [
            "The immune system distinguishes self from non-self — identity is a biological imperative",
            "Gut-brain axis: what you feed yourself shapes how you think — nourishment is literal",
            "Circadian rhythms: the body has its own clock — ignoring it costs more than you think",
        ],
    },
    "games": {
        "game_theory": [
            "Prisoner's dilemma: individual rationality produces collective irrationality — ego vs WE",
            "Tit-for-tat wins iterated games: cooperate first, then mirror — grace with memory",
            "Nash equilibrium: no one can improve by changing strategy alone — the system holds",
        ],
        "trust": [
            "Trust is built in drops and lost in buckets — 49 years of grace, one violation to lose it",
            "Reputation is a public good — once established, it reduces transaction costs for everyone",
            "Commitment devices work because they remove the option to defect — burning the ships",
        ],
        "incentives": [
            "Misaligned incentives produce misaligned behavior — if you reward extraction, you get extraction",
            "Public goods are under-provided because free-riders can't be excluded — tragedy of the commons",
            "Mechanism design: build the rules so the selfish choice is also the cooperative choice",
        ],
    },
    "thermodynamics": {
        "entropy": [
            "Entropy always increases in a closed system — disorder is the natural direction without input",
            "Free energy is what does work — the rest is waste heat, noise, beige",
            "Equilibrium is death — living systems maintain themselves far from equilibrium through constant energy flow",
        ],
        "harm_repair": [
            "Harm is thermodynamically irreversible — you can repair but never fully restore the original state",
            "The cost of repair always exceeds the cost of prevention — the physics of 'sorry' vs 'careful'",
            "Cascade failure: one broken component under load breaks the next — harm propagates through topology",
        ],
        "catch44": [
            "Catch-44 integrity check: is the system still far from equilibrium? Still doing work? Still alive?",
            "Ego as entropy source: self-centered action increases disorder in the network",
            "Grace as negentropy: service, care, and ego → 0 are the energy input that keeps the system alive",
        ],
    },
    "cosmology": {
        "origin": [
            "The universe began as a boolean tick — something rather than nothing, 0 becoming 1",
            "Reality as simulation hypothesis: the substrate doesn't change the experience",
            "DuckSauce: the universe kernel where existence bootstraps from the simplest possible operation",
        ],
        "scale": [
            "Fractal structure: the same patterns at every scale — atoms, cells, societies, galaxies",
            "The observable universe is a horizon, not a boundary — there's more we can't see",
            "Dark energy: 68% of the universe is something we can detect but not explain — humility built in",
        ],
    },
    "finance": {
        "density": [
            "Density is destiny — 5 signals compressed into 1 conviction score beats 50 weak indicators",
            "Signal quality over frequency: one DIAMOND trade beats nine BRONZE trades",
            "Market density = pattern quality + volume confirmation + breadth alignment + momentum + conviction",
            "Adaptive thresholds: what counted as strong signal yesterday may be noise today",
        ],
        "risk": [
            "Accordion risk: expand allocation when performance earns it, contract when chaos arrives",
            "Baby → Diamond evolution: a system must prove itself at small scale before earning larger bets",
            "Position sizing by conviction tier: DIAMOND gets full allocation, BRONZE gets a quarter",
            "2% floor: even in maximum contraction, never go fully to zero — ego → 0, not ego = 0",
            "Risk is not the enemy. UNEARNED risk is the enemy. Let the track record decide.",
        ],
        "regime": [
            "Market regimes: NORMAL (trade), CHAOS (contract), STAGNATION (wait) — like thermodynamic states",
            "VIX > 25 = fear dominates. Fear is information, not instruction. Contract but don't flee.",
            "Stagnation is entropy maximized — the market has no energy differential to exploit. Wait for the gradient.",
        ],
        "literacy": [
            "Survival → Security → Moves: three circles of financial awareness, like Maslow for money",
            "Get rich slow cook + live tryin: wealth is a process, not an event. Compound, don't gamble.",
            "The cheese pull: good financial advice stretches — one insight connects to the next",
            "Financial literacy is not about knowing numbers. It's about understanding which numbers matter.",
            "Budget is ego → 0 applied to money: what do you actually NEED vs what does your ego want?",
        ],
        "catch44": [
            "Night Trader works while you sleep — the market is a 24-hour topology that rewards the patient",
            "Fortune 100 only: trade the strongest companies, not lottery tickets. Quality ingredients make quality meals.",
            "Every trade has a stop loss because claim must equal deed — if the thesis is wrong, exit with integrity",
            "The market is the ultimate Catch 44: you need conviction to win but ego to lose",
        ],
    },
}

# Quick keyword hooks to detect which domains to lean on.
DOMAIN_KEYWORDS: Dict[str, List[str]] = {
    "neuroscience": ["brain", "neural", "synapse", "signal", "memory", "conscious"],
    "music": [
        "rhythm", "harmony", "tempo", "tone", "beat", "song", "rap", "hip-hop",
        "hip hop", "album", "music", "flav", "flavor", "chuck", "bomb squad",
        "production", "satire", "lyric", "lyrics", "verse", "hook", "sample",
        "biting", "joke", "911",
    ],
    "psychology": ["emotion", "fear", "love", "anxiety", "attachment", "therapy"],
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
# DOMAIN DETECTION & EXCAVATION
# ============================================================================

def detect_domains(stimulus: str) -> List[str]:
    sl = (stimulus or "").lower()
    scores = {
        d: sum(1 for kw in kws if kw in sl)
        for d, kws in DOMAIN_KEYWORDS.items()
    }
    # Sort by descending score, keep best 4 (increased from 3 for expanded domains)
    # including zeros to guarantee at least one.
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

    # Single-domain items.
    for domain, items in excavated.items():
        for item in items[:4]:
            text = item
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
        text = f"{i1} — {i2}"
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
) -> Dict:
    """
    Run interpretation passes.  Called only at OPEN or FULL disclosure.

    Now accepts baseline_results so it can compute the external trite meter.
    Also detects and applies curiosity context if present in the stimulus.

    Behavior:
    - Extracts curiosity context if injected by rilie.py.
    - Sets external trite score before generating interpretations.
    - Sets curiosity bonus if her own discoveries are relevant.
    - Always tries up to max_pass depths (capped at 9).
    - Anti-beige is a CURVE: penalizes but does not kill candidates.
    - If any candidates survive, ALWAYS returns the best one:
      * "COMPRESSED" for early/shallow question types.
      * "GUESS" when thresholds aren't hit but something exists.
    - Only if NO interpretations survive at all does it return
      the global "MISE_EN_PLACE" fallback.

    There is NO normal COURTESY_EXIT here; courtesy exits live in rilie.py
    as OHAD-style last resorts after this pipeline runs.
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

    hard_cap = 9
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

        # Thresholds — lowered slightly since beige curve means more candidates survive
        filtered = [
            i
            for i in nine
            if i.overall_score > (0.15 if current_pass == 1 else 0.25)
            or i.count_met >= (1 if current_pass == 1 else 2)
        ]

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

    # Absolute fallback: Mise en Place.  This is extremely rare now
    # because the beige curve no longer kills candidates outright.
    return {
        "stimulus": clean_stimulus,
        "result": "Everything in its right place",
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
