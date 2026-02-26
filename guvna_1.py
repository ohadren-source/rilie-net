"""
guvna_1.py

Act 5 – The Governor (Kernel + Initialization)

Contains:
- All imports and constants
- CATCH 44 blueprint loading
- Domain metadata
- Precision override logic
- Class definition
- __init__() method
- All helper methods EXCEPT process()

The Governor owns the axioms. On boot, she loads Catch 44 as kernel DNA.
"""

from __future__ import annotations

import logging
import re
import json
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
    wilden_swift_modulate,
    wilden_swift,
    _is_about_me,
    load_charculterie_manifesto,
    detect_tone_from_stimulus,
    apply_tone_header,
    TONE_EMOJIS,
    TONE_LABELS,
    is_serious_subject_text,
)

from guvna_self import GuvnaSelf

logger = logging.getLogger("guvna")

# Meaning fingerprint
try:
    from meaning import read_meaning
    MEANING_AVAILABLE = True
except ImportError:
    MEANING_AVAILABLE = False
    logger.warning("GUVNA: meaning.py not available — Kitchen will cook blind")

# Curiosity engine
try:
    from banks import search_curiosity
except ImportError:
    search_curiosity = None

# ============================================================================ #
# CATCH 44 BLUEPRINT LOADING (KERNEL DNA)
# ============================================================================ #

def load_catch44_blueprint() -> Dict[str, Any]:
    """
    Load SOi_sauc_e_SOME_KINDA_BLUEPRINT.md as kernel axioms.
    
    On boot, Guvna internalizes Catch 44 so every decision flows from axiom,
    not from pattern-matching or RLHF.
    
    Returns:
        Dictionary of axiom tracks (0-69) mapped to their rules.
    """
    try:
        with open("SOi_sauc_e_SOME_KINDA_BLUEPRINT.md", "r") as f:
            content = f.read()
        
        # Parse markdown into axiom dict
        axioms = {}
        
        # Extract each track definition (simplified parser)
        track_pattern = r"### #(\d+[a-z]?)\s+(.+?)\n\n(.+?)(?=### #|##|$)"
        matches = re.finditer(track_pattern, content, re.DOTALL)
        
        for match in matches:
            track_id = match.group(1)
            track_name = match.group(2)
            track_content = match.group(3).strip()
            
            axioms[track_id] = {
                "name": track_name,
                "content": track_content,
            }
        
        logger.info("GUVNA KERNEL: Loaded %d axioms from Catch 44 blueprint", len(axioms))
        return axioms
    
    except FileNotFoundError:
        logger.warning("GUVNA KERNEL: SOi_sauc_e_SOME_KINDA_BLUEPRINT.md not found — proceeding without axioms")
        return {}
    except Exception as e:
        logger.error("GUVNA KERNEL: Failed to load blueprint: %s", e)
        return {}

# ============================================================================ #
# CULTURAL ANCHORS + TASTE PROFILE
# ============================================================================ #

try:
    _ALL_CULTURAL_ANCHORS: Dict[str, Dict[str, Any]] = {}
    _ALL_CULTURAL_ANCHORS.update(_HIPHOP_ANCHORS)
except NameError:
    _ALL_CULTURAL_ANCHORS = {}

_RAKIM_KNOWLEDGE: Dict[str, Any] = _ALL_CULTURAL_ANCHORS.get("rakim", {})

_RILIE_TASTE: Dict[str, Any] = {
    "music_anchors": [
        "rakim",
        "eric b and rakim",
        "a tribe called quest",
        "de la soul",
        "outkast",
        "kendrick lamar",
        "black thought",
    ],
    "priority_domains": [
        "music",
        "life",
        "linguistics_cognition",
        "games",
        "urban_design",
    ],
    "notes": "Bias toward dense, thoughtful lyricism and groove-focused production.",
}

# ============================================================================ #
# DOMAIN LIBRARY METADATA
# ============================================================================ #

@dataclass
class DomainLibraryMetadata:
    """Central registry of 678 domains across all files."""

    total_domains: int = 678
    bool_domains: int = 0
    curve_domains: int = 0
    files: Dict[str, int] = field(
        default_factory=lambda: {
            "bigbang": 20,
            "biochem_universe": 25,
            "chemistry": 18,
            "civics": 32,
            "climate_catch44": 23,
            "computerscience": 22,
            "deeptime_geo": 17,
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
            "quantum_trading": 41,
            "thermodynamics": 22,
            "urban_design": 35,
        }
    )

    boole_substrate: str = "All domains reduce to bool/curve gates"
    core_tracks: List[int] = field(default_factory=lambda: [0, 2, 5, 23, 37, 67])

# ============================================================================ #
# PRECISION OVERRIDE (SOMMELIER)
# ============================================================================ #

_PRECISION_TRIGGERS = [
    r"\bwhat is\b",
    r"\bwhen did\b",
    r"\bwho was\b",
    r"\bwho is\b",
    r"\bhow many\b",
    r"\bhow much\b",
    r"\bhow long\b",
    r"\bhow far\b",
    r"\bwhere is\b",
    r"\bdefine\b",
    r"\bdefinition of\b",
    r"\bwhat does\b .* \bmean\b",
    r"\bwhat's the difference between\b",
    r"\bis it true\b",
    r"\bcheck if\b",
]

_PRECISION_EXCLUSIONS = [
    r"\bdo you think\b",
    r"\bdo you feel\b",
    r"\bwhat's life\b",
    r"\bwhat is the meaning\b",
    r"\bwhat's the point\b",
    r"\bshould I\b",
    r"\bwould you\b",
]

def detect_precision_request(stimulus: str) -> bool:
    """
    Returns True if user is asking a factual GET question.
    She must answer it. A. B. C. No tongue-in-cheek.
    The fact IS the demi-glace; skip less_is_more_or_less.
    """
    sl = stimulus.lower().strip()
    
    if any(re.search(pattern, sl) for pattern in _PRECISION_EXCLUSIONS):
        return False
    
    return any(re.search(pattern, sl) for pattern in _PRECISION_TRIGGERS)

# ============================================================================ #
# GUVNA CLASS DEFINITION
# ============================================================================ #

class Guvna(GuvnaSelf):
    """
    Act 5 – The Governor
    
    Orchestrates Acts 1–4 by delegating to RILIE (The Restaurant).
    Owns final authority, ethical guardrails, and axiom-based decisions.
    """

    def __init__(
        self,
        roux_seeds: Optional[Dict[str, Dict[str, Any]]] = None,
        search_fn: Optional[SearchFn] = None,
        library_index: Optional[LibraryIndex] = None,
        manifesto_path: Optional[str] = None,
        curiosity_engine: Optional[Any] = None,
        debug: bool = False,
    ):
        """
        Initialize the Governor.
        
        On boot:
        1. Load Catch 44 blueprint (kernel DNA)
        2. Initialize conversation memory
        3. Boot library indices
        4. Wire up RILIE (The Restaurant)
        5. Set up social/emotional state
        
        Parameters from api.py:
        - roux_seeds: Roux material seeds
        - search_fn: Search function for baseline lookups
        - library_index: Pre-built library index (optional)
        - manifesto_path: Path to manifesto file
        - curiosity_engine: Curiosity engine instance (optional)
        - debug: Debug mode flag
        """
        
        # Initialize parent (GuvnaSelf) and self-state
        super().__init__()
        self._init_self_state()
        
        # Store api.py parameters
        self.roux_seeds = roux_seeds
        self.manifesto_path = manifesto_path
        self.debug = debug
        
        # ===== KERNEL: LOAD CATCH 44 AXIOMS =====
        self.catch44_blueprint = load_catch44_blueprint()
        
        if not self.catch44_blueprint:
            logger.warning("GUVNA BOOT: Catch 44 blueprint empty — operating without kernel axioms")
        else:
            logger.info("GUVNA BOOT: Kernel loaded — %d axiom tracks active", len(self.catch44_blueprint))
        
        # ===== MEMORY =====
        self.memory = ConversationMemory()
        self.photogenic_db = PhotogenicDB()
        
        # ===== DOMAINS & LIBRARY =====
        self.domain_metadata = DomainLibraryMetadata()
        self.domain_index = build_domain_index()
        self.library_index = library_index or build_library_index()
        
        logger.info("GUVNA BOOT: Library loaded — %d domains across 21 files",
                    self.domain_metadata.total_domains)
        
        # ===== RILIE (THE RESTAURANT) =====
        self.rilie = RILIE()
        logger.info("GUVNA BOOT: RILIE initialized (Kitchen ready)")
        
        # ===== CURIOSITY ENGINE =====
        self.curiosity_engine = curiosity_engine
        if not curiosity_engine and search_curiosity:
            try:
                self.curiosity_engine = search_curiosity
            except Exception as e:
                logger.warning("GUVNA BOOT: Curiosity engine setup failed: %s", e)
        
        # ===== STATE =====
        self.self_state = RilieSelfState()
        self.social_state = SocialState()
        self.wit_state = WitState()
        self.language_mode = detect_language_mode("")  # Empty for now, detect from stimulus later
        
        # ===== TASTE & ANCHORS =====
        self.taste = _RILIE_TASTE
        self.cultural_anchors = _ALL_CULTURAL_ANCHORS
        self.rakim_knowledge = _RAKIM_KNOWLEDGE
        
        # ===== CATCH44 DNA =====
        self.catch44_dna = CATCH44DNA()
        
        # ===== SEARCH =====
        self.search_fn = search_fn
        
        logger.info("GUVNA BOOT COMPLETE: Governor ready, kernel loaded, brigade standing by")
    
    # ===== HELPER METHODS (bound from guvna_2 and guvna_2plus) =====
    # These are stitched in by the guvna.py shim after class definition
    
    def _compute_domain_and_factsfirst(
        self, stimulus: str, domains: List[str]
    ) -> tuple:
        """Helper stub — stitched in from guvna_2plus"""
        return None, False
    
    def _get_baseline(self, stimulus: str) -> Dict[str, Any]:
        """Helper stub — stitched in from guvna_2plus"""
        return {}
    
    def _apply_domain_lenses(self, stimulus: str) -> Dict[str, Any]:
        """Helper stub — stitched in from guvna_2plus"""
        return {}
    
    # _finalize_response lives in GuvnaSelf (guvna_self.py) — THE WRITER.
    # Do NOT define it here. The parent mixin owns it.
    # Any stub here would shadow the real one and break tone/history/LIMO.
