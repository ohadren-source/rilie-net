"""
meaning.py — THE SUBSTRATE (v1.0)

====================================
The missing API. The one between Chomsky and the Kitchen.

Before RILIE searches, before she cooks, before she speaks —
she reads. This is how she reads.

Four reads. One fingerprint. No domain knowledge required.

    stimulus arrives
        → Chomsky: is it a sentence? (syntax)
        → meaning.py: what does it mean? (THIS)
        → Triangle: is it safe?
        → Kitchen: cook the response

FORMULAS:

    ① PULSE (alive or dead?)
        P = (U × V) / W
        where:
            U = uniqueness — ratio of non-stopword tokens to total tokens
            V = verb energy — presence and strength of action/state verbs
            W = word count (normalized)

        P > threshold → alive → continue
        P ≤ threshold → dead → discard

        Why it works: dead inputs are either all stopwords ("the of and"),
        all filler ("um well you know like"), or empty repetition.
        A pulse means something is TRYING to happen in the sentence.

    ② INTENT (get, give, or show?)
        I = argmax(GET, GIVE, SHOW)
        where:
            GET  = question_markers + request_verbs + missing_object_signals
            GIVE = declaration_markers + first_person_claims + offering_verbs  
            SHOW = demonstrative_markers + reference_signals + evidence_verbs

        Compound intents are valid: "I'm hurting" = GIVE + GET
        Primary intent = highest score. Secondary = second highest if > 0.3

    ③ OBJECT (about what, irreducibly?)
        O = compress(nouns ∪ noun_phrases, merge_threshold)

        Not topic detection. Not keyword extraction. COMPRESSION.
        "whether my code architecture reflects my values" → "alignment"

        The rule: if two nouns in the stimulus are ABOUT the same 
        underlying thing, merge them. Keep merging until you can't.
        What's left is the irreducible object.

        Uses Chomsky's dependency parse to find the ROOT object,
        then folds modifiers and satellites into it.

    ④ WEIGHT (how much does this matter?)
        M = (depth × brevity) + personal_markers
        where:
            depth = abstract_noun_ratio + existential_signals
            brevity = 1 / (word_count / concept_count)  
            personal_markers = first_person + family + emotion signals

        Short sentence + big topic = HEAVY (high weight)
        Long sentence + small topic = LIGHT (low weight)

        Why: people use fewer words for things that matter more.
        "My mom has cancer." — 4 words, infinite weight.
        "I was wondering if perhaps you might know..." — many words, light.

OUTPUT — The Meaning Fingerprint:

    {
        "pulse": 0.0-1.0,       # alive or dead
        "act": "GET|GIVE|SHOW",  # primary intent  
        "act2": "GET|GIVE|SHOW|None",  # secondary intent (if compound)
        "object": str,           # irreducible subject
        "weight": 0.0-1.0,      # how much it matters
        "gap": str|None          # what's missing/implied (Step 5 — excavation starter)
    }

AXIOMS:
    - No domain knowledge. This runs BEFORE the Library.
    - No search. This runs BEFORE Banks.
    - No LLM. This is deterministic.
    - Chomsky parse is the only input besides the raw string.
    - The fingerprint is READ-ONLY downstream. Nothing modifies it.
      It is the stimulus's birth certificate.

"""

import re
import math
import logging
from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict, Any

logger = logging.getLogger("meaning")


# ============================================================================
# CONSTANTS — the vocabulary of surface reading
# ============================================================================

STOPWORDS = frozenset({
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "dare", "ought",
    "to", "of", "in", "for", "on", "with", "at", "by", "from", "as",
    "into", "through", "during", "before", "after", "above", "below",
    "between", "out", "off", "over", "under", "again", "further", "then",
    "once", "here", "there", "when", "where", "why", "how", "all", "each",
    "every", "both", "few", "more", "most", "other", "some", "such", "no",
    "nor", "not", "only", "own", "same", "so", "than", "too", "very",
    "just", "because", "but", "and", "or", "if", "while", "although",
    "this", "that", "these", "those", "i", "me", "my", "myself", "we",
    "our", "ours", "you", "your", "yours", "he", "him", "his", "she",
    "her", "hers", "it", "its", "they", "them", "their", "what", "which",
    "who", "whom", "up", "about", "also", "like", "um", "uh", "well",
    "yeah", "okay", "ok", "right", "know", "think", "got", "get",
    "really", "actually", "basically", "literally", "just", "thing",
})

FILLER_WORDS = frozenset({
    "um", "uh", "like", "you know", "basically", "literally", "actually",
    "sort of", "kind of", "i mean", "well", "so", "anyway", "right",
})

# --- Intent vocabularies ---

QUESTION_MARKERS = frozenset({
    "?", "what", "why", "how", "when", "where", "who", "which",
    "can you", "could you", "would you", "do you", "is there",
    "explain", "tell me", "help", "wondering",
})

REQUEST_VERBS = frozenset({
    "explain", "tell", "show", "help", "give", "teach", "describe",
    "clarify", "define", "break down", "walk me through", "elaborate",
})

DECLARATION_MARKERS = frozenset({
    "i think", "i believe", "i feel", "i know", "i realized",
    "i noticed", "i built", "i made", "i wrote", "i discovered",
    "i learned", "here's what", "the thing is", "my point is",
    "i love", "i hate", "i need", "i want", "i am", "i'm",
})

OFFERING_VERBS = frozenset({
    "sharing", "telling", "showing", "giving", "offering",
    "confessing", "admitting", "expressing",
})

DEMONSTRATIVE_MARKERS = frozenset({
    "look at", "check this", "here's", "this is", "see this",
    "watch this", "notice", "observe", "consider",
})

EVIDENCE_VERBS = frozenset({
    "look", "see", "check", "watch", "notice", "observe",
    "read", "examine", "review", "consider",
})

# --- Weight vocabularies ---

EXISTENTIAL_SIGNALS = frozenset({
    "meaning", "purpose", "life", "death", "love", "truth", "beauty",
    "consciousness", "existence", "reality", "god", "soul", "faith",
    "identity", "freedom", "justice", "suffering", "hope", "fear",
    "cancer", "dying", "born", "forever", "never", "always", "everything",
    "nothing", "impossible", "infinite",
})

PERSONAL_MARKERS = frozenset({
    "my mom", "my dad", "my kid", "my son", "my daughter", "my wife",
    "my husband", "my partner", "my family", "my sister", "my brother",
    "i lost", "i survived", "i remember", "when i was", "i can't",
    "i need", "i love", "i miss", "i hurt", "i'm scared", "i'm afraid",
    "diagnosed", "passed away", "funeral", "hospital", "surgery",
})

ABSTRACT_NOUNS = frozenset({
    "truth", "beauty", "justice", "freedom", "love", "hate", "fear",
    "meaning", "purpose", "identity", "consciousness", "existence",
    "reality", "time", "space", "energy", "entropy", "emergence",
    "intelligence", "wisdom", "knowledge", "understanding", "signal",
    "quality", "integrity", "dignity", "compassion", "courage",
    "creativity", "curiosity", "mystery", "complexity", "simplicity",
    "alignment", "coherence", "resonance", "compression", "elegance",
})


# ============================================================================
# THE MEANING FINGERPRINT
# ============================================================================

@dataclass
class MeaningFingerprint:
    """
    The birth certificate of a stimulus.
    Read-only downstream. Nothing modifies it.
    """
    pulse: float            # 0.0-1.0 — alive or dead
    act: str                # GET, GIVE, or SHOW
    act2: Optional[str]     # secondary intent if compound
    object: str             # irreducible subject
    weight: float           # 0.0-1.0 — how much it matters
    gap: Optional[str]      # what's missing / implied

    def is_alive(self) -> bool:
        return self.pulse > 0.15

    def is_heavy(self) -> bool:
        return self.weight > 0.6

    def is_compound(self) -> bool:
        return self.act2 is not None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pulse": round(self.pulse, 3),
            "act": self.act,
            "act2": self.act2,
            "object": self.object,
            "weight": round(self.weight, 3),
            "gap": self.gap,
        }


# ============================================================================
# FORMULA ① — PULSE (alive or dead?)
# P = (U × V) / max(log(W), 1)
# ============================================================================

def _compute_pulse(tokens: List[str], raw: str) -> float:
    """
    Is there a pulse in this input?
    Dead = all stopwords, all filler, empty repetition, or nothing.
    Alive = something is TRYING to happen.
    """
    if not tokens:
        return 0.0

    total = len(tokens)
    if total == 0:
        return 0.0

    # U — uniqueness: ratio of meaningful tokens
    meaningful = [t for t in tokens if t.lower() not in STOPWORDS]
    unique_meaningful = set(meaningful)
    # Penalize repetition: unique meaningful / total
    U = len(unique_meaningful) / max(total, 1)

    # V — verb energy: does the input contain action?
    # Simple heuristic: common verb endings + known verbs
    verb_signals = {"do", "make", "build", "think", "feel", "know", "want",
                    "need", "love", "hate", "create", "explain", "try",
                    "help", "show", "give", "take", "go", "come", "run",
                    "work", "play", "fight", "learn", "teach", "grow",
                    "mean", "say", "tell", "ask", "understand", "see"}
    verb_hits = sum(1 for t in tokens if t.lower() in verb_signals)
    # Also check for -ing, -ed, -es endings as verb signals
    verb_hits += sum(1 for t in tokens
                     if len(t) > 3 and t.lower().endswith(("ing", "ed", "tion")))
    V = min(verb_hits / max(total, 1) * 3, 1.0)  # scale up, cap at 1

    # W — word count normalization (log scale so long inputs aren't penalized unfairly)
    W = max(math.log(total + 1), 1.0)

    pulse = (U * 0.6 + V * 0.4)  # weighted blend
    # Very short meaningful inputs (1-3 words) get a pulse floor if they have content
    if 0 < len(meaningful) <= 3 and len(meaningful) == len(unique_meaningful):
        pulse = max(pulse, 0.3)

    return min(pulse, 1.0)


# ============================================================================
# FORMULA ② — INTENT (get, give, or show?)
# I = argmax(GET, GIVE, SHOW)
# ============================================================================

def _compute_intent(tokens: List[str], raw: str) -> Tuple[str, Optional[str]]:
    """
    What is this utterance DOING in the world?
    Returns (primary_act, secondary_act_or_None)
    """
    lower = raw.lower()
    lower_tokens = [t.lower() for t in tokens]

    get_score = 0.0
    give_score = 0.0
    show_score = 0.0

    # GET signals — questions, requests, seeking
    if "?" in raw:
        get_score += 0.5
    for marker in QUESTION_MARKERS:
        if marker in lower:
            get_score += 0.15
    for verb in REQUEST_VERBS:
        if verb in lower:
            get_score += 0.2

    # GIVE signals — declarations, claims, offerings, emotions
    for marker in DECLARATION_MARKERS:
        if marker in lower:
            give_score += 0.2
    for verb in OFFERING_VERBS:
        if verb in lower:
            give_score += 0.15
    # Exclamation = emphasis = giving energy
    if "!" in raw:
        give_score += 0.1
    # First person statements without questions = giving
    if any(t in lower_tokens for t in ["i", "my", "me"]) and "?" not in raw:
        give_score += 0.1

    # SHOW signals — demonstratives, evidence, references
    for marker in DEMONSTRATIVE_MARKERS:
        if marker in lower:
            show_score += 0.25
    for verb in EVIDENCE_VERBS:
        if verb in lower:
            show_score += 0.1
    # URLs, file references, code blocks = showing
    if any(sig in lower for sig in ["http", ".py", ".js", "```", ".json"]):
        show_score += 0.3

    # Normalize
    total = get_score + give_score + show_score
    if total == 0:
        return ("GIVE", None)  # default: if they said something, they're giving

    scores = {"GET": get_score, "GIVE": give_score, "SHOW": show_score}
    ranked = sorted(scores.items(), key=lambda x: -x[1])

    primary = ranked[0][0]
    # Secondary only if it's substantial (> 30% of primary)
    secondary = None
    if ranked[1][1] > ranked[0][1] * 0.3 and ranked[1][1] > 0.1:
        secondary = ranked[1][0]

    return (primary, secondary)


# ============================================================================
# FORMULA ③ — OBJECT (about what, irreducibly?)
# O = compress(nouns, merge_threshold)
# ============================================================================

def _compute_object(tokens: List[str], raw: str) -> str:
    """
    What is this about at the most irreducible level?
    Not topic. Not keywords. The THING underneath.

    Without spaCy: extract non-stopword nouns/noun-like tokens,
    then compress by merging tokens that point at the same concept.
    """
    lower = raw.lower()
    meaningful = [t for t in tokens if t.lower() not in STOPWORDS and len(t) > 2]

    if not meaningful:
        return "unknown"

    # Concept clusters — tokens that collapse into one idea
    CONCEPT_MERGES = {
        # alignment family
        frozenset({"code", "values", "architecture", "reflects", "design", "ethics"}): "alignment",
        frozenset({"right", "wrong", "moral", "ethics", "justice", "fair"}): "ethics",
        # identity family
        frozenset({"who", "am", "identity", "self", "person", "me"}): "identity",
        # creation family
        frozenset({"build", "make", "create", "code", "write", "design", "built"}): "creation",
        # understanding family
        frozenset({"understand", "meaning", "explain", "why", "how", "know", "learn"}): "understanding",
        # connection family
        frozenset({"love", "relationship", "family", "together", "bond", "connect"}): "connection",
        # struggle family
        frozenset({"fight", "struggle", "hard", "pain", "hurt", "suffer", "battle"}): "struggle",
        # beauty family
        frozenset({"beauty", "beautiful", "elegant", "grace", "art", "aesthetic"}): "beauty",
        # truth family
        frozenset({"truth", "real", "honest", "genuine", "authentic", "true"}): "truth",
        # signal family
        frozenset({"signal", "noise", "quality", "filter", "clarity", "clear"}): "signal",
        # emergence family
        frozenset({"emerge", "emergence", "pattern", "arise", "grow", "evolve"}): "emergence",
        # compression family
        frozenset({"compress", "compression", "reduce", "simple", "minimal", "dense"}): "compression",
    }

    # Check which concept clusters activate
    meaningful_set = set(t.lower() for t in meaningful)
    best_merge = None
    best_overlap = 0

    for cluster_keys, concept in CONCEPT_MERGES.items():
        overlap = len(meaningful_set & cluster_keys)
        if overlap > best_overlap:
            best_overlap = overlap
            best_merge = concept

    if best_merge and best_overlap >= 2:
        return best_merge

    # No cluster match — return the most "heavy" single token
    # Prefer abstract nouns > concrete nouns > verbs
    for token in meaningful:
        if token.lower() in ABSTRACT_NOUNS:
            return token.lower()

    # Fall back to longest meaningful token (crude but honest)
    return max(meaningful, key=len).lower()


# ============================================================================
# FORMULA ④ — WEIGHT (how much does this matter?)
# M = (depth × brevity) + personal_markers
# ============================================================================

def _compute_weight(tokens: List[str], raw: str) -> float:
    """
    How much does this matter to the person saying it?
    Short + deep = heavy. Long + shallow = light.
    Personal markers amplify.
    """
    lower = raw.lower()
    total = len(tokens)
    if total == 0:
        return 0.0

    meaningful = [t for t in tokens if t.lower() not in STOPWORDS]

    # Depth — ratio of abstract/existential content
    depth_hits = sum(1 for t in tokens if t.lower() in EXISTENTIAL_SIGNALS)
    abstract_hits = sum(1 for t in tokens if t.lower() in ABSTRACT_NOUNS)
    depth = min((depth_hits + abstract_hits) / max(len(meaningful), 1), 1.0)

    # Brevity — fewer words for the same concept count = heavier
    concept_count = len(set(meaningful))  # unique meaningful tokens ≈ concepts
    if concept_count == 0:
        brevity = 0.0
    else:
        # Ideal: 1 word per concept. Penalize verbosity.
        brevity = min(concept_count / max(total, 1) * 2.5, 1.0)

    # Personal markers — family, health, existential personal stakes
    personal = 0.0
    for marker in PERSONAL_MARKERS:
        if marker in lower:
            personal += 0.15
    personal = min(personal, 0.4)  # cap so it doesn't overwhelm

    # Formula: weighted blend
    weight = (depth * 0.35) + (brevity * 0.25) + (personal * 0.4)

    # Floor: if personal markers are present, minimum weight
    if personal > 0:
        weight = max(weight, 0.4)

    return min(weight, 1.0)


# ============================================================================
# FORMULA ⑤ — GAP (what's missing?)
# The excavation starter. What would make this whole?
# ============================================================================

def _compute_gap(tokens: List[str], raw: str, act: str, obj: str) -> Optional[str]:
    """
    What did they NOT say that the sentence needs to be whole?
    This is the seed for RILIE's response direction.
    """
    lower = raw.lower()

    # Questions without specificity → gap is "which specifically?"
    if act == "GET" and obj == "unknown":
        return "underspecified question — needs clarification"

    # Emotional GIVE without a request → gap is "they need to be heard"
    emotion_words = {"feel", "feeling", "hurt", "love", "scared", "afraid",
                     "angry", "sad", "happy", "grateful", "lost", "confused",
                     "overwhelmed", "tired", "exhausted", "broken", "alive"}
    if act == "GIVE" and any(w in lower for w in emotion_words):
        return "emotional disclosure — needs acknowledgment before answer"

    # Technical SHOW without a question → gap is "they want validation"
    if act == "SHOW" and "?" not in raw:
        return "showing work — wants validation or feedback"

    # Short heavy input → gap is "there's more underneath"
    if len(tokens) < 8 and any(t.lower() in EXISTENTIAL_SIGNALS for t in tokens):
        return "compressed heavy thought — there's more underneath"

    # Long light input → gap is "get to the point"
    if len(tokens) > 30 and not any(t.lower() in ABSTRACT_NOUNS for t in tokens):
        return "verbose but shallow — core question is buried"

    return None


# ============================================================================
# PUBLIC API — one function, one fingerprint
# ============================================================================

def read_meaning(stimulus: str) -> MeaningFingerprint:
    """
    The missing API.

    Takes a string. Returns its meaning fingerprint.
    No LLM. No search. No domain knowledge. Pure parse.

    Call this BEFORE Triangle, BEFORE Kitchen, BEFORE everything.
    The fingerprint is the stimulus's birth certificate.
    Everything downstream reads it. Nothing modifies it.
    """
    if not stimulus or not stimulus.strip():
        return MeaningFingerprint(
            pulse=0.0, act="GIVE", act2=None,
            object="nothing", weight=0.0, gap="empty input"
        )

    raw = stimulus.strip()

    # Tokenize (simple whitespace + punctuation split)
    tokens = re.findall(r"[\w']+|[?!.,;:]", raw)

    # ① PULSE
    pulse = _compute_pulse(tokens, raw)

    # Dead input — minimal fingerprint
    if pulse <= 0.15:
        return MeaningFingerprint(
            pulse=pulse, act="GIVE", act2=None,
            object="noise", weight=0.0, gap="no signal detected"
        )

    # ② INTENT
    act, act2 = _compute_intent(tokens, raw)

    # ③ OBJECT
    obj = _compute_object(tokens, raw)

    # ④ WEIGHT
    weight = _compute_weight(tokens, raw)

    # ⑤ GAP
    gap = _compute_gap(tokens, raw, act, obj)

    return MeaningFingerprint(
        pulse=pulse,
        act=act,
        act2=act2,
        object=obj,
        weight=weight,
        gap=gap,
    )


# ============================================================================
# CLI DEMO
# ============================================================================

if __name__ == "__main__":
    test_stimuli = [
        "What is entropy?",
        "I think beauty is compression.",
        "Look at this code.",
        "My mom has cancer.",
        "um well like you know basically",
        "I built something that scales from particles to ecosystems using five formulas and some jokes.",
        "Why?",
        "I'm hurting.",
        "Can you explain the significance of Public Enemy?",
        "rilie.py",
        "",
    ]

    print("=" * 70)
    print("MEANING FINGERPRINT — SUBSTRATE API v1.0")
    print("=" * 70)

    for stim in test_stimuli:
        fp = read_meaning(stim)
        print(f"\nInput: \"{stim}\"")
        print(f"  pulse:  {fp.pulse:.3f}  {'ALIVE' if fp.is_alive() else 'DEAD'}")
        print(f"  act:    {fp.act}" + (f" + {fp.act2}" if fp.act2 else ""))
        print(f"  object: {fp.object}")
        print(f"  weight: {fp.weight:.3f}" + ("  HEAVY" if fp.is_heavy() else ""))
        print(f"  gap:    {fp.gap or '—'}")
    print("\n" + "=" * 70)
