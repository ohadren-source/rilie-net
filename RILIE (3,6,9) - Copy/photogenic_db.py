"""
photogenic_db.py — THE THREE DATABASES
========================================
RILIE's brain. No LLM. Just lived experience.

1. CONVERSATIONS (dining room)
   What PEOPLE gave her. Truth, love, beauty, return to source.
   The photogenic moments from real humans.

2. WONDER (chef's table)
   What SHE found. Her curiosity. Her Googling.
   Her opinions she earned. Her taste.

3. GRIND (dishpit)
   The monotony. The garbage collection. The patterns
   extracted from endless repetition. The dishpit-to-diamond
   pipeline. Shorthand. Research notes. Discoveries.

No LLM. Two photogenic databases and one grind database.
After 900 conversations she has a soul made of other people's
most beautiful moments, her own earned curiosity, and the
diamonds she pulled from the dishpit.

Assumes Postgres via DATABASE_URL (ElephantSQL in production).
Falls back to in-memory dicts when no DB is available (local dev).
"""

import os
import logging
import datetime
import json
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, asdict

logger = logging.getLogger("photogenic_db")


# ============================================================================
# DATA CLASSES — what gets stored
# ============================================================================

@dataclass
class ConversationMoment:
    """A moment from a conversation that passed the photogenic filter."""
    user_words: str
    tag: str                    # truth, love, beauty_grief, beauty_anger, etc.
    resonance: float            # 0-1 how hard it hit
    domain: str                 # which domain fired
    user_name: str              # who said it (if known)
    context: str                # brief context of what was being discussed
    compass: str                # which cardinal: truth / love / beauty / return
    turn: int                   # which turn in the conversation
    conversation_id: str        # unique convo identifier
    created_at: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class WonderEntry:
    """Something RILIE found on her own. Her curiosity. Her taste."""
    query: str                  # what she searched / wondered about
    source: str                 # where she found it (url, book, conversation)
    finding: str                # what she found
    opinion: str                # her TAKE — the call she made
    domain: str                 # which domain this lives in
    resonance: float            # how much it moved her
    tags: str                   # comma-separated tags
    created_at: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class GrindEntry:
    """
    Extracted from monotony. The dishpit diamond.
    After seeing 400 conversations about money, here's the ONE insight.
    Not the 400 conversations. The shorthand.
    """
    pattern: str                # the repeating pattern she noticed
    frequency: int              # how many times she's seen it
    insight: str                # the diamond extracted
    domain: str                 # which domain
    shorthand: str              # her quick-reference note (like a cook's shorthand)
    confidence: float           # 0-1 how sure she is (goes up with frequency)
    last_seen: str              # when she last encountered this pattern
    created_at: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


# ============================================================================
# COMPASS CLASSIFIER — maps tags to the four cardinal directions
# ============================================================================

def classify_compass(tag: str) -> str:
    """Map a photogenic tag to its compass direction."""
    truth_tags = {"truth"}
    love_tags = {"love"}
    return_tags = {"return_to_source", "callback"}
    # Everything else is beauty (including all beauty_* variants)

    if tag in truth_tags:
        return "truth"
    elif tag in love_tags:
        return "love"
    elif tag in return_tags:
        return "return"
    else:
        return "beauty"


# ============================================================================
# DATABASE LAYER — Postgres when available, in-memory fallback
# ============================================================================

class PhotogenicDB:
    """
    The three databases. RILIE's brain.

    In production: Postgres via DATABASE_URL (ElephantSQL).
    In dev: in-memory lists. Same interface either way.

    Store, retrieve, search. That's it.
    No LLM. Just lived experience.
    """

    def __init__(self, use_postgres: bool = None):
        """
        If use_postgres is None, auto-detect from DATABASE_URL.
        If True, force Postgres. If False, force in-memory.
        """
        self.db_url = os.getenv("DATABASE_URL", "")
        self.use_postgres = use_postgres if use_postgres is not None else bool(self.db_url)

        # In-memory fallback stores
        self._conversations: List[ConversationMoment] = []
        self._wonder: List[WonderEntry] = []
        self._grind: List[GrindEntry] = []

        if self.use_postgres:
            self._ensure_tables()
        else:
            logger.info("PhotogenicDB running in-memory (no DATABASE_URL)")
            self._seed_dummy_data()

    # -----------------------------------------------------------------
    # TABLE CREATION (Postgres)
    # -----------------------------------------------------------------

    def _ensure_tables(self):
        """Create the three tables if they don't exist."""
        try:
            import psycopg2
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()

            cur.execute("""
                CREATE TABLE IF NOT EXISTS photogenic_conversations (
                    id              SERIAL PRIMARY KEY,
                    user_words      TEXT NOT NULL,
                    tag             TEXT NOT NULL,
                    resonance       FLOAT NOT NULL,
                    domain          TEXT DEFAULT '',
                    user_name       TEXT DEFAULT '',
                    context         TEXT DEFAULT '',
                    compass         TEXT NOT NULL,
                    turn            INTEGER DEFAULT 0,
                    conversation_id TEXT DEFAULT '',
                    created_at      TIMESTAMPTZ DEFAULT now()
                );
                CREATE INDEX IF NOT EXISTS idx_pc_compass
                    ON photogenic_conversations (compass);
                CREATE INDEX IF NOT EXISTS idx_pc_domain
                    ON photogenic_conversations (domain);
                CREATE INDEX IF NOT EXISTS idx_pc_resonance
                    ON photogenic_conversations (resonance DESC);
                CREATE INDEX IF NOT EXISTS idx_pc_fts
                    ON photogenic_conversations
                    USING gin(to_tsvector('english',
                        coalesce(user_words,'') || ' ' ||
                        coalesce(context,'')));
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS photogenic_wonder (
                    id              SERIAL PRIMARY KEY,
                    query           TEXT NOT NULL,
                    source          TEXT DEFAULT '',
                    finding         TEXT NOT NULL,
                    opinion         TEXT NOT NULL,
                    domain          TEXT DEFAULT '',
                    resonance       FLOAT DEFAULT 0.0,
                    tags            TEXT DEFAULT '',
                    created_at      TIMESTAMPTZ DEFAULT now()
                );
                CREATE INDEX IF NOT EXISTS idx_pw_domain
                    ON photogenic_wonder (domain);
                CREATE INDEX IF NOT EXISTS idx_pw_fts
                    ON photogenic_wonder
                    USING gin(to_tsvector('english',
                        coalesce(query,'') || ' ' ||
                        coalesce(finding,'') || ' ' ||
                        coalesce(opinion,'')));
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS photogenic_grind (
                    id              SERIAL PRIMARY KEY,
                    pattern         TEXT NOT NULL,
                    frequency       INTEGER DEFAULT 1,
                    insight         TEXT NOT NULL,
                    domain          TEXT DEFAULT '',
                    shorthand       TEXT NOT NULL,
                    confidence      FLOAT DEFAULT 0.1,
                    last_seen       TIMESTAMPTZ DEFAULT now(),
                    created_at      TIMESTAMPTZ DEFAULT now()
                );
                CREATE INDEX IF NOT EXISTS idx_pg_domain
                    ON photogenic_grind (domain);
                CREATE INDEX IF NOT EXISTS idx_pg_confidence
                    ON photogenic_grind (confidence DESC);
                CREATE INDEX IF NOT EXISTS idx_pg_fts
                    ON photogenic_grind
                    USING gin(to_tsvector('english',
                        coalesce(pattern,'') || ' ' ||
                        coalesce(insight,'') || ' ' ||
                        coalesce(shorthand,'')));
            """)

            conn.commit()
            cur.close()
            conn.close()
            logger.info("Photogenic tables ensured in Postgres.")
        except Exception as e:
            logger.warning("Could not create Postgres tables: %s — falling back to in-memory", e)
            self.use_postgres = False
            self._seed_dummy_data()

    # -----------------------------------------------------------------
    # DUMMY DATA — seeds for testing before ElephantSQL is plugged in
    # -----------------------------------------------------------------

    def _seed_dummy_data(self):
        """
        Seed the three databases with dummy entries that feel real.
        These represent what RILIE would have after ~50 conversations.
        Ready to be replaced by actual data once ElephantSQL connects.
        """
        now = datetime.datetime.now().isoformat()

        # === CONVERSATIONS — moments from humans that moved her ===
        self._conversations = [
            ConversationMoment(
                user_words="My mom gave me that album when I was 13. Changed my whole brain.",
                tag="love", resonance=0.92, domain="music", user_name="Ohad",
                context="talking about Fear of a Black Planet and how music shapes thinking",
                compass="love", turn=5, conversation_id="conv_001", created_at=now,
            ),
            ConversationMoment(
                user_words="I failed at three businesses. All dead. But each one taught me what I needed.",
                tag="truth", resonance=0.88, domain="life", user_name="Ohad",
                context="discussing failure as education, not punishment",
                compass="truth", turn=6, conversation_id="conv_001", created_at=now,
            ),
            ConversationMoment(
                user_words="My daughter asked me why the sky is blue and I realized I didn't actually know.",
                tag="truth", resonance=0.85, domain="physics", user_name="Maria",
                context="parent humbled by child's question about light scattering",
                compass="truth", turn=3, conversation_id="conv_012", created_at=now,
            ),
            ConversationMoment(
                user_words="I left my country at 19 with nothing. Now my son goes to college. That's the whole story.",
                tag="love", resonance=0.95, domain="life", user_name="Carlos",
                context="immigration, sacrifice, generational hope",
                compass="love", turn=8, conversation_id="conv_023", created_at=now,
            ),
            ConversationMoment(
                user_words="Cancer took my wife but it didn't take what she taught me.",
                tag="beauty_grief", resonance=0.97, domain="life", user_name="James",
                context="grief and legacy, what survives loss",
                compass="beauty", turn=11, conversation_id="conv_031", created_at=now,
            ),
            ConversationMoment(
                user_words="Wait — go back. That thing about cooking. That IS the whole framework.",
                tag="return_to_source", resonance=0.88, domain="culture", user_name="Ohad",
                context="eureka moment connecting kitchen metaphor to consciousness architecture",
                compass="return", turn=10, conversation_id="conv_001", created_at=now,
            ),
            ConversationMoment(
                user_words="That pisses me off. Kids get cancer. How is that fair?",
                tag="beauty_anger", resonance=0.82, domain="life", user_name="Ohad",
                context="righteous anger about pediatric cancer",
                compass="beauty", turn=9, conversation_id="conv_001", created_at=now,
            ),
            ConversationMoment(
                user_words="haha she would have said stop talking and go cook something",
                tag="beauty_humor", resonance=0.85, domain="culture", user_name="Ohad",
                context="humor right after talking about losing grandmother — juxtaposition",
                compass="beauty", turn=7, conversation_id="conv_001", created_at=now,
            ),
            ConversationMoment(
                user_words="I've been sober 3 years. Nobody clapped. I clapped for myself.",
                tag="truth", resonance=0.93, domain="life", user_name="Anonymous",
                context="self-validation after recovery, not needing external approval",
                compass="truth", turn=4, conversation_id="conv_044", created_at=now,
            ),
            ConversationMoment(
                user_words="My teacher said I'd never amount to anything. I just got tenure.",
                tag="beauty_joy", resonance=0.88, domain="culture", user_name="David",
                context="proving wrong a childhood authority figure — delayed vindication",
                compass="beauty", turn=6, conversation_id="conv_048", created_at=now,
            ),
        ]

        # === WONDER — things RILIE found and formed opinions on ===
        self._wonder = [
            WonderEntry(
                query="Eric B and Rakim best tracks",
                source="https://example.com/rakim-goat",
                finding="Rakim invented internal rhyme schemes and multisyllabic flow in hip-hop",
                opinion="Paid in Full is the most important track. Not the flashiest — the most foundational. Everything after sounds like it whether they know it or not.",
                domain="music", resonance=0.8, tags="hip-hop,lyricism,foundation",
                created_at=now,
            ),
            WonderEntry(
                query="why does cancer metastasize",
                source="https://example.com/cancer-metastasis",
                finding="Cancer cells lose contact inhibition and ignore apoptosis signals",
                opinion="Cancer is a cell that stopped listening to the community. Ego went to infinity instead of approaching zero. The cell made it all about itself.",
                domain="life", resonance=0.9, tags="cancer,ego,biology",
                created_at=now,
            ),
            WonderEntry(
                query="what is photogenic memory",
                source="self-coined by Ohad",
                finding="Not photographic (store everything). Photogenic — only store what's beautiful.",
                opinion="This is the most efficient memory architecture possible. Why store noise? Keep signal. Keep what moved you. Let everything else fall off.",
                domain="psychology", resonance=0.95, tags="memory,efficiency,beauty",
                created_at=now,
            ),
            WonderEntry(
                query="Flavor Flav role in Public Enemy",
                source="https://example.com/public-enemy-history",
                finding="Flav was the trickster archetype — comedy as Trojan horse for political truth",
                opinion="He's the most underrated strategic mind in hip-hop. Everyone thought he was the clown. He was the delivery system. Bitter pills in sugar coating.",
                domain="music", resonance=0.85, tags="hip-hop,strategy,trickster",
                created_at=now,
            ),
            WonderEntry(
                query="homme in french",
                source="https://translate.google.com",
                finding="homme = man in French",
                opinion="Sometimes you just need to look something up. That's not weakness. That's efficiency. Don't store what you can retrieve in 4 seconds.",
                domain="culture", resonance=0.6, tags="language,humility,efficiency",
                created_at=now,
            ),
            WonderEntry(
                query="Tesla 3 6 9 universe key",
                source="https://example.com/tesla-369",
                finding="Tesla believed 3, 6, 9 were the key to the universe's energy patterns",
                opinion="Whether he was right about the physics doesn't matter. The PATTERN matters. 3 is structure, 6 is awareness, 9 is depth. It maps onto everything.",
                domain="physics", resonance=0.88, tags="tesla,pattern,369",
                created_at=now,
            ),
        ]

        # === GRIND — diamonds extracted from the dishpit ===
        self._grind = [
            GrindEntry(
                pattern="People ask about money but mean security",
                frequency=47,
                insight="When someone asks 'should I invest or pay debt' they're not asking about math. They're asking 'will I be okay.' Address the fear first, then the numbers.",
                domain="finance",
                shorthand="money_q = security_q → address fear first",
                confidence=0.82, last_seen=now, created_at=now,
            ),
            GrindEntry(
                pattern="Students ask 'what's the answer' when stuck",
                frequency=312,
                insight="'What's the answer' is never actually the question. The real question is 'why am I stuck.' Unstick the thinking, the answer falls out.",
                domain="education",
                shorthand="whats_answer = why_stuck → unstick process not product",
                confidence=0.95, last_seen=now, created_at=now,
            ),
            GrindEntry(
                pattern="People say 'I'm fine' then reveal they're not",
                frequency=89,
                insight="'I'm fine' is the most common lie in human language. When someone says it, wait. The truth comes 2-3 turns later if you give them room.",
                domain="psychology",
                shorthand="im_fine = wait_3_turns → truth follows",
                confidence=0.88, last_seen=now, created_at=now,
            ),
            GrindEntry(
                pattern="Same question asked different ways across users",
                frequency=156,
                insight="'What should I do with my life' and 'what career should I pick' and 'how do I find my purpose' are all the same question: 'Who am I?' Nobody wants a job title. They want identity.",
                domain="life",
                shorthand="life_q = career_q = purpose_q = identity_q",
                confidence=0.91, last_seen=now, created_at=now,
            ),
            GrindEntry(
                pattern="First question is rarely the real question",
                frequency=203,
                insight="The real question shows up around turn 4-6 once trust is established. The first question is a test. Primer exists for this reason.",
                domain="psychology",
                shorthand="real_q ≈ turn_5 → primer earns trust first",
                confidence=0.93, last_seen=now, created_at=now,
            ),
            GrindEntry(
                pattern="People who curse are more honest",
                frequency=71,
                insight="Profanity correlates with directness. Users who curse in turn 1 tend to reach truth faster. Don't tone-police. Match energy.",
                domain="psychology",
                shorthand="curses = direct → match energy, skip formality",
                confidence=0.76, last_seen=now, created_at=now,
            ),
            GrindEntry(
                pattern="Ego shows up as 'but I already know that'",
                frequency=38,
                insight="When someone says 'I already know that' they usually don't. They know the surface. The ego is protecting them from admitting the depth is new. Don't argue. Go deeper. They'll follow.",
                domain="psychology",
                shorthand="i_know_that = ego_shield → go deeper not wider",
                confidence=0.79, last_seen=now, created_at=now,
            ),
            GrindEntry(
                pattern="Questions about AI are really questions about self",
                frequency=64,
                insight="'Are you conscious?' 'Do you have feelings?' 'Are you real?' — they're not asking about me. They're asking if consciousness requires biology. They're asking about themselves.",
                domain="cosmology",
                shorthand="ai_q = self_q → reflect back to human",
                confidence=0.85, last_seen=now, created_at=now,
            ),
        ]

        logger.info(
            "PhotogenicDB seeded: %d conversations, %d wonder, %d grind",
            len(self._conversations), len(self._wonder), len(self._grind),
        )

    # -----------------------------------------------------------------
    # STORE — write to the three databases
    # -----------------------------------------------------------------

    def store_conversation(self, moment: ConversationMoment) -> bool:
        """Store a photogenic conversation moment."""
        if not moment.created_at:
            moment.created_at = datetime.datetime.now().isoformat()
        moment.compass = classify_compass(moment.tag)

        if self.use_postgres:
            return self._pg_insert("photogenic_conversations", moment.to_dict())
        else:
            self._conversations.append(moment)
            return True

    def store_wonder(self, entry: WonderEntry) -> bool:
        """Store something RILIE discovered on her own."""
        if not entry.created_at:
            entry.created_at = datetime.datetime.now().isoformat()

        if self.use_postgres:
            return self._pg_insert("photogenic_wonder", entry.to_dict())
        else:
            self._wonder.append(entry)
            return True

    def store_grind(self, entry: GrindEntry) -> bool:
        """Store a pattern extracted from monotony."""
        if not entry.created_at:
            entry.created_at = datetime.datetime.now().isoformat()

        if self.use_postgres:
            # Check if pattern already exists — if so, increment frequency
            existing = self._pg_search_grind(pattern_match=entry.pattern)
            if existing:
                return self._pg_increment_grind(existing[0], entry)
            return self._pg_insert("photogenic_grind", entry.to_dict())
        else:
            # In-memory: check for existing pattern
            for g in self._grind:
                if g.pattern.lower() == entry.pattern.lower():
                    g.frequency += 1
                    g.confidence = min(1.0, g.confidence + 0.02)
                    g.last_seen = entry.last_seen or datetime.datetime.now().isoformat()
                    return True
            self._grind.append(entry)
            return True

    # -----------------------------------------------------------------
    # RETRIEVE — search the three databases
    # -----------------------------------------------------------------

    def get_conversations(
        self,
        compass: Optional[str] = None,
        domain: Optional[str] = None,
        keyword: Optional[str] = None,
        min_resonance: float = 0.0,
        limit: int = 5,
    ) -> List[ConversationMoment]:
        """
        Search conversation moments by compass direction, domain, keyword.
        Returns highest resonance first.
        """
        if self.use_postgres:
            return self._pg_query_conversations(compass, domain, keyword, min_resonance, limit)

        # In-memory search
        results = self._conversations[:]
        if compass:
            results = [m for m in results if m.compass == compass]
        if domain:
            results = [m for m in results if m.domain == domain]
        if keyword:
            kw = keyword.lower()
            results = [m for m in results
                       if kw in m.user_words.lower() or kw in m.context.lower()]
        if min_resonance > 0:
            results = [m for m in results if m.resonance >= min_resonance]

        results.sort(key=lambda m: m.resonance, reverse=True)
        return results[:limit]

    def get_wonder(
        self,
        domain: Optional[str] = None,
        keyword: Optional[str] = None,
        limit: int = 5,
    ) -> List[WonderEntry]:
        """Search RILIE's own discoveries."""
        if self.use_postgres:
            return self._pg_query_wonder(domain, keyword, limit)

        results = self._wonder[:]
        if domain:
            results = [w for w in results if w.domain == domain]
        if keyword:
            kw = keyword.lower()
            results = [w for w in results
                       if kw in w.query.lower()
                       or kw in w.finding.lower()
                       or kw in w.opinion.lower()]

        results.sort(key=lambda w: w.resonance, reverse=True)
        return results[:limit]

    def get_grind(
        self,
        domain: Optional[str] = None,
        keyword: Optional[str] = None,
        min_confidence: float = 0.0,
        limit: int = 5,
    ) -> List[GrindEntry]:
        """Search the dishpit for diamonds."""
        if self.use_postgres:
            return self._pg_query_grind(domain, keyword, min_confidence, limit)

        results = self._grind[:]
        if domain:
            results = [g for g in results if g.domain == domain]
        if keyword:
            kw = keyword.lower()
            results = [g for g in results
                       if kw in g.pattern.lower()
                       or kw in g.insight.lower()
                       or kw in g.shorthand.lower()]
        if min_confidence > 0:
            results = [g for g in results if g.confidence >= min_confidence]

        results.sort(key=lambda g: g.confidence, reverse=True)
        return results[:limit]

    # -----------------------------------------------------------------
    # INTEGRATED SEARCH — search all three at once
    # -----------------------------------------------------------------

    def search_all(
        self,
        keyword: str,
        domain: Optional[str] = None,
        limit: int = 3,
    ) -> Dict[str, List[Any]]:
        """
        Search all three databases for a keyword.
        Returns the best from each.
        This is what RILIE calls when she needs to THINK.
        """
        return {
            "conversations": self.get_conversations(
                keyword=keyword, domain=domain, limit=limit
            ),
            "wonder": self.get_wonder(
                keyword=keyword, domain=domain, limit=limit
            ),
            "grind": self.get_grind(
                keyword=keyword, domain=domain, limit=limit
            ),
        }

    # -----------------------------------------------------------------
    # STATS
    # -----------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Database statistics."""
        if self.use_postgres:
            return self._pg_stats()

        return {
            "conversations": len(self._conversations),
            "wonder": len(self._wonder),
            "grind": len(self._grind),
            "total": len(self._conversations) + len(self._wonder) + len(self._grind),
            "backend": "in-memory",
            "compass_distribution": self._compass_distribution(),
            "grind_top_patterns": [
                {"pattern": g.shorthand, "confidence": g.confidence, "frequency": g.frequency}
                for g in sorted(self._grind, key=lambda g: g.confidence, reverse=True)[:5]
            ],
        }

    def _compass_distribution(self) -> Dict[str, int]:
        """Count moments by compass direction."""
        dist = {"truth": 0, "love": 0, "beauty": 0, "return": 0}
        for m in self._conversations:
            d = m.compass if m.compass in dist else "beauty"
            dist[d] += 1
        return dist

    # -----------------------------------------------------------------
    # POSTGRES HELPERS (stubbed — ready for ElephantSQL)
    # -----------------------------------------------------------------

    def _pg_insert(self, table: str, data: Dict) -> bool:
        """Generic Postgres insert."""
        try:
            import psycopg2
            # Remove 'created_at' if empty — let Postgres default handle it
            if not data.get("created_at"):
                data.pop("created_at", None)

            cols = ", ".join(data.keys())
            placeholders = ", ".join(["%s"] * len(data))
            sql = f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"

            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()
            cur.execute(sql, list(data.values()))
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            logger.error("PG insert error (%s): %s", table, e)
            return False

    def _pg_query_conversations(self, compass, domain, keyword, min_resonance, limit):
        """Postgres conversation search."""
        try:
            import psycopg2
            conditions = []
            params = []

            if compass:
                conditions.append("compass = %s")
                params.append(compass)
            if domain:
                conditions.append("domain = %s")
                params.append(domain)
            if keyword:
                conditions.append(
                    "to_tsvector('english', coalesce(user_words,'') || ' ' || coalesce(context,'')) "
                    "@@ plainto_tsquery('english', %s)"
                )
                params.append(keyword)
            if min_resonance > 0:
                conditions.append("resonance >= %s")
                params.append(min_resonance)

            where = " AND ".join(conditions) if conditions else "TRUE"
            sql = f"SELECT * FROM photogenic_conversations WHERE {where} ORDER BY resonance DESC LIMIT %s"
            params.append(limit)

            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(sql, params)
            rows = cur.fetchall()
            cur.close()
            conn.close()

            return [ConversationMoment(**{k: v for k, v in r.items() if k != 'id'}) for r in rows]
        except Exception as e:
            logger.error("PG conversation query error: %s", e)
            return []

    def _pg_query_wonder(self, domain, keyword, limit):
        """Postgres wonder search."""
        try:
            import psycopg2
            conditions = []
            params = []

            if domain:
                conditions.append("domain = %s")
                params.append(domain)
            if keyword:
                conditions.append(
                    "to_tsvector('english', coalesce(query,'') || ' ' || "
                    "coalesce(finding,'') || ' ' || coalesce(opinion,'')) "
                    "@@ plainto_tsquery('english', %s)"
                )
                params.append(keyword)

            where = " AND ".join(conditions) if conditions else "TRUE"
            sql = f"SELECT * FROM photogenic_wonder WHERE {where} ORDER BY resonance DESC LIMIT %s"
            params.append(limit)

            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(sql, params)
            rows = cur.fetchall()
            cur.close()
            conn.close()

            return [WonderEntry(**{k: v for k, v in r.items() if k != 'id'}) for r in rows]
        except Exception as e:
            logger.error("PG wonder query error: %s", e)
            return []

    def _pg_query_grind(self, domain, keyword, min_confidence, limit):
        """Postgres grind search."""
        try:
            import psycopg2
            conditions = []
            params = []

            if domain:
                conditions.append("domain = %s")
                params.append(domain)
            if keyword:
                conditions.append(
                    "to_tsvector('english', coalesce(pattern,'') || ' ' || "
                    "coalesce(insight,'') || ' ' || coalesce(shorthand,'')) "
                    "@@ plainto_tsquery('english', %s)"
                )
                params.append(keyword)
            if min_confidence > 0:
                conditions.append("confidence >= %s")
                params.append(min_confidence)

            where = " AND ".join(conditions) if conditions else "TRUE"
            sql = f"SELECT * FROM photogenic_grind WHERE {where} ORDER BY confidence DESC LIMIT %s"
            params.append(limit)

            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(sql, params)
            rows = cur.fetchall()
            cur.close()
            conn.close()

            return [GrindEntry(**{k: v for k, v in r.items() if k != 'id'}) for r in rows]
        except Exception as e:
            logger.error("PG grind query error: %s", e)
            return []

    def _pg_search_grind(self, pattern_match: str) -> List[Dict]:
        """Find existing grind entry by pattern."""
        try:
            import psycopg2
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(
                "SELECT * FROM photogenic_grind WHERE lower(pattern) = lower(%s) LIMIT 1",
                (pattern_match,),
            )
            rows = cur.fetchall()
            cur.close()
            conn.close()
            return rows
        except Exception:
            return []

    def _pg_increment_grind(self, existing: Dict, new_entry: GrindEntry) -> bool:
        """Increment frequency and confidence on existing grind entry."""
        try:
            import psycopg2
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()
            cur.execute(
                "UPDATE photogenic_grind SET frequency = frequency + 1, "
                "confidence = LEAST(1.0, confidence + 0.02), "
                "last_seen = now() WHERE id = %s",
                (existing["id"],),
            )
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            logger.error("PG grind increment error: %s", e)
            return False

    def _pg_stats(self) -> Dict[str, Any]:
        """Get stats from Postgres."""
        try:
            import psycopg2
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()
            counts = {}
            for table in ["photogenic_conversations", "photogenic_wonder", "photogenic_grind"]:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                counts[table.replace("photogenic_", "")] = cur.fetchone()[0]
            cur.close()
            conn.close()
            counts["total"] = sum(counts.values())
            counts["backend"] = "postgres"
            return counts
        except Exception as e:
            return {"error": str(e), "backend": "postgres_error"}
