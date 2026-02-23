"""
guvna_river.py — The River

Single responsibility:

- Read the incoming stimulus at the top of the stack.
- Run all available lookup channels (meaning, baseline, domain lenses, facts_first).
- Say what she found, once, then exit. No cooking, no plating, no TALK.

Designed to be called early from Guvna.process() in debug mode.

Current contract (Session 3, debug-only):

    river_payload = guvna_river(
        stimulus=stimulus,
        meaning=_meaning,  # or None
        get_baseline=self._get_baseline,
        apply_domain_lenses=self._apply_domain_lenses,
        compute_domain_and_factsfirst=self._compute_domain_and_factsfirst,
        debug_mode=True,  # in dev; later, wire a flag
    )

    if river_payload is not None:
        return self._finalize_response(river_payload)

In production, debug_mode will be False and the river will return None (no-op).
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple
import logging

logger = logging.getLogger("guvna.river")

# Type aliases for the hooks we expect from Guvna
GetBaselineFn = Callable[[str], Dict[str, Any]]
ApplyDomainLensesFn = Callable[[str], Dict[str, Any]]
ComputeFactsFirstFn = Callable[[str, List[str]], Tuple[Optional[str], bool]]


def guvna_river(
    *,
    stimulus: str,
    meaning: Optional[Any],
    get_baseline: GetBaselineFn,
    apply_domain_lenses: ApplyDomainLensesFn,
    compute_domain_and_factsfirst: ComputeFactsFirstFn,
    debug_mode: bool = False,
) -> Optional[Dict[str, Any]]:
    """
    The River: first read of the input, before Kitchen.

    Parameters
    ----------
    stimulus:
        Raw user text from the API (what the customer typed).
    meaning:
        Optional meaning fingerprint object from meaning.read_meaning(), or None.
        Must support .pulse and .act if present.
    get_baseline:
        Function handle to Guvna._get_baseline(stimulus) → {"text": str, ...}.
    apply_domain_lenses:
        Function handle to Guvna._apply_domain_lenses(stimulus) → {"matched_domains": [...], ...}.
    compute_domain_and_factsfirst:
        Function handle to Guvna._compute_domain_and_factsfirst(stimulus, domains)
        returning (domain_name, facts_first_flag).
    debug_mode:
        If False, river is a no-op (returns None).
        If True, river returns a one-line summary payload and short-circuits the turn.

    Returns
    -------
    Optional[Dict[str, Any]]:
        - None  → continue normal Guvna processing.
        - Dict → a payload ready to hand to Guvna._finalize_response(), which
                 will be returned to the client as-is for this turn.
    """

    if not debug_mode:
        return None

    s = (stimulus or "").strip()
    if not s:
        # Empty stimulus: nothing to read, nothing to say.
        return {
            "stimulus": stimulus,
            "result": "[DEBUG_RIVER] empty stimulus — nothing to read.",
            "status": "DEBUG_RIVER",
            "tone": "neutral",
            "quality_score": 0.0,
            "domains_hit": [],
        }

    # 1) Baseline lookup
    try:
        baseline = get_baseline(stimulus)
    except Exception as e:
        logger.warning("RIVER: get_baseline failed (non-fatal): %s", e)
        baseline = {}

    baseline_text = baseline.get("text", "") if isinstance(baseline, dict) else ""
    has_baseline = bool(baseline_text and str(baseline_text).strip())
    baseline_len = len(baseline_text) if baseline_text else 0

    # 2) Domain lenses
    try:
        domain_annotations = apply_domain_lenses(stimulus)
    except Exception as e:
        logger.warning("RIVER: apply_domain_lenses failed (non-fatal): %s", e)
        domain_annotations = {}

    soi_domain_names = domain_annotations.get("matched_domains", []) or []
    if not isinstance(soi_domain_names, list):
        soi_domain_names = []

    # 3) Facts-first computation
    try:
        _, facts_first = compute_domain_and_factsfirst(stimulus, soi_domain_names)
    except Exception as e:
        logger.warning("RIVER: compute_domain_and_factsfirst failed (non-fatal): %s", e)
        facts_first = False

    # 4) Meaning fingerprint summary
    meaning_pulse = 0.0
    meaning_act: Optional[str] = None
    if meaning is not None:
        try:
            meaning_pulse = float(getattr(meaning, "pulse", 0.0) or 0.0)
            meaning_act = getattr(meaning, "act", None)
        except Exception:
            meaning_pulse = 0.0
            meaning_act = None

    # 5) Build one-line river summary
    debug_str = (
        "[DEBUG_RIVER] "
        f"baseline_len={baseline_len}, "
        f"has_baseline={'YES' if has_baseline else 'NO'}, "
        f"domains={soi_domain_names}, "
        f"meaning_pulse={meaning_pulse:.2f}, "
        f"meaning_act={meaning_act}, "
        f"facts_first={facts_first}"
    )

    logger.info("RIVER: %s", debug_str)

    payload: Dict[str, Any] = {
        "stimulus": stimulus,
        "result": debug_str,
        "status": "DEBUG_RIVER",
        "tone": "neutral",
        "quality_score": 0.0,
        "domains_hit": soi_domain_names,
        # Extra raw data for you, in case you inspect chef_mode responses later:
        "baseline_text": baseline_text,
        "meaning": getattr(meaning, "to_dict", lambda: None)() if meaning else None,
        "facts_first": facts_first,
    }

    return payload
