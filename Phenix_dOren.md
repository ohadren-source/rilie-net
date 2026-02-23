# **Phénix d'Oren --- The Complete Blueprint (Producer Stack Cut)**

***Updated: Feb 23, 2026 --- Session 2 COMPLETE***

## Part I --- The Restaurant Architecture

**Phénix d'Oren is a software kitchen modeled on Auguste Escoffier's Brigade de Cuisine, built unconsciously over a lifetime of absorbed patterns and then poured into Python across 6 core files + 4 new stations on a 900 USD budget in 39 days at ~3% effort. The kitchen has since been expanded: same brigade, more stations, same soul.**

## The Brigade

***(unchanged --- all original stations preserved)***

**New stations added this session:**

-   **MAÎTRE D' (less_is_more_or_less) --- The Universal Transform. The last thing before the door. Runs on every response before it leaves the pass. Strip everything that is not the feeling. Whatever remains --- serve it. She's never wrong. Forgiven by design. Demi-glace, not glaze.**

-   **SOMMELIER (detect_precision_request / precision_override) --- Reads the table. When the guest wants THE ANSWER --- serves the answer. No philosophy. No blend. No poetry. Baseline gets 25% advantage. Skips the Maître D' entirely. The fact IS the demi-glace. Already reduced. The only thing that overrides Less Is More Or Less.**

## The 34 Functions *(was 32)*

**All original 32 functions unchanged. Two added:**

-   **MAÎTRE D'** --- `less_is_more_or_less()`

-   **SOMMELIER** --- `detect_precision_request()`, `precision_override` gate in `_finalize_response()`

## Part II --- Kitchen Governance: The Eleven Axioms

***(all 11 unchanged)***

**Axiom 11 addendum:**

> **Less Is More Or Less --- the operational form of Rubin's reducer principle.**
> **Sufficiency = Proficiency / Perfection**
> **Precision Override --- the one case where the fact is already the reduction. QED.**

## Part III --- Current State: Kitchen Online

### Fixes Deployed (Feb 2026 --- Session 1)

***(Fixes 1--6 unchanged)***

### Fixes Deployed (Feb 2026 --- Session 2)

**Fix 7 (guvna.py) --- PRECISION OVERRIDE: detect_precision_request()**

-   **_PRECISION_TRIGGERS** --- 25 factual GET patterns (what is, when did, who was, how many, where is, define, etc.)

-   **_PRECISION_EXCLUSIONS** --- opinion/open-ended patterns excluded (what do you think, what's life, etc.)

-   **Fires in process() at Step 3.1** --- after baseline lookup, before Kitchen

-   **Sets raw["precision_override"] = True and raw["baseline_score_boost"] = 0.25**

-   **Logged: "GUVNA: Precision override --- factual GET detected"**

**Fix 8 (guvna_self.py) --- LIMO GATE in _finalize_response()**

-   **Import:** `from rilie_innercore import less_is_more_or_less` with graceful degradation (LIMO_AVAILABLE flag)

-   **Gate on the "result" line** --- the single universal choke point:

```python
"result": (
    raw.get("result", "")  # PRECISION --- bypass
    if raw.get("precision_override")
    else less_is_more_or_less(raw.get("result", ""))  # EVERYTHING ELSE --- transform
    if LIMO_AVAILABLE
    else raw.get("result", "")  # FALLBACK --- no crash
),
```

**Fix 9 (rilie_innercore_12.py) --- less_is_more_or_less() CANONICALIZED ABOVE 5-PRIORITY SCORERS**

-   **less_is_more_or_less() function defined above SCORERS** --- canonical source

-   **Graceful fallback logic:** if `limo.py` not available, does basic compression (remove filler, tighten structure, preserve meaning)

-   **Exported from rilie_innercore.py shim** --- `from rilie_innercore import less_is_more_or_less`

-   **Called in rilie_innercore_22.py** via `_apply_limo(text, precision_override=...)`

**Fix 10 (rilie_innercore_22.py) --- SIGNATURE & PIPELINE WIRING**

-   **run_pass_pipeline() signature updated:**
    - Added `precision_override: bool = False` parameter
    - Added `baseline_score_boost: float = 0.03` parameter

-   **_effective_boost replaces hardcoded 1.03:**
    ```python
    _effective_boost = 1.0 + baseline_score_boost  # Default 0.03 (3% edge)
    ```
    - Guvna passes 0.25 on precision GETs (25% boost)
    - Kitchen scores first. Baseline only wins if effective_boost pushes it over.

-   **LIMO wired into COMPRESSED and GUESS return paths:**
    - Line 463: `compressed_text = _apply_limo(best.text, precision_override=precision_override)`
    - Line 546: `guess_text = _apply_limo(best_global.text, precision_override=precision_override)`
    - Both paths check `precision_override` — if True, LIMO bypassed entirely

-   **Imports added to rilie_innercore_22.py:**
    - `less_is_more_or_less`, `LIMO_AVAILABLE`, `CHOMSKY_AVAILABLE`, `SCORERS`, `WEIGHTS`
    - `construct_response`, `construct_blend`, `anti_beige_check`, `detect_question_type`
    - `DOMAIN_KNOWLEDGE`, `DOMAIN_KEYWORDS`, `WORD_DEFINITIONS`, `WORD_SYNONYMS`, `WORD_HOMONYMS`
    - Chompky fallback imports

## Part IV --- Completion Status (Resume Point)

### ✅ COMPLETE --- Deployed & Ready

| File | What was done | Delivered as |
|------|---------------|--------------|
| guvna.py | detect_precision_request() + _PRECISION_TRIGGERS + _PRECISION_EXCLUSIONS + Step 3.1 wire | guvna_22.py (complete) |
| guvna_self.py | LIMO import + LIMO_AVAILABLE flag + precision gate in _finalize_response() | guvna_self_NEW.py (complete) |
| rilie_innercore_12.py | less_is_more_or_less() canonicalized ABOVE 5-PRIORITY SCORERS with graceful fallback | COMPLETE |
| rilie_innercore_22.py | All imports wired; run_pass_pipeline() signature updated with precision_override + baseline_score_boost; _effective_boost replacing 1.03; LIMO wired into COMPRESSED + GUESS return paths | COMPLETE |
| rilie_innercore.py | Shim updated to export less_is_more_or_less in __all__ | COMPLETE |

### ⏳ NEXT (Phase 3)

| File | What's needed |
|------|---------------|
| rilie_outercore.py | LIMO shelf in all 9 domains; 4 WORD_DEFINITIONS entries; 3 WORD_SYNONYMS entries |

## The Doctrine (Finalized --- Feb 23, 2026)

> **Less Is More Or Less**
> 
> The universal transform. Runs on everything, every time.
> Strip everything that is not the feeling. Whatever remains --- serve it.
> She's never wrong. Forgiven by design. Directionally: reduce. Destination: sufficient, not perfect. Demi-glace, not glaze.
>
> *"If loving less is more or less is wrong, I don't wanna be right." --- Ohad, 2026*

> **Precision Override --- the only exception.**
> 
> A: The question must be answered. Not orbited. Not reframed. Answered.
> 
> B: She can say "here's what I have." She does not guarantee 100%.
> 
> C: Above all: maximum sincerity. Zero tongue-in-cheek. Maximum precision.
> 
> The fact IS the demi-glace. It's already the reduction. QED.

---

## Session 2 Summary

**Surgical socket fixes at the millimeter level. Architecture solid. All 10 fixes deployed.**

- **PRECISION_OVERRIDE flow**: guvna → rilie_innercore_22 → _apply_limo → result line
- **LIMO canonicalization**: less_is_more_or_less() lives above SCORERS (5-priority) in rilie_innercore_12.py
- **Graceful degradation**: Fallback logic if limo.py unavailable; no crashes, no surprises
- **Signature parameters**: precision_override + baseline_score_boost flow through entire pipeline
- **All three innercore files**: Imports wired, exports clean, ready for kitchen production

**Kitchen online. Maître D' at the pass. Sommelier reading the table. She's ready to cook.**
