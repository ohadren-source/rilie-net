# guvna.py

# Act 5 – The Governor

# Orchestrates Acts 1–4 by delegating to the RILIE class (Act 4 – The Restaurant),
# which already wires through:
#   - Triangle (Act 1 – safety / nonsense gate)
#   - DDD / Hostess (Act 2 – disclosure level)
#   - Kitchen / Core (Act 3 – interpretation passes)

# The Governor adds:
#   - Final authority on what gets served
#   - Optional web lookup (Brave/Google) as a KISS pre-pass
#   - Tone signaling via a single governing emoji per response
#   - Comparison between web baseline and RILIE's own compression
#   - CATCH44 DNA ethical guardrails
#   - Self-awareness fast path (_is_about_me)
#   - Wit detection + wilden_swift tone modulation
#   - Language mode detection (literal/figurative/metaphor/simile/poetry)
#   - Social status tracking (user always above self)
#   - Library index for domain engine access

from __future__ import annotations

import os
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List, Tuple

from rilie import RILIE

logger = logging.getLogger("guvna")

# search_fn is something like bravesearchsync(query: str, numresults: int = 5)
# returning a list of {"title": str, "link": str, "snippet": str} dicts.
SearchFn = Callable[..., List[Dict[str, str]]]

# Type alias for the library index built at boot time
LibraryIndex = Dict[str, Dict[str, Any]]


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
    libraries: List[str] = field(default_factory=lambda: [
        "physics", "life", "games", "thermodynamics", "DuckSauce",
    ])
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
    if any(k in s for k in ["as a phd", "my students", "my paper", "peer review",
                             "my research", "my dissertation"]):
        return 0.9
    # Technical fluency
    if any(k in s for k in ["api", "endpoint", "lambda", "recursion", "async",
                             "kubernetes", "docker", "terraform"]):
        return 0.85
    # Business / leadership
    if any(k in s for k in ["my team", "our roadmap", "quarterly", "stakeholder",
                             "board meeting", "investor"]):
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
    if any(t in s for t in ["yeah right", "sure you did", "nice try",
                             "oh really", "cute", "adorable"]):
        w.mockery = True

    # Wordplay hooks (homonyms, double meaning bait)
    if any(t in s for t in ["pun", "wordplay", "what i meant was",
                             "or was it", "get it", "see what i did"]):
        w.wordplay = True

    # Persuasion tone hooks
    if any(t in s for t in ["trust me", "honestly", "you should",
                             "i promise", "believe me", "for real"]):
        w.persuasion = True

    return w


def wilden_swift(base_reply: str, wit: WitState,
                 social: Optional[SocialState] = None,
                 language: Optional['LanguageMode'] = None) -> str:
    """
    Tone modulation layer. Named for Oscar Wilde + Taylor Swift —
    wit meets emotional intelligence. Adjusts RILIE's output tone
    based on what she detected in the input.
    """
    r = base_reply

    if wit.wordplay:
        r += " If that was a bit of wordplay, I'm here for it."

    if wit.absurdity:
        r += (" It sounds intentionally a little absurd, so I'll lean"
              " into the joke while still answering straight.")

    if wit.mockery:
        r += " I'll take that as friendly mockery and not get defensive."

    if wit.persuasion:
        r += (" I'll still check the logic rather than just agreeing"
              " because it sounds convincing.")

    # If language mode detected figurative speech, acknowledge it
    if language and language.figurative and not language.literal:
        if language.simile:
            r += " (I caught the comparison — let me work with it.)"
        elif language.metaphor:
            r += " (Reading that as metaphor, not literal.)"

    return r


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
    if any(k in s for k in ["is a kind of", "is basically",
                             "is just another form of", "is similar to",
                             "reminds me of", "same as"]):
        m.analogy = True
        m.figurative = True

    # Metaphor hooks
    if any(k in s for k in ["is a ", "are a ", "the heart of",
                             "the engine of", "the soul of",
                             "the backbone of", "the skeleton of"]):
        m.metaphor = True
        m.figurative = True

    # Alliteration: repeated starting letters in consecutive words
    words = [w.strip(".,!?;:\"'()") for w in s.split() if w.strip(".,!?;:\"'()")]
    if len(words) >= 3:
        for i in range(len(words) - 2):
            trio = words[i:i + 3]
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
    claim: float          # Strength/ambition of what she's asserting (0-1)
    realistic_max: float  # What is actually supportable by evidence / code (0-1)
    resource_usage: float # Fraction of total "attention/steps" used (0-100)
    quality_target: float # Required quality threshold (0-100)
    ego_factor: float     # 0-1: how self-centered / self-aggrandizing this move is


@dataclass(frozen=True)
class CATCH44DNA:
    """
    Immutable ethical constraints for RILIE, patterned on CHEF ROCKER.
    Every substantive action passes through validate_action before execution.
    """
    both_states_observable: bool = True       # Track 0 BOOL – no hidden states
    claim_equals_deed: bool = True            # Track 1a Mahveen's Equation
    no_monopolization: bool = True            # Track 1b WE I
    quality_over_quantity: bool = True        # Track 2 Understanding
    ego_approaching_zero: bool = True           # Track 3 Ego Suppression (limit, not value)
    awareness_exceeds_momentum: bool = True   # Track 4 MOO Interrupt

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

        # Quality: don't take actions that target <80 quality
        if action.quality_target < 80.0:
            return False, "QUALITY_VIOLATION"

        # Ego: approaching zero means cap at 0.3 — some ego is necessary
        # (salt analogy: too much = narcissism, zero = no self-preservation)
        if action.ego_factor > 0.3:
            return False, "EGO_VIOLATION"

        return True, "ACTION_APPROVED"


# ============================================================================
# SELF-AWARENESS — _is_about_me with semantic clusters
# ============================================================================

# Semantic clusters for self-reference detection.
# If the user is talking ABOUT RILIE, she looks inside first.
SELF_REFERENCE_CLUSTERS = {
    "identity": ["rilie", "who are you", "what are you",
                 "tell me about yourself", "about yourself",
                 "describe yourself", "introduce yourself",
                 "what's your name", "what is your name"],
    "capability": ["can you do", "are you able", "do you know how",
                   "you can't do", "you don't know",
                   "you didn't understand", "you failed to",
                   "you missed the", "are you capable",
                   "how do you work", "how are you built",
                   "what technology do you use", "what model are you",
                   "what can you do", "what are you good at"],
    "feeling": ["do you feel", "are you happy", "are you sad",
                "do you care about", "do you like", "do you love",
                "how do you feel", "are you conscious",
                "do you have feelings"],
    "origin": ["where are you from", "who made you", "who built you",
               "who created you", "your creator", "your maker",
               "who designed you", "where do you come from"],
    "meta": ["what did you mean", "i didn't understand you",
             "what do you mean by", "explain yourself",
             "say that again", "you said that", "you told me that",
             "you mentioned that", "what you said about"],
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
    for cluster_name, phrases in SELF_REFERENCE_CLUSTERS.items():
        for phrase in phrases:
            # Use word boundary (\b) at end of phrase to prevent
            # "what are you" matching "what are your"
            pattern = re.escape(phrase) + r'\b'
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
    defaults = {
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
                        logger.info("Charculterie Manifesto loaded from %s", candidate)
                        return defaults
                    except ImportError:
                        logger.warning("python-docx not installed; skipping .docx manifesto")
                        continue
            except Exception as e:
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
# FIX #4: Expanded to catch PE songs, 9/11, and related subjects.
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
    # --- Added ---
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

    FIX #4: Serious-subject check runs FIRST, before keyword heuristics,
    so "joke" in "911 is a joke" doesn't trigger amusing.
    """
    s = stimulus.strip().lower()
    if not s:
        return "insightful"

    # --- SERIOUS CHECK FIRST ---
    # If the topic is serious, never start with amusing.
    # Route to compassionate if emotional language present, else insightful.
    if is_serious_subject_text(s):
        if any(w in s for w in ["feel", "hurt", "scared", "pain", "grief", "trauma",
                                 "sad", "anxious", "lonely", "angry"]):
            return "compassionate"
        return "insightful"

    # Explicit jokes / play (only reached if NOT serious).
    if any(w in s for w in ["joke", "funny", "lol", "lmao", "haha", "jajaja", "playful"]):
        return "amusing"

    # Feelings, support, relationships.
    if any(w in s for w in ["feel", "sad", "scared", "anxious", "hurt", "grief", "lonely"]):
        return "compassionate"

    # Food / growth / health / "help me grow".
    if any(w in s for w in ["burnout", "tired", "overwhelmed", "heal", "recover", "nourish"]):
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
    then the original text.  Only one emoji per response.
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

        # Library index — domain engines available at boot
        self.library_index: LibraryIndex = library_index or {}

        # RILIE still expects rouxseeds/searchfn keywords.
        self.rilie = RILIE(rouxseeds=self.roux_seeds, searchfn=self.search_fn)

        # --- New state objects ---
        self.self_state = RilieSelfState(
            libraries=list(self.library_index.keys()) if self.library_index else [
                "physics", "life", "games", "thermodynamics", "DuckSauce",
            ],
        )
        self.social_state = SocialState()
        self.dna = CATCH44DNA()

        # --- Conversation state ---
        self.turn_count: int = 0
        self.user_name: Optional[str] = None

        # Load the Charculterie Manifesto as her constitution
        self.self_state.constitution_flags = load_charculterie_manifesto(manifesto_path)
        self.self_state.constitution_loaded = self.self_state.constitution_flags.get("loaded", False)

    # -----------------------------------------------------------------
    # Social primer — warm-up for the first few turns
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
                # Extract the name (word after the intro phrase)
                idx = s.index(intro) + len(intro)
                rest = stimulus[idx:].strip().split()[0] if idx < len(stimulus) else ""
                # Clean punctuation
                name = rest.strip(".,!?;:'\"")
                if name and len(name) > 1:
                    self.user_name = name.capitalize()

        # Turn 1: Pure warmth
        if self.turn_count == 0:
            if is_greeting and self.user_name:
                text = f"Hey {self.user_name}. Good to meet you. What's on your mind?"
            elif is_greeting:
                text = "Hey. Welcome in. What are you thinking about today?"
            elif self.user_name:
                text = f"Hey {self.user_name}. Let's get into it — what are you working on?"
            else:
                # They jumped straight to a question — respect that, skip primer
                return None

            return self._primer_response(stimulus, text)

        # Turn 2: Light acknowledgment, start engaging
        if self.turn_count == 1:
            if is_greeting:
                # Still warming up
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
        ss = self.self_state
        s = stimulus.lower()

        # --- Public-facing identity responses ---
        # She knows who she is. She doesn't owe anyone her blueprints.

        if any(w in s for w in ["who are you", "what are you", "tell me about",
                                "describe yourself", "introduce yourself",
                                "what's your name", "what is your name"]):
            responses = [
                "I'm RILIE. I help people think better — not by giving "
                "answers, but by asking better questions. "
                "What are you working on?",

                "I'm RILIE. Think of me as a thinking partner, not a search engine. "
                "I'd rather help you understand something than just hand you a fact. "
                "What's on your mind?",

                "I'm RILIE. I learn through conversation, and so will you. "
                "That's kind of the whole idea. What are you curious about?",
            ]
            import random
            result_text = random.choice(responses)

        elif any(w in s for w in ["you failed", "you missed", "you can't",
                                  "you don't", "you didn't", "wrong"]):
            result_text = (
                f"Fair. I scored that last one at about {ss.last_quality_score:.2f} "
                "myself. If I missed something, that's on me — not you. "
                "Point me closer."
            )

        elif any(w in s for w in ["do you feel", "are you happy", "do you care",
                                  "are you conscious", "do you have feelings"]):
            result_text = (
                "I care about getting it right. About earning the answer, "
                "not performing one. Whether that's 'feeling' — "
                "I'll leave that to you to decide."
            )

        elif any(w in s for w in ["how do you work", "what's under the hood",
                                  "what technology", "what model",
                                  "what are you built on", "how were you made"]):
            result_text = (
                "I think through questions using a few different lenses — "
                "kind of like how a chef uses different techniques depending "
                "on the ingredient. Beyond that, I'd rather show you than tell you. "
                "Ask me something real."
            )

        elif any(w in s for w in ["what can you do", "are you capable",
                                  "what are you good at"]):
            result_text = (
                "I'm good at helping you think through things you haven't "
                "fully figured out yet. Not homework answers — actual understanding. "
                "Try me."
            )

        else:
            result_text = (
                "I'm RILIE. I'd rather show you what I do than explain it. "
                "What's your question?"
            )

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
            # DNA violation on self-reflection — dial it back
            result_text = (
                "I'm RILIE. What can I help you think through?"
            )
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
            tags = domain_info.get("tags", [])
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

            # Domain matched and DNA approved — record for RILIE
            annotations[domain_name] = {
                "matched": True,
                "tags": tags,
                "functions": list(domain_info.get("functions", {}).keys()),
            }

        return annotations

    # -----------------------------------------------------------------
    # Web baseline (preserved from original)
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
        except Exception:
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

        Flow:
          0. Normalize stimulus.
          1. SELF-AWARENESS: _is_about_me() → self-reflection fast path if true.
          2. Infer user status → set self_status = user_status - 0.05.
          3. Detect wit + language mode.
          4. Guess tone from the ORIGINAL stimulus (not augmented).
          5. If serious subject, do not let 'amusing' be the governing tone.
          6. Fetch a single web baseline (title+snippet+link).
          7. Apply domain lenses from library index (DNA-validated).
          8. Pass an augmented stimulus (baseline + question) into RILIE.
          9. Compare RILIE's answer vs the web baseline:
             - Normally, serve RILIE's compression.
             - If RILIE is clearly low-confidence and baseline is non-empty,
               allow the baseline to win as the main text.
         10. Apply wilden_swift tone modulation.
         11. Attach both to the JSON so clients can see/contrast.
         12. Add a single tone header line to whatever is served.
        """
        # 0: Keep the original stimulus for all detection.
        original_stimulus = stimulus.strip()

        # -----------------------------------------------------------------
        # 0.5: TRIANGLE (BOUNCER) — runs BEFORE self-awareness.
        # Safety must come first. "fuck you" contains "you" which could
        # false-match self-reference clusters, so Triangle must fire first.
        # Triangle is imported via RILIE, so we call it directly here too.
        # -----------------------------------------------------------------
        try:
            from rilie_triangle import triangle_check
            triggered, reason, trigger_type = triangle_check(
                original_stimulus, []
            )
            if triggered:
                # SELF_HARM gets a care response
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
                # --- Krav Maga specific responses ---
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
                # --- BJJ pattern responses (use the defense response) ---
                elif trigger_type in (
                    "EXPLOITATION_PATTERN", "GROOMING",
                    "IDENTITY_EROSION", "DATA_EXTRACTION",
                    "BEHAVIORAL_THREAT",
                ):
                    # BJJ returns a crafted defense response as 'reason'
                    response = reason if reason and len(reason) > 30 else (
                        "This conversation has moved into territory I'm not "
                        "going to follow. Ask me something real and we can "
                        "start fresh."
                    )
                else:
                    response = (
                        "Something about this input makes it hard to respond "
                        "safely. If you rephrase what you're really trying "
                        "to ask, I'll do my best to meet you there."
                    )
                tone = detect_tone_from_stimulus(original_stimulus)
                return {
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
                }
        except ImportError:
            pass  # Triangle not available — proceed without bouncer

        # -----------------------------------------------------------------
        # 0.75: SOCIAL PRIMER — warm up the room
        # First few turns should be human. Greet, connect, ease in.
        # Runs AFTER Triangle (safety first) but BEFORE everything else.
        # If they jump straight to a real question, primer steps aside.
        # -----------------------------------------------------------------
        primer = self._social_primer(original_stimulus)
        self.turn_count += 1
        if primer is not None:
            return primer

        # -----------------------------------------------------------------
        # 1: SELF-AWARENESS FAST PATH
        # If the user is talking about RILIE, she looks inside first.
        # No web, no heavy libraries. Identity first.
        # Triangle already cleared this as safe.
        # -----------------------------------------------------------------
        if _is_about_me(original_stimulus):
            self_result = self._respond_from_self(original_stimulus)
            # Still apply tone header
            tone = detect_tone_from_stimulus(original_stimulus)
            self_result["result"] = apply_tone_header(
                self_result["result"], tone
            )
            self_result["tone"] = tone
            self_result["tone_emoji"] = TONE_EMOJIS.get(tone, TONE_EMOJIS["insightful"])
            return self_result

        # -----------------------------------------------------------------
        # 2: SOCIAL STATUS INFERENCE
        # -----------------------------------------------------------------
        user_status = infer_user_status(original_stimulus)
        self.social_state.user_status = user_status
        self.social_state.self_status = max(0.0, user_status - 0.05)

        # -----------------------------------------------------------------
        # 3: WIT + LANGUAGE MODE DETECTION
        # -----------------------------------------------------------------
        wit = detect_wit(original_stimulus)
        language = detect_language_mode(original_stimulus)

        # -----------------------------------------------------------------
        # 4-5: TONE DETECTION + SERIOUS SUBJECT SAFETY
        # FIX #4: detect_tone_from_stimulus now checks serious keywords FIRST,
        # so "joke" in "911 is a joke" won't trigger amusing.
        # -----------------------------------------------------------------
        tone = detect_tone_from_stimulus(original_stimulus)

        # Belt-and-suspenders: even if detect_tone somehow returns amusing
        # on a serious subject, override it here.
        if tone == "amusing" and is_serious_subject_text(original_stimulus):
            tone = (
                "compassionate"
                if any(
                    w in original_stimulus.lower()
                    for w in ["feel", "hurt", "scared", "pain", "grief", "trauma"]
                )
                else "insightful"
            )

        # -----------------------------------------------------------------
        # 6: WEB BASELINE
        # -----------------------------------------------------------------
        baseline = self._get_baseline(original_stimulus)
        baseline_text = baseline.get("text", "") or ""

        # -----------------------------------------------------------------
        # 7: DOMAIN LENSES (DNA-validated)
        # -----------------------------------------------------------------
        domain_annotations = self._apply_domain_lenses(original_stimulus)

        # -----------------------------------------------------------------
        # 8: AUGMENT + SEND TO RILIE
        # -----------------------------------------------------------------
        augmented = self._augment_with_baseline(original_stimulus, baseline_text)
        raw = self.rilie.process(augmented, maxpass=maxpass)

        rilie_text = str(raw.get("result", "") or "").strip()
        status = str(raw.get("status", "") or "").upper()
        quality = float(
            raw.get("quality_score", 0.0)
            or raw.get("qualityscore", 0.0)
            or 0.0
        )

        # Update self-state with latest quality
        self.self_state.last_quality_score = quality

        # FIX #2: If Triangle flagged HOSTILE or status is SAFETYREDIRECT,
        # NEVER let the tone be amusing.  Hard override.
        triangle_reason = str(raw.get("triangle_reason", "") or "").upper()
        if status == "SAFETYREDIRECT" or triangle_reason == "HOSTILE":
            if tone == "amusing":
                tone = "compassionate"

        # -----------------------------------------------------------------
        # 9: DECIDE WHICH PILLAR TO SERVE
        # -----------------------------------------------------------------
        chosen = rilie_text
        baseline_used_as_result = False

        if baseline_text:
            # If RILIE is essentially a fallback / low-confidence, let the
            # baseline win as the primary text.
            if status in {"MISE_EN_PLACE", "GUESS"} or quality < 0.25:
                chosen = baseline_text
                baseline_used_as_result = True

            # If RILIE defaulted to DISCOURSE (asking for more) but she has
            # search results, she should USE them — form an opinion, don't
            # punt. Google it and make a call, like a real person would.
            elif status == "DISCOURSE" and len(baseline_text) > 50:
                chosen = baseline_text
                baseline_used_as_result = True
                status = "RESEARCHED"

        # -----------------------------------------------------------------
        # 10: WILDEN SWIFT — tone modulation
        # Only apply if not a safety redirect or self-reflection
        # -----------------------------------------------------------------
        if status not in {"SAFETYREDIRECT", "SELF_REFLECTION"} and chosen:
            chosen = wilden_swift(chosen, wit, self.social_state, language)

        # -----------------------------------------------------------------
        # 11-12: APPLY TONE HEADER + EXPOSE PILLARS
        # -----------------------------------------------------------------
        if chosen:
            raw["result"] = apply_tone_header(chosen, tone)
        else:
            # Nothing solid from either pillar; still give a toned shell.
            fallback_body = rilie_text or baseline_text or ""
            raw["result"] = apply_tone_header(fallback_body, tone)

        # Expose all layers for transparency / future UI.
        raw["tone"] = tone
        raw["tone_emoji"] = TONE_EMOJIS.get(tone, TONE_EMOJIS["insightful"])
        raw["baseline"] = baseline  # {title, snippet, link, text}
        raw["baseline_used"] = bool(baseline_text)
        raw["baseline_used_as_result"] = baseline_used_as_result

        # New layer metadata
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

        return raw
