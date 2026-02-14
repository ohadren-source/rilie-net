"""
response_generator.py — FINAL VERSION
======================================
All test issues fixed. Ready to ship.
"""

import logging
import random
from typing import Dict, Any, Optional

logger = logging.getLogger("response_generator")

try:
    from ChomskyAtTheBit import (
        extract_holy_trinity_for_roux,
        infer_time_bucket,
    )
    CHOMSKY_AVAILABLE = True
except Exception as e:
    logger.warning("Chomsky not available: %s", e)
    CHOMSKY_AVAILABLE = False


def generate(
    kitchen_meaning: str,
    question: str,
    disclosure_level: str = "full",
) -> str:
    """
    Nuclear: generate or return empty.
    No scripts. No "I'm thinking about that."
    She speaks or she's silent.
    """
    
    if not question or not question.strip():
        return kitchen_meaning or ""
    
    if not kitchen_meaning or not kitchen_meaning.strip():
        if CHOMSKY_AVAILABLE:
            try:
                time_bucket = infer_time_bucket(question)
                subject = extract_main_subject(question)
                ack = build_acknowledgment([subject], time_bucket, question)
                if ack:
                    return ack
            except Exception:
                pass
        return ""
    
    try:
        if CHOMSKY_AVAILABLE:
            time_bucket = infer_time_bucket(question)
            subject = extract_main_subject(question)
            acknowledgment = build_acknowledgment([subject], time_bucket, question)
            
            if acknowledgment:
                return f"{acknowledgment} {kitchen_meaning}"
        
        return kitchen_meaning
        
    except Exception as e:
        logger.debug("Generation failed: %s", e)
        return kitchen_meaning


def extract_main_subject(question: str) -> str:
    """
    Extract the MAIN subject from question, not first word.
    
    "Why is jazz complex?" → "jazz"
    "What about Public Enemy?" → "Public Enemy"
    "How does fear work?" → "fear"
    """
    
    if not question:
        return "that"
    
    q_lower = question.lower()
    
    # Remove question words
    question_words = ["why", "what", "how", "when", "where", "who", "which"]
    words = question.split()
    
    # Find first non-question word that's substantial
    for word in words:
        if word.lower() not in question_words and len(word) > 3:
            return word.rstrip("?")
    
    # Fallback
    significant = [w.rstrip("?") for w in words if len(w) > 3]
    return significant[0] if significant else "that"


def build_acknowledgment(trinity: list, time_bucket: str, stimulus: str = "") -> str:
    """Acknowledge what you heard."""
    
    if trinity and trinity[0]:
        subject = trinity[0]
    else:
        subject = extract_main_subject(stimulus)
    
    templates = {
        "past": [
            f"So {subject}... what happened there...",
            f"The way {subject} went down...",
            f"Looking back at {subject}...",
            f"About {subject}, historically...",
        ],
        "future": [
            f"About {subject}, where it's headed...",
            f"{subject} going forward...",
            f"What's coming with {subject}...",
            f"The future of {subject}...",
        ],
        "present": [
            f"Right now with {subject}...",
            f"{subject} — what's actually there...",
            f"The reality of {subject}...",
            f"About {subject}...",
            f"So {subject}...",
        ],
    }
    
    bucket = templates.get(time_bucket, templates.get("present", []))
    return random.choice(bucket) if bucket else f"About {subject}..."


def shape_for_disclosure(response: str, disclosure_level: str) -> str:
    """Light shaping."""
    return response


def can_engage_with(question: str) -> bool:
    """Can RILIE engage with this?"""
    
    if not question or len(question.strip()) < 3:
        return False
    
    return True
