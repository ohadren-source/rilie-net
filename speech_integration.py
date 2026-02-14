"""
speech_integration.py — THE BRIDGE
===================================
Wires response generation and coherence validation into RILIE's core pipeline.

This is where meaning becomes speech.

Flow:
  1. Kitchen generates semantic content (deep structure)
  2. Response generator structures it (acknowledges + shows work)
  3. Coherence validator ensures it's understandable
  4. Speech coherence engine (Chomsky) transforms it grammatically
  5. Final response returned to user

Each step preserves authenticity while ensuring clarity.
"""

import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("speech_integration")

try:
    from response_generator import generate as generate_response
    RESPONSE_GENERATOR_AVAILABLE = True
except ImportError:
    RESPONSE_GENERATOR_AVAILABLE = False
    logger.warning("Response generator not available")

try:
    from speech_coherence import validate as validate_coherence
    COHERENCE_VALIDATOR_AVAILABLE = True
except ImportError:
    COHERENCE_VALIDATOR_AVAILABLE = False
    logger.warning("Speech coherence validator not available")

try:
    from chomsky_speech_engine import speak as transform_through_chomsky
    CHOMSKY_AVAILABLE = True
except ImportError:
    CHOMSKY_AVAILABLE = False
    logger.warning("Chomsky speech engine not available")


# ============================================================================
# MAIN INTEGRATION POINT
# ============================================================================


def process_kitchen_output(
    kitchen_result: Dict[str, Any],
    stimulus: str,
    disclosure_level: str = "full",
) -> Dict[str, Any]:
    """
    Take Kitchen's raw output and transform it into speech.
    
    This is the main integration point where:
      - Kitchen semantic content becomes structured response
      - Response gets validated for coherence
      - Speech gets grammatically transformed
    
    Args:
        kitchen_result: Dict with 'result' (semantic content) + metadata
        stimulus: Original user question
        disclosure_level: "taste", "open", or "full"
    
    Returns:
        Updated kitchen_result with 'result' now containing spoken text
    """
    
    if not kitchen_result or "result" not in kitchen_result:
        logger.warning("Empty kitchen result")
        return kitchen_result
    
    kitchen_semantic = str(kitchen_result.get("result", "")).strip()
    
    if not kitchen_semantic:
        logger.warning("No semantic content from Kitchen")
        return kitchen_result
    
    # Step 1: Generate structured response
    if RESPONSE_GENERATOR_AVAILABLE:
        try:
            structured = generate_response(
                kitchen_meaning=kitchen_semantic,
                question=stimulus,
                disclosure_level=disclosure_level,
            )
            logger.debug("Response generated: %d chars", len(structured))
        except Exception as e:
            logger.warning("Response generation failed: %s", e)
            structured = kitchen_semantic
    else:
        structured = kitchen_semantic
    
    # Step 2: Validate and fix coherence
    if COHERENCE_VALIDATOR_AVAILABLE:
        try:
            coherent = validate_coherence(structured, stimulus)
            logger.debug("Coherence validated")
        except Exception as e:
            logger.warning("Coherence validation failed: %s", e)
            coherent = structured
    else:
        coherent = structured
    
    # Step 3: Transform through Chomsky grammar engine
    if CHOMSKY_AVAILABLE:
        try:
            spoken = transform_through_chomsky(
                deep_structure_text=coherent,
                stimulus=stimulus,
                disclosure_level=disclosure_level,
            )
            logger.debug("Speech transformed through Chomsky")
        except Exception as e:
            logger.warning("Chomsky transformation failed: %s", e)
            spoken = coherent
    else:
        spoken = coherent
    
    # Update result with final spoken text
    kitchen_result["result"] = spoken
    kitchen_result["speech_processed"] = True
    
    return kitchen_result


# ============================================================================
# COMPONENT AVAILABILITY CHECK
# ============================================================================


def get_speech_pipeline_status() -> Dict[str, Any]:
    """
    Check which speech components are available and working.
    Used for diagnostics and fallback logic.
    """
    
    return {
        "response_generator": RESPONSE_GENERATOR_AVAILABLE,
        "coherence_validator": COHERENCE_VALIDATOR_AVAILABLE,
        "chomsky_speech_engine": CHOMSKY_AVAILABLE,
        "fully_functional": all([
            RESPONSE_GENERATOR_AVAILABLE,
            COHERENCE_VALIDATOR_AVAILABLE,
            CHOMSKY_AVAILABLE,
        ]),
    }


# ============================================================================
# FALLBACK: If something breaks, preserve Kitchen output
# ============================================================================


def safe_process(
    kitchen_result: Dict[str, Any],
    stimulus: str,
    disclosure_level: str = "full",
) -> Dict[str, Any]:
    """
    Process Kitchen output with full fallback safety.
    
    If any component fails completely, returns Kitchen output unchanged.
    At worst, user gets raw semantic content.
    """
    
    try:
        return process_kitchen_output(
            kitchen_result,
            stimulus,
            disclosure_level,
        )
    except Exception as e:
        logger.error("Speech pipeline failed completely: %s", e)
        logger.info("Returning Kitchen output unchanged")
        return kitchen_result
