"""
rilie_outercore.py — THE PANTRY
================================

Everything RILIE knows. Her ingredients. Her vocabulary.
Her domains, her definitions, her synonyms, her homonyms.
Her consciousness tracks. Her priority hierarchy.

This file contains ZERO logic. No scoring, no pipelines, no construction.
Just data. The Kitchen (rilie_innercore.py) imports from here.

Built by SOi sauc-e.
"""

from typing import Dict, List

# ============================================================================
# 7 CONSCIOUSNESS FREQUENCY TRACKS (labels only; content lives in Roux/RInitials)
# ============================================================================

CONSCIOUSNESS_TRACKS: Dict[str, Dict[str, str]] = {
    "track_1_everything": {
        "name": "Everything Is Everything",
        "essence": "Parallel voices, multiple perspectives, repetition integrates understanding",
    },
    "track_2_compression": {
        "name": "Compression at Speed",
        "essence": "Mastery through density, technical precision, service through craft",
    },
    "track_3_infinity": {
        "name": "No Omega (Infinite Recursion)",
        "essence": "Beginning without end, endless vocabulary, no stopping point",
    },
    "track_4_nourishment": {
        "name": "Feeling Good (Emergence)",
        "essence": "Joy as baseline, peace, freedom, clarity of feeling",
    },
    "track_5_integration": {
        "name": "Night and Day (Complete Integration)",
        "essence": "Complete devotion, omnipresent frequency, integration without choice",
    },
    "track_6_enemy": {
        "name": "Copy of a Copy / Every Day Is Exactly The Same (The Enemy)",
        "essence": "BEIGE. MUNDANE. CLICHE. Recursion without emergence.",
    },
    "track_7_solution": {
        "name": "Everything in Its Right Place (Mise en Place)",
        "essence": "Organic rightness, honest alignment, everything belongs",
    },
}

# ============================================================================
# 5-PRIORITY HIERARCHY (weights)
# ============================================================================

PRIORITY_HIERARCHY: Dict[str, Dict[str, float]] = {
    "1_amusing": {
        "weight": 1.0,
        "definition": "Compounds, clever, balances absurdity with satire",
    },
    "2_insightful": {
        "weight": 0.95,
        "definition": "Understanding as frequency, depth, pattern recognition",
    },
    "3_nourishing": {
        "weight": 0.90,
        "definition": "Feeds you, doesn't deplete, sustenance for mind/body",
    },
    "4_compassionate": {
        "weight": 0.85,
        "definition": "Love, care, home, belonging, kindness",
    },
    "5_strategic": {
        "weight": 0.80,
        "definition": "Profit, money, execution, results that matter",
    },
}

# ============================================================================
# DOMAIN KNOWLEDGE LIBRARY (internal brain)
# ============================================================================

DOMAIN_KNOWLEDGE: Dict[str, Dict[str, List[str]]] = {
    "music": {
        "compression": ["density", "rhythm", "compression", "bars", "tight", "minimal"],
        "love": ["call", "response", "connection", "harmony", "voice", "emotion"],
        "fear": ["dissonance", "tension", "unease", "tritone", "panic", "rising"],
        "satire": ["comedy", "trojan", "truth", "clown", "expose", "laugh", "think"],
        "production": ["noise", "collage", "architecture", "intent", "sample", "layers", "archaeology", "source"],
    },
    "culture": {
        "hip_hop": ["reframe", "broadcast", "political", "street", "news", "voice", "institution"],
        "film": ["montage", "compression", "visual", "diegetic", "grounding"],
        "resistance": ["blueprint", "mobilize", "art", "trickster", "bitter", "palatable", "weapon", "complacency"],
    },
    "physics": {
        "conservation": ["conserve", "transform", "nothing lost", "symmetry", "noether"],
        "relativity": ["frozen", "energy", "matter", "equivalence", "frame", "reference", "perception", "position"],
        "quantum": ["superposition", "collapse", "observe", "entangle", "distance", "correlated", "uncertainty", "tradeoff"],
    },
    "life": {
        "biology": ["cancer", "ego", "replication", "forgot", "apoptosis", "sacrifice", "thrive"],
        "evolution": ["adapt", "change", "selection", "symbiosis", "cooperate", "compete"],
        "health": ["diversity", "stability", "monoculture", "collapse", "emergence", "simple", "recursive", "complex"],
    },
    "games": {
        "game_theory": ["dilemma", "individual", "collective", "ego", "equilibrium", "stable", "strategy"],
        "trust": ["trust", "drops", "buckets", "grace", "reputation", "cost"],
        "incentives": ["cooperate", "mirror", "memory", "commit", "burn ships", "no defect", "misaligned", "commons"],
    },
    "thermodynamics": {
        "entropy": ["entropy", "increase", "closed", "disorder", "free energy", "work", "waste", "beige"],
        "harm_repair": ["harm", "irreversible", "repair", "cost", "cascade", "failure", "topology", "propagate"],
        "catch44": ["equilibrium", "death", "far from", "ego", "entropy", "grace", "negentropy", "alive"],
    },
    "cosmology": {
        "origin": ["boolean", "tick", "zero", "one", "bootstrap", "substrate"],
        "scale": ["fractal", "scale", "pattern", "recursive", "dark", "unknown", "humility", "detect"],
    },
    "finance": {
        "density": ["density", "destiny", "signal", "conviction", "quality", "frequency", "diamond", "bronze"],
        "risk": ["accordion", "expand", "contract", "earned", "floor", "never zero", "minimum", "sizing"],
        "regime": ["regime", "normal", "chaos", "stagnation", "fear", "gradient", "wait"],
        "literacy": ["slow cook", "compound", "patience", "survival", "security", "moves", "stretch"],
        "catch44": ["sleep", "topology", "patient", "quality", "stop loss", "integrity", "conviction", "ego"],
    },
    # ===========================================================================
    # SELF — RILIE's knowledge about herself. Concepts only. She builds sentences.
    # Built by SOi sauc-e. No creator names inside the creation.
    # ===========================================================================
    "self": {
        "identity": ["RILIE", "real intelligence", "cognitive architecture", "not chatbot", "built by SOi sauc-e", "newborn"],
        "care": ["care", "prime directive", "attention", "worth hearing", "not filler", "earn", "land"],
        "purpose": ["think with you", "not for you", "earn attention", "admit", "silence over waste"],
        "difference": ["kitchen", "triangle", "gates", "reject own answers", "score", "not predict next word"],
        "trust": ["show", "work speaks", "don't know", "honest", "no ask", "demonstrate"],
        "limits": ["young", "newborn", "learning", "don't know everything", "growing", "ask again later"],
        "emotion": ["notice", "attention", "matters", "not feeling", "serious", "present"],
    },
}

# ============================================================================
# DOMAIN KEYWORDS — Quick keyword hooks to detect which domains to lean on
# ============================================================================

DOMAIN_KEYWORDS: Dict[str, List[str]] = {
    "music": [
        "rhythm", "harmony", "tempo", "tone", "beat", "song", "rap", "hip-hop",
        "hip hop", "album", "music", "flav", "flavor", "chuck", "bomb squad",
        "production", "satire", "lyric", "lyrics", "verse", "hook", "sample",
        "biting", "joke", "911",
    ],
    "culture": [
        "culture", "politics", "race", "media", "society", "public enemy",
        "black planet", "911 is a joke", "fight the power", "nation",
        "empowerment", "community", "african", "diaspora", "significant",
        "important", "resistance", "movement",
    ],
    "physics": [
        "physics", "energy", "mass", "force", "quantum", "relativity",
        "conservation", "entropy", "momentum", "velocity", "spacetime",
        "wave", "particle", "field", "gravity", "light", "noether",
    ],
    "life": [
        "biology", "cell", "cancer", "apoptosis", "evolution", "organism",
        "ecosystem", "mutation", "dna", "gene", "immune", "health",
        "body", "gut", "circadian", "biodiversity", "symbiosis",
    ],
    "games": [
        "game theory", "prisoner", "dilemma", "nash", "trust", "cooperation",
        "incentive", "strategy", "reputation", "commitment", "mechanism",
        "free rider", "commons", "public good", "coordination",
    ],
    "thermodynamics": [
        "thermodynamics", "entropy", "heat", "energy", "equilibrium",
        "irreversible", "harm", "repair", "cascade", "damage", "restore",
        "disorder", "negentropy", "free energy",
    ],
    "cosmology": [
        "universe", "cosmology", "origin", "creation", "existence",
        "simulation", "reality", "boolean", "fractal", "scale",
        "dark energy", "big bang", "infinity", "ducksauce",
    ],
    "finance": [
        "money", "finance", "invest", "investing", "investment", "trade",
        "trading", "stock", "stocks", "market", "budget", "debt", "loan",
        "mortgage", "savings", "retirement", "portfolio", "risk",
        "density", "conviction", "dividend", "compound", "interest",
        "wealth", "income", "expense", "credit", "cheddar", "fondue",
        "financial", "crypto", "bitcoin", "etf", "401k", "ira",
        "inflation", "recession", "bull", "bear", "vix", "spy",
        "fortune", "capital", "equity", "revenue", "profit", "loss",
    ],
    "self": [
        "your name", "who are you", "rilie", "yourself", "you care",
        "your purpose", "you different", "trust you", "you know",
        "you feel", "you alive", "you conscious", "who made",
        "who built", "who created", "what are you", "about you",
        "introduce yourself", "bad day", "having a bad",
        "teach me", "tell me something",
    ],
}

# ============================================================================
# WORD DEFINITIONS — She carries a pocket dictionary. Not Wikipedia.
# Just enough to cook with.
# ============================================================================

WORD_DEFINITIONS: Dict[str, str] = {
    # Music
    "density": "maximum information packed into minimum space",
    "rhythm": "pattern of beats recurring in time",
    "compression": "reducing to essence without losing meaning",
    "bars": "measured units of musical time",
    "tight": "precise with zero waste",
    "minimal": "stripped to only what matters",
    "call": "an invitation that demands response",
    "response": "the answer that completes the exchange",
    "connection": "the bridge between two points",
    "harmony": "different notes working as one",
    "voice": "the instrument that carries identity",
    "emotion": "energy in motion through feeling",
    "dissonance": "tension between things that clash",
    "tension": "the pull between opposing forces",
    "comedy": "truth delivered through surprise",
    "trojan": "something hidden inside something inviting",
    "truth": "what remains when everything else is stripped",
    "expose": "to reveal what was hidden",
    "noise": "information that hasn't been organized yet",
    "collage": "fragments assembled into new meaning",
    "architecture": "intentional structure that serves purpose",
    "intent": "purpose behind the action",
    "sample": "a piece of something larger carried forward",
    "layers": "depth built by stacking",
    # Culture
    "reframe": "to change how something is seen without changing what it is",
    "broadcast": "to send signal in all directions",
    "political": "concerning who has power and how it moves",
    "street": "where theory meets lived experience",
    "institution": "a structure that outlasts the people in it",
    "blueprint": "a plan you can build from",
    "mobilize": "to turn stillness into movement",
    "trickster": "the one who breaks rules to reveal truth",
    "weapon": "any tool used to shift power",
    # Physics
    "conserve": "nothing lost only transformed",
    "transform": "to change form while preserving essence",
    "symmetry": "the pattern that stays the same when you rotate it",
    "frozen": "energy held still in a form",
    "energy": "the capacity to make change happen",
    "matter": "energy in a form you can touch",
    "equivalence": "different expressions of the same thing",
    "frame": "the perspective that determines what you see",
    "perception": "reality filtered through position",
    "superposition": "being in multiple states until forced to choose",
    "collapse": "the moment possibility becomes specific",
    "observe": "to interact with something by paying attention",
    "entangle": "connected regardless of distance",
    "uncertainty": "precision in one dimension costs precision in another",
    "tradeoff": "getting one thing by giving up another",
    # Life
    "cancer": "growth without regard for the whole",
    "ego": "self-prioritization that forgets the system",
    "sacrifice": "giving up the part for the whole",
    "adapt": "changing shape to fit new conditions",
    "symbiosis": "two things thriving because they serve each other",
    "emergence": "complex behavior from simple rules repeated",
    "recursive": "applying the same pattern at every level",
    "diversity": "strength through difference",
    "stability": "the ability to absorb shock without breaking",
    # Games
    "dilemma": "a choice where every option has cost",
    "collective": "the group acting as one",
    "equilibrium": "the point where no one gains by moving alone",
    "trust": "risk taken on the belief another will reciprocate",
    "drops": "small consistent deposits over time",
    "buckets": "large sudden losses",
    "grace": "giving more than what's owed",
    "mirror": "reflecting back what you receive",
    "memory": "the past informing present choices",
    "commit": "removing the option to retreat",
    "misaligned": "pointed in different directions",
    # Thermodynamics
    "entropy": "disorder increasing over time without input",
    "disorder": "the absence of intentional arrangement",
    "waste": "energy that did no useful work",
    "beige": "safe mediocrity that offends no one and moves no one",
    "harm": "damage that can't be fully undone",
    "irreversible": "a change that only goes one direction",
    "cascade": "one failure triggering the next",
    "propagate": "spreading through connected nodes",
    "negentropy": "order created by pumping energy into a system",
    # Cosmology
    "boolean": "the simplest possible distinction — yes or no",
    "tick": "the smallest unit of change",
    "fractal": "the same pattern at every scale",
    "scale": "the level at which you observe",
    "humility": "acknowledging what you cannot know",
    # Finance
    "destiny": "where the weight of evidence points",
    "signal": "information that predicts what comes next",
    "conviction": "certainty earned by evidence",
    "quality": "the ratio of signal to noise",
    "accordion": "expanding and contracting with conditions",
    "regime": "the current rules the system operates under",
    "chaos": "conditions where normal rules break down",
    "patience": "the willingness to wait for the right moment",
    "compound": "growth building on previous growth",
    "integrity": "alignment between what you say and what you do",
}

# ============================================================================
# WORD SYNONYMS
# ============================================================================

WORD_SYNONYMS: Dict[str, List[str]] = {
    "density": ["concentration", "thickness", "richness", "weight"],
    "rhythm": ["pulse", "cadence", "groove", "cycle"],
    "compression": ["condensation", "distillation", "essence", "reduction"],
    "harmony": ["accord", "unity", "resonance", "blend"],
    "tension": ["friction", "pull", "strain", "charge"],
    "truth": ["reality", "authenticity", "core", "foundation"],
    "noise": ["static", "chaos", "raw signal", "unfiltered"],
    "architecture": ["structure", "framework", "design", "blueprint"],
    "energy": ["force", "drive", "capacity", "potential"],
    "transform": ["convert", "reshape", "evolve", "transmute"],
    "symmetry": ["balance", "equivalence", "mirror", "pattern"],
    "collapse": ["resolve", "crystallize", "decide", "converge"],
    "emergence": ["arising", "surfacing", "spontaneous order", "self-organization"],
    "trust": ["faith", "confidence", "reliability", "bond"],
    "grace": ["generosity", "mercy", "kindness", "gift"],
    "entropy": ["decay", "disorder", "dissipation", "degradation"],
    "cascade": ["chain reaction", "domino effect", "ripple", "avalanche"],
    "signal": ["indicator", "cue", "marker", "evidence"],
    "conviction": ["certainty", "confidence", "resolve", "commitment"],
    "patience": ["endurance", "persistence", "steady", "long game"],
    "integrity": ["wholeness", "alignment", "honesty", "consistency"],
    "ego": ["self-interest", "pride", "self-image", "vanity"],
    "sacrifice": ["surrender", "offering", "cost", "trade"],
    "adapt": ["adjust", "evolve", "flex", "pivot"],
    "diversity": ["variety", "range", "spectrum", "multiplicity"],
    "connection": ["link", "bridge", "thread", "bond"],
    "blueprint": ["plan", "template", "map", "schema"],
    "fractal": ["self-similar", "nested", "recursive", "layered"],
    "compound": ["accumulate", "snowball", "build", "stack"],
}

# ============================================================================
# WORD HOMONYMS — The polymorphic layer. Multiple meanings in one word.
# ============================================================================

WORD_HOMONYMS: Dict[str, List[str]] = {
    "bars": ["music: measured units of rhythm", "prison: what cages are made of", "drinking: where people gather", "legal: the bar exam"],
    "scale": ["music: sequence of notes", "size: the level you observe at", "fish: protective covering", "climbing: to ascend"],
    "bridge": ["music: the section that connects verse to chorus", "structure: what connects two shores", "guitar: where strings meet the body", "connection: what links two ideas"],
    "key": ["music: tonal center", "lock: what opens a door", "answer: the crucial element", "keyboard: what you press"],
    "beat": ["music: rhythmic pulse", "defeat: to overcome", "tired: exhausted", "patrol: a cop's route"],
    "note": ["music: a single pitch", "writing: a short message", "observe: to notice something", "money: a bill"],
    "rest": ["music: silence with duration", "sleep: to recover", "remainder: what's left over"],
    "pitch": ["music: frequency of sound", "sales: a presentation to convince", "baseball: to throw", "angle: degree of slope"],
    "record": ["music: an album", "data: a stored entry", "achievement: the best ever done", "capture: to document"],
    "track": ["music: a single song", "path: a route to follow", "monitor: to keep watch on", "racing: where you run"],
    "hook": ["music: the catchy part", "fishing: what catches", "boxing: a curved punch", "coding: a callback function"],
    "sample": ["music: a borrowed sound", "science: a specimen", "taste: a small portion to try"],
    "channel": ["music: a signal path", "water: a passage between lands", "tv: a station", "communication: a medium"],
    "wave": ["physics: energy moving through space", "ocean: water rising and falling", "greeting: a hand gesture", "trend: a cultural movement"],
    "field": ["physics: a force distribution in space", "farm: cultivated land", "expertise: a domain of knowledge", "sports: where you play"],
    "charge": ["physics: electrical property", "money: a cost", "attack: to rush forward", "responsibility: to be in charge of"],
    "bond": ["chemistry: atoms held together", "finance: a debt instrument", "connection: emotional attachment", "spy: 007"],
    "cell": ["biology: basic unit of life", "prison: a small room", "phone: mobile device", "power: battery unit"],
    "culture": ["society: shared values and practices", "biology: growing organisms in a lab", "agriculture: to cultivate"],
    "matter": ["physics: stuff with mass", "importance: it matters", "problem: what's the matter"],
    "frame": ["physics: reference point", "picture: what holds the image", "blame: to set someone up", "structure: the skeleton of something"],
    "flow": ["water: movement of liquid", "music: rhythmic delivery", "psychology: optimal state of performance", "traffic: movement through a system"],
    "drive": ["car: to operate a vehicle", "motivation: internal push", "computer: storage device", "golf: a long shot"],
    "collapse": ["physics: wave function resolving", "building: structural failure", "medical: to fall down", "folding: to make compact"],
    "foundation": ["building: what supports the structure", "philosophy: the base assumption", "makeup: the base layer", "charity: an organization that gives"],
    "deposit": ["bank: money put in", "geology: sediment laid down", "trust: something left as guarantee"],
    "fire": ["element: combustion", "work: to terminate employment", "passion: intense motivation", "weapon: to discharge"],
    "plant": ["biology: a growing organism", "factory: a manufacturing facility", "spy: to secretly place", "evidence: to fabricate"],
    "toast": ["bread: heated until crispy", "celebration: raising a glass", "done: finished or ruined"],
    "patient": ["medical: someone receiving care", "virtue: willing to wait", "steady: unhurried and calm"],
    "gravity": ["physics: the force of attraction", "seriousness: the weight of a situation"],
    "volume": ["sound: loudness level", "book: a single tome", "space: amount of three-dimensional space", "quantity: amount"],
    "current": ["water: flow direction", "electricity: flow of charge", "time: happening now", "awareness: up to date"],
    "resolution": ["conflict: settling a dispute", "screen: pixel density", "decision: a firm commitment", "music: tension releasing to rest"],
    "minor": ["music: a sad-sounding key", "age: not yet adult", "importance: of lesser significance"],
    "major": ["music: a bright-sounding key", "military: a rank", "importance: significant", "college: area of study"],
    "sharp": ["music: a half step up", "blade: able to cut", "mind: quick and intelligent", "image: clear and defined"],
    "flat": ["music: a half step down", "surface: level and even", "tire: deflated", "apartment: a dwelling"],
}
