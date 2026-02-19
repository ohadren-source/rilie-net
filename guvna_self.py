"""
guvna_self.py — SELF-GOVERNING SESSION AWARENESS

She knows what she just said. She knows who she's talking to.
She knows if she's been here before.

Extracted from guvna.py as a clean mixin.
Guvna inherits this. These functions don't work without it.

STATE OWNED HERE:
  - _response_history   : everything she's said this session (capped at 20)
  - user_name           : who she's talking to
  - _awaiting_name      : did she just ask for a name?
  - whosonfirst         : is this turn 0?
  - turn_count          : how many turns deep are we?

BEHAVIORS OWNED HERE:
  1. greet()                — APERTURE. Turn 0. First contact.
  2. _handle_name_capture() — catch the name after she asked for it
  3. _handle_recall()       — "what did you just say / what's my name"
  4. _handle_clarification()— "what do you mean / say that differently"
  5. _handle_meta_correction()— "forget that / never mind / drop it"
  6. _finalize_response()   — THE WRITER. Every response gets logged here.

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
from typing import Any, Dict, List, Optional

from guvna_tools import (
    detect_tone_from_stimulus,
    apply_tone_header,
    TONE_EMOJIS,
)

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
    - Is this the first turn?
    - Did I ask for their name?

    Guvna inherits this. Do not instantiate directly.
    """

    def _init_self_state(self) -> None:
        """
        Call this from Guvna.__init__() to wire self-state.

        Guvna.__init__ must call:
            self._init_self_state()
        """
        self.turn_count: int = 0
        self.user_name: Optional[str] = None
        self.whosonfirst: bool = True
        self._awaiting_name: bool = False
        self._response_history: List[str] = []

    # -----------------------------------------------------------------
    # APERTURE — First contact. Before anything else.
    # -----------------------------------------------------------------
    def greet(self, stimulus: str, known_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        APERTURE — Turn 0 only. First thing that happens.

        Either know them by name already, or meet them fresh.
        Returns a greeting response dict, or None if not turn 0.

        Sets:
          - self.user_name (if name found)
          - self._awaiting_name (if name not found)
          - self.whosonfirst = False (consumed)
          - self.turn_count += 1
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
            self._awaiting_name = True

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
    # NAME CAPTURE — turn after she asked "what's your name?"
    # -----------------------------------------------------------------
    def _handle_name_capture(self, s: str, sl: str) -> Optional[Dict[str, Any]]:
        """
        Fast path: catch the name on the turn after RILIE asked for it.

        Only fires if:
          - self._awaiting_name is True
          - self.user_name is not already set
          - stimulus is 1-3 words and not a known filler/bad word

        Writes:
          - self.user_name
          - self._awaiting_name = False
        """
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

    # -----------------------------------------------------------------
    # RECALL — "what did you just say / what's my name"
    # -----------------------------------------------------------------
    def _handle_recall(self, s: str, sl: str) -> Optional[Dict[str, Any]]:
        """
        Fast path: user asking RILIE to repeat herself or recall their name.

        Reads:
          - self._response_history  (to replay last response)
          - self.user_name          (to answer "what's my name")

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

        Adds all required fields, fills defaults, caps history at 20.

        Called at the end of:
          - greet()
          - process() (via fast paths and main pipeline)
        """
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

        # THE LOG — this is what makes recall and clarification work
        result_text = final.get("result", "")
        if result_text:
            self._response_history.append(result_text)
            if len(self._response_history) > 20:
                self._response_history.pop(0)

        return final
