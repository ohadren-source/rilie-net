"""
guvna_self.py — SELF-GOVERNING SESSION AWARENESS

She knows what she just said. She knows who she's talking to.
She knows if she's been here before.

Extracted from guvna.py as a clean mixin.
Guvna inherits this. These functions don't work without it.

STATE OWNED HERE:
- _response_history : everything she's said this session (capped at 20)
- user_name         : who she's talking to
- _awaiting_name    : did she just ask for a name?
- turn_count        : how many turns deep are we?

NOTE: whosonfirst removed. The API owns the door. Guvna owns the kitchen.
RILIE is always greeted before Guvna sees a single stimulus.

BEHAVIORS OWNED HERE:
1. _handle_name_capture() — catch the name after she asked for it
2. _handle_recall()       — "what did you just say / what's my name"
3. _handle_clarification()— "what do you mean / say that differently"
4. _handle_meta_correction()— "forget that / never mind / drop it"
5. _finalize_response()   — THE WRITER. Every response gets logged here.
   Logs RAW result (pre-tone-header). History is clean.

WHY THIS FILE EXISTS:
guvna.py was doing too many things.
This is the part that makes her self-governing — not just smart.
Split it out. Keep it clean. Import it back.

Usage:
    class Guvna(GuvnaSelf, ...):
        ...
    GuvnaSelf.__init__(self) wires the state.
    All methods available on Guvna instance.
"""

from __future__ import annotations

import logging
import random
import re
from collections import deque
from typing import Any, Dict, List, Optional

from guvna_tools import (
    detect_tone_from_stimulus,
    apply_tone_header,
    TONE_EMOJIS,
)

# Less Is More Or Less + Precision Override — imported from rilie_innercore
try:
    from rilie_innercore import less_is_more_or_less
    LIMO_AVAILABLE = True
except ImportError:
    LIMO_AVAILABLE = False
    def less_is_more_or_less(text: str) -> str:  # type: ignore
        return text  # graceful degradation — transform unavailable

# Chomsky — the grammar brain. Used for name extraction (regex + spaCy NER).
try:
    from ChomskyAtTheBit import extract_customer_name as _chomsky_extract_name
    CHOMSKY_AVAILABLE = True
except ImportError:
    CHOMSKY_AVAILABLE = False
    def _chomsky_extract_name(stimulus: str) -> Optional[str]:  # type: ignore
        return None  # graceful degradation — Chomsky unavailable


logger = logging.getLogger("guvna_self")

DEFAULT_NAME = "Mate"

# ============================================================================
# GUVNA SELF — MIXIN
# ============================================================================

class GuvnaSelf:
    """
    Self-governing session-aware mixin for Guvna.

    Owns all state and behavior related to:
    - Who am I talking to?
    - What did I just say?
    - Did I ask for their name?

    Guvna inherits this. Do not instantiate directly.

    NOTE: Greeting (whosonfirst / greet()) has been removed.
    The API owns turn 0. Guvna wakes on turn 1 with the name already known.
    """

    def _init_self_state(self) -> None:
        """
        Call this from Guvna.__init__() to wire self-state.
        Guvna.__init__ must call:
            self._init_self_state()
        """
        self.turn_count: int = 0
        self.user_name: Optional[str] = None
        self._awaiting_name: bool = False
        self._response_history: deque = deque(maxlen=20)

    # -----------------------------------------------------------------
    # NAME CAPTURE — turn after she asked "what's your name?"
    # -----------------------------------------------------------------

    # Fallback lead-in phrases used ONLY when Chomsky is unavailable.
    # Ordered longest-first so "my name is" matches before "my".
    _NAME_LEAD_INS = [
        "my name is", "my name's", "the name is", "the name's",
        "they call me", "people call me", "you can call me",
        "call me", "i'm called", "i am called",
        "i go by", "just call me",
        "it's", "its", "it is",
        "i'm", "im", "i am",
        "this is", "hey i'm", "hi i'm",
        "hey it's", "hi it's",
        "hey im", "hi im",
        "pleasure", "nice to meet you",
    ]

    # Words that are never names
    _BAD_NAME_TOKENS = {
        "yes", "no", "ok", "okay", "sure", "hey", "hi", "hello",
        "thanks", "nah", "idk", "what", "huh", "nothing", "nevermind",
        "good", "fine", "great", "cool", "nice", "well",
        "introduce", "called", "myself", "allow", "please",
        "i", "me", "my", "am", "is", "are", "a", "an", "the",
    }

    def _handle_name_capture(self, s: str, sl: str) -> Optional[Dict[str, Any]]:
        """
        Fast path: catch the name on the turn after RILIE asked for it.

        Only fires if:
        - self._awaiting_name is True
        - self.user_name is not already set

        Strategy:
        1. Try Chomsky (regex patterns + spaCy NER) — the real grammar brain.
        2. If Chomsky is unavailable or returns nothing, fall back to
           lead-in stripping + first-word grab.

        Writes:
        - self.user_name
        - self._awaiting_name = False
        """
        if not self._awaiting_name or (self.user_name and self.user_name != "Mate"):
            return None

        candidate = None

        # --- PRIMARY: Chomsky grammar brain ---
        if CHOMSKY_AVAILABLE:
            try:
                candidate = _chomsky_extract_name(s)
            except Exception:
                candidate = None

        # --- FALLBACK: lead-in stripping + first-word grab ---
        if not candidate:
            cleaned = s.strip().strip(".,!?;:\"'")
            cleaned_lower = cleaned.lower()

            # Strip lead-in phrases to get the actual name
            for phrase in self._NAME_LEAD_INS:
                if cleaned_lower.startswith(phrase):
                    remainder = cleaned[len(phrase):].strip().strip(".,!?;:\"'")
                    if remainder:
                        cleaned = remainder
                        cleaned_lower = cleaned.lower()
                    break

            words = cleaned.split()
            if not words or len(words) > 5:
                return None

            first = words[0].capitalize()
            if first.lower() in self._BAD_NAME_TOKENS:
                return None

            # If they gave first + last, keep both
            if len(words) >= 2 and words[1][0:1].isupper():
                candidate = f"{words[0].capitalize()} {words[1].capitalize()}"
            else:
                candidate = first

        if not candidate or len(candidate.strip()) < 2:
            return None

        # Clean any trailing junk Chomsky might leave
        candidate = candidate.strip().rstrip(".,!?;:\"'")

        self.user_name = candidate
        self._awaiting_name = False

        replies = [
            f"Pleasure to meet you, {self.user_name}! 🍳 What's on your mind?",
            f"{self.user_name}! Good name. What are we getting into?",
            f"Great, {self.user_name}. What's on your mind?",
        ]

        return {
            "result": random.choice(replies),
            "status": "NAME_CAPTURE",
            "triangle_reason": "CLEAN",
            "quality_score": 0.9,
        }

    # -----------------------------------------------------------------
    # RECALL — "what did you just say / what's my name"
    # -----------------------------------------------------------------

    def _handle_recall(self, s: str, sl: str) -> Optional[Dict[str, Any]]:
        """
        Fast path: user asking RILIE to repeat herself or recall their name.

        Reads:
        - self._response_history (to replay last response)
        - self.user_name (to answer "what's my name")

        Returns None if no recall trigger detected.
        """
        triggers = [
            "what did you just say", "what did you say", "say that again",
            "can you repeat", "repeat that", "what was that",
            "do you remember my name", "what's my name", "whats my name",
            "who am i", "do you know my name",
        ]

        if not any(t in sl for t in triggers):
            return None

        # Name recall branch
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

        # Response replay branch
        if self._response_history:
            last = self._response_history[-1]
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

    # -----------------------------------------------------------------
    # CLARIFICATION — "what do you mean / say that differently"
    # -----------------------------------------------------------------

    def _handle_clarification(self, s: str, sl: str) -> Optional[Dict[str, Any]]:
        """
        Fast path: user asking RILIE to rephrase or clarify last response.

        Reads self._response_history to rephrase the last thing she said.
        Returns None if no clarification trigger detected.
        """
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
            bridges = [
                f"What I'm getting at: {last}",
                f"Put another way — {last}",
                f"Different angle — {last}",
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
    # META CORRECTION — "forget that / never mind / drop it"
    # -----------------------------------------------------------------

    def _handle_meta_correction(self, s: str, sl: str) -> Optional[Dict[str, Any]]:
        """
        Fast path: user reacting to a bad RILIE response — reset and re-invite.
        Does NOT modify history. Just acknowledges and pivots.
        Returns None if no meta-correction pattern detected.
        """
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

    # -----------------------------------------------------------------
    # FINALIZE RESPONSE — THE WRITER
    # -----------------------------------------------------------------

    def _finalize_response(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """
        Final assembly of every response that leaves Guvna.

        This is THE WRITER — every response gets logged to _response_history here.
        That's what makes _handle_recall and _handle_clarification work.

        Adds all required fields, fills defaults. History cap handled by deque(maxlen=20).

        Called at the end of process() via fast paths and main pipeline.
        """
        final = {
            "stimulus": raw.get("stimulus", ""),
            # ── LESS IS MORE OR LESS + PRECISION OVERRIDE ──────────────────
            # The universal transform runs on everything.
            # The ONLY exception: precision_override — the fact IS the demi-glace.
            # A: answer. B: honest about limits. C: max sincerity. Zero tongue-in-cheek.
            "result": (
                raw.get("result", "")
                if raw.get("precision_override")
                else less_is_more_or_less(raw.get("result", ""))
                if LIMO_AVAILABLE
                else raw.get("result", "")
            ),
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
            "rx_signal": raw.get("rx_signal"),
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
            "library_metadata": {
                "total_domains": self.domain_metadata.total_domains,
                "files_loaded": len(self.domain_metadata.files),
                "boole_substrate": self.domain_metadata.boole_substrate,
                "core_tracks": self.domain_metadata.core_tracks,
            },
        }

        # THE LOG — this is what makes recall and clarification work
        raw_result_text = raw.get("result", "")
        if raw_result_text:
            _stripped = raw_result_text
            if "\n\n" in _stripped:
                _candidate = _stripped.split("\n\n", 1)[1]
                _first = _stripped.split("\n\n", 1)[0]
                from guvna_tools import TONE_LABELS
                _tone_labels = set(TONE_LABELS.values())
                if any(_first.startswith(lbl) for lbl in _tone_labels):
                    _stripped = _candidate
            self._response_history.append(_stripped)

        return final
