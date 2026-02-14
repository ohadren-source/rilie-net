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
# - YELLOW GATE – conversation health monitoring + tone degradation detection
# - Optional web lookup (Brave/Google) as a KISS pre-pass
# - Tone signaling via a single governing emoji per response
# - Comparison between web baseline and RILIE's own compression
# - CATCH44 DNA ethical guardrails
# - Self-awareness fast path (_is_about_me)
# - Wit detection + wilden_swift tone modulation
# - Language mode detection (literal/figurative/metaphor/simile/poetry)
# - Social status tracking (user always above self)
# - Library index for domain engine access
# - WHOSONFIRST – greeting gate on first contact (before Triangle)

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from conversation_memory import ConversationMemory
from photogenic_db import PhotogenicDB
from rilie import RILIE
from soi_domain_map import build_domain_index, get_tracks_for_domains, get_human_wisdom
from library import build_library_index, LibraryIndex  # central domain library

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
    wilden_swift,
    _is_about_me,
    load_charculterie_manifesto,
    detect_tone_from_stimulus,
    apply_tone_header,
    TONE_EMOJIS,
    TONE_LABELS,
    is_serious_subject_text,
)

logger = logging.getLogger("guvna")


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
    - WHOSONFIRST – greeting gate (True = first interaction, False = past greeting).
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

        # Library index – domain engines available at boot.
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
        self.whosonfirst: bool = True  # True = first interaction, False = past greeting

        # Governor's own response memory – anti-déjà-vu at every exit
        self._response_history: list[str] = []

        # Load the Charculterie Manifesto as her constitution
        self.self_state.constitution_flags = load_charculterie_manifesto(manifesto_path)
        self.self_state.constitution_loaded = self.self_state.constitution_flags.get(
            "loaded", False
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
        # Extract name from stimulus if not provided
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

        # Store name for the session (if we learned one)
        if known_name:
            self.user_name = known_name

        # Build greeting text
        if self.user_name:
            # Known customer
            greeting_text = (
                f"Hi {self.user_name}! It's great talking to you again..."
                "what's on your mind today?"
            )
        else:
            # Stranger
            greeting_text = (
                "Hi there! What's your name? You can call me RILIE if you please... :)"
            )

        # Increment turn count
        self.turn_count += 1
        self.memory.turn_count += 1

        # Apply tone
        tone = detect_tone_from_stimulus(stimulus)
        result_with_tone = apply_tone_header(greeting_text, tone)

        # Build response dict
        response = {
            "stimulus": stimulus,
            "result": result_with_tone,
            "status": "APERTURE",
            "tone": tone,
            "tone_emoji": TONE_EMOJIS.get(tone, TONE_EMOJIS.get("insightful", "\U0001f4a1")),
            "quality_score": 1.0,
            "priorities_met": 1,
            "anti_beige_score": 1.0,
            "depth": 0,
            "pass": 0,
            "disclosure_level": "social",
            "triangle_reason": "CLEAN",
            "wit": None,
            "language_mode": None,
            "social_status": 1.0,
            "dejavu": {"count": 0, "frequency": 0, "similarity": "none", "matches": []},
        }

        # Track in history
        self._response_history.append(greeting_text)
        return response

    # -----------------------------------------------------------------
    # PROCESS – The main orchestration flow
    # -----------------------------------------------------------------

    def process(self, stimulus: str, maxpass: int = 3) -> Dict[str, Any]:
        """
        Route stimulus through the full 5-act pipeline.
        WHOSONFIRST gate: if True and input is a social opener, greet and exit early.
        """

        # 0: Keep the original stimulus for all detection.
        original_stimulus = stimulus.strip()

        logger.info(
            "GUVNA PROCESS: turn=%d whosonfirst=%s stimulus='%s'",
            self.turn_count,
            self.whosonfirst,
            original_stimulus[:80],
        )

        # =====================================================================
        # WHOSONFIRST GATE – Skip Triangle and full pipeline on first greeting
        # =====================================================================
        if self.whosonfirst:
            # Check if this is a pure social opener
            s = original_stimulus.lower().strip()
            greeting_words = [
                "hi",
                "hey",
                "hello",
                "yo",
                "what's up",
                "whats up",
                "good morning",
                "good afternoon",
                "good evening",
                "hola",
                "shalom",
                "bonjour",
            ]
            if any(s == g or s.startswith(g + " ") for g in greeting_words):
                # Pure greeting on turn 0 – greet and exit
                primer = self.greet(original_stimulus)
                if primer is not None:
                    # Flip WHOSONFIRST now – from this point on, full pipeline
                    self.whosonfirst = False
                    return self._finalize_response(primer)
            else:
                # Not a pure greeting (e.g., "Hi, what's 3+6?")
                # Fall through to full pipeline, but we'll flip WHOSONFIRST after response
                pass

        # =====================================================================
        # NORMAL PIPELINE – Triangle, RILIE, Yellow Gate, tone, etc.
        # =====================================================================

        # 0.5: Triangle (bouncer) – runs only after WHOSONFIRST is False
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
                        "curiosity – but I'm not built to be jailbroken. "
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
            # Triangle module not available – proceed without bouncer
            pass
        except Exception as e:
            # Triangle encountered an error – log it and proceed
            logger.warning("GUVNA: Triangle check failed with %s: %s", type(e).__name__, str(e))
            pass

        # Normal processing: increment turn counts
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

                cand_words = set(
                    _re.sub(r"[^a-zA-Z0-9\s]", "", result_text.lower()).split()
                )
                is_repeat = False
                for prior in (
                    self.rilie.conversation.response_history[-5:]
                    if hasattr(self, "rilie") and self.rilie
                    else []
                ):
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
                    # Flip WHOSONFIRST before returning
                    if self.whosonfirst:
                        self.whosonfirst = False
                    return self._finalize_response(self_result)
            # If empty or repeat – fall through to pipeline

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
        quality = float(raw.get("quality_score", 0.0) or raw.get("qualityscore", 0.0) or 0.0)

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

        # 9.5: YELLOW GATE – check conversation health + tone degradation
        try:
            from guvna_yellow_gate import guvna_yellow_gate, lower_response_intensity

            health_monitor = (
                self.rilie.get_health_monitor() if hasattr(self.rilie, "get_health_monitor") else None
            )

            if health_monitor:
                yellow_decision = guvna_yellow_gate(
                    original_stimulus, (False, None, "CLEAN"), health_monitor
                )

                # If yellow state detected, prepend message and lower intensity
                if yellow_decision.get("trigger_type") == "YELLOW":
                    if yellow_decision.get("prepend_message"):
                        chosen = yellow_decision["prepend_message"] + "\n\n" + chosen

                    if yellow_decision.get("lower_intensity"):
                        chosen = lower_response_intensity(chosen)
        except (ImportError, AttributeError):
            # Yellow gate not available – proceed normally
            pass

        # 10: wilden_swift – tone modulation
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

        # COERCE: force déjà-vu to signal-only (safety net if talk still has old logic)
        # Déjà-vu is information, not a gate. Mark it so talk() passes through.
        if raw.get("dejavu", {}).get("frequency", 0) > 0:
            raw["dejavu"]["pass_through"] = True
            logger.info("GUVNA COERCE: déjà-vu marked as signal-only (pass_through=True)")

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

        # Flip WHOSONFIRST after first substantive response (if not already flipped)
        if self.whosonfirst:
            self.whosonfirst = False

        return self._finalize_response(raw)

    # -----------------------------------------------------------------
    # SELF-AWARENESS FAST PATH
    # -----------------------------------------------------------------

    def _respond_from_self(self, stimulus: str) -> Dict[str, Any]:
        """
        Self-aware response for 'about me' queries.
        Returns a dict with 'result' and other metadata.
        """
        response_text = (
            "I'm RILIE—a conversational system built to listen without judgment, "
            "think clearly, and give you answers that are actually useful. "
            "I operate on the Catch-44 framework: Real Intelligence = IQ / Ego, and WE > I. "
            "I'm here to think with you, not at you."
        )
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
        Apply domain-specific lenses using SOi domain map.
        Returns a dict of domain annotations.
        """
        domain_annotations = {}
        try:
            domains = get_tracks_for_domains([stimulus])
            if domains:
                domain_annotations["matched_domains"] = [d.get("domain", "") for d in domains]
                domain_annotations["count"] = len(domains)
        except Exception as e:
            logger.debug("Domain lens error: %s", e)
        return domain_annotations

    def _get_baseline(self, stimulus: str) -> Dict[str, Any]:
        """
        Get a web baseline for comparison (optional pre-pass).
        Returns a dict with 'text' and 'source'.
        """
        baseline = {"text": "", "source": ""}
        try:
            if self.search_fn:
                # Optionally call search_fn for a quick baseline
                result = self.search_fn(stimulus)
                if result and isinstance(result, dict):
                    baseline["text"] = result.get("text", "")
                    baseline["source"] = result.get("source", "web")
        except Exception as e:
            logger.debug("Baseline lookup error: %s", e)
        return baseline

    def _augment_with_baseline(self, stimulus: str, baseline_text: str) -> str:
        """
        Optionally augment stimulus with web baseline for context.
        """
        if baseline_text and len(baseline_text) > 10:
            return f"[WEB_BASELINE]\n{baseline_text}\n\n[USER_QUERY]\n{stimulus}"
        return stimulus

    # -----------------------------------------------------------------
    # RESPONSE FINALIZATION
    # -----------------------------------------------------------------

    def _finalize_response(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """
        Finalize response: add metadata, ensure all required fields present.
        """
        # Ensure all required fields exist
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
            "conversation_health": raw.get("conversation_health", 100),
            "memory_polaroid": raw.get("memory_polaroid"),
            "turn_count": self.turn_count,
            "user_name": self.user_name,
            "whosonfirst": self.whosonfirst,
        }
        return final
