"""
mi_gr_compare.py — MI→RR vs GR COMPARISON & SELECTION
======================================================
Takes:
  - RR: RILIE Response (already has harmony score)
  - GR: Google Response (synthesized from web)
  - MI: Meaning Fingerprint (context)

Does:
  1. Score GR through harmony gauntlet (same as RR)
  2. Compare RR_harmony vs GR_harmony
  3. Pick winner by harmony score
  4. Return winner + both scores + confidence

Output: Selected response with metadata for logging
"""

import logging
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass

logger = logging.getLogger("mi_gr_compare")


# ============================================================================
# COMPARISON RESULT
# ============================================================================

@dataclass
class ComparisonResult:
    """Result of RR vs GR comparison."""
    selected: str  # Which won: "RR" or "GR"
    selected_text: str  # The winning response text
    
    rr_text: str  # RILIE response
    rr_harmony: float  # RILIE harmony score
    rr_syncopation: float
    rr_synchronicity: float
    
    gr_text: str  # Google response
    gr_harmony: float  # Google harmony score
    gr_syncopation: float
    gr_synchronicity: float
    
    confidence: float  # How much better is the winner? (0.0-1.0)
    margin: float  # Absolute difference in harmony
    
    source: str  # "RILIE" or "Google"


# ============================================================================
# HARMONY SCORING FOR GR
# ============================================================================

def score_gr_harmony(
    gr_text: str,
    mi_object: str,
    mi_weight: float = 0.5,
) -> Tuple[float, float, float]:
    """
    Score Google Response through harmony gauntlet.
    
    GR already has real-world relevance (it came from web search).
    We score:
    - Syncopation: How surprising/original is this synthesis? (usually lower)
    - Synchronicity: How well does it match MI.object? (usually higher)
    - Harmony: Geometric mean
    
    Args:
        gr_text: Google synthesized response
        mi_object: The irreducible subject from meaning
        mi_weight: How much should we weight relevance to MI.object?
    
    Returns:
        (syncopation, synchronicity, harmony)
    """
    from harmony import (
        score_syncopation,
        score_synchronicity,
        compute_stimulus_overlap,
    )
    
    # GR is from web, so syncopation tends to be lower (it's expected/common)
    # But well-synthesized GR can still have some surprise
    syncopation = score_syncopation(gr_text, trite_score=0.3, cross_domain=False)
    
    # GR is explicitly about MI.object, so synchronicity is usually high
    # Use compute_stimulus_overlap to measure how well it covers MI.object
    overlap = compute_stimulus_overlap(mi_object, gr_text)
    
    # Synchronicity: high overlap + web-sourced = high alignment
    synchronicity = score_synchronicity(
        gr_text,
        person_interests=None,
        domains_matched=1,
        stimulus_overlap=overlap,
        curiosity_informed=False,
    )
    
    # Boost synchronicity for GR (it's from the source of truth)
    synchronicity = min(1.0, synchronicity + (overlap * 0.2))
    
    # Compute harmony (geometric mean)
    harmony = (syncopation * synchronicity) ** 0.5
    harmony = max(0.1, min(1.0, harmony))
    
    return syncopation, synchronicity, harmony


# ============================================================================
# COMPARISON LOGIC
# ============================================================================

def compare_rr_vs_gr(
    rr_text: str,
    rr_harmony: float,
    rr_syncopation: float,
    rr_synchronicity: float,
    gr_text: str,
    mi_object: str,
) -> ComparisonResult:
    """
    Compare RILIE Response vs Google Response.
    
    1. Score GR through harmony gauntlet
    2. Compare scores
    3. Pick winner
    4. Return detailed result
    
    Args:
        rr_text: RILIE response
        rr_harmony: RILIE harmony score (already computed)
        rr_syncopation: RILIE syncopation
        rr_synchronicity: RILIE synchronicity
        gr_text: Google synthesized response
        mi_object: The irreducible subject (for context)
    
    Returns:
        ComparisonResult with winner, scores, confidence
    """
    
    # Empty GR case
    if not gr_text or not gr_text.strip():
        logger.info("Empty GR, selecting RR by default")
        return ComparisonResult(
            selected="RR",
            selected_text=rr_text,
            rr_text=rr_text,
            rr_harmony=rr_harmony,
            rr_syncopation=rr_syncopation,
            rr_synchronicity=rr_synchronicity,
            gr_text="",
            gr_harmony=0.0,
            gr_syncopation=0.0,
            gr_synchronicity=0.0,
            confidence=1.0,
            margin=rr_harmony,
            source="RILIE",
        )
    
    # Score GR
    gr_syncopation, gr_synchronicity, gr_harmony = score_gr_harmony(
        gr_text, mi_object, mi_weight=0.5
    )
    
    # Compare
    rr_score = rr_harmony
    gr_score = gr_harmony
    
    margin = abs(rr_score - gr_score)
    
    # Confidence: how much better is the winner?
    # If scores are close (< 0.1 diff), confidence is lower
    # If scores are far apart (> 0.3 diff), confidence is high
    if margin < 0.05:
        confidence = 0.5  # Very close call
    elif margin < 0.15:
        confidence = 0.7  # Moderate difference
    elif margin < 0.25:
        confidence = 0.85  # Clear winner
    else:
        confidence = 0.95  # Very clear winner
    
    # Pick winner
    if rr_score >= gr_score:
        selected = "RR"
        selected_text = rr_text
        source = "RILIE"
    else:
        selected = "GR"
        selected_text = gr_text
        source = "Google"
    
    result = ComparisonResult(
        selected=selected,
        selected_text=selected_text,
        rr_text=rr_text,
        rr_harmony=rr_harmony,
        rr_syncopation=rr_syncopation,
        rr_synchronicity=rr_synchronicity,
        gr_text=gr_text,
        gr_harmony=gr_harmony,
        gr_syncopation=gr_syncopation,
        gr_synchronicity=gr_synchronicity,
        confidence=confidence,
        margin=margin,
        source=source,
    )
    
    logger.info(
        f"Comparison: RR={rr_score:.3f} vs GR={gr_score:.3f}, "
        f"winner={selected}, confidence={confidence:.2f}"
    )
    
    return result


# ============================================================================
# PUBLIC API
# ============================================================================

def compare_and_select(
    rr_data: Dict[str, Any],  # Result dict from rilie_core.run_pass_pipeline()
    gr_text: str,  # Synthesized Google response
    mi_fingerprint=None,  # MeaningFingerprint for context
) -> ComparisonResult:
    """
    Main entry point: Compare RR vs GR and select winner.
    
    Args:
        rr_data: Full result dict from RILIE with harmony scores
        gr_text: Google synthesized response
        mi_fingerprint: MeaningFingerprint (for logging context)
    
    Returns:
        ComparisonResult with winner and detailed scores
    """
    
    # Extract RR data
    rr_text = rr_data.get("result", "")
    rr_harmony = rr_data.get("harmony", 0.0)
    rr_syncopation = rr_data.get("syncopation", 0.0)
    rr_synchronicity = rr_data.get("synchronicity", 0.0)
    
    # Get MI object for context
    mi_object = ""
    if mi_fingerprint:
        mi_object = mi_fingerprint.object
    
    # Compare and select
    result = compare_rr_vs_gr(
        rr_text=rr_text,
        rr_harmony=rr_harmony,
        rr_syncopation=rr_syncopation,
        rr_synchronicity=rr_synchronicity,
        gr_text=gr_text,
        mi_object=mi_object,
    )
    
    return result
