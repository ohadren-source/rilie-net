"""

rilie_innercore_22.py — THE KITCHEN PIPELINE (v4.3.0)

=====================================================

Extended pipeline: detect_domains, excavate_domains, generate_9_interpretations,
_apply_limo, run_pass_pipeline.

This is where the cooking happens. Domain detection, excavation,
interpretation generation, scoring, and the final pass pipeline.

CHANGES FROM v4.2.0 (v4.3.0):

- run_pass_pipeline() REWRITTEN to wire in Steps 6, 8, 9, 10:

  Step 6: parse_baseline_results() — Google snippets get meaning-parsed
          before comparison. No more raw text dumps. Structured data.

  Step 8: Explicit superiority comparison — Kitchen result vs parsed baseline.
          Binary: is the Kitchen sentence actually BETTER than baseline?
          Not a keyword score. Not a boost multiplier. A real comparison.

  Step 9: direct_answer_gate() — GET questions with clear objects get
          direct answers. No philosophy. No orbiting. Fires first.

  Step 10: wild_guess() — When Kitchen is empty (MISE_EN_PLACE), instead
           of silence, take a swing from whatever she has.

- New status: DIRECT_ANSWER (from Step 9 gate)
- New status: WILD_GUESS (from Step 10 swing)
- MISE_EN_PLACE now only fires when wild_guess also returns nothing.

- All other functions (detect_domains, excavate_domains,
  generate_9_interpretations, _apply_limo, _build_debug_audit) PRESERVED.

"""

from typing import List, Dict, Optional
import re
import random

from rilie_innercore_12 import (
    QuestionType,
    Interpretation,
    extract_curiosity_context,
    strip_curiosity_context,
    compute_trite_score,
    set_trite_score,
    set_curiosity_bonus,
    less_is_more_or_less,
    LIMO_AVAILABLE,
    CHOMSKY_AVAILABLE,
    SCORERS,
    WEIGHTS,
    construct_response,
    construct_blend,
    anti_beige_check,
    detect_question_type,
    logger,
    wild_guess,
)

# --- The Pantry (rilie_outercore.py) ---
from rilie_outercore import (
    DOMAIN_KNOWLEDGE,
    DOMAIN_KEYWORDS,
    WORD_DEFINITIONS,
    WORD_SYNONYMS,
    WORD_HOMONYMS,
)

# --- Chompky — grammar brain ---
try:
    from ChomskyAtTheBit import (
        parse_question,
        extract_holy_trinity_for_roux,
        infer_time_bucket,
        resolve_identity,
    )
except Exception:
    extract_holy_trinity_for_roux = None
    parse_question = None

# --- Meaning — for Step 6 parse + Step 9 gate ---
try:
    from meaning import read_meaning, MeaningFingerprint
    MEANING_AVAILABLE = True
except ImportError:
    MEANING_AVAILABLE = False

# --- Foundation — Step 6 + Step 9 functions ---
try:
    from rilie_foundation import parse_baseline_results, direct_answer_gate
    FOUNDATION_STEPS_AVAILABLE = True
except ImportError:
    FOUNDATION_STEPS_AVAILABLE = False


# ============================================================================
# DOMAIN DETECTION & EXCAVATION
# ============================================================================

def detect_domains(stimulus: str) -> List[str]:
    sl = (stimulus or "").lower()
    scores = {
        d: sum(1 for kw in kws if kw in sl)
        for d, kws in DOMAIN_KEYWORDS.items()
    }

    # Chompky boost: use holy_trinity to find domains the keywords missed
    if CHOMSKY_AVAILABLE:
        try:
            trinity = extract_holy_trinity_for_roux(stimulus)
            for word in trinity:
                wl = word.lower()
                for d, kws in DOMAIN_KEYWORDS.items():
                    if any(wl in kw or kw in wl for kw in kws):
                        scores[d] = scores.get(d, 0) + 2
        except Exception:
            pass

    ordered = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [d for d, _ in ordered[:4] if d in DOMAIN_KNOWLEDGE]


def excavate_domains(stimulus: str, domains: List[str]) -> Dict[str, List[str]]:
    """
    For each domain, sample a small subset of its internal statements.
    Prefers sub-domains that keyword-match the stimulus.
    """
    sl = (stimulus or "").lower()
    excavated: Dict[str, List[str]] = {}
    for domain in domains:
        if domain not in DOMAIN_KNOWLEDGE:
            excavated[domain] = []
            continue

        sub_items: List[tuple] = []
        for sub_key, items in DOMAIN_KNOWLEDGE[domain].items():
            sub_relevance = 1 if sub_key.lower() in sl else 0
            for item in items:
                item_words = set(item.lower().split())
                stim_words = set(sl.split())
                word_overlap = len(item_words & stim_words)
                score = sub_relevance * 2 + word_overlap
                sub_items.append((score, item))

        if sub_items:
            sub_items.sort(key=lambda x: x[0], reverse=True)
            top = [item for _, item in sub_items[:4]]
            remaining = [item for _, item in sub_items[4:]]
            if remaining:
                top.append(random.choice(remaining))
            excavated[domain] = top
        else:
            excavated[domain] = []

    # --- WORD ENRICHMENT ---
    for domain, items in excavated.items():
        enriched = []
        for item in items:
            if len(item.split()) < 5:
                word = item.strip().lower()
                definition = WORD_DEFINITIONS.get(word, "")
                synonyms = WORD_SYNONYMS.get(word, [])
                homonyms = WORD_HOMONYMS.get(word, [])
                parts = [item]
                if definition:
                    parts.append(definition)
                if synonyms:
                    parts.append("also: " + ", ".join(synonyms[:4]))
                if homonyms:
                    parts.append("other meanings: " + "; ".join(homonyms[:3]))
                enriched.append(" — ".join(parts))
            else:
                enriched.append(item)
        excavated[domain] = enriched

    return excavated


# ============================================================================
# INTERPRETATION GENERATION
# ============================================================================

_CANNED_MARKERS = [
    "the way i understand it",
    "the way i see it",
    "what it comes down to",
    "the thing about",
    "what makes",
    "the reason is",
    "the way it works",
    "the person behind",
    "what happened with",
    "where",
    "goes from here",
]


def _originality_multiplier(text: str, domain: str) -> float:
    """Generated > Searched > Canned. Always."""
    t = text.lower().strip()
    is_canned = any(t.startswith(marker) for marker in _CANNED_MARKERS)
    if is_canned:
        return 0.5
    if domain.startswith("roux") or "[roux:" in t:
        return 2.0
    if "_" in domain and domain.count("_") >= 1:
        return 2.5
    return 3.0


def generate_9_interpretations(
    stimulus: str,
    excavated: Dict[str, List[str]],
    depth: int,
    domains: Optional[List[str]] = None,
) -> List[Interpretation]:
    """Generate up to 9 internal candidate interpretations."""
    stimulus_domains = set(domains) if domains else set()

    try:
        from guvna import detect_tone_from_stimulus
        stimulus_tone = detect_tone_from_stimulus(stimulus)
    except ImportError:
        stimulus_tone = "insightful"

    _TONE_WORDS = {
        "amusing": {"funny", "humor", "laugh", "joke", "absurd", "ironic", "haha", "lol"},
        "insightful": {"because", "reason", "means", "actually", "truth", "real", "works"},
        "nourishing": {"grow", "learn", "build", "create", "teach", "develop", "nurture"},
        "compassionate": {"feel", "hurt", "care", "understand", "hear", "support", "sorry"},
        "strategic": {"plan", "move", "step", "leverage", "position", "execute", "next"},
    }

    def _relevance_score(text: str, domain: str) -> float:
        response_domains = set()
        if domain:
            for d in domain.split("_"):
                response_domains.add(d)
        domain_overlap = len(response_domains & stimulus_domains)
        if domain_overlap == 0 and stimulus_domains:
            domain_score = 0.1
        elif domain_overlap == 1:
            domain_score = 0.6
        elif domain_overlap >= 2:
            domain_score = 1.0
        else:
            domain_score = 0.3
        t_lower = text.lower()
        tone_words = _TONE_WORDS.get(stimulus_tone, set())
        tone_hits = sum(1 for tw in tone_words if tw in t_lower)
        tone_score = min(1.0, tone_hits * 0.25)
        return (domain_score * 0.7) + (tone_score * 0.3)

    def _resonance_score(text: str) -> float:
        stim_words = len(stimulus.split())
        stim_questions = stimulus.count("?")
        challenge = min(1.0, (stim_words / 30) + (stim_questions * 0.2))
        resp_words = len(text.split())
        resp_has_structure = 1.0 if any(c in text for c in ["\u2014", ":", ";"]) else 0.0
        skill = min(1.0, (resp_words / 40) + (resp_has_structure * 0.1))
        gap = abs(skill - challenge)
        return max(0.1, 1.0 - gap)

    def _final_score(raw_overall: float, text: str, domain: str) -> float:
        orig = _originality_multiplier(text, domain)
        relev = _relevance_score(text, domain)
        reson = _resonance_score(text)
        return raw_overall * orig * relev * reson

    interpretations: List[Interpretation] = []
    idx = 0

    # Single-domain items
    for domain, items in excavated.items():
        for item in items[:4]:
            text = construct_response(stimulus, item)
            anti = anti_beige_check(text)
            scores = {k: fn(text) for k, fn in SCORERS.items()}
            count = sum(1 for v in scores.values() if v > 0.3)
            raw_overall = sum(scores[k] * WEIGHTS[k] for k in scores) / 4.5
            overall = _final_score(raw_overall, text, domain)
            interpretations.append(
                Interpretation(
                    id=depth * 1000 + idx,
                    text=text,
                    domain=domain,
                    quality_scores=scores,
                    overall_score=overall,
                    count_met=count,
                    anti_beige_score=anti,
                    depth=depth,
                )
            )
            idx += 1

    # Cross-domain blends
    attempts = 0
    domain_keys = list(excavated.keys())
    while len(interpretations) < 9 and attempts < 20:
        attempts += 1
        if len(domain_keys) < 2:
            break
        d1 = random.choice(domain_keys)
        d2 = random.choice(domain_keys)
        if d1 == d2:
            continue
        if not excavated.get(d1) or not excavated.get(d2):
            continue
        i1 = random.choice(excavated[d1])
        i2 = random.choice(excavated[d2])
        text = construct_blend(stimulus, i1, i2)
        anti = anti_beige_check(text)
        scores = {k: fn(text) for k, fn in SCORERS.items()}
        count = sum(1 for v in scores.values() if v > 0.3)
        raw_overall = sum(scores[k] * WEIGHTS[k] for k in scores) / 4.5
        blend_domain = f"{d1}_{d2}"
        overall = _final_score(raw_overall, text, blend_domain)
        interpretations.append(
            Interpretation(
                id=depth * 1000 + idx,
                text=text,
                domain=f"{d1}_{d2}",
                quality_scores=scores,
                overall_score=overall,
                count_met=count,
                anti_beige_score=anti,
                depth=depth,
            )
        )
        idx += 1

    return interpretations[:9]


# ============================================================================
# LESS IS MORE OR LESS — compression gate
# ============================================================================

def _apply_limo(text: str, precision_override: bool = False) -> str:
    """
    Run LIMO compression on a response text.
    Rules:
    - precision_override=True -> skip entirely. Fact IS the demi-glace.
    - LIMO_AVAILABLE=False -> pass through unchanged (graceful fallback)
    - Otherwise: compress. Maximum signal, zero waste.
    """
    if precision_override:
        return text
    if not LIMO_AVAILABLE:
        return text
    try:
        return less_is_more_or_less(text)
    except Exception as e:
        logger.warning("LIMO compression failed (non-fatal): %s", e)
        return text


# ============================================================================
# STEP 8 — SUPERIORITY COMPARISON (v4.3.0)
# ============================================================================
# Binary: is the Kitchen sentence actually BETTER than the parsed baseline?
# Not a keyword score. Not a boost. A real comparison.
# ============================================================================

def _is_kitchen_superior(
    kitchen_text: str,
    parsed_baseline: List[Dict],
    stimulus: str,
) -> bool:
    """
    STEP 8: Is the Kitchen result superior to the best parsed baseline?

    Compares on three axes:
    1. Coherence — is it a real sentence vs word salad?
    2. Relevance — does it address the stimulus object?
    3. Substance — does it actually say something vs empty platitude?

    Returns True if Kitchen wins. False if baseline is better.
    """
    if not kitchen_text or not kitchen_text.strip():
        return False

    # Import sentence checker from innercore_12
    from rilie_innercore_12 import _is_real_sentence

    # Kitchen coherence
    kitchen_coherent = _is_real_sentence(kitchen_text)

    # Best baseline sentence
    baseline_text = ""
    baseline_relevance = 0.0
    if parsed_baseline:
        top = parsed_baseline[0]
        baseline_text = top.get("sentence", top.get("raw_snippet", ""))
        baseline_relevance = top.get("relevance", 0.0)

    if not baseline_text:
        # No baseline to compare against — Kitchen wins by default
        return True

    baseline_coherent = _is_real_sentence(baseline_text)

    # --- Axis 1: Coherence ---
    if kitchen_coherent and not baseline_coherent:
        return True
    if not kitchen_coherent and baseline_coherent:
        return False

    # --- Axis 2: Relevance to stimulus ---
    stim_lower = stimulus.lower()
    _stop = {
        "the", "a", "an", "is", "are", "was", "were", "be",
        "to", "of", "in", "for", "on", "with", "at", "by",
        "from", "and", "or", "but", "not", "it", "this", "that",
        "what", "why", "how", "who", "when", "where", "which",
        "do", "does", "did", "can", "could", "would", "should",
        "i", "you", "he", "she", "we", "they", "my", "your",
    }
    stim_words = set(stim_lower.split()) - _stop

    kitchen_words = set(re.sub(r"[^a-zA-Z0-9]", " ", kitchen_text.lower()).split()) - _stop
    baseline_words = set(re.sub(r"[^a-zA-Z0-9]", " ", baseline_text.lower()).split()) - _stop

    kitchen_overlap = len(kitchen_words & stim_words) / max(len(stim_words), 1)
    baseline_overlap = len(baseline_words & stim_words) / max(len(stim_words), 1)

    # --- Axis 3: Substance — penalize empty platitudes ---
    _PLATITUDE_MARKERS = [
        "it comes down to", "that's what drives me",
        "everything else is built on", "that's the part most people",
        "dig in and the whole picture", "that's deep",
        "i mean that sincerely", "light bulb went",
        "two sides of the same", "same root different branches",
    ]
    kitchen_platitude = sum(1 for m in _PLATITUDE_MARKERS if m in kitchen_text.lower())
    baseline_platitude = sum(1 for m in _PLATITUDE_MARKERS if m in baseline_text.lower())

    # Kitchen word count (substance indicator)
    kitchen_word_count = len(kitchen_text.split())
    baseline_word_count = len(baseline_text.split())

    # --- SCORING ---
    kitchen_score = 0.0
    baseline_score = 0.0

    # Coherence (both passed if we're here, but real sentence = bonus)
    if kitchen_coherent:
        kitchen_score += 2.0
    if baseline_coherent:
        baseline_score += 2.0

    # Relevance
    kitchen_score += kitchen_overlap * 3.0
    baseline_score += baseline_overlap * 3.0

    # Substance (penalize platitudes, reward length up to a point)
    kitchen_score -= kitchen_platitude * 1.5
    baseline_score -= baseline_platitude * 1.5
    kitchen_score += min(kitchen_word_count / 20.0, 1.5)
    baseline_score += min(baseline_word_count / 20.0, 1.5)

    # Originality bonus for Kitchen (she cooked it, baseline is regurgitation)
    kitchen_score += 0.5

    return kitchen_score >= baseline_score


# ============================================================================
# PASS PIPELINE — the actual cooking (v4.3.0)
# ============================================================================

def run_pass_pipeline(
    stimulus: str,
    disclosure_level: str,
    max_pass: int = 3,
    baseline_results: Optional[List[Dict[str, str]]] = None,
    prior_responses: Optional[List[str]] = None,
    baseline_text: str = "",
    precision_override: bool = False,
    baseline_score_boost: float = 0.03,
) -> Dict:
    """
    Run interpretation passes. Called only at OPEN or FULL disclosure.

    v4.3.0 PIPELINE:

    1. Parse stimulus with meaning.py → get fingerprint
    2. Step 9 EARLY EXIT: if GET + clear object, try direct_answer_gate first
    3. Step 6: parse baseline results → structured comparison data
    4. Domain detection + excavation → internal ingredients
    5. Generate 9 interpretations → Kitchen candidates
    6. Step 8: superiority comparison — Kitchen vs parsed baseline
    7. Step 10: if Kitchen empty, wild_guess instead of silence

    STATUS CODES (updated):
    - COMPRESSED: Kitchen cooked, served early (shallow question)
    - GUESS: Kitchen's best candidate after all passes
    - DIRECT_ANSWER: Step 9 gate fired — factual GET answered directly
    - WILD_GUESS: Step 10 — Kitchen empty but she took a swing
    - BASELINE_WIN: Step 8 — baseline was genuinely superior
    - BASELINE_FALLBACK: absolute last resort — Kitchen AND wild_guess empty
    - MISE_EN_PLACE: true silence — nothing worked at all
    """

    # Check for curiosity context
    curiosity_ctx = extract_curiosity_context(stimulus)
    clean_stimulus = strip_curiosity_context(stimulus)

    # Set external trite score
    trite = compute_trite_score(baseline_results)
    set_trite_score(trite)

    # Set curiosity bonus
    if curiosity_ctx:
        set_curiosity_bonus(0.15)
    else:
        set_curiosity_bonus(0.0)

    question_type = detect_question_type(clean_stimulus)
    domains = detect_domains(clean_stimulus)

    # ================================================================
    # STEP 6: Parse baseline results (v4.3.0)
    # ================================================================
    # Give baseline snippets a birth certificate — same parse as stimulus.
    parsed_baseline: List[Dict] = []
    stimulus_fingerprint = None

    if MEANING_AVAILABLE:
        try:
            stimulus_fingerprint = read_meaning(clean_stimulus)
        except Exception:
            pass

    if FOUNDATION_STEPS_AVAILABLE and baseline_results:
        try:
            parsed_baseline = parse_baseline_results(
                baseline_results, stimulus_fingerprint
            )
            if parsed_baseline:
                logger.info(
                    "STEP 6: parsed %d baseline results, top relevance=%.2f",
                    len(parsed_baseline),
                    parsed_baseline[0].get("relevance", 0),
                )
        except Exception as e:
            logger.debug("STEP 6 parse_baseline_results error: %s", e)

    # ================================================================
    # STEP 9: Direct answer gate — early exit for GET questions
    # ================================================================
    if FOUNDATION_STEPS_AVAILABLE and stimulus_fingerprint:
        try:
            direct = direct_answer_gate(
                stimulus_fingerprint=stimulus_fingerprint,
                kitchen_result="",  # Kitchen hasn't cooked yet
                parsed_baseline=parsed_baseline,
                raw_baseline_text=baseline_text,
            )
            if direct and direct.strip():
                logger.info("STEP 9: direct_answer_gate fired — serving direct answer")
                debug_audit = _build_debug_audit(
                    clean_stimulus, domains, None, [], [], [],
                    "DIRECT_ANSWER"
                )
                return {
                    "stimulus": clean_stimulus,
                    "result": direct,
                    "quality_score": 0.7,
                    "priorities_met": 1,
                    "anti_beige_score": 0.5,
                    "status": "DIRECT_ANSWER",
                    "depth": 0,
                    "pass": 0,
                    "disclosure_level": disclosure_level,
                    "trite_score": trite,
                    "curiosity_informed": bool(curiosity_ctx),
                    "domains_used": domains,
                    "domain": "direct_answer",
                    "limo_applied": False,
                    "precision_override": precision_override,
                    "debug_audit": debug_audit,
                }
        except Exception as e:
            logger.debug("STEP 9 direct_answer_gate error: %s", e)

    # --- Anti-deja-vu: build word sets from her recent responses ---
    _prior_word_sets: List[set] = []
    if prior_responses:
        for pr in prior_responses[-5:]:
            words = set(re.sub(r"[^a-zA-Z0-9\s]", "", pr.lower()).split())
            _prior_word_sets.append(words)

    def _is_dejavu(candidate_text: str) -> bool:
        if not _prior_word_sets or not candidate_text:
            return False
        cand_words = set(re.sub(r"[^a-zA-Z0-9\s]", "", candidate_text.lower()).split())
        if len(cand_words) < 3:
            return False
        for prior_words in _prior_word_sets:
            if not prior_words:
                continue
            overlap = cand_words & prior_words
            smaller = min(len(cand_words), len(prior_words))
            if smaller > 0 and len(overlap) / smaller > 0.6:
                return True
        return False

    excavated = excavate_domains(clean_stimulus, domains)

    # --- ROUX INJECTION ---
    roux_match = re.match(r"\[ROUX:\s*(.*?)\]\s*\n", clean_stimulus, re.DOTALL)
    if roux_match:
        roux_text = roux_match.group(1).strip()
        if roux_text:
            roux_items = [s.strip() for s in re.split(r'[.!?]+', roux_text)
                          if s.strip() and len(s.strip()) > 10]
            if roux_items:
                excavated["roux"] = roux_items[:5]
            clean_stimulus = re.sub(r"\[ROUX:.*?\]\s*\n*", "", clean_stimulus,
                                    flags=re.DOTALL).strip()

    # --- SOi DOMAIN MAP ---
    try:
        from soi_domain_map import get_human_wisdom, DOMAIN_INDEX
        soi_domains = [d for d in domains if d in DOMAIN_INDEX]
        sl = clean_stimulus.lower()
        for soi_domain in DOMAIN_INDEX:
            if soi_domain in sl and soi_domain not in soi_domains:
                soi_domains.append(soi_domain)
        if soi_domains:
            wisdom = get_human_wisdom(soi_domains, max_tracks=6)
            if wisdom:
                if "catch44" in excavated:
                    excavated["catch44"].extend(wisdom)
                else:
                    excavated["catch44"] = wisdom
    except ImportError as e:
        logger.error(
            "SOiDOMAINMAP IMPORT FAILED — Kitchen running without wisdom layer: %s", e
        )

    hard_cap = 3
    max_pass = max(1, min(max_pass, hard_cap))
    if disclosure_level == "open":
        max_pass = min(max_pass, 3)

    best_global: Optional[Interpretation] = None

    _debug_all_candidates: List[Dict] = []
    _debug_dejavu_killed: List[Dict] = []
    _debug_passes: List[Dict] = []

    for current_pass in range(1, max_pass + 1):
        depth = current_pass - 1
        nine = generate_9_interpretations(clean_stimulus, excavated, depth, domains=domains)

        if not nine:
            _debug_passes.append({"pass": current_pass, "candidates": 0, "note": "empty"})
            continue

        pass_candidates = []
        for i in nine:
            dejavu = _is_dejavu(i.text)
            entry = {
                "id": i.id,
                "domain": i.domain,
                "text": i.text[:120],
                "overall_score": round(i.overall_score, 4),
                "count_met": i.count_met,
                "anti_beige": round(i.anti_beige_score, 3),
                "dejavu_blocked": dejavu,
            }
            pass_candidates.append(entry)
            _debug_all_candidates.append(entry)
            if dejavu:
                _debug_dejavu_killed.append(entry)

        filtered = [
            i for i in nine
            if (i.overall_score > (
                # FIX 5: factual domains get a lower gate
                0.04 if any(d in domains for d in ["music", "culinary", "science", "mathematics"])
                else (0.06 if current_pass == 1 else 0.09)
            ) or i.count_met >= 1)
            and not _is_dejavu(i.text)
        ]

        if not filtered and nine:
            def _dejavu_score(text: str) -> float:
                if not _prior_word_sets or not text:
                    return 0.0
                cand_words = set(re.sub(r"[^a-zA-Z0-9\s]", "", text.lower()).split())
                if len(cand_words) < 3:
                    return 0.0
                best_overlap = 0.0
                for pw in _prior_word_sets:
                    if not pw:
                        continue
                    overlap = cand_words & pw
                    smaller = min(len(cand_words), len(pw))
                    if smaller > 0:
                        best_overlap = max(best_overlap, len(overlap) / smaller)
                return best_overlap

            ranked = sorted(nine, key=lambda x: _dejavu_score(x.text))
            filtered = [ranked[0]]

        _debug_passes.append({
            "pass": current_pass,
            "candidates": len(nine),
            "survived_filter": len(filtered),
            "dejavu_killed": sum(1 for c in pass_candidates if c["dejavu_blocked"]),
        })

        if filtered:
            best = max(filtered, key=lambda x: (x.count_met, x.overall_score))
        else:
            best = max(nine, key=lambda x: x.overall_score)

        if (best_global is None) or (best.overall_score > best_global.overall_score):
            best_global = best

        # Compress quickly for shallow questions
        if current_pass <= 2 and question_type in {
            QuestionType.UNKNOWN,
            QuestionType.CHOICE,
            QuestionType.DEFINITION,
        }:
            debug_audit = _build_debug_audit(
                clean_stimulus, domains, best, _debug_all_candidates,
                _debug_dejavu_killed, _debug_passes, "COMPRESSED"
            )

            compressed_text = _apply_limo(best.text, precision_override=precision_override)

            return {
                "stimulus": clean_stimulus,
                "result": compressed_text,
                "quality_score": best.overall_score,
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
                "limo_applied": LIMO_AVAILABLE and not precision_override,
                "precision_override": precision_override,
                "debug_audit": debug_audit,
            }

    # ==================================================================
    # FINAL TALLY — Step 8 superiority comparison
    # ==================================================================

    def _clean_baseline(bl: str) -> str:
        """Strip HTML, clean up, cut at sentence boundary."""
        if not bl:
            return ""
        import html
        bl = html.unescape(bl)
        bl = re.sub(r"<[^>]+>", "", bl)
        bl = re.sub(r"\s+", " ", bl).strip()
        if len(bl) > 300:
            bl = bl[:300]
            for sep in [". ", "! ", "? "]:
                idx = bl.rfind(sep)
                if idx > 50:
                    bl = bl[:idx + 1]
                    break
            else:
                bl = bl.rsplit(" ", 1)[0]
        return bl

    if best_global is not None:
        # ============================================================
        # STEP 8: Is Kitchen actually superior to parsed baseline?
        # ============================================================
        kitchen_text = best_global.text

        # Run LIMO first (same as before)
        kitchen_text = _apply_limo(kitchen_text, precision_override=precision_override)

        # Check superiority
        if parsed_baseline and not _is_kitchen_superior(kitchen_text, parsed_baseline, clean_stimulus):
            # Baseline is genuinely better. Serve it.
            best_baseline_sentence = parsed_baseline[0].get("sentence", "")
            if best_baseline_sentence and len(best_baseline_sentence.split()) >= 5:
                logger.info(
                    "STEP 8: baseline superior (kitchen lost comparison). Serving baseline."
                )
                debug_audit = _build_debug_audit(
                    clean_stimulus, domains, best_global, _debug_all_candidates,
                    _debug_dejavu_killed, _debug_passes, "BASELINE_WIN"
                )
                return {
                    "stimulus": clean_stimulus,
                    "result": best_baseline_sentence,
                    "quality_score": 0.5,
                    "priorities_met": 0,
                    "anti_beige_score": 0.5,
                    "status": "BASELINE_WIN",
                    "depth": best_global.depth,
                    "pass": max_pass,
                    "disclosure_level": disclosure_level,
                    "trite_score": trite,
                    "curiosity_informed": bool(curiosity_ctx),
                    "domains_used": domains,
                    "domain": "parsed_baseline",
                    "limo_applied": False,
                    "precision_override": precision_override,
                    "debug_audit": debug_audit,
                }

        # ============================================================
        # STEP 9 (post-Kitchen): Re-check direct answer gate with Kitchen result
        # ============================================================
        if FOUNDATION_STEPS_AVAILABLE and stimulus_fingerprint:
            try:
                direct = direct_answer_gate(
                    stimulus_fingerprint=stimulus_fingerprint,
                    kitchen_result=kitchen_text,
                    parsed_baseline=parsed_baseline,
                    raw_baseline_text=baseline_text,
                )
                if direct and direct.strip() and direct != kitchen_text:
                    # Gate found a more direct answer than Kitchen produced
                    logger.info("STEP 9 (post): direct answer gate improved result")
                    debug_audit = _build_debug_audit(
                        clean_stimulus, domains, best_global, _debug_all_candidates,
                        _debug_dejavu_killed, _debug_passes, "DIRECT_ANSWER"
                    )
                    return {
                        "stimulus": clean_stimulus,
                        "result": direct,
                        "quality_score": best_global.overall_score,
                        "priorities_met": best_global.count_met,
                        "anti_beige_score": best_global.anti_beige_score,
                        "status": "DIRECT_ANSWER",
                        "depth": best_global.depth,
                        "pass": max_pass,
                        "disclosure_level": disclosure_level,
                        "trite_score": trite,
                        "curiosity_informed": bool(curiosity_ctx),
                        "domains_used": domains,
                        "domain": best_global.domain,
                        "limo_applied": LIMO_AVAILABLE and not precision_override,
                        "precision_override": precision_override,
                        "debug_audit": debug_audit,
                    }
            except Exception:
                pass

        # Kitchen cooked and survived Step 8. Serve it.
        debug_audit = _build_debug_audit(
            clean_stimulus, domains, best_global, _debug_all_candidates,
            _debug_dejavu_killed, _debug_passes, "GUESS"
        )

        return {
            "stimulus": clean_stimulus,
            "result": kitchen_text,
            "quality_score": best_global.overall_score,
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
            "limo_applied": LIMO_AVAILABLE and not precision_override,
            "precision_override": precision_override,
            "debug_audit": debug_audit,
        }

    # ==================================================================
    # STEP 10: Wild guess — Kitchen is empty but she's not silent
    # ==================================================================
    guess_text = wild_guess(
        stimulus=clean_stimulus,
        domains=domains,
        excavated=excavated,
        fingerprint=stimulus_fingerprint,
    )
    if guess_text and guess_text.strip():
        logger.info("STEP 10: wild_guess produced a response")
        guess_text = _apply_limo(guess_text, precision_override=precision_override)
        debug_audit = _build_debug_audit(
            clean_stimulus, domains, None, _debug_all_candidates,
            _debug_dejavu_killed, _debug_passes, "WILD_GUESS"
        )
        return {
            "stimulus": clean_stimulus,
            "result": guess_text,
            "quality_score": 0.2,
            "priorities_met": 0,
            "anti_beige_score": 0.3,
            "status": "WILD_GUESS",
            "depth": max_pass - 1,
            "pass": max_pass,
            "disclosure_level": disclosure_level,
            "trite_score": trite,
            "curiosity_informed": bool(curiosity_ctx),
            "domains_used": domains,
            "domain": "wild_guess",
            "limo_applied": LIMO_AVAILABLE and not precision_override,
            "precision_override": precision_override,
            "debug_audit": debug_audit,
        }

    # Absolute fallback — Kitchen AND wild_guess empty. Baseline parachute.
    clean_bl = _clean_baseline(baseline_text)
    if clean_bl:
        debug_audit = _build_debug_audit(
            clean_stimulus, domains, None, _debug_all_candidates,
            _debug_dejavu_killed, _debug_passes, "BASELINE_FALLBACK"
        )
        return {
            "stimulus": clean_stimulus,
            "result": clean_bl,
            "quality_score": 0.3,
            "priorities_met": 0,
            "anti_beige_score": 0.5,
            "status": "BASELINE_FALLBACK",
            "depth": 0,
            "pass": max_pass,
            "disclosure_level": disclosure_level,
            "trite_score": trite,
            "curiosity_informed": bool(curiosity_ctx),
            "domains_used": domains,
            "domain": "google_baseline",
            "limo_applied": False,
            "precision_override": precision_override,
            "debug_audit": debug_audit,
        }

    # True nothing. MISE_EN_PLACE.
    debug_audit = _build_debug_audit(
        clean_stimulus, domains, None, _debug_all_candidates,
        _debug_dejavu_killed, _debug_passes, "MISE_EN_PLACE"
    )
    return {
        "stimulus": clean_stimulus,
        "result": "",
        "quality_score": 0.0,
        "priorities_met": 0,
        "anti_beige_score": 0.0,
        "status": "MISE_EN_PLACE",
        "depth": max_pass - 1,
        "pass": max_pass,
        "disclosure_level": disclosure_level,
        "trite_score": trite,
        "curiosity_informed": bool(curiosity_ctx),
        "domains_used": domains,
        "domain": "",
        "limo_applied": False,
        "precision_override": precision_override,
        "debug_audit": debug_audit,
    }


def _build_debug_audit(
    stimulus: str,
    domains: List[str],
    winner: Optional[Interpretation],
    all_candidates: List[Dict],
    dejavu_killed: List[Dict],
    passes: List[Dict],
    status: str,
) -> Dict:
    """
    DEBUG MODE: She defends every response.
    This is her receipt. Her work shown. Her pick justified.
    """
    audit = {
        "stimulus": stimulus,
        "domains_detected": domains,
        "status": status,
        "passes": passes,
        "total_candidates": len(all_candidates),
        "dejavu_killed_count": len(dejavu_killed),
        "dejavu_killed": dejavu_killed[:5],
        "all_candidates": sorted(
            all_candidates,
            key=lambda x: x.get("overall_score", 0),
            reverse=True,
        )[:9],
    }

    if winner:
        audit["winner"] = {
            "text": winner.text,
            "domain": winner.domain,
            "overall_score": round(winner.overall_score, 4),
            "count_met": winner.count_met,
            "anti_beige": round(winner.anti_beige_score, 3),
        }
        reasons = []
        if winner.overall_score > 0:
            reasons.append(f"Scored {winner.overall_score:.4f} (highest surviving)")
        if winner.count_met > 0:
            reasons.append(f"Met {winner.count_met}/5 priorities")
        if winner.anti_beige_score > 0.5:
            reasons.append(f"Anti-beige {winner.anti_beige_score:.2f} (fresh)")
        if winner.domain:
            reasons.append(f"Domain: {winner.domain}")
        if not reasons:
            reasons.append("Last resort — all others worse or blocked")
        audit["defense"] = reasons
    else:
        audit["winner"] = None
        audit["defense"] = ["NO CANDIDATES SURVIVED. All gates rejected everything."]

    return audit
