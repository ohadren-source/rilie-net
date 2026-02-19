"""
session.py — RILIE's Elephant Memory (Session Persistence)

===========================================================

She remembers who you are. She picks up where she left off.

No restarts. No re-introductions. Continuous thread.

Session key: name + IP → "ohad_192.168.1.42"

Anonymous until name captured → IP-only key with name = "Mate".

One table. Load on arrival. Save every turn. Pick up on return.

Uses the same Postgres plumbing as banks.py:

- DATABASE_URL from environment
- psycopg2 via banks.get_db_conn()

Migration V006 in the BANKS family.
"""

import json
import logging
import re
from typing import Dict, Any, Optional, List, Tuple

from banks import get_db_conn

logger = logging.getLogger("session")

# ---------------------------------------------------------------------------
# The default. Eleven meanings. One word.
# ---------------------------------------------------------------------------

DEFAULT_NAME = "Mate"

# ---------------------------------------------------------------------------
# Table — one row per session (V006)
# ---------------------------------------------------------------------------


def ensure_session_table() -> None:
    """
    Idempotently create banks_sessions if it doesn't exist yet.

    Safe to call on every startup. Same pattern as banks.ensure_*_table().
    """
    sql = """
    CREATE TABLE IF NOT EXISTS banks_sessions (
        session_id TEXT PRIMARY KEY,
        user_name TEXT NOT NULL DEFAULT 'Mate',
        client_ip TEXT NOT NULL,
        name_source TEXT NOT NULL DEFAULT 'default',
        turn_count INTEGER DEFAULT 0,
        whosonfirst BOOLEAN DEFAULT TRUE,
        response_history JSONB DEFAULT '[]'::jsonb,
        talk_served JSONB DEFAULT '[]'::jsonb,
        social_state JSONB DEFAULT '{}'::jsonb,
        topics JSONB DEFAULT '{}'::jsonb,
        created_at TIMESTAMPTZ DEFAULT now(),
        updated_at TIMESTAMPTZ DEFAULT now()
    );

    CREATE INDEX IF NOT EXISTS idx_sessions_client_ip
        ON banks_sessions (client_ip);

    CREATE INDEX IF NOT EXISTS idx_sessions_user_name
        ON banks_sessions (user_name)
        WHERE user_name != 'Mate';

    CREATE INDEX IF NOT EXISTS idx_sessions_name_source
        ON banks_sessions (name_source);
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
        logger.info("banks_sessions table ensured.")
    except Exception as e:
        logger.warning("Could not ensure sessions table: %s", e)


# ---------------------------------------------------------------------------
# Session ID builder
# ---------------------------------------------------------------------------


def build_session_id(client_ip: str) -> str:
    """
    Session key = IP. One session per device.

    Name is stored IN the session, not in the key.

    This way name changes (Mate → nickname → real name) don't
    require row migration. The row stays. The name evolves.
    """
    ip_part = client_ip.strip().replace(":", "_")  # handle IPv6
    return f"session_{ip_part}"


# ---------------------------------------------------------------------------
# Name source tracking — how she learned your name
# ---------------------------------------------------------------------------

NAME_SOURCES = {
    "default": "Mate — hasn't introduced themselves yet",
    "given": "They told her their name",
    "christened": "She earned a nickname for them",
}

# ---------------------------------------------------------------------------
# Load — get session from Postgres or return fresh defaults
# ---------------------------------------------------------------------------


def load_session(client_ip: str) -> Dict[str, Any]:
    """
    Load session by IP. If nothing exists, return fresh defaults.

    One IP = one session. Name lives inside the row.
    """
    sid = build_session_id(client_ip)
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT session_id, user_name, client_ip, name_source, "
                    "turn_count, whosonfirst, response_history, talk_served, social_state, "
                    "topics, created_at, updated_at "
                    "FROM banks_sessions WHERE session_id = %s",
                    (sid,),
                )
                row = cur.fetchone()
        if row:
            return _row_to_dict(row, cur.description)  # type: ignore[name-defined]
        return _fresh_session(client_ip)
    except Exception as e:
        logger.error("Failed to load session: %s", e)
        return _fresh_session(client_ip)


def _row_to_dict(row, description) -> Dict[str, Any]:
    """Convert a DB row to a dict."""
    cols = [col.name for col in description]
    d = dict(zip(cols, row))
    for key in ("response_history", "talk_served", "social_state", "topics"):
        if isinstance(d.get(key), str):
            d[key] = json.loads(d[key])
    return d


def _fresh_session(client_ip: str) -> Dict[str, Any]:
    """Default session state for a new visitor. Name = Mate."""
    return {
        "session_id": build_session_id(client_ip),
        "user_name": DEFAULT_NAME,
        "client_ip": client_ip,
        "name_source": "default",
        "turn_count": 0,
        "whosonfirst": True,
        "response_history": [],
        "talk_served": [],
        "social_state": {"user_status": 0.5, "self_status": 0.4},
        "topics": {},
        "created_at": None,
        "updated_at": None,
    }


# ---------------------------------------------------------------------------
# Save — upsert session state after every turn
# ---------------------------------------------------------------------------


def save_session(session: Dict[str, Any]) -> None:
    """
    Upsert session to Postgres. Called after every turn.

    Row keyed on IP. Name evolves in place.
    """
    sid = session["session_id"]
    sql = """
    INSERT INTO banks_sessions
        (session_id, user_name, client_ip, name_source, turn_count, whosonfirst,
         response_history, talk_served, social_state, topics,
         created_at, updated_at)
    VALUES
        (%s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb,
         now(), now())
    ON CONFLICT (session_id) DO UPDATE SET
        user_name      = EXCLUDED.user_name,
        name_source    = EXCLUDED.name_source,
        turn_count     = EXCLUDED.turn_count,
        whosonfirst    = EXCLUDED.whosonfirst,
        response_history = EXCLUDED.response_history,
        talk_served      = EXCLUDED.talk_served,
        social_state     = EXCLUDED.social_state,
        topics           = EXCLUDED.topics,
        updated_at       = now();
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql,
                    (
                        sid,
                        session.get("user_name", DEFAULT_NAME),
                        session["client_ip"],
                        session.get("name_source", "default"),
                        session.get("turn_count", 0),
                        session.get("whosonfirst", True),
                        json.dumps(session.get("response_history", [])),
                        json.dumps(session.get("talk_served", [])),
                        json.dumps(session.get("social_state", {})),
                        json.dumps(session.get("topics", {})),
                    ),
                )
            conn.commit()
        logger.info(
            "Session saved: %s [%s] (turn %d)",
            sid,
            session.get("user_name"),
            session.get("turn_count", 0),
        )
    except Exception as e:
        logger.error("Failed to save session: %s", e)


# ---------------------------------------------------------------------------
# Name updates — Mate → nickname → real name
# ---------------------------------------------------------------------------


def update_name(session: Dict[str, Any], new_name: str, source: str) -> Dict[str, Any]:
    """
    Update the user's name. No row migration needed.

    The session stays. The name evolves in place.

    source: "given" (they told us) or "christened" (she nicknamed them)

    Priority: given > christened > default

    If they already gave their real name, a nickname won't overwrite it.
    """
    current_source = session.get("name_source", "default")

    # Real name always wins. Don't overwrite a given name with a nickname.
    if current_source == "given" and source == "christened":
        logger.info(
            "Skipping nickname — already have given name: %s",
            session.get("user_name"),
        )
        return session

    session["user_name"] = new_name.strip().capitalize() if new_name else DEFAULT_NAME
    session["name_source"] = source
    logger.info("Name updated: %s (source: %s)", session["user_name"], source)
    return session


# ---------------------------------------------------------------------------
# Topic tracking — fuel for The Christening
# ---------------------------------------------------------------------------


def record_topics(session: Dict[str, Any], domains: List[str], tags: List[str]) -> Dict[str, Any]:
    """
    Increment topic counters. This is what The Christening reads

    when deciding if there's enough signal for a nickname.

    topics = {
        "domains": {"music": 12, "physics": 3, ...},
        "tags": {"truth": 5, "beauty_humor": 8, ...},
    }
    """
    topics = session.get("topics", {})
    if "domains" not in topics:
        topics["domains"] = {}
    if "tags" not in topics:
        topics["tags"] = {}

    for d in domains:
        if d:
            topics["domains"][d] = topics["domains"].get(d, 0) + 1

    for t in tags:
        if t and t != "ordinary":
            topics["tags"][t] = topics["tags"].get(t, 0) + 1

    session["topics"] = topics
    return session


# ---------------------------------------------------------------------------
# IP extraction — handles Railway proxy
# ---------------------------------------------------------------------------


def get_client_ip(request) -> str:
    """
    Extract real client IP from a FastAPI Request.

    Handles Railway/proxy x-forwarded-for headers.
    """
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


# ---------------------------------------------------------------------------
# Reference resolution — “when you said account just now…”
# ---------------------------------------------------------------------------

_REFERENCE_TRIGGERS = [
    "when you said",
    "when you were saying",
    "what you said",
    "back when you said",
    "earlier you said",
    "when you talked about",
    "when you mentioned",
]


def _extract_reference_keyword(user_text: str) -> Optional[str]:
    """
    Heuristic: try to pull a key word/phrase after phrases like 'when you said'.

    If we can't find anything clean, return None and fall back to broader match.
    """
    text = user_text.lower()
    for trig in _REFERENCE_TRIGGERS:
        idx = text.find(trig)
        if idx == -1:
            continue
        after = text[idx + len(trig) :].strip()
        if after.startswith("that"):
            after = after[4:].strip()
        # Grab up to first punctuation or ~5 words.
        chunk = re.split(r"[.?!,]", after, maxsplit=1)[0]
        words = chunk.split()
        if not words:
            continue
        # Take up to 3 words as a phrase, drop pronouns/fillers.
        filtered = [w for w in words[:5] if w not in {"you", "just", "now", "that", "the"}]
        if not filtered:
            continue
        return " ".join(filtered)
    return None


def _score_match(candidate: str, keyword: Optional[str], user_text: str) -> float:
    """
    Very cheap relevance score: keyword hit + lexical overlap.

    We don't need perfection; we just need the right beat most of the time.
    """
    c_low = candidate.lower()
    u_low = user_text.lower()

    score = 0.0

    if keyword and keyword in c_low:
        score += 1.0

    # tiny Jaccard-ish overlap on non-stopwords
    def tokens(s: str) -> List[str]:
        return [w for w in re.findall(r"[a-z0-9]+", s.lower()) if w not in {"you", "i", "the", "and", "a", "to"}]

    c_toks = set(tokens(candidate))
    u_toks = set(tokens(u_low))
    if c_toks and u_toks:
        overlap = len(c_toks & u_toks) / max(len(c_toks), 1)
        score += overlap

    return score


def resolve_reference(session: Dict[str, Any], user_text: str) -> Optional[Dict[str, Any]]:
    """
    Try to resolve 'when you said X…' style references against response_history.

    Returns:
        {
          "turn": <int>,          # index in response_history (0-based)
          "text": <str>,          # RILIE's earlier utterance
          "keyword": <str|None>,  # extracted focus, e.g. 'account'
        }
    or None if nothing obvious is found.

    This does NOT change session; it just reads from it.
    """
    text_lower = user_text.lower()
    if not any(t in text_lower for t in _REFERENCE_TRIGGERS):
        return None

    history = session.get("response_history", []) or []
    if not history:
        return None

    keyword = _extract_reference_keyword(user_text)

    best_idx: Optional[int] = None
    best_score = 0.0

    # Newest → oldest so recent beats win ties.
    for idx in range(len(history) - 1, -1, -1):
        candidate = history[idx]
        if not isinstance(candidate, str) or not candidate.strip():
            continue
        score = _score_match(candidate, keyword, user_text)
        if score > best_score:
            best_score = score
            best_idx = idx

    if best_idx is None or best_score <= 0.0:
        return None

    return {
        "turn": best_idx,
        "text": history[best_idx],
        "keyword": keyword,
    }


# ---------------------------------------------------------------------------
# Guvna state ↔ session wiring
# ---------------------------------------------------------------------------


def restore_guvna_state(guvna, session: Dict[str, Any]) -> None:
    """Load session state back into the Guvna instance."""
    guvna.turn_count = session.get("turn_count", 0)
    guvna.user_name = session.get("user_name", DEFAULT_NAME)
    guvna.whosonfirst = session.get("whosonfirst", True)
    guvna._response_history = list(session.get("response_history", []))

    social = session.get("social_state", {})
    if social:
        guvna.social_state.user_status = social.get("user_status", 0.5)
        guvna.social_state.self_status = social.get("self_status", 0.4)

    # Keep memory turn count in sync
    guvna.memory.turn_count = session.get("turn_count", 0)
    guvna.memory.user_name = session.get("user_name", DEFAULT_NAME)


def snapshot_guvna_state(guvna, session: Dict[str, Any]) -> Dict[str, Any]:
    """Capture current Guvna state back into the session dict."""
    session["turn_count"] = guvna.turn_count
    session["whosonfirst"] = guvna.whosonfirst
    session["response_history"] = guvna._response_history[-20:]  # cap at 20
    session["social_state"] = {
        "user_status": guvna.social_state.user_status,
        "self_status": guvna.social_state.self_status,
    }

    # If guvna captured a name and it's not Mate, update session
    if (
        guvna.user_name
        and guvna.user_name != DEFAULT_NAME
        and session.get("name_source") == "default"
    ):
        session = update_name(session, guvna.user_name, "given")

    return session


# ---------------------------------------------------------------------------
# TalkMemory ↔ session wiring
# ---------------------------------------------------------------------------


def restore_talk_memory(talk_memory, session: Dict[str, Any]) -> None:
    """Load served history back into TalkMemory."""
    talk_memory.served = list(session.get("talk_served", []))


def snapshot_talk_memory(talk_memory, session: Dict[str, Any]) -> Dict[str, Any]:
    """Capture TalkMemory state into the session dict."""
    session["talk_served"] = talk_memory.served[-20:]  # cap at 20
    return session
