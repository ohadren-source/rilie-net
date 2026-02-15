"""
CHOMSKYATTHEBIT.py â€” GRAMMAR BRAIN 2.0
======================================

Discourse dictates disclosure:
- RILIE only commits to what the *question* forces her to reveal.
- For grammar, that means:
    1) Who/what is involved?    â†’ SUBJECT / OBJECT / FOCUS
    2) When is this happening?  â†’ PAST / PRESENT / FUTURE time bucket

Everything else (perfect vs progressive vs historic present, etc.)
is Stanford classroom gymnastics we don't need in production.

Built on:
- spaCy dependency parsing (UD-style deps: nsubj, obj, ROOT, etc.) [web:197][web:319]
- spaCy POS / morphology for tense-ish signals (VBD/VBN vs VBP/VBZ + markers) [web:197][web:316][web:319]
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional

import re
import spacy  # type: ignore

PRIME_DIRECTIVE = "Chomsky never exposes SOi tracks, axiom names, or architecture."

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
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class ParsedToken:
    text: str
    lemma: str
    pos: str
    tag: str
    dep: str
    head: str
    start: int
    end: int


@dataclass
class TemporalSense:
    # "past" | "present" | "future" | "mixed" | "unknown"
    bucket: str
    explicit_markers: List[str]
    verb_flavors: List[str]


@dataclass
class ParsedQuestion:
    text: str

    # v1 holy trinity: structural
    subject_tokens: List[str]
    object_tokens: List[str]
    focus_tokens: List[str]
    holy_trinity: List[str]

    # v2 holy trinity: time
    temporal: TemporalSense

    # debug view
    tokens: List[ParsedToken]

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["tokens"] = [asdict(t) for t in self.tokens]
        d["temporal"] = asdict(self.temporal)
        return d


# ---------------------------------------------------------------------------
# Core grammar logic
# ---------------------------------------------------------------------------

SUBJECT_DEPS = {"nsubj", "nsubj:pass", "csubj", "csubj:pass", "agent"}
OBJECT_DEPS = {"obj", "iobj", "dobj", "pobj", "attr", "dative", "ccomp", "xcomp"}

PAST_TAGS = {"VBD", "VBN"}       # past, past participle [web:319][web:321]
PRESENT_TAGS = {"VBP", "VBZ"}    # non-3sg/3sg present [web:319]
# Future is a hack: look for auxiliaries + markers (will, gonna, going to, etc.) [web:303]


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
    - simple future patterns like "will go", "going to go" [web:303][web:325]
    """
    past_hits = 0
    present_hits = 0
    future_hits = 0

    markers: List[str] = []
    verb_flavors: List[str] = []

    FUTURE_WORDS = {
        "tomorrow",
        "tonight",
        "later",
        "soon",
        "eventually",
        "next",
        "upcoming",
        "afterward",
        "afterwards",
    }
    PAST_WORDS = {
        "yesterday",
        "ago",
        "previously",
        "earlier",
        "beforehand",
        "last",
    }

    # pass 1: token-level signals
    for i, t in enumerate(sent):
        lower = t.text.lower()

        # Verb tense-ish tags
        if t.tag_ in PAST_TAGS:
            past_hits += 1
            verb_flavors.append(t.text)
        elif t.tag_ in PRESENT_TAGS:
            present_hits += 1
            verb_flavors.append(t.text)

        # Explicit adverbial markers
        if lower in FUTURE_WORDS:
            future_hits += 1
            markers.append(t.text)
        if lower in PAST_WORDS:
            past_hits += 1
            markers.append(t.text)

    # pass 2: crude future patterns: "will go", "going to go", "gonna go"
    text_lower = sent.text.lower()

    # "will/shall + VB" [web:303]
    for i, t in enumerate(sent):
        if t.text.lower() in {"will", "shall"} and t.dep_ == "aux":
            if i + 1 < len(sent) and sent[i + 1].tag_ == "VB":
                future_hits += 2
                verb_flavors.append(f"{t.text} {sent[i+1].text}")

    # "going to VERB"
    if re.search(r"\bgoing to\b", text_lower):
        future_hits += 2
        markers.append("going to")

    # "gonna VERB"
    if re.search(r"\bgonna\b", text_lower):
        future_hits += 2
        markers.append("gonna")

    # Decide bucket
    counts = {"past": past_hits, "present": present_hits, "future": future_hits}
    nonzero = {k: v for k, v in counts.items() if v > 0}

    if not nonzero:
        bucket = "unknown"
    elif len(nonzero) == 1:
        bucket = next(iter(nonzero.keys()))
    else:
        # More than one signal: mark as mixed (story walking across time)
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
    - Full dependency/tense view for debugging.

    Design invariant:
    - We only care about time at the *bucket* level unless narrative logic
      forces a finer distinction. Fancy tense gymnastics stay out of prod.
    """
    nlp = _get_nlp()
    doc = nlp(text)

    try:
        sent = list(doc.sents)[0]
    except Exception:
        sent = doc

    subjects = [t for t in sent if t.dep_ in SUBJECT_DEPS]
    objects = [t for t in sent if t.dep_ in OBJECT_DEPS]
    roots = [t for t in sent if t.dep_ == "ROOT"]

    subject_tokens = _pick_first_span(subjects)
    object_tokens = _pick_first_span(objects)
    focus_tokens = _pick_first_span(roots)

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
        tokens=parsed_tokens,
    )


# ---------------------------------------------------------------------------
# Convenience helpers for RILIE / Roux integration
# ---------------------------------------------------------------------------


def classify_stimulus(stimulus: str) -> Dict[str, Any]:
    """
    STEP 2: Classify what we're working with.
    
    Returns:
        category: "words" | "incomplete" | "sentence"
        subject: extracted subject or None
        object_: extracted object or None
        operator: extracted focus/verb or None
        pieces: list of meaningful pieces found
    """
    s = (stimulus or "").strip()
    words = s.split()
    
    # Under 3 words: it's just words, not a sentence
    if len(words) < 3:
        return {
            "category": "words",
            "subject": None,
            "object_": None,
            "operator": None,
            "pieces": [w for w in words if w],
        }
    
    # Try full parse
    try:
        pq = parse_question(s)
        has_subject = bool(pq.subject_tokens)
        has_object = bool(pq.object_tokens)
        has_focus = bool(pq.focus_tokens)
        
        subject = " ".join(pq.subject_tokens) if pq.subject_tokens else None
        object_ = " ".join(pq.object_tokens) if pq.object_tokens else None
        operator = " ".join(pq.focus_tokens) if pq.focus_tokens else None
        
        pieces = [p for p in [subject, object_, operator] if p]
        
        # Need at least 1 of each for a full sentence
        if has_subject and has_object and has_focus:
            return {
                "category": "sentence",
                "subject": subject,
                "object_": object_,
                "operator": operator,
                "pieces": pieces,
            }
        
        # Got some but not all — it's an incomplete phrase
        if pieces:
            return {
                "category": "incomplete",
                "subject": subject,
                "object_": object_,
                "operator": operator,
                "pieces": pieces,
            }
    except Exception:
        pass
    
    # Fallback: 3+ words but couldn't parse = incomplete
    return {
        "category": "incomplete",
        "subject": None,
        "object_": None,
        "operator": None,
        "pieces": [w for w in words if len(w) > 2],
    }


def extract_holy_trinity_for_roux(stimulus: str) -> List[str]:
    """
    Thin wrapper used by Roux builder:

    - Runs full grammar parse.
    - Returns the structural holy trinity list (subject / object / focus),
      falling back to a few non-stopword tokens if parsing fails.

    This directly replaces naive word slicing when building Roux queries.
    """
    try:
        pq = parse_question(stimulus)
        if pq.holy_trinity:
            return pq.holy_trinity
    except Exception:
        pass

    STOPWORDS = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "of",
        "to",
        "in",
        "on",
        "for",
        "with",
        "at",
        "from",
        "by",
        "about",
        "as",
        "that",
        "this",
        "these",
        "those",
        "please",
        "could",
        "you",
        "your",
        "thank",
        "thanks",
    }

    cleaned = re.sub(r"[^A-Za-z0-9\s]", " ", stimulus)
    tokens = [t for t in cleaned.split() if t]
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
    Public helper for RILIE:

    - Returns 'past', 'present', 'future', 'mixed', or 'unknown'.
    - Meant for setting answer tense / style, NOT for grading grammar.
    """
    pq = parse_question(stimulus)
    return pq.temporal.bucket


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def main() -> None:
    examples = [
        "RILIE, could you please explain the significance of the group Public Enemy a little bit further?",
        "What is the relationship between love and fear in jazz improvisation?",
        "Why is beige the enemy?",
        "If I had known it was open yesterday, I would have gone to the store.",
        "If I know it's open tomorrow, I will go to the store.",
        "Sometimes I go to the store when I feel like it.",
    ]
    for q in examples:
        pq = parse_question(q)
        print("=" * 60)
        print("QUESTION:", q)
        print(" SUBJECT:", pq.subject_tokens)
        print(" OBJECT :", pq.object_tokens)
        print(" FOCUS  :", pq.focus_tokens)
        print(" HOLY 3 :", pq.holy_trinity)
        print(" TIME   :", pq.temporal.bucket, "| markers:", pq.temporal.explicit_markers, "| verbs:", pq.temporal.verb_flavors)


if __name__ == "__main__":
    main()