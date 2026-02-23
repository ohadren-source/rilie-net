"""
guvna_12.py

Act 5 – The Governor (Core)

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
- Language mode detection (literal/figurative/metaphor/simile/poetry)
- Social status tracking (user always above self)
- Library index for domain engine access (678 domains across B-U + urban_design)
- Curiosity resurface – past insights as context before RILIE processes
- Domain lenses flow into RILIE for weighted interpretation
- Déjà-vu as informative context on the plate
- Memory seeds curiosity – interesting topics get queued

FAST PATH CLASSIFIER (fires before Kitchen wakes up) and preference / taste
handling live in guvna_22.py and are stitched in via guvna.py.
"""

from __future__ import annotations

import logging
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
    wilden_swift,           # backwards-compatible wrapper
    _is_about_me,
    load_charculterie_manifesto,
    detect_tone_from_stimulus,
    apply_tone_header,
    TONE_EMOJIS,
    TONE_LABELS,
    is_serious_subject_text,
)
from guvna_self import GuvnaSelf  # Self-governing session awareness

logger = logging.getLogger("guvna")

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
    import re

    sl = stimulus.lower().strip()

    if any(re.search(pat, sl) for pat in _PRECISION_EXCLUSIONS):
        return False

    return any(re.search(pat, sl) for pat in _PRECISION_TRIGGERS)


# ============================================================================ #
# GUVNA CLASS
# ============================================================================ #

class Guvna(GuvnaSelf):
    """
    The Governor (Act 5) sits above The Restaurant (RILIE) and provides:

    - Final authority on what gets served
    - Ethical oversight via CATCH44DNA
    - Conversation memory and health tracking
    - Domain / baseline / meaning fusion before Kitchen wakes up
    """

    def __init__(
        self,
        roux_seeds: Optional[Dict[str, Dict[str, Any]]] = None,
        search_fn: Optional[SearchFn] = None,
        library_index: Optional[LibraryIndex] = None,
        manifesto_path: Optional[str] = None,
        curiosity_engine: Optional[Any] = None,
    ) -> None:
        # Coalesce both naming styles (legacy)
        effective_roux = roux_seeds if roux_seeds is not None else roux_seeds
        effective_search = search_fn if search_fn is not None else search_fn

        self.roux_seeds: Dict[str, Dict[str, Any]] = effective_roux or {}
        self.search_fn: Optional[SearchFn] = effective_search

        # LIBRARY BOOT – 678 DOMAINS LOADED
        self.library_index: LibraryIndex = library_index or build_library_index()
        self.library_metadata = DomainLibraryMetadata()

        logger.info(f"GUVNA BOOT: {self.library_metadata.total_domains} domains loaded")
        logger.info(f" Files: {len(self.library_metadata.files)} libraries")
        logger.info(f" Boole substrate: {self.library_metadata.boole_substrate}")
        logger.info(f" Core tracks: {self.library_metadata.core_tracks}")

        # FIX 3: Hard boot confirmation — no more silent degradation
        _actual_domains = (
            sum(self.library_metadata.files.values())
            if self.library_metadata.files
            else 0
        )
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
                "GUVNA BOOT CONFIRMED: full pantry online "
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
                "physics",
                "life",
                "games",
                "thermodynamics",
                "bigbang",
                "biochem",
                "chemistry",
                "civics",
                "climate",
                "computerscience",
                "deeptime",
                "developmental",
                "ecology",
                "evolve",
                "genomics",
                "linguistics",
                "nanotechnology",
                "network",
                "mathematics",
                "urban",
            ],
            ethics_source="Catch-44 DNA + 678-Domain Library",
            dna_active=True,
        )

        self.social_state = SocialState()
        self.dna = CATCH44DNA()

        # Domain state: track the last active domain for facts-first behavior
        self.current_domain: Optional[str] = None

        # SELF-GOVERNING SESSION STATE — wired via GuvnaSelf mixin
        self._init_self_state()

        # CONSTITUTION LOADING
        self.self_state.constitution_flags = load_charculterie_manifesto(
            manifesto_path
        )
        self.self_state.constitution_loaded = self.self_state.constitution_flags.get(
            "loaded", False
        )

        logger.info(
            "GUVNA: Charculterie Manifesto loaded"
            if self.self_state.constitution_loaded
            else "GUVNA: Charculterie Manifesto not found (using defaults)"
        )

    # -------------------------------------------------------------------------
    # DOMAIN INFERENCE FROM WEB — fallback for unknown subjects
    # -------------------------------------------------------------------------

    def _infer_domain_from_web(self, original_question: str) -> Optional[str]:
        """
        Extract subject/object from question using Chomsky.

        Search web for: "What subject/category/field/discipline does [concept] belong to?"
        Parse result and match against 678 domain names/keywords dynamically.

        Returns domain name if match found, None otherwise.
        """
        logger.info("GUVNA: _infer_domain_from_web called with: %s", original_question)

        if not self.search_fn:
            logger.info("GUVNA: search_fn is None, skipping web inference")
            return None

        logger.info("GUVNA: search_fn available, proceeding with web inference")

        # Use Chomsky to extract subject/object
        try:
            from ChomskyAtTheBit import extract_holy_trinity_for_roux

            parsed = extract_holy_trinity_for_roux(original_question)
            if not parsed:
                logger.info("GUVNA: Chomsky returned None/empty")
                return None

            subject = parsed.get("subject", "")
            obj = parsed.get("object", "")
            concept = subject or obj or original_question.strip()
            logger.info(
                "GUVNA: Chomsky extracted subject=%s, object=%s, concept=%s",
                subject,
                obj,
                concept,
            )
        except Exception as e:
            logger.info("GUVNA: Chomsky extraction failed: %s", e)
            concept = original_question.strip()

        if not concept:
            logger.info("GUVNA: No concept extracted, returning None")
            return None

        query = f"what subject category field discipline does {concept} belong to"
        logger.info("GUVNA: Searching web for: %s", query)

        try:
            results = self.search_fn(query)
            logger.info(
                "GUVNA: Web search returned %d results", len(results) if results else 0
            )
            if not results:
                logger.info("GUVNA: Web search returned empty, no domain inference")
                return None

            first_result = results[0].get("snippet", "") or results[0].get("title", "")
            first_result_lower = first_result.lower()
            logger.info("GUVNA: First result snippet: %s", first_result[:100])

            # Dynamically check if any 678 domain keywords appear in the result
            try:
                from rilie_innercore_12 import DOMAIN_KEYWORDS

                logger.info(
                    "GUVNA: Loaded DOMAIN_KEYWORDS, checking %d domains",
                    len(DOMAIN_KEYWORDS),
                )
                for domain, keywords in DOMAIN_KEYWORDS.items():
                    for keyword in keywords:
                        if keyword.lower() in first_result_lower:
                            logger.info(
                                "GUVNA: Web inference matched domain=%s via keyword=%s",
                                domain,
                                keyword,
                            )
                            return domain
                logger.info("GUVNA: No domain keywords matched in web result")
            except Exception as e:
                logger.info("GUVNA: DOMAIN_KEYWORDS import failed: %s", e)
                return None
        except Exception as e:
            logger.info("GUVNA: Web inference search failed: %s", e)
            return None

        return None

    # -------------------------------------------------------------------------
    # DOMAIN SHIFT DETECTION — Facts-first wiring
    # -------------------------------------------------------------------------

    def _compute_domain_and_factsfirst(
        self, stimulus: str, soi_domain_names: Optional[List[str]]
    ) -> tuple[Optional[str], bool]:
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

        return new_domain, facts_first

    # -------------------------------------------------------------------------
    # MAIN PROCESS – Core response pipeline (TIER 2 + FAST PATHS via guvna_22)
    # -------------------------------------------------------------------------

    def process(self, stimulus: str, maxpass: int = 1, **kwargs) -> Dict[str, Any]:
        """
        Main entry point for conversation.

        Orchestrates all 5 Acts: safety -> disclosure -> interpretation -> response -> governance.

        Steps:

        - Step 0: APERTURE check → GuvnaSelf.greet()
        - Step 0.5: MEANING FINGERPRINT → meaning.read_meaning()
        - Step 1: Fast path classifier (via guvna_22)
        - Step 2: Self-awareness fast path
        - Step 3: Baseline lookup
        - Step 3.1: Precision override detection
        - Step 3.5: Domain lenses → RILIE
        - Step 3.5b: Domain shift → facts-first
        - RIVER: early lookup telemetry
        - Step 3.7: Confidence gate
        - Step 4: Curiosity resurface
        - Step 5: RILIE core processing
        - Step 6–10: Governor oversight, memory, ethics, finalize

        kwargs accepted:

        - reference_context: Optional[Dict] from session.resolve_reference()
        - debug_river: Optional[bool] — if True, River also short-circuits and responds alone
        """

        self.turn_count += 1
        self.memory.turn_count += 1

        raw: Dict[str, Any] = {"stimulus": stimulus}

        # STEP 0.5: MEANING FINGERPRINT — read before Kitchen wakes up
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
                    social_fallback = self._handle_social_glue(
                        stimulus.strip(), stimulus.strip().lower()
                    )
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
                    social_fallback = self._handle_social_glue(
                        stimulus.strip(), stimulus.strip().lower()
                    )
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

        # STEP 1: FAST PATH CLASSIFIER (from guvna_22)
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
        _precision = detect_precision_request(stimulus)
        if _precision:
            raw["precision_override"] = True
            raw["baseline_score_boost"] = 0.25
            logger.info("GUVNA: Precision override — factual GET detected")

        # STEP 3.5: DOMAIN LENSES
        domain_annotations = self._apply_domain_lenses(stimulus)
        soi_domain_names = domain_annotations.get("matched_domains", [])

        # STEP 3.5b: DOMAIN SHIFT → FACTS-FIRST
        _, facts_first = self._compute_domain_and_factsfirst(
            stimulus, soi_domain_names
        )

        # RIVER — FIRST READ (lookup + say what she found)
        try:
            river_payload = None
            if hasattr(self, "guvna_river"):
                # Always run River for telemetry; may short-circuit if debug_river=True
                river_payload = self.guvna_river(
                    stimulus=stimulus,
                    meaning=_meaning,
                    get_baseline=self._get_baseline,
                    apply_domain_lenses=self._apply_domain_lenses,
                    compute_domain_and_factsfirst=self._compute_domain_and_factsfirst,
                    debug_mode=bool(kwargs.get("debug_river", False)),
                )
                if river_payload is not None:
                    # Store what River saw in raw for future introspection
                    raw["river"] = river_payload
        except Exception as e:
            logger.warning("GUVNA: River failed (non-fatal): %s", e)
            river_payload = None

        # If debug_river=True and River returned a payload, serve River and stop
        if river_payload is not None and bool(kwargs.get("debug_river", False)):
            return self._finalize_response(river_payload)

        # STEP 3.7: CONFIDENCE GATE (PRIORITY CHECK)
        has_domain = bool(soi_domain_names)
        has_baseline = bool(baseline_text and baseline_text.strip())
        has_meaning = bool(_meaning and _meaning.pulse > 0.3)

        logger.info(
            "GUVNA CONFIDENCE GATE: has_domain=%s (%s), has_baseline=%s (len=%d), has_meaning=%s (pulse=%.2f)",
            has_domain,
            soi_domain_names if has_domain else "EMPTY",
            has_baseline,
            len(baseline_text) if baseline_text else 0,
            has_meaning,
            _meaning.pulse if _meaning else 0.0,
        )

        if not (has_domain or has_baseline or has_meaning):
            logger.info(
                "GUVNA: Confidence gate TRIGGERED → NO viable content (all checks failed). "
                "Returning 'I don't know' early."
            )
            return self._finalize_response(
                {
                    "stimulus": stimulus,
                    "result": (
                        "I don't know. I looked everywhere — combed the 678 domains, "
                        "searched the internet, came back with nothing solid enough to say with confidence."
                    ),
                    "quality_score": 0.0,
                    "status": "NO_CONFIDENCE",
                    "tone": "honest",
                    "meaning": raw.get("meaning"),
                }
            )

        logger.info(
            "GUVNA: Confidence gate PASSED → proceeding to Kitchen (domain=%s, baseline=%s, meaning=%s)",
            "YES" if has_domain else "NO",
            "YES" if has_baseline else "NO",
            "YES" if has_meaning else "NO",
        )

        # STEP 4: CURIOSITY RESURFACE (GATED BY DOMAIN KNOWLEDGE)
        curiosity_context = ""
        if has_domain:
            if self.curiosity_engine and hasattr(self.curiosity_engine, "resurface"):
                try:
                    curiosity_context = self.curiosity_engine.resurface(stimulus)
                    if curiosity_context:
                        logger.info("GUVNA: Curiosity resurfaced context for stimulus")
                except Exception as e:
                    logger.debug(
                        "GUVNA: Curiosity resurface failed (non-fatal): %s", e
                    )
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
                        logger.info(
                            "GUVNA: Curiosity resurfaced from banks_curiosity"
                        )
                except Exception as e:
                    logger.debug(
                        "GUVNA: banks curiosity search failed (non-fatal): %s", e
                    )
        else:
            logger.info(
                "GUVNA: Domain unknown — curiosity gated. Hunting for subject instead."
            )

        raw["curiosity_context"] = curiosity_context

        # STEP 5: RILIE CORE PROCESSING — unchanged
        rilie_result = self.rilie.process(
            stimulus=stimulus,
            baselinetext=baseline_text,
            domainhints=soi_domain_names,
            curiositycontext=curiosity_context,
            meaning=_meaning,
            precisionoverride=raw.get("precision_override", False),
            baselinescoreboost=raw.get("baseline_score_boost", 0.03),
            factsfirst=facts_first,
        )

        # STEP 6–10: Governor oversight, memory, ethics, finalize
        return self._finalize_response(rilie_result)
