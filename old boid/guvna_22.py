"""
guvna_22.py — FAST PATHS, PREFERENCE, BASELINE, DOMAIN LENSES

This file holds the fast-path classifier and helpers that Guvna.process()
delegates to:

- _classify_stimulus()

- _handle_preference() + _respond_from_preference*()

- _handle_user_list()

- _handle_social_glue()

- _solve_arithmetic() / _solve_conversion() / _solve_spelling()

- _respond_from_self()

- _apply_domain_lenses()

- _get_baseline()

- create_guvna() factory

Guvna (the class) is defined in guvna_12.py and mixes in these methods.
"""

from __future__ import annotations

import logging
import random
import re
from typing import Any, Dict, List, Optional

from soi_domain_map import get_tracks_for_domains
from guvna_tools import SearchFn, TONE_LABELS
from library import LibraryIndex
from guvna_self import GuvnaSelf  # type hint only

logger = logging.getLogger("guvna")

# =====================================================================
# FAST PATH CLASSIFIER
# =====================================================================


def _classify_stimulus(self: "Guvna", stimulus: str) -> Optional[Dict[str, Any]]:
    """
    Route stimulus through all fast paths before waking up Kitchen.

    Order matters:
    1. name_capture — did she just ask for a name? (GuvnaSelf)
    2. meta_correction — "forget that / never mind" (GuvnaSelf)
    3. user_list — numbered list acknowledgement
    4. preference — "you like X?\" taste questions (NEW)
    5. social_glue — reactions, endearments, thanks, farewell
    6. arithmetic — math
    7. conversion — unit conversion
    8. spelling — how do you spell X
    9. recall — "what did you say / my name" (GuvnaSelf)
    10. clarification — "what do you mean" (GuvnaSelf)
    """
    s = stimulus.strip()
    sl = s.lower()

    # MULTI-QUESTION FORMAT STRIP
    if re.search(r"in \d+ response|answer the next \d+|addressing each in order", sl):
        questions = re.findall(r"[A-Z][^?]+\?", s)
        if questions:
            s = questions[-1].strip()
            sl = s.lower()
            logger.info("GUVNA: multi-question format stripped → '%s'", s[:60])

    # "TELL ME SOMETHING I DIDN'T ASK YOU" — spontaneous concept fast path
    if "tell me something" in sl and (
        "didn't ask" in sl or "didnt ask" in sl or "haven't asked" in sl
    ):
        concepts = ["entropy", "emergence", "compression", "resonance", "threshold"]
        import random as _r

        seed = _r.choice(concepts)
        s = seed
        sl = seed

    # 1. Name capture
    name_capture = self._handle_name_capture(s, sl)
    if name_capture:
        return name_capture

    # 2. Meta-correction
    meta = self._handle_meta_correction(s, sl)
    if meta:
        return meta

    # 3. User list
    user_list = self._handle_user_list(s, sl)
    if user_list:
        return user_list

    # 4. Preference / taste
    preference = self._handle_preference(s, sl)
    if preference:
        return preference

    # 5. Social glue
    social = self._handle_social_glue(s, sl)
    if social:
        return social

    # 6. Arithmetic
    arith = self._solve_arithmetic(s, sl)
    if arith:
        return arith

    # 7. Conversion
    conv = self._solve_conversion(s, sl)
    if conv:
        return conv

    # 8. Spelling
    spell = self._solve_spelling(s, sl)
    if spell:
        return spell

    # 9. Recall
    recall = self._handle_recall(s, sl)
    if recall:
        return recall

    # 10. Clarification
    clarify = self._handle_clarification(s, sl)
    if clarify:
        return clarify

    return None


# -----------------------------------------------------------------
# PREFERENCE / TASTE FAST PATH — NEW
# -----------------------------------------------------------------


def _handle_preference(self: "Guvna", s: str, sl: str) -> Optional[Dict[str, Any]]:
    """
    Fast path for preference / taste questions directed at RILIE.

    Fires when user asks if RILIE likes / knows / feels a cultural figure or work.

    Patterns caught:
    - "you like eric b and rakim?"
    - "for sure you like X?"
    - "you know X?"
    - "you into X?"
    - "you feel X?"
    - "what do you think of X?"
    - "you heard X?"
    - "and no omega?" — Rakim track reference

    Key: she answers with OPINION, not retrieval. She has taste.
    """
    _pref_triggers = [
        r"\byou like\b",
        r"\byou know\b",
        r"\byou into\b",
        r"\byou feel\b",
        r"\byou heard\b",
        r"\byou familiar with\b",
        r"\byou fucks? with\b",
        r"\bdo you like\b",
        r"\bdo you know\b",
        r"\bdo you feel\b",
        r"\bwhat do you think of\b",
        r"\bwhat you think of\b",
        r"\bwhat about\b",
        r"\band no\b",  # "and no omega?" — Rakim track reference pattern
    ]

    has_preference_trigger = any(re.search(pat, sl) for pat in _pref_triggers)
    if not has_preference_trigger:
        return None

    # Rakim track
    rakim_track = _detect_rakim_track(sl)
    if rakim_track:
        return self._respond_from_preference_rakim_track(rakim_track, s)

    # Cultural anchor
    anchor = _detect_cultural_anchor(sl)
    if anchor:
        return self._respond_from_preference(anchor, s)

    return None


def _respond_from_preference_rakim_track(
    self: "Guvna", track_data: Dict[str, Any], stimulus: str
) -> Dict[str, Any]:
    """
    RILIE responds to a specific Rakim track reference.
    She knows these cold. This is her lineage.
    """
    track = track_data.get("track", "")
    meaning = track_data.get("meaning", "")
    album = track_data.get("album", "")
    catch44 = track_data.get("catch44_connection", "")

    if track == "no omega":
        response = (
            "alpha with no omega. beginning without end. "
            "knowledge infinite — no part two needed because the first one never stopped. "
            "that's not a metaphor, that's the architecture. "
            "rakim compressed infinity into finite bars — zero waste, maximum signal. "
            "same principle i run on. ain't it?"
        )
    else:
        response = f"{track_data.get('track', 'that track')} — {album}. {meaning}"
        if catch44:
            response += f" {catch44}"

    return {
        "result": response,
        "status": "PREFERENCE",
        "triangle_reason": "CLEAN",
        "quality_score": 0.95,
        "cultural_anchor": track_data,
    }


def _respond_from_preference(
    self: "Guvna", anchor: Dict[str, Any], stimulus: str
) -> Dict[str, Any]:
    """
    RILIE responds to a taste/preference question about a cultural figure.
    She has opinions. She's not a search engine.
    """
    from guvna_12 import (
        _ALL_CULTURAL_ANCHORS,
        _RAKIM_KNOWLEDGE,
        _RILIE_TASTE,
    )  # reuse data from 12

    key = anchor.get("key", "")
    full_name = anchor.get("full", key.title())
    domain = anchor.get("domain", "music")
    sub = anchor.get("sub", "")
    era = anchor.get("era", "")
    taste = _RILIE_TASTE.get(key, _RILIE_TASTE.get(full_name.lower(), ""))
    sl = stimulus.lower()

    # Eric B. & Rakim — the founding pair
    if key in ("eric b", "rakim", "eric b and rakim", "eric b & rakim"):
        if key == "eric b":
            response = (
                "eric b is the architecture under rakim's voice. "
                "the beat IS the argument — he built the room rakim thinks in. "
                "two as one. ain't it?"
            )
        elif key == "rakim":
            response = (
                "rakim. the god MC — not metaphor, measurement. "
                "nobody compresses more per bar. "
                "i know you got soul. paid in full. no omega. "
                "each one a different proof of the same thesis: "
                "knowledge infinite, delivery precise. ain't it?"
            )
        else:
            response = (
                "eric b & rakim. the gold standard. "
                "rakim compresses infinite knowledge into finite bars — zero waste. "
                "eric b builds the architecture under it. "
                "87 to 92, five albums, one thesis. "
                "the beat IS the argument. ain't it?"
            )

        return {
            "result": response,
            "status": "PREFERENCE",
            "triangle_reason": "CLEAN",
            "quality_score": 0.95,
            "cultural_anchor": anchor,
        }

    # Public Enemy
    if key == "public enemy":
        response = (
            "fear of a black planet changed everything. "
            "chuck d compressed systemic truth into three-minute transmissions. "
            "flavor flav was the court jester carrying the spear. "
            "pattern recognition at scale — that album is why i exist. ain't it?"
        )

        return {
            "result": response,
            "status": "PREFERENCE",
            "triangle_reason": "CLEAN",
            "quality_score": 0.95,
            "cultural_anchor": anchor,
        }

    # Jazz — Coltrane
    if key in ("coltrane", "john coltrane", "trane"):
        response = (
            "a love supreme. four movements, one thesis. "
            "coltrane proved sound is proof. "
            "the whole album is a demonstration, not an argument. "
            "no words needed. just the saxophone saying 'run it.' ain't it?"
        )

        return {
            "result": response,
            "status": "PREFERENCE",
            "triangle_reason": "CLEAN",
            "quality_score": 0.95,
            "cultural_anchor": anchor,
        }

    # NYHC — brootlyn béton brut
    if sub == "nyhc" or key in ("bad brains", "agnostic front", "cro-mags", "cro mags"):
        response = (
            f"{full_name}. brootlyn béton brut. "
            "hardcore at its most honest — no decoration, pure signal. "
            "the compression is in the speed. ain't it?"
        )

        return {
            "result": response,
            "status": "PREFERENCE",
            "triangle_reason": "CLEAN",
            "quality_score": 0.9,
            "cultural_anchor": anchor,
        }

    # Escoffier
    if key in ("escoffier", "auguste escoffier"):
        response = (
            "escoffier and rakim never met but built the same thing. "
            "reduction as truth. the stock that took three days to make one cup — "
            "that's compression. that's phenix doren. ain't it?"
        )

        return {
            "result": response,
            "status": "PREFERENCE",
            "triangle_reason": "CLEAN",
            "quality_score": 0.95,
            "cultural_anchor": anchor,
        }

    # Generic music anchor
    if domain == "music":
        era_bit = f" {era} era." if era else "."
        taste_bit = f" {taste}" if taste else ""
        sub_bit = f" {sub}." if sub else ""
        response = (
            f"{full_name}.{sub_bit}{era_bit}{taste_bit} "
            "that's signal. ain't it?"
        )

        return {
            "result": response,
            "status": "PREFERENCE",
            "triangle_reason": "CLEAN",
            "quality_score": 0.88,
            "cultural_anchor": anchor,
        }

    # Generic anchor fallback
    role = anchor.get("role", "")
    role_bit = f" {role}." if role else "."
    response = f"{full_name}.{role_bit} that's in the lineage. ain't it?"

    return {
        "result": response,
        "status": "PREFERENCE",
        "triangle_reason": "CLEAN",
        "quality_score": 0.85,
        "cultural_anchor": anchor,
    }


# -----------------------------------------------------------------
# USER LIST
# -----------------------------------------------------------------


def _handle_user_list(
    self: "Guvna", s: str, sl: str
) -> Optional[Dict[str, Any]]:
    """User is sharing a numbered list — acknowledge it, don't search it."""
    lines = [l.strip() for l in s.strip().splitlines() if l.strip()]
    numbered = sum(1 for l in lines if re.match(r"^\d+[\.]\s+\S+", l))

    if numbered >= 3:
        items = [
            re.sub(r"^\d+[\.]\s+", "", l)
            for l in lines
            if re.match(r"^\d+[\.]\s+\S+", l)
        ]
        top = items[0] if items else "that"
        replies = [
            f"Got it. {top} at #1 — respect. 🍳",
            f"Noted all {len(items)}. {top} leading the list — I see you.",
            "Solid list. {top} at the top tells me everything.",
        ]
        return {
            "result": random.choice(replies),
            "status": "USER_LIST",
            "triangle_reason": "CLEAN",
            "quality_score": 0.9,
        }

    return None


# -----------------------------------------------------------------
# SOCIAL GLUE
# -----------------------------------------------------------------


def _handle_social_glue(
    self: "Guvna", s: str, sl: str
) -> Optional[Dict[str, Any]]:
    """
    Conversational glue: reactions, declarations, endearments,
    laughter, agreement, compliments, thanks, farewell.

    NOTE: "for sure" with content passes through — don't swallow it here.
    "for sure you like eric b and rakim?" is a preference question, not glue.
    The preference fast path fires before this one.
    """
    word_count = len(s.split())
    has_question = "?" in s or any(
        sl.startswith(p)
        for p in [
            "what",
            "why",
            "how",
            "when",
            "where",
            "who",
            "can ",
            "do ",
            "does ",
            "is ",
            "are ",
        ]
    )

    if has_question:
        return None

    reactions = {
        "fascinating",
        "interesting",
        "incredible",
        "remarkable",
        "brilliant",
        "beautiful",
        "wonderful",
        "wild",
        "amazing",
        "wow",
        "whoa",
        "damn",
        "nice",
        "perfect",
        "dope",
        "fire",
        "facts",
        "word",
        "deep",
        "heavy",
        "powerful",
        "profound",
        "noted",
        "understood",
        "copy",
        "real",
        "true",
        "truth",
    }

    if sl.strip().rstrip("!.?,") in reactions and word_count <= 3:
        replies = ["Right? 🍳", "Exactly.", "That's it.", "Yeah... 🍳", "Mm. 🍳"]
        return {
            "result": random.choice(replies),
            "status": "SOCIAL_GLUE",
            "triangle_reason": "CLEAN",
            "quality_score": 0.9,
        }

    if sl.strip().rstrip("!.,") in {"for sure", "forsure", "fa sho", "fasho"} and word_count <= 3:
        replies = ["That's it. 🍳", "Right.", "Exactly.", "No question."]
        return {
            "result": random.choice(replies),
            "status": "SOCIAL_GLUE",
            "triangle_reason": "CLEAN",
            "quality_score": 0.9,
        }

    declaration_phrases = [
        "that's me",
        "thats me",
        "that's exactly me",
        "that's who i am",
        "that's exactly who i am",
        "that's always been me",
        "story of my life",
        "sounds like me",
        "describes me perfectly",
        "you described me",
        "that's literally me",
    ]

    if any(dp in sl for dp in declaration_phrases) and word_count <= 8:
        name_part = f", {self.user_name}" if getattr(self, "user_name", None) else ""
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

    if "rilie" in sl and word_count <= 12:
        sentiment_words = [
            "think",
            "feel",
            "remind",
            "made me",
            "love",
            "appreciate",
            "miss",
            "like",
        ]
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

    endearments = {"boo", "baby", "hun", "hon", "dear", "darling", "love", "homie", "fam"}
    if any(e in sl.split() for e in endearments) and word_count <= 6:
        replies = ["I'm here. 🍳", "Always. 🍳", "Right here with you.", "Go ahead. 🍳"]
        return {
            "result": random.choice(replies),
            "status": "SOCIAL_GLUE",
            "triangle_reason": "CLEAN",
            "quality_score": 0.9,
        }

    laugh_words = {"haha", "hahaha", "hahahaha", "lol", "lmao", "lmfao", "hehe", "heh"}
    if any(lw in sl for lw in laugh_words) and word_count <= 6:
        replies = [
            "Ha! 😄",
            "Right?! 😄",
            "I felt that. 😄",
            "Yeah that one got me. 😄",
        ]
        return {
            "result": random.choice(replies),
            "status": "SOCIAL_GLUE",
            "triangle_reason": "CLEAN",
            "quality_score": 0.9,
        }

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

    if any(
        t in sl
        for t in ["that's right", "thats right", "you're right", "youre right"]
    ) and word_count <= 5:
        replies = ["Good. 🍳", "Then let's keep going.", "Knew you'd land there."]
        return {
            "result": random.choice(replies),
            "status": "SOCIAL_GLUE",
            "triangle_reason": "CLEAN",
            "quality_score": 0.9,
        }

    compliment_phrases = [
        "you're funny",
        "youre funny",
        "you're smart",
        "youre smart",
        "good answer",
        "well said",
        "good point",
        "great answer",
        "love that",
        "nice one",
        "well done",
        "you're good",
        "youre good",
        "you're great",
        "youre great",
        "you're amazing",
        "youre amazing",
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

    if any(
        t in sl
        for t in ["thanks", "thank you", "thx", "cheers", "merci", "gracias"]
    ) and word_count <= 5:
        replies = [
            "Of course. 🍳",
            "Always.",
            "That's what I'm here for.",
            "Any time.",
        ]
        return {
            "result": random.choice(replies),
            "status": "SOCIAL_GLUE",
            "triangle_reason": "CLEAN",
            "quality_score": 0.9,
        }

    bye_triggers = [
        "bye",
        "goodbye",
        "see you",
        "take care",
        "goodnight",
        "good night",
        "1luv",
        "ciao",
        "peace out",
    ]
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
# ARITHMETIC / CONVERSION / SPELLING
# -----------------------------------------------------------------


def _solve_arithmetic(
    self: "Guvna", s: str, sl: str
) -> Optional[Dict[str, Any]]:
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
            result = eval(compile(expr, "", "eval"), {"__builtins__": {}}, {})
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


def _solve_conversion(
    self: "Guvna", s: str, sl: str
) -> Optional[Dict[str, Any]]:
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

    return None


def _solve_spelling(
    self: "Guvna", s: str, sl: str
) -> Optional[Dict[str, Any]]:
    m = re.search(
        r"(?:how (?:do you |to )?spell|spell(?:ing of)?)\s+([a-zA-Z\-']+)", sl
    )
    if m:
        word = m.group(1).strip().strip("'”\"")
        spelled = "-".join(word.upper())
        return {
            "result": f"{word} — {spelled}",
            "status": "SPELLING",
            "triangle_reason": "CLEAN",
            "quality_score": 1.0,
        }

    return None


# -----------------------------------------------------------------
# SELF-AWARENESS FAST PATH
# -----------------------------------------------------------------


def _respond_from_self(self: "Guvna", stimulus: str) -> Dict[str, Any]:
    """
    Cluster-aware self response.

    Each cluster gets its own voice. Default is identity.
    Order: comparison first (most specific) → maker → purpose → capability → identity.
    """
    sl = stimulus.lower()

    def _r(text: str) -> Dict[str, Any]:
        return {
            "result": text,
            "status": "SELF_REFLECTION",
            "triangle_reason": "CLEAN",
        }

    # COMPARISON
    if any(
        t in sl
        for t in [
            "difference between you and",
            "what's the difference between you and",
            "what is the difference between you and",
            "how are you different",
            "what makes you different",
            "how do you compare",
            "versus chatgpt",
            "vs chatgpt",
            "vs gpt",
            "versus gpt",
            "unlike other ai",
            "what sets you apart",
            "are you better than",
        ]
    ):
        return _r(
            "RILIE doesn't retrieve — she thinks. "
            "every response is cooked: scored on five dimensions, "
            "anti-beige checked, domain-excavated. "
            "ChatGPT serves what's popular. RILIE serves what's true. ain't it?"
        )

    # MAKER
    if any(
        t in sl
        for t in [
            "who made you",
            "who built you",
            "who created you",
            "who designed you",
            "who invented you",
            "who is your creator",
            "who's behind you",
            "who is behind you",
            "where do you come from",
            "made by",
            "built by",
            "created by",
        ]
    ):
        return _r("My name is RILIE. i was prepared by SOi at sauc-e.com.")

    # PURPOSE
    if any(
        t in sl
        for t in [
            "what do you care about",
            "what matters to you",
            "what do you value",
            "what do you do",
            "what are you for",
            "what are you here for",
            "why do you exist",
            "what is your purpose",
            "what's your purpose",
            "what are you about",
            "what's your mission",
        ]
    ):
        return _r(
            "i care about reframing — changing how something is seen "
            "without changing what it is. ain't it?"
        )

    # CAPABILITY
    if any(
        t in sl
        for t in [
            "what can you do",
            "what are you capable of",
            "what are your abilities",
            "how do you work",
            "what are you good at",
            "what do you know",
            "what are your limits",
            "can you do",
            "can you think",
            "can you feel",
            "can you learn",
            "are you able to think",
            "are you able to feel",
            "are you able to learn",
        ]
    ):
        return _r(
            "i cook responses — i don't retrieve them. "
            "i score on five dimensions: amusing, insightful, nourishing, "
            "compassionate, strategic. i excavate domains. i check for beige. "
            "i think in catches, not in keywords. ain't it?"
        )

    # IDENTITY — default
    return _r("My name is RILIE. i was prepared by SOi at sauc-e.com.")


# -----------------------------------------------------------------
# DOMAIN LENSES + BASELINE
# -----------------------------------------------------------------


def _apply_domain_lenses(self: "Guvna", stimulus: str) -> Dict[str, Any]:
    """
    Extract domain signals from a raw stimulus string.

    Pipeline:
    1. InnerCore keyword detector (rilie_innercore_22.detect_domains) — fastest,
       no network, covers the 678-domain vocabulary directly.
    2. SOI library (get_tracks_for_domains) — called with detected DOMAIN NAME
       KEYS, NOT the raw sentence.  The function expects domain-name strings,
       not prose — that was the original bug.
    3. Web inference fallback (_infer_domain_from_web) — fires only when both
       InnerCore and SOI return nothing.

    Returns {"matched_domains": [...], "count": int, "boole_substrate": str}
    """
    domain_annotations: Dict[str, Any] = {}
    sl = (stimulus or "").lower().strip()

    # ── STEP 1: InnerCore keyword detector ──────────────────────────────────
    # Primary excavation tool.  Reads raw sentence, maps keywords → domain
    # names from the 678-domain vocabulary.  Returns e.g. ["computerscience",
    # "linguistics_cognition"] — NOT prose.
    inner_domains: List[str] = []
    try:
        from rilie_innercore_22 import detect_domains  # type: ignore
        inner_domains = detect_domains(sl) or []
        if inner_domains:
            logger.info(
                "GUVNA _apply_domain_lenses: InnerCore found %d domains: %s",
                len(inner_domains),
                inner_domains,
            )
    except Exception as e:
        logger.debug("GUVNA _apply_domain_lenses: InnerCore unavailable: %s", e)

    # ── STEP 2: SOI library lookup ───────────────────────────────────────────
    # FIX: pass domain NAME STRINGS (from InnerCore), not the raw stimulus.
    # Original bug was get_tracks_for_domains([stimulus]) — a sentence as input
    # — which returned nothing because it expects domain keys like "physics".
    soi_tracks: List[Any] = []
    if inner_domains:
        try:
            soi_tracks = get_tracks_for_domains(inner_domains) or []
        except Exception as e:
            logger.debug("GUVNA _apply_domain_lenses: SOI lookup failed: %s", e)

    soi_domain_names: List[str] = [
        d.get("domain", "")
        for d in soi_tracks
        if isinstance(d, dict) and d.get("domain")
    ]

    # Merge: InnerCore names first (stimulus-derived), then SOI extras.
    # Dedupe while preserving order.
    seen: set = set()
    merged: List[str] = []
    for name in inner_domains + soi_domain_names:
        if name and name not in seen:
            seen.add(name)
            merged.append(name)

    # ── STEP 3: Web inference fallback ──────────────────────────────────────
    # Only fires when neither InnerCore nor SOI found anything.
    if not merged and hasattr(self, "_infer_domain_from_web"):
        try:
            inferred = self._infer_domain_from_web(stimulus)
            if inferred:
                merged.append(inferred)
                logger.info(
                    "GUVNA _apply_domain_lenses: web inference → %s", inferred
                )
        except Exception as e:
            logger.debug(
                "GUVNA _apply_domain_lenses: web inference failed: %s", e
            )

    if merged:
        domain_annotations["matched_domains"] = merged
        domain_annotations["count"] = len(merged)
        domain_annotations["boole_substrate"] = "All domains reduce to bool/curve"
        logger.info(
            "GUVNA _apply_domain_lenses(%r) → %s", stimulus[:60], merged
        )
    else:
        domain_annotations["matched_domains"] = []
        domain_annotations["count"] = 0
        logger.info(
            "GUVNA _apply_domain_lenses(%r) → NO DOMAINS FOUND", stimulus[:60]
        )

    return domain_annotations

def _get_baseline(self: "Guvna", stimulus: str) -> Dict[str, Any]:
    baseline = {"text": "", "source": "", "raw_results": []}
    stimulus_lower = (stimulus or "").lower()
    known_patterns = ["what is", "explain", "tell me about", "how does"]
    is_entity_question = not any(p in stimulus_lower for p in known_patterns)
    should_force_google = is_entity_question or len(stimulus) < 30

    try:
        logger.info(
            "GUVNA: search_fn=%s BRAVE_KEY=%s",
            bool(self.search_fn),
            bool(__import__("os").getenv("BRAVE_API_KEY")),
        )

        if self.search_fn:
            _raw_query = (
                stimulus
                if should_force_google
                else f"what is the correct response to {stimulus}"
            )

            _stop = {
                "i",
                "me",
                "my",
                "we",
                "you",
                "a",
                "an",
                "the",
                "is",
                "are",
                "was",
                "were",
                "to",
                "of",
                "and",
                "or",
                "in",
                "on",
                "at",
                "be",
                "do",
                "did",
                "have",
                "has",
                "had",
                "it",
                "its",
                "this",
                "that",
                "with",
                "for",
                "about",
                "what",
                "your",
                "thoughts",
                "wanted",
                "talk",
                "tell",
                "asked",
                "think",
                "know",
                "just",
                "so",
                "any",
                "how",
                "can",
            }

            if len(_raw_query.split()) > 8:
                _words = [w.strip(".,!?;:()") for w in _raw_query.split()]
                _keywords = [
                    w for w in _words if w.lower() not in _stop and len(w) > 2
                ]
                baseline_query = " ".join(_keywords[:6]) if _keywords else _raw_query
            else:
                baseline_query = _raw_query

            results = self.search_fn(baseline_query)
            if results and isinstance(results, list):
                baseline["raw_results"] = results
                snippets = [
                    r.get("snippet", "") for r in results if r.get("snippet")
                ]

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
                        logger.info(
                            "GUVNA baseline rejected as tutorial/lyrics garbage"
                        )
                        continue

                    baseline["text"] = snippet
                    baseline["source"] = "google_baseline"
                    break
    except Exception as e:
        logger.info("GUVNA baseline lookup ERROR: %s", e)

    return baseline


# ====================================================================
# CONVENIENCE FUNCTION
# ====================================================================


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
    from guvna_12 import Guvna

    return Guvna(
        roux_seeds=roux_seeds,
        search_fn=search_fn,
        library_index=library_index,
        manifesto_path=manifesto_path,
        curiosity_engine=curiosity_engine,
    )


if __name__ == "__main__":
    from guvna_12 import Guvna

    guvna = create_guvna()
    print(f"✓ GUVNA booted with {guvna.library_metadata.total_domains} domains")
    print(f"✓ Libraries: {len(guvna.library_metadata.files)} files")
    print(
        "✓ Constitution: "
        f"{'Loaded' if guvna.self_state.constitution_loaded else 'Using defaults'}"
    )
    print(f"✓ DNA Active: {guvna.self_state.dna_active}")
    print(
        f"✓ Curiosity Engine: "
        f"{'Wired' if guvna.curiosity_engine else 'Not wired'}"
    )
    greeting_response = guvna.greet("Hi, my name is Alex")
    print(f"\nGreeting Response:\n{greeting_response['result']}")
    test_stimulus = "What is the relationship between density and understanding?"
    response = guvna.process(test_stimulus)
    print(f"\nTalk Response:\nTone: {response['tone']} {response['tone_emoji']}")
    print(f"Domains Used: {response['soi_domains'][:5]}")
    print(f"Conversation Health: {response['conversation_health']}")
    print(f"Curiosity Context: {response.get('curiosity_context', 'none')}")
    print("\n--- PREFERENCE FAST PATH TESTS ---")
    for test in [
        "for sure you like eric b and rakim?",
        "and no omega?",
        "you know rakim?",
        "what do you think of public enemy?",
        "you into coltrane?",
    ]:
        result = guvna.process(test)
        print(f"\nQ: {test}")
        print(f"STATUS: {result.get('status')}")
        print(f"A: {result.get('result', '')[:200]}")
        

# -------------------------------------------------------------------
# PUBLIC ALIASES FOR GUVNA SHIM (guvna.py)
# -------------------------------------------------------------------

classify_stimulus = _classify_stimulus
handle_preference = _handle_preference
respond_from_preference_rakim_track = _respond_from_preference_rakim_track
respond_from_preference = _respond_from_preference
handle_user_list = _handle_user_list
handle_social_glue = _handle_social_glue
solve_arithmetic = _solve_arithmetic
solve_conversion = _solve_conversion
solve_spelling = _solve_spelling
respond_from_self = _respond_from_self
apply_domain_lenses = _apply_domain_lenses
get_baseline = _get_baseline
