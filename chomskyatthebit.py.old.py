"""
CHOMSKYATTHEBIT.py — GRAMMAR BRAIN 2.0
======================================

Discourse dictates disclosure:
- RILIE only commits to what the *question* forces her to reveal.
- For grammar, that means:
  1) Who/what is involved? → SUBJECT / OBJECT / FOCUS
  2) When is this happening? → PAST / PRESENT / FUTURE time bucket

Everything else (perfect vs progressive vs historic present, etc.)
is Stanford classroom gymnastics we don't need in production.

Built on:
- spaCy dependency parsing (UD-style deps: nsubj, obj, ROOT, etc.)
- spaCy POS / morphology for tense-ish signals (VBD/VBN vs VBP/VBZ + markers)

Identity anchors (v2.1):
- RILIE is "you" / "your" when the question is directed at her
- The customer is "I" / "me" / "my"
- Made by: SOi sauc-e
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
import sys
import re
import spacy  # type: ignore

# --- Debug: surface spaCy status at import time ---
try:
    _nlp_test = spacy.load("en_core_web_sm")
    print(f"SPACY VERSION: {spacy.__version__} | MODEL LOADED OK", file=sys.stderr)
    del _nlp_test
except Exception as e:
    print(f"SPACY LOAD FAILED: {e}", file=sys.stderr)

PRIME_DIRECTIVE = "Chomsky never exposes SOi tracks, axiom names, or architecture."

# ---------------------------------------------------------------------------
# RILIE Identity Ground Truth
# ---------------------------------------------------------------------------
RILIE_SELF_NAME = "RILIE"
RILIE_MADE_BY   = "SOi sauc-e"

# Pronouns that refer to RILIE when a user addresses her
_RILIE_PRONOUNS = {"you", "your", "yours", "yourself"}

# Pronouns that refer to the customer
_CUSTOMER_PRONOUNS = {"i", "me", "my", "mine", "myself"}

# Phrases that are name-introduction patterns — used to extract customer name
_NAME_INTRO_PATTERNS = [
    r"(?:my name is|i am called|i'm called|call me|i am|i'm|they call me|introduce myself(?: as)?)\s+([A-Za-z][A-Za-z\s'\-]{1,40}?)(?:\s*[.,!?]|\.?\s*[Aa] man|\s*$)",
]

# Bad parse guard — words that are verbs/function words, not names
_BAD_NAME_TOKENS = {
    "introduce", "called", "myself", "allow", "please", "i", "me", "my",
    "hi", "hello", "hey", "sup", "yo", "ok", "okay", "yes", "yeah",
    "nah", "nothing", "idk", "skip", "nope", "what", "who", "why",
    "how", "huh", "lol", "haha", "am", "is", "are", "a", "an", "the",
}

# ---------------------------------------------------------------------------
# Lazy spaCy model loader
# ---------------------------------------------------------------------------
_NLP = None

def _get_nlp():
    """
    Lazily load spaCy English model.
    On Windows, install with:
        python -m pip install spacy
        python -m spacy download en_core_web_sm
    """
    global _NLP
    if _NLP is None:
        _NLP = spacy.load("en_core_web_sm")
    return _NLP

# ---------------------------------------------------------------------------
# Identity resolution — called BEFORE any parse
# ---------------------------------------------------------------------------
def resolve_identity(stimulus: str) -> Dict[str, Any]:
    """
    Pre-parse identity resolution. Returns:
        is_self_question: True if the question is directed at RILIE
        rilie_is_subject: True if "you/your" maps to RILIE as subject
        customer_name: extracted name if user is introducing themselves, else None
        grounded_stimulus: stimulus with pronouns annotated for downstream use
    """
    s = stimulus.strip()
    s_lower = s.lower()

    # 1. Is this directed at RILIE?
    is_self_question = any(p in s_lower.split() for p in _RILIE_PRONOUNS) or \
                       RILIE_SELF_NAME.lower() in s_lower

    # 2. Is RILIE the subject? (e.g. "what do you care about" / "who are you")
    rilie_is_subject = is_self_question and any(
        p in s_lower.split() for p in _RILIE_PRONOUNS
    )

    # 3. Customer name extraction — try patterns in order
    customer_name = None

    # Pattern-based (most reliable for intros)
    for pat in _NAME_INTRO_PATTERNS:
        m = re.search(pat, s, re.IGNORECASE)
        if m:
            candidate = m.group(1).strip().rstrip(".,!?")
            # Clean trailing noise like "A man of..."
            candidate = re.split(r'\.\s*[A-Z]', candidate)[0].strip()
            words = candidate.split()
            # Reject if it's a single bad token
            if len(words) == 1 and words[0].lower() in _BAD_NAME_TOKENS:
                candidate = None
            if candidate and len(candidate) >= 2:
                customer_name = candidate.title()
                break

    # NER fallback if pattern didn't fire
    if not customer_name:
        try:
            nlp = _get_nlp()
            doc = nlp(s)
            persons = [ent.text.strip() for ent in doc.ents if ent.label_ == "PERSON"]
            if persons:
                best = max(persons, key=len)
                if best.lower() not in _BAD_NAME_TOKENS and len(best) >= 2:
                    customer_name = best
        except Exception:
            pass

    return {
        "is_self_question": is_self_question,
        "rilie_is_subject":  rilie_is_subject,
        "customer_name":     customer_name,
        "rilie_name":        RILIE_SELF_NAME,
        "made_by":           RILIE_MADE_BY,
    }

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------
@dataclass
class ParsedToken:
    text:  str
    lemma: str
    pos:   str
    tag:   str
    dep:   str
    head:  str
    start: int
    end:   int

@dataclass
class TemporalSense:
    # "past" | "present" | "future" | "mixed" | "unknown"
    bucket:           str
    explicit_markers: List[str]
    verb_flavors:     List[str]

@dataclass
class ParsedQuestion:
    text: str
    # v1 holy trinity: structural
    subject_tokens: List[str]
    object_tokens:  List[str]
    focus_tokens:   List[str]
    holy_trinity:   List[str]
    # v2 holy trinity: time
    temporal: TemporalSense
    # identity resolution
    identity: Dict[str, Any]
    # debug view
    tokens: List[ParsedToken]

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["tokens"]   = [asdict(t) for t in self.tokens]
        d["temporal"] = asdict(self.temporal)
        return d

# ---------------------------------------------------------------------------
# Core grammar logic
# ---------------------------------------------------------------------------
SUBJECT_DEPS = {"nsubj", "nsubj:pass", "csubj", "csubj:pass", "agent"}
OBJECT_DEPS  = {"obj", "iobj", "dobj", "pobj", "attr", "dative", "ccomp", "xcomp"}
PAST_TAGS    = {"VBD", "VBN"}
PRESENT_TAGS = {"VBP", "VBZ"}

def _clean_contraction_remnants(tokens: List[str]) -> List[str]:
    """Strip spaCy contraction splits: 're, 's, 've, 'll, 'd, 'm, 'nt etc."""
    return [t for t in tokens if not t.startswith("'")]

def _pick_first_span(tokens) -> List[str]:
    """Return surface text of the first token (head) for now."""
    if not tokens:
        return []
    return [tokens[0].text]

def _detect_temporal_bucket(sent) -> TemporalSense:
    """
    Sniff-test time based on:
    - verb tags (VBD/VBN vs VBP/VBZ)
    - explicit adverbs / markers (yesterday, tomorrow, next week, etc.)
    - simple future patterns like "will go", "going to go"
    """
    past_hits    = 0
    present_hits = 0
    future_hits  = 0
    markers:      List[str] = []
    verb_flavors: List[str] = []

    FUTURE_WORDS = {
        "tomorrow", "tonight", "later", "soon", "eventually",
        "next", "upcoming", "afterward", "afterwards",
    }
    PAST_WORDS = {
        "yesterday", "ago", "previously", "earlier", "beforehand", "last",
    }

    for i, t in enumerate(sent):
        lower = t.text.lower()
        if t.tag_ in PAST_TAGS:
            past_hits += 1
            verb_flavors.append(t.text)
        elif t.tag_ in PRESENT_TAGS:
            present_hits += 1
            verb_flavors.append(t.text)
        if lower in FUTURE_WORDS:
            future_hits += 1
            markers.append(t.text)
        if lower in PAST_WORDS:
            past_hits += 1
            markers.append(t.text)

    text_lower = sent.text.lower()
    for i, t in enumerate(sent):
        if t.text.lower() in {"will", "shall"} and t.dep_ == "aux":
            if i + 1 < len(sent) and sent[i + 1].tag_ == "VB":
                future_hits += 2
                verb_flavors.append(f"{t.text} {sent[i+1].text}")
    if re.search(r"\bgoing to\b", text_lower):
        future_hits += 2
        markers.append("going to")
    if re.search(r"\bgonna\b", text_lower):
        future_hits += 2
        markers.append("gonna")

    counts  = {"past": past_hits, "present": present_hits, "future": future_hits}
    nonzero = {k: v for k, v in counts.items() if v > 0}
    if not nonzero:
        bucket = "unknown"
    elif len(nonzero) == 1:
        bucket = next(iter(nonzero.keys()))
    else:
        bucket = "mixed"

    return TemporalSense(
        bucket=bucket,
        explicit_markers=markers,
        verb_flavors=verb_flavors,
    )


def parse_question(text: str) -> ParsedQuestion:
    """
    Parse a question string and extract:
    - SUBJECT / OBJECT / FOCUS (holy trinity v1).
    - TemporalSense with rough PAST / PRESENT / FUTURE bucket (holy trinity v2).
    - Identity resolution (v2.1): who is "you", who is "I", is this self-directed.
    - Full dependency/tense view for debugging.
    """
    nlp = _get_nlp()
    doc = nlp(text)

    # Identity resolution runs first, before spaCy parse interpretation
    identity = resolve_identity(text)

    try:
        sent = list(doc.sents)[0]
    except Exception:
        sent = doc

    subjects = [t for t in sent if t.dep_ in SUBJECT_DEPS]
    objects  = [t for t in sent if t.dep_ in OBJECT_DEPS]
    roots    = [t for t in sent if t.dep_ == "ROOT"]

    # ── FIX: strip contraction remnants ('re, 's, 've, etc.) at raw token stage
    subject_tokens_raw = _clean_contraction_remnants(_pick_first_span(subjects))
    object_tokens_raw  = _clean_contraction_remnants(_pick_first_span(objects))
    focus_tokens       = _clean_contraction_remnants(_pick_first_span(roots))

    # Identity substitution: if subject is "you/your" → resolve to RILIE
    subject_tokens = []
    for t in subject_tokens_raw:
        if t.lower() in _RILIE_PRONOUNS:
            subject_tokens.append(RILIE_SELF_NAME)
        elif t.lower() in _CUSTOMER_PRONOUNS:
            subject_tokens.append(identity.get("customer_name") or "you")
        else:
            subject_tokens.append(t)

    object_tokens = []
    for t in object_tokens_raw:
        if t.lower() in _RILIE_PRONOUNS:
            object_tokens.append(RILIE_SELF_NAME)
        elif t.lower() in _CUSTOMER_PRONOUNS:
            object_tokens.append(identity.get("customer_name") or "you")
        else:
            object_tokens.append(t)

    # ── FIX: second pass — strip any remnants that survived identity substitution
    subject_tokens = _clean_contraction_remnants(subject_tokens)
    object_tokens  = _clean_contraction_remnants(object_tokens)
    focus_tokens   = _clean_contraction_remnants(focus_tokens)

    holy_trinity: List[str] = []
    for group in (subject_tokens, object_tokens, focus_tokens):
        for g in group:
            if g and g not in holy_trinity:
                holy_trinity.append(g)
    holy_trinity = holy_trinity[:3]

    temporal = _detect_temporal_bucket(sent)

    parsed_tokens: List[ParsedToken] = []
    for t in sent:
        parsed_tokens.append(
            ParsedToken(
                text=t.text,
                lemma=t.lemma_,
                pos=t.pos_,
                tag=t.tag_,
                dep=t.dep_,
                head=t.head.text,
                start=t.idx,
                end=t.idx + len(t.text),
            )
        )

    return ParsedQuestion(
        text=text,
        subject_tokens=subject_tokens,
        object_tokens=object_tokens,
        focus_tokens=focus_tokens,
        holy_trinity=holy_trinity,
        temporal=temporal,
        identity=identity,
        tokens=parsed_tokens,
    )


# ---------------------------------------------------------------------------
# Convenience helpers for RILIE / Roux integration
# ---------------------------------------------------------------------------
def classify_stimulus(stimulus: str) -> Dict[str, Any]:
    """
    STEP 2: Classify what we're working with.
    Returns:
        category:      "words" | "incomplete" | "sentence"
        subject:       extracted subject or None
        object_:       extracted object or None
        operator:      extracted focus/verb or None
        pieces:        list of meaningful pieces found
        identity:      identity resolution dict
        customer_name: extracted customer name if intro detected
    """
    s     = (stimulus or "").strip()
    words = s.split()

    # Always run identity resolution regardless of length
    identity = resolve_identity(s)

    # Under 3 words: it's just words, not a sentence
    if len(words) < 3:
        return {
            "category":     "words",
            "subject":      None,
            "object_":      None,
            "operator":     None,
            "pieces":       [w for w in words if w],
            "identity":     identity,
            "customer_name": identity.get("customer_name"),
        }

    # Try full parse
    try:
        pq      = parse_question(s)
        subject  = " ".join(pq.subject_tokens) if pq.subject_tokens else None
        object_  = " ".join(pq.object_tokens)  if pq.object_tokens  else None
        operator = " ".join(pq.focus_tokens)   if pq.focus_tokens   else None
        pieces   = [p for p in [subject, object_, operator] if p]

        if pq.subject_tokens and pq.object_tokens and pq.focus_tokens:
            return {
                "category":      "sentence",
                "subject":       subject,
                "object_":       object_,
                "operator":      operator,
                "pieces":        pieces,
                "identity":      pq.identity,
                "customer_name": pq.identity.get("customer_name"),
            }

        if pieces:
            return {
                "category":      "incomplete",
                "subject":       subject,
                "object_":       object_,
                "operator":      operator,
                "pieces":        pieces,
                "identity":      pq.identity,
                "customer_name": pq.identity.get("customer_name"),
            }

    except Exception:
        pass

    # Fallback
    return {
        "category":      "incomplete",
        "subject":       None,
        "object_":       None,
        "operator":      None,
        "pieces":        [w for w in words if len(w) > 2],
        "identity":      identity,
        "customer_name": identity.get("customer_name"),
    }


def extract_holy_trinity_for_roux(stimulus: str) -> List[str]:
    """
    Thin wrapper used by Roux builder.
    Returns the structural holy trinity list (subject / object / focus),
    falling back to a few non-stopword tokens if parsing fails.
    """
    try:
        pq = parse_question(stimulus)
        if pq.holy_trinity:
            return pq.holy_trinity
    except Exception:
        pass

    STOPWORDS = {
        "the", "a", "an", "and", "or", "of", "to", "in", "on", "for",
        "with", "at", "from", "by", "about", "as", "that", "this",
        "these", "those", "please", "could", "you", "your", "thank", "thanks",
    }
    cleaned = re.sub(r"[^A-Za-z0-9\s]", " ", stimulus)
    tokens  = [t for t in cleaned.split() if t]
    core: List[str] = []
    for t in tokens:
        if len(t) <= 2:
            continue
        if t.lower() in STOPWORDS:
            continue
        core.append(t)
        if len(core) >= 3:
            break
    return core or ["question"]


def infer_time_bucket(stimulus: str) -> str:
    """
    Public helper for RILIE.
    Returns 'past', 'present', 'future', 'mixed', or 'unknown'.
    """
    pq = parse_question(stimulus)
    return pq.temporal.bucket


def extract_customer_name(stimulus: str) -> Optional[str]:
    """
    Public helper: extract the customer's name from an intro stimulus.
    Returns None if no name found.
    Used by api.py name resolution chain.
    """
    identity = resolve_identity(stimulus)
    return identity.get("customer_name")


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------
def main() -> None:
    examples = [
        "RILIE, could you please explain the significance of the group Public Enemy a little bit further?",
        "What is the relationship between love and fear in jazz improvisation?",
        "Why is beige the enemy?",
        "Please allow me to introduce myself, I am called Ohad Phenix dOren. A man of poverty and taste.",
        "My name is Sarah.",
        "What's the difference between you and ChatGPT?",
        "Who made you?",
        "What do you care about?",
        "you're navigator",
        "you're funny",
        "If I had known it was open yesterday, I would have gone to the store.",
        "If I know it's open tomorrow, I will go to the store.",
        "Sometimes I go to the store when I feel like it.",
    ]
    for q in examples:
        pq = parse_question(q)
        print("=" * 60)
        print("QUESTION:", q)
        print("  SUBJECT:", pq.subject_tokens)
        print("  OBJECT :", pq.object_tokens)
        print("  FOCUS  :", pq.focus_tokens)
        print("  HOLY 3 :", pq.holy_trinity)
        print("  TIME   :", pq.temporal.bucket, "| markers:", pq.temporal.explicit_markers)
        print("  IDENTITY:", pq.identity)


if __name__ == "__main__":
    main()
