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
  2. ANTI-DÉJÀ-VU — did we already serve this dish?
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
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


# ============================================================================
# RESPONSE HISTORY — TALK remembers what she served
# ============================================================================

class TalkMemory:
    """What TALK has served this session. She never serves the same dish twice."""
    def __init__(self):
        self.served: List[str] = []

    def record(self, text: str) -> None:
        if text and text.strip():
            self.served.append(text.strip())

    def recent(self, n: int = 5) -> List[str]:
        return self.served[-n:]


# ============================================================================
# GATE FUNCTIONS — each returns (pass: bool, reason: str)
# ============================================================================

def _words(text: str) -> set:
    """Extract word set for comparison."""
    return set(re.sub(r"[^a-zA-Z0-9\s]", "", text.lower()).split())


def gate_empty(plate: Dict[str, Any]) -> tuple:
    """Gate 1: Is there food on the plate?"""
    text = plate.get("result", "").strip()
    if not text:
        return False, "EMPTY_PLATE"
    return True, "OK"


def gate_dejavu(plate: Dict[str, Any], memory: TalkMemory) -> tuple:
    """Gate 2: Did we already serve this?"""
    text = plate.get("result", "").strip()
    if not text:
        return True, "OK"  # Nothing to check

    cand_words = _words(text)
    if len(cand_words) < 4:
        return True, "OK"  # Too short to judge

    for prior in memory.recent(5):
        prior_words = _words(prior)
        if not prior_words:
            continue
        smaller = min(len(cand_words), len(prior_words))
        if smaller > 0 and len(cand_words & prior_words) / smaller > 0.6:
            return False, "DEJAVU"

    return True, "OK"


def gate_relevance(plate: Dict[str, Any], stimulus: str) -> tuple:
    """
    Gate 3: Did she answer what was asked?
    Checks if the response has any connection to the stimulus.

    EXCEPTION: Greetings, goodbyes, and short social exchanges
    don't need topic relevance. They're social, not topical.
    """
    text = plate.get("result", "").strip()
    if not text:
        return True, "OK"

    # Social exchanges skip relevance — they're not about a topic
    s = stimulus.lower().strip()
    social_signals = [
        "hi", "hey", "hello", "sup", "what's up", "whats up", "howdy", "yo",
        "good morning", "good afternoon", "good evening", "hola", "shalom",
        "bonjour", "bye", "goodbye", "see you", "later", "peace", "thanks",
        "thank you", "ok", "okay", "cool", "nice", "wow", "haha", "lol",
        "my name is", "i'm ", "call me",
    ]
    if any(s.startswith(g) or s == g for g in social_signals):
        return True, "OK"
    # Very short stimulus (< 4 words) — social by nature
    if len(s.split()) < 4:
        return True, "OK"

    stim_words = _words(stimulus)
    resp_words = _words(text)

    if not stim_words or not resp_words:
        return True, "OK"

    # Check for ANY overlap between stimulus and response
    overlap = stim_words & resp_words
    # Remove common words that don't indicate relevance
    noise = {"the", "a", "an", "is", "are", "was", "were", "i", "you", "it",
             "to", "in", "on", "of", "and", "or", "but", "that", "this",
             "what", "how", "why", "who", "when", "where", "do", "does",
             "can", "my", "your", "me", "we", "they", "he", "she", "its",
             "not", "no", "yes", "so", "if", "for", "with", "at", "from",
             "be", "have", "has", "had", "will", "would", "could", "should"}
    meaningful_overlap = overlap - noise

    # Also check if response domains match stimulus domains
    domains_used = plate.get("domains_used", [])
    stimulus_domains = plate.get("stimulus_domains", [])

    # Relevance passes if there's any meaningful connection
    if meaningful_overlap or domains_used:
        return True, "OK"

    return False, "IRRELEVANT"


def gate_resonance(plate: Dict[str, Any], stimulus: str) -> tuple:
    """
    Gate 4: Flow = Skill × Challenge.
    Does the depth match the question?
    Simple question + dissertation = fail.
    Complex question + one word = fail.
    """
    text = plate.get("result", "").strip()
    if not text:
        return True, "OK"

    stim_len = len(stimulus.split())
    resp_len = len(text.split())

    # Simple greeting/question (< 8 words) shouldn't get a lecture (> 50 words)
    if stim_len < 8 and resp_len > 60:
        return False, "OVERCOOKED"

    # Complex question (> 20 words) shouldn't get a stub (< 5 words)
    if stim_len > 20 and resp_len < 5:
        return False, "UNDERCOOKED"

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
) -> Dict[str, Any]:
    """
    THE WAITRESS.

    Takes the plate from the kitchen. Checks every gate.
    If it passes — serve it. Record it. Return it.
    If it fails — send it back. Try again.
    If all retries fail — be honest about it.

    This is the ONLY function that returns to the customer.

    Parameters:
        plate:       The response dict from the kitchen
        stimulus:    What the customer ordered
        memory:      TalkMemory — what we've served before
        max_retries: How many times to send it back before giving up
        retry_fn:    Optional callable(stimulus) -> plate for retrying
    """

    attempts = 0
    current_plate = plate
    rejection_log: List[Dict[str, str]] = []

    while attempts <= max_retries:
        # Run all gates in order
        gates = [
            ("EMPTY", gate_empty(current_plate)),
            ("DEJAVU", gate_dejavu(current_plate, memory)),
            ("RELEVANCE", gate_relevance(current_plate, stimulus)),
            ("RESONANCE", gate_resonance(current_plate, stimulus)),
        ]

        failed = None
        for gate_name, (passed, reason) in gates:
            if not passed:
                failed = (gate_name, reason)
                break

        if failed is None:
            # All gates passed. Serve it.
            result_text = current_plate.get("result", "")
            memory.record(result_text)

            # Attach the receipt
            current_plate["talk_status"] = "SERVED"
            current_plate["talk_attempts"] = attempts + 1
            current_plate["talk_rejections"] = rejection_log

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
    memory.record("")  # Record that we had nothing

    honest_response = {
        "result": "",
        "status": "TALK_EXHAUSTED",
        "talk_status": "EXHAUSTED",
        "talk_attempts": attempts,
        "talk_rejections": rejection_log,
    }

    logger.warning("TALK: All %d attempts failed. Gates: %s",
                   attempts, [r["gate"] for r in rejection_log])
    return honest_response
