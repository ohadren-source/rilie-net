"""
rilie.py — THE RESTAURANT (v4.0)
=================================
Imports the Bouncer, the Hostess, the Kitchen, and the Speech Pipeline.
Wires them together. Serves the meal.

DIGNITY PROTOCOL (Restaurant Edition):
  - Every safe, parsable human stimulus must be treated as worthy of thought.
  - The Bouncer (Triangle) only blocks grave danger or nonsense.
  - The Kitchen pass pipeline judges the QUALITY OF HER OWN RESPONSES,
    never the worth of the person.

ARCHITECTURE (v4.0 — fits new module schema):
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

CHANGES FROM v3.3:
  - Removed déjà vu system (replaced by TASTE/OPEN sequential model)
  - Wired speech_integration pipeline for OPEN-level responses
  - shape_for_disclosure signature simplified (no kwargs)
  - ConversationState simplified (no dejavu methods)
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

from rilie_core import run_pass_pipeline

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
            "music": ["music", "song", "album", "artist", "band", "hip-hop",
                      "rap", "jazz", "guitar", "piano", "vinyl"],
            "food": ["food", "cook", "recipe", "restaurant", "chef", "meal",
                     "kitchen", "bake", "grill", "roux"],
            "tech": ["code", "python", "api", "server", "deploy", "build",
                     "debug", "database", "algorithm", "framework"],
            "philosophy": ["meaning", "purpose", "existence", "consciousness",
                          "truth", "wisdom", "dharma", "karma"],
            "science": ["physics", "chemistry", "biology", "theorem", "equation",
                       "hypothesis", "experiment", "quantum", "relativity",
                       "entropy", "noether", "lagrangian", "particle",
                       "cosmology", "astrophysics", "neuroscience"],
            "math": ["calculus", "algebra", "topology", "geometry", "proof",
                    "polynomial", "matrix", "vector", "integral", "differential",
                    "convergence", "manifold", "group theory", "field theory"],
            "engineering": ["engineering", "circuit", "mechanical", "civil",
                           "aerospace", "compiler", "kernel", "systems",
                           "architecture", "protocol", "infrastructure"],
            "academic": ["research", "dissertation", "thesis", "peer review",
                        "methodology", "published", "journal", "professor",
                        "faculty", "department", "phd", "doctorate"],
            "family": ["my kid", "my son", "my daughter", "my wife",
                      "my husband", "my partner", "my mom", "my dad",
                      "my family", "my children"],
            "health": ["health", "exercise", "workout", "meditation",
                      "therapy", "anxiety", "depression", "healing"],
            "business": ["business", "startup", "revenue", "investor",
                        "market", "strategy", "launch", "pitch"],
        }

        for interest, keywords in interest_signals.items():
            if any(kw in s for kw in keywords):
                if interest not in self.interests:
                    self.interests.append(interest)

        # Family mentions (handle with care)
        family_kw = ["my kid", "my son", "my daughter", "my children",
                     "my wife", "my husband", "my partner", "my family"]
        for kw in family_kw:
            if kw in s and kw not in self.family_mentions:
                self.family_mentions.append(kw)

        # Expertise signals
        expert_kw = ["i work in", "i'm a", "my job", "my field",
                     "my research", "my practice", "professionally"]
        for kw in expert_kw:
            if kw in s:
                idx = s.find(kw)
                fragment = stimulus[idx:idx + 60].strip()
                if fragment and fragment not in self.expertise_signals:
                    self.expertise_signals.append(fragment)

        # Story fragments — personal narratives worth remembering
        story_kw = ["when i was", "i remember", "back when", "years ago",
                    "growing up", "my experience", "i used to"]
        for kw in story_kw:
            if kw in s:
                idx = s.find(kw)
                fragment = stimulus[idx:idx + 80].strip()
                if fragment and fragment not in self.story_fragments:
                    self.story_fragments.append(fragment)

    def has_context(self) -> bool:
        """Does she know anything about this person yet?"""
        return bool(self.interests or self.expertise_signals or
                    self.family_mentions or self.story_fragments)

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
    # hints at another, that's worth exploring
    all_domains = ["neuroscience", "music", "psychology", "culture",
                   "physics", "life", "games", "thermodynamics"]

    hinted_but_unused = []
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
        tangents.append({
            "text": f"Connection between '{stimulus[:50]}' and {domain}",
            "relevance": 0.2,
            "interest": 0.8,
        })

    unknown_signals = ["i'm not sure", "i don't have", "limited",
                       "need more", "beyond my"]
    if any(sig in r for sig in unknown_signals):
        tangents.append({
            "text": f"Deepen knowledge on: {stimulus[:60]}",
            "relevance": 0.3,
            "interest": 0.9,
        })

    return tangents


# ============================================================================
# MOJIBAKE CLEANUP — fix double-encoded UTF-8 artifacts
# ============================================================================

_MOJIBAKE_PAIRS = [
    (b"\xc3\xa2\xc2\x80\xc2\x93", "\u2013"),   # en dash
    (b"\xc3\xa2\xc2\x80\xc2\x94", "\u2014"),   # em dash
    (b"\xc3\xa2\xc2\x80\xc2\x99", "\u2019"),   # right single quote
    (b"\xc3\xa2\xc2\x80\xc2\x98", "\u2018"),   # left single quote
    (b"\xc3\xa2\xc2\x80\xc2\x9c", "\u201c"),   # left double quote
    (b"\xc3\xa2\xc2\x80\xc2\x9d", "\u201d"),   # right double quote
    (b"\xc3\xa2\xc2\x80\xc2\xa6", "\u2026"),   # ellipsis
    (b"\xc3\xa2\xc2\x80\xc2\xa2", "\u2022"),   # bullet
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
    deduped: list = []
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
        return {"search_results": [], "curiosity": [], "self_reflections": []}


def _google_yardstick(response: str, search_fn) -> int:
    """
    GOOGLE YARDSTICK: Search her response in quotes.
    Returns the number of results found.
    < 9 results = nobody has ever said this = not a real sentence.
    """
    # Take the first ~60 chars to keep the query reasonable
    snippet = response.strip()
    if len(snippet) > 60:
        snippet = snippet[:60].rsplit(" ", 1)[0]
    # Strip special chars that break quoted search
    snippet = re.sub(r"[—–\"\'\(\)\[\]]", " ", snippet)
    snippet = re.sub(r"\s+", " ", snippet).strip()
    if not snippet or len(snippet) < 10:
        return 999  # Too short to judge, let it pass

    query = f'"{snippet}"'
    try:
        results = search_fn(query)
        if results and isinstance(results, list):
            return len(results)
        return 0
    except Exception:
        return 999  # Search failed, let it pass


def _store_yardstick_failure(
    stimulus: str,
    bad_response: str,
    correct_response: str,
    result_count: int,
) -> None:
    """
    Store a yardstick failure in Banks so she never says it again.
    Bad response + correct response = learning pair.
    """
    try:
        from banks import get_db_connection
        conn = get_db_connection()
        if not conn:
            return
        cur = conn.cursor()
        # Ensure table exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS banks_yardstick (
                id SERIAL PRIMARY KEY,
                stimulus TEXT NOT NULL,
                bad_response TEXT NOT NULL,
                correct_response TEXT NOT NULL,
                result_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute(
            """INSERT INTO banks_yardstick
               (stimulus, bad_response, correct_response, result_count)
               VALUES (%s, %s, %s, %s)""",
            (stimulus[:500], bad_response[:500], correct_response[:500], result_count),
        )
        conn.commit()
        cur.close()
        conn.close()
        logger.info("YARDSTICK: stored failure for '%s'", stimulus[:50])
    except Exception as e:
        logger.debug("YARDSTICK storage error: %s", e)


# ============================================================================
# THE RESTAURANT
# ============================================================================

class RILIE:
    """
    Recursive Intelligence Living Integration Engine (Act 4 — The Restaurant).

    AXIOM: DISCOURSE DICTATES DISCLOSURE
    She reveals through conversation. Mystery is the mechanism.

    Restaurant Flow (v4.0):
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
        self.version = "4.1"
        self.tracks_experienced = 0

        # Conversation state lives across turns per RILIE instance.
        self.conversation = ConversationState()

        # Person model — what she learns about the user.
        self.person = PersonModel()

        # Déjà vu tracking — lightweight, no escalation.
        # Just: what cluster are we in, and how many times.
        self._dejavu_cluster: str = ""
        self._dejavu_count: int = 0
        self._dejavu_responses: List[str] = []  # what she said for this cluster

        # Offline 9-track Roux (RInitials / ROUX.json) would be wired here if used.
        self.rouxseeds: Dict[str, Dict[str, Any]] = rouxseeds or {}

        # Optional live search function (Brave / Google wrapper) injected by API.
        self.searchfn: Optional[SearchFn] = searchfn

    # ---------------------------------------------------------------------
    # Core entrypoint
    # ---------------------------------------------------------------------

    def process(
        self,
        stimulus: str,
        maxpass: int = 3,
        searchfn: Optional[SearchFn] = None,
        baseline_text: str = "",
        from_file: bool = False,
    ) -> Dict[str, Any]:
        """
        Public entrypoint.

        Args:
            stimulus:  user input (may be augmented with baseline by Guvna)
            maxpass:   max interpretation passes (default 3, cap 9)
            searchfn:  optional callable (query: str -> list[dict]) for Roux Search.
                       If None, falls back to instance-level searchfn.
            from_file: if True, stimulus came from a file upload (admin/trusted)
                       and Triangle injection check is relaxed.

        Returns dict with:
            stimulus, result, quality_score, priorities_met, anti_beige_score,
            status, depth, pass, disclosure_level, triangle_reason (if any),
            tangents (for curiosity engine), person_context (bool),
            banks_hits (count of prior knowledge found).
        """
        stimulus = stimulus or ""
        stimulus = stimulus.strip()

        # Extract the original human question for domain detection and Kitchen cooking.
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

        # -----------------------------------------------------------------
        # MEANING — the substrate. First read. Birth certificate.
        # Runs BEFORE Triangle, BEFORE Kitchen, BEFORE everything.
        # The fingerprint is READ-ONLY downstream.
        # -----------------------------------------------------------------
        fingerprint = None
        if MEANING_AVAILABLE:
            try:
                fingerprint = read_meaning(original_question)
                logger.info(
                    "MEANING: pulse=%.2f act=%s obj=%s weight=%.2f gap=%s",
                    fingerprint.pulse, fingerprint.act, fingerprint.object,
                    fingerprint.weight, fingerprint.gap or "—"
                )
                # Dead input — no pulse, no point cooking
                if not fingerprint.is_alive():
                    self.conversation.record_exchange(original_question, "")
                    return {
                        "result": "",
                        "status": "DEAD_INPUT",
                        "meaning": fingerprint.to_dict(),
                    }
            except Exception as e:
                logger.debug("Meaning fingerprint error: %s", e)

        # -----------------------------------------------------------------
        # Person Model — passively observe before anything else
        # -----------------------------------------------------------------
        self.person.observe(original_question)

        # -----------------------------------------------------------------
        # Gate 0: Triangle (Bouncer)
        # File uploads from admin are trusted — skip injection check.
        # Triangle still runs for self-harm, hostile, etc. but injection
        # false positives on long-form content are suppressed.
        # -----------------------------------------------------------------
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
            elif trigger_type in ("SEXUAL_EXPLOITATION", "COERCION",
                                  "CHILD_SAFETY", "MASS_HARM"):
                response = (
                    "I can't engage with that. "
                    "If you have a real question, I'm here."
                )
            elif trigger_type == "BEHAVIORAL_RED":
                # Track #29 caught sustained claims. Use defense response.
                response = reason if reason and len(reason) > 30 else (
                    "I've been patient, but this isn't going anywhere good. "
                    "I know who I am. If you want a real conversation, I'm here."
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

        # -----------------------------------------------------------------
        # Banks Pre-Check — search her own knowledge
        # -----------------------------------------------------------------
        banks_knowledge = _search_banks_if_available(original_question)
        banks_hits = (
            len(banks_knowledge.get("search_results", []))
            + len(banks_knowledge.get("curiosity", []))
            + len(banks_knowledge.get("self_reflections", []))
        )

        # If curiosity found something relevant, fold it into context
        curiosity_context = ""
        curiosity_insights = banks_knowledge.get("curiosity", [])
        if curiosity_insights:
            top_insight = curiosity_insights[0]
            insight_text = top_insight.get("insight", "")
            if insight_text:
                curiosity_context = f"[Own discovery: {insight_text[:200]}]"
                logger.info("RILIE recalled her own insight for: %s",
                           original_question[:50])

        # -----------------------------------------------------------------
        # Déjà Vu Check — is this stimulus ~identical to recent ones?
        #
        # Not a system. Not stages. Just awareness.
        # If the same thing comes in 3+ times, figure out WHY and take
        # ONE new swing from a different angle. Dayenu. Move on.
        #
        # Three contexts:
        #   1. She failed to explain → her clarity problem
        #   2. She got it wrong → her accuracy problem
        #   3. They're looping → redirect responsibility
        # -----------------------------------------------------------------
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

        # -----------------------------------------------------------------
        # DDD / Hostess — disclosure level (internal state only)
        # TASTE is a flag, not a gate. She always speaks through the pipeline.
        # -----------------------------------------------------------------
        disclosure = self.conversation.disclosure_level

        # -----------------------------------------------------------------
        # SAUCIER — Roux Search (EVERY TURN)
        # 1. Chomsky parses stimulus → holy trinity
        # 2. Holy trinity × cities × channels → Brave
        # 3. Score results against tone/context
        # 4. Pick 1 — the best match
        # This is her food. Without it she's thinking on empty stomach.
        # -----------------------------------------------------------------
        roux_material = ""
        holy_trinity = []

        # Step 1: Chomsky parse for holy trinity
        try:
            from ChomskyAtTheBit import extract_holy_trinity_for_roux, infer_time_bucket
            holy_trinity = extract_holy_trinity_for_roux(original_question)
            time_bucket = infer_time_bucket(original_question)
            logger.info("ROUX: holy_trinity=%s time=%s", holy_trinity, time_bucket)
        except ImportError:
            # Chomsky not available — fall back to raw words
            words = [w for w in original_question.split() if len(w) > 2][:3]
            holy_trinity = words if words else ["question"]
            time_bucket = "unknown"
            logger.info("ROUX: no Chomsky, raw words=%s", holy_trinity)

        # Step 2: Build Roux queries from holy trinity and fire Brave
        # DISABLED: Google baseline from Guvna is the only external search now.
        # Internal domain match + SOi comparison handle the rest.
        roux_material = ""

        # -----------------------------------------------------------------
        # SOiOS CYCLE — perceive → decide → think → emerge
        # Runs on Roux material. Is this worth saying?
        # -----------------------------------------------------------------
        soios_emergence = 0.0
        try:
            from SOiOS import RIHybridBrain
            soios = RIHybridBrain()
            # Stimulus strength from roux_material presence
            stimulus_strength = 0.8 if roux_material else 0.3
            cycle = soios.run_cycle(
                stimulus=stimulus_strength,
                claim=original_question,
                deed=roux_material or original_question,
            )
            soios_emergence = cycle.get("emergence", 0.0)
            logger.info("SOiOS: emergence=%.3f intelligence=%.3f",
                        soios_emergence, cycle.get("intelligence", 0.0))
        except ImportError:
            logger.debug("SOiOS not available — proceeding without")
        except Exception as e:
            logger.warning("SOiOS cycle failed: %s", e)

        # -----------------------------------------------------------------
        # Kitchen — interpretation passes (every turn, TASTE or OPEN)
        # Fed by: clean stimulus + baseline_text (from Guvna's Google search)
        # Internal domains + SOi comparison handle the rest.
        # -----------------------------------------------------------------
        kitchen_input = original_question
        if curiosity_context:
            kitchen_input = f"{curiosity_context}\n\n{kitchen_input}"

        # Strip any leaked markup from previous augmentation
        kitchen_input = re.sub(r"\[WEB_BASELINE\].*?\[USER_QUERY\]\s*", "", kitchen_input, flags=re.DOTALL)
        kitchen_input = re.sub(r"\[ROUX:.*?\]\s*\n*", "", kitchen_input, flags=re.DOTALL)
        kitchen_input = kitchen_input.strip()

        raw = run_pass_pipeline(
            kitchen_input,
            disclosure_level=disclosure.value,
            max_pass=maxpass_int,
            prior_responses=self.conversation.response_history,
            baseline_text=baseline_text,
        )

        status = str(raw.get("status", "OK") or "OK").upper()

        # -----------------------------------------------------------------
        # Tangent Extraction — feed the curiosity engine
        # -----------------------------------------------------------------
        result_text = str(raw.get("result", "") or "")
        domains_used = []
        if "domain" in raw:
            domains_used = [raw["domain"]] if isinstance(raw["domain"], str) else []

        tangents = extract_tangents(original_question, result_text, domains_used)
        if tangents:
            raw["tangents"] = tangents

        # -----------------------------------------------------------------
        # Courtesy Exit (Ohad) when Kitchen truly cannot find a clean answer
        # -----------------------------------------------------------------
        if status == "COURTESYEXIT":
            roux_result = ""
            if active_search:
                try:
                    queries = build_roux_queries(original_question)
                    all_results: List[Dict[str, str]] = []
                    for q in queries:
                        try:
                            try:
                                results = active_search(q)  # type: ignore[arg-type]
                            except TypeError:
                                results = active_search(q, 5)  # type: ignore[arg-type]
                        except Exception:
                            break
                        if results:
                            all_results.extend(results)
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

        # -----------------------------------------------------------------
        # Speech Pipeline — transform Kitchen's semantic output into speech
        # response_generator → speech_coherence → chomsky_speech_engine
        # -----------------------------------------------------------------
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
                    "Speech pipeline failed: %s — using raw Kitchen output", e
                )

        # -----------------------------------------------------------------
        # Normal path — finalize and record
        # -----------------------------------------------------------------
        shaped = raw.get("result", result_text)

        # Let the Hostess shape what is actually spoken (TASTE vs OPEN)
        shaped = shape_for_disclosure(shaped, self.conversation)

        # QUALITY GATE 1: catch Kitchen word-salad before serving
        shaped = _scrub_repetition(shaped)
        if not shaped or not shaped.strip():
            shaped = ohad_redirect("")
            raw["status"] = "COURTESYEXIT"

        # QUALITY GATE 2: CHOMSKY + GOOGLE YARDSTICK (2x reinforced learning)
        # Gate A: Chomsky — can this even be parsed as a sentence?
        # Gate B: Google — has anyone ever said anything like this?
        # Both failures store to Banks. She learns from both.
        if (disclosure.value != "taste"
            and shaped and len(shaped.split()) > 4
            and baseline_text.strip()):

            rejected = False

            # GATE A: CHOMSKY — structural check
            try:
                from ChomskyAtTheBit import classify_stimulus
                parsed = classify_stimulus(shaped)
                if parsed["category"] in ("words", "incomplete"):
                    logger.warning(
                        "CHOMSKY REJECT (%s): '%s'",
                        parsed["category"], shaped[:80]
                    )
                    _store_yardstick_failure(
                        stimulus=original_question,
                        bad_response=shaped,
                        correct_response=baseline_text,
                        result_count=-1,  # -1 = Chomsky reject
                    )
                    rejected = True
            except Exception as e:
                logger.debug("Chomsky gate error: %s", e)

            # GATE B: GOOGLE YARDSTICK — only if Chomsky passed
            if not rejected and active_search:
                try:
                    yardstick_result = _google_yardstick(shaped, active_search)
                    if yardstick_result < 9:
                        logger.warning(
                            "YARDSTICK REJECT (%d results): '%s'",
                            yardstick_result, shaped[:80]
                        )
                        _store_yardstick_failure(
                            stimulus=original_question,
                            bad_response=shaped,
                            correct_response=baseline_text,
                            result_count=yardstick_result,
                        )
                        rejected = True
                except Exception as e:
                    logger.debug("Yardstick gate error: %s", e)

            # If either gate rejected, serve modified baseline
            if rejected:
                import html as _html
                clean_bl = _html.unescape(baseline_text)
                clean_bl = re.sub(r"<[^>]+>", "", clean_bl)
                clean_bl = re.sub(r"\s+", " ", clean_bl).strip()
                if len(clean_bl) > 300:
                    clean_bl = clean_bl[:300]
                    for _sep in [". ", "! ", "? "]:
                        _idx = clean_bl.rfind(_sep)
                        if _idx > 100:
                            clean_bl = clean_bl[:_idx + 1]
                            break
                    else:
                        clean_bl = clean_bl.rsplit(" ", 1)[0]

                # Use meaning fingerprint to shape HOW she serves the baseline
                if clean_bl and fingerprint:
                    gap = fingerprint.gap or ""
                    if "acknowledgment" in gap:
                        # They're hurting — lead with care, then answer
                        clean_bl = f"I hear you. {clean_bl}"
                    elif fingerprint.act == "GET" and fingerprint.weight > 0.6:
                        # Heavy question — direct answer, no filler
                        pass  # serve as-is, don't decorate
                    elif fingerprint.act == "SHOW":
                        # They showed something — validate first
                        clean_bl = f"Got it. {clean_bl}"

                if clean_bl:
                    shaped = clean_bl
                    raw["status"] = "YARDSTICK_BASELINE"

        # Record what she actually said
        self.conversation.record_exchange(original_question, shaped)

        # Mojibake cleanup — fix double-encoded UTF-8 artifacts
        shaped = _fix_mojibake(shaped)

        # Make sure downstream sees the shaped text
        raw["result"] = shaped
        raw["disclosure_level"] = disclosure.value
        raw["triangle_reason"] = "CLEAN"
        raw["person_context"] = self.person.has_context()
        raw["banks_hits"] = banks_hits
        raw["stimulus_hash"] = hash_stimulus(original_question)

        # Attach meaning fingerprint — birth certificate rides with the plate
        if fingerprint:
            raw["meaning"] = fingerprint.to_dict()

        return raw



    # ---------------------------------------------------------------------
    # Déjà Vu — lightweight repeat awareness
    # ---------------------------------------------------------------------

    def _check_dejavu(self, stimulus: str, threshold: float = 0.55) -> int:
        """
        Is this stimulus ~identical to recent ones?
        Returns the count (0 = fresh, 1+ = repeat).
        Uses simple word overlap — not fancy, just honest.
        """
        s_words = set(re.sub(r"[^a-zA-Z0-9\s]", "", stimulus.lower()).split())
        if not s_words:
            return 0

        # Check against current cluster
        if self._dejavu_cluster:
            c_words = set(re.sub(r"[^a-zA-Z0-9\s]", "", self._dejavu_cluster.lower()).split())
            if c_words:
                overlap = len(s_words & c_words) / max(len(s_words | c_words), 1)
                if overlap >= threshold:
                    self._dejavu_count += 1
                    return self._dejavu_count

        # Check against last 5 stimuli
        recent = self.conversation.stimuli_history[-5:]
        for prev in reversed(recent):
            p_words = set(re.sub(r"[^a-zA-Z0-9\s]", "", prev.lower()).split())
            if not p_words:
                continue
            overlap = len(s_words & p_words) / max(len(s_words | p_words), 1)
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
            "no", "wrong", "that's not", "incorrect", "try again",
            "not what i", "fix", "error", "bug", "doesn't work",
            "still broken", "same problem", "didn't work",
        ]
        if any(sig in s_lower for sig in correction_signals):
            return "wrong"

        # Context 1: Explain — stimulus is a question and she already answered
        question_signals = ["?", "why", "what", "how", "explain", "what do you mean"]
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
                raw = run_pass_pipeline(reframed, disclosure_level="open", max_pass=2)
                result = raw.get("result", "")
                if result and result.strip():
                    return result
            except Exception:
                pass
            return ""

        elif context == "wrong":
            # Her accuracy problem. New approach entirely.
            reframed = f"[NEW APPROACH: previous attempts were wrong] {stimulus}"
            try:
                raw = run_pass_pipeline(reframed, disclosure_level="open", max_pass=3)
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
                raw = run_pass_pipeline(reframed, disclosure_level="open", max_pass=2)
                result = raw.get("result", "")
                if result and result.strip():
                    return result
            except Exception:
                pass
            return ""

    # ---------------------------------------------------------------------
    # Misc helpers
    # ---------------------------------------------------------------------

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
        print(f"Status:      {result.get('status')}")
        print(f"Triangle:    {result.get('triangle_reason', 'NA')}")
        print(f"Disclosure:  {result.get('disclosure_level', 'NA')}")
        print(f"Quality:     {result.get('quality_score', 0.0):.2f}")
        print(f"Person:      {result.get('person_context', False)}")
        print(f"Banks Hits:  {result.get('banks_hits', 0)}")
        print(f"Tangents:    {len(result.get('tangents', []))}")
        print(f"Speech:      {result.get('speech_processed', False)}")
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
