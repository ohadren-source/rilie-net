"""
guvna_2plus.py — DOMAIN LENSES, BASELINE, FACTORY

Owns:
- _apply_domain_lenses()
- _get_baseline()
- create_guvna() factory
- __main__ boot test

Split from guvna_2.py (formerly guvna_22.py) at the domain lens boundary.
guvna_2.py owns all fast paths.
guvna_2plus.py owns all lookup/excavation/factory work.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from soi_domain_map import get_tracks_for_domains
from guvna_tools import SearchFn
from library import LibraryIndex

logger = logging.getLogger("guvna")


# -----------------------------------------------------------------
# DOMAIN LENSES
# -----------------------------------------------------------------
def _apply_domain_lenses(self: "Guvna", stimulus: str) -> Dict[str, Any]:
    """
    Extract domain signals from a raw stimulus string.

    Pipeline:
    1. InnerCore keyword detector (rilie_innercore_22.detect_domains) — fastest,
       no network, covers the 678-domain vocabulary directly.
    2. SOI library (get_tracks_for_domains) — called with detected DOMAIN NAME
       KEYS, NOT the raw sentence.
    3. Web inference fallback (_infer_domain_from_web) — fires only when both
       InnerCore and SOI return nothing.

    Returns {"matched_domains": [...], "count": int, "boole_substrate": str}
    """
    domain_annotations: Dict[str, Any] = {}
    sl = (stimulus or "").lower().strip()

    # STEP 1: InnerCore keyword detector
    inner_domains: List[str] = []
    try:
        from rilie_innercore_22 import detect_domains  # type: ignore
        inner_domains = detect_domains(sl) or []
        if inner_domains:
            logger.info(
                "GUVNA _apply_domain_lenses: InnerCore found %d domains: %s",
                len(inner_domains), inner_domains,
            )
    except Exception as e:
        logger.debug("GUVNA _apply_domain_lenses: InnerCore unavailable: %s", e)

    # STEP 2: SOI library lookup — pass domain NAME STRINGS, not raw stimulus
    soi_tracks: List[Any] = []
    if inner_domains:
        try:
            soi_tracks = get_tracks_for_domains(inner_domains) or []
        except Exception as e:
            logger.debug("GUVNA _apply_domain_lenses: SOI lookup failed: %s", e)

    soi_domain_names: List[str] = [
        d.get("domain", "")
        for d in soi_tracks
        if isinstance(d, dict) and d.get("domain")
    ]

    # Merge: InnerCore names first, then SOI extras. Dedupe preserving order.
    seen: set = set()
    merged: List[str] = []
    for name in inner_domains + soi_domain_names:
        if name and name not in seen:
            seen.add(name)
            merged.append(name)

    # STEP 3: Web inference fallback
    if not merged and hasattr(self, "_infer_domain_from_web"):
        try:
            inferred = self._infer_domain_from_web(stimulus)
            if inferred:
                merged.append(inferred)
                logger.info("GUVNA _apply_domain_lenses: web inference → %s", inferred)
        except Exception as e:
            logger.debug("GUVNA _apply_domain_lenses: web inference failed: %s", e)

    if merged:
        domain_annotations["matched_domains"] = merged
        domain_annotations["count"] = len(merged)
        domain_annotations["boole_substrate"] = "All domains reduce to bool/curve"
        logger.info("GUVNA _apply_domain_lenses(%r) → %s", stimulus[:60], merged)
    else:
        domain_annotations["matched_domains"] = []
        domain_annotations["count"] = 0
        logger.info("GUVNA _apply_domain_lenses(%r) → NO DOMAINS FOUND", stimulus[:60])

    return domain_annotations


# -----------------------------------------------------------------
# BASELINE LOOKUP
# -----------------------------------------------------------------
def _get_baseline(self: "Guvna", stimulus: str) -> Dict[str, Any]:
    baseline = {"text": "", "source": "", "raw_results": []}
    stimulus_lower = (stimulus or "").lower()
    known_patterns = ["what is", "explain", "tell me about", "how does"]
    is_entity_question = not any(p in stimulus_lower for p in known_patterns)
    should_force_google = is_entity_question or len(stimulus) < 30

    try:
        logger.info(
            "GUVNA: search_fn=%s BRAVE_KEY=%s",
            bool(self.search_fn),
            bool(__import__("os").getenv("BRAVE_API_KEY")),
        )
        if self.search_fn:
            _raw_query = (
                stimulus
                if should_force_google
                else f"what is the correct response to {stimulus}"
            )
            _stop = {
                "i", "me", "my", "we", "you", "a", "an", "the", "is", "are",
                "was", "were", "to", "of", "and", "or", "in", "on", "at",
                "be", "do", "did", "have", "has", "had", "it", "its",
                "this", "that", "with", "for", "about", "what", "your",
                "thoughts", "wanted", "talk", "tell", "asked", "think",
                "know", "just", "so", "any", "how", "can",
            }
            if len(_raw_query.split()) > 8:
                _words = [w.strip(".,!?;:()") for w in _raw_query.split()]
                _keywords = [w for w in _words if w.lower() not in _stop and len(w) > 2]
                baseline_query = " ".join(_keywords[:6]) if _keywords else _raw_query
            else:
                baseline_query = _raw_query

            results = self.search_fn(baseline_query)
            if results and isinstance(results, list):
                baseline["raw_results"] = results
                snippets = [r.get("snippet", "") for r in results if r.get("snippet")]
                bad_markers = [
                    "in this lesson", "you'll learn the difference between",
                    "you will learn the difference between", "visit englishclass101",
                    "englishclass101.com", "learn english fast with real lessons",
                    "sign up for your free lifetime account", "genius.com",
                    "azlyrics", "songlyrics", "metrolyrics", "verse 1",
                    "chorus", "[hook]", "narration as", "imdb.com/title",
                ]
                for snippet in snippets:
                    lower = snippet.lower()
                    if any(m in lower for m in bad_markers):
                        logger.info("GUVNA baseline rejected as tutorial/lyrics garbage")
                        continue
                    baseline["text"] = snippet
                    baseline["source"] = "google_baseline"
                    break
    except Exception as e:
        logger.info("GUVNA baseline lookup ERROR: %s", e)

    return baseline


# ====================================================================
# FACTORY
# ====================================================================
def create_guvna(
    roux_seeds: Optional[Dict[str, Dict[str, Any]]] = None,
    search_fn: Optional[SearchFn] = None,
    library_index: Optional[LibraryIndex] = None,
    manifesto_path: Optional[str] = None,
    curiosity_engine: Optional[Any] = None,
) -> "Guvna":
    """Factory function to create a Governor with full domain library."""
    from guvna_12 import Guvna
    return Guvna(
        roux_seeds=roux_seeds,
        search_fn=search_fn,
        library_index=library_index,
        manifesto_path=manifesto_path,
        curiosity_engine=curiosity_engine,
    )


if __name__ == "__main__":
    from guvna_12 import Guvna
    guvna = create_guvna()
    print(f"✓ GUVNA booted with {guvna.library_metadata.total_domains} domains")
    print(f"✓ Libraries: {len(guvna.library_metadata.files)} files")
    print(f"✓ Constitution: {'Loaded' if guvna.self_state.constitution_loaded else 'Using defaults'}")
    print(f"✓ DNA Active: {guvna.self_state.dna_active}")
    print(f"✓ Curiosity Engine: {'Wired' if guvna.curiosity_engine else 'Not wired'}")

    greeting_response = guvna.greet("Hi, my name is Alex")
    print(f"\nGreeting Response:\n{greeting_response['result']}")

    test_stimulus = "What is the relationship between density and understanding?"
    response = guvna.process(test_stimulus)
    print(f"\nTalk Response:\nTone: {response['tone']} {response['tone_emoji']}")
    print(f"Domains Used: {response['soi_domains'][:5]}")
    print(f"Conversation Health: {response['conversation_health']}")
    print(f"Curiosity Context: {response.get('curiosity_context', 'none')}")

    print("\n--- PREFERENCE FAST PATH TESTS ---")
    for test in [
        "for sure you like eric b and rakim?",
        "and no omega?",
        "you know rakim?",
        "what do you think of public enemy?",
        "you into coltrane?",
    ]:
        result = guvna.process(test)
        print(f"\nQ: {test}")
        print(f"STATUS: {result.get('status')}")
        print(f"A: {result.get('result', '')[:200]}")


# -------------------------------------------------------------------
# PUBLIC ALIASES FOR GUVNA SHIM (guvna.py)
# -------------------------------------------------------------------
apply_domain_lenses = _apply_domain_lenses
get_base
