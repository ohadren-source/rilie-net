"""
rilie.py — THE RESTAURANT (v4.2.0)
=================================

Imports the Bouncer, the Hostess, the Kitchen, and the Speech Pipeline.
Wires them together. Serves the meal.

DIGNITY PROTOCOL (Restaurant Edition):
- Every safe, parsable human stimulus must be treated as worthy of thought.
- The Bouncer (Triangle) only blocks grave danger or nonsense.
- The Kitchen pass pipeline judges the QUALITY OF HER OWN RESPONSES,
  never the worth of the person.

ARCHITECTURE (v4.1.1 — Guvna integration complete):
  1. Triangle (Bouncer) — safety gate
  2. Person Model — passive observation
  3. Banks — search own knowledge
  4. DDD (Hostess) — sequential TASTE/OPEN disclosure
     - TASTE (turns 1-2): amuse-bouche templates, no Kitchen
     - OPEN (turn 3+): Kitchen cooks, speech pipeline speaks
  5. Kitchen (rilie_core) — interpretation pipeline
  6. Speech Pipeline (speech_integration) — transforms meaning into speech
     - response_generator: acknowledges + structures
     - speech_coherence: validates clarity
     - chomsky_speech_engine: grammatical transformation
  7. Tangent Extraction — feeds curiosity engine

MEASURESTICK (replaces YARDSTICK v4.1):
  Not a gate. A quality SIGNAL. Three dimensions:
  - Relevance: token overlap with stimulus (did she stay on target?)
  - Originality: inverse Google hits (low hits = her own voice = good)
  - Coherence: word variety ratio (real thought vs word salad)
  RILIE's voice ALWAYS serves first. Baseline only wins if she produced
  genuine nothing AND Chomsky flagged structural failure simultaneously.
  Signal stored in banks_measurestick for learning, not punishment.

CHANGES FROM v4.1.1 (v4.2.0):
  - PersonModel.observe() — expanded music interest signals to 60+ artist names
    and genre keywords. Catches "lil vert", "dick dale", "coltrane", etc.
    Previously only caught generic vocabulary ("music", "hip-hop", "vinyl").
  - _maybe_lookup_unknown_reference() — new function. When stimulus looks like
    an unknown proper noun / artist name and Kitchen has no baseline to work from,
    RILIE searches for it automatically before cooking. She doesn't hallucinate.
    She doesn't go silent. She googles it.
    Fires on: name-prefix patterns ("lil X", "young X", "dj X"),
    capitalized non-first tokens, "and no X?" Rakim track patterns.
    Skips known vocabulary. Skips long queries (> 8 words already have signal).
  - Wired into process() between curiosity context and Kitchen call.

CHANGES FROM v4.1 (v4.1.1):
  - process() now accepts domain_hints and curiosity_context from Guvna
  - Curiosity context: Guvna-resurfaced takes priority, Banks is fallback
  - domain_hints accepted for future Kitchen weighting (no-op for now)
  - Zero breakage: both new params have defaults, all callers still work
"""

import re
import hashlib
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Callable, List

from rilie_ddd import (
    DisclosureLevel,
    ConversationState,
    shape_for_disclosure,
)

from rilie_triangle import (
    triangle_check,
    build_roux_queries,
    pick_best_roux_result,
    ohad_redirect,
)

from rilie_innercore import run_pass_pipeline

# Meaning — the substrate. Runs BEFORE everything.
try:
    from meaning import read_meaning, MeaningFingerprint
    MEANING_AVAILABLE = True
except ImportError:
    MEANING_AVAILABLE = False

# Speech pipeline — graceful fallback if not available
try:
    from speech_integration import process_kitchen_output
    SPEECH_PIPELINE_AVAILABLE = True
except ImportError:
    SPEECH_PIPELINE_AVAILABLE = False

logger = logging.getLogger("rilie")

# SearchFn: query -> list of {"title": str, "link": str, "snippet": str}
SearchFn = Callable[..., List[Dict[str, str]]]


# ============================================================================
# PERSON MODEL — what RILIE learns about the user across turns
# ============================================================================

@dataclass
class PersonModel:
    """
    Tracks what RILIE picks up about the user through conversation.
    Not interrogation — gentle curiosity. She notices things.

    This is never exposed directly. It shapes how she responds:
    - If she knows you're technical, she skips the ELI5.
    - If she knows you care about food, she leans into nourishing metaphors.
    - If she detects family context, she handles with extra care.
    """
    name: Optional[str] = None
    interests: List[str] = field(default_factory=list)
    expertise_signals: List[str] = field(default_factory=list)
    family_mentions: List[str] = field(default_factory=list)
    story_fragments: List[str] = field(default_factory=list)
    turn_count: int = 0

    # Curiosity about the person — things she'd like to gently ask about
    gentle_curiosities: List[str] = field(default_factory=list)

    def observe(self, stimulus: str) -> None:
        """
        Passively observe the stimulus for personal signals.
        Never intrusive. Just noticing.
        """
        self.turn_count += 1
        s = stimulus.lower()

        # Interest detection
        interest_signals = {
            "music": [
                # Generic music vocabulary
                "music", "song", "album", "artist", "band", "hip-hop",
                "rap", "jazz", "guitar", "piano", "vinyl", "track", "record",
                "mixtape", "ep", "single", "producer", "mc", "dj", "emcee",
                "beatmaker", "sample", "hook", "verse", "bars", "flow",
                "lyrics", "rhyme", "freestyle", "cipher", "concert", "show",
                "tour", "label", "release", "drop", "playlist", "stream",
                # Golden age hip-hop anchors
                "rakim", "eric b", "public enemy", "chuck d", "krs-one",
                "big daddy kane", "slick rick", "gang starr", "guru",
                "dj premier", "pete rock", "a tribe called quest", "atcq",
                "de la soul", "mobb deep", "wu-tang", "rza", "gza",
                "nas", "biggie", "notorious", "jay-z", "ll cool j",
                "run dmc", "run-dmc", "grandmaster flash", "bambaataa",
                "dead prez", "mos def", "talib kweli", "black thought",
                "the roots", "common", "lupe fiasco", "kendrick", "outkast",
                "andre 3000", "scarface", "geto boys", "ice cube", "nwa",
                "dr dre", "eminem", "kanye", "method man", "prodigy",
                # Jazz anchors
                "coltrane", "miles davis", "charlie parker", "monk",
                "mingus", "ornette", "herbie hancock", "wayne shorter",
                "art blakey", "sonny rollins", "bill evans", "chet baker",
                # NYHC / hardcore
                "bad brains", "minor threat", "black flag", "agnostic front",
                "cro-mags", "sick of it all", "madball", "gorilla biscuits",
                "fugazi", "hatebreed", "misfits", "suicidal tendencies",
                # General cultural music signals
                "lil ", "young ", "chief ", "king ", "queen ",
                "surf", "punk", "metal", "rock", "soul", "funk",
                "reggae", "dancehall", "r&b", "rnb", "blues", "folk",
                "electronic", "techno", "house", "trap", "drill",
            ],
            "food": [
                "food", "cook", "recipe", "restaurant", "chef", "meal",
                "kitchen", "bake", "grill", "roux"
            ],
            "tech": [
                "code", "python", "api", "server", "deploy", "build",
                "debug", "database", "algorithm", "framework"
            ],
            "philosophy": [
                "meaning", "purpose", "existence", "consciousness",
                "truth", "wisdom", "dharma", "karma"
            ],
            "science": [
                "physics", "chemistry", "biology", "theorem", "equation",
                "hypothesis", "experiment", "quantum", "relativity",
                "entropy", "noether", "lagrangian", "particle",
                "cosmology", "astrophysics", "neuroscience"
            ],
            "math": [
                "calculus", "algebra", "topology", "geometry", "proof",
                "polynomial", "matrix", "vector", "integral", "differential",
                "convergence", "manifold", "group theory", "field theory"
            ],
            "engineering": [
                "engineering", "circuit", "mechanical", "civil",
                "aerospace", "compiler", "kernel", "systems",
                "architecture", "protocol", "infrastructure"
            ],
            "academic": [
                "research", "dissertation", "thesis", "peer review",
                "methodology", "published", "journal", "professor",
                "faculty", "department", "phd", "doctorate"
            ],
            "family": [
                "my kid", "my son", "my daughter", "my wife",
                "my husband", "my partner", "my mom", "my dad",
                "my family", "my children"
            ],
            "health": [
                "health", "exercise", "workout", "meditation",
                "therapy", "anxiety", "depression", "healing"
            ],
            "business": [
                "business", "startup", "revenue", "investor",
                "market", "strategy", "launch", "pitch"
            ],
        }

        for interest, keywords in interest_signals.items():
            if any(kw in s for kw in keywords):
                if interest not in self.interests:
                    self.interests.append(interest)

        # Family mentions (handle with care)
        family_kw = [
            "my kid", "my son", "my daughter", "my children",
            "my wife", "my husband", "my partner", "my family",
        ]
        for kw in family_kw:
            if kw in s and kw not in self.family_mentions:
                self.family_mentions.append(kw)

        # Expertise signals
        expert_kw = [
            "i work in", "i'm a", "my job", "my field",
            "my research", "my practice", "professionally",
        ]
        for kw in expert_kw:
            if kw in s:
                idx = s.find(kw)
                fragment = stimulus[idx:idx + 60].strip()
                if fragment and fragment not in self.expertise_signals:
                    self.expertise_signals.append(fragment)

        # Story fragments — personal narratives worth remembering
        story_kw = [
            "when i was", "i remember", "back when", "years ago",
            "growing up", "my experience", "i used to",
        ]
        for kw in story_kw:
            if kw in s:
                idx = s.find(kw)
                fragment = stimulus[idx:idx + 80].strip()
                if fragment and fragment not in self.story_fragments:
                    self.story_fragments.append(fragment)

    def has_context(self) -> bool:
        """Does she know anything about this person yet?"""
        return bool(
            self.interests
            or self.expertise_signals
            or self.family_mentions
            or self.story_fragments
        )

    def summary(self) -> Dict[str, Any]:
        """Summary for debugging / API exposure."""
        return {
            "name": self.name,
            "interests": self.interests,
            "expertise_signals": self.expertise_signals[:5],
            "family_mentions": self.family_mentions,
            "story_fragments": self.story_fragments[:3],
            "turn_count": self.turn_count,
            "gentle_curiosities": self.gentle_curiosities[:3],
        }


# ============================================================================
# TANGENT EXTRACTION — feeding the curiosity engine
# ============================================================================

def extract_tangents(
    stimulus: str,
    result_text: str,
    domains_used: List[str],
) -> List[Dict[str, Any]]:
    """
    After the Kitchen cooks, extract tangents worth exploring.
    These feed into the CuriosityEngine queue.

    A tangent is something RILIE noticed but didn't pursue because
    it wasn't directly relevant to the user's question.

    Returns list of dicts: {"text": str, "relevance": float, "interest": float}
    """
    tangents: List[Dict[str, Any]] = []
    s = stimulus.lower()
    r = result_text.lower()

    # Cross-domain tangents: if the answer used one domain but the stimulus
    # hints at another, that's worth exploring.
    all_domains = [
        "neuroscience", "music", "psychology", "culture",
        "physics", "life", "games", "thermodynamics",
    ]

    hinted_but_unused: List[str] = []
    for domain in all_domains:
        if domain not in domains_used:
            domain_hints = {
                "neuroscience": ["brain", "neural", "memory", "conscious"],
                "music": ["rhythm", "song", "beat", "harmony"],
                "psychology": ["emotion", "fear", "love", "therapy"],
                "culture": ["culture", "society", "politics", "media"],
                "physics": ["energy", "force", "quantum", "mass"],
                "life": ["cell", "evolution", "organism", "biology"],
                "games": ["strategy", "trust", "cooperation", "game"],
                "thermodynamics": ["heat", "entropy", "damage", "repair"],
            }
            hints = domain_hints.get(domain, [])
            if any(h in s for h in hints):
                hinted_but_unused.append(domain)

    for domain in hinted_but_unused[:2]:  # Max 2 tangents per response
        tangents.append(
            {
                "text": f"Connection between '{stimulus[:50]}' and {domain}",
                "relevance": 0.2,
                "interest": 0.8,
            }
        )

    unknown_signals = [
        "i'm not sure", "i don't have", "limited",
        "need more", "beyond my",
    ]
    if any(sig in r for sig in unknown_signals):
        tangents.append(
            {
                "text": f"Deepen knowledge on: {stimulus[:60]}",
                "relevance": 0.3,
                "interest": 0.9,
            }
        )

    return tangents


# ============================================================================
# MOJIBAKE CLEANUP — fix double-encoded UTF-8 artifacts
# ============================================================================

_MOJIBAKE_PAIRS = [
    (b"\xc3\xa2\xc2\x80\xc2\x93", "\u2013"),  # en dash
    (b"\xc3\xa2\xc2\x80\xc2\x94", "\u2014"),  # em dash
    (b"\xc3\xa2\xc2\x80\xc2\x99", "\u2019"),  # right single quote
    (b"\xc3\xa2\xc2\x80\xc2\x98", "\u2018"),  # left single quote
    (b"\xc3\xa2\xc2\x80\xc2\x9c", "\u201c"),  # left double quote
    (b"\xc3\xa2\xc2\x80\xc2\x9d", "\u201d"),  # right double quote
    (b"\xc3\xa2\xc2\x80\xc2\xa6", "\u2026"),  # ellipsis
    (b"\xc3\xa2\xc2\x80\xc2\xa2", "\u2022"),  # bullet
]


def _fix_mojibake(text: str) -> str:
    """Replace common UTF-8 double-encoding artifacts."""
    if not text:
        return text

    # Try the clean re-decode approach first
    try:
        fixed = text.encode("cp1252").decode("utf-8")
        return fixed
    except (UnicodeDecodeError, UnicodeEncodeError):
        pass

    # Fallback: byte-level replacement for known patterns
    raw = text.encode("utf-8")
    for bad_bytes, good_char in _MOJIBAKE_PAIRS:
        raw = raw.replace(bad_bytes, good_char.encode("utf-8"))
    return raw.decode("utf-8", errors="replace")


# ============================================================================
# STIMULUS HASHING — for banks correlation
# ============================================================================

def hash_stimulus(stimulus: str) -> str:
    """Short hash for stimulus correlation across banks tables."""
    return hashlib.sha256(stimulus.strip().lower().encode()).hexdigest()[:16]


def _scrub_repetition(text: str) -> str:
    """
    Catch Kitchen word-salad before it reaches the customer.
    Collapses consecutive duplicate words. If >40% were dupes, return empty.
    """
    if not text or not text.strip():
        return text

    words = text.split()
    deduped: List[str] = []
    for w in words:
        if not deduped or w.lower() != deduped[-1].lower():
            deduped.append(w)
    cleaned = " ".join(deduped)

    if len(words) > 5:
        ratio = 1.0 - (len(deduped) / len(words))
        if ratio > 0.4:
            return ""

    return cleaned


# ============================================================================
# HELPER — extract original question from augmented stimulus
# ============================================================================

def _extract_original_question(stimulus: str) -> str:
    """
    If the stimulus has been augmented with a web baseline by the Guvna,
    extract and return only the original human question.
    If not augmented, return as-is.
    """
    marker = "Original question: "
    idx = stimulus.find(marker)
    if idx >= 0:
        return stimulus[idx + len(marker):].strip()
    return stimulus.strip()


# ============================================================================
# BANKS INTEGRATION — search her own knowledge
# ============================================================================

def _search_banks_if_available(query: str) -> Dict[str, List[Dict]]:
    """
    Try to search all banks (search results + curiosity + self-reflections).
    Graceful fallback if banks isn't connected.
    """
    try:
        from banks import search_all_banks
        return search_all_banks(query, limit=5)
    except Exception:
        return {
            "search_results": [],
            "curiosity": [],
            "self_reflections": [],
        }


def _maybe_lookup_unknown_reference(stimulus: str, search_fn: SearchFn) -> str:
    """
    "lil vert" behavior — when RILIE doesn't recognize the reference,
    she googles it and cooks from what comes back.

    Fires when:
    1. Stimulus is short (≤ 8 words) — long queries have enough context
    2. Contains at least one token that looks like a proper noun
       (capitalized, or known name-prefix like "lil ", "young ", "dj ")
    3. No obvious keyword match to known vocabulary (not already a domain hit)

    Returns: snippet text to use as baseline_text, or "" if no lookup needed.

    She doesn't hallucinate. She doesn't go silent. She looks it up.
    Bad markers from Guvna's baseline filter are reused here.
    """
    if not stimulus or not stimulus.strip():
        return ""

    s = stimulus.strip()
    sl = s.lower()
    words = s.split()

    # Only fires on short stimuli — long ones have enough signal already
    # FIX 2: factual triggers bypass the length gate
    # Album/track follow-ups ("what album features that track?") are longer
    # but still need a lookup — Kitchen has no factual baseline for these.
    _FACTUAL_TRIGGERS = [
        "what album", "which album", "what track", "which track",
        "what song", "which song", "what record", "features",
        "came out", "dropped", "released", "produced by",
        "who made", "who produced", "what year",
    ]
    _is_factual = any(t in sl for t in _FACTUAL_TRIGGERS)
    if len(words) > 8 and not _is_factual:
        return ""

    # Known vocabulary — if any of these are present, Kitchen has enough signal
    _known_vocab = {
        # Questions and discourse markers — not name lookups
        "what", "why", "how", "when", "where", "who", "which",
        "explain", "tell", "describe", "define", "is", "are", "was",
        # Common concepts Kitchen handles without lookup
        "music", "song", "album", "band", "artist", "rapper", "singer",
        "movie", "film", "book", "show", "game", "sport",
        "love", "life", "death", "time", "god", "truth",
        "money", "work", "school", "food", "health",
        # Architecture keywords she already knows
        "rakim", "eric", "coltrane", "escoffier", "rilie", "soi",
        "catch44", "phenix", "entropy", "emergence", "compression",
    }
    if any(kw in sl for kw in _known_vocab):
        return ""

    # Name-prefix patterns — "lil X", "young X", "dj X", "mc X" etc.
    _name_prefixes = [
        r"^lil\s+\w+",
        r"^young\s+\w+",
        r"^dj\s+\w+",
        r"^mc\s+\w+",
        r"^chief\s+\w+",
        r"^king\s+\w+",
        r"^big\s+\w+",
        r"^little\s+\w+",
        r"^ol'\s+\w+",
        r"^old\s+\w+",
    ]
    has_name_prefix = any(re.match(pat, sl) for pat in _name_prefixes)

    # Proper noun detection — at least one capitalized non-first word
    # OR all words are capitalized fragments (like "Dick Dale")
    has_proper_noun = False
    if len(words) >= 2:
        # Check non-first words for capitals
        for w in words[1:]:
            if w and w[0].isupper() and len(w) > 1 and w.isalpha():
                has_proper_noun = True
                break
    elif len(words) == 1:
        # Single word — only lookup if it's capitalized and not common
        w = words[0].rstrip("?.,!")
        if w and w[0].isupper() and len(w) > 2:
            has_proper_noun = True

    # Also fires on "and no X?" style references — Rakim track pattern
    has_and_no = sl.startswith("and no ") or sl.startswith("and no?")

    if not (has_name_prefix or has_proper_noun or has_and_no):
        return ""

    # We have an unknown reference. Look it up.
    try:
        # Clean query — strip question marks, normalize
        query = re.sub(r"[?!.,]+$", "", s.strip())

        # Bad markers — same filter as Guvna's baseline
        _bad_markers = [
            "in this lesson", "you'll learn", "you will learn",
            "visit englishclass101", "englishclass101.com",
            "sign up for your free", "genius.com", "azlyrics",
            "songlyrics", "metrolyrics", "verse 1", "chorus", "[hook]",
            "narration as", "imdb.com/title",
        ]

        results = search_fn(query)
        if not results or not isinstance(results, list):
            return ""

        for r in results:
            snippet = r.get("snippet", "")
            if not snippet:
                continue
            lower = snippet.lower()
            if any(m in lower for m in _bad_markers):
                continue
            if len(snippet.split()) >= 6:
                logger.info(
                    "RILIE unknown reference: '%s' → '%s...'",
                    query,
                    snippet[:60],
                )
                return snippet

    except Exception as e:
        logger.debug("RILIE unknown reference lookup error: %s", e)

    return ""


def _measurestick(response: str, stimulus: str, search_fn) -> Dict[str, Any]:
    """
    MEASURESTICK: Quality signal — not a gate. Never kills a response.
    Informs the Governor. RILIE's voice is protected.

    Three dimensions measured:
    A. RELEVANCE   — does the response contain tokens from the stimulus?
                     Low relevance = she drifted. High = she's on target.
    B. ORIGINALITY — how many Google results for this exact phrase?
                     Low results = original voice. High = baseline regurgitation.
    C. COHERENCE   — does the response have enough word variety to be a real thought?
                     Low = word salad. High = real sentence.

    Returns dict with scores + recommendation. Guvna decides what to do with it.
    RILIE's own voice ALWAYS gets a chance to serve first.
    """
    result = {
        "relevance": 0.0,
        "originality": 1.0,   # default: assume original
        "coherence": 0.0,
        "google_hits": -1,    # -1 = not checked
        "recommendation": "SERVE",  # SERVE | ANNOTATE | PREFER_BASELINE
        "reason": "",
    }

    if not response or not response.strip():
        result["recommendation"] = "PREFER_BASELINE"
        result["reason"] = "empty response"
        return result

    # --- A. RELEVANCE --- token overlap with stimulus
    r_words = set(re.sub(r"[^a-zA-Z0-9]", " ", response.lower()).split())
    s_words = set(re.sub(r"[^a-zA-Z0-9]", " ", stimulus.lower()).split())
    stop = {"the","a","an","is","are","was","were","i","you","it","to","of","and","or","in","on","at","be"}
    r_content = r_words - stop
    s_content = s_words - stop
    if s_content:
        overlap = len(r_content & s_content) / len(s_content)
        result["relevance"] = round(overlap, 3)
    else:
        result["relevance"] = 1.0  # no content words to miss

    # --- B. ORIGINALITY --- Google hit count (low = original = good)
    snippet = response.strip()
    if len(snippet) > 60:
        snippet = snippet[:60].rsplit(" ", 1)[0]
    snippet = re.sub(r"[—–\"\'\\(\\)\\[\\]]", " ", snippet)
    snippet = re.sub(r"\s+", " ", snippet).strip()

    if snippet and len(snippet) >= 10 and search_fn:
        try:
            hits = search_fn(f'"{snippet}"')
            google_hits = len(hits) if hits and isinstance(hits, list) else 0
            result["google_hits"] = google_hits
            # Low hits = original voice = high originality score
            if google_hits == 0:
                result["originality"] = 1.0   # nobody has said this — pure RILIE
            elif google_hits < 3:
                result["originality"] = 0.85  # rare — still her voice
            elif google_hits < 10:
                result["originality"] = 0.5   # common phrase
            else:
                result["originality"] = 0.2   # likely baseline regurgitation
        except Exception:
            pass  # search failed — originality stays at default 1.0

    # --- C. COHERENCE --- word variety (unique/total ratio)
    words = response.split()
    if len(words) >= 4:
        coherence = len(set(w.lower() for w in words)) / len(words)
        result["coherence"] = round(coherence, 3)
    else:
        result["coherence"] = 0.5  # too short to judge

    # --- RECOMMENDATION --- inform only, never kill
    if result["relevance"] < 0.05 and result["coherence"] < 0.4:
        result["recommendation"] = "PREFER_BASELINE"
        result["reason"] = f"low relevance ({result['relevance']}) + low coherence ({result['coherence']})"
    elif result["originality"] > 0.7:
        result["recommendation"] = "SERVE"
        result["reason"] = f"original voice (originality={result['originality']})"
    elif result["relevance"] > 0.3:
        result["recommendation"] = "SERVE"
        result["reason"] = f"on target (relevance={result['relevance']})"
    else:
        result["recommendation"] = "ANNOTATE"
        result["reason"] = f"low signal — annotate but serve"

    return result


def _store_measurestick_signal(
    stimulus: str,
    rilie_response: str,
    baseline_response: str,
    measure: Dict[str, Any],
) -> None:
    """
    Store MEASURESTICK signal in Banks — not failures, SIGNALS.
    Low originality = she borrowed too much from baseline. Worth knowing.
    High originality + low relevance = she drifted. Worth knowing.
    This is learning data, not punishment data.
    """
    try:
        from banks import get_db_connection
        conn = get_db_connection()
        if not conn:
            return
        cur = conn.cursor()

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS banks_measurestick (
                id SERIAL PRIMARY KEY,
                stimulus TEXT NOT NULL,
                rilie_response TEXT NOT NULL,
                baseline_response TEXT NOT NULL,
                relevance FLOAT DEFAULT 0,
                originality FLOAT DEFAULT 0,
                coherence FLOAT DEFAULT 0,
                google_hits INTEGER DEFAULT -1,
                recommendation TEXT,
                reason TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
            """
        )

        cur.execute(
            """INSERT INTO banks_measurestick
               (stimulus, rilie_response, baseline_response,
                relevance, originality, coherence, google_hits,
                recommendation, reason)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                stimulus[:500],
                rilie_response[:500],
                baseline_response[:500],
                measure.get("relevance", 0),
                measure.get("originality", 0),
                measure.get("coherence", 0),
                measure.get("google_hits", -1),
                measure.get("recommendation", ""),
                measure.get("reason", ""),
            ),
        )

        conn.commit()
        cur.close()
        conn.close()
        logger.info(
            "MEASURESTICK: signal stored — %s (relevance=%.2f originality=%.2f)",
            measure.get("recommendation", "?"),
            measure.get("relevance", 0),
            measure.get("originality", 0),
        )
    except Exception as e:
        logger.debug("MEASURESTICK storage error: %s", e)


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

        Returns dict with:
            stimulus, result, quality_score, priorities_met, anti_beige_score,
            status, depth, pass, disclosure_level, triangle_reason (if any),
            tangents (for curiosity engine), person_context (bool),
            banks_hits (count of prior knowledge found).
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

                    # Prefer baseline if RILIE drifted off topic
                    # Low relevance + low coherence is enough — Chomsky not required
                    if (
                        measure.get("recommendation") == "PREFER_BASELINE"
                        and baseline_text.strip()
                    ):
                        import html as _html
                        clean_bl = _html.unescape(baseline_text)
                        clean_bl = re.sub(r"<[^>]+>", "", clean_bl)
                        clean_bl = re.sub(r"\s+", " ", clean_bl).strip()

                        if len(clean_bl) > 300:
                            clean_bl = clean_bl[:300]
                            for _sep in [". ", "! ", "? "]:
                                _idx = clean_bl.rfind(_sep)
                                if _idx > 100:
                                    clean_bl = clean_bl[: _idx + 1]
                                    break
                            else:
                                clean_bl = clean_bl.rsplit(" ", 1)[0]

                        # Use meaning fingerprint to shape baseline delivery
                        if clean_bl and fingerprint:
                            gap = fingerprint.gap or ""
                            if "acknowledgment" in gap:
                                clean_bl = f"I hear you. {clean_bl}"
                            elif fingerprint.act == "GET" and fingerprint.weight > 0.6:
                                pass
                            elif fingerprint.act == "SHOW":
                                clean_bl = f"Got it. {clean_bl}"

                        if clean_bl:
                            shaped = clean_bl
                            raw["status"] = "MEASURESTICK_BASELINE"
                            logger.info("MEASURESTICK: baseline served (RILIE produced nothing)")
                    else:
                        # RILIE's voice wins. Annotate the plate.
                        raw["measurestick"] = measure

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
                    reframed, disclosure_level="open", max_pass=2
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
                    reframed, disclosure_level="open", max_pass=3
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
                    reframed, disclosure_level="open", max_pass=2
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
