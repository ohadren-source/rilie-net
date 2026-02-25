# guvna_2plus.py
# DOMAIN LENSES, BASELINE, FACTORY
# Owns:
#   - apply_domain_lenses
#   - get_baseline
#   - create_guvna factory
#
# Split from guvna_22.py at the domain/baseline boundary.
# guvna_2.py owns all fast paths.
# guvna_2plus.py owns all lookup / excavation / factory work.

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from soidomainmap import gettracksfordomains
from guvnatools import SearchFn
from library import LibraryIndex

logger = logging.getLogger("guvna")


def applydomainlenses(self: "Guvna", stimulus: str) -> Dict[str, Any]:
    """
    Extract domain signals from a raw stimulus string.

    Pipeline:
    1. InnerCore keyword detector (rilieinnercore22.detectdomains) — fastest, no network,
       covers the 678-domain vocabulary directly.
    2. SOI library gettracksfordomains — called with detected DOMAIN NAME KEYS,
       NOT the raw sentence. The function expects domain-name strings, not prose.
    3. Web inference fallback inferdomainfromweb — fires only when both InnerCore
       and SOI return nothing.

    Returns:
        {
            "matched_domains": [...],   # ordered, deduped list of domain names
            "count": int,               # number of matched domains
            "boole_substrate": str,     # e.g., "All domains reduce to boolcurve"
        }
    """
    domain_annotations: Dict[str, Any] = {}
    sl = (stimulus or "").lower().strip()

    # STEP 1: InnerCore keyword detector
    inner_domains: List[str] = []
    try:
        from rilieinnercore22 import detectdomains  # type: ignore

        inner_domains = detectdomains(sl) or []
        if inner_domains:
            logger.info(
                "GUVNA applydomainlenses InnerCore found %d domains %s",
                len(inner_domains),
                inner_domains,
            )
    except Exception as e:
        logger.debug(
            "GUVNA applydomainlenses InnerCore unavailable %s, %s",
            sl,
            e,
        )

    # STEP 2: SOI library lookup — pass DOMAIN NAME STRINGS, not raw stimulus
    soi_tracks: List[Any] = []
    if inner_domains:
        try:
            soi_tracks = gettracksfordomains(inner_domains) or []
        except Exception as e:
            logger.debug(
                "GUVNA applydomainlenses SOI lookup failed %s, %s",
                sl,
                e,
            )

    soi_domain_names: List[str] = [
        d.get("domain")
        for d in soi_tracks
        if isinstance(d, dict) and d.get("domain")
    ]

    # Merge InnerCore names first, then SOI extras. Dedupe preserving order.
    seen: set = set()
    merged: List[str] = []
    for name in inner_domains + soi_domain_names:
        if name and name not in seen:
            seen.add(name)
            merged.append(name)

    # STEP 3: Web inference fallback (only if nothing so far)
    if not merged and hasattr(self, "inferdomainfromweb"):
        try:
            inferred = self.inferdomainfromweb(stimulus)
            if inferred:
                merged.append(inferred)
                logger.info(
                    "GUVNA applydomainlenses web inference %s",
                    inferred,
                )
        except Exception as e:
            logger.debug(
                "GUVNA applydomainlenses web inference failed %s, %s",
                sl,
                e,
            )

    if merged:
        domain_annotations["matched_domains"] = merged
        domain_annotations["count"] = len(merged)
        domain_annotations["boole_substrate"] = "All domains reduce to boolcurve"
        logger.info(
            "GUVNA applydomainlenses↓ %s ... %s",
            stimulus[:60],
            merged,
        )
    else:
        domain_annotations["matched_domains"] = []
        domain_annotations["count"] = 0
        logger.info(
            "GUVNA applydomainlenses↓ NO DOMAINS FOUND, %s",
            stimulus[:60],
        )

    return domain_annotations


def getbaseline(self: "Guvna", stimulus: str) -> Dict[str, Any]:
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
        "raw_results": None,
    }

    sl = (stimulus or "").lower()
    known_patterns = ["what is", "explain", "tell me about", "how does"]
    is_entity_question = any(p in sl for p in known_patterns)
    should_force_google = is_entity_question or len(stimulus or "") < 30

    if not self.searchfn:
        logger.info("GUVNA baseline lookup SKIPPED searchfn is None")
        return baseline

    try:
        logger.info(
            "GUVNA searchfns BRAVEKEYs searchfn=%s",
            bool(self.searchfn),
        )

        # Build the raw query
        if should_force_google:
            raw_query = stimulus
        else:
            raw_query = f"what is the correct response to {stimulus}"

        # Light query compression: strip stopwords and short tokens
        stop = {
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
            "if",
        }
        words = [w.strip(".,!?") for w in raw_query.split()]
        keywords = [w for w in words if w.lower() not in stop and len(w) > 2]

        if len(raw_query.split()) > 8 and keywords:
            baseline_query = " ".join(keywords[:6])
        else:
            baseline_query = raw_query

        results = self.searchfn(baseline_query)
        baseline["raw_results"] = results

        if results and isinstance(results, list):
            snippets = [r.get("snippet", "") for r in results if r.get("snippet")]

            bad_markers = [
                "in this lesson, you'll learn the difference between",
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
                "hook",
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
                baseline["source"] = "googlebaseline"
                break

        return baseline

    except Exception as e:
        logger.info("GUVNA baseline lookup ERROR %s", e)
        return baseline


def createguvna(
    rouxseeds: Optional[Dict[str, Dict[str, Any]]] = None,
    searchfn: Optional[SearchFn] = None,
    libraryindex: Optional[LibraryIndex] = None,
    manifestopath: Optional[str] = None,
    curiosityengine: Optional[Any] = None,
) -> "Guvna":
    """
    Factory function to create a Governor with full domain library.

    Returns:
        Initialized Guvna instance with 678 domains loaded.
    """
    from guvna_12 import Guvna

    return Guvna(
        rouxseeds=rouxseeds,
        searchfn=searchfn,
        libraryindex=libraryindex,
        manifestopath=manifestopath,
        curiosityengine=curiosityengine,
    )


if __name__ == "__main__":
    # Simple boot test, mirroring the original monolith pattern but
    # safe to ignore in production.
    from guvna_12 import Guvna

    guvna = createguvna()
    print(f"GUVNA booted with {guvna.librarymetadata.totaldomains} domains")
    print(f"Libraries len={len(guvna.librarymetadata.files)}")
    print(
        "Constitution",
        "Loaded" if guvna.selfstate.constitutionloaded else "Using defaults",
    )
    print("DNA Active", guvna.selfstate.dnaactive)
    print("Curiosity Engine", "Wired" if guvna.curiosityengine else "Not wired")

    greeting_response = guvna.greet("Hi, my name is Alex")
    print("Response", greeting_response.get("result"))
