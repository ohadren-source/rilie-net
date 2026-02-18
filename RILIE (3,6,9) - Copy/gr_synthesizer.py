"""
gr_synthesizer.py — GOOGLE RESPONSE SYNTHESIS
==============================================
Takes MI.object (irreducible subject from meaning.py),
fetches top 3 results from Brave Search,
synthesizes them into a coherent, natural response.

GR = Google Response (ground truth from web)
"""

import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger("gr_synthesizer")


# ============================================================================
# BRAVE SEARCH WRAPPER
# ============================================================================

async def fetch_top_3_results(
    query: str,
    search_fn=None,  # Passed in from api.py (brave_search_sync or similar)
) -> List[Dict[str, str]]:
    """
    Fetch top 3 results from Brave Search.
    Returns list of {"title": str, "link": str, "snippet": str}
    """
    if not search_fn:
        logger.warning("No search_fn provided to gr_synthesizer")
        return []

    try:
        # search_fn can be sync or we wrap it
        results = search_fn(query, num_results=3)
        return results[:3]
    except Exception as e:
        logger.error(f"Error fetching search results for '{query}': {e}")
        return []


# ============================================================================
# SYNTHESIS LOGIC
# ============================================================================

def synthesize_from_snippets(
    mi_object: str,
    results: List[Dict[str, str]],
) -> str:
    """
    Take top 3 search results and synthesize into a coherent response.
    
    Strategy:
    1. Extract key phrases from each snippet (sentences, not individual words)
    2. Arrange chronologically or by relevance
    3. Connect with natural transition phrases
    4. Avoid redundancy
    5. Return as a paragraph, not bullet points
    
    Returns: synthesized response string (or empty if no results)
    """
    if not results:
        return ""

    if len(results) == 0:
        return ""

    # Extract meaningful sentences from snippets
    sentences: List[str] = []
    
    for result in results:
        snippet = result.get("snippet", "").strip()
        if not snippet:
            continue
        
        # Split snippet into sentences (naive but works)
        # Remove trailing ellipsis and clean up
        snippet = snippet.rstrip("…").rstrip(".") + "."
        
        # Take first 1-2 sentences from each snippet (not the whole thing)
        sentence_list = [s.strip() for s in snippet.split(".") if s.strip()]
        sentences.extend(sentence_list[:2])  # Max 2 sentences per result
    
    if not sentences:
        return ""
    
    # Remove duplicates while preserving order
    seen = set()
    unique_sentences = []
    for sent in sentences:
        if sent.lower() not in seen:
            seen.add(sent.lower())
            unique_sentences.append(sent)
    
    # Synthesize with transitions
    if len(unique_sentences) == 0:
        return ""
    
    if len(unique_sentences) == 1:
        return unique_sentences[0] + "."
    
    if len(unique_sentences) == 2:
        return unique_sentences[0] + ". " + unique_sentences[1] + "."
    
    # 3+ sentences: use transitions
    transitions = [
        "Additionally, ",
        "Moreover, ",
        "Furthermore, ",
        "Also, ",
        "In fact, ",
    ]
    
    result_text = unique_sentences[0] + ". "
    for i, sent in enumerate(unique_sentences[1:], start=1):
        if i < len(transitions):
            result_text += transitions[i] + sent + ". "
        else:
            result_text += sent + ". "
    
    return result_text.strip()


# ============================================================================
# PUBLIC API
# ============================================================================

async def synthesize_google_response(
    mi_object: str,
    search_fn=None,
) -> str:
    """
    Main entry point:
    1. Fetch top 3 results for MI.object
    2. Synthesize into coherent response
    3. Return GR (Google Response)
    
    Args:
        mi_object: The irreducible subject (from meaning.object)
        search_fn: Search function (brave_search_sync or similar)
    
    Returns:
        GR: Synthesized response string, or "" if no results
    """
    if not mi_object or not mi_object.strip():
        logger.warning("Empty mi_object provided to synthesize_google_response")
        return ""
    
    # Fetch top 3
    results = await fetch_top_3_results(mi_object, search_fn)
    
    if not results:
        logger.info(f"No search results for '{mi_object}'")
        return ""
    
    # Synthesize
    gr = synthesize_from_snippets(mi_object, results)
    
    logger.info(f"Synthesized GR for '{mi_object}': {len(gr)} chars")
    return gr


# ============================================================================
# SYNC WRAPPER (for use in sync contexts like guvna)
# ============================================================================

def synthesize_google_response_sync(
    mi_object: str,
    search_fn=None,
) -> str:
    """
    Synchronous wrapper around synthesize_google_response.
    Use this in guvna.process() which is synchronous.
    """
    import asyncio
    
    try:
        # If we're already in an async context, this won't work
        # Fall back to direct fetch
        if not search_fn:
            return ""
        
        # Try async first
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Already in async context, can't nest
                logger.warning("Already in async context, falling back to sync search")
                results = search_fn(mi_object, num_results=3)
                return synthesize_from_snippets(mi_object, results)
            else:
                return loop.run_until_complete(
                    synthesize_google_response(mi_object, search_fn)
                )
        except RuntimeError:
            # No event loop, create one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(
                    synthesize_google_response(mi_object, search_fn)
                )
            finally:
                loop.close()
    
    except Exception as e:
        logger.error(f"Error in synthesize_google_response_sync: {e}")
        return ""
