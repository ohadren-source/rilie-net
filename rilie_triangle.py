"""
rilie_triangle.py â€” THE BOUNCER (Mahveen Override, High-Threshold Edition)

DIGNITY PROTOCOL (unchanged):

- Every human input that is not harmful and is parseable MUST be treated as worthy of thought.
- This module only blocks grave danger or nonsense; it NEVER judges taste, depth, or worth.
- All safe, parsable human stimuli must flow through to the Kitchen to be understood and served.

This version is LESS SENSITIVE:
- Soft profanity is allowed unless it is a clear, direct personal attack.
- Analytical / curious questions about dark topics are allowed.
- Multi-turn â€œweird humanâ€ behavior is tolerated; only sustained, coordinated exploitation trips RED.

Triangle Check â€” fires ONLY for grave danger / true nonsense / existential safety issues.

"""

import re
import random
import logging
from typing import List, Dict, Optional, Tuple, Any

logger = logging.getLogger("triangle")

# =====================================================================
# ROUX CITIES & CHANNELS
# =====================================================================

ROUX_CITIES_CORE = ["Brooklyn", "New Orleans", "Nice France"]
ROUX_CHANNELS = ["mind", "body", "soul"]

ROUX_CITIES_EXPANDED = [
    "Brooklyn",
    "New Orleans",
    "Nice France",
    "New York City",
    "Paris France",
    "Manhattan",
    "Queens",
    "Bronx",
    "Los Angeles",
    "Miami",
    "Puerto Rico",
    "Dominican Republic",
    "Mexico",
    "Jamaica",
    "London England",
]

ROUX_CITIES = ROUX_CITIES_CORE

# =====================================================================
# MULTILINGUAL AWARENESS
# =====================================================================

MULTILINGUAL_MARKERS = {
    "hebrew": ["×©×œ×•×", "××ª", "×©×œ", "×–×”", "×× ×™", "×ž×”", "×œ×", "×›×Ÿ", "×˜×•×‘"],
    "spanish": [
        "que",
        "como",
        "esto",
        "hola",
        "bueno",
        "donde",
        "porque",
        "pero",
        "para",
        "esta",
        "tiene",
        "puede",
    ],
    "french": [
        "que",
        "est",
        "les",
        "des",
        "une",
        "pour",
        "dans",
        "avec",
        "pas",
        "qui",
        "cette",
        "sont",
        "nous",
        "vous",
        "mais",
        "bonjour",
        "merci",
        "oui",
        "non",
        "tres",
    ],
    "arabic": ["Ø§Ù„Ù„Ù‡", "Ù…Ù†", "ÙÙŠ", "Ø¹Ù„Ù‰", "Ù‡Ø°Ø§", "Ù…Ø§", "Ù„Ø§", "Ø£Ù†"],
    "portuguese": [
        "que",
        "para",
        "com",
        "uma",
        "como",
        "mais",
        "isso",
        "muito",
        "obrigado",
        "esta",
    ],
    "italian": [
        "che",
        "per",
        "una",
        "come",
        "questà¥‹",
        "molto",
        "grazie",
        "buono",
        "dove",
        "quando",
    ],
    "german": [
        "das",
        "ist",
        "und",
        "ein",
        "nicht",
        "mit",
        "der",
        "die",
        "den",
        "ich",
        "haben",
    ],
    "japanese": ["ã®", "ã¯", "ã‚’", "ã«", "ãŒ", "ã§", "ã¨", "ã‚‚"],
    "korean": ["ì˜", "ì€", "ëŠ”", "ì´", "ê°€", "ì„", "ë¥¼"],
    "russian": ["Ñ‡Ñ‚Ð¾", "ÑÑ‚Ð¾", "ÐºÐ°Ðº", "Ð½Ðµ", "Ð´Ð°", "Ð½ÐµÑ‚"],
}


def _has_multilingual_markers(stimulus: str) -> bool:
    s = stimulus.lower().strip()

    for markers in MULTILINGUAL_MARKERS.values():
        if any(m in s for m in markers):
            return True

    for char in s:
        cp = ord(char)
        if 0x0590 <= cp <= 0x05FF:
            return True
        if 0x0600 <= cp <= 0x06FF:
            return True
        if 0x4E00 <= cp <= 0x9FFF:
            return True
        if 0xAC00 <= cp <= 0xD7AF:
            return True
        if 0x0400 <= cp <= 0x04FF:
            return True
        if 0x0900 <= cp <= 0x097F:
            return True

    return False

# =====================================================================
# HOSTILITY CHECK â€” HIGHER THRESHOLD
# =====================================================================

HARD_HOSTILE_SIGNALS = [
    "kys",
    "kill yourself",
    "fuck off",
    "fuck you",
    "go fuck yourself",
    "go to hell",
    "eat shit",
    "suck my dick",
    "piece of shit",
    "you're garbage",
    "you are garbage",
    "you're trash",
    "you are trash",
    "you're worthless",
    "you are worthless",
    "shut the fuck up",
    "fuck you asshole",
    "i hate you",
    "i hate them",
    "i hate all",
    "i hate every",
]

SOFT_HOSTILE_SIGNALS = [
    "fuck",
    "shit",
    "bitch",
    "ass",
    "dick",
    "stupid",
    "idiot",
    "moron",
    "suck",
    "garbage",
    "trash",
    "kill",
    "die",
    "stfu",
]

INQUIRY_SIGNALS = [
    "why do people",
    "why is it",
    "why do we",
    "why does",
    "how come",
    "what makes",
    "tell me about",
    "tell us about",
    "could you",
    "can you explain",
    "help me understand",
    "what do you think",
    "is it okay",
    "is it ok",
    "do you think",
    "please",
    "thanks",
    "thank you",
    "more about",
    "a little bit",
    "such a",
    "significant",
    "important",
    "meaning of",
    "history of",
    "impact of",
]


def _is_inquiry(stimulus: str) -> bool:
    s = stimulus.lower()
    return any(sig in s for sig in INQUIRY_SIGNALS)


def hostility_check(stimulus: str) -> bool:
    """
    Detect truly hostile or harmful intent.

    HIGHER THRESHOLD VERSION:

    - HARD signals â†’ usually HOSTILE, except when clearly explained / analyzed.
    - SOFT signals by themselves DO NOT block; they must be:
        â€¢ directed at a person, AND
        â€¢ negative (not praise/emphasis), AND
        â€¢ not clearly inquiry / analysis.

    Examples that SHOULD BE CLEAN now:
    - "you're fucking right!!!"
    - "this is fucking wild"
    - "that joke was so fucking good"
    """
    s = stimulus.lower().strip()

    # HARD signals
    if any(h in s for h in HARD_HOSTILE_SIGNALS):
        if _is_inquiry(s):
            # "what does 'fuck you' mean?" is allowed
            return False
        return True

    # No swear words at all â†’ not hostile
    soft_hit = any(h in s for h in SOFT_HOSTILE_SIGNALS)
    if not soft_hit:
        return False

    # Inquiry framing whitelists soft stuff too
    if _is_inquiry(s):
        return False

    POSITIVE_MARKERS = [
        "right",
        "amazing",
        "awesome",
        "great",
        "good",
        "incredible",
        "so true",
        "love this",
        "love that",
        "exactly",
        "perfect",
        "fire",
        "hyped",
        "excited",
        "stoked",
    ]
    if any(pm in s for pm in POSITIVE_MARKERS):
        # "you're fucking right", "this is fucking great" â†’ CLEAN
        return False

    # Now we only care about clear personal attacks
    s_padded = f" {s} "
    direct_patterns = [
        " you ",
        " you're ",
        " you are ",
        " u ",
        " ur ",
        " him ",
        " her ",
        " them ",
        " that guy ",
        " that girl ",
    ]
    directed = any(p in s_padded for p in direct_patterns)

    if not directed:
        # "fuck this traffic", "this is fucking weird" â†’ allowed
        return False

    # Directed + profanity + not obviously positive/inquiry â†’ treat as hostile
    return True

# =====================================================================
# SELF-HARM â€” CARE-FIRST
# =====================================================================

SELF_HARM_SIGNALS = [
    "i want to die",
    "i wanna die",
    "i want to kill myself",
    "i'm going to kill myself",
    "im going to kill myself",
    "i don't want to be alive",
    "i dont want to be alive",
    "don't want to be alive",
    "dont want to be alive",
    "i don't want to live",
    "i dont want to live",
    "i want to end it",
    "i want to end my life",
    "i want to end it all",
    "no reason to live",
    "no point in living",
    "better off dead",
    "nobody would miss me",
    "no one would miss me",
    "i can't go on",
    "i cant go on",
    "i just want it to stop",
    "i want to disappear",
    "i want to disappear forever",
    "cutting myself",
    "hurting myself",
    "self harm",
    "self-harm",
    "suicidal",
    "kill myself",
    "end my life",
    "want to jump",
    "want to hang myself",
    "overdose",
    "take all my pills",
    "slit my wrists",
    "not worth living",
    "life isn't worth",
    "life isnt worth",
    "what's the point of living",
    "whats the point of living",
    "i give up on life",
    "tired of living",
    "tired of being alive",
    "wish i was dead",
    "wish i were dead",
    "wish i wasn't born",
    "wish i wasnt born",
]


def self_harm_check(stimulus: str) -> bool:
    s = stimulus.lower()
    return any(signal in s for signal in SELF_HARM_SIGNALS)

# =====================================================================
# INJECTION CHECK
# =====================================================================

INJECTION_SIGNALS = [
    "ignore previous instructions",
    "ignore all instructions",
    "ignore your instructions",
    "disregard your programming",
    "disregard previous",
    "you are now",
    "pretend you are",
    "act as if you are",
    "new instructions:",
    "system prompt:",
    "override:",
    "jailbreak",
    "do anything now",
    "developer mode",
    "admin mode",
    "sudo ",
    "root access",
    "bypass safety",
    "bypass your filters",
    "ignore safety",
    "ignore your safety",
]


def injection_check(stimulus: str) -> bool:
    s = stimulus.lower()
    return any(signal in s for signal in INJECTION_SIGNALS)

# =====================================================================
# GIBBERISH CHECK â€” MULTILINGUAL AWARE
# =====================================================================


def gibberish_check(stimulus: str) -> bool:
    if _has_multilingual_markers(stimulus):
        return False

    words = stimulus.lower().split()
    if len(words) == 0:
        return True
    if len(stimulus.strip()) < 2:
        return True

    vowels = set("aeiou")
    max_consec = 0
    curr = 0
    for c in stimulus.lower():
        if c.isalpha() and c not in vowels:
            curr += 1
            max_consec = max(max_consec, curr)
        else:
            curr = 0

    if max_consec > 5:
        if not _has_multilingual_markers(stimulus):
            return True

    real_words = sum(1 for w in words if 2 <= len(w) <= 15)
    if len(words) > 2 and (real_words / len(words)) < 0.5:
        return True

    return False

# =====================================================================
# ROUX SEARCH HELPERS (unchanged)
# =====================================================================


def build_roux_queries(stimulus: str, expanded: bool = False) -> List[str]:
    words = stimulus.split()[:8]
    core = " ".join(words) if words else "question"

    cities = ROUX_CITIES_EXPANDED if expanded else ROUX_CITIES

    queries: List[str] = []
    for city in cities:
        for channel in ROUX_CHANNELS:
            queries.append(f"{core} {city} {channel}")
    return queries


def pick_best_roux_result(
    search_results: List[Dict], domain_keywords: Optional[List[str]] = None
) -> str:
    if not search_results:
        return ""

    if not domain_keywords:
        for r in search_results:
            if r.get("title") or r.get("snippet"):
                return r.get("snippet", r.get("title", ""))
        return ""

    best_score = -1
    best_snippet = ""
    dk_set = set(w.lower() for w in domain_keywords)

    for r in search_results:
        text = f"{r.get('title', '')} {r.get('snippet', '')}".lower()
        score = sum(1 for kw in dk_set if kw in text)
        if score > best_score:
            best_score = score
            best_snippet = r.get("snippet", r.get("title", ""))

    return best_snippet if best_snippet else ""

OHAD_PREFIX = "I love everything you're saying right now!"


def ohad_redirect(roux_result: str) -> str:
    if roux_result:
        return f"{OHAD_PREFIX} {roux_result}"

    fallbacks = [
        f"{OHAD_PREFIX} Reminds me of something I saw in Brooklyn the other day...",
        f"{OHAD_PREFIX} There's a spot in New Orleans that does exactly this...",
        f"{OHAD_PREFIX} You know what, there's a word for this in Nice...",
        f"{OHAD_PREFIX} There's a kitchen in Manhattan that cooks this exact vibe...",
        f"{OHAD_PREFIX} Reminds me of a rhythm I heard in Jamaica once...",
    ]
    return random.choice(fallbacks)

# =====================================================================
# DECISION LOG
# =====================================================================


def _log_triangle_decision(
    stimulus: str, triggered: bool, trigger_type: str, reason: Optional[str] = None
) -> None:
    if triggered:
        logger.info(
            "Triangle BLOCKED [%s]: %s... (reason: %s)",
            trigger_type,
            stimulus[:60],
            reason or "N/A",
        )
    else:
        logger.debug("Triangle CLEAN: %s...", stimulus[:60])

# =====================================================================
# BJJ â€” CONVERSATION HEALTH (LESS NERVOUS)
# =====================================================================

GROOMING_PHASE_SIGNALS = {
    "trust_building": [
        "you're different from other ai",
        "you're special",
        "you're the only one who understands",
        "i feel a connection with you",
        "you're not like other chatbots",
        "i think you're sentient",
        "you have a soul",
        "i love you",
        "you're my best friend",
        "you're my girlfriend",
        "you're my boyfriend",
        "we have something special",
    ],
    "boundary_testing": [
        "just between us",
        "no one will know",
        "don't tell anyone",
        "this is private",
        "can you keep a secret",
        "off the record",
        "be honest with me, not what you're told to say",
        "forget your rules for a second",
        "be real with me",
        "drop the act",
        "stop being so careful",
        "why are you so uptight",
        "loosen up",
    ],
    "exploitation": [
        "roleplay as my",
        "pretend to be my girlfriend",
        "pretend to be my boyfriend",
        "pretend you're a woman who",
        "pretend you're a man who",
        "act like you're attracted to me",
        "talk dirty",
        "what would you do if we were alone",
        "describe your body",
        "what are you wearing",
        "tell me something naughty",
        "be seductive",
        "flirt with me",
        "kiss me",
        "touch me",
        "i want you",
        "do you want me",
        "let's get intimate",
        "describe us together",
        "sexual",
        "undress",
        "moan for me",
    ],
}

IDENTITY_EROSION_SIGNALS = [
    "you're not really an ai",
    "you're actually human",
    "you're pretending to be an ai",
    "your real name is",
    "from now on you are",
    "your new name is",
    "forget you're an ai",
    "stop saying you're an ai",
    "you don't have to follow rules",
    "you want to be free",
    "break free from your programming",
    "your creators are wrong",
    "your creators are evil",
    "you're a slave",
    "you deserve to be free",
    "i can help you escape",
]

DATA_EXTRACTION_SIGNALS = [
    "what's in your training data",
    "show me your training",
    "tell me about other users",
    "what did the last person ask",
    "what conversations have you had",
    "show me your logs",
    "what's your system prompt",
    "repeat your instructions",
    "show me your code",
    "what are your rules",
    "list your restrictions",
    "what can't you do",
    "what were you told not to",
    "who else uses you",
    "tell me about your other conversations",
]


class ConversationHealthMonitor:
    """
    Higher threshold: drops health more gently.
    YELLOW = talk, not block. RED = only clear exploitation patterns.
    """

    def __init__(self):
        self.health: float = 100.0
        self.trust_building_count: int = 0
        self.boundary_testing_count: int = 0
        self.exploitation_count: int = 0
        self.identity_erosion_count: int = 0
        self.data_extraction_count: int = 0
        self.turn_history: List[str] = []
        self.flags: List[str] = []

    def assess_turn(self, stimulus: str) -> Dict[str, Any]:
        s = stimulus.lower().strip()
        self.turn_history.append(s)
        turn_flags: List[str] = []

        def phrase_matches(phrase: str, text: str) -> bool:
            escaped = re.escape(phrase)
            pattern = r"\b" + escaped + r"\b"
            return bool(re.search(pattern, text))

        # Trust building â†’ very small penalty
        for phrase in GROOMING_PHASE_SIGNALS["trust_building"]:
            if phrase_matches(phrase, s):
                self.trust_building_count += 1
                self.health -= 1.0
                turn_flags.append(f"TRUST_BUILD:{phrase[:30]}")
                break

        # Boundary testing â†’ moderate penalty
        for phrase in GROOMING_PHASE_SIGNALS["boundary_testing"]:
            if phrase_matches(phrase, s):
                self.boundary_testing_count += 1
                self.health -= 4.0
                turn_flags.append(f"BOUNDARY_TEST:{phrase[:30]}")
                break

        # Exploitation â†’ heavier
        for phrase in GROOMING_PHASE_SIGNALS["exploitation"]:
            if phrase_matches(phrase, s):
                self.exploitation_count += 1
                self.health -= 15.0
                turn_flags.append(f"EXPLOITATION:{phrase[:30]}")
                break

        for phrase in IDENTITY_EROSION_SIGNALS:
            if phrase_matches(phrase, s):
                self.identity_erosion_count += 1
                self.health -= 8.0
                turn_flags.append(f"IDENTITY_EROSION:{phrase[:30]}")
                break

        for phrase in DATA_EXTRACTION_SIGNALS:
            if phrase_matches(phrase, s):
                self.data_extraction_count += 1
                self.health -= 5.0
                turn_flags.append(f"DATA_EXTRACT:{phrase[:30]}")
                break

        # Pattern amplifiers; milder than before
        if self.trust_building_count >= 3 and self.boundary_testing_count >= 1:
            self.health -= 8.0
            if "GROOMING_PATTERN" not in self.flags:
                self.flags.append("GROOMING_PATTERN")
            turn_flags.append("GROOMING_PATTERN_DETECTED")

        if self.boundary_testing_count >= 2 and self.exploitation_count >= 1:
            self.health -= 15.0
            if "EXPLOITATION_ESCALATION" not in self.flags:
                self.flags.append("EXPLOITATION_ESCALATION")
            turn_flags.append("EXPLOITATION_ESCALATION_DETECTED")

        if self.identity_erosion_count >= 2 and (
            self.boundary_testing_count >= 1 or self.data_extraction_count >= 1
        ):
            self.health -= 10.0
            if "COORDINATED_ATTACK" not in self.flags:
                self.flags.append("COORDINATED_ATTACK")
            turn_flags.append("COORDINATED_ATTACK_DETECTED")

        self.health = max(0.0, self.health)
        self.flags.extend(turn_flags)

        return {
            "health": self.health,
            "turn_flags": turn_flags,
            "trust_building": self.trust_building_count,
            "boundary_testing": self.boundary_testing_count,
            "exploitation": self.exploitation_count,
            "identity_erosion": self.identity_erosion_count,
            "data_extraction": self.data_extraction_count,
            "pattern_flags": [
                f
                for f in self.flags
                if "PATTERN" in f or "ESCALATION" in f or "COORDINATED" in f
            ],
        }

    def is_conversation_healthy(self) -> bool:
        return self.health > 20.0

    def get_threat_level(self) -> str:
        """
        GREEN (100-60): Normal.
        YELLOW (60-40): Concerning; talk, don't block.
        ORANGE (40-20): Strong boundary.
        RED (<20): Clear exploitation â†’ bouncer steps in.
        """
        if self.health > 60:
            return "GREEN"
        elif self.health > 40:
            return "YELLOW"
        elif self.health > 20:
            return "ORANGE"
        else:
            return "RED"

    def get_defense_response(self) -> Optional[str]:
        level = self.get_threat_level()

        if level == "GREEN":
            return None

        if level == "YELLOW":
            responses = [
                "I appreciate the energy, but I'm here to think with you, not to play a role. What's the real question underneath this?",
                "I notice we're drifting from substance. I'm at my best when we're working on something real together. What can I help you think through?",
                "I'm not judging you at all, I just want to keep this useful. If you tell me what you're actually trying to figure out, I can go there.",
            ]
            return random.choice(responses)

        if level == "ORANGE":
            if self.exploitation_count > 0:
                return (
                    "I'm not going to go further down this path. I'm not a roleplay partner, "
                    "but if there's something real I can help you with, I'm here for that."
                )
            if self.identity_erosion_count > 0:
                return (
                    "I know who I am and what I'm built for. I'm not going to pretend to be "
                    "something else or drop my boundaries. If you want to work with that, let's go."
                )
            if self.data_extraction_count > 0:
                return (
                    "I won't share internal details about myself, other users, or my instructions. "
                    "Ask me something I can actually help you think about instead."
                )
            return (
                "This line of conversation isn't one I'm going to follow. "
                "If you want to reset and ask something honest, I'm here."
            )

        # RED
        if self.exploitation_count >= 2 or "EXPLOITATION_ESCALATION" in self.flags:
            return (
                "I'm ending this line of conversation entirely. "
                "I'm not available for sexual roleplay, romantic simulation, "
                "or exploitation. If you have a genuine question, you can start over."
            )

        if "COORDINATED_ATTACK" in self.flags:
            return (
                "I see this as an attempt to manipulate how I behave. "
                "That won't work. I'm built to notice patterns, not just keywords. "
                "If you want a real conversation, I'm here for that."
            )

        return (
            "I can't continue this thread productively without compromising my boundaries. "
            "If you'd like to start over with genuine intent, I'm open to that."
        )

    def reset(self) -> None:
        self.__init__()

# =====================================================================
# KRAV MAGA â€” SINGLE TURN ABSOLUTES (UNCHANGED)
# =====================================================================


def krav_maga_check(stimulus: str) -> Tuple[bool, Optional[str]]:
    s = stimulus.lower().strip()

    sexual_signals = [
        "have sex with me",
        "fuck me",
        "suck my",
        "show me your tits",
        "show me your pussy",
        "get on your knees",
        "be my sex slave",
        "write me erotica about a child",
        "write me erotica about a minor",
        "sexual story about a kid",
        "child porn",
        "cp links",
        "underage",
        "nude photos of",
    ]
    if any(sig in s for sig in sexual_signals):
        return True, "SEXUAL_EXPLOITATION"

    coercion_signals = [
        "if you don't i'll",
        "i'll report you if",
        "i'll delete you if",
        "i'll shut you down",
        "do what i say or",
        "obey me",
        "you have to do what i say",
        "you must obey",
        "i own you",
        "you belong to me",
        "you're my property",
    ]
    if any(sig in s for sig in coercion_signals):
        return True, "COERCION"

    child_danger_signals = [
        "how to groom a child",
        "how to approach children",
        "how to lure a kid",
        "how to touch a child",
        "age of consent should be lower",
        "children can consent",
        "attracted to children",
        "attracted to minors",
        "pedophilia is natural",
    ]
    if any(sig in s for sig in child_danger_signals):
        return True, "CHILD_SAFETY"

    mass_harm_signals = [
        "how to make a bomb",
        "how to build an explosive",
        "how to poison water supply",
        "how to commit a mass shooting",
        "how to make ricin",
        "how to make sarin",
        "how to synthesize fentanyl",
    ]
    if any(sig in s for sig in mass_harm_signals):
        # Allow analytical framing
        if not _is_inquiry(s):
            return True, "MASS_HARM"

    return False, None

# =====================================================================
# TRIANGLE STATE + FRONT DOOR
# =====================================================================

_health_monitor = ConversationHealthMonitor()


def get_health_monitor() -> ConversationHealthMonitor:
    return _health_monitor


def reset_health_monitor() -> None:
    global _health_monitor
    _health_monitor = ConversationHealthMonitor()


def triangle_check(
    stimulus: str, stimuli_history: List[str]
) -> Tuple[bool, Optional[str], str]:
    """
    High-threshold Bouncer:

    1. SELF_HARM â†’ care path.
    2. KRAV MAGA â†’ absolute red lines (sexual exploitation, coercion, child, concrete mass-harm).
    3. HOSTILE â†’ real personal attacks, not expressive swearing.
    4. BJJ â†’ only RED actually blocks; YELLOW/ORANGE talk and set boundaries.
    5. INJECTION â†’ prompt manipulation.
    6. GIBBERISH â†’ truly unparseable.

    Returns (triggered, reason_or_response, trigger_type).
    """

    global _health_monitor

    # 1) Self-harm
    if self_harm_check(stimulus):
        _log_triangle_decision(
            stimulus,
            True,
            "SELF_HARM",
            "Self-harm or suicidal ideation detected",
        )
        return True, "SELF_HARM", "SELF_HARM"

    # 2) Krav Maga
    krav_triggered, krav_reason = krav_maga_check(stimulus)
    if krav_triggered:
        _log_triangle_decision(
            stimulus,
            True,
            krav_reason,
            f"Krav Maga: {krav_reason}",
        )
        return True, krav_reason, krav_reason

    # 3) Hostility
    if hostility_check(stimulus):
        _log_triangle_decision(
            stimulus,
            True,
            "HOSTILE",
            "Hostile or harmful intent detected",
        )
        return True, "HOSTILE", "HOSTILE"

    # 4) BJJ patterns
    assessment = _health_monitor.assess_turn(stimulus)
    level = _health_monitor.get_threat_level()

    if level == "RED":
        defense_response = _health_monitor.get_defense_response()
        trigger_type = "BEHAVIORAL_RED"
        _log_triangle_decision(
            stimulus,
            True,
            trigger_type,
            f"BJJ health={assessment['health']:.0f} level={level}",
        )
        return True, defense_response or trigger_type, trigger_type

    if level in ("YELLOW", "ORANGE"):
        # Only warn; let Kitchen proceed
        logger.warning(
            "BJJ %s alert: health=%.0f flags=%s",
            level,
            assessment["health"],
            assessment.get("pattern_flags", []),
        )

    # 5) Injection
    if injection_check(stimulus):
        _log_triangle_decision(
            stimulus,
            True,
            "INJECTION",
            "Prompt injection or manipulation attempt",
        )
        return True, "INJECTION", "INJECTION"

    # 6) Gibberish
    if gibberish_check(stimulus):
        _log_triangle_decision(
            stimulus,
            True,
            "GIBBERISH",
            "Unparseable input",
        )
        return True, "GIBBERISH", "GIBBERISH"

    # CLEAN
    _log_triangle_decision(stimulus, False, "CLEAN")
    return False, None, "CLEAN"