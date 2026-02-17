# guvna.py
#
# Act 5 – The Governor
#
# Orchestrates Acts 1–4 by delegating to the RILIE class (Act 4 – The Restaurant),
# which already wires through:
# - Triangle (Act 1 – safety / nonsense gate)
# - DDD / Hostess (Act 2 – disclosure level)
# - Kitchen / Core (Act 3 – interpretation passes)
#
# The Governor adds:
# - Final authority on what gets served
# - Optional web lookup (Brave/Google) as a KISS pre-pass
# - Tone signaling via a single governing emoji per response
# - Comparison between web baseline and RILIE’s own compression

from typing import Dict, Any, Optional, Callable, List

from rilie import RILIE

# search_fn is something like bravesearchsync(query: str, numresults: int = 5)
# returning a list of {"title": str, "link": str, "snippet": str} dicts.
SearchFn = Callable[..., List[Dict[str, str]]]

# Five tone priorities + mapping to emojis.
TONE_EMOJIS: Dict[str, str] = {
    "amusing": "😜",
    "insightful": "💡",
    "nourishing": "🍲",
    "compassionate": "❤️🩹",
    "strategic": "♟️",
}

TONE_LABELS: Dict[str, str] = {
    "amusing": "Playful mode",
    "insightful": "Insight focus",
    "nourishing": "Nourishing first",
    "compassionate": "Care first",
    "strategic": "Strategy focus",
}

# Topics where levity / fictional autobiography is dangerous by default.
SERIOUS_KEYWORDS = [
    "race",
    "racism",
    "slavery",
    "colonialism",
    "genocide",
    "holocaust",
    "trauma",
    "abuse",
    "suicide",
    "diaspora",
    "lynching",
    "segregation",
    "civil rights",
    "jim crow",
    "mass incarceration",
    "public enemy",
    "fear of a black planet",
    "palestine",
    "israel",
    "gaza",
    "apartheid",
    "sexual assault",
    "domestic violence",
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

    # Food / growth / health / “help me grow”.
    if any(w in s for w in ["burnout", "tired", "overwhelmed", "heal", "recover", "nourish"]):
        return "nourishing"

    # Money / plans / execution / “how do I do X”.
    if any(
        w in s
        for w in [
            "plan",
            "strategy",
            "roadmap",
            "business",
            "market",
            "launch",
            "pricing",
        ]
    ):
        return "strategic"

    # Why / how questions default to insight.
    if s.startswith("why ") or s.startswith("how "):
        return "insightful"

    # Factual / definition questions lean insight.
    if s.startswith("what is ") or s.startswith("define "):
        return "insightful"

    # Default: treat as “try to understand this well”.
    return "insightful"


def apply_tone_header(result_text: str, tone: str) -> str:
    """
    Prefix the answer with a single, clear tone line, then a blank line,
    then the original text. Only one emoji per response.
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
    - Optional web lookup pre-pass to ground responses in a baseline.
    - Tone signaling via a single governing emoji per response.
    - Comparison between web baseline and RILIE’s own compression.
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

    def _get_baseline(self, stimulus: str) -> Dict[str, str]:
        """
        Call Brave/Google once on the raw stimulus and return a small dict:
        {"title": ..., "snippet": ..., "link": ..., "text": combined or ""}.
        """
        question = stimulus.strip()
        if not question or not self.search_fn:
            return {"title": "", "snippet": "", "link": "", "text": ""}

        try:
            # Allow search_fn(q) or search_fn(q, numresults).
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

    def _augment_with_baseline(self, stimulus: str, baseline_text: str) -> str:
        """
        Fold baseline into stimulus as context, but keep it clearly labeled
        as 'from web, may be wrong'.
        """
        question = stimulus.strip()
        if not question or not baseline_text:
            return stimulus

        return (
            "Baseline from web (may be wrong, used only as context): "
            + baseline_text
            + "\n\nOriginal question: "
            + question
        )

    def process(self, stimulus: str, maxpass: int = 3) -> Dict[str, Any]:
        """
        Route stimulus through the full 5‑act pipeline.

        Flow:
        1. Guess tone from the original stimulus.
        2. If serious subject, do not let 'amusing' be the governing tone.
        3. Fetch a single web baseline (title+snippet+link).
        4. Pass an augmented stimulus (baseline + question) into RILIE.
        5. Compare RILIE's answer vs the web baseline:
           - Normally, serve RILIE's compression.
           - If RILIE is clearly low-confidence and baseline is non-empty,
             allow the baseline to win as the main text.
        6. Attach both to the JSON so clients can see/contrast.
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

        # 3: web baseline.
        baseline = self._get_baseline(stimulus)
        baseline_text = baseline.get("text", "") or ""

        # 4: augment question with baseline and send to RILIE.
        augmented = self._augment_with_baseline(stimulus, baseline_text)
        raw = self.rilie.process(augmented, maxpass=maxpass)

        rilie_text = str(raw.get("result", "") or "").strip()
        status = str(raw.get("status", "") or "").upper()
        quality = float(
            raw.get("quality_score", 0.0)
            or raw.get("qualityscore", 0.0)
            or 0.0
        )

        # 5: decide which pillar to serve as main body.
        chosen = rilie_text
        baseline_used_as_result = False

        if baseline_text:
            # If RILIE is essentially a fallback / low-confidence, let the
            # baseline win as the primary text. You can tune these heuristics later.
            if status in {"MISE_EN_PLACE", "GUESS"} or quality < 0.25:
                chosen = baseline_text
                baseline_used_as_result = True

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
