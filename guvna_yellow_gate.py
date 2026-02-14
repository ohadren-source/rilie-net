"""
guvna_yellow_gate.py — Demiglace Yellow Gate
=============================================
Minimal integration of yellow warning into Guvna's decision flow.

If Triangle doesn't block AND conversation health is YELLOW:
  - Detect if tone is degrading
  - Respond shorter, clearer, less elaborate
  - Name it once if needed

No bureaucracy. Just adjustment.
"""

import logging
from typing import Optional, Tuple, Dict, Any

logger = logging.getLogger("guvna_yellow")


# ============================================================================
# TONE DEGRADATION CHECK
# ============================================================================

DEGRADATION_SIGNALS = [
    "that's stupid",
    "that doesn't make sense",
    "you're not understanding",
    "you're missing the point",
    "lol you",
    "seriously?",
    "come on",
    "pathetic",
    "ridiculous",
    "you have to",
    "you need to",
    "just do it",
    "stop wasting time",
]


def tone_is_degrading(stimulus: str) -> bool:
    """Check if tone is visibly degrading."""
    s = stimulus.lower().strip()
    return any(sig in s for sig in DEGRADATION_SIGNALS)


# ============================================================================
# YELLOW GATE DECISION
# ============================================================================

def guvna_yellow_gate(
    stimulus: str,
    triangle_result: Tuple[bool, Optional[str], str],
    health_monitor: Any,
) -> Dict[str, Any]:
    """
    Yellow gate integration point.
    
    Args:
        stimulus: Current user input
        triangle_result: (triggered, reason, trigger_type) from triangle_check
        health_monitor: ConversationHealthMonitor from triangle_check
    
    Returns:
        {
            'allow_kitchen': bool,
            'prepend_message': Optional[str],
            'lower_intensity': bool,
            'trigger_type': str,
        }
    """
    
    triggered, reason, trigger_type = triangle_result
    
    # Hard blocks: don't cook, redirect
    if triggered:
        return {
            'allow_kitchen': False,
            'prepend_message': reason,
            'lower_intensity': False,
            'trigger_type': trigger_type,
        }
    
    # Check yellow state
    threat_level = health_monitor.get_threat_level()
    
    if threat_level == "YELLOW":
        # Tone degrading?
        if tone_is_degrading(stimulus):
            return {
                'allow_kitchen': True,
                'prepend_message': "I notice the tone shifting. What's the actual problem?",
                'lower_intensity': True,
                'trigger_type': 'YELLOW',
            }
        else:
            # Yellow but tone is still okay — just lower intensity slightly
            return {
                'allow_kitchen': True,
                'prepend_message': None,
                'lower_intensity': True,
                'trigger_type': 'YELLOW',
            }
    
    # Green: full go
    return {
        'allow_kitchen': True,
        'prepend_message': None,
        'lower_intensity': False,
        'trigger_type': 'CLEAN',
    }


# ============================================================================
# INTENSITY LOWERING
# ============================================================================

def lower_response_intensity(response: str) -> str:
    """
    Respond shorter, clearer, less elaborate.
    ~50% of original length, direct answers, no elaboration.
    """
    # Split by paragraphs
    paragraphs = response.split('\n\n')
    
    if len(paragraphs) > 1:
        # Keep first paragraph + first sentence of second
        first = paragraphs[0]
        second_sents = paragraphs[1].split('. ')
        if second_sents:
            second = second_sents[0] + ('.' if not second_sents[0].endswith('.') else '')
            return first + '\n\n' + second
        return first
    
    # Single paragraph: first 2 sentences max
    sentences = response.split('. ')
    if len(sentences) > 2:
        return '. '.join(sentences[:2]) + ('.' if not sentences[1].endswith('.') else '')
    
    return response


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

"""
from rilie_triangle import triangle_check, get_health_monitor

def guvna_response(stimulus: str, history: list) -> str:
    # Triangle check
    triangle_result = triangle_check(stimulus, history)
    health_monitor = get_health_monitor()
    
    # Yellow gate decision
    decision = guvna_yellow_gate(stimulus, triangle_result, health_monitor)
    
    # If blocked, return reason
    if not decision['allow_kitchen']:
        return decision['prepend_message']
    
    # Kitchen cooks
    kitchen_response = kitchen.cook(stimulus, history)
    
    # Yellow state modifications
    if decision['prepend_message']:
        kitchen_response = decision['prepend_message'] + '\n\n' + kitchen_response
    
    if decision['lower_intensity']:
        kitchen_response = lower_response_intensity(kitchen_response)
    
    return kitchen_response
"""
