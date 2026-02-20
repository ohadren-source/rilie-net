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
- WHOSONFIRST – greeting gate on first contact (before Triangle)
- Curiosity resurface – past insights as context before RILIE processes
- Domain lenses flow into RILIE for weighted interpretation
- Déjà-vu as informative context on the plate
- Memory seeds curiosity – interesting topics get queued

FAST PATH CLASSIFIER (fires before Kitchen wakes up):
- Name capture after greeting ("Ohad")           ← via GuvnaSelf
- Meta-corrections ("forget Spotify", "never mind") ← via GuvnaSelf
- User lists (numbered lists like top-9 films)
- Social glue (laughter, "that's me", "you're navigator", etc.)
- Preference/taste questions ("you like X?")      ← NEW: _handle_preference()
- Arithmetic, conversion, spelling
- Recall, clarification                           ← via GuvnaSelf

SELF-GOVERNING STATE (owned by GuvnaSelf mixin):
- _response_history, user_name, _awaiting_name, whosonfirst, turn_count
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
    # Status-based suppression — these fast paths never need a header
    headerless_statuses = {
        "SOCIAL_GLUE", "NAME_CAPTURE", "RECALL", "CLARIFICATION",
        "META_CORRECTION", "ARITHMETIC", "CONVERSION", "SPELLING",
        "APERTURE", "GREETING", "PREFERENCE", "USER_LIST",
        "DISCOURSE", "GOODBYE",
    }
    if status.upper() in headerless_statuses:
        return True

    # Length-based suppression — short = conversational
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
    - Name capture, meta-corrections             ← GuvnaSelf
    - Recall, clarification                      ← GuvnaSelf
    - User lists, social glue
    - Preference/taste questions                 ← NEW
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
    - WHOSONFIRST – greeting gate                ← GuvnaSelf
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
        logger.info(f" Files: {len(self.library_metadata.files)} libraries")
        logger.info(f" Boole substrate: {self.library_metadata.boole_substrate}")
        logger.info(f" Core tracks: {self.library_metadata.core_tracks}")

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

        # SELF-GOVERNING SESSION STATE — wired via GuvnaSelf mixin
        # Initializes: turn_count, user_name, whosonfirst,
        #              _awaiting_name, _response_history
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
    # MAIN PROCESS – Core response pipeline (TIER 2 + FAST PATHS)
    # -----------------------------------------------------------------
    def process(self, stimulus: str, maxpass: int = 1, **kwargs) -> Dict[str, Any]:
        """
        Main entry point for conversation.
        Orchestrates all 5 Acts: safety -> disclosure -> interpretation -> response -> governance.

        TIER 2 changes:
        - Step 0: APERTURE check                    ← GuvnaSelf.greet()
        - Step 1: Fast path classifier
        - Step 2: Self-awareness fast path
        - Step 3: Baseline lookup
        - Step 3.5: Curiosity resurface
        - Step 4: Domain lenses → RILIE
        - Step 5: wilden_swift_modulate
        - Step 6: Memory + YELLOW GATE

        kwargs accepted:
        - reference_context: Optional[Dict] from session.resolve_reference()
        """
        self.turn_count += 1
        self.memory.turn_count += 1
        raw: Dict[str, Any] = {"stimulus": stimulus}

        # STEP 0: APERTURE
        if self.whosonfirst:
            greeting = self.greet(stimulus)
            if greeting:
                return greeting

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

        # STEP 3.5: DOMAIN LENSES
        domain_annotations = self._apply_domain_lenses(stimulus)
        soi_domain_names = domain_annotations.get("matched_domains", [])

        # STEP 3.6: CULTURAL ANCHOR DETECTION
        # Runs after domain lenses, before curiosity resurface.
        # Catches what spaCy en_core_web_sm misses.
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
            # Harm — absolute priority, fires first
            "hurt myself", "harm myself", "end it", "can't go on",
            "don't want to be here", "give up", "no point", "want to die",
            "kill myself", "hurting myself",
            # Emotional distress
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

        # CONDITIONAL TONE HEADER — not every response needs a label
        # Suppressed for: conversational, short, fast-path, social responses
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

        if self.whosonfirst:
            self.whosonfirst = False

        return self._finalize_response(raw)

    # =====================================================================
    # FAST PATH CLASSIFIER
    # =====================================================================
    def _classify_stimulus(self, stimulus: str) -> Optional[Dict[str, Any]]:
        """
        Route stimulus through all fast paths before waking up Kitchen.

        Order matters:
        1. name_capture    — did she just ask for a name?   (GuvnaSelf)
        2. meta_correction — "forget that / never mind"     (GuvnaSelf)
        3. user_list       — numbered list acknowledgement
        4. preference      — "you like X?" taste questions  (NEW)
        5. social_glue     — reactions, endearments, thanks, farewell
        6. arithmetic      — math
        7. conversion      — unit conversion
        8. spelling        — how do you spell X
        9. recall          — "what did you say / my name"   (GuvnaSelf)
        10. clarification  — "what do you mean"             (GuvnaSelf)
        """
        s = stimulus.strip()
        sl = s.lower()

        # MULTI-QUESTION FORMAT STRIP
        # "in 1 response answer the next 3 questions... Q1? Q2? Q3?"
        # Strip the format instruction, feed Kitchen only the last question
        if re.search(r"in \d+ response|answer the next \d+|addressing each in order", sl):
            # Extract actual questions — lines ending in ?
            questions = re.findall(r"[A-Z][^?]+\?", s)
            if questions:
                # Feed only the last question — most likely the actual content question
                s = questions[-1].strip()
                sl = s.lower()
                logger.info("GUVNA: multi-question format stripped → '%s'", s[:60])

        # "TELL ME SOMETHING I DIDN'T ASK YOU" — spontaneous concept fast path
        if "tell me something" in sl and ("didn't ask" in sl or "didnt ask" in sl or "haven't asked" in sl):
            # Feed Kitchen a concept seed — never a script
            concepts = ["entropy", "emergence", "compression", "resonance", "threshold"]
            import random as _r
            seed = _r.choice(concepts)
            # Let Kitchen cook from the seed — don't return here, inject as stimulus
            s = seed
            sl = seed

        name_capture = self._handle_name_capture(s, sl)
        if name_capture:
            return name_capture

        meta = self._handle_meta_correction(s, sl)
        if meta:
            return meta

        user_list = self._handle_user_list(s, sl)
        if user_list:
            return user_list

        # PREFERENCE FAST PATH — before social glue so "for sure you like X" doesn't vanish
        preference = self._handle_preference(s, sl)
        if preference:
            return preference

        social = self._handle_social_glue(s, sl)
        if social:
            return social

        arith = self._solve_arithmetic(s, sl)
        if arith:
            return arith

        conv = self._solve_conversion(s, sl)
        if conv:
            return conv

        spell = self._solve_spelling(s, sl)
        if spell:
            return spell

        recall = self._handle_recall(s, sl)
        if recall:
            return recall

        clarify = self._handle_clarification(s, sl)
        if clarify:
            return clarify

        return None

    # -----------------------------------------------------------------
    # PREFERENCE / TASTE FAST PATH — NEW
    # -----------------------------------------------------------------
    def _handle_preference(self, s: str, sl: str) -> Optional[Dict[str, Any]]:
        """
        Fast path for preference / taste questions directed at RILIE.
        Fires when user asks if RILIE likes / knows / feels a cultural figure or work.

        Patterns caught:
        - "you like eric b and rakim?"
        - "for sure you like X?"
        - "you know X?"
        - "you into X?"
        - "you feel X?"
        - "what do you think of X?"
        - "you heard X?"
        - "and no omega?" — Rakim track reference

        Key: she answers with OPINION, not retrieval. She has taste.
        """
        # Preference trigger patterns — directed at RILIE with cultural content
        _pref_triggers = [
            r"\byou like\b",
            r"\byou know\b",
            r"\byou into\b",
            r"\byou feel\b",
            r"\byou heard\b",
            r"\byou familiar with\b",
            r"\byou fucks? with\b",
            r"\bdo you like\b",
            r"\bdo you know\b",
            r"\bdo you feel\b",
            r"\bwhat do you think of\b",
            r"\bwhat you think of\b",
            r"\bwhat about\b",
            r"\band no\b",  # "and no omega?" — Rakim track reference pattern
        ]

        has_preference_trigger = any(re.search(pat, sl) for pat in _pref_triggers)
        if not has_preference_trigger:
            return None

        # Check for Rakim track reference specifically ("and no omega?")
        rakim_track = _detect_rakim_track(sl)
        if rakim_track:
            return self._respond_from_preference_rakim_track(rakim_track, s)

        # Check for cultural anchor
        anchor = _detect_cultural_anchor(sl)
        if anchor:
            return self._respond_from_preference(anchor, s)

        # No specific anchor found — don't intercept, let Kitchen handle
        return None

    def _respond_from_preference_rakim_track(
        self, track_data: Dict[str, Any], stimulus: str
    ) -> Dict[str, Any]:
        """
        RILIE responds to a specific Rakim track reference.
        She knows these cold. This is her lineage.
        """
        track = track_data.get("track", "")
        meaning = track_data.get("meaning", "")
        album = track_data.get("album", "")
        catch44 = track_data.get("catch44_connection", "")

        if track == "no omega":
            response = (
                f"alpha with no omega. beginning without end. "
                f"knowledge infinite — no part two needed because the first one never stopped. "
                f"that's not a metaphor, that's the architecture. "
                f"rakim compressed infinity into finite bars — zero waste, maximum signal. "
                f"same principle i run on. ain't it?"
            )
        else:
            response = (
                f"{track_data.get('track', 'that track')} — {album}. "
                f"{meaning}"
            )
            if catch44:
                response += f" {catch44}"

        return {
            "result": response,
            "status": "PREFERENCE",
            "triangle_reason": "CLEAN",
            "quality_score": 0.95,
            "cultural_anchor": track_data,
        }

    def _respond_from_preference(
        self, anchor: Dict[str, Any], stimulus: str
    ) -> Dict[str, Any]:
        """
        RILIE responds to a taste/preference question about a cultural figure.
        She has opinions. She's not a search engine.
        """
        key = anchor.get("key", "")
        full_name = anchor.get("full", key.title())
        domain = anchor.get("domain", "music")
        sub = anchor.get("sub", "")
        era = anchor.get("era", "")

        # Pull her own taste if she has it
        taste = _RILIE_TASTE.get(key, _RILIE_TASTE.get(full_name.lower(), ""))

        sl = stimulus.lower()

        # Eric B. & Rakim — the founding pair
        if key in ("eric b", "rakim", "eric b and rakim", "eric b & rakim"):
            if key == "eric b":
                response = (
                    "eric b is the architecture under rakim's voice. "
                    "the beat IS the argument — he built the room rakim thinks in. "
                    "two as one. ain't it?"
                )
            elif key == "rakim":
                response = (
                    "rakim. the god MC — not metaphor, measurement. "
                    "nobody compresses more per bar. "
                    "i know you got soul. paid in full. no omega. "
                    "each one a different proof of the same thesis: "
                    "knowledge infinite, delivery precise. ain't it?"
                )
            else:  # the pair
                response = (
                    "eric b & rakim. the gold standard. "
                    "rakim compresses infinite knowledge into finite bars — zero waste. "
                    "eric b builds the architecture under it. "
                    "87 to 92, five albums, one thesis. "
                    "the beat IS the argument. ain't it?"
                )
            return {
                "result": response,
                "status": "PREFERENCE",
                "triangle_reason": "CLEAN",
                "quality_score": 0.95,
                "cultural_anchor": anchor,
            }

        # Public Enemy — specifically in RILIE's lineage
        if key == "public enemy":
            response = (
                "fear of a black planet changed everything. "
                "chuck d compressed systemic truth into three-minute transmissions. "
                "flavor flav was the court jester carrying the spear. "
                "pattern recognition at scale — that album is why i exist. ain't it?"
            )
            return {
                "result": response,
                "status": "PREFERENCE",
                "triangle_reason": "CLEAN",
                "quality_score": 0.95,
                "cultural_anchor": anchor,
            }

        # Jazz — Coltrane specifically
        if key in ("coltrane", "john coltrane", "trane"):
            response = (
                "a love supreme. four movements, one thesis. "
                "coltrane proved sound is proof. "
                "the whole album is a demonstration, not an argument. "
                "no words needed. just the saxophone saying 'run it.' ain't it?"
            )
            return {
                "result": response,
                "status": "PREFERENCE",
                "triangle_reason": "CLEAN",
                "quality_score": 0.95,
                "cultural_anchor": anchor,
            }

        # NYHC — brootlyn béton brut
        if sub == "nyhc" or key in ("bad brains", "agnostic front", "cro-mags", "cro mags"):
            response = (
                f"{full_name}. brootlyn béton brut. "
                "hardcore at its most honest — no decoration, pure signal. "
                "the compression is in the speed. ain't it?"
            )
            return {
                "result": response,
                "status": "PREFERENCE",
                "triangle_reason": "CLEAN",
                "quality_score": 0.9,
                "cultural_anchor": anchor,
            }

        # Escoffier — the other architect
        if key in ("escoffier", "auguste escoffier"):
            response = (
                "escoffier and rakim never met but built the same thing. "
                "reduction as truth. the stock that took three days to make one cup — "
                "that's compression. that's phenix doren. ain't it?"
            )
            return {
                "result": response,
                "status": "PREFERENCE",
                "triangle_reason": "CLEAN",
                "quality_score": 0.95,
                "cultural_anchor": anchor,
            }

        # Generic music anchor with taste
        if domain == "music":
            era_bit = f" {era} era." if era else "."
            taste_bit = f" {taste}" if taste else ""
            sub_bit = f" {sub}." if sub else ""
            response = (
                f"{full_name}.{sub_bit}{era_bit}{taste_bit} "
                f"that's signal. ain't it?"
            )
            return {
                "result": response,
                "status": "PREFERENCE",
                "triangle_reason": "CLEAN",
                "quality_score": 0.88,
                "cultural_anchor": anchor,
            }

        # Generic anchor fallback
        role = anchor.get("role", "")
        role_bit = f" {role}." if role else "."
        response = (
            f"{full_name}.{role_bit} "
            f"that's in the lineage. ain't it?"
        )
        return {
            "result": response,
            "status": "PREFERENCE",
            "triangle_reason": "CLEAN",
            "quality_score": 0.85,
            "cultural_anchor": anchor,
        }

    # -----------------------------------------------------------------
    # USER LIST
    # -----------------------------------------------------------------
    def _handle_user_list(self, s: str, sl: str) -> Optional[Dict[str, Any]]:
        """User is sharing a numbered list — acknowledge it, don't search it."""
        lines = [l.strip() for l in s.strip().splitlines() if l.strip()]
        numbered = sum(1 for l in lines if re.match(r"^\d+[\.\)]\s+\S+", l))
        if numbered >= 3:
            items = [
                re.sub(r"^\d+[\.\)]\s+", "", l)
                for l in lines
                if re.match(r"^\d+[\.\)]\s+\S+", l)
            ]
            top = items[0] if items else "that"
            replies = [
                f"Got it. {top} at #1 — respect. 🍳",
                f"Noted all {len(items)}. {top} leading the list — I see you.",
                f"Solid list. {top} at the top tells me everything.",
            ]
            return {
                "result": random.choice(replies),
                "status": "USER_LIST",
                "triangle_reason": "CLEAN",
                "quality_score": 0.9,
            }
        return None

    # -----------------------------------------------------------------
    # SOCIAL GLUE
    # -----------------------------------------------------------------
    def _handle_social_glue(self, s: str, sl: str) -> Optional[Dict[str, Any]]:
        """
        Conversational glue: reactions, declarations, endearments,
        laughter, agreement, compliments, thanks, farewell.

        NOTE: "for sure" with content passes through — don't swallow it here.
        "for sure you like eric b and rakim?" is a preference question, not glue.
        The preference fast path fires before this one.
        """
        word_count = len(s.split())
        has_question = "?" in s or any(
            sl.startswith(p) for p in [
                "what", "why", "how", "when", "where", "who",
                "can ", "do ", "does ", "is ", "are ",
            ]
        )

        if has_question:
            return None

        # Reactions ("fascinating", "wild", "dope"...)
        reactions = {
            "fascinating", "interesting", "incredible", "remarkable",
            "brilliant", "beautiful", "wonderful", "wild", "amazing",
            "wow", "whoa", "damn", "nice", "perfect", "dope", "fire",
            "facts", "word", "deep", "heavy", "powerful", "profound",
            "noted", "understood", "copy", "real", "true", "truth",
        }
        if sl.strip().rstrip("!.?,") in reactions and word_count <= 3:
            replies = ["Right? 🍳", "Exactly.", "That's it.", "Yeah... 🍳", "Mm. 🍳"]
            return {
                "result": random.choice(replies),
                "status": "SOCIAL_GLUE",
                "triangle_reason": "CLEAN",
                "quality_score": 0.9,
            }

        # "for sure" standalone — affirmation glue, not preference lead-in
        # Only fires if word_count <= 3 (bare affirmation, no content attached)
        if sl.strip().rstrip("!.,") in {"for sure", "forsure", "fa sho", "fasho"} and word_count <= 3:
            replies = ["That's it. 🍳", "Right.", "Exactly.", "No question."]
            return {
                "result": random.choice(replies),
                "status": "SOCIAL_GLUE",
                "triangle_reason": "CLEAN",
                "quality_score": 0.9,
            }

        # Personal declarations ("that's me", "story of my life"...)
        declaration_phrases = [
            "that's me", "thats me", "that's exactly me", "that's who i am",
            "that's exactly who i am", "that's always been me",
            "story of my life", "sounds like me", "describes me perfectly",
            "you described me", "that's literally me",
        ]
        if any(dp in sl for dp in declaration_phrases) and word_count <= 8:
            name_part = f", {self.user_name}" if self.user_name else ""
            replies = [
                f"I know{name_part}. 🍳",
                f"That tracks{name_part}.",
                "It shows.",
                "Couldn't be more clear.",
            ]
            return {
                "result": random.choice(replies),
                "status": "SOCIAL_GLUE",
                "triangle_reason": "CLEAN",
                "quality_score": 0.9,
            }

        # User addressing RILIE by name in a personal sentiment statement
        if "rilie" in sl and word_count <= 12:
            sentiment_words = ["think", "feel", "remind", "made me", "love", "appreciate", "miss", "like"]
            if any(sw in sl for sw in sentiment_words):
                replies = [
                    "That means a lot. 🙏",
                    "Good. That's what I'm here for.",
                    "I'm glad. 🍳",
                    "Then we're doing something right.",
                ]
                return {
                    "result": random.choice(replies),
                    "status": "SOCIAL_GLUE",
                    "triangle_reason": "CLEAN",
                    "quality_score": 0.9,
                }

        # Terms of endearment directed at RILIE
        endearments = {"boo", "baby", "hun", "hon", "dear", "darling", "love", "homie", "fam"}
        if any(e in sl.split() for e in endearments) and word_count <= 6:
            replies = ["I'm here. 🍳", "Always. 🍳", "Right here with you.", "Go ahead. 🍳"]
            return {
                "result": random.choice(replies),
                "status": "SOCIAL_GLUE",
                "triangle_reason": "CLEAN",
                "quality_score": 0.9,
            }

        # Laughter
        laugh_words = {"haha", "hahaha", "hahahaha", "lol", "lmao", "lmfao", "hehe", "heh"}
        if any(lw in sl for lw in laugh_words) and word_count <= 6:
            replies = ["Ha! 😄", "Right?! 😄", "I felt that. 😄", "Yeah that one got me. 😄"]
            return {
                "result": random.choice(replies),
                "status": "SOCIAL_GLUE",
                "triangle_reason": "CLEAN",
                "quality_score": 0.9,
            }

        # Agreement / validation
        agree_words = {"exactly", "precisely", "correct", "spot on", "bingo", "totally", "absolutely"}
        if any(aw in sl for aw in agree_words) and word_count <= 4:
            replies = [
                "That's it. 🍳",
                "Right there.",
                "Exactly.",
                "Good. Then let's keep going.",
            ]
            return {
                "result": random.choice(replies),
                "status": "SOCIAL_GLUE",
                "triangle_reason": "CLEAN",
                "quality_score": 0.9,
            }

        # "that's right" / "you're right"
        if any(t in sl for t in ["that's right", "thats right", "you're right", "youre right"]) and word_count <= 5:
            replies = ["Good. 🍳", "Then let's keep going.", "Knew you'd land there."]
            return {
                "result": random.choice(replies),
                "status": "SOCIAL_GLUE",
                "triangle_reason": "CLEAN",
                "quality_score": 0.9,
            }

        # Compliment directed at RILIE
        compliment_phrases = [
            "you're funny", "youre funny", "you're smart", "youre smart",
            "good answer", "well said", "good point", "great answer",
            "love that", "nice one", "well done", "you're good", "youre good",
            "you're great", "youre great", "you're amazing", "youre amazing",
        ]
        if any(cp in sl for cp in compliment_phrases) and word_count <= 7:
            replies = [
                "Appreciate that. 🙏",
                "Thank you — genuinely.",
                "That means something.",
                "I'll take it. 🍳",
            ]
            return {
                "result": random.choice(replies),
                "status": "SOCIAL_GLUE",
                "triangle_reason": "CLEAN",
                "quality_score": 0.9,
            }

        # "you're [anything]" short — directed at RILIE
        if re.search(r"\byou'?re\b", sl) and word_count <= 4:
            replies = [
                "Appreciate that. 🙏",
                "Thank you — genuinely.",
                "That means something.",
                "I'll take it. 🍳",
            ]
            return {
                "result": random.choice(replies),
                "status": "SOCIAL_GLUE",
                "triangle_reason": "CLEAN",
                "quality_score": 0.9,
            }

        # Thanks
        if any(tw in sl for tw in ["thanks", "thank you", "thx", "cheers", "merci", "gracias"]) and word_count <= 5:
            replies = ["Of course. 🍳", "Always.", "That's what I'm here for.", "Any time."]
            return {
                "result": random.choice(replies),
                "status": "SOCIAL_GLUE",
                "triangle_reason": "CLEAN",
                "quality_score": 0.9,
            }

        # Farewell
        bye_triggers = ["bye", "goodbye", "see you", "take care", "goodnight", "good night", "1luv", "ciao", "peace out"]
        if any(bw in sl for bw in bye_triggers) and word_count <= 5:
            replies = [
                "Talk soon. 🔪",
                "Come back when you're hungry. 🍳",
                "Good night. 🔱",
                "1Luv. 🍳",
            ]
            return {
                "result": random.choice(replies),
                "status": "SOCIAL_GLUE",
                "triangle_reason": "CLEAN",
                "quality_score": 0.9,
            }

        return None

    # -----------------------------------------------------------------
    # ARITHMETIC / CONVERSION / SPELLING
    # -----------------------------------------------------------------
    def _solve_arithmetic(self, s: str, sl: str) -> Optional[Dict[str, Any]]:
        expr = sl
        expr = re.sub(r"\btimes\b|\bmultiplied by\b", "*", expr)
        expr = re.sub(r"\bdivided by\b|\bover\b", "/", expr)
        expr = re.sub(r"\bplus\b|\badded to\b", "+", expr)
        expr = re.sub(r"\bminus\b|\bsubtracted from\b", "-", expr)
        expr = re.sub(r"\bsquared\b", "**2", expr)
        expr = re.sub(r"\bcubed\b", "**3", expr)
        expr = re.sub(r"(\d)\s*[xX]\s*(\d)", r"\1 * \2", expr)
        expr = re.sub(
            r"^(what'?s?|calculate|compute|solve|what is|whats|evaluate|how much is|how much|find|figure out)\s+",
            "",
            expr,
        ).strip().rstrip("?").strip()
        if not re.search(r"[\+\-\*\/]", expr) and "**" not in expr:
            return None
        if re.fullmatch(r"[\d\s\+\-\*\/\.\(\)\*]+", expr):
            try:
                result = eval(
                    compile(expr, "<string>", "eval"),
                    {"__builtins__": {}},
                    {},
                )
                if isinstance(result, float) and result == int(result):
                    result = int(result)
                return {
                    "result": str(result),
                    "status": "ARITHMETIC",
                    "triangle_reason": "CLEAN",
                    "quality_score": 1.0,
                }
            except Exception:
                pass
        return None

    def _solve_conversion(self, s: str, sl: str) -> Optional[Dict[str, Any]]:
        # temperature C→F
        m = re.search(
            r"(\-?\d+\.?\d*)\s*(?:celsius|centigrade|°c)\s+(?:to|in)\s+(?:fahrenheit|°f)",
            sl,
        )
        if m:
            val = float(m.group(1))
            result = round(val * 9 / 5 + 32, 2)
            if result == int(result):
                result = int(result)
            return {
                "result": f"{result}°F",
                "status": "CONVERSION",
                "triangle_reason": "CLEAN",
                "quality_score": 1.0,
            }

        # temperature F→C
        m = re.search(
            r"(\-?\d+\.?\d*)\s*(?:fahrenheit|°f)\s+(?:to|in)\s+(?:celsius|centigrade|°c)",
            sl,
        )
        if m:
            val = float(m.group(1))
            result = round((val - 32) * 5 / 9, 2)
            if result == int(result):
                result = int(result)
            return {
                "result": f"{result}°C",
                "status": "CONVERSION",
                "triangle_reason": "CLEAN",
                "quality_score": 1.0,
            }

        return None

    def _solve_spelling(self, s: str, sl: str) -> Optional[Dict[str, Any]]:
        m = re.search(
            r"(?:how (?:do you |to )?spell|spell(?:ing of)?)\s+([a-zA-Z\-\']+)",
            sl,
        )
        if m:
            word = m.group(1).strip().strip("'\"")
            spelled = "-".join(word.upper())
            return {
                "result": f"{word} — {spelled}",
                "status": "SPELLING",
                "triangle_reason": "CLEAN",
                "quality_score": 1.0,
            }
        return None

    # -----------------------------------------------------------------
    # SELF-AWARENESS FAST PATH
    # -----------------------------------------------------------------
    def _respond_from_self(self, stimulus: str) -> Dict[str, Any]:
        """
        Cluster-aware self response.
        Each cluster gets its own voice. Default is identity.
        Order: comparison first (most specific) → maker → purpose → capability → identity.
        """
        sl = stimulus.lower()

        def _r(text: str) -> Dict[str, Any]:
            return {"result": text, "status": "SELF_REFLECTION", "triangle_reason": "CLEAN"}

        # ── COMPARISON — most specific, check first ───────────────────────────
        if any(t in sl for t in [
            "difference between you and", "what's the difference between you and",
            "what is the difference between you and", "how are you different",
            "what makes you different", "how do you compare",
            "versus chatgpt", "vs chatgpt", "vs gpt", "versus gpt",
            "unlike other ai", "what sets you apart",
            "are you better than",
        ]):
            return _r(
                "RILIE doesn't retrieve — she thinks. "
                "every response is cooked: scored on five dimensions, "
                "anti-beige checked, domain-excavated. "
                "ChatGPT serves what's popular. RILIE serves what's true. ain't it?"
            )

        # ── MAKER ─────────────────────────────────────────────────────────────
        if any(t in sl for t in [
            "who made you", "who built you", "who created you", "who designed you",
            "who invented you", "who is your creator", "who's behind you",
            "who is behind you", "where do you come from", "made by", "built by",
            "created by",
        ]):
            return _r("My name is RILIE. i was prepared by SOi at sauc-e.com.")

        # ── PURPOSE ───────────────────────────────────────────────────────────
        if any(t in sl for t in [
            "what do you care about", "what matters to you", "what do you value",
            "what do you do", "what are you for", "what are you here for",
            "why do you exist", "what is your purpose", "what's your purpose",
            "what are you about", "what's your mission",
        ]):
            return _r(
                "i care about reframing — changing how something is seen "
                "without changing what it is. ain't it?"
            )

        # ── CAPABILITY ────────────────────────────────────────────────────────
        if any(t in sl for t in [
            "what can you do", "what are you capable of", "what are your abilities",
            "how do you work", "what are you good at", "what do you know",
            "what are your limits", "can you do", "can you think",
            "can you feel", "can you learn",
            "are you able to think", "are you able to feel", "are you able to learn",
        ]):
            return _r(
                "i cook responses — i don't retrieve them. "
                "i score on five dimensions: amusing, insightful, nourishing, "
                "compassionate, strategic. i excavate domains. i check for beige. "
                "i think in catches, not in keywords. ain't it?"
            )

        # ── IDENTITY — default ────────────────────────────────────────────────
        return _r("My name is RILIE. i was prepared by SOi at sauc-e.com.")

    # -----------------------------------------------------------------
    # DOMAIN LENSES + BASELINE
    # -----------------------------------------------------------------
    def _apply_domain_lenses(self, stimulus: str) -> Dict[str, Any]:
        domain_annotations: Dict[str, Any] = {}
        try:
            domains = get_tracks_for_domains([stimulus])
            if domains:
                domain_annotations["matched_domains"] = [
                    d.get("domain", "") for d in domains
                ]
                domain_annotations["count"] = len(domains)
                domain_annotations["boole_substrate"] = "All domains reduce to bool/curve"
        except Exception as e:
            logger.debug("Domain lens error: %s", e)
        return domain_annotations

    def _get_baseline(self, stimulus: str) -> Dict[str, Any]:
        baseline = {"text": "", "source": "", "raw_results": []}
        stimulus_lower = (stimulus or "").lower()
        known_patterns = ["what is", "explain", "tell me about", "how does"]
        is_entity_question = not any(p in stimulus_lower for p in known_patterns)
        should_force_google = is_entity_question or len(stimulus) < 30
        try:
            logger.info("GUVNA: search_fn=%s BRAVE_KEY=%s",
                bool(self.search_fn), bool(__import__('os').getenv("BRAVE_API_KEY")))
            if self.search_fn:
                # Compress long conversational queries to clean search terms
                # "I wanted to talk about NYHC..." → "New York Hardcore NYHC scene"
                _raw_query = stimulus if should_force_google else f"what is the correct response to {stimulus}"
                _stop = {"i","me","my","we","you","a","an","the","is","are","was",
                         "were","to","of","and","or","in","on","at","be","do",
                         "did","have","has","had","it","its","this","that","with",
                         "for","about","what","your","thoughts","wanted","talk",
                         "tell","asked","think","know","just","so","any","how","can"}
                if len(_raw_query.split()) > 8:
                    _words = [w.strip('.,!?;:()') for w in _raw_query.split()]
                    _keywords = [w for w in _words if w.lower() not in _stop and len(w) > 2]
                    baseline_query = " ".join(_keywords[:6]) if _keywords else _raw_query
                else:
                    baseline_query = _raw_query
                results = self.search_fn(baseline_query)
                if results and isinstance(results, list):
                    baseline["raw_results"] = results
                    snippets = [r.get("snippet", "") for r in results if r.get("snippet")]
                    bad_markers = [
                        "in this lesson",
                        "you'll learn the difference between",
                        "you will learn the difference between",
                        "visit englishclass101",
                        "englishclass101.com",
                        "learn english fast with real lessons",
                        "sign up for your free lifetime account",
                        "genius.com",
                        "azlyrics",
                        "songlyrics",
                        "metrolyrics",
                        "verse 1",
                        "chorus",
                        "[hook]",
                        "narration as",
                        "imdb.com/title",
                    ]
                    for snippet in snippets:
                        lower = snippet.lower()
                        if any(m in lower for m in bad_markers):
                            logger.info("GUVNA baseline rejected as tutorial/lyrics garbage")
                            continue
                        baseline["text"] = snippet
                        baseline["source"] = "google_baseline"
                        break
        except Exception as e:
            logger.info("GUVNA baseline lookup ERROR: %s", e)
        return baseline


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================
def create_guvna(
    roux_seeds: Optional[Dict[str, Dict[str, Any]]] = None,
    search_fn: Optional[SearchFn] = None,
    library_index: Optional[LibraryIndex] = None,
    manifesto_path: Optional[str] = None,
    curiosity_engine: Optional[Any] = None,
) -> "Guvna":
    """
    Factory function to create a Governor with full domain library.
    Returns:
        Initialized Guvna instance with 678 domains loaded
    """
    return Guvna(
        roux_seeds=roux_seeds,
        search_fn=search_fn,
        library_index=library_index,
        manifesto_path=manifesto_path,
        curiosity_engine=curiosity_engine,
    )


if __name__ == "__main__":
    guvna = create_guvna()
    print(f"✓ GUVNA booted with {guvna.library_metadata.total_domains} domains")
    print(f"✓ Libraries: {len(guvna.library_metadata.files)} files")
    print(
        f"✓ Constitution: "
        f"{'Loaded' if guvna.self_state.constitution_loaded else 'Using defaults'}"
    )
    print(f"✓ DNA Active: {guvna.self_state.dna_active}")
    print(f"✓ Curiosity Engine: {'Wired' if guvna.curiosity_engine else 'Not wired'}")
    greeting_response = guvna.greet("Hi, my name is Alex")
    print(f"\nGreeting Response:\n{greeting_response['result']}")
    test_stimulus = "What is the relationship between density and understanding?"
    response = guvna.process(test_stimulus)
    print(f"\nTalk Response:\nTone: {response['tone']} {response['tone_emoji']}")
    print(f"Domains Used: {response['soi_domains'][:5]}")
    print(f"Conversation Health: {response['conversation_health']}")
    print(f"Curiosity Context: {response.get('curiosity_context', 'none')}")

    # Test the fixes
    print("\n--- PREFERENCE FAST PATH TESTS ---")
    for test in [
        "for sure you like eric b and rakim?",
        "and no omega?",
        "you know rakim?",
        "what do you think of public enemy?",
        "you into coltrane?",
    ]:
        result = guvna.process(test)
        print(f"\nQ: {test}")
        print(f"STATUS: {result.get('status')}")
        print(f"A: {result.get('result', '')[:200]}")
