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
- Self-awareness fast path (_is_about_me + rilie_innercore)
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
- Social glue   → laughter, agreement, compliments, thanks, farewell
- Arithmetic    → "what is 3 times 6" → 18
- Conversion    → "how many feet in a mile" → 5280
- Spelling      → "how do you spell necessary" → N-E-C-E-S-S-A-R-Y
- Recall        → "what did you just say" / "what's my name"
- Clarification → "what do you mean" → rewraps last response

TIER 2 WIRING:
1. Curiosity resurfaces into Step 3.5 (context, not afterthought)
2. wilden_swift_modulate() in Step 5 (Guvna owns shaping, Talk owns scoring)
3. Domain lenses flow into rilie.process() (Kitchen uses them to weight)
4. Déjà-vu rides as informative context (not a gate)
5. Memory seeds curiosity (bidirectional from day one)

678 total bool/curve gates, all demiglace to Boole substrate
"""

from __future__ import annotations

import logging
import re
import random
from typing import Any, Dict, List, Optional, Tuple
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
    wilden_swift_score,
    wilden_swift,
    _is_about_me,
    load_charculterie_manifesto,
    detect_tone_from_stimulus,
    apply_tone_header,
    TONE_EMOJIS,
    TONE_LABELS,
    is_serious_subject_text,
)

# Curiosity engine — resurface past insights as context
try:
    from banks import search_curiosity
except ImportError:
    search_curiosity = None

logger = logging.getLogger("guvna")

# ============================================================================
# FAST PATH CONVERSION TABLE
# ============================================================================

_CONVERSIONS: Dict[tuple, float] = {
    # Length
    ("mile", "foot"): 5280.0,   ("mile", "feet"): 5280.0,
    ("mile", "meter"): 1609.34, ("mile", "metre"): 1609.34,
    ("mile", "kilometer"): 1.60934, ("mile", "kilometre"): 1.60934,
    ("mile", "km"): 1.60934,
    ("kilometer", "mile"): 0.621371, ("kilometre", "mile"): 0.621371,
    ("km", "mile"): 0.621371,
    ("meter", "foot"): 3.28084,  ("meter", "feet"): 3.28084,
    ("metre", "foot"): 3.28084,  ("metre", "feet"): 3.28084,
    ("meter", "inch"): 39.3701,  ("metre", "inch"): 39.3701,
    ("foot", "meter"): 0.3048,   ("foot", "metre"): 0.3048,
    ("foot", "centimeter"): 30.48, ("foot", "cm"): 30.48,
    ("feet", "meter"): 0.3048,   ("feet", "metre"): 0.3048,
    ("inch", "centimeter"): 2.54, ("inch", "cm"): 2.54,
    ("inch", "millimeter"): 25.4, ("inch", "mm"): 25.4,
    ("centimeter", "inch"): 0.393701, ("cm", "inch"): 0.393701,
    ("millimeter", "inch"): 0.0393701, ("mm", "inch"): 0.0393701,
    # Weight
    ("kilogram", "pound"): 2.20462, ("kilogram", "lb"): 2.20462,
    ("kg", "pound"): 2.20462,       ("kg", "lb"): 2.20462,
    ("pound", "kilogram"): 0.453592, ("pound", "kg"): 0.453592,
    ("lb", "kilogram"): 0.453592,   ("lb", "kg"): 0.453592,
    ("ounce", "gram"): 28.3495,     ("oz", "gram"): 28.3495,
    ("ounce", "g"): 28.3495,        ("oz", "g"): 28.3495,
    ("gram", "ounce"): 0.035274,    ("gram", "oz"): 0.035274,
    ("g", "ounce"): 0.035274,       ("g", "oz"): 0.035274,
    ("ton", "kilogram"): 907.185,   ("ton", "kg"): 907.185,
    # Volume
    ("liter", "gallon"): 0.264172,  ("litre", "gallon"): 0.264172,
    ("gallon", "liter"): 3.78541,   ("gallon", "litre"): 3.78541,
    ("cup", "milliliter"): 236.588, ("cup", "ml"): 236.588,
    ("milliliter", "cup"): 0.00422675, ("ml", "cup"): 0.00422675,
    ("liter", "milliliter"): 1000.0, ("litre", "milliliter"): 1000.0,
    ("liter", "ml"): 1000.0,         ("litre", "ml"): 1000.0,
    ("milliliter", "liter"): 0.001,  ("ml", "liter"): 0.001,
    # Time
    ("hour", "minute"): 60.0,   ("hour", "second"): 3600.0,
    ("minute", "second"): 60.0, ("day", "hour"): 24.0,
    ("day", "minute"): 1440.0,  ("week", "day"): 7.0,
    ("year", "day"): 365.25,    ("year", "month"): 12.0,
    ("month", "day"): 30.44,
    # Data
    ("gigabyte", "megabyte"): 1024.0, ("gb", "mb"): 1024.0,
    ("terabyte", "gigabyte"): 1024.0, ("tb", "gb"): 1024.0,
    ("megabyte", "kilobyte"): 1024.0, ("mb", "kb"): 1024.0,
    ("kilobyte", "byte"): 1024.0,     ("kb", "byte"): 1024.0,
}

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
# THE GOVERNOR (REVISED — TIER 2 WIRING + FAST PATHS)
# ============================================================================

class Guvna:
    """
    The Governor (Act 5) sits above The Restaurant (RILIE) and provides:

    Core Authority:
    - Final authority on what gets served
    - Ethical oversight via CATCH44DNA
    - Self-awareness fast path (_is_about_me + rilie_innercore)

    Fast Path Classifier (NEW — fires BEFORE Kitchen):
    - Social glue (laughter, agreement, compliments, thanks, farewell)
    - Arithmetic (3 times 6 → 18)
    - Unit conversion (feet in a mile → 5280)
    - Spelling (spell necessary → N-E-C-E-S-S-A-R-Y)
    - Recall (what did you say / what's my name)
    - Clarification (what do you mean → rewrap last response)

    Tone & Expression:
    - Wit detection and wilden_swift_modulate (Guvna owns shaping)
    - Language mode detection
    - Tone signaling via single governing emoji per response
    - Social status tracking (user always > self)

    Knowledge & Baselines:
    - Optional web lookup pre-pass (KISS philosophy)
    - Comparison between web baseline and RILIE's own compression
    - Library index for domain engine access (678 domains)
    - Curiosity resurface — past insights as pre-RILIE context

    Conversation Management:
    - YELLOW GATE – conversation health monitoring
    - WHOSONFIRST – greeting gate
    - Conversation memory (9 behaviors)
    - Photogenic DB (elephant memory)
    - Memory seeds curiosity (bidirectional cross-talk)

    Integration:
    Orchestrates Acts 1–4:
    - Act 1: Triangle (safety gate)
    - Act 2: DDD/Hostess (disclosure level)
    - Act 3: Kitchen/Core (interpretation passes)
    - Act 4: RILIE (conversation response)
    """

    def __init__(
        self,
        roux_seeds: Optional[Dict[str, Dict[str, Any]]] = None,
        search_fn: Optional[SearchFn] = None,
        library_index: Optional[LibraryIndex] = None,
        manifesto_path: Optional[str] = None,
        curiosity_engine: Optional[Any] = None,
        # Backwards-compatible aliases for existing callers:
        rouxseeds: Optional[Dict[str, Dict[str, Any]]] = None,
        searchfn: Optional[SearchFn] = None,
    ) -> None:
        """
        Initialize the Governor with full domain library access.

        Args:
            roux_seeds: Configuration dict for RILIE
            search_fn: Optional web search function
            library_index: Pre-built LibraryIndex (678 domains) or builds from library/
            manifesto_path: Path to Charculterie Manifesto
            curiosity_engine: Optional CuriosityEngine for resurface + seeding
            rouxseeds: Backwards-compatible alias for roux_seeds
            searchfn: Backwards-compatible alias for search_fn
        """
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

        # RILIE still expects rouxseeds/searchfn keywords
        self.rilie = RILIE(rouxseeds=self.roux_seeds, searchfn=self.search_fn)

        # MEMORY SYSTEMS
        self.memory = ConversationMemory()
        self.photogenic = PhotogenicDB()
        self.domain_index = build_domain_index()

        # CURIOSITY ENGINE (Tier 2 — bidirectional cross-talk)
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

        # CONVERSATION STATE
        self.turn_count: int = 0
        self.user_name: Optional[str] = None
        self.whosonfirst: bool = True

        # Governor's own response memory – anti-déjà-vu at every exit
        self._response_history: List[str] = []

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
    # APERTURE – First contact. Before anything else.
    # -----------------------------------------------------------------
    def greet(self, stimulus: str, known_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        APERTURE – Turn 0 only. First thing that happens.
        Either know them by name, or meet them.
        Returns greeting response or None if not turn 0.
        """
        if not self.whosonfirst:
            return None
        if not known_name:
            s = stimulus.lower().strip()
            name_intros = ["my name is", "i'm ", "i am ", "call me", "name's"]
            for intro in name_intros:
                if intro in s:
                    idx = s.index(intro) + len(intro)
                    rest = stimulus[idx:].strip().split()[0] if idx < len(stimulus) else ""
                    name = rest.strip(".,!?;:'\"")
                    if name and len(name) > 1:
                        known_name = name.capitalize()
                        break
        if known_name:
            self.user_name = known_name
        if self.user_name:
            greeting_text = (
                f"Hi {self.user_name}! It's great talking to you again... "
                "what's on your mind today?"
            )
        else:
            greeting_text = (
                "Hi there! What's your name? You can call me RILIE if you please... :)"
            )
        self.turn_count += 1
        self.memory.turn_count += 1
        tone = detect_tone_from_stimulus(stimulus)
        result_with_tone = apply_tone_header(greeting_text, tone)
        response = {
            "stimulus": stimulus,
            "result": result_with_tone,
            "status": "APERTURE",
            "tone": tone,
            "tone_emoji": TONE_EMOJIS.get(tone, TONE_EMOJIS["insightful"]),
            "turn_count": self.turn_count,
            "user_name": self.user_name,
            "whosonfirst": False,
        }
        self.whosonfirst = False
        return self._finalize_response(response)

    # -----------------------------------------------------------------
    # MAIN PROCESS – Core response pipeline (TIER 2 WIRED + FAST PATHS)
    # -----------------------------------------------------------------
    def process(self, stimulus: str, maxpass: int = 1) -> Dict[str, Any]:
        """
        Main entry point for conversation.
        Orchestrates all 5 Acts: safety -> disclosure -> interpretation -> response -> governance.

        TIER 2 changes:
        - Step 0: APERTURE check
        - Step 1: FAST PATH CLASSIFIER (new — fires before Kitchen)
        - Step 2: SELF-AWARENESS FAST PATH (wired to rilie_innercore)
        - Step 3: BASELINE LOOKUP
        - Step 3.5: Curiosity resurface (context before RILIE)
        - Step 4: Domain lenses flow into rilie.process()
        - Step 5: wilden_swift_modulate (not the combined function)
        - Step 6: Déjà-vu as informative context + memory seeds curiosity
        """
        self.turn_count += 1
        self.memory.turn_count += 1
        raw = {"stimulus": stimulus}

        # ==============================================================
        # STEP 0: APERTURE CHECK
        # ==============================================================
        if self.whosonfirst:
            greeting = self.greet(stimulus)
            if greeting:
                return greeting

        # ==============================================================
        # STEP 1: FAST PATH CLASSIFIER
        # Kitchen doesn't wake up for things that don't need cooking.
        # ==============================================================
        fast = self._classify_stimulus(stimulus)
        if fast:
            fast["stimulus"] = stimulus
            return self._finalize_response(fast)

        # ==============================================================
        # STEP 2: SELF-AWARENESS FAST PATH (wired to rilie_innercore)
        # ==============================================================
        try:
            from rilie_innercore import is_self_question
            _self_gate = _is_about_me(stimulus) or is_self_question(stimulus)
        except ImportError:
            _self_gate = _is_about_me(stimulus)

        if _self_gate:
            return self._finalize_response(self._respond_from_self(stimulus))

        # ==============================================================
        # STEP 3: BASELINE LOOKUP (web search if needed)
        # ==============================================================
        baseline = self._get_baseline(stimulus)
        baseline_text = baseline.get("text", "")

        # ==============================================================
        # STEP 3.5: DOMAIN LENSES (apply 678-domain library)
        # ==============================================================
        domain_annotations = self._apply_domain_lenses(stimulus)
        soi_domain_names = domain_annotations.get("matched_domains", [])

        # ==============================================================
        # STEP 4: CURIOSITY RESURFACE (Tier 2 — context before RILIE)
        # She walks into the kitchen already knowing what she explored.
        # ==============================================================
        curiosity_context = ""
        if self.curiosity_engine and hasattr(self.curiosity_engine, 'resurface'):
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

        # ==============================================================
        # STEP 5: RILIE CORE PROCESSING (Acts 1-4) — DOMAIN LENSES FLOW
        # TIER 2: Domain lenses now flow into RILIE so the Kitchen
        # uses them to weight interpretation passes. Supreme burrito.
        # ==============================================================
        rilie_result = self.rilie.process(
            stimulus=stimulus,
            baseline_text=baseline_text,
            domain_hints=soi_domain_names,
            curiosity_context=curiosity_context,
        )
        if not rilie_result:
            rilie_result = {}
        raw.update(rilie_result)

        # ==============================================================
        # STEP 6: GOVERNOR OVERSIGHT (Act 5) — MODULATE, NOT SCORE
        # ==============================================================
        wit = detect_wit(stimulus)
        raw["wit"] = wit

        language = detect_language_mode(stimulus)
        raw["language_mode"] = language

        tone = detect_tone_from_stimulus(stimulus)
        if is_serious_subject_text(stimulus):
            if any(w in stimulus.lower() for w in ["feel", "hurt", "scared", "pain"]):
                tone = "compassionate"
        raw["tone"] = tone
        raw["tone_emoji"] = TONE_EMOJIS.get(tone, TONE_EMOJIS["insightful"])

        # TIER 2: wilden_swift_modulate — Guvna owns shaping, Talk owns scoring
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

        # ==============================================================
        # STEP 7: MEMORY & CONVERSATION HEALTH (YELLOW GATE)
        # ==============================================================
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

        # TIER 2: Déjà-vu as informative context (not a gate)
        dejavu = raw.get("dejavu", {"count": 0, "frequency": 0, "similarity": "none"})
        if dejavu.get("frequency", 0) > 0:
            logger.info(
                "GUVNA: Déjà-vu signal (freq=%d) — informative context, not gate",
                dejavu["frequency"]
            )

        # TIER 2: Memory seeds curiosity (bidirectional cross-talk)
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

        # ==============================================================
        # STEP 8: DOMAIN ANNOTATIONS & SOi TRACKS
        # ==============================================================
        raw["domain_annotations"] = domain_annotations
        raw["soi_domains"] = soi_domain_names
        raw["memory_polaroid"] = memory_polaroid
        raw["domains_used"] = soi_domain_names

        # ==============================================================
        # STEP 9: ETHICS CHECK (CATCH44DNA)
        # ==============================================================
        self.self_state.dna_active = True
        raw["dna_active"] = self.self_state.dna_active

        # ==============================================================
        # STEP 10: RESPONSE FINALIZATION
        # ==============================================================
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

        if result_text and not result_text.startswith(tone) and not is_blocked:
            raw["result"] = apply_tone_header(result_text, tone)

        result_text = raw.get("result", "")
        if memory_callback and result_text:
            raw["result"] = memory_callback + "\n\n" + result_text
        if memory_thread and result_text:
            raw["result"] = raw["result"] + "\n\n" + memory_thread

        if self.whosonfirst:
            self.whosonfirst = False

        return self._finalize_response(raw)

    # ═══════════════════════════════════════════════════════════════════════
    # FAST PATH CLASSIFIER — fires before the Kitchen wakes up
    # ═══════════════════════════════════════════════════════════════════════

    def _classify_stimulus(self, stimulus: str) -> Optional[Dict[str, Any]]:
        """
        Routes stimulus to a fast-path handler if it matches.
        Returns a response dict or None (let Kitchen handle it).
        Order: social glue → arithmetic → conversion → spelling → recall → clarification
        """
        s = stimulus.strip()
        sl = s.lower()

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

    def _handle_social_glue(self, s: str, sl: str) -> Optional[Dict[str, Any]]:
        """
        Catch conversational glue: laughter, agreement, compliments,
        thanks, farewell. Only fires on SHORT inputs with no real question.
        """
        word_count = len(s.split())
        has_question = "?" in s or any(
            sl.startswith(p) for p in [
                "what", "why", "how", "when", "where", "who",
                "can ", "do ", "does ", "is ", "are ", "tell me",
                "explain", "describe",
            ]
        )
        if has_question:
            return None

        # Laughter
        laugh_words = {"haha", "hahaha", "hahahaha", "lol", "lmao", "lmfao", "hehe", "heh"}
        if any(lw in sl for lw in laugh_words) and word_count <= 6:
            replies = ["Ha! 😄", "Right?! 😄", "I felt that. 😄", "Yeah that one got me. 😄"]
            return {"result": random.choice(replies), "status": "SOCIAL_GLUE", "triangle_reason": "CLEAN", "quality_score": 0.9}

        # Agreement / validation
        agree_words = {"exactly", "precisely", "correct", "spot on", "bingo", "totally", "absolutely"}
        if any(aw in sl for aw in agree_words) and word_count <= 5:
            replies = ["That's it. 🍳", "Right there.", "Exactly.", "Good. Then let's keep going."]
            return {"result": random.choice(replies), "status": "SOCIAL_GLUE", "triangle_reason": "CLEAN", "quality_score": 0.9}

        # "that's right" / "you're right"
        if (
            any(t in sl for t in ["that's right", "thats right", "you're right", "youre right"])
            and word_count <= 5
        ):
            replies = ["Good. 🍳", "Then let's keep going.", "Knew you'd land there."]
            return {"result": random.choice(replies), "status": "SOCIAL_GLUE", "triangle_reason": "CLEAN", "quality_score": 0.9}

        # Compliment directed at RILIE
        compliment_phrases = [
            "you're funny", "youre funny", "you're smart", "youre smart",
            "good answer", "well said", "good point", "great answer",
            "love that", "nice one", "well done", "you're good", "youre good",
            "you're great", "youre great", "you're amazing", "youre amazing",
        ]
        if any(cp in sl for cp in compliment_phrases) and word_count <= 7:
            replies = [
                "Appreciate that. 🙏", "Thank you — genuinely.",
                "That means something.", "I'll take it. 🍳",
            ]
            return {"result": random.choice(replies), "status": "SOCIAL_GLUE", "triangle_reason": "CLEAN", "quality_score": 0.9}

        # Thanks
        thanks_words = ["thanks", "thank you", "thx", "cheers", "merci", "gracias"]
        if any(tw in sl for tw in thanks_words) and word_count <= 5:
            replies = ["Of course. 🍳", "Always.", "That's what I'm here for.", "Any time."]
            return {"result": random.choice(replies), "status": "SOCIAL_GLUE", "triangle_reason": "CLEAN", "quality_score": 0.9}

        # Farewell
        bye_triggers = [
            "bye", "goodbye", "see you", "take care", "goodnight",
            "good night", "1luv", "3-luv", "ciao", "peace out",
        ]
        if any(bw in sl for bw in bye_triggers) and word_count <= 5:
            replies = [
                "Talk soon. 🔪", "Come back when you're hungry. 🍳",
                "Good night. 🔱", "1Luv. 🍳",
            ]
            return {"result": random.choice(replies), "status": "SOCIAL_GLUE", "triangle_reason": "CLEAN", "quality_score": 0.9}

        return None

    def _solve_arithmetic(self, s: str, sl: str) -> Optional[Dict[str, Any]]:
        """
        Fast-path arithmetic. Handles word operators and digit expressions.
        Requires at least one operator — bare numbers fall through to Kitchen.
        """
        expr = sl
        # Normalize word operators
        expr = re.sub(r'\btimes\b|\bmultiplied by\b', '*', expr)
        expr = re.sub(r'\bdivided by\b|\bover\b', '/', expr)
        expr = re.sub(r'\bplus\b|\badded to\b', '+', expr)
        expr = re.sub(r'\bminus\b|\bsubtracted from\b', '-', expr)
        expr = re.sub(r'\bsquared\b', '**2', expr)
        expr = re.sub(r'\bcubed\b', '**3', expr)
        # x between digits only (3x6 → 3*6, not "explain x to me")
        expr = re.sub(r'(\d)\s*[xX]\s*(\d)', r'\1 * \2', expr)
        # Strip question prefixes
        expr = re.sub(
            r"^(what'?s?|calculate|compute|solve|what is|whats|evaluate)\s+",
            '', expr
        ).strip().rstrip('?').strip()
        # Must contain at least one real operator
        if not re.search(r'[\+\-\*\/]', expr) and '**' not in expr:
            return None
        # Must be a pure arithmetic expression
        if re.fullmatch(r'[\d\s\+\-\*\/\.\(\)\*\*]+', expr):
            try:
                result = eval(
                    compile(expr, '<string>', 'eval'),
                    {"__builtins__": {}},
                    {}
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
        """
        Fast-path unit conversion.
        Handles temperature (C↔F), and table lookups for common units.
        """
        # Temperature: Celsius → Fahrenheit
        m = re.search(
            r'(\-?\d+\.?\d*)\s*(?:celsius|centigrade|°c)\s+(?:to|in)\s+(?:fahrenheit|°f)',
            sl
        )
        if m:
            val = float(m.group(1))
            result = round(val * 9 / 5 + 32, 2)
            if result == int(result):
                result = int(result)
            return {"result": f"{result}°F", "status": "CONVERSION", "triangle_reason": "CLEAN", "quality_score": 1.0}

        # Temperature: Fahrenheit → Celsius
        m = re.search(
            r'(\-?\d+\.?\d*)\s*(?:fahrenheit|°f)\s+(?:to|in)\s+(?:celsius|centigrade|°c)',
            sl
        )
        if m:
            val = float(m.group(1))
            result = round((val - 32) * 5 / 9, 2)
            if result == int(result):
                result = int(result)
            return {"result": f"{result}°C", "status": "CONVERSION", "triangle_reason": "CLEAN", "quality_score": 1.0}

        # "how many UNIT in a/an UNIT"
        m = re.search(r'how many (\w+)\s+(?:are |is )?in (?:a |an |one )?(\w+)', sl)
        if m:
            target = m.group(1).rstrip('s') if not m.group(1).endswith('ss') else m.group(1)
            source = m.group(2).rstrip('s') if not m.group(2).endswith('ss') else m.group(2)
            for tu in [m.group(1), target]:
                for su in [m.group(2), source]:
                    factor = _CONVERSIONS.get((su, tu))
                    if factor is not None:
                        result = factor if factor != int(factor) else int(factor)
                        return {
                            "result": f"{result:g} {m.group(1)} in a {m.group(2)}",
                            "status": "CONVERSION",
                            "triangle_reason": "CLEAN",
                            "quality_score": 1.0,
                        }

        # "convert N UNIT to UNIT"
        m = re.search(r'convert\s+(\d+\.?\d*)\s+(\w+)\s+to\s+(\w+)', sl)
        if m:
            amount = float(m.group(1))
            from_u = m.group(2).rstrip('s') if not m.group(2).endswith('ss') else m.group(2)
            to_u = m.group(3).rstrip('s') if not m.group(3).endswith('ss') else m.group(3)
            for fu in [m.group(2), from_u]:
                for tu in [m.group(3), to_u]:
                    factor = _CONVERSIONS.get((fu, tu))
                    if factor is not None:
                        result = round(amount * factor, 4)
                        if result == int(result):
                            result = int(result)
                        return {
                            "result": f"{amount} {m.group(2)} = {result:g} {m.group(3)}",
                            "status": "CONVERSION",
                            "triangle_reason": "CLEAN",
                            "quality_score": 1.0,
                        }

        return None

    def _solve_spelling(self, s: str, sl: str) -> Optional[Dict[str, Any]]:
        """
        Fast-path spelling. Returns the word with letter-by-letter breakdown.
        """
        m = re.search(
            r'(?:how (?:do you |to )?spell|spell(?:ing of)?)\s+([a-zA-Z\-\']+)',
            sl
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

    def _handle_recall(self, s: str, sl: str) -> Optional[Dict[str, Any]]:
        """
        Fast-path memory recall.
        Handles: name recall, last response recall.
        Goes to Photogenic first, falls back to _response_history.
        """
        recall_triggers = [
            "what did you just say", "what did you say", "say that again",
            "can you repeat", "repeat that", "what was that",
            "do you remember my name", "what's my name", "whats my name",
            "who am i", "do you know my name",
        ]
        if not any(trigger in sl for trigger in recall_triggers):
            return None

        # Name recall
        if any(t in sl for t in ["my name", "who am i", "know my name"]):
            if self.user_name:
                return {
                    "result": f"Your name is {self.user_name}. 🐘",
                    "status": "RECALL",
                    "triangle_reason": "CLEAN",
                    "quality_score": 1.0,
                }
            return {
                "result": "I don't have your name yet — what should I call you?",
                "status": "RECALL",
                "triangle_reason": "CLEAN",
                "quality_score": 1.0,
            }

        # Last response recall
        if self._response_history:
            last = self._response_history[-1]
            # Strip tone header if present
            if "\n\n" in last:
                last = last.split("\n\n", 1)[1]
            return {
                "result": f"I said: \"{last}\"",
                "status": "RECALL",
                "triangle_reason": "CLEAN",
                "quality_score": 1.0,
            }

        return {
            "result": "I don't have that in my memory yet — we've only just started.",
            "status": "RECALL",
            "triangle_reason": "CLEAN",
            "quality_score": 0.7,
        }

    def _handle_clarification(self, s: str, sl: str) -> Optional[Dict[str, Any]]:
        """
        Fast-path clarification.
        Rewraps the last response with a bridge phrase.
        Only fires on SHORT inputs (≤8 words) with no new topic.
        """
        clarify_triggers = [
            "what do you mean", "what does that mean", "can you explain that",
            "explain that", "i don't understand", "i dont understand",
            "say that differently", "in other words", "what are you saying",
        ]
        short_triggers = ["huh?", "what?", "come again", "say again"]

        word_count = len(s.split())
        matched = any(t in sl for t in clarify_triggers) and word_count <= 8
        matched = matched or any(sl.strip().rstrip('?!.') == t.rstrip('?') for t in short_triggers)

        if not matched:
            return None

        if self._response_history:
            last = self._response_history[-1]
            if "\n\n" in last:
                last = last.split("\n\n", 1)[1]
            bridges = [
                f"What I'm getting at: {last}",
                f"Put another way — {last}",
                f"Simpler: {last}",
            ]
            return {
                "result": random.choice(bridges),
                "status": "CLARIFICATION",
                "triangle_reason": "CLEAN",
                "quality_score": 0.8,
            }

        return {
            "result": "Which part? Give me a bit more and I'll work with you on it.",
            "status": "CLARIFICATION",
            "triangle_reason": "CLEAN",
            "quality_score": 0.7,
        }

    # ═══════════════════════════════════════════════════════════════════════
    # SELF-AWARENESS FAST PATH (wired to rilie_innercore)
    # ═══════════════════════════════════════════════════════════════════════

    def _respond_from_self(self, stimulus: str) -> Dict[str, Any]:
        """
        Self-aware response for 'about me' queries.
        Delegates to rilie_innercore.get_self_answer() for rich identity answers.
        Falls back to name if no hard answer exists.
        """
        try:
            from rilie_innercore import get_self_answer
            answer = get_self_answer(stimulus)
            if answer:
                return {
                    "result": answer,
                    "status": "SELF_REFLECTION",
                    "triangle_reason": "CLEAN",
                }
        except ImportError:
            pass
        return {
            "result": "My name is RILIE.",
            "status": "SELF_REFLECTION",
            "triangle_reason": "CLEAN",
        }

    # -----------------------------------------------------------------
    # DOMAIN LENSES + BASELINE
    # -----------------------------------------------------------------
    def _apply_domain_lenses(self, stimulus: str) -> Dict[str, Any]:
        """
        Apply domain-specific lenses using 678-domain library.
        Returns a dict of domain annotations showing which domains were activated.
        """
        domain_annotations = {}
        try:
            domains = get_tracks_for_domains([stimulus])
            if domains:
                domain_annotations["matched_domains"] = [d.get("domain", "") for d in domains]
                domain_annotations["count"] = len(domains)
                domain_annotations["boole_substrate"] = "All domains reduce to bool/curve"
        except Exception as e:
            logger.debug("Domain lens error: %s", e)
        return domain_annotations

    def _get_baseline(self, stimulus: str) -> Dict[str, Any]:
        """
        STEP 3: Do I know this? If not, learn from Google.
        She shouldn't pretend. If she doesn't know, she learns.
        """
        baseline = {"text": "", "source": "", "raw_results": []}
        stimulus_lower = (stimulus or "").lower()
        known_patterns = ["what is", "explain", "tell me about", "how does"]
        is_entity_question = not any(p in stimulus_lower for p in known_patterns)
        should_force_google = is_entity_question or len(stimulus) < 30
        try:
            if self.search_fn:
                baseline_query = (
                    stimulus if should_force_google
                    else f"what is the correct response to {stimulus}"
                )
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
                    ]
                    for snippet in snippets:
                        lower = snippet.lower()
                        if any(m in lower for m in bad_markers):
                            logger.info("GUVNA baseline rejected as ESL/tutorial garbage")
                            continue
                        baseline["text"] = snippet
                        baseline["source"] = "google_baseline"
                        break
        except Exception as e:
            logger.debug("Baseline lookup error: %s", e)
        return baseline

    # -----------------------------------------------------------------
    # RESPONSE FINALIZATION
    # -----------------------------------------------------------------
    def _finalize_response(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Finalize response: add metadata, ensure all required fields present."""
        final = {
            "stimulus": raw.get("stimulus", ""),
            "result": raw.get("result", ""),
            "status": raw.get("status", "OK"),
            "tone": raw.get("tone", "insightful"),
            "tone_emoji": raw.get("tone_emoji", TONE_EMOJIS.get("insightful", "💡")),
            "quality_score": raw.get("quality_score", 0.5),
            "priorities_met": raw.get("priorities_met", 0),
            "anti_beige_score": raw.get("anti_beige_score", 0.5),
            "depth": raw.get("depth", 0),
            "pass": raw.get("pass", 0),
            "disclosure_level": raw.get("disclosure_level", "standard"),
            "triangle_reason": raw.get("triangle_reason", "CLEAN"),
            "wit": raw.get("wit"),
            "language_mode": raw.get("language_mode"),
            "social": raw.get("social", {}),
            "dejavu": raw.get("dejavu", {"count": 0, "frequency": 0, "similarity": "none"}),
            "baseline": raw.get("baseline", {}),
            "baseline_used": raw.get("baseline_used", False),
            "domain_annotations": raw.get("domain_annotations", {}),
            "soi_domains": raw.get("soi_domains", []),
            "curiosity_context": raw.get("curiosity_context", ""),
            "conversation_health": raw.get("conversation_health", 100),
            "memory_polaroid": raw.get("memory_polaroid"),
            "turn_count": self.turn_count,
            "user_name": self.user_name,
            "whosonfirst": self.whosonfirst,
            "library_metadata": {
                "total_domains": self.library_metadata.total_domains,
                "files_loaded": len(self.library_metadata.files),
                "boole_substrate": self.library_metadata.boole_substrate,
                "core_tracks": self.library_metadata.core_tracks,
            },
        }
        # Track response history for recall + clarification fast paths
        result_text = final.get("result", "")
        if result_text:
            self._response_history.append(result_text)
            if len(self._response_history) > 20:
                self._response_history.pop(0)
        return final


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
    print(f"✓ Constitution: {'Loaded' if guvna.self_state.constitution_loaded else 'Using defaults'}")
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
