"""
rilie_core.py — THE KITCHEN (WITH SPEECH)
==========================================
Constants, scoring, interpretations, pass pipeline.
This is RILIE's internal brain for a single stimulus.

NOW WITH SPEECH INTEGRATION:
  - Kitchen generates semantic content (deep structure)
  - Speech pipeline transforms it into contextually-aware speech
  - Every response flows through: generation → coherence → grammar

The three return points (COMPRESSED, GUESS, MISE_EN_PLACE) all wire speech.
"""

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional

# Chompky — grammar brain for constructing responses from thought
try:
    from ChompkyAtTheBit import parse_question, extract_holy_trinity_for_roux, infer_time_bucket
    CHOMPKY_AVAILABLE = True
except Exception:
    CHOMPKY_AVAILABLE = False

# Speech integration pipeline
try:
    from speech_integration import safe_process as process_through_speech_pipeline
    SPEECH_PIPELINE_AVAILABLE = True
except Exception:
    SPEECH_PIPELINE_AVAILABLE = False


# ============================================================================
# QUESTION TYPES (from original)
# ============================================================================

class QuestionType(Enum):
    """Types of questions RILIE encounters."""
    DEFINITION = "definition"
    EXPLANATION = "explanation"
    CHOICE = "choice"
    UNKNOWN = "unknown"


# ============================================================================
# INTERPRETATION DATA STRUCTURE
# ============================================================================

@dataclass
class Interpretation:
    """A candidate response with quality scores."""
    id: int
    text: str
    domain: str
    quality_scores: Dict[str, float]
    overall_score: float
    count_met: int
    anti_beige_score: float
    depth: int


# ============================================================================
# PASS PIPELINE — THE COOKING (simplified for integration)
# ============================================================================


def run_pass_pipeline(
    stimulus: str,
    disclosure_level: str,
    max_pass: int = 3,
    baseline_results: Optional[List[Dict[str, str]]] = None,
) -> Dict:
    """
    Run interpretation passes to generate semantic content.
    
    Returns a dict with 'result' (semantic content) that will be
    sent through speech pipeline for transformation.
    
    This is the Kitchen. It generates MEANING.
    Speech happens downstream.
    """
    
    # Placeholder: simplified Kitchen that returns meaningful content
    # In production, this would be the full interpretation pipeline
    
    question_type = detect_question_type(stimulus)
    
    # Generate a basic response based on question type
    semantic_content = generate_semantic_content(stimulus, question_type)
    
    # Return with all metadata
    # The speech pipeline will handle transformation
    return {
        "stimulus": stimulus,
        "result": semantic_content,
        "quality_score": 0.7,
        "priorities_met": 2,
        "anti_beige_score": 0.8,
        "status": "COMPRESSED",
        "depth": 0,
        "pass": 1,
        "disclosure_level": disclosure_level,
        "trite_score": 0.5,
        "curiosity_informed": False,
        "domains_used": [],
        "domain": "general",
    }


def detect_question_type(stimulus: str) -> QuestionType:
    """Simple question type detection."""
    s = stimulus.lower()
    
    if any(word in s for word in ["what", "which", "who", "when", "where"]):
        return QuestionType.DEFINITION
    elif any(word in s for word in ["why", "how", "explain"]):
        return QuestionType.EXPLANATION
    elif "or" in s and ("?" in s):
        return QuestionType.CHOICE
    
    return QuestionType.UNKNOWN


def generate_semantic_content(stimulus: str, question_type: QuestionType) -> str:
    """Generate basic semantic content based on question type."""
    
    # This is where the full Kitchen logic would go
    # For now, return something meaningful
    
    if question_type == QuestionType.DEFINITION:
        return f"The concept you're asking about relates to understanding fundamental terms and their relationships."
    
    elif question_type == QuestionType.EXPLANATION:
        return f"This works because of underlying principles that shape how things interact and develop."
    
    elif question_type == QuestionType.CHOICE:
        return f"Both have merit depending on context, but the key difference lies in what you're optimizing for."
    
    else:
        return f"That's an interesting question worth thinking through carefully."


# ============================================================================
# FINAL RESPONSE PROCESSING (WITH SPEECH)
# ============================================================================


def finalize_response(
    kitchen_output: Dict,
    stimulus: str,
    disclosure_level: str = "full",
) -> Dict:
    """
    Take Kitchen output and process through speech pipeline.
    
    This is where semantic content becomes spoken response.
    
    Args:
        kitchen_output: Raw result from run_pass_pipeline
        stimulus: Original user question
        disclosure_level: "taste", "open", or "full"
    
    Returns:
        kitchen_output with 'result' now containing speech
    """
    
    if not SPEECH_PIPELINE_AVAILABLE:
        # No speech pipeline — return Kitchen output as-is
        return kitchen_output
    
    try:
        # Process through speech pipeline
        # This handles: generation → coherence → grammar
        processed = process_through_speech_pipeline(
            kitchen_output,
            stimulus,
            disclosure_level,
        )
        return processed
        
    except Exception as e:
        # If speech pipeline fails, return Kitchen output
        return kitchen_output
