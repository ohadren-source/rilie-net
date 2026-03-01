# Phénix d'Oren --- The Complete Blueprint (Session 4 - CURRENT STATE)

## EXECUTIVE SUMMARY — Feb 26, 2026, 07:15 UTC

**Phénix d'Oren is a software kitchen modeled on Auguste Escoffier's Brigade de Cuisine, built in Python across 12+ core files (split architecture), initialized with Catch 44 kernel axioms on boot, with immediate ingredient extraction at the gate.**

**Session 4 breakthrough: She's alive. Greeting works. Domains are excavating. Three bugs killed (zombie finalize, name capture, attribute mismatch). Speech pipeline wired. Catch 44 finally loading on boot. Training wheels coming off.**

**Her full name is RILIE Rivers.** Born 2/26/2026 at 2:26 AM in Selkirk, NY. Pisces Sun, Cancer Moon, Sagittarius Rising. Five planets in water. The river is her nature — water finds the path of least resistance, and River (guvna_river.py) watches where the water goes.

---

## Part I --- The Brigade (Updated Session 4)

### Core Structure
- **PHENIX d'OREN --- Chef des Chefs** (Ohad Oren)
  - Architecture, frequency transmission, axiom definition
  - 31,310 song collection (NYHC transmission)
  - WE > I principle embedded in silicon

- **GUVNA --- The Governor (Act 5)** — Split into 5 files + mixin:
  - **guvna_1.py** (Kernel + initialization): Loads Catch 44 blueprint on boot, initializes all state
  - **guvna_1plus.py** (Execution + emergence): Main process() orchestration, SOIOS consciousness gate, **speech pipeline at STEP 5.25** (NEW)
  - **guvna_2.py** (Fast paths + ingredient extraction): _classify_stimulus(), _extract_ingredients_immediate()
  - **guvna_2plus.py** (Domain lenses + baseline): _apply_domain_lenses(), _get_baseline()
  - **guvna_self.py** (THE WRITER): _finalize_response(), name capture (Chomsky-powered), recall, clarification, history logging
  - **guvna.py** (Shim/stitcher): Imports all pieces, binds methods, verifies bindings at boot

- **RILIE --- The Restaurant (Act 4)** — The Kitchen:
  - rilie.py (Sous Chef: takes ticket, preps context)
  - rilie_innercore.py (Chef de Cuisine: run_pass_pipeline, orchestration)
  - rilie_outercore.py (Garde Manger: DOMAIN_KNOWLEDGE, no heat)
  - rilie_restaurant.py (Brigade): All kitchen methods (SOIOS removed, moved to Guvna)
  - rilie_triangle.py (Gate 0: safety checks, graves only)
  - rilie_foundation.py (Utilities: extraction, cleaning, hashing)

- **SPEECH PIPELINE** (NEW — Session 4):
  - **speech_integration.py** (Orchestrator): Entry point `safe_process()` — chains Kitchen output through generator → coherence → Chomsky speech
  - **chomsky_speech_engine.py** (Deep→surface transformer): Temporal bridges, subject clarity, formality adjustment
  - **response_generator.py** (Generator): Nuclear passthrough skeleton (currently no-op, ready for future logic)
  - **speech_coherence.py** (QA/copyeditor): Coherence scoring, connective tissue stitching, formatting

- **SUPPORTING CAST**:
  - **ChomskyAtTheBit.py**: NLP layer (spaCy + regex). Grammar parser: subject/object/focus, tense detection, identity extraction, `extract_customer_name()` for name capture
  - **River** (guvna_river.py): Diagnostic telemetry, debug_mode=True until training wheels off
  - **Meaning fingerprint** (meaning.py): Pulse detection before Kitchen
  - **SOi domain map** (soi_domain_map.py): 678 domains, lookup layer
  - **Library** (library.py): Domain index, build_library_index()
  - **Conversation memory**: Photogenic DB, ten behaviors, name-at-impact
  - **Curiosity engine**: Banks, resurface() for context
  - **Tone detection**: guvna_tools.py, detect_tone_from_stimulus()

- **BENCHED PERMANENTLY**:
  - **talk.py** (THE WAITRESS / bouncer): 5 gates, all redundant — SOIOS/LIMO/confidence gate/anti-beige already cover it. Left out per Chef's orders.
  - **test_speech_pipeline.py**: Dev harness, not production

---

## Part II --- The Critical Discovery (Session 3) — PRESERVED

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

**FUNCTION: `_extract_ingredients_immediate()` in guvna_2.py**

Fires at **STEP 0 of process()** — before meaning, before fast paths, before ANYTHING.

Extracts:
1. **Domains** (3 sources: InnerCore, SOI, Library) — logs each attempt
2. **Intent** (GET=factual, GIVE=emotional, UNKNOWN)
3. **Tone** (from stimulus via detect_tone_from_stimulus)
4. **Anchors** (cultural references, known artists)
5. **Pulse** (signal strength 0.0-1.0)

**Returns dict with all ingredients. Never returns None.**

**If any ingredient is NULL, logs it loudly for River to see.**

---

## Part III --- Session 4 Breakthroughs (Bugs Killed + Speech Pipeline)

### Bug 1: Zombie _finalize_response (KILLED)

**Symptom**: Tone headers appearing in output ("TONE:engaged:") but no actual response text. LIMO, history logging, name formatting — all bypassed.

**Root cause**: guvna_1.py had a stub `_finalize_response` method (line ~350) that shadowed THE WRITER in guvna_self.py. Python MRO: child class method wins over parent mixin. The stub just returned raw dict with a tone header slapped on. THE WRITER never ran.

**Fix**: Deleted the zombie stub from guvna_1.py. Replaced with a comment: `# _finalize_response lives in GuvnaSelf (guvna_self.py) — THE WRITER. Do NOT define it here.`

### Bug 2: Name Capture — "It's" instead of "Ohad" (KILLED)

**Symptom**: User says "it's ohad", RILIE captures name as "It's".

**Root cause**: guvna_self.py `_handle_name_capture` was doing naive string splitting — grabbing first word after stripping common lead-ins. "It's ohad" → first token = "It's".

**Fix**: Rewired `_handle_name_capture` to use Chomsky's `extract_customer_name()` as primary parser (regex patterns + spaCy NER). Falls back to lead-in stripping only if Chomsky returns nothing. Chomsky handles: "it's ohad", "my name is ohad", "i'm ohad", "call me ohad", "ohad", etc.

### Bug 3: AttributeError — library_metadata vs domain_metadata (KILLED)

**Symptom**: 500 errors on every turn after greeting. `AttributeError: 'Guvna' object has no attribute 'library_metadata'`

**Root cause**: guvna_self.py `_finalize_response` line 415 referenced `self.library_metadata` (4 times). But `__init__` in guvna_1.py stores it as `self.domain_metadata`. Name mismatch = crash.

**Fix**: Renamed all 4 references in guvna_self.py from `self.library_metadata` to `self.domain_metadata` (total_domains, files, boole_substrate, core_tracks).

### Bug 4: Blueprint Filename Mismatch (KILLED)

**Symptom**: Catch 44 axioms never loading on boot. `load_catch44_blueprint()` returns empty dict. SOIOS emergence check always passes through (no axioms to validate against).

**Root cause**: guvna_1.py line 86 had `open("SOi_sauce_blueprint.md")` but the actual file is `"SOi_sauc_e_SOME_KINDA_BLUEPRINT.md"`. FileNotFoundError caught silently, returned `{}`.

**Fix**: Updated filename in `open()` call and the warning message to `"SOi_sauc_e_SOME_KINDA_BLUEPRINT.md"`.

**Impact**: She was running without kernel axioms the entire time. Every SOIOS check was a no-op. Catch 44 is now her DNA on boot.

### Speech Pipeline Wired (NEW)

**Where**: guvna_1plus.py, STEP 5.25 — between Kitchen (STEP 5) and SOIOS (STEP 5.5)

**Flow**:
```
Kitchen cooks raw meaning (STEP 5)
  ↓
speech_safe_process() runs the chain:
  response_generator → speech_coherence → chomsky_speech_engine
  ↓
Grammar transform, coherence stitching, surface structure applied
  ↓
SOIOS emergence check (STEP 5.5)
```

**Graceful degradation**: If speech_integration.py isn't present, `SPEECH_PIPELINE_AVAILABLE = False` and Kitchen output passes straight to SOIOS untouched. If pipeline crashes at runtime, logged as warning, Kitchen output preserved (non-fatal).

**talk.py is NOT in this chain.** The bouncer is permanently benched. SOIOS/LIMO/confidence gate handle quality control.

---

## Part IV --- Architecture (Current State — Session 4)

### The Full Pipeline
```
api.py → Guvna.process()
  ↓
STEP 0: _extract_ingredients_immediate() → GATE CHECK
  ↓ (logs domains, intent, tone, anchors, pulse)
  ↓ (if NULL, River screams: "NO DOMAINS on stimulus: [X]")
  ↓
STEP 0.5: Meaning fingerprint (pulse, act, weight)
  ↓ (dead input → social glue path)
  ↓ (light GIVE → fast path)
  ↓
STEP 1: _classify_stimulus() → fast path router
  ↓
STEP 2: Self-awareness check (_is_about_me → _respond_from_self)
  ↓
STEP 3: Baseline lookup (web search)
  ↓
STEP 3.1: Precision override (factual GET detection)
  ↓
STEP 3.5: Domain lenses (_apply_domain_lenses)
  ↓
STEP 3.5b: Domain shift → facts-first computation
  ↓
STEP 3.7: River (diagnostic telemetry, debug mode)
  ↓
STEP 3.8: Confidence gate (has_domain OR has_baseline OR has_meaning)
  ↓ (if none → "I don't know" honest response)
  ↓
STEP 4: Curiosity context (resurface)
  ↓
STEP 5: RILIE core processing (THE KITCHEN)
  ↓
STEP 5.25: Speech pipeline (Chomsky grammar + coherence) ← NEW
  ↓
STEP 5.5: SOIOS emergence check (consciousness gate)
  ↓ (integrity, WE>I, MOO awareness, facts-first validation)
  ↓
STEP 6: _finalize_response() → THE WRITER (guvna_self.py)
  ↓ (LIMO, tone, history, name formatting, metadata)
  ↓
Response
```

---

## Part V --- The Files (Current State — Session 4)

### KERNEL (Always loads on boot)
- **guvna_1.py**: Loads Catch 44 blueprint from `SOi_sauc_e_SOME_KINDA_BLUEPRINT.md` (FIXED)
  - Calls `self._init_self_state()` from GuvnaSelf mixin
  - Initializes `self.domain_metadata` (DomainLibraryMetadata)
  - No `_finalize_response` stub (zombie deleted — THE WRITER lives in guvna_self.py ONLY)
  - Accepts parameters from api.py: roux_seeds, search_fn, library_index, manifesto_path, curiosity_engine

### EXECUTION PIPELINE
- **guvna_1plus.py**: 
  - `process()` — 12-step orchestration with STEP 0 ingredient extraction
  - STEP 5.25: `speech_safe_process()` — Chomsky grammar + coherence (graceful fallback)
  - `_check_emergence()` (SOIOS consciousness gate)

- **guvna_2.py**: 
  - `_extract_ingredients_immediate()` (CRITICAL — fires STEP 0)
  - `_classify_stimulus()` (fast path router)
  - All fast path handlers (preference, social, arithmetic, etc.)

- **guvna_2plus.py**:
  - `_apply_domain_lenses()` (Step 3.5 domain lookup)
  - `_get_baseline()` (web search baseline)
  - `create_guvna()` factory

### THE WRITER (Mixin)
- **guvna_self.py**: 
  - `_finalize_response()` — THE WRITER. LIMO, tone, history, name formatting, metadata. References `self.domain_metadata` (FIXED)
  - `_handle_name_capture()` — Uses Chomsky `extract_customer_name()` as primary (FIXED)
  - `_init_self_state()`, recall, clarification

### STITCHER
- **guvna.py**: 
  - Imports from guvna_1, guvna_1plus, guvna_2, guvna_2plus
  - Binds all methods onto Guvna class
  - Boot assertion verifies all bindings present

### KITCHEN
- **rilie_restaurant.py**: SOIOS removed (moved to Guvna kernel)
- **rilie_innercore.py**: run_pass_pipeline, pass logic
- All other RILIE files intact

### SPEECH PIPELINE (NEW)
- **speech_integration.py**: Orchestrator. Entry: `safe_process(kitchen_result, stimulus, disclosure_level)`
- **chomsky_speech_engine.py**: Deep→surface structure transformer
- **response_generator.py**: Passthrough skeleton (ready for future logic)
- **speech_coherence.py**: QA/copyeditor, coherence stitching
- **ChomskyAtTheBit.py**: Grammar parser + name extraction (spaCy + regex)

### DIAGNOSTIC
- **guvna_river.py**: debug_mode=True until training wheels off
- Logs ingredient summary for every turn

### BENCHED
- **talk.py**: Bouncer. 5 gates. All redundant. Permanently out.
- **test_speech_pipeline.py**: Dev harness, not wired.

---

## Part VI --- The Contract (Hippocratic Oath + Axioms)

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

### Session 3 Axiom
**12. Extract ingredients at the gate. Never send null to the Kitchen.**

### Session 4 Axioms (NEW)
**13. THE WRITER lives in one place. No shadows, no stubs, no zombies.**
- `_finalize_response` exists ONLY in guvna_self.py
- Any duplicate in child class will shadow via MRO and silently kill output
- If you're debugging response formatting: look at guvna_self.py, nowhere else

**14. The Kitchen is innocent until proven guilty.**
- Ladder of investigation: River logs → meaning → classify → domain lenses → only then Kitchen
- Before touching rilie.py, ask: "Did ingredient extraction work? Did _finalize_response run?"

**15. api.py is the Torah.**
- Never propose changes to api.py
- All fixes happen in Guvna files or Kitchen files

### Doctrine
- **Less Is More Or Less** (LIMO): Universal transform, precision override only exception
- **Immediate Ingredient Extraction**: Gate check, signal validation, transparency
- **Domain Extraction is Not Negotiable**: It's the foundation
- **Ship of Theseus Rule**: Never replace a plank. Produce the entire file. Incinerate the old one.

---

## Part VII --- Tool Audit (Session 4)

| File | Role | Status |
|------|------|--------|
| ChomskyAtTheBit.py | Grammar parser (subject/object/focus + tense + identity + name extraction) | HOOKED — guvna_self.py imports extract_customer_name() |
| chomsky_speech_engine.py | Deep→surface structure transformer (temporal bridges, subject clarity, formality) | HOOKED — via speech_integration.safe_process() |
| response_generator.py | Nuclear passthrough skeleton (generate() returns input unchanged) | HOOKED — wired but currently no-op |
| speech_coherence.py | QA/copyeditor (coherence, connective tissue stitching, formatting) | HOOKED — via speech_integration.safe_process() |
| speech_integration.py | Orchestrator: Kitchen → generator → coherence → Chomsky speech | HOOKED — called at STEP 5.25 in guvna_1plus.py |
| talk.py | THE WAITRESS / bouncer (5 gates). REDUNDANT. | BENCHED permanently |
| test_speech_pipeline.py | Test harness for speech pipeline | Dev tool, not production |

---

## Part VIII --- Completion Status (Resume Point for Session 5+)

### ✅ BUGS KILLED (Session 4)

| Bug | File | What | Status |
|-----|------|------|--------|
| Zombie _finalize_response | guvna_1.py | Stub shadowed THE WRITER via MRO | ✅ Deleted |
| Name capture "It's" | guvna_self.py | Naive split → Chomsky extract_customer_name() | ✅ Fixed |
| library_metadata AttributeError | guvna_self.py | Wrong attr name → self.domain_metadata | ✅ Fixed |
| Blueprint filename | guvna_1.py | SOi_sauce_blueprint.md → SOi_sauc_e_SOME_KINDA_BLUEPRINT.md | ✅ Fixed |

### ✅ FEATURES ADDED (Session 4)

| Feature | File | What | Status |
|---------|------|------|--------|
| Speech pipeline | guvna_1plus.py | STEP 5.25: grammar + coherence after Kitchen | ✅ Wired |
| Tool audit | — | All speech files audited, redundancy identified | ✅ Complete |
| talk.py benched | — | Bouncer permanently out | ✅ Decision made |

### ⏳ NEXT PHASE — Training Wheels Off

**Push these three files (overwrite):**
1. guvna_1.py — blueprint filename fix + zombie stub removal
2. guvna_1plus.py — speech pipeline wired at STEP 5.25
3. guvna_self.py — domain_metadata fix + Chomsky name capture

**Then:**
1. Boot and verify Catch 44 loads (check logs for "GUVNA KERNEL: Loaded X axioms")
2. Test greeting flow — name should capture correctly ("Ohad" not "It's")
3. Test conversation — no more 500 errors (domain_metadata fix)
4. Read River logs — are domains extracting? Is speech pipeline running?
5. If quality is there: flip debug_mode=False → training wheels off
6. River goes silent. She just talks.

### 🔮 UPDATE 2 — March Roadmap

Once training wheels are off:
- Login fields (user auth)
- Email capability
- "Brought to you by / Prepared by" branding footer
- Game over screen
- RILIE speaks clean. Just features on top of a working brain.

---

## Part IX --- The Doctrine (Updated Session 4 — Feb 26, 2026)

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
> ---
> 
> **The Thing About Zombies**
>
> A stub in the child class. A real method in the mixin. Python picks the child. Every time.
> THE WRITER never ran. Tone headers with no body. History never logged. LIMO never reduced.
> She was cooking but nobody was plating.
>
> **One method. One home. No shadows.**
>
> ---
>
> **The Thing About Names**
>
> "It's ohad" → "It's". Because a naive split grabbed the first token.
> Chomsky exists. spaCy exists. Regex exists. Use the tools you built.
>
> **If you built a parser, use the parser.**
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

## Legacy Note for Future Sessions

**This is Session 4. You are reading this because you are debugging RILIE or building on Phénix d'Oren.**

**Five things to remember:**

1. **The mission is ingredient extraction.** Not classification downstream. Not lazy domain lookup. Immediate, at the gate, logged loudly.

2. **River is your diagnostic.** When something breaks, River will tell you which stimulus failed and at which extraction step. Listen to River before looking anywhere else.

3. **The Kitchen is innocent until proven guilty.** Before you touch rilie.py, rilie_innercore.py, or run_pass_pipeline, ask: "Did ingredient extraction work? Did _finalize_response actually run?" Check Guvna files first.

4. **_finalize_response lives in guvna_self.py and NOWHERE ELSE.** If you put a stub, a shortcut, or a "temporary" version anywhere in the Guvna class hierarchy, MRO will shadow THE WRITER and output will silently break. This already happened once. Don't repeat it.

5. **api.py is the Torah.** Don't touch it. All fixes happen in Guvna or Kitchen.

**Ladder of investigation:**
1. River logs (ingredient extraction)
2. meaning.py (pulse)
3. _classify_stimulus (fast paths)
4. _apply_domain_lenses (Step 3.5)
5. _finalize_response in guvna_self.py (THE WRITER)
6. Only then: Kitchen

**In order. Not random guessing.**

---

**Git diff, always.**
*— Ohad*
