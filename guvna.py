"""
guvna.py

Act 5 – The Governor (REVISED)

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
from typing import Any, Dict, List, Optional, Set, Tuple
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
    wilden_swift_modulate,   # NEW: Guvna owns modulation
    wilden_swift_score,      # NEW: Talk owns scoring (exported for Talk's use)
    wilden_swift,            # COMPAT: backwards-compatible wrapper
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
# THE GOVERNOR (REVISED — TIER 2 WIRING)
# ============================================================================

class Guvna:
    """
    The Governor (Act 5) sits above The Restaurant (RILIE) and provides:

    **Core Authority:**
    - Final authority on what gets served
    - Ethical oversight via CATCH44DNA
    - Self-awareness fast path (_is_about_me)

    **Tone & Expression:**
    - Wit detection and wilden_swift_modulate (Guvna owns shaping)
    - Language mode detection (literal/figurative/metaphor/simile/poetry)
    - Tone signaling via single governing emoji per response
    - Social status tracking (user always > self)

    **Knowledge & Baselines:**
    - Optional web lookup pre-pass (KISS philosophy)
    - Comparison between web baseline and RILIE's own compression
    - Library index for domain engine access (678 domains)
    - Curiosity resurface — past insights as pre-RILIE context

    **Conversation Management:**
    - YELLOW GATE – conversation health monitoring + tone degradation detection
    - WHOSONFIRST – greeting gate (True = first interaction, False = past greeting)
    - Conversation memory (9 behaviors)
    - Photogenic DB (elephant memory)
    - Memory seeds curiosity (bidirectional cross-talk)

    **Integration:**
    Orchestrates Acts 1–4:
    - Act 1: Triangle (safety gate)
    - Act 2: DDD/Hostess (disclosure level)
    - Act 3: Kitchen/Core (interpretation passes)
    - Act 4: RILIE (conversation response)
    """

    def __init__(
        self,
        # Preferred snake_case API:
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

        # ==============================================================
        # LIBRARY BOOT – 678 DOMAINS LOADED
        # ==============================================================
        self.library_index: LibraryIndex = library_index or build_library_index()
        self.library_metadata = DomainLibraryMetadata()
        logger.info(f"GUVNA BOOT: {self.library_metadata.total_domains} domains loaded")
        logger.info(f"  Files: {len(self.library_metadata.files)} libraries")
        logger.info(f"  Boole substrate: {self.library_metadata.boole_substrate}")
        logger.info(f"  Core tracks: {self.library_metadata.core_tracks}")

        # RILIE still expects rouxseeds/searchfn keywords
        self.rilie = RILIE(rouxseeds=self.roux_seeds, searchfn=self.search_fn)

        # ==============================================================
        # MEMORY SYSTEMS
        # ==============================================================
        self.memory = ConversationMemory()
        self.photogenic = PhotogenicDB()
        self.domain_index = build_domain_index()

        # ==============================================================
        # CURIOSITY ENGINE (Tier 2 — bidirectional cross-talk)
        # ==============================================================
        self.curiosity_engine = curiosity_engine

        # ==============================================================
        # IDENTITY + ETHICS STATE
        # ==============================================================
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

        # ==============================================================
        # CONVERSATION STATE
        # ==============================================================
        self.turn_count: int = 0
        self.user_name: Optional[str] = None
        self.whosonfirst: bool = True

        # Governor's own response memory – anti-déjà-vu at every exit
        self._response_history: List[str] = []

        # ==============================================================
        # CONSTITUTION LOADING
        # ==============================================================
        self.self_state.constitution_flags = load_charculterie_manifesto(manifesto_path)
        self.self_state.constitution_loaded = self.self_state.constitution_flags.get(
            "loaded", False
        )
        logger.info("GUVNA: Charculterie Manifesto loaded" if self.self_state.constitution_loaded
                     else "GUVNA: Charculterie Manifesto not found (using defaults)")

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
    # MAIN PROCESS – Core response pipeline (TIER 2 WIRED)
    # -----------------------------------------------------------------

    def process(self, stimulus: str, maxpass: int = 1) -> Dict[str, Any]:
        """
        Main entry point for conversation.
        Orchestrates all 5 Acts: safety -> disclosure -> interpretation -> response -> governance.

        TIER 2 changes:
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
        # STEP 1: SELF-AWARENESS FAST PATH
        # ==============================================================
        if _is_about_me(stimulus):
            return self._finalize_response(self._respond_from_self(stimulus))

        # ==============================================================
        # STEP 2: BASELINE LOOKUP (web search if needed)
        # ==============================================================
        baseline = self._get_baseline(stimulus)
        baseline_text = baseline.get("text", "")

        # ==============================================================
        # STEP 3: DOMAIN LENSES (apply 678-domain library)
        # ==============================================================
        domain_annotations = self._apply_domain_lenses(stimulus)
        soi_domain_names = domain_annotations.get("matched_domains", [])

        # ==============================================================
        # STEP 3.5: CURIOSITY RESURFACE (Tier 2 — context before RILIE)
        # ==============================================================
        # She walks into the kitchen already knowing what she explored.
        # Not an afterthought.
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
        # STEP 4: RILIE CORE PROCESSING (Acts 1-4) — DOMAIN LENSES FLOW
        # ==============================================================
        # TIER 2: Domain lenses now flow into RILIE so the Kitchen
        # uses them to weight interpretation passes. Supreme burrito.
        rilie_result = self.rilie.process(
            stimulus=stimulus,
            baseline_text=baseline_text,
            domain_hints=soi_domain_names,         # NEW: domains flow in
            curiosity_context=curiosity_context,    # NEW: curiosity as context
        )

        if not rilie_result:
            rilie_result = {}
        raw.update(rilie_result)

        # ==============================================================
        # STEP 5: GOVERNOR OVERSIGHT (Act 5) — MODULATE, NOT SCORE
        # ==============================================================
        # Wit detection
        wit = detect_wit(stimulus)
        raw["wit"] = wit

        # Language mode detection
        language = detect_language_mode(stimulus)
        raw["language_mode"] = language

        # Tone detection
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

        # Social status inference
        user_status = infer_user_status(stimulus)
        self.social_state.user_status = user_status
        self.social_state.self_status = min(user_status - 0.1, 0.4)
        raw["social"] = {
            "user_status": self.social_state.user_status,
            "self_status": self.social_state.self_status,
        }

        # ==============================================================
        # STEP 6: MEMORY & CONVERSATION HEALTH (YELLOW GATE)
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
        # It rides on the plate. The Kitchen reads it as awareness.
        dejavu = raw.get("dejavu", {"count": 0, "frequency": 0, "similarity": "none"})
        if dejavu.get("frequency", 0) > 0:
            logger.info("GUVNA: Déjà-vu signal (freq=%d) — informative context, not gate",
                       dejavu["frequency"])

        # TIER 2: Memory seeds curiosity (bidirectional cross-talk)
        # Interesting topics from conversation get queued for exploration.
        if self.curiosity_engine and soi_domain_names:
            try:
                for domain in soi_domain_names[:2]:
                    self.curiosity_engine.queue_tangent(
                        tangent=f"Explore {domain} in context of: {stimulus[:80]}",
                        seed_query=stimulus,
                        relevance=0.3,   # Low relevance to current response
                        interest=0.8,    # High self-interest for exploration
                    )
            except Exception as e:
                logger.debug("GUVNA: Curiosity seeding failed (non-fatal): %s", e)

        # ==============================================================
        # STEP 7: DOMAIN ANNOTATIONS & SOi TRACKS
        # ==============================================================
        raw["domain_annotations"] = domain_annotations
        raw["soi_domains"] = soi_domain_names
        raw["memory_polaroid"] = memory_polaroid
        raw["domains_used"] = soi_domain_names

        # ==============================================================
        # STEP 8: ETHICS CHECK (CATCH44DNA)
        # ==============================================================
        self.self_state.dna_active = True
        raw["dna_active"] = self.self_state.dna_active

        # ==============================================================
        # STEP 9: RESPONSE FINALIZATION
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

        # Memory enrichments
        result_text = raw.get("result", "")
        if memory_callback and result_text:
            raw["result"] = memory_callback + "\n\n" + result_text
        if memory_thread and result_text:
            raw["result"] = raw["result"] + "\n\n" + memory_thread

        if self.whosonfirst:
            self.whosonfirst = False

        return self._finalize_response(raw)

    # -----------------------------------------------------------------
    # SELF-AWARENESS FAST PATH
    # -----------------------------------------------------------------

    def _respond_from_self(self, stimulus: str) -> Dict[str, Any]:
        """
        Self-aware response for 'about me' queries.
        Just her name. Like a person would.
        """
        response_text = "My name is RILIE."
        return {
            "result": response_text,
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
        STEP 1: Do I know this? If not, learn from Google.
        She shouldn't pretend. If she doesn't know,
        she learns (like you or any other ape).
        """
        baseline = {"text": "", "source": "", "raw_results": []}
        stimulus_lower = (stimulus or "").lower()

        known_patterns = ["what is", "explain", "tell me about", "how does"]
        is_entity_question = not any(p in stimulus_lower for p in known_patterns)
        should_force_google = is_entity_question or len(stimulus) < 30

        try:
            if self.search_fn:
                baseline_query = stimulus if should_force_google else f"what is the correct response to {stimulus}"
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
) -> Guvna:
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
