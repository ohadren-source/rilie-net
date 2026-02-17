"""
BANKS COMPARISON LOG (append to banks.py)
==========================================
Track MI → RR vs GR comparisons.
Learn which responses work better for each user/context.

Table: banks_mi_gr_comparisons
- stimulus: raw input
- mi_object: what it's about (irreducible subject)
- mi_weight: how much it matters to user
- rr_text: RILIE's response
- rr_harmony: RILIE harmony score
- gr_text: Google synthesized response
- gr_harmony: Google harmony score
- selected: which won ("RR" or "GR")
- confidence: how sure (0.0-1.0)
- margin: score difference
- session_id: user identifier
- created_at: timestamp
"""

import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("banks_comparison_log")


def ensure_comparison_log_table() -> None:
    """
    Idempotently create banks_mi_gr_comparisons if it doesn't exist yet.
    Safe to call on every startup. Same pattern as other banks tables.
    """
    from banks import get_db_conn
    
    sql = """
    CREATE TABLE IF NOT EXISTS banks_mi_gr_comparisons (
        id                  SERIAL PRIMARY KEY,
        stimulus            TEXT NOT NULL,
        mi_object           TEXT,
        mi_weight           FLOAT DEFAULT 0.5,
        mi_act              VARCHAR(10),
        mi_gap              TEXT,
        rr_text             TEXT NOT NULL,
        rr_harmony          FLOAT DEFAULT 0.0,
        rr_syncopation      FLOAT DEFAULT 0.0,
        rr_synchronicity    FLOAT DEFAULT 0.0,
        gr_text             TEXT,
        gr_harmony          FLOAT DEFAULT 0.0,
        gr_syncopation      FLOAT DEFAULT 0.0,
        gr_synchronicity    FLOAT DEFAULT 0.0,
        selected            VARCHAR(3) CHECK (selected IN ('RR', 'GR')),
        confidence          FLOAT DEFAULT 0.5,
        margin              FLOAT DEFAULT 0.0,
        session_id          TEXT,
        user_name           TEXT,
        created_at          TIMESTAMPTZ DEFAULT now()
    );

    CREATE INDEX IF NOT EXISTS idx_comparisons_selected
        ON banks_mi_gr_comparisons (selected);
    
    CREATE INDEX IF NOT EXISTS idx_comparisons_session
        ON banks_mi_gr_comparisons (session_id);
    
    CREATE INDEX IF NOT EXISTS idx_comparisons_mi_object
        ON banks_mi_gr_comparisons (mi_object);
    
    CREATE INDEX IF NOT EXISTS idx_comparisons_fts
        ON banks_mi_gr_comparisons
        USING gin(to_tsvector('english',
            coalesce(stimulus,'') || ' ' ||
            coalesce(mi_object,'') || ' ' ||
            coalesce(rr_text,'')));
    """
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
        logger.info("banks_mi_gr_comparisons table ensured.")
    except Exception as e:
        logger.warning("Could not ensure comparison log table: %s", e)


def log_comparison(
    stimulus: str,
    mi_fingerprint: Optional[Any] = None,
    comparison_result: Optional[Any] = None,
    session_id: Optional[str] = None,
    user_name: Optional[str] = None,
) -> bool:
    """
    Log a MI→RR vs GR comparison to the database.
    
    Args:
        stimulus: Raw input
        mi_fingerprint: MeaningFingerprint object (has .object, .weight, .act, .gap)
        comparison_result: ComparisonResult object (from mi_gr_compare.py)
        session_id: User session identifier
        user_name: User name (if known)
    
    Returns:
        True if logged successfully, False otherwise
    """
    from banks import get_db_conn
    
    if not comparison_result or not mi_fingerprint:
        logger.warning("Missing comparison_result or mi_fingerprint, skipping log")
        return False
    
    try:
        sql = """
        INSERT INTO banks_mi_gr_comparisons
            (stimulus, mi_object, mi_weight, mi_act, mi_gap,
             rr_text, rr_harmony, rr_syncopation, rr_synchronicity,
             gr_text, gr_harmony, gr_syncopation, gr_synchronicity,
             selected, confidence, margin, session_id, user_name)
        VALUES
            (%s, %s, %s, %s, %s,
             %s, %s, %s, %s,
             %s, %s, %s, %s,
             %s, %s, %s, %s, %s)
        """
        
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (
                    stimulus[:500],  # cap at 500 chars
                    mi_fingerprint.object if mi_fingerprint else None,
                    mi_fingerprint.weight if mi_fingerprint else 0.5,
                    mi_fingerprint.act if mi_fingerprint else None,
                    mi_fingerprint.gap if mi_fingerprint else None,
                    comparison_result.rr_text[:1000],  # cap RR
                    comparison_result.rr_harmony,
                    comparison_result.rr_syncopation,
                    comparison_result.rr_synchronicity,
                    comparison_result.gr_text[:1000] if comparison_result.gr_text else None,  # cap GR
                    comparison_result.gr_harmony,
                    comparison_result.gr_syncopation,
                    comparison_result.gr_synchronicity,
                    comparison_result.selected,
                    comparison_result.confidence,
                    comparison_result.margin,
                    session_id,
                    user_name,
                ))
            conn.commit()
        
        logger.info(
            "Comparison logged: %s (selected=%s, confidence=%.2f)",
            stimulus[:60], comparison_result.selected, comparison_result.confidence
        )
        return True
    
    except Exception as e:
        logger.error("Failed to log comparison: %s", e)
        return False


def get_comparison_stats(session_id: str) -> Dict[str, Any]:
    """
    Get RR vs GR stats for a session.
    Which won more often? What's the average margin?
    """
    from banks import get_db_conn
    
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        selected,
                        COUNT(*) as count,
                        AVG(confidence) as avg_confidence,
                        AVG(margin) as avg_margin,
                        AVG(rr_harmony) as avg_rr_harmony,
                        AVG(gr_harmony) as avg_gr_harmony
                    FROM banks_mi_gr_comparisons
                    WHERE session_id = %s
                    GROUP BY selected
                """, (session_id,))
                
                rows = cur.fetchall()
                stats = {}
                for row in rows:
                    selected, count, avg_conf, avg_margin, avg_rr, avg_gr = row
                    stats[selected] = {
                        "count": count,
                        "avg_confidence": avg_conf,
                        "avg_margin": avg_margin,
                        "avg_rr_harmony": avg_rr,
                        "avg_gr_harmony": avg_gr,
                    }
                
                return stats
    
    except Exception as e:
        logger.error("Failed to get comparison stats: %s", e)
        return {}
