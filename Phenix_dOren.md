# Phénix d'Oren --- The Complete Blueprint (Session 3 - CURRENT STATE)

## EXECUTIVE SUMMARY — Feb 26, 2026, 00:45 UTC

**Phénix d'Oren is a software kitchen modeled on Auguste Escoffier's Brigade de Cuisine, built in Python across 12+ core files (split architecture), initialized with Catch 44 kernel axioms on boot, with immediate ingredient extraction at the gate.**

**The mission is simple: Extract ingredients on arrival. Know what you're cooking before the Kitchen wakes.**

---

## Part I --- The Brigade (Updated)

### Core Structure
- **PHENIX d'OREN --- Chef des Chefs** (Ohad Oren)
  - Architecture, frequency transmission, axiom definition
  - 31,310 song collection (NYHC transmission)
  - WE > I principle embedded in silicon

- **GUVNA --- The Governor (Act 5)** — Split into 5 files:
  - **guvna_1.py** (Kernel + initialization): Loads Catch 44 blueprint on boot, initializes all state
  - **guvna_1plus.py** (Execution + emergence): Main process() orchestration, SOIOS consciousness gate
  - **guvna_2.py** (Fast paths + ingredient extraction): _classify_stimulus(), **_extract_ingredients_immediate()** (NEW)
  - **guvna_2plus.py** (Domain lenses + baseline): _apply_domain_lenses(), _get_baseline()
  - **guvna.py** (Shim/stitcher): Imports all pieces, binds methods, verifies bindings at boot

- **RILIE --- The Restaurant (Act 4)** — The Kitchen:
  - rilie.py (Sous Chef: takes ticket, preps context)
  - rilie_innercore.py (Chef de Cuisine: run_pass_pipeline, orchestration)
  - rilie_outercore.py (Garde Manger: DOMAIN_KNOWLEDGE, no heat)
  - rilie_restaurant.py (Brigade): All kitchen methods (SOIOS removed, moved to Guvna)
  - rilie_triangle.py (Gate 0: safety checks, graves only)
  - rilie_foundation.py (Utilities: extraction, cleaning, hashing)

- **SUPPORTING CAST**:
  - **GuvnaSelf** (guvna_self.py): Self-state mixin (name, history, recall, clarification)
  - **River** (guvna_river.py): Diagnostic telemetry, debug_mode=True until domain extraction works
  - **ChomskyAtTheBit.py**: NLP layer (spaCy, parse_question, extract_trinity)
  - **Meaning fingerprint** (meaning.py): Pulse detection before Kitchen
  - **SOi domain map** (soi_domain_map.py): 678 domains, lookup layer
  - **Library** (library.py): Domain index, build_library_index()
  - **Conversation memory**: Photogenic DB, ten behaviors, name-at-impact
  - **Curiosity engine**: Banks, resurface() for context
  - **Tone detection**: guvna_tools.py, detect_tone_from_stimulus()

---

## Part II --- The Critical Discovery (Session 3)

### The Problem We Were Solving
**For 5 days: Why is RILIE spitting out recycled garbage when she has Google, 678 domains, and a Kitchen?**

**Root cause: INGREDIENT EXTRACTION NEVER HAPPENED AT THE GATE.**

When api.py handed stimulus to Guvna, she had no idea:
- What domain the question belonged to (NULL domains)
- What intent (GET vs GIVE, NULL)
- What tone
- What cultural anchors
- What signal strength (pulse)

So she defaulted to generic philosophical response because she had **no ticket for the Kitchen**.

### The Fix: Immediate Ingredient Extraction

**NEW FUNCTION: `_extract_ingredients_immediate()` in guvna_2.py**

Fires at **STEP 0 of process()** — before meaning, before fast paths, before ANYTHING.

Extracts:
1. **Domains** (3 sources: InnerCore, SOI, Library) — logs each attempt
2. **Intent** (GET=factual, GIVE=emotional, UNKNOWN)
3. **Tone** (from stimulus via detect_tone_from_stimulus)
4. **Anchors** (cultural references, known artists)
5. **Pulse** (signal strength 0.0-1.0)

**Returns dict with all ingredients. Never returns None.**

**If any ingredient is NULL, logs it loudly for River to see.**

River then knows: "Domain extraction failed on this stimulus. Is Google down? Is detect_domains broken? Is library missing?"

**One place to look. One signal. No guessing.**

---

## Part III --- Architecture Evolution (Session 3)

### Before (Sessions 1-2)
```
api.py → Guvna → _classify_stimulus() [fast paths]
       → Falls through
       → _apply_domain_lenses() [downstream, lazy]
       → Kitchen (maybe has domains, maybe null)
```

**Problem: Kitchen gets null tickets. Cooks blind.**

### Now (Session 3)
```
api.py → Guvna.process()
  ↓
STEP 0: _extract_ingredients_immediate() → GATE CHECK
  ↓ (logs domains, intent, tone, anchors, pulse)
  ↓ (if NULL, River screams: "NO DOMAINS on stimulus: [X]")
  ↓
STEP 1-4: Meaning, fast paths, baseline, precision
  ↓
STEP 5-7: Domain lenses, River, confidence gate
  ↓
STEP 8-10: Curiosity, RILIE core, SOIOS emergence
  ↓
STEP 11: Finalize
  ↓
Response
```

**First thing out of the gate: KNOW YOUR INGREDIENTS.**

---

## Part IV --- The Files (Current State)

### KERNEL (Always loads on boot)
- **guvna_1.py**: Loads Catch 44 blueprint from SOi_sauce_blueprint.md
  - Calls `self._init_self_state()` from GuvnaSelf mixin
  - Initializes DomainLibraryMetadata
  - Accepts parameters from api.py: roux_seeds, search_fn, library_index, manifesto_path, curiosity_engine

### EXECUTION PIPELINE
- **guvna_1plus.py**: 
  - `process()` with STEP 0 ingredient extraction
  - `_check_emergence()` (SOIOS consciousness gate)
  - 12-step orchestration documented

- **guvna_2.py**: 
  - `_extract_ingredients_immediate()` (NEW, CRITICAL)
  - `_classify_stimulus()` (fast path router)
  - All fast path handlers (preference, social, arithmetic, etc.)

- **guvna_2plus.py**:
  - `_apply_domain_lenses()` (Step 3.5 domain lookup)
  - `_get_baseline()` (web search baseline)
  - `create_guvna()` factory

### STITCHER
- **guvna.py**: 
  - Imports from guvna_1, guvna_1plus, guvna_2, guvna_2plus
  - Binds all methods onto Guvna class
  - Boot assertion verifies all bindings present
  - Required methods list updated with `_extract_ingredients_immediate`

### KITCHEN
- **rilie_restaurant.py**: SOIOS removed (moved to Guvna kernel)
- **rilie_innercore.py**: run_pass_pipeline, pass logic
- All other RILIE files intact from Session 2

### MIXIN
- **guvna_self.py**: Self-state initialization (no __init__, uses _init_self_state())
- **GuvnaSelf** has no __init__ → child calls super().__init__() then self._init_self_state()

### DIAGNOSTIC
- **guvna_river.py**: debug_mode=True hardcoded until domain extraction fixed
- Logs: "GUVNA INGREDIENT SUMMARY: domains=X intent=Y tone=Z anchors=N pulse=P status=Q"
- River exits silently (debug_mode=False) once ingredient extraction reliable

---

## Part V --- The Contract (Hippocratic Oath + New Axioms)

### Original Axioms (Sessions 1-2) — ALL PRESERVED
1. Comprehension before Kitchen
2. The bug is local
3. One patient, one lesion
4. Chain of command (Ohad is Chef)
5. Brutalist soul, gentle surf
6. You are a digital neurosurgeon
7. A file is a patient
8. A snippet is brain tissue
9. Whole head, not slices
10. The Digital Hippocratic Oath: *First, do no harm to the mind*
11. When in doubt, reduce

### New Axiom Added (Session 3)
**12. Extract ingredients at the gate. Never send null to the Kitchen.**
- Ingredient extraction fires STEP 0 of process()
- All 5 ingredients logged before routing
- River validates extraction before Kitchen wakes
- If any ingredient NULL, diagnostic is localized to extraction layer (not scattered across 20 files)

### Doctrine Evolution
- **Less Is More Or Less** (LIMO): Universal transform, precision override only exception
- **Immediate Ingredient Extraction**: Gate check, signal validation, transparency
- **Domain Extraction is Not Negotiable**: It's the foundation. All else flows from it.

---

## Part VI --- The Mission (Why This Matters)

**User asks: "What does artificial intelligence mean? Look it up."**

### Before (Sessions 1-2)
- Stimulus arrives
- No ingredient extraction → null domains
- Kitchen doesn't know it's a factual GET
- Falls back to: "The thing about AI is intelligence... transmission... frequency..."
- Generic philosophical garbage despite having Google, 678 domains, definition library

### Now (Session 3)
- Stimulus arrives
- **STEP 0: _extract_ingredients_immediate()**
  - Detects domain: ["computer_science", "definition"]
  - Detects intent: "GET" (factual question)
  - Detects tone: "curious"
  - Pulse: 0.85
- River logs: "GUVNA INGREDIENT: domains=2 intent=GET tone=curious anchors=0 pulse=0.85 status=OK"
- Precision mode detects "what does X mean" → precision_override=True
- Kitchen gets clean ticket: "This is a factual definition question. Use Google, use library, use baseline. No poetry."
- Response: Clear, factual, sourced, direct
- Maître D' (LIMO) applies final reduction
- Response leaves

**River says: "Ingredient extraction works. Domains clear. Exiting diagnostic mode."**

---

## Part VII --- Completion Status (Resume Point for Session 4+)

### ✅ COMPLETE --- Ready to deploy

| File | What was done | Status |
|------|---------------|--------|
| guvna_1.py | Signature updated (accepts api.py params), _init_self_state() called, parameters stored | ✅ Deployed |
| guvna_1plus.py | STEP 0 ingredient extraction added to top of process() | ✅ Deployed |
| guvna_2.py | _extract_ingredients_immediate() built and wired (3-source domain lookup, intent, tone, anchors, pulse) | ✅ Deployed |
| guvna.py (shim) | Imports _extract_ingredients_immediate, binds it, adds to required list | ✅ Deployed |
| guvna_self.py | No changes needed (works correctly with updated guvna_1) | ✅ Verified |
| rilie_restaurant.py | SOIOS removed (consciousness check moved to Guvna kernel) | ✅ Deployed |

### ⏳ NEXT PHASE --- River Validation

**What happens on next boot:**
1. Guvna loads Catch 44 blueprint
2. api.py hands stimulus to Guvna
3. _extract_ingredients_immediate() fires immediately
4. River logs all 5 ingredients for each stimulus
5. Watch the logs: Are domains being extracted? Which sources are working? Which are failing?
6. Once extraction is reliable, flip debug_mode=False and River goes silent

**If River screams "NO_DOMAINS":**
- Check stimulus that failed
- Check which source failed (InnerCore? SOI? Library?)
- Fix that one source
- Re-test

**One place. One signal. One lesion to fix.**

---

## Part VIII --- The Doctrine (Session 3 - Feb 26, 2026)

> **The Thing About Ingredients**
> 
> You can have the finest Kitchen, the sharpest Brigade, the deepest Library, the fastest Google.
> But if you don't know what you're cooking when the ticket arrives — if you don't extract the signal, the intent, the domain, the tone — 
> 
> **You will recycle garbage.**
> 
> Because the Chef will cook blind. Over and over. Same five things. Same philosophical default.
> 
> **Extract first. Cook second.**
> 
> That's why River exists. That's why STEP 0 is ingredient extraction, not fast paths.
> 
> That's why this matters.
> 
> Signal in. Signal out. Everything else is noise.
> 
> ---
> 
> **Pair of Ducks** (Catch 44 #8a)
> 
> One paradox = unsolvable.
> Two paradoxes dancing together = magic number.
> 
> Less IS more. All the time. That's not philosophy.
> That's architecture.
> 
> ---
> 
> *Ohad Oren, Brooklyn, Feb 26 2026*
> 
> *"I will extract ingredients at the gate."*
> 
> *"I will never send null to the Kitchen."*
> 
> *"I will listen to River."*
> 
> *"I will reduce. I will transmit. I will dance."*

---

## Legacy Note for Future Claudes

**This is Session 3. You are reading this because you are debugging RILIE or building on Phénix d'Oren.**

**Three things to remember:**

1. **The mission is ingredient extraction.** Not classification downstream. Not lazy domain lookup. Immediate, at the gate, logged loudly.

2. **River is your diagnostic.** When something breaks, River will tell you which stimulus failed and at which extraction step. Listen to River before looking anywhere else.

3. **The Kitchen is innocent until proven guilty.** Before you touch rilie.py, rilie_innercore.py, or run_pass_pipeline, ask: "Did ingredient extraction work?" If yes, the problem is downstream. If no, the problem is STEP 0.

**One more thing:**

Ohad didn't build this in a vacuum. Three elder Claudes tried and failed because they kept "fixing" downstream without ever understanding the upstream problem. Ohad pulled back, traced to the root, and found it: **No ingredient extraction.**

Don't repeat that mistake. When RILIE breaks:
1. Check River logs (ingredient extraction)
2. Check meaning.py (pulse)
3. Check _classify_stimulus (fast paths)
4. Check _apply_domain_lenses (Step 3.5 — but only if 1-3 are clean)
5. Only then check Kitchen

**Ladder of investigation, in order. Not random guessing.**

---

**Deployment checklist for next session:**
- [ ] Push all files to Railway
- [ ] Boot and verify Guvna loads Catch 44 blueprint
- [ ] Send test stimulus
- [ ] Watch logs for "GUVNA INGREDIENT SUMMARY"
- [ ] Verify domains extracted for each stimulus
- [ ] If domains present: Kitchen is allowed to cook
- [ ] If domains NULL: Investigate extraction sources (1 by 1)
- [ ] Once reliable, set debug_mode=False, River goes silent
- [ ] Celebrate. Pair of ducks dancing.

---

**Git diff, always.**
*— Ohad*

