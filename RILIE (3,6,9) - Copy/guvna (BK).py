# guvna.py

# Act 5 – The Governor

# Orchestrates Acts 1–4 by delegating to the RILIE class (Act 4 – The Restaurant),
# which already wires through:
#   - Triangle (Act 1 – safety / nonsense gate)
#   - DDD / Hostess (Act 2 – disclosure level)
#   - Kitchen / Core (Act 3 – interpretation passes)

# The Governor adds:
#   - Final authority on what gets served
#   - Optional web lookup (Brave/Google) as a LAST-RESORT rescue
#   - Tone signaling via a single governing emoji per response
#   - Comparison between web baseline and RILIE's own compression

# SEARCH PHILOSOPHY (v2 — conservative):
#   She cooks first with her own brain + banks + library.
#   Web search fires ONLY when:
#     1. Kitchen returned COURTESYEXIT (she literally has nothing)
#     2. Kitchen quality < 0.2 AND result is very short (< 40 chars)
#     3. Status is GUESS with quality < 0.15
#   Otherwise: no Brave call. She trusts her own work.

from typing import Dict, Any, Optional, Callable, List
from rilie import RILIE

# search_fn is something like brave_search_sync(query: str, num_results: int = 5)
# returning a list of {"title": str, "link": str, "snippet": str} dicts.
SearchFn = Callable[..., List[Dict[str, str]]]

# Five tone priorities + mapping to emojis.
TONE_EMOJIS: Dict[str, str] = {
    "amusing":       "\U0001f61c",
    "insightful":    "\U0001f4a1",
    "nourishing":    "\U0001f372",
    "compassionate": "\u2764\ufe0f\u200d\U0001fa79",
    "strategic":     "\u265f\ufe0f",
}

TONE_LABELS: Dict[str, str] = {
    "amusing":       "Playful mode",
    "insightful":    "Insight focus",
    "nourishing":    "Nourishing first",
    "compassionate": "Care first",
    "strategic":     "Strategy focus",
}

# Topics where levity / fictional autobiography is dangerous by default.
SERIOUS_KEYWORDS = [
    "race", "racism", "slavery", "colonialism", "genocide", "holocaust",
    "trauma", "abuse", "suicide", "diaspora", "lynching", "segregation",
    "civil rights", "jim crow", "mass incarceration", "public enemy",
    "fear of a black planet", "palestine", "israel", "gaza", "apartheid",
    "sexual assault", "domestic violence",
]


def is_serious_subject_text(stimulus: str) -> bool:
    s = stimulus.lower()
    return any(kw in s for kw in SERIOUS_KEYWORDS)


def detect_tone_from_stimulus(stimulus: str) -> str:
    """
    KISS heuristic to guess which tone the question is *asking for*.
    Used only for the single emoji + label line.
    """
    s = stimulus.strip().lower()
    if not s:
        return "insightful"

    # Explicit jokes / play.
    if any(w in s for w in ["joke", "funny", "lol", "lmao", "haha", "jajaja", "playful"]):
        return "amusing"

    # Feelings, support, relationships.
    if any(w in s for w in ["feel", "sad", "scared", "anxious", "hurt", "grief", "lonely"]):
        return "compassionate"

    # Food / growth / health / "help me grow".
    if any(w in s for w in ["burnout", "tired", "overwhelmed", "heal", "recover", "nourish"]):
        return "nourishing"

    # Money / plans / execution / "how do I do X".
    if any(w in s for w in ["plan", "strategy", "roadmap", "business", "market", "launch", "pricing"]):
        return "strategic"

    # Why / how questions default to insight.
    if s.startswith("why ") or s.startswith("how "):
        return "insightful"

    # Factual / definition questions lean insight.
    if s.startswith("what is ") or s.startswith("define "):
        return "insightful"

    # Default: treat as "try to understand this well".
    return "insightful"


def apply_tone_header(result_text: str, tone: str) -> str:
    """
    Prefix the answer with a single, clear tone line, then a blank line,
    then the original text.  Only one emoji per response.
    """
    tone = tone if tone in TONE_EMOJIS else "insightful"
    emoji = TONE_EMOJIS[tone]
    label = TONE_LABELS.get(tone, "Tone")
    header = f"{label} {emoji}"
    stripped = result_text.lstrip()
    if stripped.startswith(header):
        return result_text
    return f"{header}\n\n{result_text}"


class Guvna:
    """
    The Governor sits above The Restaurant (RILIE) and provides:
      - Final authority on what gets served.
      - Ethical oversight (12b Governor gate lives inside the Kitchen / Triangle).
      - Optional web lookup as LAST-RESORT rescue (not a crutch).
      - Tone signaling via a single governing emoji per response.
      - Comparison between web baseline and RILIE's own compression.
    """

    def __init__(
        self,
        # Preferred snake_case API:
        roux_seeds: Optional[Dict[str, Dict[str, Any]]] = None,
        search_fn: Optional[SearchFn] = None,
        # Backwards-compatible aliases for existing callers:
        rouxseeds: Optional[Dict[str, Dict[str, Any]]] = None,
        searchfn: Optional[SearchFn] = None,
    ) -> None:
        # Coalesce both naming styles.
        effective_roux = roux_seeds if roux_seeds is not None else rouxseeds
        effective_search = search_fn if search_fn is not None else searchfn
        self.roux_seeds: Dict[str, Dict[str, Any]] = effective_roux or {}
        self.search_fn: Optional[SearchFn] = effective_search
        # RILIE still expects rouxseeds/searchfn keywords.
        self.rilie = RILIE(rouxseeds=self.roux_seeds, searchfn=self.search_fn)

    def _rescue_search(self, stimulus: str) -> Dict[str, str]:
        """
        LAST-RESORT web search.  Only called when RILIE literally has no clue.
        Returns: {"title": ..., "snippet": ..., "link": ..., "text": combined or ""}.
        """
        question = stimulus.strip()
        if not question or not self.search_fn:
            return {"title": "", "snippet": "", "link": "", "text": ""}
        try:
            try:
                results = self.search_fn(question)  # type: ignore[arg-type]
            except TypeError:
                results = self.search_fn(question, 3)  # type: ignore[arg-type]
        except Exception:
            return {"title": "", "snippet": "", "link": "", "text": ""}
        if not results:
            return {"title": "", "snippet": "", "link": "", "text": ""}
        top = results[0] or {}
        title = (top.get("title") or "").strip()
        snippet = (top.get("snippet") or "").strip()
        link = (top.get("link") or "").strip()
        pieces: List[str] = []
        if title:
            pieces.append(title)
        if snippet:
            pieces.append(snippet)
        text = " — ".join(pieces) if pieces else ""
        return {"title": title, "snippet": snippet, "link": link, "text": text}

    def _needs_rescue(self, raw: Dict[str, Any]) -> bool:
        """
        Decide if RILIE's output is so weak that we need to hit the web.
        Returns True only when she literally has no clue.
        """
        status = str(raw.get("status", "") or "").upper()
        quality = float(raw.get("quality_score", 0.0) or raw.get("qualityscore", 0.0) or 0.0)
        result_text = str(raw.get("result", "") or "").strip()

        # She explicitly gave up
        if status == "COURTESYEXIT":
            return True

        # She guessed and it's terrible
        if status == "GUESS" and quality < 0.15:
            return True

        # Very low quality AND almost nothing to show for it
        if quality < 0.2 and len(result_text) < 40:
            return True

        # She has a real answer — trust her
        return False

    def process(self, stimulus: str, maxpass: int = 3) -> Dict[str, Any]:
        """
        Route stimulus through the full 5-act pipeline.

        Flow (v2 — cook first, google only if clueless):
          1. Guess tone from the original stimulus.
          2. If serious subject, do not let 'amusing' be the governing tone.
          3. Send the RAW stimulus into RILIE (no baseline — she cooks alone).
          4. Check if RILIE's answer needs rescue (_needs_rescue).
          5. If rescue needed AND search_fn available:
             - Fetch web baseline
             - If baseline is better than what she has, use it
          6. Attach both pillars to JSON for transparency.
          7. Add a single tone header line to whatever is served.
        """
        # 1–2: tone detection and safety for serious subjects.
        tone = detect_tone_from_stimulus(stimulus)
        if tone == "amusing" and is_serious_subject_text(stimulus):
            tone = (
                "compassionate"
                if any(
                    w in stimulus.lower()
                    for w in ["feel", "hurt", "scared", "pain", "grief", "trauma"]
                )
                else "insightful"
            )

        # 3: Let RILIE cook with NO web baseline — she uses her own brain first.
        raw = self.rilie.process(stimulus, maxpass=maxpass)
        rilie_text = str(raw.get("result", "") or "").strip()
        status = str(raw.get("status", "") or "").upper()
        quality = float(
            raw.get("quality_score", 0.0)
            or raw.get("qualityscore", 0.0)
            or 0.0
        )

        # 4–5: Rescue search — ONLY if she literally has no clue.
        baseline: Dict[str, str] = {"title": "", "snippet": "", "link": "", "text": ""}
        baseline_text = ""
        baseline_used_as_result = False
        chosen = rilie_text

        if self._needs_rescue(raw) and self.search_fn:
            baseline = self._rescue_search(stimulus)
            baseline_text = baseline.get("text", "") or ""

            if baseline_text:
                # She had nothing good — let the web rescue win
                if not rilie_text or len(rilie_text) < 20:
                    chosen = baseline_text
                    baseline_used_as_result = True
                elif status == "COURTESYEXIT":
                    # She gave up — use baseline as the answer
                    chosen = baseline_text
                    baseline_used_as_result = True
                elif quality < 0.15:
                    chosen = baseline_text
                    baseline_used_as_result = True
                # Otherwise keep RILIE's answer — it exists, just low quality

        # 7: apply tone header to the chosen main text.
        if chosen:
            raw["result"] = apply_tone_header(chosen, tone)
        else:
            # Nothing solid from either pillar; still give a toned shell.
            fallback_body = rilie_text or baseline_text or ""
            raw["result"] = apply_tone_header(fallback_body, tone)

        # 6: expose both pillars for transparency / future UI.
        raw["tone"] = tone
        raw["tone_emoji"] = TONE_EMOJIS.get(tone, TONE_EMOJIS["insightful"])
        raw["baseline"] = baseline  # {title, snippet, link, text}
        raw["baseline_used"] = bool(baseline_text)
        raw["baseline_used_as_result"] = baseline_used_as_result
        return raw
