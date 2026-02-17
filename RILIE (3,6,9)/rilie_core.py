"""
rilie_core.py — THE KITCHEN PIPELINE (REFACTORED FOR COMPOSITION)
==================================================================
Interpretation generation using ROUX tracks as reasoning lenses.
Composes novel responses instead of retrieving pre-written content.

PIPELINE:
  1. detect_domains(stimulus) → List[str]
  2. match_tracks(stimulus) → List[track_index] (which ROUX tracks resonate)
  3. compose_from_tracks(stimulus, matched_tracks) → Dict[composed_thoughts]
  4. run_pass_pipeline(stimulus, baseline, max_pass) → Dict[result]
"""

import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

# Import all utilities from scorers
from rilie_core_scorers import (
    CONSCIOUSNESS_TRACKS,
    PRIORITY_HIERARCHY,
    DOMAIN_KEYWORDS,
    QuestionType,
    detect_question_type,
    extract_curiosity_context,
    strip_curiosity_context,
    compute_trite_score,
    set_trite_score,
    set_curiosity_bonus,
    anti_beige_check,
    score_amusing,
    score_insightful,
    score_nourishing,
    score_compassionate,
    score_strategic,
    _EXTERNAL_TRITE_SCORE,
)

# ✅ HARMONY INTEGRATION
from harmony import (
    HarmonicScore,
    compute_harmonic_score,
    compute_stimulus_overlap,
    is_unresolved_entity,
)

# ✅ MEANING INTEGRATION — The substrate layer
from meaning import read_meaning, MeaningFingerprint


# ============================================================================
# ROUX TRACK LOADING & MATCHING
# ============================================================================

def load_roux_tracks() -> Dict[int, Dict[str, str]]:
    """
    Load the 9 ROUX tracks from CONSCIOUSNESS_TRACKS.
    Returns: {track_num: {essence, role, name}}
    """
    tracks = {}
    for i, (key, data) in enumerate(sorted(CONSCIOUSNESS_TRACKS.items())):
        tracks[i] = {
            "name": data.get("name", f"Track {i}"),
            "essence": data.get("essence", ""),
        }
    return tracks


ROUX_TRACKS = load_roux_tracks()


def match_tracks(stimulus: str) -> List[int]:
    """
    Match ROUX tracks to stimulus by essence keywords.
    Returns list of track indices that resonate with the stimulus.
    
    Matching logic:
    - Track 0 (Alpha/Infinite): "infinite", "mastery", "deep", "endless"
    - Track 1 (Renewal): "new", "fresh", "freedom", "transform", "emerge"
    - Track 2 (Day/Night): "cycle", "persist", "yearn", "follow", "constant"
    - Track 3 (Everything): "whole", "all", "unity", "connect", "voice"
    - Track 4 (What Is): "truth", "struggle", "season", "accept", "become"
    - Track 5 (One Love): "heal", "together", "compassion", "belong", "love"
    - Track 6 (Medium): "how", "structure", "culture", "media", "why", "absurd"
    - Track 7 (Becoming Real): "real", "know", "vulnerable", "change", "action"
    - Track 8 (Presence/Grace): "grace", "notice", "humor", "present", "delight"
    """
    s = stimulus.lower()
    matched = []
    
    # Track 0: Alpha/Infinite
    if any(w in s for w in ["infinite", "endless", "forever", "always", "mastery", "deep", "technical", "skill"]):
        matched.append(0)
    
    # Track 1: Renewal/Freedom
    if any(w in s for w in ["new", "fresh", "freedom", "transform", "emerge", "change", "start", "begin"]):
        matched.append(1)
    
    # Track 2: Day/Night/Cycle
    if any(w in s for w in ["cycle", "persist", "yearn", "follow", "constant", "always", "night", "day"]):
        matched.append(2)
    
    # Track 3: Everything/Wholeness
    if any(w in s for w in ["whole", "all", "unity", "together", "connect", "resonance", "everything"]):
        matched.append(3)
    
    # Track 4: What Is/Truth
    if any(w in s for w in ["truth", "struggle", "season", "accept", "become", "meant", "spring"]):
        matched.append(4)
    
    # Track 5: One Love/Healing
    if any(w in s for w in ["heal", "compassion", "belong", "love", "together", "family", "one"]):
        matched.append(5)
    
    # Track 6: Medium/Structure
    if any(w in s for w in ["how", "why", "structure", "culture", "media", "system", "rule", "absurd"]):
        matched.append(6)
    
    # Track 7: Becoming Real
    if any(w in s for w in ["real", "know", "vulnerable", "action", "do", "change", "become"]):
        matched.append(7)
    
    # Track 8: Presence/Grace
    if any(w in s for w in ["grace", "notice", "humor", "present", "delight", "real", "funny"]):
        matched.append(8)
    
    # If no matches, pick 1-2 random tracks
    if not matched:
        matched = random.sample(range(9), min(2, 9))
    
    return list(set(matched))[:3]  # Max 3 tracks


def compose_from_tracks(stimulus: str, track_indices: List[int]) -> str:
    """
    Compose a response by blending principles from matched tracks.
    
    This is the COMPOSITION ENGINE — it doesn't retrieve, it constructs.
    Returns PURE composition, no anti-beige pollution.
    """
    if not track_indices:
        return "I'm still finding the right frame for that."
    
    # Get the essence of each matched track
    essences = [ROUX_TRACKS[i]["essence"] for i in track_indices if i in ROUX_TRACKS]
    names = [ROUX_TRACKS[i]["name"] for i in track_indices if i in ROUX_TRACKS]
    
    # Safety check: ensure we have essences
    if not essences:
        return "That's an interesting question. I'm still calibrating how to think about it."
    
    # Build connectors based on track combination
    connectors = {
        (0, 1): "flows from mastery into emergence",
        (0, 2): "extends endlessly, yet cycles back",
        (0, 3): "is infinite when all voices sing",
        (1, 2): "emerges, then cycles, then renews",
        (1, 5): "freedom blooms in togetherness",
        (2, 3): "the cycle connects everything",
        (3, 5): "wholeness is one love expressed",
        (4, 7): "truth becomes real through action",
        (6, 8): "grace is noticing how culture moves",
    }
    
    # Pick a connector or default
    key = tuple(sorted(track_indices[:2]))
    connector = connectors.get(key, "connects across dimensions")
    
    # Construct CLEAN sentence (no anti_beige pollution)
    if len(essences) == 1:
        # Single track: focus on essence
        essence = essences[0].strip()
        name = names[0] if names else "Insight"
        composed = f"{name}: {essence.lower()}."
    
    elif len(essences) >= 2:
        # Two+ tracks: blend them cleanly
        essence1 = essences[0].strip()
        essence2 = essences[1].strip()
        composed = f"{essence1.lower()} {connector} {essence2.lower()}."
    
    else:
        # Fallback
        composed = "Something connects here."
    
    # Clean up any remnant pollution
    composed = composed.replace("beige.", "").replace("mundane.", "").replace("cliche.", "").replace("recursion without emergence.", "").strip()
    
    # Ensure proper capitalization and punctuation
    if composed and not composed.endswith("."):
        composed += "."
    
    return composed[0].upper() + composed[1:] if composed else "Listening..."


# ============================================================================
# INTERPRETATION DATACLASS
# ============================================================================

@dataclass
class Interpretation:
    """One possible response to the stimulus."""

    id: int
    text: str
    domain: str
    quality_scores: Dict[str, float]
    overall_score: float
    count_met: int
    anti_beige_score: float
    depth: int
    harmonic: Optional[HarmonicScore] = None  # ✅ HARMONY FIELD


# ============================================================================
# DOMAIN DETECTION
# ============================================================================

def detect_domains(stimulus: str) -> List[str]:
    """Which domains are relevant to this stimulus?"""
    sl = (stimulus or "").lower()
    scores = {
        d: sum(1 for kw in kws if kw in sl)
        for d, kws in DOMAIN_KEYWORDS.items()
    }
    ordered = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    result = [d for d, s in ordered[:4] if s > 0]

    # ✅ Check for unresolved entity
    if is_unresolved_entity(stimulus, result):
        result.append("__unresolved_entity__")

    return result


# ============================================================================
# 9 CANDIDATE INTERPRETATIONS (COMPOSED FROM TRACKS)
# ============================================================================

SCORERS = {
    "amusing": score_amusing,
    "insightful": score_insightful,
    "nourishing": score_nourishing,
    "compassionate": score_compassionate,
    "strategic": score_strategic,
}

WEIGHTS = {
    "amusing": 1.0,
    "insightful": 0.95,
    "nourishing": 0.90,
    "compassionate": 0.85,
    "strategic": 0.80,
}


def generate_9_interpretations(
    stimulus: str,
    domains: List[str],
    depth: int = 1,
    curiosity_ctx: Optional[str] = None,
) -> List[Interpretation]:
    """
    Generate up to 9 candidate interpretations by:
    1. Matching ROUX tracks to stimulus
    2. Composing novel responses from track blends
    3. Scoring each composition
    4. Varying depth/variation for multiple passes
    """
    interpretations: List[Interpretation] = []
    idx = 0

    # Get all possible track combinations (with variation)
    base_tracks = match_tracks(stimulus)
    
    # Generate variations for this depth
    all_track_combos = []
    
    # Variation 1: Base match
    all_track_combos.append(base_tracks)
    
    # Variation 2: Add adjacent track
    if len(base_tracks) < 3:
        adjacent = [t for t in range(9) if t not in base_tracks]
        if adjacent:
            varied = base_tracks + [random.choice(adjacent)]
            all_track_combos.append(varied[:3])
    
    # Variation 3: Shift focus to different track
    if len(base_tracks) < 3:
        shifted = random.sample(range(9), min(2, 9))
        all_track_combos.append(shifted)
    
    # Variation 4: Opposite perspective (complement)
    complement = [(i + 4) % 9 for i in base_tracks[:2]]
    all_track_combos.append(complement)
    
    # Generate interpretations from track combinations
    for combo_idx, track_combo in enumerate(all_track_combos[:9]):
        # Compose response from tracks
        text = compose_from_tracks(stimulus, track_combo)
        
        if not text or text == "":
            continue
        
        # Score the composition
        anti = anti_beige_check(text)
        scores = {k: fn(text) for k, fn in SCORERS.items()}
        count = sum(1 for v in scores.values() if v > 0.3)
        overall = max(0.3, sum(scores[k] * WEIGHTS[k] for k in scores) / 4.5)

        # ✅ HARMONIC SCORING
        harmonic = compute_harmonic_score(
            text=text,
            trite_score=_EXTERNAL_TRITE_SCORE,
            cross_domain=len(track_combo) > 1,
            person_interests=None,
            domains_matched=min(len(track_combo), 2),
            stimulus_overlap=compute_stimulus_overlap(stimulus, text),
            curiosity_informed=bool(curiosity_ctx),
        )
        # Modulate overall by harmony
        overall = overall * (0.5 + harmonic.harmony * 0.5)

        interpretations.append(
            Interpretation(
                id=depth * 1000 + idx,
                text=text,
                domain=f"tracks_{','.join(str(t) for t in track_combo)}",
                quality_scores=scores,
                overall_score=overall,
                count_met=count,
                anti_beige_score=anti,
                depth=depth,
                harmonic=harmonic,  # ✅ STORE
            )
        )
        idx += 1

    return interpretations[:9]


# ============================================================================
# PASS PIPELINE – the actual cooking
# ============================================================================

def run_pass_pipeline(
    stimulus: str,
    baseline_results: Optional[List[Dict[str, str]]] = None,
    library_index: Optional[Dict[str, Dict[str, List[str]]]] = None,
    max_pass: int = 3,
    disclosure_level: str = "public",
    extra_items: Optional[Dict[str, List[str]]] = None,
) -> Dict[str, any]:
    """
    Core cooking logic: 1–max_pass depth, return best interpretation.
    Now uses ROUX tracks for composition instead of retrieval.
    Reads meaning FIRST to inform composition strategy.
    Returns COMPRESSED (early win), GUESS (honest attempt), or MISE_EN_PLACE (fallback).
    """
    clean_stimulus = strip_curiosity_context(stimulus)
    curiosity_ctx = extract_curiosity_context(stimulus)

    # ✅ READ MEANING — informs composition strategy
    meaning_fp = read_meaning(clean_stimulus)
    
    # If no pulse, short circuit
    if not meaning_fp.is_alive():
        return {
            "stimulus": clean_stimulus,
            "result": "I'm not picking up a signal there. Can you rephrase?",
            "status": "NO_PULSE",
            "meaning_fingerprint": meaning_fp,
            "harmony": 0.0,
            "syncopation": 0.0,
            "synchronicity": 0.0,
        }

    # Compute trite score from baseline
    trite = compute_trite_score(baseline_results)
    set_trite_score(trite)

    if curiosity_ctx:
        set_curiosity_bonus(0.2)

    # Question type
    q_type = detect_question_type(clean_stimulus)

    # Domains
    domains = detect_domains(clean_stimulus)
    
    # Best across all passes
    best_global: Optional[Interpretation] = None

    for current_pass in range(1, max_pass + 1):
        depth = current_pass
        # Generate compositions from ROUX tracks
        candidates = generate_9_interpretations(
            clean_stimulus, domains, depth, curiosity_ctx
        )

        if not candidates:
            continue

        # Best in this pass
        best = max(candidates, key=lambda c: c.overall_score)

        # COMPRESSED: solid early win
        if current_pass == 1 and best.overall_score > 0.75 and best.anti_beige_score > 0.6:
            return {
                "stimulus": clean_stimulus,
                "result": best.text,
                "internal_priority_score": best.overall_score,
                "comprehension": True,
                "priorities_met": best.count_met,
                "anti_beige_score": best.anti_beige_score,
                "status": "COMPRESSED",
                "depth": depth,
                "pass": current_pass,
                "disclosure_level": disclosure_level,
                "trite_score": trite,
                "curiosity_informed": bool(curiosity_ctx),
                "domains_used": domains,
                "domain": best.domain,
                "syncopation": best.harmonic.syncopation if best.harmonic else 0.0,
                "synchronicity": best.harmonic.synchronicity if best.harmonic else 0.0,
                "harmony": best.harmonic.harmony if best.harmonic else 0.0,
                "meaning_fingerprint": meaning_fp,  # ✅ MEANING
            }

        # Track best globally
        if best_global is None or best.overall_score > best_global.overall_score:
            best_global = best

    # GUESS: honest attempt when thresholds aren't met
    if best_global:
        return {
            "stimulus": clean_stimulus,
            "result": best_global.text,
            "internal_priority_score": best_global.overall_score,
            "comprehension": True,
            "priorities_met": best_global.count_met,
            "anti_beige_score": best_global.anti_beige_score,
            "status": "GUESS",
            "depth": best_global.depth,
            "pass": max_pass,
            "disclosure_level": disclosure_level,
            "trite_score": trite,
            "curiosity_informed": bool(curiosity_ctx),
            "domains_used": domains,
            "domain": best_global.domain,
            "syncopation": best_global.harmonic.syncopation if best_global.harmonic else 0.0,
            "synchronicity": best_global.harmonic.synchronicity if best_global.harmonic else 0.0,
            "harmony": best_global.harmonic.harmony if best_global.harmonic else 0.0,
            "meaning_fingerprint": meaning_fp,  # ✅ MEANING
        }

    # MISE_EN_PLACE: fallback
    return {
        "stimulus": clean_stimulus,
        "result": "I've reached the edge of what I can offer on this right now. Ask me something else?",
        "internal_priority_score": 0.3,
        "comprehension": False,
        "priorities_met": 0,
        "anti_beige_score": 0.3,
        "status": "MISE_EN_PLACE",
        "depth": max_pass - 1,
        "pass": max_pass,
        "disclosure_level": disclosure_level,
        "trite_score": trite,
        "curiosity_informed": bool(curiosity_ctx),
        "domains_used": domains,
        "domain": "",
        "syncopation": 0.0,
        "synchronicity": 0.0,
        "harmony": 0.0,
        "meaning_fingerprint": meaning_fp,  # ✅ MEANING
    }
