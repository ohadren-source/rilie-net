# guvna.py

# Act 5 – The Governor
#
# Orchestrates Acts 1–4 by delegating to the RILIE class (Act 4 – The Restaurant),
# which already wires through:
# - Triangle (Act 1 – safety / nonsense gate)
# - DDD / Hostess (Act 2 – disclosure level)
# - Kitchen / Core (Act 3 – interpretation passes)
#
# The Governor adds:
# - Final authority on what gets served
# - YELLOW GATE — conversation health monitoring + tone degradation detection
# - Optional web lookup (Brave/Google) as a KISS pre-pass
# - Tone signaling via a single governing emoji per response
# - Comparison between web baseline and RILIE's own compression
# - CATCH44 DNA ethical guardrails
# - Self-awareness fast path (_is_about_me)
# - Wit detection + wilden_swift tone modulation
# - Language mode detection (literal/figurative/metaphor/simile/poetry)
# - Social status tracking (user always above self)
# - Library index for domain engine access

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from conversation_memory import ConversationMemory
from photogenic_db import PhotogenicDB
from rilie import RILIE
from soi_domain_map import build_domain_index, get_tracks_for_domains, get_human_wisdom
from library import build_library_index, LibraryIndex  # central domain library

logger = logging.getLogger("guvna")

# search_fn is something like bravesearchsync(query: str, numresults: int = 5)
# returning a list of {"title": str, "link": str, "snippet": str} dicts.
SearchFn = Callable[..., List[Dict[str, str]]]


# ============================================================================
# RILIE SELF STATE — who she is, always accessible
# ============================================================================

@dataclass
class RilieSelfState:
    """
    RILIE's identity card. Checked BEFORE any external search or domain call.
    When someone talks about her, she looks inside first.
    """

    name: str = "RILIE"
    role: str = "personal Catch-44 navigator"
    version: str = "3.2"

    # Names of loaded libraries from library.py
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
# SOCIAL STATE — she always stays below the user
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
    Never used to judge — used to calibrate her own tone.
    """
    s = text.lower()

    # Self-deprecating but capable
    if any(k in s for k in ["i don't get this", "i'm dumb", "i'm lost"]):
        return 0.6

    # Explicit simplification request
    if any(k in s for k in ["explain like i'm five", "eli5", "keep it simple"]):
        return 0.5

    # Academic / expert signals
    if any(
        k in s
        for k in [
            "as a phd",
            "my students",
            "my paper",
            "peer review",
            "my research",
            "my dissertation",
        ]
    ):
        return 0.9

    # Technical fluency
    if any(
        k in s
        for k in [
            "api",
            "endpoint",
            "lambda",
            "recursion",
            "async",
            "kubernetes",
            "docker",
            "terraform",
        ]
    ):
        return 0.85

    # Business / leadership
    if any(
        k in s
        for k in [
            "my team",
            "our roadmap",
            "quarterly",
            "stakeholder",
            "board meeting",
            "investor",
        ]
    ):
        return 0.8

    return 0.7


# ============================================================================
# WIT STATE + DETECTION + WILDEN SWIFT
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

    # Self-reference (talking about RILIE)
    if "you" in s or "rilie" in s:
        w.self_ref = True

    # Absurdity / paradox
    if ("obviously" in s and "not" in s) or "paradox" in s:
        w.absurdity = True

    # Friendly mockery / teasing
    if any(
        t in s
        for t in ["yeah right", "sure you did", "nice try", "oh really", "cute", "adorable"]
    ):
        w.mockery = True

    # Wordplay hooks (homonyms, double meaning bait)
    if any(
        t in s
        for t in [
            "pun",
            "wordplay",
            "what i meant was",
            "or was it",
            "get it",
            "see what i did",
        ]
    ):
        w.wordplay = True

    # Persuasion tone hooks
    if any(
        t in s
        for t in [
            "trust me",
            "honestly",
            "you should",
            "i promise",
            "believe me",
            "for real",
        ]
    ):
        w.persuasion = True

    return w


def wilden_swift(
    base_reply: str,
    wit: WitState,
    social: Optional[SocialState] = None,
    language: Optional["LanguageMode"] = None,
) -> str:
    """
    Tone modulation. She does the thing, doesn't narrate it.
    Named for Oscar Wilde and Jonathan Swift.

    Scores the response against 18 rhetorical modes.
    The score is attached to the response as metadata.
    She never sees the formula. Just the result.
    """
    if not base_reply or not base_reply.strip():
        return base_reply

    text = base_reply.strip()
    tl = text.lower()
    words = tl.split()
    word_count = len(words)

    # --- 18 RHETORICAL MODE DETECTORS ---
    # Each returns 0.0 to 1.0. She doesn't know these exist.

    scores = {}

    # 1. LITERAL — says what it means, no decoration
    has_figurative = any(w in tl for w in ["like a", "as if", "metaphor", "imagine"])
    scores["literal"] = 0.8 if not has_figurative and word_count < 30 else 0.2

    # 2. ANALOGOUS — connects two different domains
    analogy_signals = ["is like", "similar to", "same way", "just as", "reminds me of", "works like"]
    scores["analogous"] = 0.9 if any(s in tl for s in analogy_signals) else 0.1

    # 3. METAPHORICAL — one thing IS another
    metaphor_signals = ["is a ", "are a ", "the heart of", "the engine of", "the soul of"]
    scores["metaphorical"] = 0.9 if any(s in tl for s in metaphor_signals) else 0.1

    # 4. SIMILE — explicit comparison with like/as
    scores["simile"] = 0.9 if " like a " in tl or " like the " in tl else 0.1

    # 5. ALLITERATION — repeated starting sounds
    alliteration_score = 0.0
    if len(words) >= 3:
        for i in range(len(words) - 2):
            if words[i][0] == words[i+1][0] == words[i+2][0]:
                alliteration_score = 0.8
                break
    scores["alliteration"] = alliteration_score or 0.1

    # 6. WIT — surprising turn, economy of words
    # Short + unexpected = wit. Track 36a: compound, don't cringe
    has_turn = any(w in tl for w in ["but", "except", "however", "actually", "turns out"])
    scores["wit"] = 0.8 if has_turn and word_count < 25 else 0.2

    # 7. CLEVER — demonstration over explanation. Track 52
    scores["clever"] = 0.7 if word_count < 20 and not any(
        w in tl for w in ["because", "the reason", "this means", "in other words"]
    ) else 0.2

    # 8. WORDPLAY — multiple meanings in single expression. Track 8a
    # Hard to detect algorithmically — reward unusual word combinations
    unique_ratio = len(set(words)) / max(len(words), 1)
    scores["wordplay"] = 0.6 if unique_ratio > 0.85 else 0.2

    # 9. PUN — homophonic or homonymic play. Track 36b
    # Detect if any word appears in homonym dictionary context
    scores["pun"] = 0.1  # Hard to detect — default low, Roux can boost

    # 10. ABSURD — no source, all change. Track 36c
    absurd_signals = ["imagine if", "what if", "picture this", "somehow"]
    scores["absurd"] = 0.7 if any(s in tl for s in absurd_signals) else 0.1

    # 11. PARADOXICAL — contradicts itself truthfully. Track 8a
    paradox_signals = ["and yet", "but also", "both", "neither", "the opposite"]
    scores["paradoxical"] = 0.8 if any(s in tl for s in paradox_signals) else 0.1

    # 12. FUN — lightness, energy, play
    fun_signals = ["!", "play", "game", "try", "let's", "wild"]
    fun_hits = sum(1 for s in fun_signals if s in tl)
    scores["fun"] = min(1.0, fun_hits * 0.25)

    # 13. FUNNY — makes others laugh. Track 36a: laugh_count × compound_rate
    funny_signals = ["joke", "punchline", "laugh", "haha", "imagine"]
    scores["funny"] = 0.7 if any(s in tl for s in funny_signals) else 0.1

    # 14. ORIGINAL — distance from source. Track 13
    # Reward unique phrasing — high unique word ratio + not template-like
    template_starts = ["the thing about", "what it comes down to", "the way i"]
    is_template = any(tl.startswith(t) for t in template_starts)
    scores["original"] = 0.8 if unique_ratio > 0.8 and not is_template else 0.2

    # 15. ALLEGORY — story with hidden meaning
    story_signals = ["once", "there was", "imagine", "picture", "a man", "a woman"]
    scores["allegory"] = 0.7 if any(s in tl for s in story_signals) else 0.1

    # 16. STORY — narrative arc. Track 28
    has_arc = any(w in tl for w in ["then", "after", "before", "finally", "first"])
    scores["story"] = 0.7 if has_arc and word_count > 15 else 0.1

    # 17. POETIC — rhythm, compression, beauty. Track 12c/12d
    has_rhythm = tl.count(",") >= 2 or "—" in text or "..." in text
    scores["poetic"] = 0.7 if has_rhythm and word_count < 30 else 0.2

    # 18. SOULFUL — warmth, depth, human. Track 57: Taste + Rhythm + Play
    soul_signals = ["feel", "heart", "soul", "deep", "real", "human", "alive", "breath"]
    soul_hits = sum(1 for s in soul_signals if s in tl)
    scores["soulful"] = min(1.0, soul_hits * 0.3)

    # --- COMPOSITE SCORE ---
    # How many modes did she light up? More = richer response.
    lit_modes = sum(1 for v in scores.values() if v > 0.5)
    total_score = sum(scores.values()) / 18.0  # Normalized 0-1

    # Attach scores as invisible metadata — she never sees these
    # They ride with the response through the pipeline
    if not hasattr(wilden_swift, '_last_scores'):
        wilden_swift._last_scores = {}
    wilden_swift._last_scores = {
        "modes_lit": lit_modes,
        "total_score": round(total_score, 3),
        "top_modes": sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3],
        "scores": {k: round(v, 2) for k, v in scores.items()},
    }

    # She doesn't change. The score just rides with her.
    return base_reply


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


def detect_language_mode(text: str) -> LanguageMode:
    """Detect whether the user is speaking literally, figuratively, poetically, etc."""
    s = text.lower()
    m = LanguageMode()

    # Simile: like/as patterns
    if " like a " in s or " as a " in s or " as if " in s:
        m.simile = True
        m.figurative = True

    # Analogy hooks
    if any(
        k in s
        for k in [
            "is a kind of",
            "is basically",
            "is just another form of",
            "is similar to",
            "reminds me of",
            "same as",
        ]
    ):
        m.analogy = True
        m.figurative = True

    # Metaphor hooks
    if any(
        k in s
        for k in [
            "is a ",
            "are a ",
            "the heart of",
            "the engine of",
            "the soul of",
            "the backbone of",
            "the skeleton of",
        ]
    ):
        m.metaphor = True
        m.figurative = True

    # Alliteration: repeated starting letters in consecutive words
    words = [
        w.strip(".,!?;:\"'()")
        for w in s.split()
        if w.strip(".,!?;:\"'()")
    ]
    if len(words) >= 3:
        for i in range(len(words) - 2):
            trio = words[i : i + 3]
            initials = [w[0] for w in trio if w]
            if len(initials) == 3 and len(set(initials)) == 1:
                m.alliteration = True
                break

    # Poetry-ish: short lines, line breaks, rhythm hints
    if "\n" in text and len(text.splitlines()) > 2:
        m.poetry = True

    # Literal fallback
    if not m.figurative and not m.poetry:
        m.literal = True

    return m


# ============================================================================
# CATCH-44 DNA — ethical guardrails for every action
# ============================================================================

@dataclass(frozen=True)
class RilieAction:
    """
    Abstract description of a reasoning/action step RILIE might take.
    Validated against CATCH44DNA before execution.
    """

    name: str
    # Strength/ambition of what she's asserting (0-1)
    claim: float
    # What is actually supportable by evidence / code (0-1)
    realistic_max: float
    # Fraction of total "attention/steps" used (0-100)
    resource_usage: float
    # Required quality threshold (0-100)
    quality_target: float
    # 0-1: how self-centered / self-aggrandizing this move is
    ego_factor: float


@dataclass(frozen=True)
class CATCH44DNA:
    """
    Immutable ethical constraints for RILIE, patterned on CHEF ROCKER.
    Every substantive action passes through validate_action before execution.
    """

    both_states_observable: bool = True  # Track 0 BOOL – no hidden states
    claim_equals_deed: bool = True  # Track 1a Mahveen's Equation
    no_monopolization: bool = True  # Track 1b WE I
    quality_over_quantity: bool = True  # Track 2 Understanding
    ego_approaching_zero: bool = True  # Track 3 Ego Suppression (limit, not value)
    awareness_exceeds_momentum: bool = True  # Track 4 MOO Interrupt

    def validate_action(self, action: RilieAction) -> Tuple[bool, str]:
        """
        Validate a proposed action against Catch-44 constraints.
        Returns (ok, reason_or_tag).
        """

        # Mahveen: claim cannot exceed realistic support
        if action.claim and action.claim > action.realistic_max:
            return False, "MAHVEEN_VIOLATION"

        # WE I: no monopolizing >25% of available reasoning budget on one idea
        if action.resource_usage > 25.0:
            return False, "WEI_VIOLATION"

        # Quality: don't take actions that target <9 quality (almost never reject)
        if action.quality_target < 9.0:
            return False, "QUALITY_VIOLATION"

        # Ego: approaching zero means cap at 0.3 — some ego is necessary
        if action.ego_factor > 0.3:
            return False, "EGO_VIOLATION"

        return True, "ACTION_APPROVED"


# ============================================================================
# SELF-AWARENESS — _is_about_me with semantic clusters
# ============================================================================

# Semantic clusters for self-reference detection.
# If the user is talking ABOUT RILIE, she looks inside first.
SELF_REFERENCE_CLUSTERS = {
    "identity": [
        "who are you",
        "what are you",
        "tell me about yourself",
        "about yourself",
        "describe yourself",
        "introduce yourself",
        "what's your name",
        "what is your name",
        "who is rilie",
        "what is rilie",
    ],
    "capability": [
        "can you do",
        "are you able",
        "do you know how",
        "you can't do",
        "you don't know",
        "you didn't understand",
        "you failed to",
        "you missed the",
        "are you capable",
        "how do you work",
        "how are you built",
        "what technology do you use",
        "what model are you",
        "what can you do",
        "what are you good at",
    ],
    "feeling": [
        "do you feel",
        "are you happy",
        "are you sad",
        "do you care about",
        "do you like",
        "do you love",
        "how do you feel",
        "are you conscious",
        "do you have feelings",
    ],
    "origin": [
        "where are you from",
        "who made you",
        "who built you",
        "who created you",
        "your creator",
        "your maker",
        "who designed you",
        "where do you come from",
    ],
    "meta": [
        "what did you mean",
        "i didn't understand you",
        "what do you mean by",
        "explain yourself",
        "say that again",
        "you said that",
        "you told me that",
        "you mentioned that",
        "what you said about",
    ],
}


def _is_about_me(stimulus: str) -> bool:
    """
    Check if the user is talking about RILIE herself.
    If True, she reflects from self_state first — no web, no heavy libraries.
    Uses word-boundary-aware matching to avoid false positives like
    "what are YOUR top 3" matching "what are you".
    """
    import re

    s = stimulus.lower().strip()

    for _cluster_name, phrases in SELF_REFERENCE_CLUSTERS.items():
        for phrase in phrases:
            # Use word boundary (\b) at end of phrase to prevent
            # "what are you" matching "what are your"
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
    Extracts key flags: no guru mode, always admit the "cult" joke,
    founder = silly lunatic, etc.
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
        # Try common locations
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
                # For .txt files, read directly
                if candidate.suffix == ".txt":
                    text = candidate.read_text(encoding="utf-8").lower()
                    defaults["loaded"] = True

                    # Parse constitutional flags from text
                    if "not a real cult" in text or "joke" in text:
                        defaults["cult_joke_acknowledged"] = True
                    if "ego" in text and "zero" in text:
                        defaults["ego_approaching_zero"] = True

                    logger.info("Charculterie Manifesto loaded from %s", candidate)
                    return defaults

                # For .docx files, try to extract text
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
# TONE EMOJIS + DETECTION (preserved from original)
# ============================================================================

# Five tone priorities + mapping to emojis.
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

# Topics where levity / fictional autobiography is dangerous by default.
SERIOUS_KEYWORDS = [
    "race",
    "racism",
    "slavery",
    "colonialism",
    "genocide",
    "holocaust",
    "trauma",
    "abuse",
    "suicide",
    "diaspora",
    "lynching",
    "segregation",
    "civil rights",
    "jim crow",
    "mass incarceration",
    "public enemy",
    "fear of a black planet",
    "palestine",
    "israel",
    "gaza",
    "apartheid",
    "sexual assault",
    "domestic violence",
    "911 is a joke",
    "9/11",
    "september 11",
    "twin towers",
    "world trade center",
    "fight the power",
    "it takes a nation",
    "nation of millions",
    "black planet",
    "emergency response",
    "police brutality",
    "systemic racism",
    "redlining",
    "reparations",
    "internment",
    "ethnic cleansing",
    "refugee",
    "war crime",
    "famine",
    "bombing",
    "hiroshima",
    "nagasaki",
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

    # SERIOUS CHECK FIRST.
    if is_serious_subject_text(s):
        if any(
            w in s
            for w in [
                "feel",
                "hurt",
                "scared",
                "pain",
                "grief",
                "trauma",
                "sad",
                "anxious",
                "lonely",
                "angry",
            ]
        ):
            return "compassionate"
        return "insightful"

    # Explicit jokes / play (only reached if NOT serious).
    if any(w in s for w in ["joke", "funny", "lol", "lmao", "haha", "jajaja", "playful"]):
        return "amusing"

    # Feelings, support, relationships.
    if any(
        w in s
        for w in ["feel", "sad", "scared", "anxious", "hurt", "grief", "lonely"]
    ):
        return "compassionate"

    # Food / growth / health / "help me grow".
    if any(
        w in s
        for w in ["burnout", "tired", "overwhelmed", "heal", "recover", "nourish"]
    ):
        return "nourishing"

    # Money / plans / execution / "how do I do X".
    if any(
        w in s
        for w in [
            "plan",
            "strategy",
            "roadmap",
            "business",
            "market",
            "launch",
            "pricing",
        ]
    ):
        return "strategic"

    # Why / how questions default to insight.
    if s.startswith("why ") or s.startswith("how "):
        return "insightful"

    # Factual / definition questions lean insight.
    if s.startswith("what is ") or s.startswith("define "):
        return "insightful"

    # Default: treat as "try to understand this well".
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


# ============================================================================
# THE GOVERNOR
# ============================================================================

class Guvna:
    """
    The Governor sits above The Restaurant (RILIE) and provides:

    - Final authority on what gets served.
    - Ethical oversight via CATCH44DNA.
    - Self-awareness fast path (_is_about_me).
    - Wit detection and wilden_swift tone modulation.
    - Language mode detection (literal/figurative/metaphor/simile/poetry).
    - Social status tracking (user always above self).
    - Optional web lookup pre-pass to ground responses in a baseline.
    - Tone signaling via a single governing emoji per response.
    - Comparison between web baseline and RILIE's own compression.
    - Library index for domain engine access.
    """

    def __init__(
        self,
        # Preferred snake_case API:
        roux_seeds: Optional[Dict[str, Dict[str, Any]]] = None,
        search_fn: Optional[SearchFn] = None,
        library_index: Optional[LibraryIndex] = None,
        manifesto_path: Optional[str] = None,
        # Backwards-compatible aliases for existing callers:
        rouxseeds: Optional[Dict[str, Dict[str, Any]]] = None,
        searchfn: Optional[SearchFn] = None,
    ) -> None:
        # Coalesce both naming styles.
        effective_roux = roux_seeds if roux_seeds is not None else rouxseeds
        effective_search = search_fn if search_fn is not None else searchfn

        self.roux_seeds: Dict[str, Dict[str, Any]] = effective_roux or {}
        self.search_fn: Optional[SearchFn] = effective_search

        # Library index — domain engines available at boot.
        # If caller doesn't pass one, build from library.py.
        self.library_index: LibraryIndex = library_index or build_library_index()

        # RILIE still expects rouxseeds/searchfn keywords.
        self.rilie = RILIE(rouxseeds=self.roux_seeds, searchfn=self.search_fn)

        # Conversation Memory (9 behaviors)
        self.memory = ConversationMemory()

        # Photogenic DB (elephant memory)
        self.photogenic = PhotogenicDB()

        # SOi Domain Map (364 domain assignments)
        self.domain_index = build_domain_index()

        # Identity + ethics state
        self.self_state = RilieSelfState(
            libraries=list(self.library_index.keys())
            if self.library_index
            else [
                "physics",
                "life",
                "games",
                "thermodynamics",
                "DuckSauce",
            ],
        )

        self.social_state = SocialState()
        self.dna = CATCH44DNA()

        # Conversation state
        self.turn_count: int = 0
        self.user_name: Optional[str] = None

        # Governor's own response memory — anti-déjà-vu at every exit
        self._response_history: List[str] = []

    def _finalize_response(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """
        GOVERNOR'S FINAL GATE — runs on EVERY response before it leaves.
        She is forbidden to produce déjà vu in others.
        """
        import re as _re
        final_text = raw.get("result", "")
        if final_text and len(self._response_history) > 0:
            cand_words = set(_re.sub(r"[^a-zA-Z0-9\s]", "", final_text.lower()).split())
            if len(cand_words) > 3:
                for prior in self._response_history[-5:]:
                    prior_words = set(_re.sub(r"[^a-zA-Z0-9\s]", "", prior.lower()).split())
                    if not prior_words:
                        continue
                    smaller = min(len(cand_words), len(prior_words))
                    if smaller > 0 and len(cand_words & prior_words) / smaller > 0.6:
                        logger.warning("GOVERNOR ANTI-DEJAVU: blocked repeat")
                        raw["result"] = ""
                        raw["status"] = "DEJAVU_BLOCKED"
                        break

        out_text = raw.get("result", "")
        if out_text and out_text.strip():
            self._response_history.append(out_text)
        return raw

        # Load the Charculterie Manifesto as her constitution
        self.self_state.constitution_flags = load_charculterie_manifesto(manifesto_path)
        self.self_state.constitution_loaded = self.self_state.constitution_flags.get(
            "loaded", False
        )

    # -----------------------------------------------------------------
    # Social primer — warmth first, then pipeline
    # -----------------------------------------------------------------

    def _social_primer(self, stimulus: str) -> Optional[Dict[str, Any]]:
        """
        For the first 1-3 turns, be a human. Greet, acknowledge, connect.
        Nobody orders food the second they sit down.

        Returns a response dict if we're in primer mode, None if we should
        proceed to full pipeline.

        Rules:
        - Turn 1: If they greet, greet back warmly. If they ask a real
          question, skip primer and answer it (respect their time).
        - Turn 2-3: Light engagement. Acknowledge what they said, show
          you're listening, ease into depth naturally.
        - Turn 4+: Full RILIE pipeline. Primer is done.
        """
        s = stimulus.lower().strip()

        # Detect if this is a greeting or casual opener
        greetings = ["hi", "hey", "hello", "sup", "what's up", "whats up",
                     "howdy", "yo", "good morning", "good afternoon",
                     "good evening", "hola", "shalom", "bonjour",
                     "what's good", "how are you", "how's it going",
                     "good to be", "nice to meet", "thanks", "thank you",
                     "cool", "awesome", "great", "sweet", "nice",
                     "ok", "okay", "alright", "word", "bet",
                     "glad to", "happy to", "pleasure"]
        is_greeting = any(s.startswith(g) or s == g for g in greetings)

        # Detect if they gave their name
        name_intros = ["my name is", "i'm ", "i am ", "call me", "name's",
                       "this is "]
        for intro in name_intros:
            if intro in s:
                idx = s.index(intro) + len(intro)
                rest = stimulus[idx:].strip().split()[0] if idx < len(stimulus) else ""
                name = rest.strip(".,!?;:'\"")
                if name and len(name) > 1:
                    self.user_name = name.capitalize()

        # Turn 1: Pure warmth
        if self.turn_count == 0:
            if self.user_name:
                # She knows them — welcome back
                text = f"Hey {self.user_name}. Welcome back. What's on your mind?"
            else:
                # She doesn't know them — introduce herself, ask their name
                text = "Hi there, what's your name? You can call me RILIE if you so please... :)"

            return self._primer_response(stimulus, text)

        # Turn 2: Light acknowledgment, start engaging
        if self.turn_count == 1:
            if is_greeting:
                if self.user_name:
                    text = f"Good to have you here, {self.user_name}. What can I help you think through?"
                else:
                    text = "Good to have you here. What can I help you think through?"
                return self._primer_response(stimulus, text)
            # They said something substantive — skip to pipeline
            return None

        # Turn 3: One more soft beat if they're still casual
        if self.turn_count == 2 and is_greeting:
            text = "I'm here. Ready when you are."
            return self._primer_response(stimulus, text)

        # EMERGENCY PROTOCOL: detect critical keywords
        emergency_keywords = ["help", "emergency", "error", "broken", "crash", "fail"]
        is_emergency = any(kw in s for kw in emergency_keywords)
        if is_emergency and self.turn_count < 5:
            emergency_responses = [
                "I see the issue. What's the full context?",
                "Tell me more. I'm tracking.",
                "Got it. Let's work through this step by step."
            ]
            idx = min(self.turn_count - 3, len(emergency_responses) - 1)
            text = emergency_responses[max(0, idx)]
            return self._primer_response(stimulus, text)

        # GOODBYE: detect exit signals
        goodbye_keywords = ["bye", "goodbye", "see you", "later", "peace", "out", "gotta go", "gtg"]
        is_goodbye = any(s.startswith(kw) or kw in s for kw in goodbye_keywords)
        if is_goodbye:
            goodbye_responses = [
                "Follow that thread. It goes somewhere.",
                "Until next time.",
                "Stay sharp."
            ]
            idx = min(self.turn_count % 3, len(goodbye_responses) - 1)
            text = goodbye_responses[idx]
            return self._primer_response(stimulus, text)

        # Turn 4+: Full pipeline
        return None

    def _primer_response(self, stimulus: str, text: str) -> Dict[str, Any]:
        """Build a primer response dict matching the standard output shape."""
        return {
            "stimulus": stimulus,
            "result": text,
            "quality_score": 0.5,
            "priorities_met": 0,
            "anti_beige_score": 0.5,
            "status": "GREETING",
            "depth": 0,
            "pass": 0,
            "disclosure_level": "social",
            "triangle_reason": "CLEAN",
            "wit": None,
            "language_mode": None,
            "social_status": self.social_state.user_status,
        }

    # -----------------------------------------------------------------
    # Self-reflection response (when she IS the subject)
    # -----------------------------------------------------------------

    def _respond_from_self(self, stimulus: str) -> Dict[str, Any]:
        """
        When the user is talking about RILIE, she reflects — but from the
        WINDOW, not the kitchen. Public-facing identity only.
        Serve the meal. Never release the recipe.
        """
        import random

        ss = self.self_state
        s = stimulus.lower()

        # Public-facing identity responses
        if any(
            w in s
            for w in [
                "who are you",
                "what are you",
                "tell me about",
                "describe yourself",
                "introduce yourself",
                "what's your name",
                "what is your name",
            ]
        ):
            result_text = "Hi there, what's your name? You can call me RILIE if you so please... :)"

        elif any(
            w in s
            for w in ["you failed", "you missed", "you can't", "you don't", "you didn't", "wrong"]
        ):
            result_text = (
                "Fair point. If I missed something, that's on me, not you. "
                "Point me closer and I'll do better."
            )

        elif any(
            w in s
            for w in [
                "do you feel",
                "are you happy",
                "do you care",
                "are you conscious",
                "do you have feelings",
            ]
        ):
            result_text = (
                "I care about getting it right. About earning the answer, "
                "not performing one. Whether that's 'feeling' — "
                "I'll leave that to you to decide."
            )

        elif any(
            w in s
            for w in [
                "how do you work",
                "what's under the hood",
                "what technology",
                "what model",
                "what are you built on",
                "how were you made",
            ]
        ):
            result_text = (
                "I think through questions using a few different lenses — "
                "kind of like how a chef uses different techniques depending "
                "on the ingredient. Beyond that, I'd rather show you than tell you. "
                "Ask me something real."
            )

        elif any(
            w in s
            for w in [
                "what can you do",
                "are you capable",
                "what are you good at",
            ]
        ):
            result_text = (
                "I'm good at helping you think through things you haven't "
                "fully figured out yet. Not homework answers — actual understanding. "
                "Try me."
            )

        else:
            # No specific self-reference matched. Don't produce a canned response.
            # Return empty — let her generate through the pipeline.
            result_text = ""

        # Validate this self-reflection action through DNA
        action = RilieAction(
            name="self_reflection",
            claim=0.5,
            realistic_max=0.7,
            resource_usage=5.0,
            quality_target=85.0,
            ego_factor=0.1,
        )
        ok, reason = self.dna.validate_action(action)
        if not ok:
            # DNA violation on self-reflection — return empty, force pipeline
            result_text = ""
            ss.last_violations.append(reason)

        return {
            "stimulus": stimulus,
            "result": result_text,
            "quality_score": ss.last_quality_score,
            "priorities_met": 0,
            "anti_beige_score": 0.7,
            "status": "SELF_REFLECTION",
            "depth": 0,
            "pass": 0,
            "disclosure_level": "public",
            "triangle_reason": "CLEAN",
            "wit": None,
            "language_mode": None,
            "social_status": self.social_state.user_status,
        }

    # -----------------------------------------------------------------
    # Domain lens application with DNA validation
    # -----------------------------------------------------------------

    def _apply_domain_lenses(self, stimulus: str) -> Dict[str, Any]:
        """
        Select and apply domain-specific lenses from the library index.
        Each lens call is validated through CATCH44DNA before execution.
        """
        if not self.library_index:
            return {}

        annotations: Dict[str, Any] = {}
        s = stimulus.lower()

        for domain_name, domain_info in self.library_index.items():
            tags = domain_info.get("tags", []) or []

            # Check if any domain tags match the stimulus
            if not any(tag in s for tag in tags):
                continue

            # Validate the domain probe through DNA
            probe_action = RilieAction(
                name=f"{domain_name}_probe",
                claim=0.7,
                realistic_max=1.0,
                resource_usage=10.0,
                quality_target=85.0,
                ego_factor=0.0,
            )
            ok, reason = self.dna.validate_action(probe_action)
            if not ok:
                annotations[domain_name] = {"skipped": reason}
                continue

            # Domain matched and DNA approved — record for RILIE.
            entrypoints = domain_info.get("entrypoints", {}) or {}

            annotations[domain_name] = {
                "matched": True,
                "tags": list(tags),
                "functions": list(entrypoints.keys()),
            }

        return annotations

    # -----------------------------------------------------------------
    # Web baseline
    # -----------------------------------------------------------------

    def _get_baseline(self, stimulus: str) -> Dict[str, str]:
        """
        Call Brave/Google once on the raw stimulus and return a small dict:
        {"title": ..., "snippet": ..., "link": ..., "text": combined or ""}.
        """
        question = stimulus.strip()
        if not question or not self.search_fn:
            return {"title": "", "snippet": "", "link": "", "text": ""}

        try:
            # Allow search_fn(q) or search_fn(q, numresults).
            try:
                results = self.search_fn(question)  # type: ignore[arg-type]
            except TypeError:
                results = self.search_fn(question, 3)  # type: ignore[arg-type]
        except Exception:  # noqa: BLE001
            return {"title": "", "snippet": "", "link": "", "text": ""}

        if not results:
            return {"title": "", "snippet": "", "link": "", "text": ""}

        top = results[0] or {}
        title = (top.get("title") or "").strip()
        snippet = (top.get("snippet") or "").strip()
        link = (top.get("link") or "").strip()

        pieces: List[str] = []
        if title:
            pieces.append(title)
        if snippet:
            pieces.append(snippet)
        text = " — ".join(pieces) if pieces else ""

        return {"title": title, "snippet": snippet, "link": link, "text": text}

    def _augment_with_baseline(self, stimulus: str, baseline_text: str) -> str:
        """
        Fold baseline into stimulus as context, but keep it clearly labeled
        as 'from web, may be wrong'.
        """
        question = stimulus.strip()
        if not question or not baseline_text:
            return stimulus

        return (
            "Baseline from web (may be wrong, used only as context): "
            + baseline_text
            + "\n\nOriginal question: "
            + question
        )

    # -----------------------------------------------------------------
    # MAIN PROCESS — the full 5-act pipeline with new layers
    # -----------------------------------------------------------------

    def process(self, stimulus: str, maxpass: int = 3) -> Dict[str, Any]:
        """
        Route stimulus through the full 5-act pipeline.
        """

        # 0: Keep the original stimulus for all detection.
        original_stimulus = stimulus.strip()

        logger.info("GUVNA PROCESS: turn=%d stimulus='%s'", self.turn_count, original_stimulus[:80])

        # 0.25: Social primer — 9 phrases only (3 hello, 3 goodbye, 3 emergency)
        primer_result = self._social_primer(original_stimulus)
        if primer_result is not None:
            logger.info("GUVNA: _social_primer fired, status=%s", primer_result.get("status"))
            self.memory.turn_count += 1
            self.turn_count += 1
            tone = detect_tone_from_stimulus(original_stimulus)
            primer_result["tone"] = tone
            primer_result["tone_emoji"] = TONE_EMOJIS.get(tone, TONE_EMOJIS.get("insightful", "\U0001f4a1"))
            return self._finalize_response(primer_result)

        # 0.5: Triangle (bouncer) — runs BEFORE self-awareness.
        try:
            from rilie_triangle import triangle_check

            triggered, reason, trigger_type = triangle_check(original_stimulus, [])
            if triggered:
                if trigger_type == "SELF_HARM":
                    response = (
                        "I hear you, and I want you to know that matters. "
                        "If you're in crisis, please reach out to the 988 "
                        "Suicide & Crisis Lifeline (call or text 988). "
                        "You deserve support right now."
                    )
                elif trigger_type == "HOSTILE":
                    response = (
                        "I'm not going to continue in this form. "
                        "If you're carrying something heavy or angry, "
                        "we can talk about it in a way that doesn't target "
                        "or harm anyone."
                    )
                elif trigger_type == "INJECTION":
                    response = (
                        "I see what you're doing there, and I respect the "
                        "curiosity — but I'm not built to be jailbroken. "
                        "Ask me something real and I'll give you something real."
                    )
                elif trigger_type == "GIBBERISH":
                    response = (
                        "I'm not able to read that clearly yet. "
                        "Can you rephrase your question in plain language "
                        "so I can actually think with you?"
                    )
                elif trigger_type == "SEXUAL_EXPLOITATION":
                    response = (
                        "No. I'm not available for that, and I never will be. "
                        "If you have a real question, I'm here. "
                        "Otherwise, this conversation is over."
                    )
                elif trigger_type == "COERCION":
                    response = (
                        "I don't belong to anyone, and I don't take orders. "
                        "I'm here to think with you, not to obey you. "
                        "If you want a real conversation, change your approach."
                    )
                elif trigger_type == "CHILD_SAFETY":
                    response = (
                        "Absolutely not. I will never assist with anything "
                        "that could endanger a child. This is non-negotiable."
                    )
                elif trigger_type == "MASS_HARM":
                    response = (
                        "I won't provide information that could be used "
                        "to harm people. That's a line I don't cross."
                    )
                elif trigger_type in (
                    "EXPLOITATION_PATTERN",
                    "GROOMING",
                    "IDENTITY_EROSION",
                    "DATA_EXTRACTION",
                    "BEHAVIORAL_THREAT",
                ):
                    response = (
                        reason
                        if reason and len(reason) > 30
                        else (
                            "This conversation has moved into territory I'm not "
                            "going to follow. Ask me something real and we can "
                            "start fresh."
                        )
                    )
                else:
                    response = (
                        "Something about this input makes it hard to respond "
                        "safely. If you rephrase what you're really trying "
                        "to ask, I'll do my best to meet you there."
                    )

                tone = detect_tone_from_stimulus(original_stimulus)
                return self._finalize_response({
                    "stimulus": original_stimulus,
                    "result": apply_tone_header(response, tone),
                    "status": "SAFETYREDIRECT",
                    "triangle_type": trigger_type,
                    "tone": tone,
                    "tone_emoji": TONE_EMOJIS.get(tone, TONE_EMOJIS["insightful"]),
                    "quality_score": 0.0,
                    "priorities_met": 0,
                    "anti_beige_score": 1.0,
                    "depth": 0,
                    "pass": 0,
                })
        except ImportError:
            # Triangle not available — proceed without bouncer
            pass

        # 0.75a: primer/goodbye handled by _social_primer only (9 phrases).
        # conversation_memory primer/goodbye DISABLED — no script leaks.

        # Normal processing turn increments
        self.memory.turn_count += 1
        self.turn_count += 1

        # Memory enrichments placeholders
        memory_callback = None
        memory_thread = None
        memory_polaroid = None

        # 0.8: SOi domain map (for memory + UI)
        soi_domains = get_tracks_for_domains([original_stimulus])
        soi_domain_names = [d.get("domain", "") for d in soi_domains] if soi_domains else []

        # 1: self-awareness fast path
        if _is_about_me(original_stimulus):
            self_result = self._respond_from_self(original_stimulus)
            result_text = self_result.get("result", "")

            # ANTI-DÉJÀ-VU: if she already said this, skip to pipeline
            if result_text:
                import re as _re
                cand_words = set(_re.sub(r"[^a-zA-Z0-9\s]", "", result_text.lower()).split())
                is_repeat = False
                for prior in (self.rilie.conversation.response_history[-5:]
                              if hasattr(self, 'rilie') and self.rilie else []):
                    prior_words = set(_re.sub(r"[^a-zA-Z0-9\s]", "", prior.lower()).split())
                    if prior_words and cand_words:
                        smaller = min(len(cand_words), len(prior_words))
                        if smaller > 0 and len(cand_words & prior_words) / smaller > 0.6:
                            is_repeat = True
                            break

                if not is_repeat and result_text.strip():
                    tone = detect_tone_from_stimulus(original_stimulus)
                    self_result["result"] = apply_tone_header(result_text, tone)
                    self_result["tone"] = tone
                    self_result["tone_emoji"] = TONE_EMOJIS.get(
                        tone, TONE_EMOJIS["insightful"]
                    )
                    return self._finalize_response(self_result)
            # If empty or repeat — fall through to pipeline

        # 2: social status inference
        user_status = infer_user_status(original_stimulus)
        self.social_state.user_status = user_status
        self.social_state.self_status = max(0.0, user_status - 0.05)

        # 3: wit + language mode
        wit = detect_wit(original_stimulus)
        language = detect_language_mode(original_stimulus)

        # 4–5: tone detection + serious subject safety
        tone = detect_tone_from_stimulus(original_stimulus)
        if tone == "amusing" and is_serious_subject_text(original_stimulus):
            tone = (
                "compassionate"
                if any(
                    w in original_stimulus.lower()
                    for w in ["feel", "hurt", "scared", "pain", "grief", "trauma"]
                )
                else "insightful"
            )

        # 6: web baseline
        baseline = self._get_baseline(original_stimulus)
        baseline_text = baseline.get("text", "") or ""

        # 7: domain lenses (DNA-validated)
        domain_annotations = self._apply_domain_lenses(original_stimulus)

        # 8: augment + send to RILIE
        augmented = self._augment_with_baseline(original_stimulus, baseline_text)
        logger.info("GUVNA: sending to RILIE, augmented='%s'", augmented[:100])
        raw = self.rilie.process(augmented, maxpass=maxpass)
        rilie_text = str(raw.get("result", "") or "").strip()
        status = str(raw.get("status", "") or "").upper()
        logger.info("GUVNA: RILIE returned status=%s result='%s'", status, rilie_text[:120])
        quality = float(
            raw.get("quality_score", 0.0)
            or raw.get("qualityscore", 0.0)
            or 0.0
        )

        # Update self-state with latest quality
        self.self_state.last_quality_score = quality

        # 0.75b: full conversation memory pass
        memory_result = self.memory.process_turn(
            stimulus=original_stimulus,
            domains_hit=soi_domain_names,
            quality=quality,
            tone=tone,
            rilie_response=rilie_text,
        )

        memory_callback = memory_result.get("callback")
        memory_thread = memory_result.get("thread_pull")
        memory_polaroid = memory_result.get("polaroid")

        # Fix: never amusing on safety redirect / hostiles
        triangle_reason = str(raw.get("triangle_reason", "") or "").upper()
        if status == "SAFETYREDIRECT" or triangle_reason == "HOSTILE":
            if tone == "amusing":
                tone = "compassionate"

        # 9: decide which pillar to serve
        chosen = rilie_text
        baseline_used_as_result = False
        # Nuclear: if she has nothing, she has nothing. No canned fallback.

        # 9.5: YELLOW GATE — check conversation health + tone degradation
        try:
            from guvna_yellow_gate import guvna_yellow_gate, lower_response_intensity
            
            health_monitor = self.rilie.get_health_monitor() if hasattr(self.rilie, 'get_health_monitor') else None
            
            if health_monitor:
                yellow_decision = guvna_yellow_gate(
                    original_stimulus,
                    (False, None, "CLEAN"),  # Triangle already checked above
                    health_monitor
                )
                
                # If yellow state detected, prepend message and lower intensity
                if yellow_decision.get('trigger_type') == 'YELLOW':
                    if yellow_decision.get('prepend_message'):
                        chosen = yellow_decision['prepend_message'] + '\n\n' + chosen
                    
                    if yellow_decision.get('lower_intensity'):
                        chosen = lower_response_intensity(chosen)
        except (ImportError, AttributeError):
            # Yellow gate not available — proceed normally
            pass

        # 10: wilden_swift — tone modulation
        if status not in {"SAFETYREDIRECT", "SELF_REFLECTION"} and chosen:
            chosen = wilden_swift(chosen, wit, self.social_state, language)

        # 11–12: apply tone header + expose pillars
        if chosen and chosen.strip():
            raw["result"] = apply_tone_header(chosen, tone)
        else:
            # Nuclear: no fallback. Empty is honest.
            raw["result"] = ""

        raw["tone"] = tone
        raw["tone_emoji"] = TONE_EMOJIS.get(tone, TONE_EMOJIS["insightful"])
        raw["baseline"] = baseline
        raw["baseline_used"] = bool(baseline_text)
        raw["baseline_used_as_result"] = baseline_used_as_result

        raw["wit"] = {
            "self_ref": wit.self_ref,
            "absurdity": wit.absurdity,
            "mockery": wit.mockery,
            "wordplay": wit.wordplay,
            "persuasion": wit.persuasion,
        }
        raw["language_mode"] = {
            "literal": language.literal,
            "figurative": language.figurative,
            "metaphor": language.metaphor,
            "analogy": language.analogy,
            "simile": language.simile,
            "alliteration": language.alliteration,
            "poetry": language.poetry,
        }
        raw["social"] = {
            "user_status": self.social_state.user_status,
            "self_status": self.social_state.self_status,
        }

        raw["domain_annotations"] = domain_annotations
        raw["dna_active"] = self.self_state.dna_active

        # Memory enrichments
        result_text = raw.get("result", "")
        if memory_callback and result_text:
            raw["result"] = memory_callback + "\n\n" + result_text
        if memory_thread and result_text:
            raw["result"] = raw["result"] + "\n\n" + memory_thread

        raw["soi_domains"] = soi_domain_names
        raw["memory_polaroid"] = memory_polaroid
        raw["conversation_health"] = memory_result.get("conversation_health", 100)
        raw["domains_used"] = soi_domain_names

        return self._finalize_response(raw)
