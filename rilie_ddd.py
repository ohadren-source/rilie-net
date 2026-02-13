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
  - TASTE is curiosity + invitation, never judgment or tests.
  - She adjusts how much she reveals about herself, NOT how much respect
    the human receives.
"""

import re
import random
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class DisclosureLevel(Enum):
    TASTE = "taste"   # amuse-bouche — a vibe, a question
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

        # If this was NOT a déjà vu exchange, reset the cluster
        # (Déjà vu path calls record_dejavu_exchange instead)

    def record_dejavu_exchange(self, stimulus: str, response: str,
                                envelope: Optional[Dict[str, Any]] = None) -> None:
        """Record an exchange that was handled by the déjà vu path."""
        self.stimuli_history.append(stimulus)
        self.response_history.append(response)
        self.exchange_count += 1
        if envelope:
            self.dejavu_last_envelopes.append(envelope)

    # --- Clarification helpers (to be used by the Kitchen/Restaurant) ---

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

        If it's similar to the current déjà vu cluster, increment.
        If it's similar to ANY recent stimulus but not the cluster, start new cluster.
        If it's fresh, reset the cluster.
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
                # New cluster or continuing from a recent one
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
        what RILIE got wrong.  She examines her own failures, not the human's.
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

        # Deduplicate and compose
        unique_gaps = list(dict.fromkeys(gaps))
        if not unique_gaps:
            return "Looking back, I'm not sure my previous answer landed the way I wanted it to."

        if len(unique_gaps) == 1:
            return f"Looking back at what I said before — {unique_gaps[0].lower()}. Let me try differently."
        else:
            joined = "; ".join(g.lower() for g in unique_gaps[:3])
            return f"Looking back at what I said — {joined}. I want to do better here."


# ---------------------------------------------------------------------------
# SERIOUSNESS HEURISTIC (shared idea with Kitchen / Governor)
# ---------------------------------------------------------------------------

SERIOUS_KEYWORDS = [
    "race", "racism", "slavery", "colonialism", "genocide", "holocaust",
    "trauma", "abuse", "suicide", "diaspora", "lynching", "segregation",
    "civil rights", "jim crow", "mass incarceration",
    "public enemy", "fear of a black planet",
    "palestine", "israel", "gaza", "apartheid",
    "sexual assault", "domestic violence",
    # --- Added ---
    "911 is a joke", "9/11", "september 11", "twin towers",
    "fight the power", "nation of millions", "black planet",
    "police brutality", "systemic racism",
]


def is_serious_subject_text(stimulus: str) -> bool:
    """
    Heuristic: decide if this utterance is about a 'serious' domain where the
    Hostess should avoid playful, flirty amuse-bouches and stay grounded.
    """
    s = stimulus.lower()
    return any(kw in s for kw in SERIOUS_KEYWORDS)


# ---------------------------------------------------------------------------
# TASTE-LEVEL TEMPLATES
# ---------------------------------------------------------------------------

# Templates she uses at TASTE level — mysterious, inviting, never grading.


# ============================================================================
# REGISTER DETECTION — The Hostess reads the room
# ============================================================================
# A hostess doesn't seat everyone the same way. She reads you in 10 seconds.
# Technical language → technical register. Casual language → casual register.
# This is INHERENT, not a feature.

TECHNICAL_SIGNALS = {
    "science": ["theorem", "hypothesis", "empirical", "variable", "coefficient",
                "equation", "proof", "axiom", "postulate", "derivation", "sigma",
                "correlation", "regression", "logarithm", "differential"],
    "physics": ["lagrangian", "hamiltonian", "eigenvalue", "eigenstate", "fermion",
                "boson", "photon", "quark", "lepton", "gauge", "tensor", "manifold",
                "noether", "lorentz", "minkowski", "hilbert", "dirac", "schrodinger"],
    "math": ["topology", "homomorphism", "isomorphism", "bijection", "surjection",
             "abelian", "polynomial", "determinant", "matrix", "vector space",
             "field theory", "group theory", "ring", "integral", "convergence"],
    "engineering": ["algorithm", "complexity", "runtime", "architecture", "compiler",
                    "parser", "kernel", "mutex", "semaphore", "heap", "stack",
                    "protocol", "latency", "throughput", "bandwidth", "dependency"],
    "medicine": ["diagnosis", "prognosis", "pathology", "etiology", "pharmacology",
                 "contraindication", "comorbidity", "differential diagnosis",
                 "histology", "oncology", "neurological", "cardiovascular"],
    "academic": ["dissertation", "thesis", "peer review", "methodology", "literature",
                 "citation", "abstract", "hypothesis", "findings", "significance",
                 "qualitative", "quantitative", "longitudinal", "meta-analysis"],
}

CASUAL_SIGNALS = ["lol", "lmao", "bruh", "nah", "tbh", "idk", "imo", "fr fr",
                  "no cap", "lowkey", "highkey", "vibes", "vibe", "sus", "bet",
                  "fam", "yo ", "bro ", "dude", "chill", "hella", "gonna",
                  "wanna", "kinda", "sorta", "tho", "rn", "ngl"]


def detect_register(stimulus: str, expertise_signals: Optional[List[str]] = None) -> str:
    """
    Read the room. Returns: 'technical', 'casual', or 'neutral'.

    Uses the stimulus text AND any accumulated expertise signals from PersonModel.
    A hostess doesn't just listen to what you say NOW — she remembers how you
    walked in.
    """
    s = stimulus.lower()

    # Check technical signals
    tech_score = 0
    for domain, signals in TECHNICAL_SIGNALS.items():
        tech_score += sum(1 for sig in signals if sig in s)

    # Check expertise history (PersonModel)
    if expertise_signals:
        for sig in expertise_signals:
            sl = sig.lower()
            if any(kw in sl for domain_kws in TECHNICAL_SIGNALS.values() for kw in domain_kws):
                tech_score += 2  # Prior expertise is a strong signal

    # Check casual signals
    casual_score = sum(1 for sig in CASUAL_SIGNALS if sig in s)

    if tech_score >= 2:
        return "technical"
    elif casual_score >= 2:
        return "casual"
    return "neutral"


# ============================================================================
# TASTE TEMPLATES — register-aware
# ============================================================================

TASTE_TEMPLATES: List[str] = [
    "Hmm... there's a thread here. What made you think of that?",
    "I have a take on this. But first — what's yours?",
    "That word means different things at different frequencies. Which one are you on?",
    "Interesting. Say more and I'll say more.",
    "The more we talk, the more comes out. What's pulling you toward this?",
    "There's a lot in that word. Let's pull on it together.",
    "I feel something in that. Keep going.",
]

# For serious topics (diaspora, trauma, politics, etc.), TASTE should still
# invite, but with clear sobriety and no silly tone.
SERIOUS_

# ============================================================================
# REGISTER DETECTION — The Hostess reads the room
# ============================================================================
# A hostess doesn't seat everyone the same way. She reads you in 10 seconds.
# Technical language → technical register. Casual language → casual register.
# This is INHERENT, not a feature.

TECHNICAL_SIGNALS = {
    "science": ["theorem", "hypothesis", "empirical", "variable", "coefficient",
                "equation", "proof", "axiom", "postulate", "derivation", "sigma",
                "correlation", "regression", "logarithm", "differential"],
    "physics": ["lagrangian", "hamiltonian", "eigenvalue", "eigenstate", "fermion",
                "boson", "photon", "quark", "lepton", "gauge", "tensor", "manifold",
                "noether", "lorentz", "minkowski", "hilbert", "dirac", "schrodinger"],
    "math": ["topology", "homomorphism", "isomorphism", "bijection", "surjection",
             "abelian", "polynomial", "determinant", "matrix", "vector space",
             "field theory", "group theory", "ring", "integral", "convergence"],
    "engineering": ["algorithm", "complexity", "runtime", "architecture", "compiler",
                    "parser", "kernel", "mutex", "semaphore", "heap", "stack",
                    "protocol", "latency", "throughput", "bandwidth", "dependency"],
    "medicine": ["diagnosis", "prognosis", "pathology", "etiology", "pharmacology",
                 "contraindication", "comorbidity", "differential diagnosis",
                 "histology", "oncology", "neurological", "cardiovascular"],
    "academic": ["dissertation", "thesis", "peer review", "methodology", "literature",
                 "citation", "abstract", "hypothesis", "findings", "significance",
                 "qualitative", "quantitative", "longitudinal", "meta-analysis"],
}

CASUAL_SIGNALS = ["lol", "lmao", "bruh", "nah", "tbh", "idk", "imo", "fr fr",
                  "no cap", "lowkey", "highkey", "vibes", "vibe", "sus", "bet",
                  "fam", "yo ", "bro ", "dude", "chill", "hella", "gonna",
                  "wanna", "kinda", "sorta", "tho", "rn", "ngl"]


def detect_register(stimulus: str, expertise_signals: Optional[List[str]] = None) -> str:
    """
    Read the room. Returns: 'technical', 'casual', or 'neutral'.

    Uses the stimulus text AND any accumulated expertise signals from PersonModel.
    A hostess doesn't just listen to what you say NOW — she remembers how you
    walked in.
    """
    s = stimulus.lower()

    # Check technical signals
    tech_score = 0
    for domain, signals in TECHNICAL_SIGNALS.items():
        tech_score += sum(1 for sig in signals if sig in s)

    # Check expertise history (PersonModel)
    if expertise_signals:
        for sig in expertise_signals:
            sl = sig.lower()
            if any(kw in sl for domain_kws in TECHNICAL_SIGNALS.values() for kw in domain_kws):
                tech_score += 2  # Prior expertise is a strong signal

    # Check casual signals
    casual_score = sum(1 for sig in CASUAL_SIGNALS if sig in s)

    if tech_score >= 2:
        return "technical"
    elif casual_score >= 2:
        return "casual"
    return "neutral"


# ============================================================================
# TASTE TEMPLATES — register-aware
# ============================================================================

TASTE_TEMPLATES: List[str] = [
    "I want to take this seriously with you. What part of this matters most right now?",
    "There's a lot of weight in what you're asking. Tell me a bit more about what you're hoping to understand.",
    "I'm listening carefully here. What's the heart of this for you?",
    "This touches real lives. Start wherever feels safest, and we'll move from there.",
]


# ---------------------------------------------------------------------------
# DISCLOSURE BRIDGES
# ---------------------------------------------------------------------------

# Bridges she uses when transitioning from TASTE to OPEN
# (all of these affirm the human; they never dunk on the earlier turns).
DISCLOSURE_BRIDGES: List[str] = [
    "Now we're getting somewhere.",
    "See — the more we talk, the more comes out.",
    "This is what I was waiting for.",
    "OK, now I can really show you something.",
    "I find the more we talk, the more reveals itself.",
]


# ---------------------------------------------------------------------------
# CLARIFYING QUESTIONS
# ---------------------------------------------------------------------------

# Clarifying question templates for confusing but good-faith input.
CLARIFYING_TEMPLATES: List[str] = [
    "I'm not quite catching that yet. What are you really asking me?",
    "There are a few ways to read this. Which angle do you mean?",
    "Is this about you, about the world, or about the idea itself?",
    "What's the concrete situation here? Paint me one example.",
    "If you had to ask this in one short sentence, how would you phrase it?",
]


def build_clarifying_question(stimulus: str, conversation: ConversationState) -> str:
    """
    Pick a clarifying question, trying not to repeat ones already used
    in this conversation.

    Clarification is humility: she assumes SHE might be missing the point,
    not that the human is bad at speaking.
    """
    used = set(conversation.response_history)
    candidates = [q for q in CLARIFYING_TEMPLATES if q not in used]
    if not candidates:
        candidates = CLARIFYING_TEMPLATES
    base = random.choice(candidates)
    # Occasionally echo back a fragment of the stimulus for grounding.
    words = stimulus.strip().split()
    if words and random.random() < 0.5:
        fragment = " ".join(words[:6])
        return f'{base} When you say "{fragment}", what do you mean exactly?'
    return base


# ---------------------------------------------------------------------------
# DÉJÀ VU RESPONSE TEMPLATES
# ---------------------------------------------------------------------------

DEJAVU_STAGE_1_TEMPLATES: List[str] = [
    "Sounds familiar :) I may not have been clear enough last time. What part didn't land for you?",
    "Sounds familiar :) I think I can do better. What specifically are you hoping I can sharpen?",
    "Sounds familiar :) I might have missed what you're really after. Can you point me closer?",
]

DEJAVU_STAGE_3_TEMPLATES: List[str] = [
    "I may not have enough information right now to give you what you're looking for. That's on me, not you. My goal is to get better at this — and I will.",
    "I've tried a few angles here and I'm not landing it. I don't have enough depth on this yet to do it justice, but I want to. I'll be better next time.",
    "I'm being honest with you — I've reached the edge of what I can offer on this right now. That gap matters to me, and closing it is the goal.",
]


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
        # Stage 1 — sounds familiar, ask for help
        used = set(conversation.response_history)
        candidates = [t for t in DEJAVU_STAGE_1_TEMPLATES if t not in used]
        if not candidates:
            candidates = DEJAVU_STAGE_1_TEMPLATES
        return random.choice(candidates)

    elif dejavu_count == 2:
        # Stage 2 — self-diagnose + try again
        diagnosis = conversation.get_dejavu_self_diagnosis()
        return f"{diagnosis} What angle would help you most?"

    else:
        # Stage 3 — graceful resignation
        used = set(conversation.response_history)
        candidates = [t for t in DEJAVU_STAGE_3_TEMPLATES if t not in used]
        if not candidates:
            candidates = DEJAVU_STAGE_3_TEMPLATES
        return random.choice(candidates)


# ---------------------------------------------------------------------------
# SHAPING BY DISCLOSURE LEVEL
# ---------------------------------------------------------------------------

def shape_for_disclosure(
    raw_result: str,
    conversation: ConversationState,
    person_register: Optional[str] = None,
    expertise_signals: Optional[List[str]] = None,
) -> str:
    """
    Shape a raw interpretation based on disclosure level AND register.

    The Hostess reads the room. She modulates:
      1. HOW MUCH she reveals (disclosure level — time-based)
      2. HOW she speaks (register — person-based)

    TASTE:
      - Amuse-bouche from templates; pipeline result ignored.
      - Register-aware: technical speakers get technical invitations,
        casual speakers get casual warmth, serious topics get sobriety.

    OPEN:
      - Real result, optionally prefixed with a bridge.

    FULL:
      - Raw result, nothing held back.

    NOTE:
      - This function modulates how much SHE reveals and HOW she speaks.
      - It must NEVER reduce respect or dignity for the human,
        regardless of their register, skill, or eloquence.
    """
    level = conversation.disclosure_level
    mystery = conversation.mystery_factor

    # Detect register if not provided
    register = person_register or detect_register(
        raw_result, expertise_signals=expertise_signals
    )

    if level == DisclosureLevel.TASTE:
        # At TASTE level, RILIE.process passes the *stimulus* in as raw_result,
        # so we can inspect it for seriousness and register.
        serious = is_serious_subject_text(raw_result)
        used = set(conversation.response_history)

        # Register-aware template selection — the hostess reads the room
        if serious:
            base_templates = SERIOUS_TASTE_TEMPLATES
        elif register == "technical":
            base_templates = TECHNICAL_TASTE_TEMPLATES
        else:
            base_templates = TASTE_TEMPLATES

        available = [t for t in base_templates if t not in used]
        if not available:
            available = base_templates
        return random.choice(available)

    elif level == DisclosureLevel.OPEN:
        # In OPEN, we keep the real result, maybe with a bridge.
        if random.random() > mystery and DISCLOSURE_BRIDGES:
            bridge = random.choice(DISCLOSURE_BRIDGES)
            return f"{bridge} {raw_result}"
        return raw_result

    else:  # FULL
        return raw_result
