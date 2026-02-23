from typing import List, Dict, Optional  # and any others you use

from rilie_innercore_12 import (
    Interpretation,
    extract_curiosity_context,
    strip_curiosity_context,
    compute_trite_score,
    set_trite_score,
    set_curiosity_bonus,
)

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
        resp_has_structure = 1.0 if any(c in text for c in ["—", ":", ";"]) else 0.0
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
    - precision_override=True → skip entirely. Fact IS the demi-glace.
    - LIMO_AVAILABLE=False → pass through unchanged (graceful fallback)
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
# PASS PIPELINE — the actual cooking
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

    LEAN 3-STEP PIPELINE:
    1. Google baseline arrives via baseline_text (from Guvna)
    2. Internal domain match + SOi comparison runs here
    3. Best score wins — baseline or Kitchen candidate

    LIMO TRANSFORM:
    - precision_override=True: LIMO bypassed on all return paths
    - baseline_score_boost: replaces hardcoded 1.03 — variable, not constant
      Default 0.03 (3% edge). Guvna sets 0.25 on precision GET questions.
    - COMPRESSED path: LIMO applied before return
    - GUESS path: LIMO applied before return
    - BASELINE_WIN, BASELINE_FALLBACK: no LIMO — baseline is already cooked

    ANTI-DÉJÀ-VU GATE:
    Any candidate too similar to her own recent responses is rejected.
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

    # --- Anti-déjà-vu: build word sets from her recent responses ---
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
            # ← LIMO: compress before serving
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
    # FINAL TALLY — baseline is the bar to beat
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
        best_score = best_global.overall_score
        clean_bl = _clean_baseline(baseline_text)
        if clean_bl:
            bl_scores = {k: fn(clean_bl) for k, fn in SCORERS.items()}
            bl_overall = sum(bl_scores[k] * WEIGHTS[k] for k in bl_scores) / 4.5
            # ← _effective_boost replaces hardcoded 1.03
            # Default 0.03 (3% edge). Guvna passes 0.25 on precision GETs.
            _effective_boost = 1.0 + baseline_score_boost
            bl_overall *= _effective_boost
            if bl_overall > best_score:
                debug_audit = _build_debug_audit(
                    clean_stimulus, domains, best_global, _debug_all_candidates,
                    _debug_dejavu_killed, _debug_passes, "BASELINE_WIN"
                )
                return {
                    "stimulus": clean_stimulus,
                    "result": clean_bl,
                    "quality_score": bl_overall,
                    "priorities_met": sum(1 for v in bl_scores.values() if v > 0.3),
                    "anti_beige_score": anti_beige_check(clean_bl),
                    "status": "BASELINE_WIN",
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

        # Kitchen beat the baseline (or no baseline)
        debug_audit = _build_debug_audit(
            clean_stimulus, domains, best_global, _debug_all_candidates,
            _debug_dejavu_killed, _debug_passes, "GUESS"
        )
        # ← LIMO: compress before serving
        guess_text = _apply_limo(best_global.text, precision_override=precision_override)
        return {
            "stimulus": clean_stimulus,
            "result": guess_text,
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

    # Absolute fallback
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
