"""
test_speech_pipeline.py — VALIDATION SUITE
===========================================
Tests the full speech pipeline: Kitchen → Generation → Coherence → Grammar.

Tests what matters:
  - Does the response acknowledge what was asked? (listening)
  - Is it understandable? (coherence)
  - Does it sound human? (authenticity check)
  - Does it preserve Kitchen meaning? (semantic integrity)

Tests what doesn't matter:
  - Perfect grammar (allowed imperfection)
  - Formal structure (authentic messiness okay)
  - Word count (density vs elaboration)
"""

import logging
from typing import Dict, List, Tuple

logger = logging.getLogger("test_speech_pipeline")

# Import components
try:
    from response_generator import generate, can_engage_with
    RESPONSE_GEN_AVAILABLE = True
except ImportError:
    RESPONSE_GEN_AVAILABLE = False

try:
    from speech_coherence import validate as validate_coherence
    COHERENCE_AVAILABLE = True
except ImportError:
    COHERENCE_AVAILABLE = False

try:
    from speech_integration import process_kitchen_output
    INTEGRATION_AVAILABLE = True
except ImportError:
    INTEGRATION_AVAILABLE = False


# ============================================================================
# TEST DATA
# ============================================================================

TEST_CASES = [
    {
        "name": "Simple past question",
        "stimulus": "Why was the jazz improvisation so complex?",
        "kitchen_content": "Jazz improvisation achieves complexity through layered harmonic structures and rhythmic counterpoint.",
        "expected_properties": ["acknowledges_subject", "coherent", "human_sounding"],
    },
    {
        "name": "Future-oriented question",
        "stimulus": "What's coming next in AI research?",
        "kitchen_content": "The field is moving toward interpretability and efficiency, away from pure scale.",
        "expected_properties": ["acknowledges_subject", "coherent", "forward_looking"],
    },
    {
        "name": "Why question (explanation)",
        "stimulus": "Why do people fear change?",
        "kitchen_content": "Fear of change comes from loss of control and identity disruption.",
        "expected_properties": ["acknowledges_subject", "coherent", "empathetic"],
    },
    {
        "name": "Abstract question",
        "stimulus": "What makes something beautiful?",
        "kitchen_content": "Beauty emerges from balance between order and surprise, familiarity and novelty.",
        "expected_properties": ["acknowledges_subject", "coherent", "thoughtful"],
    },
]


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================


def test_response_generation():
    """Test that response generator creates structured responses."""
    
    if not RESPONSE_GEN_AVAILABLE:
        logger.warning("Response generator not available")
        return {"status": "SKIPPED", "reason": "Generator not available"}
    
    results = []
    
    for test_case in TEST_CASES:
        stimulus = test_case["stimulus"]
        kitchen_content = test_case["kitchen_content"]
        
        try:
            response = generate(
                kitchen_meaning=kitchen_content,
                question=stimulus,
                disclosure_level="full",
            )
            
            # Check properties
            properties_met = validate_response_properties(
                response,
                stimulus,
                test_case["expected_properties"],
            )
            
            results.append({
                "test": test_case["name"],
                "passed": properties_met,
                "response": response[:100] + "..." if len(response) > 100 else response,
            })
            
            logger.info("Generated response: %s", response[:80])
            
        except Exception as e:
            logger.error("Generation failed for '%s': %s", test_case["name"], e)
            results.append({
                "test": test_case["name"],
                "passed": False,
                "error": str(e),
            })
    
    return {
        "status": "COMPLETE",
        "component": "response_generator",
        "results": results,
        "passed": sum(1 for r in results if r["passed"]),
        "total": len(results),
    }


def test_coherence_validation():
    """Test that coherence validator preserves meaning while fixing critical errors."""
    
    if not COHERENCE_AVAILABLE:
        logger.warning("Coherence validator not available")
        return {"status": "SKIPPED", "reason": "Validator not available"}
    
    test_inputs = [
        {
            "text": "About jazz improvisation... complex layering happens through harmonic structures.",
            "stimulus": "Why was the jazz improvisation so complex?",
            "should_remain_coherent": True,
        },
        {
            "text": "They said the thing about the matter which concerns it.",
            "stimulus": "What happened?",
            "should_fix_ambiguity": True,
        },
        {
            "text": "The reality of change stems from identity disruption.",
            "stimulus": "Why do people fear change?",
            "should_remain_coherent": True,
        },
    ]
    
    results = []
    
    for test in test_inputs:
        try:
            validated = validate_coherence(test["text"], test["stimulus"])
            
            is_coherent = len(validated.strip()) > 0 and has_clear_subject(validated)
            
            results.append({
                "original": test["text"][:60],
                "validated": validated[:60],
                "coherent": is_coherent,
                "passed": is_coherent,
            })
            
            logger.info("Validated: %s → %s", test["text"][:40], validated[:40])
            
        except Exception as e:
            logger.error("Validation failed: %s", e)
            results.append({
                "original": test["text"][:60],
                "error": str(e),
                "passed": False,
            })
    
    return {
        "status": "COMPLETE",
        "component": "speech_coherence",
        "results": results,
        "passed": sum(1 for r in results if r["passed"]),
        "total": len(results),
    }


def test_full_pipeline():
    """Test the full pipeline from Kitchen to speech."""
    
    if not INTEGRATION_AVAILABLE:
        logger.warning("Speech integration not available")
        return {"status": "SKIPPED", "reason": "Integration not available"}
    
    results = []
    
    for test_case in TEST_CASES[:2]:  # Test first 2 cases
        stimulus = test_case["stimulus"]
        kitchen_output = {
            "result": test_case["kitchen_content"],
            "quality_score": 0.7,
            "status": "COMPRESSED",
        }
        
        try:
            processed = process_kitchen_output(
                kitchen_output,
                stimulus,
                disclosure_level="full",
            )
            
            final_response = processed.get("result", "")
            
            # Check that response is better than raw Kitchen output
            is_structured = len(final_response) > len(test_case["kitchen_content"])
            is_coherent = has_clear_subject(final_response)
            preserves_meaning = any(
                word in final_response.lower()
                for word in test_case["kitchen_content"].split()[:3]
                if len(word) > 3
            )
            
            passed = is_structured and is_coherent and preserves_meaning
            
            results.append({
                "test": test_case["name"],
                "raw_length": len(test_case["kitchen_content"]),
                "processed_length": len(final_response),
                "coherent": is_coherent,
                "meaning_preserved": preserves_meaning,
                "passed": passed,
                "response": final_response[:100],
            })
            
            logger.info("Pipeline test '%s': %s", test_case["name"], "PASS" if passed else "FAIL")
            
        except Exception as e:
            logger.error("Pipeline failed for '%s': %s", test_case["name"], e)
            results.append({
                "test": test_case["name"],
                "passed": False,
                "error": str(e),
            })
    
    return {
        "status": "COMPLETE",
        "component": "speech_integration",
        "results": results,
        "passed": sum(1 for r in results if r["passed"]),
        "total": len(results),
    }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def validate_response_properties(
    response: str,
    stimulus: str,
    expected: List[str],
) -> bool:
    """Check if response has expected properties."""
    
    checks = {
        "acknowledges_subject": acknowledges_subject(response, stimulus),
        "coherent": has_clear_subject(response),
        "human_sounding": is_human_sounding(response),
        "empathetic": has_emotional_language(response),
        "thoughtful": is_thoughtful(response),
        "forward_looking": has_future_language(response),
    }
    
    # All expected properties must be present
    return all(checks.get(prop, False) for prop in expected)


def acknowledges_subject(response: str, stimulus: str) -> bool:
    """Check if response acknowledges the question's subject."""
    
    # Extract key words from stimulus
    key_words = [word for word in stimulus.lower().split() if len(word) > 3]
    
    # Check if response includes at least one key word
    response_lower = response.lower()
    return any(word in response_lower for word in key_words[:3])


def has_clear_subject(text: str) -> bool:
    """Check if text has identifiable subject."""
    
    subject_starts = [
        "i ", "you ", "he ", "she ", "it ", "we ", "they ",
        "this ", "that ", "about ", "regarding ",
    ]
    
    text_lower = text.lower().strip()
    return any(text_lower.startswith(sub) for sub in subject_starts)


def is_human_sounding(text: str) -> bool:
    """Check if text sounds natural (not robotic)."""
    
    # Human speech has contractions, casual phrasing, etc.
    # Overly formal = less human
    
    human_markers = ["...", "i ", "you ", "it ", "think", "feel", "actually"]
    robotic_markers = ["hereby", "therefore", "moreover", "consequently"]
    
    human_score = sum(1 for marker in human_markers if marker in text.lower())
    robotic_score = sum(1 for marker in robotic_markers if marker in text.lower())
    
    return human_score >= robotic_score


def has_emotional_language(text: str) -> bool:
    """Check for empathetic or emotional language."""
    
    emotional_words = [
        "fear", "love", "care", "feel", "matter", "important",
        "pain", "joy", "struggle", "belong",
    ]
    
    text_lower = text.lower()
    return any(word in text_lower for word in emotional_words)


def is_thoughtful(text: str) -> bool:
    """Check if response shows thinking."""
    
    thoughtful_markers = [
        "balance", "tension", "both", "depends", "context",
        "emerges", "comes from", "shaped by",
    ]
    
    text_lower = text.lower()
    return any(marker in text_lower for marker in thoughtful_markers)


def has_future_language(text: str) -> bool:
    """Check if response is forward-looking."""
    
    future_markers = [
        "next", "coming", "ahead", "will", "forward", "future",
        "emerging", "moving toward",
    ]
    
    text_lower = text.lower()
    return any(marker in text_lower for marker in future_markers)


# ============================================================================
# RUN ALL TESTS
# ============================================================================


def run_all_tests() -> Dict:
    """Run complete validation suite."""
    
    logger.info("Starting speech pipeline tests...")
    
    return {
        "response_generation": test_response_generation(),
        "coherence_validation": test_coherence_validation(),
        "full_pipeline": test_full_pipeline(),
        "timestamp": str(__import__("datetime").datetime.now()),
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    results = run_all_tests()
    
    print("\n" + "="*60)
    print("SPEECH PIPELINE TEST RESULTS")
    print("="*60)
    
    for component, result in results.items():
        if component == "timestamp":
            continue
        
        print(f"\n{component.upper()}:")
        print(f"  Status: {result.get('status')}")
        
        if result.get("status") == "COMPLETE":
            print(f"  Passed: {result.get('passed')}/{result.get('total')}")
            for r in result.get("results", []):
                status = "✓" if r.get("passed") else "✗"
                print(f"    {status} {r.get('test', r.get('original', 'test'))[:40]}")
    
    print("\n" + "="*60)
