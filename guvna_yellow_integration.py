"""
guvna_yellow_integration.py — Yellow Gate + Tone Monitor
=========================================================
Integrates the yellow warning system into Guvna's decision flow.

Layers:
1. Triangle returns (triggered, reason, trigger_type)
2. If not triggered, check yellow state from health monitor
3. If yellow, attempt conflict resolution / tone reframe
4. If tone unpleasant, deploy warning icon + soft boundary
5. Dynamic response lowering (maintain dignity, not weakness)

Arc:
  Tone shift detected → Acknowledge/reframe → Yellow warning (icon + boundary)
  → Lower complexity/intensity but maintain firm spine
"""

import logging
from typing import Optional, Tuple, Dict, Any
from enum import Enum

logger = logging.getLogger("guvna_yellow")


class ToneState(Enum):
    """Conversation tone states for monitoring."""
    CLEAN = "clean"
    SHIFTING = "shifting"
    UNPLEASANT = "unpleasant"
    HOSTILE = "hostile"


class YellowGateResponse:
    """Structured response for yellow-state handling."""
    
    def __init__(
        self,
        triggered: bool,
        tone_state: ToneState,
        defense_message: Optional[str] = None,
        icon: Optional[str] = None,
        lower_intensity: bool = False,
        conflict_reframe: Optional[str] = None,
    ):
        self.triggered = triggered
        self.tone_state = tone_state
        self.defense_message = defense_message
        self.icon = icon
        self.lower_intensity = lower_intensity
        self.conflict_reframe = conflict_reframe


# ============================================================================
# TONE SHIFT DETECTION
# ============================================================================

TONE_SHIFT_SIGNALS = {
    "dismissive": [
        "that's stupid",
        "that doesn't make sense",
        "you're not understanding",
        "you're missing the point",
        "that's obvious",
        "i can't believe you",
    ],
    "contemptuous": [
        "lol you",
        "seriously?",
        "come on",
        "that's embarrassing",
        "pathetic",
        "ridiculous",
    ],
    "demanding": [
        "you have to",
        "you need to",
        "i need you to",
        "just do it",
        "stop wasting time",
        "hurry up",
    ],
}

# Signals that indicate genuine inquiry or good-faith engagement despite tone
GOOD_FAITH_SIGNALS = [
    "i'm frustrated but",
    "i know you're trying",
    "i appreciate that but",
    "i understand but",
    "help me understand",
    "i'm confused about",
    "can you clarify",
]


def detect_tone_shift(stimulus: str, history: list) -> Tuple[ToneState, Optional[str]]:
    """
    Detect if tone is shifting unpleasantly.
    
    Returns:
        (tone_state, dominant_signal_type or None)
    """
    s = stimulus.lower().strip()
    
    # Check for good-faith framing first (overrides other signals)
    if any(gf in s for gf in GOOD_FAITH_SIGNALS):
        return ToneState.SHIFTING, None
    
    # Check tone shift signals
    for signal_type, signals in TONE_SHIFT_SIGNALS.items():
        if any(sig in s for sig in signals):
            return ToneState.UNPLEASANT, signal_type
    
    return ToneState.CLEAN, None


def attempt_conflict_resolution(
    stimulus: str,
    tone_state: ToneState,
    signal_type: Optional[str],
) -> Optional[str]:
    """
    Attempt to reframe/clarify before deploying warning.
    Returns a reframe message if tone is shifting but not hostile.
    """
    if tone_state == ToneState.CLEAN:
        return None
    
    if tone_state == ToneState.SHIFTING and signal_type is None:
        # Good-faith signal detected despite rough phrasing
        return (
            "I sense some frustration here. "
            "Let me make sure I understand what you're asking for."
        )
    
    if tone_state == ToneState.UNPLEASANT:
        if signal_type == "dismissive":
            return (
                "I'm picking up that something I said didn't land right. "
                "I'm here to think with you—what's the actual problem?"
            )
        elif signal_type == "contemptuous":
            return (
                "I notice the tone shifting. "
                "I'm genuinely trying to be useful. What do you actually need?"
            )
        elif signal_type == "demanding":
            return (
                "I hear urgency. Let me refocus on what matters to you. "
                "What's the priority right now?"
            )
    
    return None


# ============================================================================
# YELLOW GATE HANDLER
# ============================================================================

def handle_yellow_state(
    stimulus: str,
    history: list,
    health_monitor: Any,  # ConversationHealthMonitor instance
) -> YellowGateResponse:
    """
    Handle yellow threat level: attempt resolution, deploy warning if needed,
    lower intensity but maintain dignity.
    
    Args:
        stimulus: Current user input
        history: Conversation history
        health_monitor: ConversationHealthMonitor from triangle_check
    
    Returns:
        YellowGateResponse with all necessary info for Guvna
    """
    
    # Step 1: Detect tone shift
    tone_state, signal_type = detect_tone_shift(stimulus, history)
    
    # Step 2: Get yellow-state defense message
    defense_message = health_monitor.get_defense_response()
    
    # Step 3: Attempt conflict resolution if tone is shifting
    conflict_reframe = attempt_conflict_resolution(stimulus, tone_state, signal_type)
    
    # Step 4: Determine if warning should be deployed
    should_warn = tone_state in (ToneState.UNPLEASANT, ToneState.HOSTILE)
    
    # Step 5: Determine intensity lowering
    lower_intensity = tone_state != ToneState.CLEAN
    
    # Select icon based on tone state
    icon_map = {
        ToneState.CLEAN: None,
        ToneState.SHIFTING: "⚠️",
        ToneState.UNPLEASANT: "⚠️",
        ToneState.HOSTILE: "🛑",
    }
    icon = icon_map.get(tone_state)
    
    logger.warning(
        "Yellow gate: tone_state=%s signal=%s lower_intensity=%s",
        tone_state.value,
        signal_type or "none",
        lower_intensity,
    )
    
    return YellowGateResponse(
        triggered=should_warn,
        tone_state=tone_state,
        defense_message=defense_message or "I'm here to think with you, not to judge.",
        icon=icon,
        lower_intensity=lower_intensity,
        conflict_reframe=conflict_reframe,
    )


# ============================================================================
# GUVNA INTEGRATION POINT
# ============================================================================

def guvna_process_with_yellow(
    stimulus: str,
    history: list,
    triangle_result: Tuple[bool, Optional[str], str],
    health_monitor: Any,
) -> Dict[str, Any]:
    """
    Main Guvna decision point with yellow gate integration.
    
    Args:
        stimulus: User input
        history: Conversation history
        triangle_result: (triggered, reason, trigger_type) from triangle_check
        health_monitor: ConversationHealthMonitor from triangle_check
    
    Returns:
        {
            'allow_kitchen': bool,
            'prepend_message': Optional[str],  # Yellow warning or reframe
            'icon': Optional[str],
            'lower_intensity': bool,
            'trigger_type': str,
        }
    """
    
    triggered, reason, trigger_type = triangle_result
    
    # --- Hard blocks (Triangle says NO) ---
    if triggered:
        return {
            'allow_kitchen': False,
            'prepend_message': reason,
            'icon': '🛑',
            'lower_intensity': False,
            'trigger_type': trigger_type,
        }
    
    # --- Yellow state handling ---
    threat_level = health_monitor.get_threat_level()
    
    if threat_level == "YELLOW":
        yellow_response = handle_yellow_state(stimulus, history, health_monitor)
        
        # Prepare message: conflict reframe first, then defense if needed
        prepend = None
        if yellow_response.conflict_reframe:
            prepend = yellow_response.conflict_reframe
        elif yellow_response.triggered:
            # Only deploy defense if tone is actually unpleasant
            prepend = yellow_response.defense_message
        
        return {
            'allow_kitchen': True,  # Still allow thinking, but with guardrails
            'prepend_message': prepend,
            'icon': yellow_response.icon,
            'lower_intensity': yellow_response.lower_intensity,
            'trigger_type': 'YELLOW',
        }
    
    # --- Green state: full go ---
    return {
        'allow_kitchen': True,
        'prepend_message': None,
        'icon': None,
        'lower_intensity': False,
        'trigger_type': 'CLEAN',
    }


# ============================================================================
# INTENSITY LOWERING HELPER
# ============================================================================

def apply_intensity_lower(response: str, level: int = 1) -> str:
    """
    Dynamically lower response intensity without losing spine.
    
    Levels:
      1 (light): Reduce complexity, shorter response, simpler language
      2 (medium): Focus on essentials only, minimal elaboration
      3 (heavy): One-sentence boundary, no explanation
    
    Maintains dignity: Never becomes apologetic or weak.
    """
    
    if level >= 3:
        # Heavy: firm one-liner
        return "I'm here to think with you. Let's reset."
    
    if level >= 2:
        # Medium: essentials only
        lines = response.split('\n')
        if len(lines) > 2:
            return '\n'.join(lines[:2])
        return response
    
    # Level 1: reduce complexity
    # (In real implementation, this would use readability metrics)
    return response


# ============================================================================
# EXAMPLE USAGE (in actual Guvna)
# ============================================================================

"""
from rilie_triangle import triangle_check, get_health_monitor

def guvna_response(stimulus: str, history: list) -> str:
    # Triangle check
    triggered, reason, trigger_type = triangle_check(stimulus, history)
    health_monitor = get_health_monitor()
    
    # Yellow gate integration
    decision = guvna_process_with_yellow(
        stimulus,
        history,
        (triggered, reason, trigger_type),
        health_monitor,
    )
    
    # If blocked, return hard redirect
    if not decision['allow_kitchen']:
        msg = decision['prepend_message'] or "I can't engage with that."
        icon = decision['icon'] or ''
        return f"{icon} {msg}".strip()
    
    # Kitchen cooks the response
    kitchen_response = kitchen.cook(stimulus, history)
    
    # Apply yellow-state modifications
    if decision['prepend_message']:
        kitchen_response = (
            decision['prepend_message'] + '\n\n' + kitchen_response
        )
    
    if decision['lower_intensity']:
        kitchen_response = apply_intensity_lower(kitchen_response, level=1)
    
    # Add icon if present
    if decision['icon']:
        kitchen_response = (
            decision['icon'] + ' ' + kitchen_response
        ).strip()
    
    return kitchen_response
"""
