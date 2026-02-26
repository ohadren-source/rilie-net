"""
guvna_2plus.py — DOMAIN LENSES, BASELINE, FACTORY

Owns:
- _apply_domain_lenses()
- _get_baseline()
- create_guvna() factory

Split from guvna_22.py at the domain/baseline boundary.
guvna_2.py owns all fast paths.
guvna_2plus.py owns all lookup / excavation / factory work.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from soi_domain_map import get_tracks_for_domains
from guvna_tools import SearchFn
from library import LibraryIndex

logger = logging.getLogger("guvna")


def _apply_domain_lenses(self: "Guvna", stimulus: str) -> Dict[str, Any]:
    """
    Extract domain signals from a raw stimulus string.

    Pipeline:
    1. InnerCore keyword detector (rilie_innercore.detect_domains) — fastest, no network,
       covers the 678-domain vocabulary directly.
    2. SOI library get_tracks_for_domains — called with detected DOMAIN NAME KEYS,
       NOT the raw sentence. The function expects domain-name strings, not prose.
    3. Web inference fallback _infer_domain_from_web — fires only when both InnerCore
       and SOI return nothing.

    Returns:
        {
            "matched_domains": [...],   # ordered, deduped list of domain names
            "count": int,               # number of matched domains
            "boole_substrate": str,     # e.g., "All domains reduce to bool/curve"
        }
    """
    domain_annotations: Dict[str, Any] = {}
    sl = (stimulus or "").lower().strip()

    # STEP 1: InnerCore keyword detector
    inner_domains: List[str] = []
    try:
        from rilie_innercore import detect_domains  # type: ignore

        inner_domains = detect_domains(sl) or []
        if inner_domains:
            logger.info(
                "GUVNA _apply_domain_lenses: InnerCore found %d domains: %s",
                len(inner_domains),
                inner_domains,
            )
    except Exception as e:
        logger.debug(
            "GUVNA _apply_domain_lenses: InnerCore unavailable: %s, error: %s",
            sl,
            e,
        )

    # STEP 2: SOI library lookup — pass DOMAIN NAME STRINGS, not raw stimulus
    soi_tracks: List[Any] = []
    if inner_domains:
        try:
            soi_tracks = get_tracks_for_domains(inner_domains) or []
        except Exception as e:
            logger.debug(
                "GUVNA _apply_domain_lenses: SOI lookup failed: %s", e
            )

    soi_domain_names: List[str] = [
        d.get("domain", "")
        for d in soi_tracks
        if isinstance(d, dict) and d.get("domain")
    ]

    # Merge: InnerCore names first (stimulus-derived), then SOI extras.
    # Dedupe while preserving order.
    seen: set = set()
    merged: List[str] = []
    for name in inner_domains + soi_domain_names:
        if name and name not in seen:
            seen.add(name)
            merged.append(name)

    # STEP 3: Web inference fallback — only fires when neither InnerCore nor SOI found anything.
    if not merged and hasattr(self, "_infer_domain_from_web"):
        try:
            inferred = self._infer_domain_from_web(stimulus)
            if inferred:
                merged.append(inferred)
                logger.info(
                    "GUVNA _apply_domain_lenses: web inference → %s", inferred
                )
        except Exception as e:
            logger.debug(
                "GUVNA _apply_domain_lenses: web inference failed: %s", e
            )

    if merged:
        domain_annotations["matched_domains"] = merged
        domain_annotations["count"] = len(merged)
        domain_annotations["boole_substrate"] = "All domains reduce to bool/curve"
        logger.info(
            "GUVNA _apply_domain_lenses(%r) → %s", stimulus[:60], merged
        )
    else:
        domain_annotations["matched_domains"] = []
        domain_annotations["count"] = 0
        logger.info(
            "GUVNA _apply_domain_lenses(%r) → NO DOMAINS FOUND", stimulus[:60]
        )

    return domain_annotations


def _get_baseline(self: "Guvna", stimulus: str) -> Dict[str, Any]:
    """
    Baseline text from web search.

    Strategy:
    - For clear factual GET patterns (what is, explain, tell me about, how does),
      use the raw stimulus directly.
    - For looser prompts, construct a focused query from content words and wrap it
      as 'what is the correct response to ...'.
    - Reject low-signal tutorial / lyrics / SEO garbage snippets.
    """
    baseline: Dict[str, Any] = {
        "text": "",
        "source": "",
        "raw_results": [],
    }

    stimulus_lower = (stimulus or "").lower()
    known_patterns = ["what is", "explain", "tell me about", "how does"]
    is_entity_question = any(p in stimulus_lower for p in known_patterns)
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
                "i",
                "me",
                "my",
                "we",
                "you",
                "a",
                "an",
                "the",
                "is",
                "are",
                "was",
                "were",
                "to",
                "of",
                "and",
                "or",
                "in",
                "on",
                "at",
                "be",
                "do",
                "did",
                "have",
                "has",
                "had",
                "it",
                "its",
                "this",
                "that",
                "with",
                "for",
                "about",
                "what",
                "your",
                "thoughts",
                "wanted",
                "talk",
                "tell",
                "asked",
                "think",
                "know",
                "just",
                "so",
                "any",
                "how",
                "can",
            }

            if len(_raw_query.split()) > 8:
                _words = [w.strip(".,!?;:()") for w in _raw_query.split()]
                _keywords = [
                    w for w in _words if w.lower() not in _stop and len(w) > 2
                ]
                baseline_query = " ".join(_keywords[:6]) if _keywords else _raw_query
            else:
                baseline_query = _raw_query

            results = self.search_fn(baseline_query)
            if results and isinstance(results, list):
                baseline["raw_results"] = results
                snippets = [
                    r.get("snippet", "") for r in results if r.get("snippet")
                ]

                bad_markers = [
                    "in this lesson",
                    "you'll learn the difference between",
                    "you will learn the difference between",
                    "visit englishclass101",
                    "englishclass101.com",
                    "learn english fast with real lessons",
                    "sign up for your free lifetime account",
                    "genius.com",
                    "azlyrics",
                    "songlyrics",
                    "metrolyrics",
                    "verse 1",
                    "chorus",
                    "[hook]",
                    "narration as",
                    "imdb.com/title",
                ]

                for snippet in snippets:
                    lower = snippet.lower()
                    if any(m in lower for m in bad_markers):
                        logger.info(
                            "GUVNA baseline rejected as tutorial/lyrics garbage"
                        )
                        continue

                    baseline["text"] = snippet
                    baseline["source"] = "google_baseline"
                    break
    except Exception as e:
        logger.info("GUVNA baseline lookup ERROR: %s", e)

    return baseline


# ====================================================================
# CONVENIENCE FUNCTION
# ====================================================================


def create_guvna(
    roux_seeds: Optional[Dict[str, Dict[str, Any]]] = None,
    search_fn: Optional[SearchFn] = None,
    library_index: Optional[LibraryIndex] = None,
    manifesto_path: Optional[str] = None,
    curiosity_engine: Optional[Any] = None,
) -> "Guvna":
    """
    Factory function to create a Governor with full domain library.

    Returns:
        Initialized Guvna instance with 678 domains loaded.
    """
    from guvna_1 import Guvna

    return Guvna(
        roux_seeds=roux_seeds,
        search_fn=search_fn,
        library_index=library_index,
        manifesto_path=manifesto_path,
        curiosity_engine=curiosity_engine,
    )


# -------------------------------------------------------------------
# PUBLIC ALIASES FOR GUVNA SHIM (guvna.py)
# -------------------------------------------------------------------

apply_domain_lenses = _apply_domain_lenses
get_baseline = _get_baseline
