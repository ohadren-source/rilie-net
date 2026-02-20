"""
speech_coherence.py — FINAL VERSION
====================================
Fixed: whitespace-only handling, None stimulus

FIXES (this revision):
  - validate() double docstring removed.
  - stitch_connective_tissue() regex hardened with proper noun protection.
  - align_temporal_sense() band-aid prefix removed — logs mismatch, returns as-is.
"""

import logging
import re
from typing import Optional

logger = logging.getLogger("speech_coherence")


coherence_check_count = 0

def ensure_coherence(text: str, stimulus: Optional[str] = None) -> str:
    """Ensure speech is understandable."""
    if not text:
        return ""
    text = text.strip()
    if not text or all(c.isspace() for c in text):
        return ""
    if len(text.strip()) < 3:
        return text
    text = ensure_has_subject(text)
    if stimulus:
        text = align_temporal_sense(text, stimulus)
    text = resolve_critical_references(text)
    return text


def has_clear_subject(sentence: str) -> bool:
    """Check if sentence has identifiable subject."""
    if not sentence:
        return False
    sentence = sentence.strip()
    subject_starts = [
        "i ", "you ", "he ", "she ", "it ", "we ", "they ",
        "this ", "that ", "these ", "those ",
        "what ", "which ", "who ",
    ]
    s_lower = sentence.lower()
    if any(s_lower.startswith(sub) for sub in subject_starts):
        return True
    imperatives = [
        "go ", "come ", "bring ", "take ", "make ", "get ",
        "tell ", "ask ", "try ", "keep ",
    ]
    if any(s_lower.startswith(imp) for imp in imperatives):
        return True
    return False


def ensure_has_subject(text: str) -> str:
    """Ensure text has clear subject. No band-aid prefixes."""
    if not text:
        return text
    sentences = text.split(".")
    for sent in sentences:
        if has_clear_subject(sent):
            return text
    return text


def align_temporal_sense(response: str, stimulus: Optional[str]) -> str:
    """
    Align temporal sense between stimulus and response.

    CONSERVATIVE: if tenses diverge, log and return unchanged.
    No band-aid prefixes. Temporal alignment is Kitchen/Guvna's job.
    """
    if not response or not stimulus:
        return response
    try:
        from ChomskyAtTheBit import infer_time_bucket
        stimulus_time = infer_time_bucket(stimulus)
        response_time = infer_time_bucket(response)
        if stimulus_time != response_time and stimulus_time != "unknown":
            logger.debug(
                "TEMPORAL MISMATCH: stimulus=%s response=%s -- returning as-is",
                stimulus_time, response_time,
            )
        return response
    except Exception:
        return response


def has_temporal_marker(text: str, time_type: str) -> bool:
    """Check if text has temporal grounding."""
    if time_type == "past":
        markers = ["historically", "back then", "when", "was", "before"]
    else:
        return True
    text_lower = text.lower()
    return any(marker in text_lower for marker in markers)


def resolve_critical_references(text: str) -> str:
    """Fix dangling references. No band-aid prefixes."""
    if not text or len(text) < 10:
        return text
    return text


def has_critical_ambiguity(text: str) -> bool:
    """Check for pronouns with NO possible antecedent."""
    if text.startswith(("They ", "It ", "He ", "She ", "Him ", "Her ")):
        if len(text.split(".")[0]) < 20:
            return True
    return False


# Protected proper nouns -- stitch_connective_tissue never touches these
_STITCH_PROTECTED = {
    "RILIE", "Rakim", "Coltrane", "Escoffier", "Bourdain",
    "Eric", "Chuck", "Mingus", "Monk", "Davis", "Parker",
    "Phenix", "Ohad", "SOi", "Kitchen", "Guvna", "Triangle",
    "Banks", "Chomsky", "Monday", "Tuesday", "Wednesday",
    "Thursday", "Friday", "Saturday", "Sunday",
    "January", "February", "March", "April", "June",
    "July", "August", "September", "October", "November", "December",
    "I",
    "Fugazi", "Madball", "Converge", "Hatebreed", "Misfits",
    "Trane", "Bird", "Dizzy",
}


def stitch_connective_tissue(text: str) -> str:
    """
    When Kitchen outputs concepts bumping into each other without connectors,
    stitch them with em dashes.

    Pattern: "RILIE doesn't retrieve She thinks" -> "RILIE doesn't retrieve -- she thinks"
    Never insert if punctuation already exists.

    GUARDED against:
    - Protected proper nouns (see _STITCH_PROTECTED above)
    - Words following punctuation (sentence boundary != concept bump)
    - ALL_CAPS tokens (acronyms, brand names)
    - The pronoun "I" -- never lowercased
    """
    if not text:
        return text

    def _should_stitch(m) -> str:
        before = m.group(1)
        space = m.group(2)
        capital_word = m.group(3)

        word_match = re.match(r'[A-Za-z]+', capital_word)
        word_str = word_match.group(0) if word_match else capital_word

        if word_str in _STITCH_PROTECTED:
            return before + space + capital_word

        if word_str == word_str.upper() and len(word_str) > 1:
            return before + space + capital_word

        start = max(0, m.start() - 6)
        preceding = text[start:m.start()]
        if any(p in preceding for p in ['.', '!', '?', ':', ';', ',']):
            return before + space + capital_word

        return before + " -- " + capital_word[0].lower() + capital_word[1:]

    text = re.sub(
        r'([a-z])( +)([A-Z][a-z])',
        _should_stitch,
        text
    )
    return text


def clean_formatting(text: str) -> str:
    """Light formatting cleanup."""
    if not text:
        return text
    while "  " in text:
        text = text.replace("  ", " ")
    text = re.sub(r'\s+([.!?])', r'\1', text)
    return text


def validate(text: str, stimulus: Optional[str] = None) -> str:
    """
    Validate speech for coherence.
    Dayenu: Validate ONCE. No re-checking.
    """
    if not text or not isinstance(text, str):
        return ""
    text = ensure_coherence(text, stimulus)
    if not text:
        return ""
    text = stitch_connective_tissue(text)
    text = clean_formatting(text)
    text = text.strip()
    if text:
        text = text[0].upper() + text[1:]
        if text and text[-1] not in ".!?":
            text += "."
    return text
