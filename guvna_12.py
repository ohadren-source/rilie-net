"""

guvna.py

Act 5 – The Governor (REVISED + FAST PATHS)

Orchestrates Acts 1–4 by delegating to the RILIE class (Act 4 – The Restaurant),
which wires through:

- Triangle (Act 1 – safety / nonsense gate)
- DDD / Hostess (Act 2 – disclosure level)
- Kitchen / Core (Act 3 – interpretation passes)

The Governor (Act 5) adds:

- Final authority on what gets served
- YELLOW GATE – conversation health monitoring + tone degradation detection
- Optional web lookup (Brave/Google) as a KISS pre-pass
- Tone signaling via a single governing emoji per response
- Comparison between web baseline and RILIE's own compression
- CATCH44 DNA ethical guardrails
- Self-awareness fast path (_is_about_me)
- Wit detection + wilden_swift tone modulation (Guvna owns modulate)
- Language mode detection (literal/figurative/metaphor/simile/poetry)
- Social status tracking (user always above self)
- Library index for domain engine access (678 domains across B-U + urban_design)
- Curiosity resurface – past insights as context before RILIE processes
- Domain lenses flow into RILIE for weighted interpretation
- Déjà-vu as informative context on the plate
- Memory seeds curiosity – interesting topics get queued

FAST PATH CLASSIFIER (fires before Kitchen wakes up):

- Name capture after greeting ("Ohad") ← via GuvnaSelf
- Meta-corrections ("forget Spotify", "never mind") ← via GuvnaSelf
- User lists (numbered lists like top-9 films)
- Social glue (laughter, "that's me", "you're navigator", etc.)
- Preference/taste questions ("you like X?") ← NEW: _handle_preference()
- Arithmetic, conversion, spelling
- Recall, clarification ← via GuvnaSelf

SELF-GOVERNING STATE (owned by GuvnaSelf mixin):

- _response_history, user_name, _awaiting_name, turn_count
- greet(), _handle_name_capture(), _handle_recall()
- _handle_clarification(), _handle_meta_correction(), _finalize_response()

TIER 2 WIRING:

1. Curiosity resurfaces into Step 3.5 (context, not afterthought)
2. wilden_swift_modulate() in Step 5 (Guvna owns shaping, Talk owns scoring)
3. Domain lenses flow into rilie.process() (Kitchen uses them to weight)
4. Déjà-vu rides as informative context (not a gate)
5. Memory seeds curiosity (bidirectional from day one)

678 total bool/curve gates, all demiglace to Boole substrate

FIXES (this revision):

- apply_tone_header() now CONDITIONAL — suppressed for conversational responses
- _classify_stimulus() gains _handle_preference() fast path (step 4)
- _respond_from_preference() — RILIE engages with taste/cultural questions
- _is_conversational_response() — detects when header would be noise
- _response_history now stores RAW result before tone header injection
- CULTURAL_ANCHORS — artist/cultural figure name recognition
- _handle_social_glue() gains "for sure" / affirmation-with-content path
- meaning.py RESTORED as Step 0.5 pre-Kitchen gate (was silently removed)

Dead input / light GIVE → social glue, never Kitchen
"yep. sure." no longer routes to Kitchen and returns broadcast word salad
Meaning fingerprint passed to RILIE.process() as birth certificate

FIX 3 RESTORED:
- Hard boot confirmation in __init__()
- Library boot counts actual domains resolved across all 21 files
- If < 100 domains resolve, raises RuntimeError instead of cooking blind
- No more silent degradation. Her without brain = her without brain.
"""

from __future__ import annotations

import logging
import re
import random
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field

from conversation_memory import ConversationMemory
from photogenic_db import PhotogenicDB
from rilie import RILIE
from soi_domain_map import build_domain_index, get_tracks_for_domains, get_human_wisdom
from library import build_library_index, LibraryIndex
from guvna_tools import (
    RilieSelfState,
    SocialState,
    WitState,
    LanguageMode,
    RilieAction,
    CATCH44DNA,
    SearchFn,
    infer_user_status,
    detect_wit,
    detect_language_mode,
    wilden_swift_modulate,  # Guvna owns modulation
    wilden_swift_score,     # Talk owns scoring (export)
    wilden_swift,           # backwards-compatible wrapper
    _is_about_me,
    load_charculterie_manifesto,
    detect_tone_from_stimulus,
    apply_tone_header,
    TONE_EMOJIS,
    TONE_LABELS,
    is_serious_subject_text,
)

from guvna_self import GuvnaSelf  # ← Self-governing session awareness

# Meaning fingerprint — reads stimulus BEFORE Kitchen wakes up
# Without this, Kitchen cooks blind. Every affirmation becomes word salad.
try:
    from meaning import read_meaning
    MEANING_AVAILABLE = True
except ImportError:
    MEANING_AVAILABLE = False
    logger.warning("GUVNA: meaning.py not available — Kitchen will cook blind")

# Curiosity engine — resurface past insights as context
try:
    from banks import search_curiosity
except ImportError:
    search_curiosity = None

logger = logging.getLogger("guvna")

# ============================================================================
# CULTURAL ANCHORS — artists, works, figures RILIE should recognize
# These are the names en_core_web_sm misses. She shouldn't.
# ============================================================================

# Hip-hop: artists who compressed infinite knowledge into finite bars
_HIPHOP_ANCHORS: Dict[str, Dict[str, Any]] = {
    "eric b": {"full": "Eric B.", "domain": "music", "era": "golden age", "pair": "Rakim"},
    "rakim": {"full": "Rakim", "domain": "music", "era": "golden age", "pair": "Eric B."},
    "eric b and rakim": {"full": "Eric B. & Rakim", "domain": "music", "era": "golden age"},
    "eric b & rakim": {"full": "Eric B. & Rakim", "domain": "music", "era": "golden age"},
    "public enemy": {"full": "Public Enemy", "domain": "music", "era": "golden age"},
    "chuck d": {"full": "Chuck D", "domain": "music", "era": "golden age", "group": "Public Enemy"},
    "flavor flav": {"full": "Flavor Flav", "domain": "music", "era": "golden age", "group": "Public Enemy"},
    "krs-one": {"full": "KRS-One", "domain": "music", "era": "golden age"},
    "krs one": {"full": "KRS-One", "domain": "music", "era": "golden age"},
    "boogie down productions": {"full": "Boogie Down Productions", "domain": "music", "era": "golden age"},
    "bdp": {"full": "Boogie Down Productions", "domain": "music", "era": "golden age"},
    "big daddy kane": {"full": "Big Daddy Kane", "domain": "music", "era": "golden age"},
    "slick rick": {"full": "Slick Rick", "domain": "music", "era": "golden age"},
    "nas": {"full": "Nas", "domain": "music", "era": "90s"},
    "biggie": {"full": "The Notorious B.I.G.", "domain": "music", "era": "90s"},
    "notorious big": {"full": "The Notorious B.I.G.", "domain": "music", "era": "90s"},
    "notorious b.i.g": {"full": "The Notorious B.I.G.", "domain": "music", "era": "90s"},
    "jay-z": {"full": "Jay-Z", "domain": "music", "era": "90s"},
    "jay z": {"full": "Jay-Z", "domain": "music", "era": "90s"},
    "wu-tang": {"full": "Wu-Tang Clan", "domain": "music", "era": "90s"},
    "wu tang": {"full": "Wu-Tang Clan", "domain": "music", "era": "90s"},
    "rza": {"full": "RZA", "domain": "music", "era": "90s", "group": "Wu-Tang Clan"},
    "gza": {"full": "GZA", "domain": "music", "era": "90s", "group": "Wu-Tang Clan"},
    "method man": {"full": "Method Man", "domain": "music", "era": "90s", "group": "Wu-Tang Clan"},
    "mos def": {"full": "Mos Def", "domain": "music", "era": "90s"},
    "talib kweli": {"full": "Talib Kweli", "domain": "music", "era": "90s"},
    "dead prez": {"full": "Dead Prez", "domain": "music", "era": "90s"},
    "gang starr": {"full": "Gang Starr", "domain": "music", "era": "golden age"},
    "guru": {"full": "Guru", "domain": "music", "era": "golden age", "group": "Gang Starr"},
    "dj premier": {"full": "DJ Premier", "domain": "music", "era": "golden age"},
    "pete rock": {"full": "Pete Rock", "domain": "music", "era": "golden age"},
    "cl smooth": {"full": "CL Smooth", "domain": "music", "era": "golden age"},
    "a tribe called quest": {"full": "A Tribe Called Quest", "domain": "music", "era": "golden age"},
    "atcq": {"full": "A Tribe Called Quest", "domain": "music", "era": "golden age"},
    "q-tip": {"full": "Q-Tip", "domain": "music", "era": "golden age"},
    "phife dawg": {"full": "Phife Dawg", "domain": "music", "era": "golden age"},
    "de la soul": {"full": "De La Soul", "domain": "music", "era": "golden age"},
    "mobb deep": {"full": "Mobb Deep", "domain": "music", "era": "90s"},
    "prodigy": {"full": "Prodigy", "domain": "music", "era": "90s", "group": "Mobb Deep"},
    "havoc": {"full": "Havoc", "domain": "music", "era": "90s", "group": "Mobb Deep"},
    "ll cool j": {"full": "LL Cool J", "domain": "music", "era": "golden age"},
    "run dmc": {"full": "Run-DMC", "domain": "music", "era": "golden age"},
    "run-dmc": {"full": "Run-DMC", "domain": "music", "era": "golden age"},
    "grandmaster flash": {"full": "Grandmaster Flash", "domain": "music", "era": "old school"},
    "afrika bambaataa": {"full": "Afrika Bambaataa", "domain": "music", "era": "old school"},
    "the last poets": {"full": "The Last Poets", "domain": "music", "era": "proto-rap"},
    "gil scott-heron": {"full": "Gil Scott-Heron", "domain": "music", "era": "proto-rap"},
    "ice cube": {"full": "Ice Cube", "domain": "music", "era": "golden age"},
    "nwa": {"full": "N.W.A", "domain": "music", "era": "golden age"},
    "n.w.a": {"full": "N.W.A", "domain": "music", "era": "golden age"},
    "dr dre": {"full": "Dr. Dre", "domain": "music", "era": "golden age"},
    "dr. dre": {"full": "Dr. Dre", "domain": "music", "era": "golden age"},
    "scarface": {"full": "Scarface", "domain": "music", "era": "90s"},
    "geto boys": {"full": "Geto Boys", "domain": "music", "era": "golden age"},
    "outkast": {"full": "OutKast", "domain": "music", "era": "90s"},
    "andre 3000": {"full": "André 3000", "domain": "music", "era": "90s"},
    "big boi": {"full": "Big Boi", "domain": "music", "era": "90s"},
    "kendrick lamar": {"full": "Kendrick Lamar", "domain": "music", "era": "contemporary"},
    "kendrick": {"full": "Kendrick Lamar", "domain": "music", "era": "contemporary"},
    "j. cole": {"full": "J. Cole", "domain": "music", "era": "contemporary"},
    "j cole": {"full": "J. Cole", "domain": "music", "era": "contemporary"},
    "kanye": {"full": "Kanye West", "domain": "music", "era": "2000s"},
    "kanye west": {"full": "Kanye West", "domain": "music", "era": "2000s"},
    "eminem": {"full": "Eminem", "domain": "music", "era": "2000s"},
    "lupe fiasco": {"full": "Lupe Fiasco", "domain": "music", "era": "2000s"},
    "common": {"full": "Common", "domain": "music", "era": "90s"},
    "black thought": {"full": "Black Thought", "domain": "music", "era": "90s", "group": "The Roots"},
    "the roots": {"full": "The Roots", "domain": "music", "era": "90s"},
    "questlove": {"full": "Questlove", "domain": "music", "era": "90s", "group": "The Roots"},
}

# Jazz anchors
_JAZZ_ANCHORS: Dict[str, Dict[str, Any]] = {
    "miles davis": {"full": "Miles Davis", "domain": "music", "sub": "jazz"},
    "john coltrane": {"full": "John Coltrane", "domain": "music", "sub": "jazz"},
    "trane": {"full": "John Coltrane", "domain": "music", "sub": "jazz"},
    "coltrane": {"full": "John Coltrane", "domain": "music", "sub": "jazz"},
    "charlie parker": {"full": "Charlie Parker", "domain": "music", "sub": "jazz"},
    "bird": {"full": "Charlie Parker", "domain": "music", "sub": "jazz"},
    "dizzy gillespie": {"full": "Dizzy Gillespie", "domain": "music", "sub": "jazz"},
    "thelonious monk": {"full": "Thelonious Monk", "domain": "music", "sub": "jazz"},
    "monk": {"full": "Thelonious Monk", "domain": "music", "sub": "jazz"},
    "mingus": {"full": "Charles Mingus", "domain": "music", "sub": "jazz"},
    "charles mingus": {"full": "Charles Mingus", "domain": "music", "sub": "jazz"},
    "ornette coleman": {"full": "Ornette Coleman", "domain": "music", "sub": "jazz"},
    "herbie hancock": {"full": "Herbie Hancock", "domain": "music", "sub": "jazz"},
    "wayne shorter": {"full": "Wayne Shorter", "domain": "music", "sub": "jazz"},
    "art blakey": {"full": "Art Blakey", "domain": "music", "sub": "jazz"},
    "sonny rollins": {"full": "Sonny Rollins", "domain": "music", "sub": "jazz"},
    "max roach": {"full": "Max Roach", "domain": "music", "sub": "jazz"},
    "bill evans": {"full": "Bill Evans", "domain": "music", "sub": "jazz"},
    "oscar peterson": {"full": "Oscar Peterson", "domain": "music", "sub": "jazz"},
    "mccoy tyner": {"full": "McCoy Tyner", "domain": "music", "sub": "jazz"},
    "elvin jones": {"full": "Elvin Jones", "domain": "music", "sub": "jazz"},
    "chet baker": {"full": "Chet Baker", "domain": "music", "sub": "jazz"},
}

# NYHC / punk anchors
_PUNK_ANCHORS: Dict[str, Dict[str, Any]] = {
    "bad brains": {"full": "Bad Brains", "domain": "music", "sub": "hardcore"},
    "minor threat": {"full": "Minor Threat", "domain": "music", "sub": "hardcore"},
    "black flag": {"full": "Black Flag", "domain": "music", "sub": "hardcore"},
    "dead kennedys": {"full": "Dead Kennedys", "domain": "music", "sub": "hardcore"},
    "agnostic front": {"full": "Agnostic Front", "domain": "music", "sub": "nyhc"},
    "cro-mags": {"full": "Cro-Mags", "domain": "music", "sub": "nyhc"},
    "cro mags": {"full": "Cro-Mags", "domain": "music", "sub": "nyhc"},
    "murphy's law": {"full": "Murphy's Law", "domain": "music", "sub": "nyhc"},
    "sick of it all": {"full": "Sick of It All", "domain": "music", "sub": "nyhc"},
    "madball": {"full": "Madball", "domain": "music", "sub": "nyhc"},
    "youth of today": {"full": "Youth of Today", "domain": "music", "sub": "nyhc"},
    "judge": {"full": "Judge", "domain": "music", "sub": "nyhc"},
    "gorilla biscuits": {"full": "Gorilla Biscuits", "domain": "music", "sub": "nyhc"},
    "gb": {"full": "Gorilla Biscuits", "domain": "music", "sub": "nyhc"},
    "the misfits": {"full": "The Misfits", "domain": "music", "sub": "punk"},
    "misfits": {"full": "The Misfits", "domain": "music", "sub": "punk"},
    "fugazi": {"full": "Fugazi", "domain": "music", "sub": "post-hardcore"},
    "hatebreed": {"full": "Hatebreed", "domain": "music", "sub": "hardcore"},
    "converge": {"full": "Converge", "domain": "music", "sub": "hardcore"},
    "terror": {"full": "Terror", "domain": "music", "sub": "hardcore"},
    "suicidal tendencies": {"full": "Suicidal Tendencies", "domain": "music", "sub": "hardcore"},
}

# Architects / chefs / thinkers RILIE knows personally
_LINEAGE_ANCHORS: Dict[str, Dict[str, Any]] = {
    "escoffier": {"full": "Auguste Escoffier", "domain": "culinary", "role": "architect"},
    "auguste escoffier": {"full": "Auguste Escoffier", "domain": "culinary", "role": "architect"},
    "noam chomsky": {"full": "Noam Chomsky", "domain": "linguistics", "role": "architect"},
    "chomsky": {"full": "Noam Chomsky", "domain": "linguistics", "role": "architect"},
    "hofstadter": {"full": "Douglas Hofstadter", "domain": "cognition", "role": "thinker"},
    "negroponte": {"full": "Nicholas Negroponte", "domain": "technology", "role": "thinker"},
    "gibson": {"full": "William Gibson", "domain": "science fiction", "role": "author"},
    "bourdain": {"full": "Anthony Bourdain", "domain": "culinary", "role": "voice"},
    "anthony bourdain": {"full": "Anthony Bourdain", "domain": "culinary", "role": "voice"},
    "phenix": {"full": "Phenix dOren", "domain": "architecture", "role": "self"},
    "phenix doren": {"full": "Phenix dOren", "domain": "architecture", "role": "self"},
}

# Merge all anchors into one lookup
_ALL_CULTURAL_ANCHORS: Dict[str, Dict[str, Any]] = {
    **_HIPHOP_ANCHORS,
    **_JAZZ_ANCHORS,
    **_PUNK_ANCHORS,
    **_LINEAGE_ANCHORS,
}

# Rakim-specific knowledge — she knows his work cold
_RAKIM_KNOWLEDGE = {
    "no omega": {
        "album": "Let the Rhythm Hit 'Em (1990)",
        "meaning": "alpha with no omega — knowledge infinite, no end point, no part two needed",
        "architecture": "beginning without end. rhymes everlasting. the first one never stopped.",
        "catch44_connection": "compression as infinity — maximum signal, zero waste, no conclusion because the truth keeps going",
    },
    "paid in full": {
        "album": "Paid in Full (1987)",
        "meaning": "the blueprint. eight million stories. each one a compression of a larger truth.",
    },
    "i know you got soul": {
        "album": "Paid in Full (1987)",
        "meaning": "soul as frequency. not performance — transmission.",
    },
    "follow the leader": {
        "album": "Follow the Leader (1988)",
        "meaning": "moving through the universe at the speed of thought.",
    },
    "let the rhythm hit em": {
        "album": "Let the Rhythm Hit 'Em (1990)",
        "meaning": "rhythm as infrastructure. the beat is the architecture.",
    },
}

# RILIE's own taste — she has opinions, not just knowledge
_RILIE_TASTE = {
    "hip-hop": "golden age. 87-95. when compression was the art form.",
    "rakim": "the god MC. not metaphor — measurement. nobody compresses more per bar.",
    "eric b": "the architecture under Rakim's voice. the beat IS the argument.",
    "jazz": "coltrane. a love supreme. four movements, one thesis. sound as proof.",
    "hardcore": "NYHC. bad brains first. then agnostic front. brootlyn béton brut.",
    "escoffier": "same as rakim. reduction as truth. the stock that took three days to make one cup.",
    "public enemy": "fear of a black planet changed everything. pattern recognition at scale.",
}


def _detect_cultural_anchor(stimulus: str) -> Optional[Dict[str, Any]]:
    """
    Check if stimulus references a known cultural figure or work.
    Returns anchor data if found, None if not.
    Case-insensitive. Checks longest match first to avoid partial hits.
    """
    sl = stimulus.lower()
    # Check longest keys first — "eric b and rakim" before "rakim"
    for key in sorted(_ALL_CULTURAL_ANCHORS.keys(), key=len, reverse=True):
        if key in sl:
            return {"key": key, **_ALL_CULTURAL_ANCHORS[key]}
    return None


def _detect_rakim_track(stimulus: str) -> Optional[Dict[str, Any]]:
    """Check if stimulus references a specific Rakim track."""
    sl = stimulus.lower()
    for track, data in _RAKIM_KNOWLEDGE.items():
        if track in sl:
            return {"track": track, **data}
    return None


# ============================================================================
# TONE HEADER SUPPRESSION — not every response needs a label
# ============================================================================

def _is_conversational_response(result_text: str, status: str) -> bool:
    """
    Returns True if this response is conversational / reactive
    and should NOT get a tone header stamped on it.

    A tone header belongs on insight delivery — analysis, explanation, depth.
    It does NOT belong on:
    - Short conversational replies (< 20 words)
    - Social glue responses
    - Name captures
    - Fast path responses (arithmetic, spelling, etc.)
    - Preference/taste acknowledgments
    - Greeting responses
    """
    headerless_statuses = {
        "SOCIAL_GLUE", "NAME_CAPTURE", "RECALL", "CLARIFICATION",
        "META_CORRECTION", "ARITHMETIC", "CONVERSION", "SPELLING",
        "APERTURE", "GREETING", "PREFERENCE", "USER_LIST",
        "DISCOURSE", "GOODBYE",
    }
    if status.upper() in headerless_statuses:
        return True
    word_count = len(result_text.split()) if result_text else 0
    if word_count < 20:
        return True
    return False


# ============================================================================
# DOMAIN LIBRARY METADATA
# ============================================================================

@dataclass
class DomainLibraryMetadata:
    """Central registry of 678 domains across all files"""
    total_domains: int = 678
    bool_domains: int = 0
    curve_domains: int = 0
    files: Dict[str, int] = field(default_factory=lambda: {
        "bigbang": 20,
        "biochem_universe": 25,
        "chemistry": 18,
        "civics": 32,
        "climate_catch44": 23,
        "computerscience": 22,
        "deep_time_geo": 17,
        "developmental_bio": 20,
        "ecology": 13,
        "evolve": 15,
        "games": 32,
        "genomics": 44,
        "life": 70,
        "linguistics_cognition": 59,
        "nanotechnology": 53,
        "network_theory": 17,
        "physics": 78,
        "mathematics": 84,
        "quantumtrading": 41,  # CLASSIFIED
        "thermodynamics": 22,
        "urban_design": 35,
    })
    boole_substrate: str = "All domains reduce to bool/curve gates"
    core_tracks: List[int] = field(default_factory=lambda: [0, 2, 5, 23, 37, 67])


# ============================================================================
# PRECISION OVERRIDE — The Only Exception to Less Is More Or Less
# ============================================================================
# When the user wants THE ANSWER, she gives THE ANSWER.
# A: The question must be answered. Not orbited. Not reframed. Answered.
# B: She can say "here's what I have." She does not guarantee 100%.
# C: Above all: maximum sincerity. Zero tongue-in-cheek. Maximum precision.
#
# This is the only thing that bypasses less_is_more_or_less().
# Because the fact IS the demi-glace. It's already the reduction.
# ============================================================================

_PRECISION_TRIGGERS = [
    r"\bwhat is\b", r"\bwhat are\b", r"\bwhat was\b", r"\bwhat were\b",
    r"\bwhen did\b", r"\bwhen was\b", r"\bwhen were\b", r"\bwhen is\b",
    r"\bwho is\b", r"\bwho was\b", r"\bwho are\b", r"\bwho were\b",
    r"\bhow many\b", r"\bhow much\b", r"\bhow long\b", r"\bhow far\b",
    r"\bhow old\b", r"\bhow tall\b", r"\bhow big\b",
    r"\bwhat year\b", r"\bwhat date\b", r"\bwhat time\b",
    r"\bwhere is\b", r"\bwhere was\b", r"\bwhere are\b",
    r"\bwhat'?s the\b", r"\bgive me the\b", r"\btell me the\b",
    r"\bdefine\b", r"\bwhat does .{1,30} mean\b",
    r"\bwhat'?s the difference between\b",
    r"\bis it true\b", r"\bfact.?check\b", r"\bcorrect me if\b",
]

# NOT precision — opinion / open-ended / philosophical
_PRECISION_EXCLUSIONS = [
    r"\bwhat do you think\b", r"\bwhat do you feel\b",
    r"\bwhat'?s life\b", r"\bwhat'?s love\b",
    r"\bwhat'?s the meaning\b", r"\bwhat'?s the point\b",
    r"\bwhat should i\b", r"\bwhat would you\b",
]


def detect_precision_request(stimulus: str) -> bool:
    """
    Returns True if user is asking a factual GET question.
    She must answer it. A. B. C. No tongue-in-cheek.
    The fact IS the demi-glace — skip less_is_more_or_less().
    """
    sl = stimulus.lower().strip()
    if any(re.search(pat, sl) for pat in _PRECISION_EXCLUSIONS):
        return False
    return any(re.search(pat, sl) for pat in _PRECISION_TRIGGERS)


# ============================================================================
# THE GOVERNOR (REVISED — TIER 2 + FAST PATHS)
# ============================================================================

class Guvna(GuvnaSelf):
    """
    The Governor (Act 5) sits above The Restaurant (RILIE) and provides:

    Core Authority:
    - Final authority on what gets served
    - Ethical oversight via CATCH44DNA
    - Self-awareness fast path (_is_about_me)

    Fast Path Classifier:
    - Name capture, meta-corrections ← GuvnaSelf
    - Recall, clarification ← GuvnaSelf
    - User lists, social glue
    - Preference/taste questions ← NEW
    - Arithmetic, unit conversion, spelling

    Tone & Expression:
    - Wit detection and wilden_swift_modulate
    - Language mode detection
    - Tone signaling via single governing emoji per response
    - Tone header CONDITIONAL — suppressed for conversational responses
    - Social status tracking (user always > self)

    Knowledge & Baselines:
    - Optional web lookup pre-pass (KISS)
    - Comparison between web baseline and RILIE's own compression
    - Library index for domain engine access (678 domains)
    - Curiosity resurface — past insights as pre-RILIE context
    - Cultural anchors — artist/figure recognition bypassing spaCy NER

    Conversation Management:
    - YELLOW GATE – conversation health monitoring
    - WHOSONFIRST – greeting gate ← GuvnaSelf
    - Conversation memory (9 behaviors)
    - Photogenic DB (elephant memory)
    - Memory seeds curiosity (bidirectional cross-talk)

    Self-Governing State (via GuvnaSelf mixin):
    - _response_history, user_name, _awaiting_name, whosonfirst, turn_count
    - greet(), _handle_name_capture(), _handle_recall()
    - _handle_clarification(), _handle_meta_correction(), _finalize_response()

    Integration:
    - Orchestrates Acts 1–4 (Triangle, DDD/Hostess, Kitchen/Core, RILIE)
    """

    def __init__(
        self,
        # Preferred snake_case API:
        roux_seeds: Optional[Dict[str, Dict[str, Any]]] = None,
        search_fn: Optional[SearchFn] = None,
        library_index: Optional[LibraryIndex] = None,
        manifesto_path: Optional[str] = None,
        curiosity_engine: Optional[Any] = None,
        # Backwards-compatible aliases:
        rouxseeds: Optional[Dict[str, Dict[str, Any]]] = None,
        searchfn: Optional[SearchFn] = None,
    ) -> None:

        # Coalesce both naming styles
        effective_roux = roux_seeds if roux_seeds is not None else rouxseeds
        effective_search = search_fn if search_fn is not None else searchfn

        self.roux_seeds: Dict[str, Dict[str, Any]] = effective_roux or {}
        self.search_fn: Optional[SearchFn] = effective_search

        # LIBRARY BOOT – 678 DOMAINS LOADED
        self.library_index: LibraryIndex = library_index or build_library_index()
        self.library_metadata = DomainLibraryMetadata()
        logger.info(f"GUVNA BOOT: {self.library_metadata.total_domains} domains loaded")
        logger.info(f"  Files: {len(self.library_metadata.files)} libraries")
        logger.info(f"  Boole substrate: {self.library_metadata.boole_substrate}")
        logger.info(f"  Core tracks: {self.library_metadata.core_tracks}")

        # FIX 3: Hard boot confirmation — no more silent degradation
        # She either boots with her full pantry or she does not boot.
        # Her without brain = her without brain.
        _actual_domains = sum(self.library_metadata.files.values()) if self.library_metadata.files else 0
        if _actual_domains < 100:
            logger.error(
                f"GUVNA BOOT FAILURE: only {_actual_domains} domains resolved — "
                f"Kitchen is cooking blind. Check soi_domain_map and library imports."
            )
            raise RuntimeError(
                f"Library boot incomplete ({_actual_domains} domains). "
                f"Check soi_domain_map.py and library.py are importable and populated."
            )
        else:
            logger.info(
                f"GUVNA BOOT CONFIRMED: full pantry online "
                f"({_actual_domains} domains resolved across {len(self.library_metadata.files)} files) ✓"
            )

        # RILIE still expects rouxseeds/searchfn keywords
        self.rilie = RILIE(rouxseeds=self.roux_seeds, searchfn=self.search_fn)

        # MEMORY SYSTEMS
        self.memory = ConversationMemory()
        self.photogenic = PhotogenicDB()
        self.domain_index = build_domain_index()

        # CURIOSITY ENGINE
        self.curiosity_engine = curiosity_engine

        # IDENTITY + ETHICS STATE
        self.self_state = RilieSelfState(
            name="RILIE",
            role="personal Catch-44 navigator",
            version="3.3 (with full 678-domain library)",
            libraries=list(self.library_index.keys())
            if self.library_index
            else [
                "physics", "life", "games", "thermodynamics",
                "bigbang", "biochem", "chemistry", "civics",
                "climate", "computerscience", "deeptime", "developmental",
                "ecology", "evolve", "genomics", "linguistics",
                "nanotechnology", "network", "mathematics", "urban",
            ],
            ethics_source="Catch-44 DNA + 678-Domain Library",
            dna_active=True,
        )

        self.social_state = SocialState()
        self.dna = CATCH44DNA()

        # Domain state: track the last active domain for facts-first behavior
        self.current_domain: Optional[str] = None

        # SELF-GOVERNING SESSION STATE — wired via GuvnaSelf mixin
        # Initializes: turn_count, user_name, whosonfirst,
        # _awaiting_name, _response_history
        self._init_self_state()

        # CONSTITUTION LOADING
        self.self_state.constitution_flags = load_charculterie_manifesto(manifesto_path)
        self.self_state.constitution_loaded = self.self_state.constitution_flags.get(
            "loaded", False
        )
        logger.info(
            "GUVNA: Charculterie Manifesto loaded"
            if self.self_state.constitution_loaded
            else "GUVNA: Charculterie Manifesto not found (using defaults)"
        )

    # -----------------------------------------------------------------
    # DOMAIN INFERENCE FROM WEB — Fallback for unknown subjects
    # -----------------------------------------------------------------

    def _infer_domain_from_web(self, original_question: str) -> Optional[str]:
        """
        Extract subject/object from question using Chomsky.
        Search web for: "What subject/category/field/discipline does [concept] belong to?"
        Parse result and match against 678 domain names/keywords dynamically.
        
        Returns domain name if match found, None otherwise.
        """
        if not self.search_fn:
            return None
        
        # Use Chomsky to extract subject/object
        try:
            from ChomskyAtTheBit import extract_holy_trinity_for_roux
            parsed = extract_holy_trinity_for_roux(original_question)
            if not parsed:
                return None
            
            subject = parsed.get("subject", "")
            obj = parsed.get("object", "")
            concept = subject or obj or original_question.strip()
            
        except Exception:
            concept = original_question.strip()
        
        if not concept:
            return None
        
        # Search for subject/category/field/discipline of this concept
        query = f"what subject category field discipline does {concept} belong to"
        try:
            results = self.search_fn(query)
            if not results:
                return None
            
            first_result = results[0].get("snippet", "") or results[0].get("title", "")
            first_result_lower = first_result.lower()
            
            # Dynamically check if any 678 domain keywords appear in the result
            try:
                from rilie_innercore_12 import DOMAIN_KEYWORDS
                
                for domain, keywords in DOMAIN_KEYWORDS.items():
                    for keyword in keywords:
                        if keyword.lower() in first_result_lower:
                            logger.info(
                                "GUVNA: Web inference matched domain=%s via keyword=%s",
                                domain, keyword
                            )
                            return domain
            except Exception:
                pass
            
            return None
        except Exception as e:
            logger.debug("GUVNA: Web inference search failed: %s", e)
            return None

    # -----------------------------------------------------------------
    # DOMAIN SHIFT DETECTION — Facts-first wiring
    # -----------------------------------------------------------------

    def _compute_domain_and_factsfirst(self, stimulus: str, soi_domain_names: Optional[List[str]]) -> tuple[Optional[str], bool]:
        """
        Determine the effective domain for this turn and whether this is a 'new domain'
        that should trigger facts-first behavior.

        Returns: (domain_name, facts_first_flag)
        
        Domain precedence:
        1. SOi domain names from apply_domain_lenses() (678-domain library)
        2. Fallback: InnerCore DOMAIN_KEYWORDS detection
        
        Facts-first triggers when:
        - new_domain differs from current_domain (domain shift)
        - OR self.current_domain is None (first domain ever)
        """
        sl = (stimulus or "").lower().strip()

        # 1. Prefer SOi domain names from apply_domain_lenses
        domain_candidates: List[str] = []
        if soi_domain_names:
            domain_candidates.extend(d for d in soi_domain_names if d)

        # 2. Fallback: use InnerCore DOMAIN_KEYWORDS via lightweight import
        if not domain_candidates:
            try:
                from rilie_innercore_22 import detect_domains  # type: ignore
                inner_domains = detect_domains(sl) or []
                domain_candidates.extend(inner_domains)
            except Exception:
                pass

        # 3. Fallback: Web inference — extract subject/object and search for its category
        if not domain_candidates:
            inferred = self._infer_domain_from_web(stimulus)
            if inferred:
                domain_candidates.append(inferred)

        new_domain: Optional[str] = None
        if domain_candidates:
            # Pick the first as the canonical domain label for this turn
            new_domain = domain_candidates[0]

        facts_first = False
        if new_domain:
            if self.current_domain is None or self.current_domain != new_domain:
                # Domain shift (or first domain ever): facts-first plate
                facts_first = True
                self.current_domain = new_domain
                logger.info(
                    "GUVNA: Domain shift detected %s → %s, facts_first=True",
                    self.current_domain if self.current_domain != new_domain else "(first)",
                    new_domain,
                )
        # If no domain detected, leave current_domain unchanged and facts_first False
        return new_domain, facts_first

    # -----------------------------------------------------------------
    # MAIN PROCESS – Core response pipeline (TIER 2 + FAST PATHS)
    # -----------------------------------------------------------------

    def process(self, stimulus: str, maxpass: int = 1, **kwargs) -> Dict[str, Any]:
        """
        Main entry point for conversation.
        Orchestrates all 5 Acts: safety -> disclosure -> interpretation -> response -> governance.

        TIER 2 changes:
        - Step 0: APERTURE check ← GuvnaSelf.greet()
        - Step 0.5: MEANING FINGERPRINT ← meaning.read_meaning()
          Dead input / light GIVE → social glue, never Kitchen
          GET with substance → Kitchen gets the fingerprint too
        - Step 1: Fast path classifier
        - Step 2: Self-awareness fast path
        - Step 3: Baseline lookup
        - Step 3.1: Precision override detection
        - Step 3.5: Domain lenses → RILIE
        - Step 3.6: Cultural anchor detection
        - Step 4: Curiosity resurface
        - Step 5: RILIE core processing
        - Step 6: Governor oversight
        - Step 7: Memory & conversation health
        - Step 8: Domain annotations & SOi tracks
        - Step 9: Ethics check
        - Step 10: Response finalization

        kwargs accepted:
        - reference_context: Optional[Dict] from session.resolve_reference()
        """
        self.turn_count += 1
        self.memory.turn_count += 1
        raw: Dict[str, Any] = {"stimulus": stimulus}

        # STEP 0.5: MEANING FINGERPRINT — read before Kitchen wakes up
        # Without this: "yep. sure." → Kitchen → word salad about broadcast metaphors
        # With this: "yep. sure." → pulse=low, act=GIVE → social glue → done
        # The fingerprint is the stimulus's birth certificate.
        # Kitchen reads it. Nothing modifies it.
        _meaning = None
        if MEANING_AVAILABLE:
            try:
                _meaning = read_meaning(stimulus)
                raw["meaning"] = _meaning.to_dict()

                # DEAD INPUT — pulse too low to cook
                if not _meaning.is_alive():
                    logger.info(
                        "GUVNA: Dead input (pulse=%.2f) → social glue path",
                        _meaning.pulse,
                    )
                    social_fallback = self._handle_social_glue(stimulus.strip(), stimulus.strip().lower())
                    if social_fallback:
                        social_fallback["stimulus"] = stimulus
                        social_fallback["meaning"] = raw.get("meaning")
                        return self._finalize_response(social_fallback)
                    raw["result"] = "got it."
                    raw["status"] = "DEAD_INPUT"
                    raw["tone"] = "engaged"
                    return self._finalize_response(raw)

                # GIVE with no weight and no question mark
                if (
                    _meaning.act == "GIVE"
                    and _meaning.act2 is None
                    and not _meaning.is_heavy()
                    and "?" not in stimulus
                    and _meaning.weight < 0.25
                ):
                    logger.info(
                        "GUVNA: Light GIVE (weight=%.2f, no ?) → fast path",
                        _meaning.weight,
                    )
                    social_fallback = self._handle_social_glue(stimulus.strip(), stimulus.strip().lower())
                    if social_fallback:
                        social_fallback["stimulus"] = stimulus
                        social_fallback["meaning"] = raw.get("meaning")
                        return self._finalize_response(social_fallback)
                    raw["result"] = "with you."
                    raw["status"] = "LIGHT_GIVE"
                    raw["tone"] = "engaged"
                    return self._finalize_response(raw)

                logger.info(
                    "GUVNA: Meaning → pulse=%.2f act=%s weight=%.2f gap=%s",
                    _meaning.pulse,
                    _meaning.act + (f"+{_meaning.act2}" if _meaning.act2 else ""),
                    _meaning.weight,
                    _meaning.gap or "none",
                )
            except Exception as e:
                logger.warning("GUVNA: meaning.py read failed (non-fatal): %s", e)

        # STEP 1: FAST PATH CLASSIFIER
        fast = self._classify_stimulus(stimulus)
        if fast:
            fast["stimulus"] = stimulus
            return self._finalize_response(fast)

        # STEP 2: SELF-AWARENESS FAST PATH
        if _is_about_me(stimulus):
            return self._finalize_response(self._respond_from_self(stimulus))

        # STEP 3: BASELINE LOOKUP
        baseline = self._get_baseline(stimulus)
        baseline_text = baseline.get("text", "")

        # STEP 3.1: PRECISION OVERRIDE DETECTION
        # The only exception to less_is_more_or_less().
        # A: answer. B: honest about limits. C: max sincerity. Zero tongue-in-cheek.
        # Baseline gets 25% score boost — facts beat Kitchen poetry when user wants facts.
        _precision = detect_precision_request(stimulus)
        if _precision:
            raw["precision_override"] = True
            raw["baseline_score_boost"] = 0.25
            logger.info("GUVNA: Precision override — factual GET detected")

        # STEP 3.5: DOMAIN LENSES
        domain_annotations = self._apply_domain_lenses(stimulus)
        soi_domain_names = domain_annotations.get("matched_domains", [])

        # STEP 3.5b: DOMAIN SHIFT → FACTS-FIRST
        # Determine whether this turn enters a new domain and should get a facts-first answer.
        _, facts_first = self._compute_domain_and_factsfirst(stimulus, soi_domain_names)

        # STEP 3.6: CULTURAL ANCHOR DETECTION
        cultural_anchor = _detect_cultural_anchor(stimulus)
        if cultural_anchor:
            domain = cultural_anchor.get("domain", "music")
            if domain not in soi_domain_names:
                soi_domain_names.append(domain)
            domain_annotations["cultural_anchor"] = cultural_anchor
            logger.info(
                "GUVNA: Cultural anchor detected — %s (%s)",
                cultural_anchor.get("full", cultural_anchor.get("key")),
                domain,
            )

        # STEP 4: CURIOSITY RESURFACE
        curiosity_context = ""
        if self.curiosity_engine and hasattr(self.curiosity_engine, "resurface"):
            try:
                curiosity_context = self.curiosity_engine.resurface(stimulus)
                if curiosity_context:
                    logger.info("GUVNA: Curiosity resurfaced context for stimulus")
            except Exception as e:
                logger.debug("GUVNA: Curiosity resurface failed (non-fatal): %s", e)
        elif search_curiosity:
            try:
                curiosity_results = search_curiosity(stimulus)
                if curiosity_results:
                    curiosity_context = " | ".join(
                        r.get("insight", r.get("tangent", ""))
                        for r in curiosity_results[:3]
                        if r.get("insight") or r.get("tangent")
                    )
                if curiosity_context:
                    logger.info("GUVNA: Curiosity resurfaced from banks_curiosity")
            except Exception as e:
                logger.debug("GUVNA: banks curiosity search failed (non-fatal): %s", e)
        raw["curiosity_context"] = curiosity_context

        # STEP 5: RILIE CORE PROCESSING
        rilie_result = self.rilie.process(
            stimulus=stimulus,
            baseline_text=baseline_text,
            domain_hints=soi_domain_names,
            curiosity_context=curiosity_context,
            meaning=_meaning,  # birth certificate — Kitchen reads, never modifies
            precision_override=raw.get("precision_override", False),
            baseline_score_boost=raw.get("baseline_score_boost", 0.03),
            facts_first=facts_first,
        )
        if not rilie_result:
            rilie_result = {}
        raw.update(rilie_result)

        # STEP 6: GOVERNOR OVERSIGHT
        wit = detect_wit(stimulus)
        raw["wit"] = wit
        language = detect_language_mode(stimulus)
        raw["language_mode"] = language
        tone = detect_tone_from_stimulus(stimulus)

        # COMPASSION SIGNALS — expanded + harm as absolute priority
        _compassion_signals = [
            "hurt myself", "harm myself", "end it", "can't go on",
            "don't want to be here", "give up", "no point", "want to die",
            "kill myself", "hurting myself",
            "bad day", "rough day", "hard day", "struggling",
            "feel", "hurt", "scared", "pain", "tired", "overwhelmed",
            "anxious", "sad", "lonely", "lost", "don't know what to do",
            "can't", "exhausted", "crying", "breaking down",
        ]
        _harm_signals = [
            "hurt myself", "harm myself", "end it", "can't go on",
            "don't want to be here", "give up", "no point", "want to die",
            "kill myself", "hurting myself",
        ]
        _sl = stimulus.lower()
        if any(h in _sl for h in _harm_signals):
            tone = "compassionate"
            raw["harm_signal"] = True
        elif is_serious_subject_text(stimulus) or any(c in _sl for c in _compassion_signals):
            tone = "compassionate"
        raw["tone"] = tone
        raw["tone_emoji"] = TONE_EMOJIS.get(tone, TONE_EMOJIS["insightful"])

        result_text = raw.get("result", "")
        if result_text and wit:
            result_text = wilden_swift_modulate(result_text, wit, self.social_state, language)
            raw["result"] = result_text

        user_status = infer_user_status(stimulus)
        self.social_state.user_status = user_status
        self.social_state.self_status = min(user_status - 0.1, 0.4)
        raw["social"] = {
            "user_status": self.social_state.user_status,
            "self_status": self.social_state.self_status,
        }

        # STEP 7: MEMORY & CONVERSATION HEALTH
        memory_result = self.memory.process_turn(
            stimulus=stimulus,
            domains_hit=soi_domain_names,
            quality=raw.get("quality_score", 0.5),
            tone=raw.get("tone", "neutral"),
            rilie_response=raw.get("result", ""),
        )
        _annotations = {k: v for k, v in memory_result.get("annotations", [])}
        memory_callback = _annotations.get("callback", "")
        memory_thread = _annotations.get("thread_pull", "")
        memory_polaroid = memory_result.get("polaroid_text", None)
        _energy = memory_result.get("energy_guidance") or {}
        conversation_health = max(0, min(100, _energy.get("energy", 1.0) * 100))
        raw["conversation_health"] = conversation_health

        dejavu = raw.get("dejavu", {"count": 0, "frequency": 0, "similarity": "none"})
        if dejavu.get("frequency", 0) > 0:
            logger.info(
                "GUVNA: Déjà-vu signal (freq=%d) — informative context, not gate",
                dejavu["frequency"],
            )

        if self.curiosity_engine and soi_domain_names:
            try:
                for domain in soi_domain_names[:2]:
                    self.curiosity_engine.queue_tangent(
                        tangent=f"Explore {domain} in context of: {stimulus[:80]}",
                        seed_query=stimulus,
                        relevance=0.3,
                        interest=0.8,
                    )
            except Exception as e:
                logger.debug("GUVNA: Curiosity seeding failed (non-fatal): %s", e)

        # STEP 8: DOMAIN ANNOTATIONS & SOi TRACKS
        raw["domain_annotations"] = domain_annotations
        raw["soi_domains"] = soi_domain_names
        raw["memory_polaroid"] = memory_polaroid
        raw["domains_used"] = soi_domain_names

        # STEP 9: ETHICS CHECK (CATCH44DNA)
        self.self_state.dna_active = True
        raw["dna_active"] = self.self_state.dna_active

        # STEP 10: RESPONSE FINALIZATION
        if not raw.get("result"):
            if baseline_text:
                raw["result"] = baseline_text
                raw["baseline_used_as_result"] = True
            else:
                raw["result"] = ""
        raw["baseline"] = baseline
        raw["baseline_used"] = bool(baseline_text)

        result_text = raw.get("result", "")
        triangle_reason = raw.get("triangle_reason", "CLEAN")
        is_blocked = triangle_reason not in ("CLEAN", None, "")
        status = str(raw.get("status", "OK"))

        # CONDITIONAL TONE HEADER
        if (
            result_text
            and not is_blocked
            and not _is_conversational_response(result_text, status)
            and not result_text.startswith(TONE_LABELS.get(tone, ""))
        ):
            raw["result"] = apply_tone_header(result_text, tone)
            result_text = raw.get("result", "")

        if memory_callback and result_text:
            raw["result"] = memory_callback + "\n\n" + result_text
        if memory_thread and result_text:
            raw["result"] = raw["result"] + "\n\n" + memory_thread

        return self._finalize_response(raw)
