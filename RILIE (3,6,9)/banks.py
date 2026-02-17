"""
banks.py — BANKS search result store + Curiosity Engine + Self-Awareness Store
================================================================================
Thin Postgres helper for:
  - Storing multi-lens search results (city × channel) into banks_search_results.
  - Querying BANKS later by keywords instead of hitting Brave every time.
  - Storing and retrieving RILIE's self-generated curiosity insights.
  - Storing self-reflection events (when RILIE talks about herself).
  - Logging CATCH44 DNA violations for audit and learning.
  - Tracking domain lens usage patterns per query.

Assumes:
  - A Postgres DATABASE_URL in the environment, e.g.
    postgres://user:password@host:5432/rilie_prod
  - Table banks_search_results already created by migration V001.
  - Table banks_curiosity created by migration V002 (see ensure_curiosity_table).
  - Table banks_self_reflection created by migration V003 (see ensure_self_reflection_table).
  - Table banks_dna_log created by migration V004 (see ensure_dna_log_table).
  - Table banks_domain_usage created by migration V005 (see ensure_domain_usage_table).
"""

import os
import logging
import datetime
from typing import List, Dict, Optional, Callable, Any

import psycopg2
import psycopg2.extras

logger = logging.getLogger("banks")

# ---------------------------------------------------------------------------
# Connection helper
# ---------------------------------------------------------------------------

def get_db_conn():
    """
    Open a new Postgres connection using DATABASE_URL.
    You can later swap this for a connection pool if needed.
    """
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL is not set in environment.")
    return psycopg2.connect(db_url)


# ---------------------------------------------------------------------------
# Auto-create curiosity table if it doesn't exist
# ---------------------------------------------------------------------------

def ensure_curiosity_table():
    """
    Idempotently create banks_curiosity if it doesn't exist yet.
    Safe to call on every startup.
    """
    sql = """
        CREATE TABLE IF NOT EXISTS banks_curiosity (
            id              SERIAL PRIMARY KEY,
            origin          TEXT NOT NULL DEFAULT 'curiosity',
            seed_query      TEXT,
            tangent         TEXT NOT NULL,
            research        TEXT,
            insight         TEXT,
            quality_score   FLOAT DEFAULT 0.0,
            kept            BOOLEAN DEFAULT FALSE,
            created_at      TIMESTAMPTZ DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_curiosity_kept
            ON banks_curiosity (kept) WHERE kept = TRUE;
        CREATE INDEX IF NOT EXISTS idx_curiosity_fts
            ON banks_curiosity
            USING gin(to_tsvector('english',
                coalesce(tangent,'') || ' ' ||
                coalesce(insight,'') || ' ' ||
                coalesce(seed_query,'')));
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
        logger.info("banks_curiosity table ensured.")
    except Exception as e:
        logger.warning("Could not ensure curiosity table: %s", e)


# ---------------------------------------------------------------------------
# Auto-create self-reflection table
# ---------------------------------------------------------------------------

def ensure_self_reflection_table():
    """
    Idempotently create banks_self_reflection if it doesn't exist yet.
    Stores moments when RILIE reflected on her own identity, capability,
    or state — the _is_about_me fast path in Guvna.

    This lets her learn from her own self-assessments over time.
    Safe to call on every startup.
    """
    sql = """
        CREATE TABLE IF NOT EXISTS banks_self_reflection (
            id              SERIAL PRIMARY KEY,
            stimulus         TEXT NOT NULL,
            reflection       TEXT NOT NULL,
            cluster_type     TEXT DEFAULT 'identity',
            quality_score    FLOAT DEFAULT 0.0,
            self_status      FLOAT DEFAULT 0.4,
            user_status      FLOAT DEFAULT 0.7,
            dna_passed       BOOLEAN DEFAULT TRUE,
            created_at       TIMESTAMPTZ DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_self_reflection_cluster
            ON banks_self_reflection (cluster_type);
        CREATE INDEX IF NOT EXISTS idx_self_reflection_fts
            ON banks_self_reflection
            USING gin(to_tsvector('english',
                coalesce(stimulus,'') || ' ' ||
                coalesce(reflection,'')));
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
        logger.info("banks_self_reflection table ensured.")
    except Exception as e:
        logger.warning("Could not ensure self_reflection table: %s", e)


# ---------------------------------------------------------------------------
# Auto-create DNA violation log table
# ---------------------------------------------------------------------------

def ensure_dna_log_table():
    """
    Idempotently create banks_dna_log if it doesn't exist yet.
    Records every CATCH44DNA violation for audit and pattern detection.

    If RILIE keeps tripping MAHVEEN_VIOLATION on certain topics, that's
    signal — she's overclaiming in a domain she doesn't have evidence for.
    Safe to call on every startup.
    """
    sql = """
        CREATE TABLE IF NOT EXISTS banks_dna_log (
            id              SERIAL PRIMARY KEY,
            action_name      TEXT NOT NULL,
            violation_type   TEXT NOT NULL,
            claim            FLOAT,
            realistic_max    FLOAT,
            resource_usage   FLOAT,
            quality_target   FLOAT,
            ego_factor       FLOAT,
            stimulus_hash    TEXT,
            created_at       TIMESTAMPTZ DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_dna_log_violation
            ON banks_dna_log (violation_type);
        CREATE INDEX IF NOT EXISTS idx_dna_log_action
            ON banks_dna_log (action_name);
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
        logger.info("banks_dna_log table ensured.")
    except Exception as e:
        logger.warning("Could not ensure dna_log table: %s", e)


# ---------------------------------------------------------------------------
# Auto-create domain usage tracking table
# ---------------------------------------------------------------------------

def ensure_domain_usage_table():
    """
    Idempotently create banks_domain_usage if it doesn't exist yet.
    Tracks which domain engines RILIE reaches for per query.

    Over time this shows her patterns — does she lean too hard on
    thermodynamics? Never use games? That's signal for rebalancing.
    Safe to call on every startup.
    """
    sql = """
        CREATE TABLE IF NOT EXISTS banks_domain_usage (
            id              SERIAL PRIMARY KEY,
            stimulus_hash    TEXT,
            domain_name      TEXT NOT NULL,
            matched_tags     TEXT[],
            functions_available INT DEFAULT 0,
            dna_approved     BOOLEAN DEFAULT TRUE,
            skip_reason      TEXT,
            created_at       TIMESTAMPTZ DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_domain_usage_domain
            ON banks_domain_usage (domain_name);
        CREATE INDEX IF NOT EXISTS idx_domain_usage_approved
            ON banks_domain_usage (dna_approved);
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
        logger.info("banks_domain_usage table ensured.")
    except Exception as e:
        logger.warning("Could not ensure domain_usage table: %s", e)


# ---------------------------------------------------------------------------
# Ensure ALL tables — single call for startup
# ---------------------------------------------------------------------------

def ensure_all_tables():
    """
    Ensure all BANKS tables exist. Call once on startup.
    Graceful — each table creation is independent.
    """
    ensure_curiosity_table()
    ensure_self_reflection_table()
    ensure_dna_log_table()
    ensure_domain_usage_table()


# ---------------------------------------------------------------------------
# Core write path — store Brave/Google results into BANKS
# ---------------------------------------------------------------------------

def store_search_results(
    query_text: str,
    lens_city: str,
    lens_channel: str,
    provider: str,
    results: List[Dict[str, str]],
    fetched_at: Optional[datetime.datetime] = None,
) -> int:
    """
    Insert a list of search results into banks_search_results.

    Args:
        query_text:  original user question (trimmed).
        lens_city:   e.g. 'Brooklyn', 'New Orleans', 'Paris, France'.
        lens_channel: e.g. 'mind', 'body', 'soul', 'food', 'music', 'funny', 'film'.
        provider:    e.g. 'brave'.
        results:     list of dicts with at least keys 'title', 'snippet', 'link'.
        fetched_at:  override timestamp; defaults to now() if None.

    Returns:
        Number of rows inserted.
    """
    if fetched_at is None:
        fetched_at = datetime.datetime.utcnow()

    if not results:
        return 0

    rows = []
    for idx, r in enumerate(results, start=1):
        rows.append((
            query_text.strip(),
            lens_city,
            lens_channel,
            provider,
            idx,  # result_rank
            (r.get("title") or "").strip(),
            (r.get("snippet") or "").strip(),
            (r.get("link") or "").strip(),
            fetched_at,
            None,  # status_code (optional)
            None,  # raw_json (optional)
        ))

    sql = """
        INSERT INTO banks_search_results
            (query_text, lens_city, lens_channel, provider,
             result_rank, title, snippet, url, fetched_at,
             status_code, raw_json)
        VALUES
            %s
    """

    with get_db_conn() as conn:
        with conn.cursor() as cur:
            psycopg2.extras.execute_values(
                cur,
                sql,
                rows,
                template="(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            )
        conn.commit()

    return len(rows)


# ---------------------------------------------------------------------------
# Read path — search BANKS by keywords
# ---------------------------------------------------------------------------

def search_banks_by_keywords(
    query_text: str,
    lens_city: Optional[str] = None,
    lens_channel: Optional[str] = None,
    limit: int = 9,
) -> List[Dict[str, str]]:
    """
    Search BANKS for rows relevant to a query using Postgres full-text search.
    """
    ts_query = query_text.strip()
    if not ts_query:
        return []

    base_sql = """
        SELECT
            title,
            snippet,
            url,
            lens_city,
            lens_channel,
            provider,
            result_rank,
            fetched_at
        FROM banks_search_results
        WHERE
            to_tsvector('english', coalesce(query_text,\'\') || ' ' || coalesce(title,\'\') || ' ' || coalesce(snippet,\'\')) @@
            plainto_tsquery('english', %s)
    """

    params: List = [ts_query]

    if lens_city:
        base_sql += " AND lens_city = %s"
        params.append(lens_city)
    if lens_channel:
        base_sql += " AND lens_channel = %s"
        params.append(lens_channel)

    base_sql += " ORDER BY fetched_at DESC, result_rank ASC LIMIT %s"
    params.append(limit)

    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(base_sql, params)
            rows = cur.fetchall()

    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Curiosity Engine — RILIE's subconscious
# ---------------------------------------------------------------------------

# Minimum quality score for a curiosity insight to be kept
CURIOSITY_TASTE_THRESHOLD = 0.6

def store_curiosity(
    seed_query: str,
    tangent: str,
    research: str,
    insight: str,
    quality_score: float,
    origin: str = "curiosity",
) -> bool:
    """
    Store a self-generated insight into banks_curiosity.
    Only marks 'kept = TRUE' if quality_score meets the taste threshold.

    Args:
        seed_query:     the original user query that sparked the tangent.
        tangent:        what she got curious about.
        research:       raw material she found (Brave snippets, etc.).
        insight:        her Triangle-processed conclusion.
        quality_score:  how good the insight is (0.0 - 1.0).
        origin:         'curiosity' | 'reflection' | 'connection'.

    Returns:
        True if the insight was kept (passed taste), False if stored but not kept.
    """
    kept = quality_score >= CURIOSITY_TASTE_THRESHOLD

    sql = """
        INSERT INTO banks_curiosity
            (origin, seed_query, tangent, research, insight, quality_score, kept)
        VALUES
            (%s, %s, %s, %s, %s, %s, %s)
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (origin, seed_query, tangent,
                                  research, insight, quality_score, kept))
            conn.commit()
        logger.info("Curiosity stored [kept=%s, score=%.2f]: %s",
                     kept, quality_score, tangent[:80])
    except Exception as e:
        logger.error("Failed to store curiosity: %s", e)
        return False

    return kept


def search_curiosity(
    query_text: str,
    limit: int = 5,
) -> List[Dict]:
    """
    Search RILIE's own self-generated insights — things she discovered
    on her own time, not from a user prompt.

    Only returns kept insights (passed taste threshold).
    Ordered by quality descending, then recency.
    """
    ts_query = query_text.strip()
    if not ts_query:
        return []

    sql = """
        SELECT
            id,
            origin,
            seed_query,
            tangent,
            insight,
            quality_score,
            created_at
        FROM banks_curiosity
        WHERE kept = TRUE
          AND to_tsvector('english',
              coalesce(tangent,'') || ' ' ||
              coalesce(insight,'') || ' ' ||
              coalesce(seed_query,''))
          @@ plainto_tsquery('english', %s)
        ORDER BY quality_score DESC, created_at DESC
        LIMIT %s
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(sql, (ts_query, limit))
                rows = cur.fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.error("Failed to search curiosity: %s", e)
        return []


def get_curiosity_stats() -> Dict:
    """
    Quick stats on the curiosity engine — how many total, how many kept,
    average quality. Useful for health checks and the UI.
    """
    sql = """
        SELECT
            COUNT(*)                          AS total,
            COUNT(*) FILTER (WHERE kept)      AS kept,
            COALESCE(AVG(quality_score), 0)   AS avg_quality,
            MAX(created_at)                   AS last_curiosity
        FROM banks_curiosity
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(sql)
                row = cur.fetchone()
        return dict(row) if row else {"total": 0, "kept": 0, "avg_quality": 0.0, "last_curiosity": None}
    except Exception as e:
        logger.error("Failed to get curiosity stats: %s", e)
        return {"total": 0, "kept": 0, "avg_quality": 0.0, "last_curiosity": None}


def search_all_banks(
    query_text: str,
    limit: int = 9,
) -> Dict[str, List[Dict]]:
    """
    Unified search across BOTH banks_search_results AND banks_curiosity.
    Returns a dict with two keys: 'search_results' and 'curiosity'.

    This is the function RILIE should call during her passes —
    she gets everything: user-prompted research AND her own discoveries.
    """
    search_hits = search_banks_by_keywords(query_text, limit=limit)
    curiosity_hits = search_curiosity(query_text, limit=5)

    return {
        "search_results": search_hits,
        "curiosity": curiosity_hits,
    }


# ---------------------------------------------------------------------------
# Self-Reflection Store — RILIE's mirror
# ---------------------------------------------------------------------------

def store_self_reflection(
    stimulus: str,
    reflection: str,
    cluster_type: str = "identity",
    quality_score: float = 0.0,
    self_status: float = 0.4,
    user_status: float = 0.7,
    dna_passed: bool = True,
) -> bool:
    """
    Store a self-reflection event — when RILIE reflected on her own
    identity, capability, or state via the _is_about_me fast path.

    Args:
        stimulus:       what the user said that triggered self-reflection.
        reflection:     what RILIE said about herself.
        cluster_type:   which semantic cluster matched ('identity', 'capability',
                        'feeling', 'origin', 'meta').
        quality_score:  her self-assessed quality at time of reflection.
        self_status:    her social self_status at time of reflection.
        user_status:    inferred user_status at time of reflection.
        dna_passed:     whether the reflection action passed DNA validation.

    Returns:
        True if stored successfully, False on error.
    """
    sql = """
        INSERT INTO banks_self_reflection
            (stimulus, reflection, cluster_type, quality_score,
             self_status, user_status, dna_passed)
        VALUES
            (%s, %s, %s, %s, %s, %s, %s)
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (stimulus, reflection, cluster_type,
                                  quality_score, self_status, user_status,
                                  dna_passed))
            conn.commit()
        logger.info("Self-reflection stored [cluster=%s, dna=%s]: %s",
                     cluster_type, dna_passed, stimulus[:60])
        return True
    except Exception as e:
        logger.error("Failed to store self-reflection: %s", e)
        return False


def search_self_reflections(
    query_text: str,
    cluster_type: Optional[str] = None,
    limit: int = 5,
) -> List[Dict]:
    """
    Search RILIE's self-reflections — what has she said about herself?

    Useful for:
    - Consistency: is she describing herself the same way over time?
    - Growth: is her quality_score trending up?
    - Pattern: which clusters trigger self-reflection most?
    """
    ts_query = query_text.strip()
    if not ts_query:
        return []

    sql = """
        SELECT
            id,
            stimulus,
            reflection,
            cluster_type,
            quality_score,
            self_status,
            user_status,
            dna_passed,
            created_at
        FROM banks_self_reflection
        WHERE to_tsvector('english',
              coalesce(stimulus,'') || ' ' ||
              coalesce(reflection,''))
          @@ plainto_tsquery('english', %s)
    """
    params: List[Any] = [ts_query]

    if cluster_type:
        sql += " AND cluster_type = %s"
        params.append(cluster_type)

    sql += " ORDER BY created_at DESC LIMIT %s"
    params.append(limit)

    try:
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.error("Failed to search self-reflections: %s", e)
        return []


def get_self_reflection_stats() -> Dict:
    """
    Stats on RILIE's self-reflection patterns.
    How often does she reflect? Which clusters? DNA pass rate?
    """
    sql = """
        SELECT
            COUNT(*)                                AS total,
            COUNT(*) FILTER (WHERE dna_passed)      AS dna_passed,
            COUNT(*) FILTER (WHERE NOT dna_passed)   AS dna_failed,
            COALESCE(AVG(quality_score), 0)          AS avg_quality,
            MAX(created_at)                          AS last_reflection
        FROM banks_self_reflection
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(sql)
                row = cur.fetchone()
        return dict(row) if row else {
            "total": 0, "dna_passed": 0, "dna_failed": 0,
            "avg_quality": 0.0, "last_reflection": None,
        }
    except Exception as e:
        logger.error("Failed to get self-reflection stats: %s", e)
        return {
            "total": 0, "dna_passed": 0, "dna_failed": 0,
            "avg_quality": 0.0, "last_reflection": None,
        }


# ---------------------------------------------------------------------------
# DNA Violation Log — CATCH44 audit trail
# ---------------------------------------------------------------------------

def log_dna_violation(
    action_name: str,
    violation_type: str,
    claim: float = 0.0,
    realistic_max: float = 0.0,
    resource_usage: float = 0.0,
    quality_target: float = 0.0,
    ego_factor: float = 0.0,
    stimulus_hash: str = "",
) -> bool:
    """
    Log a CATCH44DNA violation for audit.

    Over time, patterns emerge:
    - Frequent MAHVEEN_VIOLATION = she's overclaiming
    - Frequent WEI_VIOLATION = she's monopolizing reasoning on one thread
    - Frequent EGO_VIOLATION = her responses are becoming self-centered

    Args:
        action_name:     what she was trying to do (e.g., 'thermo_probe').
        violation_type:  which DNA check failed (e.g., 'MAHVEEN_VIOLATION').
        claim:           the claim strength that was rejected.
        realistic_max:   the realistic maximum that was exceeded.
        resource_usage:  the resource % that was too high.
        quality_target:  the quality target that was too low.
        ego_factor:      the ego score that was too high.
        stimulus_hash:   hash of the stimulus (for correlation, not the text itself).

    Returns:
        True if logged successfully, False on error.
    """
    sql = """
        INSERT INTO banks_dna_log
            (action_name, violation_type, claim, realistic_max,
             resource_usage, quality_target, ego_factor, stimulus_hash)
        VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (action_name, violation_type, claim,
                                  realistic_max, resource_usage,
                                  quality_target, ego_factor, stimulus_hash))
            conn.commit()
        logger.info("DNA violation logged [%s]: %s (claim=%.2f, max=%.2f)",
                     violation_type, action_name, claim, realistic_max)
        return True
    except Exception as e:
        logger.error("Failed to log DNA violation: %s", e)
        return False


def get_dna_violation_stats() -> Dict:
    """
    Stats on DNA violations — which types, how frequent, trending?
    """
    sql = """
        SELECT
            COUNT(*)                                          AS total,
            COUNT(*) FILTER (WHERE violation_type = 'MAHVEEN_VIOLATION')  AS mahveen,
            COUNT(*) FILTER (WHERE violation_type = 'WEI_VIOLATION')      AS wei,
            COUNT(*) FILTER (WHERE violation_type = 'QUALITY_VIOLATION')  AS quality,
            COUNT(*) FILTER (WHERE violation_type = 'EGO_VIOLATION')      AS ego,
            MAX(created_at)                                   AS last_violation
        FROM banks_dna_log
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(sql)
                row = cur.fetchone()
        return dict(row) if row else {
            "total": 0, "mahveen": 0, "wei": 0,
            "quality": 0, "ego": 0, "last_violation": None,
        }
    except Exception as e:
        logger.error("Failed to get DNA violation stats: %s", e)
        return {
            "total": 0, "mahveen": 0, "wei": 0,
            "quality": 0, "ego": 0, "last_violation": None,
        }


# ---------------------------------------------------------------------------
# Domain Usage Tracking — which engines does she reach for?
# ---------------------------------------------------------------------------

def store_domain_usage(
    stimulus_hash: str,
    domain_name: str,
    matched_tags: List[str],
    functions_available: int = 0,
    dna_approved: bool = True,
    skip_reason: str = "",
) -> bool:
    """
    Record that RILIE reached for (or was blocked from) a domain engine.

    Args:
        stimulus_hash:       hash of the stimulus (for correlation).
        domain_name:         which domain (e.g., 'physics', 'thermodynamics').
        matched_tags:        which tags in the domain matched the stimulus.
        functions_available: how many functions were available in that domain.
        dna_approved:        whether DNA approved the domain probe.
        skip_reason:         if DNA blocked it, why.

    Returns:
        True if stored successfully, False on error.
    """
    sql = """
        INSERT INTO banks_domain_usage
            (stimulus_hash, domain_name, matched_tags,
             functions_available, dna_approved, skip_reason)
        VALUES
            (%s, %s, %s, %s, %s, %s)
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (stimulus_hash, domain_name, matched_tags,
                                  functions_available, dna_approved, skip_reason))
            conn.commit()
        logger.info("Domain usage stored [%s, approved=%s]: %s",
                     domain_name, dna_approved, ", ".join(matched_tags[:3]))
        return True
    except Exception as e:
        logger.error("Failed to store domain usage: %s", e)
        return False


def get_domain_usage_stats() -> Dict:
    """
    Stats on domain engine usage — which engines does she lean on most?
    Which get DNA-blocked most? Where are her blind spots?
    """
    sql = """
        SELECT
            domain_name,
            COUNT(*)                                  AS total_uses,
            COUNT(*) FILTER (WHERE dna_approved)      AS approved,
            COUNT(*) FILTER (WHERE NOT dna_approved)  AS blocked
        FROM banks_domain_usage
        GROUP BY domain_name
        ORDER BY total_uses DESC
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(sql)
                rows = cur.fetchall()
        return {
            "domains": [dict(r) for r in rows],
            "total_probes": sum(dict(r)["total_uses"] for r in rows) if rows else 0,
        }
    except Exception as e:
        logger.error("Failed to get domain usage stats: %s", e)
        return {"domains": [], "total_probes": 0}


# ---------------------------------------------------------------------------
# Unified search — everything RILIE knows
# ---------------------------------------------------------------------------

def search_all_banks(
    query_text: str,
    limit: int = 9,
) -> Dict[str, List[Dict]]:
    """
    Unified search across ALL banks tables:
    - banks_search_results (user-prompted research)
    - banks_curiosity (her own discoveries)
    - banks_self_reflection (what she's said about herself)

    This is the function RILIE should call during her passes —
    she gets everything: research, discoveries, AND self-knowledge.
    """
    search_hits = search_banks_by_keywords(query_text, limit=limit)
    curiosity_hits = search_curiosity(query_text, limit=5)
    reflection_hits = search_self_reflections(query_text, limit=3)

    return {
        "search_results": search_hits,
        "curiosity": curiosity_hits,
        "self_reflections": reflection_hits,
    }


# ---------------------------------------------------------------------------
# Unified stats — full BANKS health check
# ---------------------------------------------------------------------------

def get_all_banks_stats() -> Dict:
    """
    Comprehensive stats across all BANKS tables.
    One call to see everything: curiosity, self-reflection, DNA, domain usage.
    """
    return {
        "curiosity": get_curiosity_stats(),
        "self_reflection": get_self_reflection_stats(),
        "dna_violations": get_dna_violation_stats(),
        "domain_usage": get_domain_usage_stats(),
    }


# ---------------------------------------------------------------------------
# Convenience: store a full PRE-RESPONSE 3×3 grid
# ---------------------------------------------------------------------------

DEFAULT_CITIES = [
    "Brooklyn",
    "New Orleans",
    "Nice, France",
    "New York City",
    "Paris, France",
    "Manhattan",
    "Queens",
    "Bronx",
    "Los Angeles",
    "Miami",
    "Puerto Rico",
    "Dominican Republic",
    "Mexico",
    "Jamaica",
    "London, England",
]

DEFAULT_CHANNELS = [
    "mind",
    "body",
    "soul",
    "food",
    "music",
    "funny",
    "film",
]


def fanout_pre_response_queries(
    query_text: str,
    searchfn,
    cities: Optional[List[str]] = None,
    channels: Optional[List[str]] = None,
    per_query_results: int = 9,
    provider: str = "brave",
) -> int:
    """
    Implement the PRE-RESPONSE behavior on top of BANKS:
      - For each (city, channel) pair, build "query_text + city + channel".
      - Call the provided searchfn(query, numresults).
      - Store all results in banks_search_results.

    Returns:
        Total number of rows inserted.
    """
    cities = cities or DEFAULT_CITIES
    channels = channels or DEFAULT_CHANNELS
    total_inserted = 0

    for city in cities:
        for channel in channels:
            lens_query = f"{query_text.strip()} {city} {channel}"
            try:
                try:
                    results = searchfn(lens_query, per_query_results)
                except TypeError:
                    results = searchfn(lens_query)
            except Exception:
                continue

            if not results:
                continue

            inserted = store_search_results(
                query_text=query_text,
                lens_city=city,
                lens_channel=channel,
                provider=provider,
                results=results,
            )
            total_inserted += inserted

    return total_inserted
