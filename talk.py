"""

talk.py — THE WAITRESS

======================

The bouncer at return. The only mouth RILIE has.

RILIE cooks. TALK decides if it's good enough to serve.
Nothing reaches the customer without passing through TALK.

Architecture:
- The Kitchen (rilie_core) builds candidates
- The Guvna (guvna) orchestrates the pipeline
- TALK checks the plate before it leaves the building

Gates (in order):
1. EMPTY CHECK — is there even food on the plate?
2. ANTI-DÉJÀ-VU — did we already serve this dish? (signal, not rejection)
3. RELEVANCE — did she answer what was asked?
4. RESONANCE — does the depth match the question?
5. ORIGINALITY — is this cooked fresh or reheated?

If a plate fails, it goes back to the kitchen.
If all plates fail, TALK says so honestly.
The customer never sees the mess.

One file. One function. One return.

"""

import re
import logging
import time
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


# ============================================================================
# DIRECTNESS DETECTION — Does the ape want a straight answer?
# ============================================================================

# Nine question-word openers. Hard cap.
_Q_WORDS = [
    "what", "who", "when", "where", "which",
    "how many", "how much", "how old", "how long",
    "how far", "is ", "are ", "was ", "were ",
    "did ", "does ", "do ", "can ", "will ",
]

# Nine imperative triggers. Hard cap.
_IMPERATIVES = [
    "name", "list", "explain", "describe",
    "tell me", "give me", "show me", "define", "compare",
]


def _is_direct(stimulus: str) -> bool:
    """
    Detect direct questions and imperative commands.
    Direct = tighter leash on resonance, stricter relevance.
    """
    s = stimulus.lower().strip()
    # Question word opener
    if any(s.startswith(q) for q in _Q_WORDS):
        return True
    # Ends with question mark
    if s.endswith("?"):
        return True
    # Imperative opener
    if any(s.startswith(imp) for imp in _IMPERATIVES):
        return True
    return False


# ============================================================================
# SOCIAL SIGNALS — The full ape vocabulary gets a pass
# ============================================================================

_SOCIAL_SIGNALS = [
    # Greetings
    "hi", "hey", "hello", "sup", "what's up", "whats up", "howdy", "yo",
    "good morning", "good afternoon", "good evening", "hola", "shalom",
    "bonjour",
    # Goodbyes
    "bye", "goodbye", "see you", "later", "peace",
    # Gratitude
    "thanks", "thank you",
    # Confirmations / affirmations
    "ok", "okay", "cool", "nice", "wow", "haha", "lol",
    "yes", "yeah", "yep", "yup", "ya", "sure", "absolutely",
    "right", "correct", "exactly", "agreed", "true", "totally",
    "of course", "definitely", "certainly", "affirmative",
    # Dismissals / negations
    "no", "nah", "nope", "naw", "never mind", "forget it",
    # Continuations
    "go ahead", "go on", "continue", "keep going", "proceed",
    # Introductions
    "my name is", "i'm ", "call me",
]


# ============================================================================
# FILLER FRAGMENTS — Nine reheated legos. Most common down.
# ============================================================================

_FILLER_FRAGMENTS = [
    "important to note",
    "great question",
    "many perspectives",
    "it's worth mentioning",
    "as we know",
    "in conclusion",
    "at the end of the day",
    "it goes without saying",
    "when it comes to",
]


# ============================================================================
# HEAVY DOMAINS — Libraries that justify longer responses
# ============================================================================

_HEAVY_DOMAINS = {
    "physics", "mathematics", "genomics", "linguistics_cognition",
    "nanotechnology", "life", "chemistry", "biochem_universe",
}


# ============================================================================
# RESPONSE HISTORY — TALK remembers what she served
# ============================================================================

class TalkMemory:
    """
    What TALK has served this session.
    She never serves the same dish twice.

    Stores rich metadata per serve: text, disclosure level, domains, tone.
    In-memory list now, DB-ready interface for Tier 2 (banks_sessions).
    """

    def __init__(self):
        self._served: List[Dict[str, Any]] = []

    def record(self, text: str, plate: Optional[Dict[str, Any]] = None) -> None:
        """Record a served plate with metadata."""
        entry = {
            "text": text.strip() if text else "",
            "served_at": time.time(),
            "disclosure_level": (plate or {}).get("disclosure_level", ""),
            "domains_used": (plate or {}).get("domains_used", []),
            "tone": (plate or {}).get("tone", ""),
            "status": (plate or {}).get("status", ""),
        }
        self._served.append(entry)

    def recent(self, n: int = 5) -> List[Dict[str, Any]]:
        """Last N served plates with metadata."""
        return self._served[-n:]

    def recent_texts(self, n: int = 5) -> List[str]:
        """Last N served texts (for backwards compat and comparison)."""
        return [e["text"] for e in self._served[-n:] if e["text"]]

    @property
    def served_count(self) -> int:
        return len(self._served)


# ============================================================================
# WORD EXTRACTION — shared utility
# ============================================================================

def _words(text: str) -> set:
    """Extract word set for comparison."""
    return set(re.sub(r"[^a-zA-Z0-9\s]", "", text.lower()).split())


# Noise words that don't indicate relevance
_NOISE = {
    "the", "a", "an", "is", "are", "was", "were", "i", "you", "it",
    "to", "in", "on", "of", "and", "or", "but", "that", "this",
    "what", "how", "why", "who", "when", "where", "do", "does",
    "can", "my", "your", "me", "we", "they", "he", "she", "its",
    "not", "no", "yes", "so", "if", "for", "with", "at", "from",
    "be", "have", "has", "had", "will", "would", "could", "should",
}


# ============================================================================
# GATE FUNCTIONS — each returns (pass: bool, reason: str)
# ============================================================================

def gate_empty(plate: Dict[str, Any]) -> tuple:
    """Gate 1: Is there food on the plate?"""
    text = plate.get("result", "").strip()
    if not text:
        return False, "EMPTY_PLATE"
    word_count = len(text.split())
    if word_count < 3:
        return False, f"UNDERWEIGHT_{word_count}"
    return True, "OK"


def gate_dejavu(plate: Dict[str, Any], memory: TalkMemory) -> tuple:
    """
    Gate 2: Déjà-vu is SIGNAL, not rejection.
    Guvna tracks it in metadata. TALK passes it through.
    The signal tells us about rhythm and theme—whether she's riffing or stuck.
    Downstream can decide what to do with it.
    """
    dejavu_info = plate.get("dejavu", {})
    if dejavu_info.get("frequency", 0) > 0:
        similarity = dejavu_info.get("similarity", "none")
        logger.debug("TALK: Déjà-vu signal detected (freq=%d, similarity=%s) - PASS",
                     dejavu_info["frequency"],
                     similarity)
    return True, "OK"


def gate_relevance(plate: Dict[str, Any], stimulus: str) -> tuple:
    """
    Gate 3: Did she answer what was asked?
    Checks if the response has any connection to the stimulus.

    Social signals get a pass — they're social, not topical.
    TASTE turns get a pass — disclosure-level override.
    Direct questions get STRICTER checking.
    No word-count bypass. Social list handles greetings.
    """
    text = plate.get("result", "").strip()
    if not text:
        return True, "OK"

    # TASTE turns bypass relevance
    disclosure = plate.get("disclosure_level")
    if disclosure == "taste":
        return True, "OK"

    # Social signals get a pass
    s = stimulus.lower().strip()
    if any(s.startswith(g) or s == g for g in _SOCIAL_SIGNALS):
        return True, "OK"

    stim_words = _words(stimulus)
    resp_words = _words(text)

    if not stim_words or not resp_words:
        return True, "OK"

    # Check meaningful overlap
    overlap = stim_words & resp_words
    meaningful_overlap = overlap - _NOISE

    # Domain coverage counts as relevance
    domains_used = plate.get("domains_used", [])

    if meaningful_overlap or domains_used:
        return True, "OK"

    # Direct question with zero meaningful overlap = hard reject
    if _is_direct(stimulus):
        return False, "IRRELEVANT_DIRECT"

    return False, "IRRELEVANT"


def gate_resonance(plate: Dict[str, Any], stimulus: str) -> tuple:
    """
    Gate 4: Flow = Skill × Challenge.
    Does the depth match the question?
    Simple question + dissertation = fail.
    Complex question + one word = fail.
    Direct questions get a tighter leash.
    Heavy domains get more room.
    """
    text = plate.get("result", "").strip()
    if not text:
        return True, "OK"

    stim_len = len(stimulus.split())
    resp_len = len(text.split())
    direct = _is_direct(stimulus)
    domains_used = plate.get("domains_used", [])

    # Domain complexity bump: heavy domains get more ceiling
    heavy = any(d in _HEAVY_DOMAINS for d in domains_used) or len(domains_used) >= 3
    direct_ceiling = 100 if heavy else 60
    open_ceiling = 150 if heavy else 120

    # Direct question: tighter leash
    if direct and stim_len < 10 and resp_len > direct_ceiling:
        return False, "OVERCOOKED_DIRECT"

    # Open prompt: still has a ceiling
    if not direct and stim_len < 8 and resp_len > open_ceiling:
        return False, "OVERCOOKED"

    # Complex question shouldn't get a stub
    if stim_len > 20 and resp_len < 5:
        return False, "UNDERCOOKED"

    return True, "OK"


def gate_originality(plate: Dict[str, Any], memory: TalkMemory) -> tuple:
    """
    Gate 5: Is this cooked fresh or reheated?
    Comprehension first, originality second.
    Never reject a clear plate for being plain.

    Checks two things:
    1. Filler fragments — dead-weight connector phrases (9 legos)
    2. Baseline echo — response is just parroting Google text

    Originality is a soft reject: sends back once, then serves anyway.
    The customer doesn't starve chasing poetry.
    """
    text = plate.get("result", "").strip()
    if not text:
        return True, "OK"

    text_lower = text.lower()
    resp_words = text.split()
    resp_len = len(resp_words)

    # --- FILLER CHECK ---
    filler_count = sum(1 for f in _FILLER_FRAGMENTS if f in text_lower)

    # More than 2 filler fragments in a response = reheated
    if filler_count > 2:
        return False, "REHEATED_FILLER"

    # --- BASELINE ECHO CHECK ---
    baseline = plate.get("baseline", {})
    baseline_text = ""
    if isinstance(baseline, dict):
        baseline_text = baseline.get("text", "")
    elif isinstance(baseline, str):
        baseline_text = baseline

    if baseline_text and len(baseline_text.strip()) > 20:
        baseline_words = _words(baseline_text)
        response_words = _words(text)
        if baseline_words and response_words:
            overlap = baseline_words & response_words
            meaningful_overlap = overlap - _NOISE
            # If more than 70% of the response words come from baseline = echo
            if len(response_words) > 0:
                echo_ratio = len(meaningful_overlap) / max(len(response_words - _NOISE), 1)
                if echo_ratio > 0.7:
                    return False, "BASELINE_ECHO"

    return True, "OK"


# ============================================================================
# TALK — The only return. The only mouth.
# ============================================================================

def talk(
    plate: Dict[str, Any],
    stimulus: str,
    memory: TalkMemory,
    max_retries: int = 2,
    retry_fn=None,
    search_fn=None,
    wilden_swift_fn=None,
) -> Dict[str, Any]:
    """
    THE WAITRESS.

    Takes the plate from the kitchen. Checks every gate.
    If it passes — serve it. Record it. Return it.
    If it fails — send it back. Try again.
    If all retries fail — be honest about it.

    This is the ONLY function that returns to the customer.

    Order:
    1. Gates (empty, dejavu, relevance, resonance, originality)
    2. wilden_swift scores on 18 rhetorical modes
    3. Self-search googles her sentence
    4. Decide: serve or send back

    Parameters:
        plate: The response dict from the kitchen
        stimulus: What the customer ordered
        memory: TalkMemory — what we've served before
        max_retries: How many times to send it back before giving up
        retry_fn: Optional callable(stimulus) -> plate for retrying
        search_fn: Optional callable(query) -> str for self-search verification
        wilden_swift_fn: Optional callable(text) -> text for rhetorical scoring
    """

    # APERTURE FAST PATH: greeting and goodbye bypass all gates
    status = str(plate.get("status", "")).upper()
    if status in ("APERTURE", "GOODBYE"):
        logger.info("TALK: %s - serve directly (no gates)", status)
        result_text = plate.get("result", "")
        if result_text and result_text.strip():
            memory.record(result_text, plate)
        plate["talk_status"] = "SERVED"
        plate["talk_attempts"] = 1
        plate["talk_rejections"] = []
        return plate

    attempts = 0
    current_plate = plate
    rejection_log: List[Dict[str, str]] = []
    originality_retried = False

    while attempts <= max_retries:

        # Run all 5 gates in order
        gates = [
            ("EMPTY", gate_empty(current_plate)),
            ("DEJAVU", gate_dejavu(current_plate, memory)),
            ("RELEVANCE", gate_relevance(current_plate, stimulus)),
            ("RESONANCE", gate_resonance(current_plate, stimulus)),
            ("ORIGINALITY", gate_originality(current_plate, memory)),
        ]

        failed = None
        for gate_name, (passed, reason) in gates:
            if not passed:
                failed = (gate_name, reason)
                break

        if failed is None:
            # All gates passed.
            result_text = current_plate.get("result", "")
            status = str(current_plate.get("status", "")).upper()
            is_primer = status in ("GREETING", "PRIMER", "GOODBYE")

            # STEP 1: WILDEN_SWIFT — score on 18 rhetorical modes
            # She writes it, then it's graded. She never sees the formula.
            if wilden_swift_fn and result_text and not is_primer:
                try:
                    wilden_swift_fn(result_text)
                    if hasattr(wilden_swift_fn, '_last_scores'):
                        current_plate["wilden_swift"] = wilden_swift_fn._last_scores
                    elif hasattr(wilden_swift_fn, '__wrapped__') and hasattr(wilden_swift_fn.__wrapped__, '_last_scores'):
                        current_plate["wilden_swift"] = wilden_swift_fn.__wrapped__._last_scores
                    logger.info("TALK: wilden_swift scored response")
                except Exception as e:
                    logger.debug("TALK: wilden_swift failed (non-fatal): %s", e)

            # STEP 2: SELF-SEARCH — google her sentence before speaking
            if search_fn and result_text and not is_primer:
                try:
                    enrichment = search_fn(result_text)
                    if enrichment and len(enrichment.strip()) > 20:
                        current_plate["self_search"] = enrichment.strip()
                        logger.info("TALK: Self-search enriched response")
                except Exception as e:
                    logger.debug("TALK: Self-search failed (non-fatal): %s", e)

            # STEP 3: SERVE
            memory.record(result_text, current_plate)

            # Attach the receipt
            current_plate["talk_status"] = "SERVED"
            current_plate["talk_attempts"] = attempts + 1
            current_plate["talk_rejections"] = rejection_log
            current_plate["talk_direct"] = _is_direct(stimulus)

            logger.info("TALK: SERVED after %d attempt(s)", attempts + 1)
            return current_plate

        # Failed a gate
        gate_name, reason = failed
        rejection_log.append({
            "attempt": attempts + 1,
            "gate": gate_name,
            "reason": reason,
            "rejected_text": current_plate.get("result", "")[:80],
        })

        logger.warning("TALK: Gate %s rejected plate — %s (attempt %d)",
                       gate_name, reason, attempts + 1)

        # ORIGINALITY soft reject: only one retry on originality grounds
        # Comprehension > originality — don't starve the customer chasing poetry
        if gate_name == "ORIGINALITY" and not originality_retried:
            originality_retried = True
        elif gate_name == "ORIGINALITY" and originality_retried:
            # Already retried once for originality. Serve it anyway.
            result_text = current_plate.get("result", "")
            memory.record(result_text, current_plate)
            current_plate["talk_status"] = "SERVED_DESPITE_ORIGINALITY"
            current_plate["talk_attempts"] = attempts + 1
            current_plate["talk_rejections"] = rejection_log
            current_plate["talk_direct"] = _is_direct(stimulus)
            logger.info("TALK: SERVED (originality override) after %d attempt(s)", attempts + 1)
            return current_plate

        attempts += 1

        # Try to get a new plate from the kitchen
        if retry_fn and attempts <= max_retries:
            try:
                current_plate = retry_fn(stimulus)
            except Exception as e:
                logger.error("TALK: retry_fn failed: %s", e)
                break
        else:
            break

    # All retries exhausted. Be honest.
    memory.record("", None)
    honest_response = {
        "result": "",
        "status": "TALK_EXHAUSTED",
        "talk_status": "EXHAUSTED",
        "talk_attempts": attempts,
        "talk_rejections": rejection_log,
        "talk_direct": _is_direct(stimulus),
    }

    logger.warning("TALK: All %d attempts failed. Gates: %s",
                   attempts, [r["gate"] for r in rejection_log])

    return honest_response
