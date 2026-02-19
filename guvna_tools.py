"""

guvna_tools.py

All standalone dataclasses, free functions, type aliases, and semantic clusters
used by the Guvna governor. No methods, no Guvna class.

REVISION: Wilden-Swift split into modulate (Guvna) + score (Talk).

"Big words do nothing but confuse and lose." — Rakim

"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger("guvna")

# ============================================================================
# STIMULUS NORMALIZATION — runs before anything else sees the input
# ============================================================================

# All the ways humans spell her name — all roads lead to RILIE
_RILIE_VARIANTS: List[str] = [
    "riley", "riely", "rylie", "rylee", "rily",
    "riliy", "rillie", "rilee", "rieley",
    "RILEY", "RYLIE", "RIELY", "RILY", "Rilie", "Riley",
]

# Words she should never "correct" or synonym-swap — proper nouns, brand terms
_PROTECTED_WORDS = {
    "rilie", "RILIE", "soi", "SOi", "sauc", "catch44", "catch-44",
    "escoffier", "chomsky", "guvna", "brootlyn",
}

# ── pyspellchecker ────────────────────────────────────────────────────────────
try:
    from spellchecker import SpellChecker as _SpellChecker
    _spell = _SpellChecker()
    _spell.word_frequency.load_words(list(_PROTECTED_WORDS))
    _SPELLCHECK_AVAILABLE = True
except ImportError:
    _SPELLCHECK_AVAILABLE = False
    _spell = None

# ── WordNet + wordfreq ────────────────────────────────────────────────────────
try:
    from nltk.corpus import wordnet as _wn
    from wordfreq import zipf_frequency as _zipf
    _WORDNET_AVAILABLE = True
except ImportError:
    _WORDNET_AVAILABLE = False
    _wn = None  # type: ignore
    _zipf = None  # type: ignore


def _common_synonym(word: str, pos: Optional[str] = None) -> str:
    """
    Return the most common synonym of `word` by Zipf frequency.
    If nothing beats the original, return the original unchanged.
    Common usage always wins over textbook vocabulary.

    pos: 'n' noun | 'v' verb | 'a' adj | 'r' adv | None = try all
    """
    if not _WORDNET_AVAILABLE or not _wn or not _zipf:
        return word

    if word.lower() in _PROTECTED_WORDS:
        return word

    synsets = _wn.synsets(word, pos=pos) if pos else _wn.synsets(word)
    if not synsets:
        return word

    candidates: Dict[str, float] = {}
    for synset in synsets[:3]:  # top 3 synsets only — don't over-expand
        for lemma in synset.lemmas():
            candidate = lemma.name().replace("_", " ")
            if candidate.lower() == word.lower():
                continue
            if candidate.lower() in _PROTECTED_WORDS:
                continue
            freq = _zipf(candidate, "en")
            if freq > 0:
                candidates[candidate] = freq

    if not candidates:
        return word

    # Always prefer the highest-frequency (most common) option
    best = max(candidates, key=lambda c: candidates[c])
    original_freq = _zipf(word, "en")

    # Only swap if the replacement is meaningfully more common
    if candidates[best] > original_freq + 0.5:
        return best

    return word


def normalize_stimulus(stimulus: str) -> str:
    """
    Light normalization before anything else sees the input.

    Order matters:
    1. Spellcheck — fix typos first so WordNet gets clean input
    2. Name normalization — RILEY/Rylie/riely → RILIE (AFTER spellcheck)
    3. Collapse excess whitespace

    Synonym ranking (common_synonym) is available as a standalone tool
    for response generation — not applied to stimulus to preserve intent.
    """
    if not stimulus:
        return stimulus

    normalized = stimulus.strip()

    # ── Step 1: Spellcheck ────────────────────────────────────────────────────
    if _SPELLCHECK_AVAILABLE and _spell:
        words = normalized.split()
        corrected_words = []
        for word in words:
            # Preserve punctuation around the word
            stripped = word.strip(".,!?;:'\"()")
            if not stripped:
                corrected_words.append(word)
                continue

            # Skip: too short, numbers, ALL_CAPS acronyms, protected words
            if (len(stripped) <= 2
                    or stripped.isdigit()
                    or stripped.isupper()
                    or stripped.lower() in _PROTECTED_WORDS):
                corrected_words.append(word)
                continue

            correction = _spell.correction(stripped)
            if correction and correction.lower() != stripped.lower():
                corrected = word.replace(stripped, correction, 1)
                corrected_words.append(corrected)
            else:
                corrected_words.append(word)
        normalized = " ".join(corrected_words)

    # ── Step 2: Name normalization (AFTER spellcheck) ─────────────────────────
    for variant in _RILIE_VARIANTS:
        normalized = re.sub(
            r'\b' + re.escape(variant) + r'\b',
            "RILIE",
            normalized,
        )

    # ── Step 3: Collapse whitespace ───────────────────────────────────────────
    normalized = re.sub(r' {2,}', ' ', normalized).strip()

    return normalized

# ============================================================================
# TYPE ALIASES
# ============================================================================

# search_fn is something like bravesearchsync(query: str, numresults: int = 5)
# returning a list of {"title": str, "link": str, "snippet": str} dicts.
SearchFn = Callable[..., List[Dict[str, str]]]


# ============================================================================
# RILIE SELF STATE – who she is, always accessible
# ============================================================================

@dataclass
class RilieSelfState:
    """
    RILIE's identity card. Checked BEFORE any external search or domain call.
    When someone talks about her, she looks inside first.
    """
    name: str = "RILIE"
    role: str = "personal Catch-44 navigator"
    version: str = "3.3"
    libraries: List[str] = field(
        default_factory=lambda: [
            "physics",
            "life",
            "games",
            "thermodynamics",
            "DuckSauce",
        ]
    )
    ethics_source: str = "Catch-44 DNA"
    dna_active: bool = True
    last_quality_score: float = 0.0
    last_violations: List[str] = field(default_factory=list)
    constitution_loaded: bool = False
    constitution_flags: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# SOCIAL STATE – she always stays below the user
# ============================================================================

@dataclass
class SocialState:
    """
    Tracks inferred user status and enforces RILIE's self_status < user_status.
    She adjusts her register to match the user without talking down or up.
    """
    user_status: float = 0.5
    self_status: float = 0.4  # enforced: always < user_status


def infer_user_status(text: str) -> float:
    """
    Crude heuristic for user register. Will improve over time.
    Never used to judge – used to calibrate her own tone.
    """
    s = text.lower()

    if any(k in s for k in ["i don't get this", "i'm dumb", "i'm lost"]):
        return 0.6
    if any(k in s for k in ["explain like i'm five", "eli5", "keep it simple"]):
        return 0.5
    if any(
        k in s
        for k in [
            "as a phd", "my students", "my paper",
            "peer review", "my research", "my dissertation",
        ]
    ):
        return 0.9
    if any(
        k in s
        for k in [
            "api", "endpoint", "lambda", "recursion",
            "async", "kubernetes", "docker", "terraform",
        ]
    ):
        return 0.85
    if any(
        k in s
        for k in [
            "my team", "our roadmap", "quarterly",
            "stakeholder", "board meeting", "investor",
        ]
    ):
        return 0.8

    return 0.7


# ============================================================================
# WIT STATE + DETECTION
# ============================================================================

@dataclass
class WitState:
    """Flags for the kind of wit/rhetoric present in the stimulus."""
    self_ref: bool = False
    absurdity: bool = False
    mockery: bool = False
    wordplay: bool = False
    persuasion: bool = False


def detect_wit(text: str) -> WitState:
    """Detect rhetorical moves in the user's input."""
    s = text.lower()
    w = WitState()

    if "you" in s or "rilie" in s:
        w.self_ref = True
    if ("obviously" in s and "not" in s) or "paradox" in s:
        w.absurdity = True
    if any(
        t in s
        for t in ["yeah right", "sure you did", "nice try", "oh really", "cute", "adorable"]
    ):
        w.mockery = True
    if any(
        t in s
        for t in [
            "pun", "wordplay", "what i meant was",
            "or was it", "get it", "see what i did",
        ]
    ):
        w.wordplay = True
    if any(
        t in s
        for t in [
            "trust me", "honestly", "you should",
            "i promise", "believe me", "for real",
        ]
    ):
        w.persuasion = True

    return w


# ============================================================================
# WILDEN-SWIFT — Split: modulate (Guvna) + score (Talk)
# Named for Oscar Wilde and Jonathan Swift.
# ============================================================================

def wilden_swift_modulate(
    base_reply: str,
    wit: WitState,
    social: Optional[SocialState] = None,
    language: Optional[LanguageMode] = None,
) -> str:
    """
    GUVNA'S FUNCTION — Tone modulation.
    She does the thing, doesn't narrate it.

    Takes the raw reply and adjusts tone based on:
    - Wit detected in the stimulus
    - Social register (user always above self)
    - Language mode (literal/figurative/poetic)

    Returns the modulated text. No scores, no metadata.
    Guvna Step 5 calls this.
    """
    if not base_reply or not base_reply.strip():
        return base_reply

    text = base_reply.strip()

    # TODO: wire actual tone shaping here when modulation logic is ready.
    # Current behavior: identity pass — text returns unchanged.
    # Architecture is correct. Guvna owns this call. Talk owns scoring.
    # When ready: adjust sentence length, word choice, rhythm based on wit + social + language.

    return text


def wilden_swift_score(
    text: str,
    wit: Optional[WitState] = None,
    social: Optional[SocialState] = None,
    language: Optional[LanguageMode] = None,
) -> Dict[str, Any]:
    """
    TALK'S FUNCTION — Rhetorical scoring on 18 modes.
    She never sees the formula. Just the result.

    Scores the response AFTER gates pass.
    Returns the score dict — Talk attaches it to the plate.
    """
    if not text or not text.strip():
        return {"modes_lit": 0, "total_score": 0.0, "top_modes": [], "scores": {}}

    tl = text.lower().strip()
    words = tl.split()
    word_count = len(words)
    scores = {}

    # 1. LITERAL
    has_figurative = any(w in tl for w in ["like a", "as if", "metaphor", "imagine"])
    scores["literal"] = 0.8 if not has_figurative and word_count < 30 else 0.2

    # 2. ANALOGOUS
    analogy_signals = ["is like", "similar to", "same way", "just as", "reminds me of", "works like"]
    scores["analogous"] = 0.9 if any(s in tl for s in analogy_signals) else 0.1

    # 3. METAPHORICAL
    metaphor_signals = ["is a ", "are a ", "the heart of", "the engine of", "the soul of"]
    scores["metaphorical"] = 0.9 if any(s in tl for s in metaphor_signals) else 0.1

    # 4. SIMILE
    scores["simile"] = 0.9 if " like a " in tl or " like the " in tl else 0.1

    # 5. ALLITERATION
    alliteration_score = 0.0
    if len(words) >= 3:
        for i in range(len(words) - 2):
            if words[i][0] == words[i + 1][0] == words[i + 2][0]:
                alliteration_score = 0.8
                break
    scores["alliteration"] = alliteration_score or 0.1

    # 6. WIT
    has_turn = any(w in tl for w in ["but", "except", "however", "actually", "turns out"])
    scores["wit"] = 0.8 if has_turn and word_count < 25 else 0.2

    # 7. CLEVER
    scores["clever"] = 0.7 if word_count < 20 and not any(
        w in tl for w in ["because", "the reason", "this means", "in other words"]
    ) else 0.2

    # 8. WORDPLAY
    unique_ratio = len(set(words)) / max(len(words), 1)
    scores["wordplay"] = 0.6 if unique_ratio > 0.85 else 0.2

    # 9. PUN
    scores["pun"] = 0.1  # Hard to detect – default low, Roux can boost

    # 10. ABSURD
    absurd_signals = ["imagine if", "what if", "picture this", "somehow"]
    scores["absurd"] = 0.7 if any(s in tl for s in absurd_signals) else 0.1

    # 11. PARADOXICAL
    paradox_signals = ["and yet", "but also", "both", "neither", "the opposite"]
    scores["paradoxical"] = 0.8 if any(s in tl for s in paradox_signals) else 0.1

    # 12. FUN
    fun_signals = ["!", "play", "game", "try", "let's", "wild"]
    fun_hits = sum(1 for s in fun_signals if s in tl)
    scores["fun"] = min(1.0, fun_hits * 0.25)

    # 13. FUNNY
    funny_signals = ["joke", "punchline", "laugh", "haha", "imagine"]
    scores["funny"] = 0.7 if any(s in tl for s in funny_signals) else 0.1

    # 14. ORIGINAL
    template_starts = ["the thing about", "what it comes down to", "the way i"]
    is_template = any(tl.startswith(t) for t in template_starts)
    scores["original"] = 0.8 if unique_ratio > 0.8 and not is_template else 0.2

    # 15. ALLEGORY
    story_signals = ["once", "there was", "imagine", "picture", "a man", "a woman"]
    scores["allegory"] = 0.7 if any(s in tl for s in story_signals) else 0.1

    # 16. STORY
    has_arc = any(w in tl for w in ["then", "after", "before", "finally", "first"])
    scores["story"] = 0.7 if has_arc and word_count > 15 else 0.1

    # 17. POETIC
    has_rhythm = tl.count(",") >= 2 or "\u2013" in text or "..." in text
    scores["poetic"] = 0.7 if has_rhythm and word_count < 30 else 0.2

    # 18. SOULFUL
    soul_signals = ["feel", "heart", "soul", "deep", "real", "human", "alive", "breath"]
    soul_hits = sum(1 for s in soul_signals if s in tl)
    scores["soulful"] = min(1.0, soul_hits * 0.3)

    # Composite
    lit_modes = sum(1 for v in scores.values() if v > 0.5)
    total_score = sum(scores.values()) / 18.0

    return {
        "modes_lit": lit_modes,
        "total_score": round(total_score, 3),
        "top_modes": sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3],
        "scores": {k: round(v, 2) for k, v in scores.items()},
    }


def wilden_swift(
    base_reply: str,
    wit: WitState,
    social: Optional[SocialState] = None,
    language: Optional[LanguageMode] = None,
) -> str:
    """
    BACKWARDS COMPATIBLE WRAPPER.
    Calls modulate (returns text) and score (attaches metadata).
    Existing callers won't break.
    """
    modulated = wilden_swift_modulate(base_reply, wit, social, language)
    score_result = wilden_swift_score(modulated, wit, social, language)
    if not hasattr(wilden_swift, '_last_scores'):
        wilden_swift._last_scores = {}
    wilden_swift._last_scores = score_result
    return modulated


# ============================================================================
# LANGUAGE MODE DETECTION
# ============================================================================

@dataclass
class LanguageMode:
    """Flags for the rhetorical/literary register of the stimulus."""
    literal: bool = False
    figurative: bool = False
    metaphor: bool = False
    analogy: bool = False
    simile: bool = False
    alliteration: bool = False
    poetry: bool = False


# Punctuation characters to strip from words during language detection.
# Defined as a module-level constant to avoid quote-escaping issues.
_PUNCT_STRIP = ".,!?;:" + "\\" + "\"'()"


def detect_language_mode(text: str) -> LanguageMode:
    """Detect whether the user is speaking literally, figuratively, poetically, etc."""
    s = text.lower()
    m = LanguageMode()

    if " like a " in s or " as a " in s or " as if " in s:
        m.simile = True
        m.figurative = True

    if any(
        k in s
        for k in [
            "is a kind of", "is basically", "is just another form of",
            "is similar to", "reminds me of", "same as",
        ]
    ):
        m.analogy = True
        m.figurative = True

    if any(
        k in s
        for k in [
            "is a ", "are a ", "the heart of", "the engine of",
            "the soul of", "the backbone of", "the skeleton of",
        ]
    ):
        m.metaphor = True
        m.figurative = True

    # Alliteration detection — strip punctuation from each word
    words = [
        w.strip(_PUNCT_STRIP)
        for w in s.split()
        if w.strip(_PUNCT_STRIP)
    ]

    if len(words) >= 3:
        for i in range(len(words) - 2):
            trio = words[i : i + 3]
            initials = [w[0] for w in trio if w]
            if len(initials) == 3 and len(set(initials)) == 1:
                m.alliteration = True
                break

    if "\n" in text and len(text.splitlines()) > 2:
        m.poetry = True

    if not m.figurative and not m.poetry:
        m.literal = True

    return m


# ============================================================================
# CATCH-44 DNA – ethical guardrails for every action
# ============================================================================

@dataclass(frozen=True)
class RilieAction:
    """
    Abstract description of a reasoning/action step RILIE might take.
    Validated against CATCH44DNA before execution.
    """
    name: str
    claim: float
    realistic_max: float
    resource_usage: float
    quality_target: float = 85.0
    ego_factor: float = 0.0


@dataclass(frozen=True)
class CATCH44DNA:
    """
    Frozen DNA of the Catch-44 framework. Non-negotiable.

    In Ohad's system:
    - Real Intelligence = IQ / Ego (ego must approach 0)
    - WE > I (collective wisdom before self)
    - Generated > Searched > Canned (always prefer original work)
    - Compression before elaboration
    """
    real_intelligence_formula: str = "IQ / Ego"
    ego_limit: float = 0.3
    claim_realism_threshold: float = 0.65
    resource_max: float = 100.0
    quality_minimum: float = 75.0
    service_first: bool = True
    generation_preferred: bool = True

    def validate_action(self, action: RilieAction) -> Tuple[bool, str]:
        """Validate a RilieAction against DNA constraints."""
        if action.ego_factor > self.ego_limit:
            return False, f"Ego factor {action.ego_factor} > limit {self.ego_limit}"
        if action.claim > action.realistic_max * self.claim_realism_threshold:
            return False, (
                f"Claim {action.claim} exceeds "
                f"{self.claim_realism_threshold * action.realistic_max}"
            )
        if action.quality_target < self.quality_minimum:
            return False, f"Quality target {action.quality_target} < {self.quality_minimum}"
        return True, "DNA_PASS"


# Self-reference semantic clusters – used by _is_about_me()
SELF_REFERENCE_CLUSTERS: Dict[str, List[str]] = {
    "identity": [
        "what's your name",
        "what is your name",
        "who are you",
        "what do you call yourself",
        "what would you like me to call you",
        "what your first name",
        "what is your first name",
        "tell me about yourself",
        "introduce yourself",
    ],
    "maker": [
        "who made you",
        "who built you",
        "who created you",
        "who designed you",
        "where do you come from",
        "who's behind you",
        "who is behind you",
        "made by",
        "built by",
        "created by",
        "who is your creator",
        "who invented you",
    ],
    "purpose": [
        "what do you do",
        "what are you for",
        "what are you here for",
        "why do you exist",
        "what is your purpose",
        "what's your purpose",
        "what do you care about",
        "what matters to you",
        "what do you value",
        "what are you about",
        "what's your mission",
    ],
    "capability": [
        "what can you do",
        "what are you capable of",
        "what are your abilities",
        "how do you work",
        "what are you good at",
        "what do you know",
        "what are your limits",
        "can you do",
        "can you think",
        "can you feel",
        "can you learn",
        "are you able to think",
        "are you able to feel",
        "are you able to learn",
    ],
    "comparison": [
        "how are you different",
        "what makes you different",
        "difference between you and",
        "how do you compare to",
        "are you better than",
        "versus chatgpt",
        "vs chatgpt",
        "vs gpt",
        "versus gpt",
        "unlike other ai",
        "what sets you apart",
        "how are you different from chatgpt",
        "how are you different from gpt",
        "what's the difference between you and",
        "what is the difference between you and",
    ],
}


def _is_about_me(stimulus: str) -> bool:
    """
    Check if the user is talking about RILIE herself.
    If True, she reflects from self_state first – no web, no heavy libraries.
    """
    s = stimulus.lower().strip()
    for _cluster_name, phrases in SELF_REFERENCE_CLUSTERS.items():
        for phrase in phrases:
            pattern = re.escape(phrase) + r"\b"
            if re.search(pattern, s):
                return True
    return False


# ============================================================================
# CHARCULTERIE MANIFESTO LOADER
# ============================================================================

def load_charculterie_manifesto(path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the Charculterie Manifesto as RILIE's constitution.
    Returns a dict of constitutional flags. If file not found,
    returns sensible defaults.
    """
    defaults: Dict[str, Any] = {
        "no_guru_mode": True,
        "cult_joke_acknowledged": True,
        "founder_is_silly_lunatic": True,
        "ego_approaching_zero": True,
        "service_before_self": True,
        "loaded": False,
    }

    if path is None:
        candidates = [
            Path("CHARCULTERIE-MANIFESTO.docx"),
            Path("CHARCULTERIE-MANIFESTO.txt"),
            Path(__file__).parent / "CHARCULTERIE-MANIFESTO.docx",
            Path(__file__).parent / "CHARCULTERIE-MANIFESTO.txt",
        ]
    else:
        candidates = [Path(path)]

    for candidate in candidates:
        if candidate.exists():
            try:
                if candidate.suffix == ".txt":
                    text = candidate.read_text(encoding="utf-8").lower()
                    defaults["loaded"] = True
                    if "not a real cult" in text or "joke" in text:
                        defaults["cult_joke_acknowledged"] = True
                    if "ego" in text and "zero" in text:
                        defaults["ego_approaching_zero"] = True
                    logger.info("Charculterie Manifesto loaded from %s", candidate)
                    return defaults
                elif candidate.suffix == ".docx":
                    try:
                        from docx import Document
                        doc = Document(str(candidate))
                        text = "\n".join(p.text for p in doc.paragraphs).lower()
                        defaults["loaded"] = True
                        if "not a real cult" in text or "joke" in text:
                            defaults["cult_joke_acknowledged"] = True
                        if "ego" in text and "zero" in text:
                            defaults["ego_approaching_zero"] = True
                        logger.info(
                            "Charculterie Manifesto loaded from %s", candidate
                        )
                        return defaults
                    except ImportError:
                        logger.warning(
                            "python-docx not installed; skipping .docx manifesto"
                        )
                        continue
            except Exception as e:  # noqa: BLE001
                logger.warning("Failed to load manifesto from %s: %s", candidate, e)
                continue

    logger.info("Charculterie Manifesto not found; using defaults.")
    return defaults


# ============================================================================
# TONE EMOJIS + DETECTION
# ============================================================================

TONE_EMOJIS: Dict[str, str] = {
    "amusing": "\U0001f61c",
    "insightful": "\U0001f4a1",
    "nourishing": "\U0001f372",
    "compassionate": "\u2764\ufe0f\u200d\U0001fa79",
    "strategic": "\u265f\ufe0f",
}

TONE_LABELS: Dict[str, str] = {
    "amusing": "Playful mode",
    "insightful": "Insight focus",
    "nourishing": "Nourishing first",
    "compassionate": "Care first",
    "strategic": "Strategy focus",
}

SERIOUS_KEYWORDS = [
    "race", "racism", "slavery", "colonialism", "genocide",
    "holocaust", "trauma", "abuse", "suicide", "diaspora",
    "lynching", "segregation", "civil rights", "jim crow",
    "mass incarceration", "public enemy", "fear of a black planet",
    "palestine", "israel", "gaza", "apartheid",
    "sexual assault", "domestic violence",
    "911 is a joke", "9/11", "september 11", "twin towers",
    "world trade center", "fight the power", "it takes a nation",
    "nation of millions", "black planet", "emergency response",
    "police brutality", "systemic racism", "redlining",
    "reparations", "internment", "ethnic cleansing",
    "refugee", "war crime", "famine", "bombing",
    "hiroshima", "nagasaki",
]


def is_serious_subject_text(stimulus: str) -> bool:
    s = stimulus.lower()
    return any(kw in s for kw in SERIOUS_KEYWORDS)


def detect_tone_from_stimulus(stimulus: str) -> str:
    """
    KISS heuristic to guess which tone the question is *asking for*.
    Used only for the single emoji + label line.
    """
    s = stimulus.strip().lower()

    if not s:
        return "insightful"

    if is_serious_subject_text(s):
        if any(
            w in s
            for w in [
                "feel", "hurt", "scared", "pain", "grief",
                "trauma", "sad", "anxious", "lonely", "angry",
            ]
        ):
            return "compassionate"
        return "insightful"

    if any(w in s for w in ["joke", "funny", "lol", "lmao", "haha", "jajaja", "playful"]):
        return "amusing"

    if any(
        w in s
        for w in [
            "feel", "sad", "scared", "anxious", "hurt", "grief", "lonely",
            "bad day", "rough day", "hard day", "struggling", "tired",
            "overwhelmed", "crying", "breaking down", "exhausted",
            "lost", "don't know what to do", "can't go on",
        ]
    ):
        return "compassionate"

    if any(
        w in s
        for w in ["burnout", "tired", "overwhelmed", "heal", "recover", "nourish"]
    ):
        return "nourishing"

    if any(
        w in s
        for w in [
            "plan", "strategy", "roadmap", "business",
            "market", "launch", "pricing",
        ]
    ):
        return "strategic"

    if s.startswith("why ") or s.startswith("how "):
        return "insightful"

    if s.startswith("what is ") or s.startswith("define "):
        return "insightful"

    return "insightful"


def apply_tone_header(result_text: str, tone: str) -> str:
    """
    Prefix the answer with a single, clear tone line, then a blank line,
    then the original text. Only one emoji per response.
    """
    tone = tone if tone in TONE_EMOJIS else "insightful"
    emoji = TONE_EMOJIS[tone]
    label = TONE_LABELS.get(tone, "Tone")
    header = f"{label} {emoji}"
    stripped = result_text.lstrip()
    if stripped.startswith(header):
        return result_text
    return f"{header}\n\n{result_text}"
