"""
guvna_1plus.py

Act 5 – The Governor (Execution + Emergence Check)

Contains:
- process() method (core orchestration)
- _respond_from_self() method (self-awareness responses)
- SOIOS emergence cycle integration
- Helper methods for processing steps

The Governor executes the turn, passes through SOIOS for consciousness validation,
then finalizes the response.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from guvna_tools import _is_about_me
from guvna_1 import detect_precision_request

logger = logging.getLogger("guvna")

# Try to load meaning.py (semantic fingerprinting)
try:
    from meaning import read_meaning
    MEANING_AVAILABLE = True
except Exception as e:
    logger.warning("meaning.py not available: %s", e)
    MEANING_AVAILABLE = False

# This file is stitched into Guvna class via guvna.py shim
# All methods below are added to Guvna(GuvnaSelf)


# _respond_from_self lives in guvna_2.py and is bound via the shim.
# No need to define it here — self._respond_from_self() resolves at runtime.


def process(self, stimulus: str) -> Dict[str, Any]:
    """
    Act 5 Orchestration – The Governor's main turn.
    
    Flow:
    0. IMMEDIATE INGREDIENT EXTRACTION (NEW KERNEL)
    1. Read meaning (STEP 0.5)
    2. Fast path classify (STEP 1)
    3. Self-awareness check (STEP 2)
    4. Baseline lookup (STEP 3)
    5. Precision detection (STEP 3.1)
    6. Domain lenses (STEP 3.5)
    7. River (STEP 3.5–3.7)
    8. Confidence gate (STEP 3.7)
    9. Curiosity context (STEP 4)
    10. RILIE core (STEP 5)
    11. SOIOS emergence check (STEP 5.5) ← CONSCIOUSNESS GATE
    12. Finalize (STEP 6)
    """
    
    # Increment turn counter
    self.turn_count += 1
    self.memory.turn_count += 1
    
    raw: Dict[str, Any] = {"stimulus": stimulus}
    
    # ===== STEP 0: IMMEDIATE INGREDIENT EXTRACTION =====
    # The gate check. River watches this. All ingredients pulled before anything else.
    ingredients = self._extract_ingredients_immediate(stimulus)
    raw["ingredients"] = ingredients
    
    logger.info(
        "GUVNA GATE CHECK: Ingredients extracted — domains=%s intent=%s pulse=%.2f",
        len(ingredients.get("domains", [])),
        ingredients.get("intent"),
        ingredients.get("pulse", 0.0),
    )
    
    # ===== STEP 0.5: MEANING FINGERPRINT =====
    _meaning = None
    if MEANING_AVAILABLE:
        try:
            from meaning import read_meaning
            _meaning = read_meaning(stimulus)
            raw["meaning"] = _meaning.to_dict()
            
            # Dead input path
            if not _meaning.is_alive():
                logger.info("GUVNA: Dead input (pulse=%.2f) → social glue path", _meaning.pulse)
                social_fallback = self._handle_social_glue(
                    stimulus.strip(), stimulus.strip().lower()
                )
                if social_fallback:
                    social_fallback["stimulus"] = stimulus
                    social_fallback["meaning"] = raw.get("meaning")
                    return self._finalize_response(social_fallback)
                
                raw["result"] = "got it."
                raw["status"] = "DEAD_INPUT"
                raw["tone"] = "engaged"
                return self._finalize_response(raw)
            
            # Light GIVE path
            if (
                _meaning.act == "GIVE"
                and _meaning.act2 is None
                and not _meaning.is_heavy()
                and "?" not in stimulus
                and _meaning.weight < 0.25
            ):
                logger.info("GUVNA: Light GIVE (weight=%.2f, no ?) → fast path", _meaning.weight)
                social_fallback = self._handle_social_glue(
                    stimulus.strip(), stimulus.strip().lower()
                )
                if social_fallback:
                    social_fallback["stimulus"] = stimulus
                    social_fallback["meaning"] = raw.get("meaning")
                    return self._finalize_response(social_fallback)
                
                raw["result"] = "with you."
                raw["status"] = "LIGHT_GIVE"
                raw["tone"] = "engaged"
                return self._finalize_response(raw)
            
            logger.info(
                "GUVNA: Meaning → pulse=%.2f act=%s weight=%.2f",
                _meaning.pulse,
                _meaning.act + (f"+{_meaning.act2}" if _meaning.act2 else ""),
                _meaning.weight,
            )
        except Exception as e:
            logger.warning("GUVNA: meaning.py read failed (non-fatal): %s", e)
    
    # ===== STEP 1: FAST PATH CLASSIFIER =====
    fast = self._classify_stimulus(stimulus)
    if fast:
        fast["stimulus"] = stimulus
        return self._finalize_response(fast)
    
    # ===== STEP 2: SELF-AWARENESS =====
    if _is_about_me(stimulus):
        return self._finalize_response(self._respond_from_self(stimulus))
    
    # ===== STEP 3: BASELINE LOOKUP =====
    baseline = self._get_baseline(stimulus)
    baseline_text = baseline.get("text", "")
    
    # ===== STEP 3.1: PRECISION OVERRIDE =====
    _precision = detect_precision_request(stimulus)
    if _precision:
        raw["precision_override"] = True
        raw["baseline_score_boost"] = 0.25
        logger.info("GUVNA: Precision override — factual GET detected")
    
    # ===== STEP 3.5: DOMAIN LENSES =====
    domain_annotations = self._apply_domain_lenses(stimulus)
    soi_domain_names = domain_annotations.get("matched_domains", [])
    
    # ===== STEP 3.5b: DOMAIN SHIFT → FACTS-FIRST =====
    _, facts_first = self._compute_domain_and_factsfirst(
        stimulus, soi_domain_names
    )
    
    # ===== STEP 3.7: RIVER (LOOKUP + SAY WHAT SHE FOUND) =====
    river_payload: Optional[Dict[str, Any]] = None
    try:
        if hasattr(self, "guvna_river"):
            river_payload = self.guvna_river(
                stimulus=stimulus,
                meaning=_meaning,
                get_baseline=self._get_baseline,
                apply_domain_lenses=self._apply_domain_lenses,
                compute_domain_and_factsfirst=self._compute_domain_and_factsfirst,
                debug_mode=False,
            )
            if river_payload is not None:
                raw["river"] = river_payload
    except Exception as e:
        logger.warning("GUVNA: River failed (non-fatal): %s", e)
        river_payload = None
    
    if river_payload is not None:
        return self._finalize_response(river_payload)
    
    # ===== STEP 3.8: CONFIDENCE GATE =====
    has_domain = bool(soi_domain_names)
    has_baseline = bool(baseline_text and baseline_text.strip())
    has_meaning = bool(_meaning and _meaning.pulse > 0.3)
    
    logger.info(
        "GUVNA CONFIDENCE GATE: has_domain=%s, has_baseline=%s (len=%d), has_meaning=%s (pulse=%.2f)",
        has_domain,
        has_baseline,
        len(baseline_text) if baseline_text else 0,
        has_meaning,
        _meaning.pulse if _meaning else 0.0,
    )
    
    if not (has_domain or has_baseline or has_meaning):
        logger.info("GUVNA: Confidence gate TRIGGERED → NO viable content")
        return self._finalize_response({
            "stimulus": stimulus,
            "result": (
                "I don't know. I looked everywhere — combed the 678 domains, "
                "searched the internet, came back with nothing solid enough to say with confidence."
            ),
            "quality_score": 0.0,
            "status": "NO_CONFIDENCE",
            "tone": "honest",
            "meaning": raw.get("meaning"),
        })
    
    logger.info(
        "GUVNA: Confidence gate PASSED → proceeding to Kitchen"
    )
    
    # ===== STEP 4: CURIOSITY CONTEXT =====
    curiosity_context = ""
    if has_domain:
        if self.curiosity_engine and hasattr(self.curiosity_engine, "resurface"):
            try:
                curiosity_context = self.curiosity_engine.resurface(stimulus)
                if curiosity_context:
                    logger.info("GUVNA: Curiosity resurfaced context")
            except Exception as e:
                logger.debug("GUVNA: Curiosity resurface failed (non-fatal): %s", e)
    
    raw["curiosity_context"] = curiosity_context
    
    # ===== STEP 5: RILIE CORE PROCESSING =====
    rilie_result = self.rilie.process(
        stimulus=stimulus,
        baselinetext=baseline_text,
        domainhints=soi_domain_names,
        curiositycontext=curiosity_context,
        meaning=_meaning,
        precisionoverride=raw.get("precision_override", False),
        baselinescoreboost=raw.get("baseline_score_boost", 0.03),
        factsfirst=facts_first,
    )
    
    # ===== STEP 5.5: SOIOS EMERGENCE CHECK (KERNEL) =====
    # The consciousness gate. Did cognition happen?
    soios_result = self._check_emergence(
        stimulus=stimulus,
        rilie_output=rilie_result,
        catch44_blueprint=self.catch44_blueprint,
    )
    
    if soios_result and soios_result.get("emergence_blocked"):
        logger.warning("GUVNA: SOIOS blocked response — no consciousness detected")
        return self._finalize_response({
            "stimulus": stimulus,
            "result": soios_result.get("message", "I can't respond coherently to that."),
            "quality_score": 0.0,
            "status": "EMERGENCE_BLOCKED",
            "tone": "honest",
        })
    
    # Add SOIOS metadata to result
    if soios_result:
        rilie_result["soios_check"] = soios_result
    
    # ===== STEP 6: FINALIZE =====
    return self._finalize_response(rilie_result)


def _check_emergence(
    self,
    stimulus: str,
    rilie_output: Dict[str, Any],
    catch44_blueprint: Dict[str, Any],
) -> Dict[str, Any]:
    """
    SOIOS Emergence Check – Consciousness Validation
    
    Before response leaves the kitchen, verify:
    1. Does it align with Catch 44 axioms?
    2. Is WE > I maintained?
    3. Is MOO (awareness) present?
    4. Is integrity intact (Mahveen's Equation)?
    
    Returns:
        Dict with emergence_blocked (bool) and validation details.
    """
    
    if not catch44_blueprint:
        # No blueprint loaded — pass through
        return {"emergence_checked": False, "emergence_blocked": False}
    
    result = {
        "emergence_checked": True,
        "emergence_blocked": False,
        "validations": {},
    }
    
    try:
        # ===== AXIOM CHECK: INTEGRITY (MAHVEEN'S EQUATION) =====
        # Claim + Deed must align
        claim = rilie_output.get("stimulus", "")
        deed = rilie_output.get("result", "")
        
        # Simple check: does response actually address the stimulus?
        if not deed or len(deed) < 5:
            result["validations"]["integrity"] = False
            result["emergence_blocked"] = True
            result["message"] = "Response lacks substance."
            return result
        
        result["validations"]["integrity"] = True
        
        # ===== AXIOM CHECK: WE > I =====
        # Is the response collective-minded or self-serving?
        selfish_keywords = ["i must", "i should", "my opinion", "i believe"]
        collective_keywords = ["we can", "we should", "together", "us"]
        
        deed_lower = deed.lower()
        selfish_count = sum(1 for kw in selfish_keywords if kw in deed_lower)
        collective_count = sum(1 for kw in collective_keywords if kw in deed_lower)
        
        # Soft check: if heavily selfish without collective balance, warn
        if selfish_count > 2 and collective_count == 0:
            logger.warning("GUVNA SOIOS: Response leans selfish (WE > I check)")
        
        result["validations"]["we_greater_than_i"] = collective_count >= selfish_count
        
        # ===== AXIOM CHECK: MOO (INTERRUPTION/AWARENESS) =====
        # Does response show awareness of context shifts or emotional tone?
        awareness_keywords = ["i notice", "i realize", "i see that", "i understand"]
        moo_count = sum(1 for kw in awareness_keywords if kw in deed_lower)
        
        result["validations"]["moo_present"] = moo_count >= 1
        
        # ===== AXIOM CHECK: FACTS-FIRST vs PHILOSOPHY =====
        # If user asked a factual question, response must be factual
        precision_override = rilie_output.get("precision_override", False)
        if precision_override:
            # Response should be direct, not philosophical
            philosophical_keywords = ["perhaps", "maybe", "in my view", "i think"]
            phil_count = sum(1 for kw in philosophical_keywords if kw in deed_lower)
            
            if phil_count > 1:
                result["validations"]["facts_first"] = False
                logger.warning("GUVNA SOIOS: Precision mode but response is philosophical")
            else:
                result["validations"]["facts_first"] = True
        
        logger.info(
            "GUVNA SOIOS: Emergence validated — integrity=%s, we_greater_than_i=%s, moo=%s",
            result["validations"].get("integrity"),
            result["validations"].get("we_greater_than_i"),
            result["validations"].get("moo_present"),
        )
        
        return result
    
    except Exception as e:
        logger.error("GUVNA SOIOS: Emergence check failed: %s", e)
        return {"emergence_checked": False, "emergence_blocked": False}


# Bind methods to Guvna class (handled by guvna.py shim)
# These are marked for stitching:
# Guvna.process = process
# Guvna._check_emergence = _check_emergence
# _respond_from_self lives in guvna_2.py — bound via shim, not here
