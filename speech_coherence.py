"""
speech_coherence.py — FINAL VERSION
====================================
Fixed: whitespace-only handling, None stimulus
"""

import logging
import re
from typing import Optional

logger = logging.getLogger("speech_coherence")


def ensure_coherence(text: str, stimulus: Optional[str] = None) -> str:
    """Ensure speech is understandable."""
    
    if not text:
        return ""
    
    text = text.strip()
    
    # Handle whitespace-only
    if not text or all(c.isspace() for c in text):
        return ""
    
    if len(text.strip()) < 3:
        return text
    
    # Ensure has subject
    text = ensure_has_subject(text)
    
    # Fix temporal sense
    if stimulus:
        text = align_temporal_sense(text, stimulus)
    
    # Fix dangling refs
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
    
    # Check for implied "you" in imperative
    imperatives = [
        "go ", "come ", "bring ", "take ", "make ", "get ",
        "tell ", "ask ", "try ", "keep ",
    ]
    if any(s_lower.startswith(imp) for imp in imperatives):
        return True
    
    return False


def ensure_has_subject(text: str) -> str:
    """Ensure text has clear subject."""
    
    if not text:
        return text
    
    sentences = text.split(".")
    has_any = False
    
    for sent in sentences:
        if has_clear_subject(sent):
            has_any = True
            break
    
    if has_any:
        return text
    
    # Add subject conversationally
    if text.startswith(("Here", "The", "This", "That", "About")):
        return text
    
    return f"Here's the thing: {text}"


def align_temporal_sense(response: str, stimulus: Optional[str]) -> str:
    """Align temporal sense."""
    
    if not response or not stimulus:
        return response
    
    try:
        from ChomskyAtTheBit import infer_time_bucket
        
        stimulus_time = infer_time_bucket(stimulus)
        response_time = infer_time_bucket(response)
        
        if stimulus_time != response_time and stimulus_time != "unknown":
            if stimulus_time == "past" and response_time == "present":
                if not has_temporal_marker(response, "past"):
                    response = f"Historically, {response[0].lower()}{response[1:]}"
        
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
    """Fix dangling references."""
    
    if not text or len(text) < 10:
        return text
    
    # Only fix if completely ambiguous
    if has_critical_ambiguity(text):
        text = f"Here's what I mean: {text}"
    
    return text


def has_critical_ambiguity(text: str) -> bool:
    """Check for pronouns with NO possible antecedent."""
    
    if text.startswith(("They ", "It ", "He ", "She ", "Him ", "Her ")):
        if len(text.split(".")[0]) < 20:
            return True
    
    return False


def clean_formatting(text: str) -> str:
    """Light formatting cleanup."""
    
    if not text:
        return text
    
    while "  " in text:
        text = text.replace("  ", " ")
    
    text = re.sub(r'\s+([.!?])', r'\1', text)
    
    return text


def validate(text: str, stimulus: Optional[str] = None) -> str:
    """Validate speech for coherence."""
    
    if not text or not isinstance(text, str):
        return ""
    
    # Ensure basic coherence
    text = ensure_coherence(text, stimulus)
    
    if not text:
        return ""
    
    # Light formatting
    text = clean_formatting(text)
    
    # Capitalize and punctuate
    text = text.strip()
    if text:
        text = text[0].upper() + text[1:]
        if text and text[-1] not in ".!?":
            text += "."
    
    return text
