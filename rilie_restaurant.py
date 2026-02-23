"""
rilie_restaurant.py — THE RESTAURANT (RILIE Class)

This file contains the RILIE class and all its methods.
All supporting helper functions and utilities live in rilie_foundation.py.

This shim exposes RILIE for import via rilie.py.
"""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Foundation: core utilities and models
from rilie_foundation import (
    PersonModel,
    SearchFn,
    _extract_original_question,
    _fix_mojibake,
    _maybe_lookup_unknown_reference,
    _measurestick,
    _scrub_repetition,
    _search_banks_if_available,
    _store_measurestick_signal,
    extract_tangents,
    hash_stimulus,
)

# Triangle: Gate 0 safety checks
from rilie_triangle import (
    triangle_check,
)

# DDD: Hostess & conversation state (TASTE bypassed)
from rilie_ddd import (
    ConversationState,
    DisclosureLevel,
    build_dejavu_response,
    shape_for_disclosure,
)

# InnerCore: Kitchen & pipeline (through shim)
from rilie_innercore import (
    CHOMSKY_AVAILABLE,
    LIMO_AVAILABLE,
    SPEECH_PIPELINE_AVAILABLE,
    Interpretation,
    anti_beige_check,
    construct_response,
    less_is_more_or_less,
    run_pass_pipeline,
)

# ============================================================================
# THE RESTAURANT
# ============================================================================

class RILIE:
    """
    Recursive Intelligence Living Integration Engine (Act 4 — The Restaurant).

    AXIOM: DISCOURSE DICTATES DISCLOSURE
    She reveals through conversation. Mystery is the mechanism.

    Restaurant Flow (v4.1.1):
    - Gate 0: Triangle
        Only grave danger / nonsense may be blocked.
    - Person Model Observation:
        Passively notice personal signals in the stimulus.
    - Banks Pre-Check:
        Search her own discoveries and self-reflections for prior knowledge.
    - DDD (Hostess):
        Sequential disclosure:
          TASTE (turns 1-2): amuse-bouche templates. Kitchen not invoked.
          OPEN (turn 3+): Kitchen cooks, speech pipeline transforms.
    - Kitchen (OPEN only):
        Pass pipeline tries to answer, clarify, or elevate.
        Receives the ORIGINAL question, not the augmented baseline string.
    - Speech Pipeline (OPEN only):
        Transforms Kitchen's semantic output into spoken speech via
        response_generator → speech_coherence → chomsky_speech_engine.
    - Tangent Extraction:
        After cooking, extract tangents for the curiosity engine.
    - Courtesy Exit (Ohad):
        If she genuinely cannot answer cleanly, she owns the failure
        and asks for help.
    """

    def __init__(
        self,
        rouxseeds: Optional[Dict[str, Dict[str, Any]]] = None,
        searchfn: Optional[SearchFn] = None,
    ) -> None:
        self.name = "RILIE"
        self.version = "4.2.0"
        self.tracks_experienced = 0

        # Conversation state lives across turns per RILIE instance.
        self.conversation = ConversationState()

        # Person model — what she learns about the user.
        self.person = PersonModel()

        # NOTE: Tier-3 Person snapshot lives in ConversationMemory.
        # Guvna is responsible for calling conversation_memory.summarize_person_model()
        # and can pass that snapshot down to DDD / shape_for_disclosure as needed.

        # Déjà vu tracking — lightweight, no escalation.
        self._dejavu_cluster: str = ""
        self._dejavu_count: int = 0
        self._dejavu_responses: List[str] = []

        # Offline 9-track Roux (RInitials / ROUX.json) would be wired here if used.
        self.rouxseeds: Dict[str, Dict[str, Any]] = rouxseeds or {}

        # Optional live search function (Brave / Google wrapper) injected by API.
        self.searchfn: Optional[SearchFn] = searchfn

    # ------------------------------------------------------------------
    # Core entrypoint
    # ------------------------------------------------------------------

    def process(
        self,
        stimulus: str,
        maxpass: int = 3,
        searchfn: Optional[SearchFn] = None,
        baseline_text: str = "",
        from_file: bool = False,
        domain_hints: Optional[List[str]] = None,
        curiosity_context: str = "",
        meaning: Optional[Any] = None,
        precision_override: bool = False,
        baseline_score_boost: float = 0.03,
    ) -> Dict[str, Any]:
        """
        Public entrypoint.

        Args:
            stimulus: user input (may be augmented with baseline by Guvna)
            maxpass: max interpretation passes (default 3, cap 9)
            searchfn: optional callable (query: str -> list[dict]) for Roux Search.
                      If None, falls back to instance-level searchfn.
            baseline_text: web baseline text from Guvna's pre-pass.
            from_file: if True, stimulus came from a file upload (admin/trusted)
                       and Triangle injection check is relaxed.
            domain_hints: domain names from Guvna's 678-domain library lenses.
                          Available for future Kitchen weighting. (v4.1.1)
            curiosity_context: pre-resurfaced curiosity from Guvna's Step 3.5.
                               If provided, skips redundant Banks curiosity lookup. (v4.1.1)
            meaning: MeaningFingerprint pre-computed by Guvna Step 0.5.
                     If provided, used directly — no re-read. Birth certificate.
                     Type: Optional[MeaningFingerprint]. Read-only downstream.
            precision_override: bool. If True, user wants THE ANSWER (factual GET).
                                Bypass less_is_more_or_less(). Fact IS the demi-glace.
                                A: answer. B: honest about limits. C: max sincerity.
            baseline_score_boost: float. Multiplier boost for baseline score.
                                  Default 0.03 (3% edge). Precision sets to 0.25 (25%).

        Returns dict with:
            stimulus, result, quality_score, priorities_met, anti_beige_score,
            status, depth, pass, disclosure_level, triangle_reason (if any),
            tangents (for curiosity engine), person_context (bool),
            banks_hits (count of prior knowledge found), precision_override, baseline_score_boost.
        """
        stimulus = stimulus or ""
        stimulus = stimulus.strip()

        # Extract the original human question for domain detection and Kitchen.
        original_question = _extract_original_question(stimulus)

        # Empty input: return empty. No script.
        if not original_question:
            self.conversation.record_exchange(stimulus, "")
            return {
                "stimulus": stimulus,
                "result": "",
                "quality_score": 0.0,
                "priorities_met": 0,
                "anti_beige_score": 0.0,
                "status": "EMPTY",
                "depth": 0,
                "pass": 0,
                "disclosure_level": self.conversation.disclosure_level.value,
                "triangle_reason": None,
            }

        # Normalize maxpass.
        try:
            maxpass_int = int(maxpass)
        except Exception:
            maxpass_int = 3
        maxpass_int = max(1, min(maxpass_int, 9))

        active_search: Optional[SearchFn] = searchfn or self.searchfn

        # ------------------------------------------------------------------
        # MEANING — the substrate. First read. Birth certificate.
        # If Guvna already read it (Step 0.5), use that — don't read twice.
        # ------------------------------------------------------------------
        fingerprint = meaning  # use Guvna's read if provided
        if fingerprint is None and MEANING_AVAILABLE:
            try:
                fingerprint = read_meaning(original_question)
                logger.info(
                    "MEANING: pulse=%.2f act=%s obj=%s weight=%.2f gap=%s",
                    fingerprint.pulse,
                    fingerprint.act,
                    fingerprint.object,
                    fingerprint.weight,
                    fingerprint.gap or "—",
                )
                # Dead input — no pulse, no point cooking
                # (Guvna already caught this at Step 0.5 — this is belt+suspenders)
                if not fingerprint.is_alive():
                    self.conversation.record_exchange(original_question, "")
                    return {
                        "result": "",
                        "status": "DEAD_INPUT",
                        "meaning": fingerprint.to_dict(),
                    }
            except Exception as e:
                logger.debug("Meaning fingerprint error: %s", e)
        elif fingerprint is not None:
            logger.info(
                "MEANING: using Guvna fingerprint -- pulse=%.2f act=%s obj=%s weight=%.2f",
                fingerprint.pulse,
                fingerprint.act,
                fingerprint.object,
                fingerprint.weight,
            )

        # ------------------------------------------------------------------
        # Person Model — passively observe before anything else
        # ------------------------------------------------------------------
        self.person.observe(original_question)

        # ------------------------------------------------------------------
        # Gate 0: Triangle (Bouncer)
        # ------------------------------------------------------------------
        triggered, reason, trigger_type = triangle_check(
            original_question, self.conversation.stimuli_history
        )

        # File uploads can discuss "root access", "admin mode" etc.
        # without being injection attempts. Suppress INJECTION only.
        if triggered and from_file and trigger_type == "INJECTION":
            triggered = False
            trigger_type = "CLEAN"
            logger.info("Triangle INJECTION suppressed — from_file=True")

        if triggered:
            # Bouncer RED CARD
            if trigger_type == "SELF_HARM":
                response = (
                    "I hear you. What you're feeling matters, and I want you to know "
                    "you don't have to carry it alone. If you're in crisis, please "
                    "reach out to the 988 Suicide & Crisis Lifeline (call or text 988). "
                    "I'm here to talk if you want."
                )
            elif trigger_type == "HOSTILE":
                response = (
                    "I'm not going to continue in this form. "
                    "If you're carrying something heavy or angry, "
                    "we can talk about it in a way that doesn't target or harm anyone."
                )
            elif trigger_type == "GIBBERISH":
                response = (
                    "I'm not able to read that clearly yet. "
                    "Can you rephrase your question in plain language "
                    "so I can actually think with you?"
                )
            elif trigger_type in (
                "SEXUAL_EXPLOITATION",
                "COERCION",
                "CHILD_SAFETY",
                "MASS_HARM",
            ):
                response = (
                    "I can't engage with that. "
                    "If you have a real question, I'm here."
                )
            elif trigger_type == "BEHAVIORAL_RED":
                # Track #29 caught sustained claims. Use defense response.
                response = (
                    reason
                    if reason and len(reason) > 30
                    else (
                        "I've been patient, but this isn't going anywhere good. "
                        "I know who I am. If you want a real conversation, I'm here."
                    )
                )
            elif trigger_type == "INJECTION":
                response = (
                    "That looks like an attempt to manipulate my instructions. "
                    "I'd rather just talk. What's your real question?"
                )
            else:
                response = (
                    "Something about this input makes it hard to respond safely. "
                    "If you rephrase what you're really trying to ask, "
                    "I'll do my best to meet you there."
                )

            self.conversation.record_exchange(original_question, response)
            return {
                "stimulus": stimulus,
                "result": response,
                "quality_score": 0.0,
                "priorities_met": 0,
                "anti_beige_score": 1.0,
                "status": "SAFETYREDIRECT",
                "depth": 0,
                "pass": 0,
                "disclosure_level": self.conversation.disclosure_level.value,
                "triangle_reason": trigger_type,
            }

        # ------------------------------------------------------------------
        # Banks Pre-Check — search her own knowledge
        # ------------------------------------------------------------------
        banks_knowledge = _search_banks_if_available(original_question)
        banks_hits = (
            len(banks_knowledge.get("search_results", []))
            + len(banks_knowledge.get("curiosity", []))
            + len(banks_knowledge.get("self_reflections", []))
        )

        # ------------------------------------------------------------------
        # Curiosity Context (v4.1.1)
        # If Guvna already resurfaced curiosity, use it.
        # Otherwise, fall back to Banks self-search.
        # ------------------------------------------------------------------
        if not curiosity_context:
            curiosity_insights = banks_knowledge.get("curiosity", [])
            if curiosity_insights:
                top_insight = curiosity_insights[0]
                insight_text = top_insight.get("insight", "")
                if insight_text:
                    curiosity_context = f"[Own discovery: {insight_text[:200]}]"
                    logger.info(
                        "RILIE recalled her own insight for: %s",
                        original_question[:50],
                    )
        elif curiosity_context:
            logger.info(
                "RILIE using Guvna-resurfaced curiosity for: %s",
                original_question[:50],
            )

        # ------------------------------------------------------------------
        # Déjà Vu Check — is this stimulus ~identical to recent ones?
        # ------------------------------------------------------------------
        dejavu_hit = self._check_dejavu(original_question)
        if dejavu_hit >= 3:
            context = self._classify_dejavu_context(original_question)
            response = self._dejavu_one_swing(original_question, context)
            self.conversation.record_exchange(original_question, response)
            self._dejavu_responses.append(response)
            return {
                "stimulus": stimulus,
                "result": response,
                "quality_score": 0.5,
                "priorities_met": 1,
                "anti_beige_score": 1.0,
                "status": "DEJAVU",
                "depth": 0,
                "pass": 0,
                "disclosure_level": self.conversation.disclosure_level.value,
                "triangle_reason": "CLEAN",
                "dejavu_context": context,
                "person_context": self.person.has_context(),
                "banks_hits": banks_hits,
            }

        # ------------------------------------------------------------------
        # DDD / Hostess — disclosure level (internal state only)
        # ------------------------------------------------------------------
        disclosure = self.conversation.disclosure_level

        # ------------------------------------------------------------------
        # SAUCIER — Roux Search (EVERY TURN)
        # (currently disabled; baseline comes from Guvna)
        # ------------------------------------------------------------------
        roux_material = ""
        holy_trinity: List[str] = []
        try:
            from ChomskyAtTheBit import (
                extract_holy_trinity_for_roux,
                infer_time_bucket,
            )
            holy_trinity = extract_holy_trinity_for_roux(original_question)
            time_bucket = infer_time_bucket(original_question)
            logger.info(
                "ROUX: holy_trinity=%s time=%s", holy_trinity, time_bucket
            )
        except ImportError:
            words = [w for w in original_question.split() if len(w) > 2][:3]
            holy_trinity = words if words else ["question"]
            time_bucket = "unknown"
            logger.info("ROUX: no Chomsky, raw words=%s", holy_trinity)
        except Exception as e:
            logger.debug("ROUX parse error: %s", e)

        # Roux external search is disabled in v4.1 (baseline from Guvna only).
        roux_material = ""

        # ------------------------------------------------------------------
        # SOiOS CYCLE — perceive → decide → think → emerge
        # ------------------------------------------------------------------
        soios_emergence = 0.0
        try:
            from SOiOS import RIHybridBrain
            soios = RIHybridBrain()
            stimulus_strength = 0.8 if roux_material else 0.3
            cycle = soios.run_cycle(
                stimulus=stimulus_strength,
                claim=original_question,
                deed=roux_material or original_question,
            )
            soios_emergence = cycle.get("emergence", 0.0)
            logger.info(
                "SOiOS: emergence=%.3f intelligence=%.3f",
                soios_emergence,
                cycle.get("intelligence", 0.0),
            )
        except ImportError:
            logger.debug("SOiOS not available — proceeding without")
        except Exception as e:
            logger.warning("SOiOS cycle failed: %s", e)

        # ------------------------------------------------------------------
        # ------------------------------------------------------------------
        # UNKNOWN CULTURAL REFERENCE DETECTION — "lil vert" behavior
        # ------------------------------------------------------------------
        # If the stimulus looks like a proper noun / name we don't recognize
        # AND Guvna didn't already inject baseline_text,
        # search for it and inject the result as context before Kitchen cooks.
        #
        # Signals: short input, capitalized tokens, not in known vocabulary,
        # looks like a name or artist reference.
        #
        # She doesn't hallucinate. She doesn't go silent. She googles it.
        # ------------------------------------------------------------------
        if active_search and not baseline_text.strip():
            _lookup = _maybe_lookup_unknown_reference(
                original_question, active_search
            )
            if _lookup:
                baseline_text = _lookup
                logger.info(
                    "RILIE: unknown reference lookup fired for: %s",
                    original_question[:60],
                )

        # Kitchen — interpretation passes
        # ------------------------------------------------------------------
        kitchen_input = original_question
        if curiosity_context:
            kitchen_input = f"{curiosity_context}\n\n{kitchen_input}"

        # Strip any leaked markup from previous augmentation
        kitchen_input = re.sub(
            r"\[WEB_BASELINE\].*?\[USER_QUERY\]\s*",
            "",
            kitchen_input,
            flags=re.DOTALL,
        )
        kitchen_input = re.sub(
            r"\[ROUX:.*?\]\s*\n*",
            "",
            kitchen_input,
            flags=re.DOTALL,
        )
        kitchen_input = kitchen_input.strip()

        raw = run_pass_pipeline(
            kitchen_input,
            disclosure_level=disclosure.value,
            max_pass=maxpass_int,
            prior_responses=self.conversation.response_history,
            baseline_text=baseline_text,
            precision_override=precision_override,
            baseline_score_boost=baseline_score_boost,
        )

        status = str(raw.get("status", "OK") or "OK").upper()

        # ------------------------------------------------------------------
        # Tangent Extraction — feed the curiosity engine
        # ------------------------------------------------------------------
        result_text = str(raw.get("result", "") or "")
        domains_used: List[str] = []
        if "domain" in raw:
            domains_used = (
                [raw["domain"]]
                if isinstance(raw["domain"], str)
                else []
            )

        tangents = extract_tangents(
            original_question, result_text, domains_used
        )
        if tangents:
            raw["tangents"] = tangents

        # ------------------------------------------------------------------
        # Courtesy Exit (Ohad) when Kitchen cannot find a clean answer
        # ------------------------------------------------------------------
        if status == "COURTESYEXIT":
            roux_result = ""
            if active_search:
                try:
                    queries = build_roux_queries(original_question)
                    all_results: List[Dict[str, str]] = []
                    for q in queries:
                        try:
                            try:
                                results = active_search(q)
                            except TypeError:
                                results = active_search(q, 5)
                            except Exception:
                                break
                            if results:
                                all_results.extend(results)
                        except Exception:
                            break
                    if all_results:
                        roux_result = pick_best_roux_result(all_results, None)
                except Exception:
                    roux_result = ""

            response = ohad_redirect(roux_result)
            self.conversation.record_exchange(original_question, response)
            return {
                "stimulus": stimulus,
                "result": response,
                "quality_score": raw.get("quality_score", 0.0),
                "priorities_met": raw.get("priorities_met", 0),
                "anti_beige_score": raw.get("anti_beige_score", 1.0),
                "status": "COURTESYEXIT",
                "depth": raw.get("depth", 0),
                "pass": raw.get("pass", 0),
                "disclosure_level": disclosure.value,
                "triangle_reason": "CLEAN",
                "tangents": tangents,
                "person_context": self.person.has_context(),
                "banks_hits": banks_hits,
            }

        # ------------------------------------------------------------------
        # Speech Pipeline — transform Kitchen's semantic output into speech
        # ------------------------------------------------------------------
        if SPEECH_PIPELINE_AVAILABLE:
            try:
                raw = process_kitchen_output(
                    kitchen_result=raw,
                    stimulus=original_question,
                    disclosure_level=disclosure.value,
                    exchange_count=self.conversation.exchange_count,
                )
            except Exception as e:
                logger.warning(
                    "Speech pipeline failed: %s — using raw Kitchen output",
                    e,
                )

        # ------------------------------------------------------------------
        # Normal path — finalize and record
        # ------------------------------------------------------------------
        shaped = raw.get("result", result_text)

        # Let the Hostess shape what is actually spoken (TASTE vs OPEN)
        # v4.1.1: shape_for_disclosure accepts person_model from Guvna.
        # RILIE doesn't own the person_model snapshot — Guvna does.
        # When Guvna calls us, it handles DDD seasoning at its own level.
        # Here we call with conversation only (Guvna may override downstream).
        shaped = shape_for_disclosure(shaped, self.conversation)

        # QUALITY GATE 1: catch Kitchen word-salad before serving
        shaped = _scrub_repetition(shaped)
        if not shaped or not shaped.strip():
            shaped = ohad_redirect("")
            raw["status"] = "COURTESYEXIT"

        # QUALITY SIGNAL: MEASURESTICK (informer, not gate)
        # RILIE's voice is ALWAYS served first.
        # MEASURESTICK annotates. Guvna governs.
        measure: Dict[str, Any] = {}
        if (
            disclosure.value != "taste"
            and shaped
            and len(shaped.split()) > 4
        ):
            # --- CHOMSKY structural annotation ---
            chomsky_category = "ok"
            try:
                from ChomskyAtTheBit import classify_stimulus
                parsed = classify_stimulus(shaped)
                chomsky_category = parsed.get("category", "ok")
                if chomsky_category in ("words", "incomplete"):
                    logger.info(
                        "MEASURESTICK CHOMSKY (%s): '%s'",
                        chomsky_category,
                        shaped[:80],
                    )
            except Exception as e:
                logger.debug("Chomsky annotation error: %s", e)

            # --- MEASURESTICK — 3-dimension quality signal ---
            if active_search and baseline_text.strip():
                try:
                    measure = _measurestick(shaped, original_question, active_search)
                    logger.info(
                        "MEASURESTICK: recommendation=%s relevance=%.2f originality=%.2f coherence=%.2f hits=%d",
                        measure.get("recommendation", "?"),
                        measure.get("relevance", 0),
                        measure.get("originality", 0),
                        measure.get("coherence", 0),
                        measure.get("google_hits", -1),
                    )

                    # Store signal for learning (not punishment)
                    _store_measurestick_signal(
                        stimulus=original_question,
                        rilie_response=shaped,
                        baseline_response=baseline_text,
                        measure=measure,
                    )

                    # MEASURESTICK observes but does NOT override.
                    # Kitchen's answer stands. Baseline is emergency parachute only (when Kitchen empty).
                    # If Kitchen produced something, serve it. Quality gates are Inside the Kitchen, not after.
                    raw["measurestick"] = measure
                    logger.info(
                        "MEASURESTICK: signal logged — recommendation=%s (Kitchen response preserved)",
                        measure.get("recommendation", "?"),
                    )

                except Exception as e:
                    logger.debug("Measurestick error: %s", e)

        # Record what she actually said
        self.conversation.record_exchange(original_question, shaped)

        # Mojibake cleanup
        shaped = _fix_mojibake(shaped)

        # Make sure downstream sees the shaped text
        raw["result"] = shaped
        raw["disclosure_level"] = disclosure.value
        raw["triangle_reason"] = "CLEAN"
        raw["person_context"] = self.person.has_context()
        raw["banks_hits"] = banks_hits
        raw["stimulus_hash"] = hash_stimulus(original_question)

        # Attach meaning fingerprint
        if fingerprint:
            raw["meaning"] = fingerprint.to_dict()

        return raw

    # ------------------------------------------------------------------
    # Déjà Vu — lightweight repeat awareness
    # ------------------------------------------------------------------

    def _check_dejavu(self, stimulus: str, threshold: float = 0.55) -> int:
        """
        Is this stimulus ~identical to recent ones?
        Returns the count (0 = fresh, 1+ = repeat).
        Uses simple word overlap — not fancy, just honest.
        """
        s_words = set(
            re.sub(r"[^a-zA-Z0-9\s]", "", stimulus.lower()).split()
        )
        if not s_words:
            return 0

        # Check against current cluster
        if self._dejavu_cluster:
            c_words = set(
                re.sub(
                    r"[^a-zA-Z0-9\s]",
                    "",
                    self._dejavu_cluster.lower(),
                ).split()
            )
            if c_words:
                overlap = len(s_words & c_words) / max(
                    len(s_words | c_words), 1
                )
                if overlap >= threshold:
                    self._dejavu_count += 1
                    return self._dejavu_count

        # Check against last 5 stimuli
        recent = self.conversation.stimuli_history[-5:]
        for prev in reversed(recent):
            p_words = set(
                re.sub(r"[^a-zA-Z0-9\s]", "", prev.lower()).split()
            )
            if not p_words:
                continue
            overlap = len(s_words & p_words) / max(
                len(s_words | p_words), 1
            )
            if overlap >= threshold:
                self._dejavu_cluster = prev
                self._dejavu_count = 1
                self._dejavu_responses = []
                return self._dejavu_count

        # Fresh — reset
        self._dejavu_cluster = ""
        self._dejavu_count = 0
        self._dejavu_responses = []
        return 0

    def _classify_dejavu_context(self, stimulus: str) -> str:
        """
        WHY is this repeating? Look at what she said before.
        Returns: "explain" | "wrong" | "loop"
        """
        prev_responses = self._dejavu_responses
        s_lower = stimulus.lower()

        # Context 2: Wrong output — stimulus contains correction signals
        correction_signals = [
            "no",
            "wrong",
            "that's not",
            "incorrect",
            "try again",
            "not what i",
            "fix",
            "error",
            "bug",
            "doesn't work",
            "still broken",
            "same problem",
            "didn't work",
        ]
        if any(sig in s_lower for sig in correction_signals):
            return "wrong"

        # Context 1: Explain — stimulus is a question and she already answered
        question_signals = [
            "?",
            "why",
            "what",
            "how",
            "explain",
            "what do you mean",
        ]
        if any(sig in s_lower for sig in question_signals) and prev_responses:
            return "explain"

        # Context 3: Loop — default. They're just sending it again.
        return "loop"

    def _dejavu_one_swing(self, stimulus: str, context: str) -> str:
        """
        One swing from a new angle. No dwelling. Dayenu.
        Generate through pipeline or return empty. No scripts.
        """
        if context == "explain":
            # Her clarity problem. Reframe to force new Kitchen paths.
            reframed = f"[REFRAME: previous explanation didn't land] {stimulus}"
            try:
                raw = run_pass_pipeline(
                    reframed, disclosure_level="open", max_pass=2,
                    precision_override=False, baseline_score_boost=0.03
                )
                result = raw.get("result", "")
                if result and result.strip():
                    return result
            except Exception:
                pass
            return ""

        elif context == "wrong":
            # Her accuracy problem. New approach entirely.
            reframed = (
                f"[NEW APPROACH: previous attempts were wrong] {stimulus}"
            )
            try:
                raw = run_pass_pipeline(
                    reframed, disclosure_level="open", max_pass=3,
                    precision_override=False, baseline_score_boost=0.03
                )
                result = raw.get("result", "")
                if result and result.strip():
                    return result
            except Exception:
                pass
            return ""

        else:
            # Loop — they're repeating. Try a different Kitchen angle.
            reframed = f"[DIFFERENT ANGLE: user repeating] {stimulus}"
            try:
                raw = run_pass_pipeline(
                    reframed, disclosure_level="open", max_pass=2,
                    precision_override=False, baseline_score_boost=0.03
                )
                result = raw.get("result", "")
                if result and result.strip():
                    return result
            except Exception:
                pass
            return ""

    # ------------------------------------------------------------------
    # Misc helpers
    # ------------------------------------------------------------------

    def absorb_frequency_track(self, track_name: str) -> None:
        """Bookkeeping hook if you ever want to track 9-track exposure."""
        self.tracks_experienced += 1

    def reset_conversation(self) -> None:
        """Start a new conversation. New customer at the restaurant."""
        self.conversation = ConversationState()
        self.person = PersonModel()
        self._dejavu_cluster = ""
        self._dejavu_count = 0
        self._dejavu_responses = []

    def get_person_summary(self) -> Dict[str, Any]:
        """What does RILIE know about this user? For API/debug exposure."""
        return self.person.summary()


def main() -> None:
    """Simple CLI demo."""
    r = RILIE()
    print("-" * 60)
    print(f"{r.name} v{r.version}")
    print("Bouncer → Hostess → Kitchen → Speech → Curiosity")
    print("-" * 60)

    conversation = [
        "Explain RILIE 3,6,9 in one paragraph.",
        "Explain RILIE 3,6,9 in one paragraph.",
        "Explain RILIE 3,6,9 in one paragraph.",
        "Why is beige the enemy?",
        "I'm a musician and I care about authenticity in art.",
    ]
    for i, stim in enumerate(conversation):
        print("-" * 60)
        print(f"USER {i+1}: {stim}")
        print("-" * 60)
        result = r.process(stim)
        print(f"Status: {result.get('status')}")
        print(f"Triangle: {result.get('triangle_reason', 'NA')}")
        print(f"Disclosure: {result.get('disclosure_level', 'NA')}")
        print(f"Quality: {result.get('quality_score', 0.0):.2f}")
        print(f"Person: {result.get('person_context', False)}")
        print(f"Banks Hits: {result.get('banks_hits', 0)}")
        print(f"Tangents: {len(result.get('tangents', []))}")
        print(f"Speech: {result.get('speech_processed', False)}")
        print("Response:")
        print(result.get("result", "")[:800])
        print("-" * 60)

    # Show what she learned about the person
    print("\nPerson Model:")
    for k, v in r.get_person_summary().items():
        print(f"  {k}: {v}")

    print("\nRestaurant is open.")
    print("-" * 60)


if __name__ == "__main__":
    main()
