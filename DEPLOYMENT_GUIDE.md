"""
SPEECH PIPELINE DEPLOYMENT GUIDE
=================================

This document explains how to wire the speech pipeline into RILIE's existing codebase.

THE ARCHITECTURE:
  Kitchen (rilie_core.py)
    ↓ generates semantic content (deep structure)
    ↓
  Response Generator (response_generator.py)
    ↓ acknowledges question + shows work
    ↓
  Speech Coherence (speech_coherence.py)
    ↓ ensures understandable (fixes critical errors only)
    ↓
  Chomsky Speech Engine (chomsky_speech_engine.py)
    ↓ transforms through grammar rules
    ↓
  Final Response (surface structure)

INTEGRATION POINTS
==================

1. IN rilie_core.py (run_pass_pipeline function)
   
   Current code returns:
   ```python
   return {
       "result": best.text,
       ...
   }
   ```
   
   Change to:
   ```python
   from speech_integration import safe_process
   
   raw_result = {
       "result": best.text,
       ...
   }
   
   # Process through speech pipeline
   processed = safe_process(
       raw_result,
       clean_stimulus,
       disclosure_level,
   )
   
   return processed
   ```

2. IN rilie.py (RILIE.process method)
   
   After Kitchen returns, speech happens automatically.
   The speech pipeline is transparent — RILIE just gets back spoken text.
   
   No changes needed in rilie.py — speech integration handles it in rilie_core.

3. IN api.py (response endpoint)
   
   The response from guvna.process() already includes spoken text.
   No changes needed — speech has already happened.

FALLBACK BEHAVIOR
=================

If any component fails:
  - Response generator unavailable → Kitchen output used as-is
  - Coherence validator unavailable → No validation applied
  - Chomsky engine unavailable → No grammar transformation
  
In all cases, response is still returned (graceful degradation).

CONFIGURATION
==============

No configuration needed. The speech pipeline works automatically.

Optional: Adjust disclosure levels in response_generator.py
  - "taste": More conversational
  - "open": Natural
  - "full": Complete, direct

TESTING
=======

Run the test suite:
  
  ```bash
  python test_speech_pipeline.py
  ```

This validates:
  - Response generation
  - Coherence validation
  - Full pipeline integration

DEBUGGING
=========

If responses are not working as expected:

1. Check component availability:
   ```python
   from speech_integration import get_speech_pipeline_status
   status = get_speech_pipeline_status()
   print(status)
   ```

2. Check individual components:
   ```python
   from response_generator import generate
   from speech_coherence import validate
   from chomsky_speech_engine import speak
   
   # Test each step
   response = generate(kitchen_meaning, question)
   coherent = validate(response, question)
   spoken = speak(coherent, question)
   ```

3. Enable debug logging:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

PERFORMANCE NOTES
=================

The speech pipeline adds minimal overhead:
  - Response generation: ~1-5ms
  - Coherence validation: <1ms
  - Chomsky transformation: ~10-50ms (if spaCy model loaded)

First call loads spaCy model (~100ms one-time cost).

PRODUCTION DEPLOYMENT
=====================

1. Install dependencies:
   ```bash
   pip install spacy
   python -m spacy download en_core_web_sm
   ```

2. Copy files to production:
   - response_generator.py
   - speech_coherence.py
   - chomsky_speech_engine.py
   - speech_integration.py
   - Updated rilie_core.py

3. Update rilie_core.py with speech integration (see section 1 above)

4. Run tests to verify:
   ```bash
   python test_speech_pipeline.py
   ```

5. Deploy and monitor:
   - Check logs for speech pipeline errors
   - Verify responses are contextually grounded
   - Monitor performance (Chomsky load time)

PRINCIPLES EMBEDDED IN IMPLEMENTATION
======================================

#49: EARNEST EFFORT > ANTISEPTIC PERFECTION
  - Responses show work (don't hide process)
  - Imperfect phrasing is okay (authentic)
  - Listeners can follow (coherent) but not sterile (human)

DIGNITY PROTOCOL
  - Every safe input treated as worthy
  - Response generation respects user's intelligence
  - Coherence validator fixes only critical errors
  - Grammar transformation preserves authenticity

CHOMSKY'S VOCAL CHORDS
  - Deep structure (meaning) → Surface structure (speech)
  - Grammar rules reshape meaning into speakable form
  - Holy trinity + temporal sense guide transformation
  - Result sounds human, not generated

CHANGELOG
=========

v1.0 (Initial)
  - Response generator (acknowledges + shows work)
  - Speech coherence validator (critical fixes only)
  - Chomsky speech engine (grammar transformation)
  - Speech integration bridge (wires components)
  - Test suite (validation)

FUTURE ENHANCEMENTS
===================

Possible improvements (not implemented yet):
  - Discourse-aware response shortening (TASTE level)
  - Emotional tone calibration (empathy detection)
  - Personality drift detection (RILIE getting repetitive)
  - Engagement metrics (did user follow up on this response?)
  - Learning from conversation (getting better with each turn)

These would use the same architecture (easy to add).

SUPPORT
=======

For issues:
  1. Check test suite output
  2. Review logs (enable DEBUG level)
  3. Test individual components
  4. Verify spaCy model is installed and working

Key files:
  - speech_integration.py: Main orchestrator
  - test_speech_pipeline.py: Validation and diagnostics
  - response_generator.py: Acknowledges + structures
  - speech_coherence.py: Fixes only critical errors
  - chomsky_speech_engine.py: Grammar transformation
"""

# This file is documentation-only. No code below.

INTEGRATION_CHECKLIST = """
DEPLOYMENT CHECKLIST
====================

Before deploying to production:

[ ] Install spaCy and download model
    pip install spacy
    python -m spacy download en_core_web_sm

[ ] Copy all speech files to production directory
    - response_generator.py
    - speech_coherence.py
    - chomsky_speech_engine.py
    - speech_integration.py

[ ] Update rilie_core.py with speech integration
    - Import speech_integration
    - Wire process_through_speech_pipeline into return statements

[ ] Run test suite
    python test_speech_pipeline.py
    Verify: All components COMPLETE, all tests PASS

[ ] Enable logging
    logging.basicConfig(level=logging.INFO)

[ ] Deploy to staging
    Verify responses are:
    - Contextually grounded (acknowledge question)
    - Coherent (understandable)
    - Human-sounding (not sterile)
    - Meaning-preserving (Kitchen's work intact)

[ ] Monitor production
    - Check for speech pipeline errors in logs
    - Verify response quality (spot-check a few)
    - Monitor performance (Chomsky load time)

[ ] Enable DEBUG logging if issues
    logging.basicConfig(level=logging.DEBUG)
    Run test suite again
    Check specific component failures

[ ] Document any customizations
    - Custom disclosure level handling
    - Modified templates in response_generator
    - Performance tuning (Chomsky model variations)

DONE. Speech pipeline is live.
RILIE now speaks.
"""
