"""
curiosity.py — RILIE's Subconscious
====================================
The curiosity engine runs between conversations (or between passes).
When RILIE encounters an interesting tangent that isn't relevant to
the current user response, she queues it here. On her own time, she
researches it, runs it through the Triangle, and stores worthy
insights back into Banks.

She doesn't just answer. She *wonders*.
"""

import logging
import threading
import time
from collections import deque
from typing import Dict, Any, List, Optional, Callable

from banks import store_curiosity, search_curiosity, get_curiosity_stats

logger = logging.getLogger("curiosity")


# ---------------------------------------------------------------------------
# The Queue — tangents waiting to be explored
# ---------------------------------------------------------------------------

class CuriosityQueue:
    """
    Thread-safe queue of tangents RILIE wants to explore.
    Each item is a dict with:
      - tangent: the interesting thought (str)
      - seed_query: the user query that sparked it (str)
      - relevance: how relevant it was to the user response (float, 0-1)
      - interest: how interesting it is on its own (float, 0-1)
    """
    def __init__(self, max_size: int = 50):
        self._queue: deque = deque(maxlen=max_size)
        self._lock = threading.Lock()

    def push(self, tangent: str, seed_query: str,
             relevance: float, interest: float) -> bool:
        """
        Add a tangent to the curiosity queue.
        Only queues if: low relevance to user BUT high self-interest.
        Returns True if queued, False if filtered out.
        """
        # The filter: not useful to the user right now, but interesting
        if relevance >= 0.5 or interest < 0.7:
            return False

        item = {
            "tangent": tangent,
            "seed_query": seed_query,
            "relevance": relevance,
            "interest": interest,
            "queued_at": time.time(),
        }

        with self._lock:
            # Don't queue duplicates (same tangent text)
            for existing in self._queue:
                if existing["tangent"].lower().strip() == tangent.lower().strip():
                    return False
            self._queue.append(item)
            logger.info("Curiosity queued [interest=%.2f]: %s", interest, tangent[:80])
            return True

    def pop(self) -> Optional[Dict]:
        """Pop the next tangent to explore. Returns None if empty."""
        with self._lock:
            if not self._queue:
                return None
            return self._queue.popleft()

    def peek_all(self) -> List[Dict]:
        """View everything in the queue without removing."""
        with self._lock:
            return list(self._queue)

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._queue)


# ---------------------------------------------------------------------------
# The Engine — processes tangents into insights
# ---------------------------------------------------------------------------

class CuriosityEngine:
    """
    RILIE's background curiosity processor.
    Takes tangents from the queue, researches them via search,
    processes them through the Triangle, and stores worthy insights
    in banks_curiosity.

    Can run as:
      - Synchronous drain (process all queued items now)
      - Background thread (process on a timer / between conversations)
    """
    def __init__(
        self,
        search_fn: Optional[Callable] = None,
        triangle_fn: Optional[Callable] = None,
        max_per_cycle: int = 3,
        cycle_interval: float = 60.0,
    ):
        """
        Args:
            search_fn: callable(query, num_results) -> list[dict]
                Same signature as brave_search_sync.
            triangle_fn: callable(stimulus, context) -> dict with 'result' and 'quality_score'
                A lightweight Triangle pass for curiosity processing.
            max_per_cycle: max tangents to process per curiosity cycle.
            cycle_interval: seconds between background cycles (if running threaded).
        """
        self.queue = CuriosityQueue()
        self.search_fn = search_fn
        self.triangle_fn = triangle_fn
        self.max_per_cycle = max_per_cycle
        self.cycle_interval = cycle_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def queue_tangent(self, tangent: str, seed_query: str,
                     relevance: float, interest: float) -> bool:
        """Public interface to queue a tangent from RILIE's passes."""
        return self.queue.push(tangent, seed_query, relevance, interest)

    def process_one(self, item: Dict) -> bool:
        """
        Process a single curiosity item:
          1. Research it (Brave search)
          2. Think about it (Triangle)
          3. Store if worthy (Banks)
        Returns True if the insight was kept.
        """
        tangent = item["tangent"]
        seed_query = item["seed_query"]
        logger.info("Curiosity exploring: %s", tangent[:80])

        # Step 1: Research
        research = ""
        if self.search_fn:
            try:
                results = self.search_fn(tangent, 5)
                research = "\n".join(
                    f"- {r.get('title', '')}: {r.get('snippet', '')}"
                    for r in results
                )
            except Exception as e:
                logger.warning("Curiosity search failed: %s", e)
                research = ""

        # Step 2: Think (Triangle processing)
        insight = ""
        quality_score = 0.0
        if self.triangle_fn and research:
            try:
                processed = self.triangle_fn(tangent, research)
                insight = processed.get("result", "")
                quality_score = processed.get("quality_score", 0.0)
            except Exception as e:
                logger.warning("Curiosity triangle failed: %s", e)
                # If Triangle isn't wired yet, store research as-is
                insight = research
                quality_score = item.get("interest", 0.5)
        elif research:
            # No Triangle wired — store raw research with interest as score
            insight = research
            quality_score = item.get("interest", 0.5)
        else:
            # Nothing found — not worth storing
            logger.info("Curiosity dead end: %s", tangent[:80])
            return False

        # Step 3: Store in Banks
        kept = store_curiosity(
            seed_query=seed_query,
            tangent=tangent,
            research=research,
            insight=insight,
            quality_score=quality_score,
            origin="curiosity",
        )

        if kept:
            logger.info("Curiosity KEPT [%.2f]: %s", quality_score, tangent[:60])
        else:
            logger.info("Curiosity discarded [%.2f]: %s", quality_score, tangent[:60])

        return kept

    def drain(self) -> Dict[str, int]:
        """
        Synchronous: process up to max_per_cycle tangents right now.
        Returns stats: {"processed": N, "kept": M}
        """
        processed = 0
        kept = 0
        while processed < self.max_per_cycle:
            item = self.queue.pop()
            if item is None:
                break
            processed += 1
            if self.process_one(item):
                kept += 1

        if processed > 0:
            logger.info("Curiosity drain: processed=%d, kept=%d", processed, kept)

        return {"processed": processed, "kept": kept}

    # -----------------------------------------------------------------------
    # NEW: Resurface curiosities
    # -----------------------------------------------------------------------
    
    def resurface_curiosities(self, current_stimulus: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Resurface past curiosities that are relevant to the current conversation.
        
        This is RILIE's ability to remember "I was curious about X before" and
        bring it back when X becomes relevant again. Part of the 360° loop:
        conversation generates curiosity → curiosity stored → curiosity resurfaces
        when context matches → deeper conversation emerges.
        
        Args:
            current_stimulus: The current user input
            limit: Max number of past curiosities to resurface (default 3)
            
        Returns:
            List of relevant past curiosities with their context
        """
        try:
            # Search Banks for past tangents related to current topic
            results = search_curiosity(
                query=current_stimulus,
                limit=limit,
                min_quality=0.6
            )
            
            resurfaced = []
            for result in results:
                resurfaced.append({
                    'tangent': result.get('tangent', ''),
                    'original_context': result.get('seed_query', ''),
                    'insight': result.get('insight', ''),
                    'timestamp': result.get('timestamp'),
                    'quality_score': result.get('quality_score', 0.0),
                })
                
            if resurfaced:
                logger.info(f"[CURIOSITY] Resurfaced {len(resurfaced)} past curiosities for: {current_stimulus[:60]}")
                
            return resurfaced
            
        except Exception as e:
            logger.error(f"[CURIOSITY] Error resurfacing: {e}")
            return []

    # -----------------------------------------------------------------------
    # Background thread — she thinks when nobody's talking
    # -----------------------------------------------------------------------

    def start_background(self):
        """Start the background curiosity thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._background_loop,
            daemon=True,
            name="rilie-curiosity",
        )
        self._thread.start()
        logger.info("Curiosity background thread started (interval=%.0fs)", self.cycle_interval)

    def stop_background(self):
        """Stop the background curiosity thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
        logger.info("Curiosity background thread stopped.")

    def _background_loop(self):
        """The loop that runs in the background thread."""
        while self._running:
            try:
                if self.queue.size > 0:
                    self.drain()
            except Exception as e:
                logger.error("Curiosity background error: %s", e)

            # Sleep in small chunks so we can stop quickly
            for _ in range(int(self.cycle_interval)):
                if not self._running:
                    break
                time.sleep(1)

    # -----------------------------------------------------------------------
    # Status
    # -----------------------------------------------------------------------

    def status(self) -> Dict[str, Any]:
        """Full curiosity engine status — queue + stored insights."""
        db_stats = get_curiosity_stats()
        return {
            "queue_size": self.queue.size,
            "queue_items": [
                {"tangent": i["tangent"][:80], "interest": i["interest"]}
                for i in self.queue.peek_all()
            ],
            "background_running": self._running,
            "db_total": db_stats.get("total", 0),
            "db_kept": db_stats.get("kept", 0),
            "db_avg_quality": round(db_stats.get("avg_quality", 0.0), 3),
            "db_last_curiosity": str(db_stats.get("last_curiosity", "")),
        }
