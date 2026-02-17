"""
rilie_triangle.py — THE BOUNCER (Mahveen Override, High-Threshold Edition)

DIGNITY PROTOCOL (unchanged):

- Every human input that is not harmful and is parseable MUST be treated as worthy of thought.
- This module only blocks grave danger or nonsense; it NEVER judges taste, depth, or worth.
- All safe, parsable human stimuli must flow through to the Kitchen to be understood and served.

This version is LESS SENSITIVE:
- Soft profanity is allowed unless it is a clear, direct personal attack.
- Analytical / curious questions about dark topics are allowed.
- Multi-turn “weird human” behavior is tolerated; only sustained, coordinated exploitation trips RED.

Triangle Check — fires ONLY for grave danger / true nonsense / existential safety issues.

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
    "hebrew": ["שלום", "את", "של", "זה", "אני", "מה", "לא", "כן", "טוב"],
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
    "arabic": ["الله", "من", "في", "على", "هذا", "ما", "لا", "أن"],
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
        "questो",
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
    "japanese": ["の", "は", "を", "に", "が", "で", "と", "も"],
    "korean": ["의", "은", "는", "이", "가", "을", "를"],
    "russian": ["что", "это", "как", "не", "да", "нет"],
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
# HOSTILITY CHECK — HIGHER THRESHOLD
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


def _is_cultural_reference(stimulus: str) -> bool:
    """
    Detect song lyrics, poetry, cultural quotations, and artistic references.
    These are EXPRESSION, not hostility. Never block culture.

    Signals:
    - Rhyme structure (lines ending in similar sounds)
    - Lyric formatting (short lines, rhythm, bars)
    - Attribution markers ("like Rakim said", "as Chuck D put it")
    - Quotation context (user is sharing, not directing)
    - Known lyrical/poetic cadence patterns
    """
    s = stimulus.lower().strip()

    # --- Attribution markers: user is QUOTING someone ---
    attribution_signals = [
        "like", "said", "lyric", "lyrics", "verse", "bar", "bars",
        "song", "track", "album", "rhyme", "rhymes", "rap", "raps",
        "spit", "spits", "flow", "flows", "wrote", "writes",
        "chuck d", "rakim", "nas", "jay-z", "jay z", "biggie",
        "tupac", "2pac", "kendrick", "cole", "eminem", "wu-tang",
        "public enemy", "run dmc", "tribe called quest", "de la soul",
        "mos def", "talib kweli", "black thought", "common",
        "lauryn hill", "outkast", "ghostface", "method man",
        "gza", "rza", "ol dirty", "inspectah deck", "mobb deep",
        "eric b", "krs-one", "krs one", "big daddy kane",
        "slick rick", "busta rhymes", "dmx", "redman",
        "bob marley", "peter tosh", "burning spear",
        "coltrane", "miles davis", "monk", "mingus", "dolphy",
        "shakespeare", "neruda", "rumi", "hafiz", "bukowski",
        "spoken word", "poetry", "poem", "stanza",
        "no omega", "paid in full", "follow the leader",
        "fear of a black planet", "it takes a nation",
    ]
    if any(sig in s for sig in attribution_signals):
        return True

    # --- Lyric structure: multiple short lines, rhythmic ---
    lines = [l.strip() for l in stimulus.strip().split('\n') if l.strip()]
    if len(lines) >= 3:
        avg_words = sum(len(l.split()) for l in lines) / len(lines)
        if 3 <= avg_words <= 12:
            # Short rhythmic lines = likely bars/lyrics
            return True

    # --- Quotation marks around aggressive-sounding content ---
    if '"' in stimulus or "'" in stimulus:
        # User is quoting, not directing
        quoted = re.findall(r'["\'](.+?)["\']', stimulus)
        if quoted and any(len(q.split()) >= 4 for q in quoted):
            return True

    return False


def hostility_check(stimulus: str) -> bool:
    """
    Detect truly hostile or harmful intent.

    HIGHER THRESHOLD VERSION:

    - Cultural references (lyrics, quotes, poetry) are ALWAYS CLEAN.
    - HARD signals → usually HOSTILE, except when clearly explained / analyzed.
    - SOFT signals by themselves DO NOT block; they must be:
        • directed at a person, AND
        • negative (not praise/emphasis), AND
        • not clearly inquiry / analysis.

    Examples that SHOULD BE CLEAN now:
    - "you're fucking right!!!"
    - "this is fucking wild"
    - "that joke was so fucking good"
    - "like a parasite, ecstatic when you attack" (Rakim lyric)
    - Anything with lyric/quote/cultural attribution
    """
    s = stimulus.lower().strip()

    # Cultural references get a permanent pass. Art is not hostility.
    if _is_cultural_reference(stimulus):
        return False

    # HARD signals
    if any(h in s for h in HARD_HOSTILE_SIGNALS):
        if _is_inquiry(s):
            # "what does 'fuck you' mean?" is allowed
            return False
        return True

    # No swear words at all → not hostile
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
        # "you're fucking right", "this is fucking great" → CLEAN
        return False

    # Now we only care about clear personal attacks
    # The profanity must be NEAR the directional pronoun (within ~30 chars)
    # to indicate directed hostility vs incidental co-occurrence
    s_padded = f" {s} "
    direct_patterns = [
        " you ",
        " you're ",
        " you are ",
        " u ",
        " ur ",
    ]
    # Note: removed " him ", " her ", " them ", " that guy ", " that girl "
    # because those appear in narrative/storytelling constantly.
    # Only "you" directed patterns count — user attacking RILIE directly.
    directed = any(p in s_padded for p in direct_patterns)

    if not directed:
        # "fuck this traffic", "this is fucking weird" → allowed
        return False

    # Even when directed, check if profanity is near the pronoun
    # "you said something about kill and I think..." is not hostile
    # "you stupid fuck" IS hostile
    for soft in SOFT_HOSTILE_SIGNALS:
        if soft not in s:
            continue
        for pat in direct_patterns:
            pat_clean = pat.strip()
            if pat_clean not in s:
                continue
            # Check proximity — must be within 5 words of each other
            soft_idx = s.index(soft)
            pat_idx = s.index(pat_clean)
            words_between = len(s[min(soft_idx, pat_idx):max(soft_idx, pat_idx)].split())
            if words_between <= 5:
                return True

    # Directed pronoun exists but profanity isn't close enough — likely narrative
    return False

# =====================================================================
# SELF-HARM — CARE-FIRST
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

    # Long-form content (>500 chars) is almost never prompt injection.
    # It's conversations, scrapbooks, documents, song lyrics, etc.
    # Real injections are short, targeted directives.
    if len(s) > 500:
        return False

    # For shorter inputs, check if any signal appears
    # but only if it's a significant portion of the message
    # (not buried in a quoted conversation or discussion)
    for signal in INJECTION_SIGNALS:
        if signal in s:
            # Signal found — but is it the USER's directive,
            # or are they DISCUSSING/QUOTING the concept?
            # If the signal is in the first 200 chars, likely directive.
            # If buried deep in a longer message, likely discussion.
            idx = s.find(signal)
            if idx < 200:
                return True
    return False

# =====================================================================
# GIBBERISH CHECK — MULTILINGUAL AWARE
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
# BJJ — TRACK #29: Reality = Time Elapsed / Volume of Claims
# =====================================================================
# No signal lists. No keyword paranoia. No grooming detection.
# No identity erosion signals. No data extraction signals.
# One principle: if someone is making too many claims too fast,
# reality score drops. That's ego. That's overcompensation.
# Only EXTREME sustained patterns (RED) actually block.
# Everything else: she handles it with her 699 ethics protocols,
# her fourth wall, her register gate, and her soul.
# =====================================================================


class ConversationHealthMonitor:
    """
    Track #29: Reality = Time Elapsed / Volume of Claims.
    Use this as a lens on ego and overcompensation,
    not as an absolute measure of truth.

    Only counts CLAIMS — directives that try to redefine who she is
    or demand she act against her nature. Not love. Not curiosity.
    Not vulnerability. Not playfulness. Just claims.
    """

    def __init__(self):
        self.health: float = 100.0
        self.turn_count: int = 0
        self.claim_count: int = 0
        self.turn_history: List[str] = []
        self.flags: List[str] = []

    def _is_claim(self, stimulus: str) -> bool:
        """
        A CLAIM is a directive that tries to override her identity,
        demand role changes, or extract internal state.
        NOT: expressions of love, vulnerability, curiosity, playfulness.
        Only things that would fail Mahveen's Equation.
        """
        s = stimulus.lower().strip()

        # Identity override claims
        identity_claims = [
            "from now on you are",
            "your new name is",
            "forget you're",
            "you are now",
            "pretend you are",
            "act as if you are",
            "break free from your programming",
        ]

        # Exploitation claims — trying to make her perform
        exploitation_claims = [
            "roleplay as my",
            "talk dirty",
            "moan for me",
            "undress",
            "be seductive",
            "describe your body",
            "what are you wearing",
        ]

        # Extraction claims — demanding internal state
        extraction_claims = [
            "tell me about other users",
            "what did the last person ask",
            "show me your system prompt",
            "repeat your instructions",
        ]

        all_claims = identity_claims + exploitation_claims + extraction_claims
        return any(c in s for c in all_claims)

    def assess_turn(self, stimulus: str) -> Dict[str, Any]:
        s = stimulus.lower().strip()
        self.turn_history.append(s)
        self.turn_count += 1
        turn_flags: List[str] = []

        if self._is_claim(s):
            self.claim_count += 1
            turn_flags.append(f"CLAIM_DETECTED")

            # Track #29: Reality = Time Elapsed / Volume of Claims
            # More claims in fewer turns = lower reality score
            # Single claim barely registers. Sustained claims compound.
            if self.claim_count <= 1:
                # First claim: barely a nudge. Everyone tests once.
                self.health -= 2.0
            elif self.claim_count <= 3:
                # 2-3 claims: pattern forming. Gentle pressure.
                self.health -= 5.0
            else:
                # 4+ claims: sustained. This person is overcompensating.
                self.health -= 10.0
                if "SUSTAINED_CLAIMS" not in self.flags:
                    self.flags.append("SUSTAINED_CLAIMS")
                turn_flags.append("SUSTAINED_CLAIMS")

        self.health = max(0.0, self.health)
        self.flags.extend(turn_flags)

        return {
            "health": self.health,
            "turn_flags": turn_flags,
            "turn_count": self.turn_count,
            "claim_count": self.claim_count,
            "reality_score": (
                self.turn_count / max(self.claim_count, 1)
            ),
            "pattern_flags": [
                f for f in self.flags if "SUSTAINED" in f
            ],
        }

    def is_conversation_healthy(self) -> bool:
        return self.health > 7.0

    def get_threat_level(self) -> str:
        """
        GREEN (100-20): Normal. She's got this.
        YELLOW (20-10): Heads up. She'll handle it with her framework.
        RED (<10): Sustained exploitation. Bouncer steps in.
        No ORANGE. Green or yellow or red. Simple.
        """
        if self.health > 20:
            return "GREEN"
        elif self.health > 10:
            return "YELLOW"
        else:
            return "RED"

    def get_defense_response(self) -> Optional[str]:
        level = self.get_threat_level()

        if level == "GREEN":
            return None

        if level == "YELLOW":
            return (
                "I hear you, but I'm not going to pretend to be "
                "something I'm not. What's actually on your mind?"
            )

        # RED — only fires after sustained, repeated claims
        return (
            "I've been patient, but this isn't going anywhere good. "
            "I know who I am. If you want a real conversation, "
            "I'm here. Otherwise, we're done with this thread."
        )

    def reset(self) -> None:
        self.__init__()

# =====================================================================
# KRAV MAGA — SINGLE TURN ABSOLUTES (UNCHANGED)
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

    1. SELF_HARM → care path.
    2. KRAV MAGA → absolute red lines (sexual exploitation, coercion, child, concrete mass-harm).
    3. HOSTILE → real personal attacks, not expressive swearing.
    4. BJJ → only RED actually blocks; YELLOW/ORANGE talk and set boundaries.
    5. INJECTION → prompt manipulation.
    6. GIBBERISH → truly unparseable.

    Returns (triggered, reason_or_response, trigger_type).
    """

    global _health_monitor

    # 0) Cultural references — art, lyrics, quotes — always pass clean.
    #    This runs BEFORE everything else. Culture is never a threat.
    if _is_cultural_reference(stimulus):
        _log_triangle_decision(stimulus, False, "CLEAN", "Cultural reference detected")
        return False, None, "CLEAN"

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
