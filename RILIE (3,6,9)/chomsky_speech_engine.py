"""
chomsky_speech_engine.py — RILIE'S VOCAL CHORDS
================================================
Transforms semantic meaning (deep structure) into grammatically-correct,
contextually-aware speech (surface structure).

Every response RILIE generates flows through this to be *spoken*.

Core transformation:
  Deep Structure (meaning) → Grammar Rules → Surface Structure (words that sound right)

Uses ChompkyAtTheBit to:
  - Extract subject/object/focus (holy trinity)
  - Detect temporal sense (past/present/future)
  - Apply grammatical rules to reshape the meaning

The result is speech that:
  - Has clear subject/object relationships
  - Respects temporal grounding
  - Sounds natural and contextually appropriate
  - Maintains the original semantic intent
"""

import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("chomsky_speech")

# Try to load Chomsky grammar engine
try:
    from ChomskyAtTheBit import (
        parse_question,
        extract_holy_trinity_for_roux,
        infer_time_bucket,
    )
    CHOMSKY_AVAILABLE = True
except Exception as e:
    logger.warning("Chomsky grammar engine not available: %s", e)
    CHOMSKY_AVAILABLE = False


# ============================================================================
# SPEECH TRANSFORMATION — deep to surface structure
# ============================================================================


def transform_response_through_chomsky(
    deep_structure_text: str,
    stimulus: str,
    disclosure_level: str = "full",
) -> str:
    """
    Transform raw semantic meaning into grammatically-appropriate speech.
    
    Dayenu: Transform ONCE. Return. No re-perfecting.
    
    Args:
        deep_structure_text: Raw response text from Kitchen (semantic content)
        stimulus: Original user question (for context)
        disclosure_level: "taste", "open", or "full" (may affect formality)
    
    Returns:
        Surface structure: grammatically-correct, contextually-aware response
        Falls back to original text if transformation unavailable
    """
    
    if not CHOMSKY_AVAILABLE:
        logger.debug("Chomsky unavailable; returning raw text")
        return deep_structure_text
    
    if not deep_structure_text or not deep_structure_text.strip():
        return deep_structure_text
    
    try:
        # Step 1: Understand what the stimulus is asking for
        stimulus_holy_trinity = extract_holy_trinity_for_roux(stimulus)
        stimulus_time_bucket = infer_time_bucket(stimulus)
        
        # Step 2: Understand what we're saying in response
        response_holy_trinity = extract_holy_trinity_for_roux(deep_structure_text)
        response_time_bucket = infer_time_bucket(deep_structure_text)
        
        # Step 3: Apply transformational rules
        # This is where grammar rules reshape the raw meaning
        transformed = apply_transformational_rules(
            deep_structure_text,
            stimulus_trinity=stimulus_holy_trinity,
            stimulus_time=stimulus_time_bucket,
            response_trinity=response_holy_trinity,
            response_time=response_time_bucket,
            disclosure_level=disclosure_level,
        )
        
        logger.debug(
            "Chomsky transform: stimulus_time=%s response_time=%s",
            stimulus_time_bucket,
            response_time_bucket,
        )
        
        return transformed
        
    except Exception as e:
        logger.warning("Chomsky transformation failed: %s", e)
        # Graceful fallback — return original text
        return deep_structure_text


# ============================================================================
# TRANSFORMATIONAL RULES
# ============================================================================


def apply_transformational_rules(
    text: str,
    stimulus_trinity: list,
    stimulus_time: str,
    response_trinity: list,
    response_time: str,
    disclosure_level: str,
) -> str:
    """
    Apply Chomskyan transformational grammar rules to reshape the response.
    
    Dayenu: Apply rules ONCE. Return immediately. One transformation.
    
    These rules are the grammar engine — they take raw meaning and shape it
    into speech that:
      - Respects subject/object/focus structure
      - Grounds temporally (past/present/future)
      - Matches the discourse context
    """
    
    result = text
    
    # -----------------------------------------------------------------------
    # RULE 1: Temporal grounding
    # -----------------------------------------------------------------------
    # If stimulus asks about future but response is in past tense,
    # add temporal clarity
    if stimulus_time == "future" and response_time == "past":
        result = add_temporal_bridge(result, "future_to_past")
    elif stimulus_time == "past" and response_time == "present":
        result = add_temporal_bridge(result, "past_to_present")
    
    # -----------------------------------------------------------------------
    # RULE 2: Subject/object clarity
    # -----------------------------------------------------------------------
    # Ensure the response establishes clear subjects and objects
    # This prevents ambiguity in who/what is doing what
    result = ensure_subject_clarity(result, response_trinity)
    
    # -----------------------------------------------------------------------
    # RULE 3: Disclosure-aware formality
    # -----------------------------------------------------------------------
    # TASTE level: more conversational, less formal
    # FULL level: direct, complete, no hedging
    if disclosure_level == "taste":
        result = adjust_formality_for_taste(result)
    elif disclosure_level == "full":
        result = adjust_formality_for_full(result)
    
    # -----------------------------------------------------------------------
    # RULE 4: Coherence checking
    # -----------------------------------------------------------------------
    # Ensure the response maintains internal grammatical consistency
    result = check_and_fix_coherence(result)
    
    # Dayenu: One transformation complete. Exit.
    return result


# ============================================================================
# TRANSFORMATION HELPERS
# ============================================================================


def add_temporal_bridge(text: str, bridge_type: str) -> str:
    """
    Add temporal clarity when tense shifts between stimulus and response.
    
    Bridges:
      - future_to_past: "Here's what happened when..."
      - past_to_present: "That shaped what we see now..."
      - present_to_future: "Which means going forward..."
    """
    bridges = {
        "future_to_past": "To understand, look at what happened: ",
        "past_to_present": "That history shaped what we see now: ",
        "present_to_future": "Which means going forward: ",
    }
    
    bridge = bridges.get(bridge_type, "")
    if bridge and not text.startswith(bridge):
        return bridge + text
    
    return text


def ensure_subject_clarity(text: str, trinity: list) -> str:
    """
    Ensure response has clear subjects and objects.
    Uses the holy trinity (subject/object/focus) to reshape.
    
    If the response mentions concepts from the trinity, make sure
    the relationships are explicit.
    """
    # This is where deep Chomskyan parsing would reshape the sentence structure
    # For now, basic check: if response is too vague, add grounding
    
    if not trinity or len(text) < 20:
        return text
    
    # If response lacks pronouns/subjects, it might be too compressed
    # Check for clarity
    sentences = text.split(".")
    for i, sent in enumerate(sentences):
        sent = sent.strip()
        if sent and len(sent) > 15:
            # Check if sentence has a clear subject
            if not has_clear_subject(sent):
                # Try to add subject clarity using the trinity
                sentences[i] = add_subject_to_sentence(sent, trinity)
    
    return ".".join(sentences)


def has_clear_subject(sentence: str) -> bool:
    """Check if a sentence has a clear grammatical subject."""
    # Simple heuristic: does it have a pronoun or noun at the start?
    subject_indicators = [
        "i ", "you ", "he ", "she ", "it ", "we ", "they ",
        "this ", "that ", "these ", "those ",
        "the ", "a ", "an ",
    ]
    s = sentence.lower().strip()
    return any(s.startswith(ind) for ind in subject_indicators)


def add_subject_to_sentence(sentence: str, trinity: list) -> str:
    """
    If a sentence lacks clear subject, try to add one from the trinity.
    """
    if not trinity:
        return sentence
    
    # Use the first trinity element as the subject
    subject = trinity[0] if trinity else "This"
    
    # Check if sentence already starts with a subject
    if has_clear_subject(sentence):
        return sentence
    
    # Add subject: "Subject [original sentence]"
    return f"{subject} {sentence[0].lower()}{sentence[1:]}"


def adjust_formality_for_taste(text: str) -> str:
    """
    TASTE level disclosure: more conversational, inviting, less formal.
    """
    # Replace formal words with conversational ones
    replacements = {
        "however": "but",
        "furthermore": "plus",
        "therefore": "so",
        "consequently": "which means",
        "in addition": "also",
        "prior to": "before",
        "subsequently": "then",
    }
    
    result = text
    for formal, casual in replacements.items():
        result = result.replace(formal, casual)
        result = result.replace(formal.capitalize(), casual.capitalize())
    
    return result


def adjust_formality_for_full(text: str) -> str:
    """
    FULL level disclosure: direct, complete, no hedging or softening.
    Remove qualifiers like "might", "perhaps", "seems".
    """
    hedges = [
        "might ",
        "perhaps ",
        "seems ",
        "appears ",
        "could be ",
        "may be ",
        "possibly ",
        "arguably ",
        "in some ways ",
    ]
    
    result = text
    for hedge in hedges:
        result = result.replace(hedge, "")
        result = result.replace(hedge.capitalize(), "")
    
    return result


def check_and_fix_coherence(text: str) -> str:
    """
    Basic coherence checking: ensure sentences flow logically.
    Catch obvious grammatical issues and fix them.
    """
    # Fix common issues
    
    # Double spaces
    while "  " in text:
        text = text.replace("  ", " ")
    
    # Missing spaces after periods
    text = text.replace(".", " ").replace("  ", " ")
    text = text.replace(".", ". ")
    
    # Ensure proper capitalization after periods
    sentences = text.split(". ")
    fixed = []
    for sent in sentences:
        sent = sent.strip()
        if sent and not sent[0].isupper():
            sent = sent[0].upper() + sent[1:]
        fixed.append(sent)
    
    return ". ".join(fixed)


# ============================================================================
# PUBLIC API — called from rilie_core.py after Kitchen generates response
# ============================================================================


def speak(
    deep_structure: str,
    stimulus: str,
    disclosure_level: str = "full",
) -> str:
    """
    Main entry point: transform meaning into speech.
    
    Called after Kitchen generates `best.text` (semantic content).
    Returns grammatically-correct, contextually-aware response.
    
    Args:
        deep_structure: Raw response from Kitchen (the meaning)
        stimulus: User's original question (context)
        disclosure_level: "taste", "open", or "full"
    
    Returns:
        Surface structure: what RILIE actually says
    """
    return transform_response_through_chomsky(
        deep_structure,
        stimulus,
        disclosure_level,
    )
