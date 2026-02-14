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

        # Governor's own response memory – anti-déjà-vu at every exit
        self._response_history: list[str] = []

        # Load the Charculterie Manifesto as her constitution
        self.self_state.constitution_flags = load_charculterie_manifesto(manifesto_path)
        self.self_state.constitution_loaded = self.self_state.constitution_flags.get(
            "loaded", False
        )

    def _finalize_response(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """
        GOVERNOR'S FINAL GATE – runs on EVERY response before it leaves.
        Déjà-vu is tracked as SIGNAL, not blocked.
        Exposes: word overlap, frequency, similarity (variation vs literal).
        What to do with it is up to caller.
        """
        import re as _re
        
        final_text = raw.get("result", "")
        dejavu_info = {
            "count": 0,
            "frequency": 0,
            "similarity": "none",
            "matches": []
        }
        
        if final_text and len(self._response_history) > 0:
            cand_words = set(_re.sub(r"[^a-zA-Z0-9\s]", "", final_text.lower()).split())
            
            if len(cand_words) > 3:
                overlap_matches = []
                
                for i, prior in enumerate(self._response_history[-5:]):
                    prior_words = set(_re.sub(r"[^a-zA-Z0-9\s]", "", prior.lower()).split())
                    if not prior_words:
                        continue
                    
                    overlap = len(cand_words & prior_words)
                    
                    if overlap >= 3:  # Aminimum: 3+ word overlap = signal
                        overlap_matches.append({
                            "response": prior[:60] + ("..." if len(prior) > 60 else ""),
                            "overlap": overlap,
                            "turn": len(self._response_history) - 5 + i,
                            "total_words_prior": len(prior_words),
                            "total_words_candidate": len(cand_words),
                        })
                
                if overlap_matches:
                    # Calculate similarity: overlap / min(prior, candidate) = how much of shorter text is repeated
                    best_match = max(overlap_matches, key=lambda x: x["overlap"])
                    similarity_pct = (best_match["overlap"] / min(best_match["total_words_prior"], best_match["total_words_candidate"])) * 100
                    
                    dejavu_info["count"] = best_match["overlap"]
                    dejavu_info["matches"] = overlap_matches
                    
                    # Classify: variation (low overlap%) vs literal (high overlap%)
                    if similarity_pct >= 70:
                        dejavu_info["similarity"] = "literal"  # >70% same words = near-verbatim
                    elif similarity_pct >= 40:
                        dejavu_info["similarity"] = "thematic"  # 40-70% = similar idea, different words (jazz variation)
                    else:
                        dejavu_info["similarity"] = "resonance"  # <40% = just echoing some themes
                    
                    # Count frequency: how many times has this pattern appeared?
                    frequency = len(overlap_matches)
                    dejavu_info["frequency"] = frequency
                    
                    logger.info(
                        "GOVERNOR DEJAVU SIGNAL: count=%d freq=%d similarity=%s",
                        dejavu_info["count"],
                        dejavu_info["frequency"],
                        dejavu_info["similarity"]
                    )

        # Append to history (never block, always track)
        out_text = raw.get("result", "")
        if out_text and out_text.strip():
            self._response_history.append(out_text)
        
        raw["dejavu"] = dejavu_info
        return raw

    # -----------------------------------------------------------------
    # Social primer – warmth first, then pipeline
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
                idx = s.index(intro) + len(intro)
                rest = stimulus[idx:].strip().split()[0] if idx < len(stimulus) else ""
                name = rest.strip(".,!?;:'\"")
                if name and len(name) > 1:
                    self.user_name = name.capitalize()

        # Turn 1: Pure warmth
        if self.turn_count == 0:
            if self.user_name:
                # Name known – welcome back
                text = f"Hey {self.user_name}. Welcome back. What's on your mind?"
            elif is_greeting:
                # Greeting, no name – introduce herself, ask their name
                text = "Hi there, what's your name? You can call me RILIE if you so please... :)"
            else:
                # They jumped straight to a question – respect that, skip primer
                return None

            return self._primer_response(stimulus, text)

        # Turn 2: Light acknowledgment, start engaging
        if self.turn_count == 1:
            if is_greeting:
                if self.user_name:
                    text = f"Good to have you here, {self.user_name}. What can I help you think through?"
                else:
                    text = "Good to have you here. What can I help you think through?"
                return self._primer_response(stimulus, text)
            # They said something substantive – skip to pipeline
            return None

        # Turn 3: One more soft beat if they're still casual
        if self.turn_count == 2 and is_greeting:
            text = "I'm here. Ready when you are."
            return self._primer_response(stimulus, text)

        # EMERGENCY PROTOCOL: detect critical keywords
        emergency_keywords = ["help", "emergency", "error", "broken", "crash", "fail"]
        is_emergency = any(kw in s for kw in emergency_keywords)
        if is_emergency and self.turn_count < 5:
            emergency_responses = [
                "I see the issue. What's the full context?",
                "Tell me more. I'm tracking.",
                "Got it. Let's work through this step by step."
            ]
            idx = min(self.turn_count - 3, len(emergency_responses) - 1)
            text = emergency_responses[max(0, idx)]
            return self._primer_response(stimulus, text)

        # GOODBYE: detect exit signals
        goodbye_keywords = ["bye", "goodbye", "see you", "later", "peace", "out", "gotta go", "gtg"]
        is_goodbye = any(s.startswith(kw) or kw in s for kw in goodbye_keywords)
        if is_goodbye:
            goodbye_responses = [
                "Follow that thread. It goes somewhere.",
                "Until next time.",
                "Stay sharp."
            ]
            idx = min(self.turn_count % 3, len(goodbye_responses) - 1)
            text = goodbye_responses[idx]
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
        When the user is talking about RILIE, she reflects – but from the
        WINDOW, not the kitchen. Public-facing identity only.
        Serve the meal. Never release the recipe.
        """
        import random

        ss = self.self_state
        s = stimulus.lower()

        # Public-facing identity responses
        if any(
            w in s
            for w in [
                "who are you",
                "what are you",
                "tell me about",
                "describe yourself",
                "introduce yourself",
                "what's your name",
                "what is your name",
            ]
        ):
            result_text = "Hi there, what's your name? You can call me RILIE if you so please... :)"

        elif any(
            w in s
            for w in ["you failed", "you missed", "you can't", "you don't", "you didn't", "wrong"]
        ):
            result_text = (
                "Fair point. If I missed something, that's on me, not you. "
                "Point me closer and I'll do better."
            )

        elif any(
            w in s
            for w in [
                "do you feel",
                "are you happy",
                "do you care",
                "are you conscious",
                "do you have feelings",
            ]
        ):
            result_text = (
                "I care about getting it right. About earning the answer, "
                "not performing one. Whether that's 'feeling' – "
                "I'll leave that to you to decide."
            )

        elif any(
            w in s
            for w in [
                "how do you work",
                "what's under the hood",
                "what technology",
                "what model",
                "what are you built on",
                "how were you made",
            ]
        ):
            result_text = (
                "I think through questions using a few different lenses – "
                "kind of like how a chef uses different techniques depending "
                "on the ingredient. Beyond that, I'd rather show you than tell you. "
                "Ask me something real."
            )

        elif any(
            w in s
            for w in [
                "what can you do",
                "are you capable",
                "what are you good at",
            ]
        ):
            result_text = (
                "I'm good at helping you think through things you haven't "
                "fully figured out yet. Not homework answers – actual understanding. "
                "Try me."
            )

        else:
            # No specific self-reference matched. Don't produce a canned response.
            # Return empty – let her generate through the pipeline.
            result_text = ""

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
            # DNA violation on self-reflection – return empty, force pipeline
            result_text = ""
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
            tags = domain_info.get("tags", []) or []

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

            # Domain matched and DNA approved – record for RILIE.
            entrypoints = domain_info.get("entrypoints", {}) or {}

            annotations[domain_name] = {
                "matched": True,
                "tags": list(tags),
                "functions": list(entrypoints.keys()),
            }

        return annotations

    # -----------------------------------------------------------------
    # Web baseline
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
        except Exception:  # noqa: BLE001
            return {"title": "", "snippet": "", "link": "", "text": ""}

        if not results:
            return {"title": "", "snippet": "", "link": "", "text": ""}

        top = results[0] or {}
        title = (top.get("title") or "").strip()
        snippet = (top.get("snippet") or "").strip()
        link = (top.get("link") or "").strip()

        pieces: list[str] = []
        if title:
            pieces.append(title)
        if snippet:
            pieces.append(snippet)
        text = " – ".join(pieces) if pieces else ""

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
    # MAIN PROCESS – the full 5-act pipeline with new layers
    # -----------------------------------------------------------------

    def process(self, stimulus: str, maxpass: int = 3) -> Dict[str, Any]:
        """
        Route stimulus through the full 5-act pipeline.
        """

        # 0: Keep the original stimulus for all detection.
        original_stimulus = stimulus.strip()

        logger.info("GUVNA PROCESS: turn=%d stimulus='%s'", self.turn_count, original_stimulus[:80])

        # 0.25: Social primer – 9 phrases only (3 hello, 3 goodbye, 3 emergency)
        primer_result = self._social_primer(original_stimulus)
        if primer_result is not None:
            logger.info("GUVNA: _social_primer fired, status=%s", primer_result.get("status"))
            self.memory.turn_count += 1
            self.turn_count += 1
            tone = detect_tone_from_stimulus(original_stimulus)
            primer_result["result"] = apply_tone_header(primer_result["result"], tone)
            primer_result["tone"] = tone
            primer_result["tone_emoji"] = TONE_EMOJIS.get(tone, TONE_EMOJIS.get("insightful", "\U0001f4a1"))
            return self._finalize_response(primer_result)

        # 0.5: Triangle (bouncer) – runs BEFORE self-awareness.
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
            # Triangle not available – proceed without bouncer
            pass

        # 0.75a: primer/goodbye handled by _social_primer only (9 phrases).
        # conversation_memory primer/goodbye DISABLED – no script leaks.

        # Normal processing turn increments
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
                cand_words = set(_re.sub(r"[^a-zA-Z0-9\s]", "", result_text.lower()).split())
                is_repeat = False
                for prior in (self.rilie.conversation.response_history[-5:]
                              if hasattr(self, 'rilie') and self.rilie else []):
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
        quality = float(
            raw.get("quality_score", 0.0)
            or raw.get("qualityscore", 0.0)
            or 0.0
        )

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
            
            health_monitor = self.rilie.get_health_monitor() if hasattr(self.rilie, 'get_health_monitor') else None
            
            if health_monitor:
                yellow_decision = guvna_yellow_gate(
                    original_stimulus,
                    (False, None, "CLEAN"),  # Triangle already checked above
                    health_monitor
                )
                
                # If yellow state detected, prepend message and lower intensity
                if yellow_decision.get('trigger_type') == 'YELLOW':
                    if yellow_decision.get('prepend_message'):
                        chosen = yellow_decision['prepend_message'] + '\n\n' + chosen
                    
                    if yellow_decision.get('lower_intensity'):
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

        return self._finalize_response(raw)
