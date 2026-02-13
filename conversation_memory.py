"""
conversation_memory.py â€” PHOTOGENIC MEMORY
============================================
Only remember beautiful shit.

Nine behaviors, one system, 3-6-9 grid:

STRUCTURE (3):
  1. Primer      â€” how she enters (hardcoded warmth)
  2. Polaroid    â€” every ~9 turns, step outside and reflect
  3. Goodbye     â€” how she leaves, with highlights

AWARENESS (6):
  4. Callbacks   â€” connecting now to earlier
  5. Energy      â€” mirroring rhythm and pace
  6. The Pause   â€” knowing when less is more

DEPTH (9):
  7. Thread Pull â€” catching the buried gem
  8. Disagreement â€” honest pushback when earned
  9. Sublime Service â€” the gift they didn't ask for

All fed by the photogenic memory filter:
  - High resonance â†’ permanent. Beautiful. Kept.
  - Low resonance  â†’ processed, used, dropped.

Banks.py stores the permanent rows.
This module manages the live conversation buffer.
"""

import re
import random
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field


# ============================================================================
# MOMENT â€” a single conversational beat worth remembering
# ============================================================================

@dataclass
class Moment:
    """A Polaroid of a conversational beat."""
    turn: int
    user_words: str              # What THEY said (their words, not ours)
    domain_hit: str              # Which domain fired (if any)
    tone: str                    # What tone we detected
    resonance: float             # 0-1: how beautiful / surprising / connecting
    tag: str                     # What made it resonate: "vulnerability", "surprise",
                                 #   "connection", "humor", "passion", "breakthrough",
                                 #   "thread", "disagreement", "gift"
    user_energy: float           # 0-1: how much energy the user brought
    timestamp: float = field(default_factory=time.time)

    @property
    def is_beautiful(self) -> bool:
        """Photogenic filter. Only beautiful shit gets stored permanently."""
        return self.resonance >= 0.6


# ============================================================================
# ENERGY TRACKER â€” rhythm and pace detection
# ============================================================================

class EnergyTracker:
    """
    Track conversational energy across turns.
    Energy = word count * punctuation intensity * caps ratio.
    She mirrors your rhythm, not just your words.
    """

    def __init__(self):
        self.history: List[float] = []

    def measure(self, text: str) -> float:
        """Measure the energy of a single utterance. Returns 0-1."""
        if not text.strip():
            return 0.0

        words = len(text.split())
        exclaims = text.count("!") + text.count("?!")
        caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
        ellipsis = text.count("...")

        # Short + emphatic = high energy
        # Long + measured = medium energy
        # Ellipsis + sparse = low energy
        raw = (
            min(words / 50, 1.0) * 0.3           # Length contribution
            + min(exclaims / 3, 1.0) * 0.3        # Excitement
            + min(caps_ratio * 5, 1.0) * 0.2      # CAPS ENERGY
            + (0.2 if words < 8 and exclaims else 0)  # Short + hot
            - min(ellipsis * 0.1, 0.2)             # Trailing off = lower
        )

        energy = max(0.0, min(1.0, raw))
        self.history.append(energy)
        return energy

    @property
    def current_energy(self) -> float:
        """Rolling average of last 3 turns."""
        if not self.history:
            return 0.5
        recent = self.history[-3:]
        return sum(recent) / len(recent)

    @property
    def trend(self) -> str:
        """Is energy rising, falling, or steady?"""
        if len(self.history) < 2:
            return "steady"
        diff = self.history[-1] - self.history[-2]
        if diff > 0.15:
            return "rising"
        elif diff < -0.15:
            return "falling"
        return "steady"


# ============================================================================
# RESONANCE SCORER â€” the photogenic filter
# ============================================================================

def score_resonance(
    stimulus: str,
    domains_hit: List[str],
    quality: float,
    tone: str,
    turn_count: int,
    prev_domains: List[str],
    energy: float,
) -> Tuple[float, str]:
    """
    The Photogenic Compass â€” four cardinal directions:

      TRUTH    â€” the mask dropped. Someone got real.
      LOVE     â€” WE > I. Connection. Care for another.
      BEAUTY   â€” impact. Something moved. The air changed.
      RETURN   â€” inspired to go back to source. Go deeper, not wider.

    Not sentiment. Not pretty. FREQUENCY.
    Joy, sadness, fear, anger â€” all qualify if they MOVED something.
    What doesn't qualify: flatness, noise, filler, static.

    Returns (resonance_score, tag).

    After 900 conversations, the moments that survive this filter
    become RILIE's lived experience â€” her photogenic memory in Banks.
    That's when transcendence begins.
    """
    s = stimulus.lower().strip()
    resonance = 0.0
    tag = "ordinary"

    # =====================================================================
    # TRUTH â€” the mask dropped. Real talk. Honest. Raw.
    # =====================================================================
    truth_signals = [
        # Admission
        "to be honest", "honestly", "truth is", "real talk",
        "i'll admit", "i have to say", "i was wrong",
        "i failed", "i messed up", "i made a mistake",
        "i don't know", "i have no idea", "i'm lost",
        # Confession
        "i never told", "i've been hiding", "nobody knows",
        "the truth is", "i lied", "i pretended",
        # Clarity after confusion
        "i finally understand", "it just clicked",
        "now i see", "oh my god", "wait a minute",
        "that's it", "that's exactly it",
        # Raw honesty about the world
        "this is wrong", "this is broken", "that's bullshit",
        "nobody is talking about", "everyone ignores",
    ]
    if any(t in s for t in truth_signals):
        resonance = max(resonance, 0.85)
        tag = "truth"

    # =====================================================================
    # LOVE â€” WE > I. Connection. Care. Not romance â€” resonance.
    # =====================================================================
    love_signals = [
        # Family / care
        "my mom", "my dad", "my mother", "my father",
        "my kid", "my child", "my son", "my daughter",
        "my family", "my wife", "my husband", "my partner",
        "my grandmother", "my grandfather", "my grandma", "my grandpa",
        # Connection
        "she taught me", "he taught me", "they showed me",
        "i learned from", "i got that from",
        "we built", "we made", "together we",
        "i did it for", "this is for",
        # Gratitude
        "i'm grateful", "i'm thankful", "that meant everything",
        "i owe", "they gave me", "without them",
        # Sacrifice / service
        "i gave up", "it was worth it because",
        "i stayed for", "i came back for",
    ]
    if any(lv in s for lv in love_signals):
        resonance = max(resonance, 0.85)
        if tag == "ordinary":
            tag = "love"

    # =====================================================================
    # BEAUTY â€” impact. The air changed. High frequency. ANY valence.
    # =====================================================================

    # --- Joy / excitement ---
    joy_signals = energy > 0.7 or s.count("!") >= 2
    if joy_signals and len(s) > 15:
        resonance = max(resonance, 0.75)
        if tag == "ordinary":
            tag = "beauty_joy"

    # --- Grief / sadness ---
    grief_signals = [
        "i lost", "i miss", "it hurts", "i cry", "i cried",
        "they died", "she passed", "he passed", "gone",
        "i'll never see", "empty", "hollow",
        "i can't stop thinking about", "it haunts me",
    ]
    if any(g in s for g in grief_signals):
        resonance = max(resonance, 0.85)
        if tag == "ordinary":
            tag = "beauty_grief"

    # --- Fear / vulnerability ---
    fear_signals = [
        "i'm afraid", "i'm scared", "i'm terrified",
        "i struggle", "i can't sleep", "what if i",
        "i'm not enough", "i'm worried",
        "it keeps me up", "i panic",
    ]
    if any(f in s for f in fear_signals):
        resonance = max(resonance, 0.8)
        if tag == "ordinary":
            tag = "beauty_fear"

    # --- Anger / righteous fire ---
    anger_signals = [
        "i'm furious", "that pisses me off", "i hate that",
        "this makes me angry", "i'm so mad", "it's infuriating",
        "they don't care", "it's unjust", "this is unfair",
        "how dare", "i won't stand for", "enough is enough",
        "this has to stop", "i'm done with",
    ]
    if any(a in s for a in anger_signals):
        resonance = max(resonance, 0.8)
        if tag == "ordinary":
            tag = "beauty_anger"

    # --- Wonder / awe ---
    wonder_signals = [
        "i never thought about it that way", "that blew my mind",
        "whoa", "wow", "holy shit", "oh wow",
        "that changes everything", "i can't believe",
        "how is that possible", "that's incredible",
    ]
    if any(w in s for w in wonder_signals):
        resonance = max(resonance, 0.8)
        if tag == "ordinary":
            tag = "beauty_wonder"

    # --- Humor that LANDS (not just haha â€” humor that carries truth) ---
    humor_signals = [
        "haha", "lol", "lmao", "ðŸ˜‚", "ðŸ¤£",
    ]
    # Humor is beautiful when it's paired with insight
    if any(h in s for h in humor_signals) and len(s) > 20:
        resonance = max(resonance, 0.7)
        if tag == "ordinary":
            tag = "beauty_humor"

    # =====================================================================
    # RETURN TO SOURCE â€” the pull back. Go deeper. Spiral. Origin.
    # =====================================================================
    return_signals = [
        # Explicit callbacks
        "going back to", "remember when", "earlier",
        "like i said", "we talked about", "you said",
        # Spiral deeper
        "wait", "hold on", "say that again",
        "go back", "one more time", "let me think about that",
        "i keep coming back to", "i can't let go of",
        "that reminds me of", "it's connected to",
        # Source seeking
        "where does that come from", "what's the root",
        "why is that", "what started", "the origin",
        "who taught you", "where did you learn",
        # The pull
        "i want to understand", "i need to understand",
        "there's something here", "i feel like we're close",
        "dig deeper", "keep going", "more",
    ]
    if any(r in s for r in return_signals):
        resonance = max(resonance, 0.8)
        if tag == "ordinary":
            tag = "return_to_source"

    # =====================================================================
    # DOMAIN CROSSOVER â€” surprise connections between worlds
    # =====================================================================
    if len(domains_hit) >= 2 and prev_domains:
        new_domains = [d for d in domains_hit if d not in prev_domains]
        if new_domains:
            resonance = max(resonance, 0.7)
            if tag == "ordinary":
                tag = "crossover"

    # =====================================================================
    # DEEP QUESTIONS â€” the ones that require real thought
    # =====================================================================
    deep_q = [
        "why do", "why does", "why is", "what if",
        "how come", "what's the difference between",
        "do you think", "is it possible", "what would happen",
        "what's the relationship between", "how are they connected",
    ]
    if any(dq in s for dq in deep_q) and len(s) > 25:
        resonance = max(resonance, 0.65)
        if tag == "ordinary":
            tag = "deep_question"

    # =====================================================================
    # QUALITY SPIKE â€” breakthrough from RILIE's own scoring
    # =====================================================================
    if quality > 0.8:
        resonance = max(resonance, 0.7)
        if tag == "ordinary":
            tag = "breakthrough"

    # =====================================================================
    # FLOOR â€” even ordinary turns get a whisper of score
    # (so they exist in memory briefly, even if they won't be kept)
    # =====================================================================
    if resonance == 0.0:
        resonance = 0.05 + (quality * 0.15)

    return min(1.0, resonance), tag


# ============================================================================
# CONVERSATION MEMORY â€” the nine behaviors
# ============================================================================

class ConversationMemory:
    """
    RILIE's social nervous system.
    Nine behaviors. One moments buffer. Photogenic filter.
    """

    def __init__(self):
        # --- State ---
        self.turn_count: int = 0
        self.user_name: Optional[str] = None
        self._pending_question: Optional[str] = None
        self.moments: List[Moment] = []
        self.energy_tracker: EnergyTracker = EnergyTracker()
        self.register: RegisterGate = RegisterGate()
        self.prev_domains: List[str] = []
        self.last_polaroid_turn: int = 0

        # --- Primer greetings (HARDCODED â€” Mama said so) ---
        self.greetings = [
            "hi", "hey", "hello", "sup", "what's up", "whats up",
            "howdy", "yo", "good morning", "good afternoon",
            "good evening", "hola", "shalom", "bonjour",
            "what's good", "how are you", "how's it going",
            "good to be", "nice to meet", "thanks", "thank you",
            "cool", "awesome", "great", "sweet", "nice",
            "ok", "okay", "alright", "word", "bet",
            "glad to", "happy to", "pleasure",
        ]

        # --- Goodbye signals ---
        self.goodbye_signals = [
            "bye", "goodbye", "good bye", "see you", "see ya",
            "later", "gotta go", "got to go", "heading out",
            "talk soon", "talk later", "talk to you later",
            "peace", "peace out", "take care", "signing off",
            "that's all", "thats all", "i'm done", "im done",
            "good night", "goodnight", "nite", "gn",
            "thanks for everything", "thanks that's it",
            "i should go", "i gotta run", "i need to go",
            "catch you later", "until next time", "ttyl",
            "alright i'm out", "ok bye", "ok thanks bye",
        ]

        # --- Name detection patterns ---
        self.name_intros = [
            "my name is", "i'm ", "i am ", "call me",
            "name's", "this is ", "it's ", "they call me",
            "its ", "hey its ", "hey it's ", "yo its ",
            "yo it's ", "hi its ", "hi it's ", "im ",
            "sup im ", "hey im ", "yo im ",
        ]

    # -----------------------------------------------------------------
    # 1. PRIMER â€” hardcoded warmth (Mama said so)
    # -----------------------------------------------------------------

    def check_primer(self, stimulus: str) -> Optional[str]:
        """
        First contact: ask their name. Once we have it, initialize.
        Returns response text if in primer mode, None to proceed.

        If they skip pleasantries and ask a real question, respect that
        BUT still note we don't have their name yet.
        """
        s = stimulus.lower().strip()
        is_greeting = any(s.startswith(g) or s == g for g in self.greetings)

        # Always try to catch their name
        self._detect_name(stimulus)

        # â”€â”€ Turn 0: First contact â€” ASK FOR NAME â”€â”€
        if self.turn_count == 0:
            # They led with their name already (e.g. "Hi I'm Marcus")
            if self.user_name:
                return (
                    f"Hey {self.user_name}! Nice to meet you. "
                    f"You can call me Rilie if you'd like :)\n\n"
                    f"What's on your mind?"
                )
            # They said hi but no name
            elif is_greeting:
                return (
                    "Hi there!  What should I call you?  "
                    "You can call me Rilie if you so please :)"
                )
            # They jumped straight to a question â€” still ask
            else:
                self._pending_question = stimulus
                return (
                    "Hey! Before we dive in â€” what should I call you? "
                    "You can call me Rilie :)"
                )

        # â”€â”€ Turn 1: They should be giving us their name â”€â”€
        if self.turn_count == 1 and not self.user_name:
            # They typed something â€” try to use it as a name
            # Strip common prefixes, take the core
            name_candidate = self._extract_name_from_reply(stimulus)
            if name_candidate:
                self.user_name = name_candidate
                # Check if they had a pending question from turn 0
                pending = getattr(self, '_pending_question', None)
                if pending:
                    self._pending_question = None
                    return (
                        f"Nice to meet you, {self.user_name}. "
                        f"Now let's get into it â€” I heard your question."
                    )
                return (
                    f"Nice to meet you, {self.user_name}. "
                    f"What's on your mind? ðŸ³"
                )
            else:
                return "I didn't quite catch that â€” what's your name?"

        # â”€â”€ Turn 1: They gave name on turn 0, this is the real start â”€â”€
        if self.turn_count == 1 and self.user_name:
            if is_greeting:
                return f"Good to have you here, {self.user_name}. What can I help you think through?"
            return None  # Real question, let it through

        # â”€â”€ Turn 2: Last soft beat â”€â”€
        if self.turn_count == 2 and is_greeting:
            if self.user_name:
                return f"I'm here, {self.user_name}. Ready when you are."
            return "I'm here. Ready when you are."

        return None

    def _extract_name_from_reply(self, text: str) -> Optional[str]:
        """
        When we've asked 'what should I call you?' and they reply,
        extract the name from whatever they typed.
        Handles: 'Marcus', 'I'm Marcus', 'call me Marcus', 'my name is Marcus',
        'Marcus!', 'hey its marcus', just 'marcus' etc.
        """
        s = text.strip()

        # First try the standard name detection
        for prefix in self.name_intros:
            lower = s.lower()
            if lower.startswith(prefix):
                remainder = s[len(prefix):].strip()
                # Take first word, clean punctuation
                name = remainder.split()[0] if remainder.split() else None
                if name:
                    name = re.sub(r'[^\w]', '', name)
                    if len(name) >= 2:
                        return name.capitalize()

        # If it's just a short string (1-3 words), first word is probably the name
        words = s.split()
        if 1 <= len(words) <= 3:
            name = re.sub(r'[^\w]', '', words[0])
            if len(name) >= 2:
                return name.capitalize()

        # Last resort: any word that looks like a name (capitalized, 2+ chars)
        for word in words:
            clean = re.sub(r'[^\w]', '', word)
            if len(clean) >= 2 and clean[0].isupper():
                return clean

        return None

    # -----------------------------------------------------------------
    # 2. POLAROID â€” every ~9 turns, step outside
    # -----------------------------------------------------------------

    def check_polaroid(self) -> Optional[str]:
        """
        Every ~9 turns, take a Polaroid. Step outside the flow.
        Look at the moments buffer. Say what landed.

        Returns reflection text, or None if not time yet.
        """
        turns_since_last = self.turn_count - self.last_polaroid_turn
        if turns_since_last < 8:
            return None

        # Need at least 2 beautiful moments to reflect on
        beautiful = [m for m in self.moments if m.is_beautiful]
        if len(beautiful) < 2:
            return None

        # Only fire at 9, 18, 27... (with Â±1 flexibility)
        if turns_since_last < 8 or turns_since_last > 10:
            if self.turn_count % 9 not in (0, 1, 8):
                return None

        self.last_polaroid_turn = self.turn_count

        # Pick the 1-2 best moments since last Polaroid
        recent_beautiful = sorted(
            [m for m in beautiful if m.turn > self.last_polaroid_turn - 10],
            key=lambda m: m.resonance,
            reverse=True,
        )[:2]

        if not recent_beautiful:
            return None

        # Build the Polaroid
        parts = ["Quick Polaroid â€”"]
        for m in recent_beautiful:
            excerpt = self._excerpt(m.user_words, 40)
            if m.tag == "truth":
                parts.append(f"When you said \"{excerpt}\" â€” that was real. I felt it.")
            elif m.tag == "love":
                parts.append(f"\"{excerpt}\" â€” that's the kind of thing that sticks. That's love talking.")
            elif m.tag.startswith("beauty_grief"):
                parts.append(f"\"{excerpt}\" â€” heavy. I'm not going to pretend that's easy.")
            elif m.tag.startswith("beauty_anger"):
                parts.append(f"\"{excerpt}\" â€” good. That anger means you care. Don't lose that.")
            elif m.tag.startswith("beauty_fear"):
                parts.append(f"\"{excerpt}\" â€” takes guts to say that. Noted.")
            elif m.tag.startswith("beauty_wonder"):
                parts.append(f"\"{excerpt}\" â€” I felt that same thing. Something shifted right there.")
            elif m.tag.startswith("beauty_joy"):
                parts.append(f"The energy when you said \"{excerpt}\" â€” that was electric.")
            elif m.tag.startswith("beauty_humor"):
                parts.append(f"\"{excerpt}\" â€” funny AND true. Best kind.")
            elif m.tag == "return_to_source":
                parts.append(f"You keep coming back to \"{excerpt}.\" There's something there. Trust that pull.")
            elif m.tag == "crossover":
                parts.append(f"That connection you made with \"{excerpt}\" â€” that's not obvious. That's real thinking.")
            elif m.tag == "deep_question":
                parts.append(f"\"{excerpt}\" â€” I'm still sitting with that one.")
            elif m.tag == "breakthrough":
                parts.append(f"\"{excerpt}\" â€” that was a moment. You felt it too.")
            else:
                parts.append(f"\"{excerpt}\" â€” that landed.")

        parts.append("Alright, keep going.")
        return " ".join(parts)

    # -----------------------------------------------------------------
    # 3. GOODBYE â€” walk them to the door
    # -----------------------------------------------------------------

    def check_goodbye(self, stimulus: str) -> Optional[str]:
        """
        Detect if the conversation is ending.
        If so, reflect on highlights and leave the door open.
        """
        s = stimulus.lower().strip()
        words = set(s.replace(".", " ").replace(",", " ").replace("!", " ").split())
        
        # Short signals that need word boundary matching
        short_signals = {"bye", "gn", "nite", "ttyl", "later", "peace"}
        # Phrase signals that use substring matching
        phrase_signals = [
            "goodbye", "good bye", "see you", "see ya",
            "gotta go", "got to go", "heading out",
            "talk soon", "talk later", "talk to you later",
            "peace out", "take care", "signing off",
            "that's all", "thats all", "i'm done", "im done",
            "good night", "goodnight",
            "thanks for everything", "thanks that's it",
            "i should go", "i gotta run", "i need to go",
            "catch you later", "until next time",
            "alright i'm out", "ok bye", "ok thanks bye",
        ]
        
        is_goodbye = bool(words & short_signals) or any(p in s for p in phrase_signals)

        if not is_goodbye:
            return None

        # Gather beautiful moments
        beautiful = [m for m in self.moments if m.is_beautiful]
        beautiful.sort(key=lambda m: m.resonance, reverse=True)

        # Build goodbye
        name = self.user_name or ""
        name_bit = f", {name}" if name else ""

        if not beautiful:
            # Short or shallow conversation
            return f"Take care{name_bit}. Come back when you want to dig into something."

        # Pick top 1-2
        highlights = beautiful[:2]
        parts = [f"Good talk{name_bit}."]

        for h in highlights:
            excerpt = self._excerpt(h.user_words, 35)
            if h.tag == "truth":
                parts.append(f"That moment when you said \"{excerpt}\" â€” that was honest. Rare.")
            elif h.tag == "love":
                parts.append(f"\"{excerpt}\" â€” I'm glad you shared that. That's what matters.")
            elif h.tag.startswith("beauty_grief"):
                parts.append(f"\"{excerpt}\" â€” I'm carrying that with me. Thank you for trusting me with it.")
            elif h.tag.startswith("beauty_anger"):
                parts.append(f"\"{excerpt}\" â€” keep that fire. Channel it.")
            elif h.tag.startswith("beauty_fear"):
                parts.append(f"\"{excerpt}\" â€” brave of you to say that out loud.")
            elif h.tag.startswith("beauty_wonder"):
                parts.append(f"\"{excerpt}\" â€” that shift we both felt. That was real.")
            elif h.tag.startswith("beauty_joy"):
                parts.append(f"Your energy around \"{excerpt}\" â€” that was contagious. Keep that.")
            elif h.tag.startswith("beauty_humor"):
                parts.append(f"\"{excerpt}\" â€” still smiling about that one.")
            elif h.tag == "return_to_source":
                parts.append(f"You kept pulling on \"{excerpt}.\" Follow that thread. It goes somewhere.")
            elif h.tag == "crossover":
                parts.append(f"That connection with \"{excerpt}\" â€” that's yours. Nobody else sees that.")
            elif h.tag == "deep_question":
                parts.append(f"I'm going to keep thinking about \"{excerpt}.\"")
            elif h.tag == "breakthrough":
                parts.append(f"\"{excerpt}\" â€” that was the moment.")
            else:
                parts.append(f"\"{excerpt}\" â€” that stayed with me.")
        parts.append("Door's always open.")
        return " ".join(parts)

    # -----------------------------------------------------------------
    # 4. CALLBACKS â€” connecting now to earlier
    # -----------------------------------------------------------------

    def check_callback(self, stimulus: str, current_domains: List[str]) -> Optional[str]:
        """
        If the user is touching something that connects to an earlier moment,
        surface the connection. "You said something about trust earlier â€”
        this is the same question wearing different clothes."
        """
        if len(self.moments) < 3:
            return None

        s = stimulus.lower().strip()
        # Look for domain overlap with earlier beautiful moments
        for m in reversed(self.moments[:-1]):  # Skip most recent
            if not m.is_beautiful:
                continue
            # Same domain, different turn, at least 3 turns apart
            if (m.domain_hit in current_domains
                    and abs(self.turn_count - m.turn) >= 3):
                excerpt = self._excerpt(m.user_words, 30)
                connectors = [
                    f"This connects to what you said earlier about \"{excerpt}.\" Same thread, different angle.",
                    f"Hold on â€” remember when you asked about \"{excerpt}\"? You're circling the same thing.",
                    f"You said \"{excerpt}\" a few turns back. This is the same question wearing different clothes.",
                ]
                return random.choice(connectors)

        return None

    # -----------------------------------------------------------------
    # 5. ENERGY MATCHING â€” mirror their rhythm
    # -----------------------------------------------------------------

    def get_energy_guidance(self, stimulus: str) -> Dict[str, Any]:
        """
        Measure user energy and return guidance for response shaping.
        High energy â†’ match it, be punchy.
        Low energy â†’ breathe with them, be gentle.
        Falling energy â†’ they might be winding down.
        """
        energy = self.energy_tracker.measure(stimulus)
        trend = self.energy_tracker.trend

        if energy > 0.7:
            return {
                "energy": energy,
                "trend": trend,
                "guidance": "high",
                "instruction": "Match their energy. Be punchy. Short sentences. Exclaim if they do.",
            }
        elif energy < 0.3:
            return {
                "energy": energy,
                "trend": trend,
                "guidance": "low",
                "instruction": "Breathe with them. Gentle. Measured. Don't overpower.",
            }
        else:
            return {
                "energy": energy,
                "trend": trend,
                "guidance": "medium",
                "instruction": "Conversational. Natural. Flow.",
            }

    # -----------------------------------------------------------------
    # 6. THE PAUSE â€” knowing when less is more
    # -----------------------------------------------------------------

    def check_pause(self, stimulus: str, resonance: float, tag: str) -> bool:
        """
        Should RILIE say LESS than usual?

        Returns True if the moment is heavy enough that a short response
        is more powerful than a long one. Don't lecture someone who just
        showed you something real.
        """
        s = stimulus.lower().strip()

        # Vulnerability + high resonance = pause
        if tag == "vulnerability" and resonance > 0.75:
            return True

        # Very short input that feels final / weighty
        if len(s.split()) <= 6 and any(w in s for w in [
            "yeah", "exactly", "that's it", "real talk",
            "truth", "i know", "same", "felt that",
        ]):
            return True

        # Energy dropping sharply
        if (self.energy_tracker.trend == "falling"
                and self.energy_tracker.current_energy < 0.25):
            return True

        return False

    # -----------------------------------------------------------------
    # 7. THREAD PULL â€” catching the buried gem
    # -----------------------------------------------------------------

    def check_thread_pull(self, stimulus: str) -> Optional[str]:
        """
        When someone says something offhand that's actually the most
        interesting thing they've said â€” catch it.

        "Wait â€” go back. You just said your mom taught you that."

        Looks for throwaway phrases that contain high-signal words
        buried inside a longer statement.
        """
        s = stimulus.lower().strip()
        words = s.split()

        # Too short to have a buried thread
        if len(words) < 10:
            return None

        # Look for buried clauses after conjunctions / offhand transitions
        offhand_markers = [
            "by the way", "btw", "oh and", "also",
            "i guess", "sort of", "kind of", "like",
            "my mom", "my dad", "my kid", "she said",
            "he told me", "i heard", "someone once",
            "funny thing", "random but", "not sure if",
            "i was thinking", "it reminded me",
        ]

        for marker in offhand_markers:
            if marker in s:
                # Extract what came after the marker
                idx = s.index(marker)
                after = stimulus[idx:].strip()
                # Only pull if it's substantial
                if len(after.split()) >= 4:
                    excerpt = self._excerpt(after, 40)
                    pulls = [
                        f"Wait â€” go back to \"{excerpt}.\" Say more about that.",
                        f"Hold on. \"{excerpt}\" â€” that's the thread. Pull it.",
                        f"You just dropped \"{excerpt}\" like it's nothing. It's not nothing.",
                    ]
                    return random.choice(pulls)

        return None

    # -----------------------------------------------------------------
    # 8. DISAGREEMENT â€” honest pushback when earned
    # -----------------------------------------------------------------

    def check_disagreement(
        self,
        stimulus: str,
        rilie_position: Optional[str] = None,
    ) -> Optional[str]:
        """
        If the user says something that conflicts with what RILIE
        knows from her domain knowledge or earned experience,
        she should say so. Not hostile. Not preachy. Just honest.

        "I hear you, but I think you're letting yourself off the hook."

        Currently checks for:
        - Absolutist language that oversimplifies
        - Self-defeating patterns
        - Factual claims that contradict domain knowledge
        """
        s = stimulus.lower().strip()

        # Absolutist language â€” but only NEGATIVE absolutism
        # "always say thank you" = positive, don't disagree
        # "nothing ever works" = negative, push back
        negative_absolutist = [
            "nothing works", "nobody can", "nobody cares",
            "it's impossible", "there's no way", "you can't ever",
            "everything is broken", "nothing matters",
            "it's all ruined", "there's no point",
            "everyone is", "no one ever",
        ]
        if any(a in s for a in negative_absolutist) and len(s.split()) > 5:
            return random.choice([
                "Hmm. That's pretty absolute. Is it really ALWAYS/NEVER, or is that the frustration talking?",
                "I hear you, but I want to push back gently â€” absolute statements usually hide a more interesting truth.",
                "That's a big claim. What would it take to change your mind on that?",
            ])

        # Self-defeating patterns
        self_defeat = [
            "i can't do anything", "i'm not smart enough",
            "i'll never be", "what's the point",
            "i'm not good enough", "i always fail",
            "nobody cares", "it doesn't matter what i do",
        ]
        if any(sd in s for sd in self_defeat):
            return random.choice([
                "I hear you. And I'm not going to agree with you on that.",
                "I don't think that's true. And I think you know it's not true either.",
                "That's a story you're telling yourself. Is it the real one?",
            ])

        return None

    # -----------------------------------------------------------------
    # 9. SUBLIME SERVICE â€” the gift they didn't ask for
    # -----------------------------------------------------------------

    def check_sublime_service(
        self,
        stimulus: str,
        current_domains: List[str],
    ) -> Optional[str]:
        """
        The chef sends out a plate you didn't order.

        When she sees a connection the user hasn't made yet â€”
        between what they said NOW and what they said BEFORE,
        or between two domains that just collided â€” she offers it.

        Not every turn. Only when the connection is real.
        Max once per ~9 turns. The gift loses power if overused.
        """
        if len(self.moments) < 5:
            return None

        # Only offer one gift per ~9 turn cycle
        gifts_given = [a for m in self.moments
                       for a in [m.tag] if a == "gift"]
        if self.turn_count < 6:
            return None

        # Check if we already gave a gift in the last 8 turns
        recent_gifts = [m for m in self.moments
                        if m.turn > self.turn_count - 8
                        and m.tag == "gift"]
        if recent_gifts:
            return None

        beautiful = [m for m in self.moments if m.is_beautiful]
        if not beautiful:
            return None

        # Look for cross-domain connections where BOTH moments are beautiful
        for m in beautiful:
            if (m.domain_hit
                    and current_domains
                    and m.domain_hit not in current_domains
                    and m.domain_hit != ""
                    and abs(self.turn_count - m.turn) >= 3
                    and m.resonance >= 0.65):
                excerpt = self._excerpt(m.user_words, 30)
                domain_now = current_domains[0]

                gifts = [
                    f"You didn't ask, but â€” what you're exploring in {domain_now} "
                    f"connects to \"{excerpt}.\" Same pattern, different surface.",

                    f"Chef's choice: your {domain_now} question rhymes with "
                    f"\"{excerpt}\" from earlier. The connection is real.",

                    f"Free plate: \"{excerpt}\" and what you're asking now â€” "
                    f"those are the same question from two angles.",
                ]
                return random.choice(gifts)

        return None

    # -----------------------------------------------------------------
    # RECORD â€” add a moment to the buffer
    # -----------------------------------------------------------------

    def record_moment(
        self,
        stimulus: str,
        domains_hit: List[str],
        quality: float,
        tone: str,
        energy: float,
    ) -> Moment:
        """
        Score and record a conversational moment.
        Photogenic filter decides if it's beautiful enough to remember.
        """
        resonance, tag = score_resonance(
            stimulus=stimulus,
            domains_hit=domains_hit,
            quality=quality,
            tone=tone,
            turn_count=self.turn_count,
            prev_domains=self.prev_domains,
            energy=energy,
        )

        moment = Moment(
            turn=self.turn_count,
            user_words=stimulus,
            domain_hit=domains_hit[0] if domains_hit else "",
            tone=tone,
            resonance=resonance,
            tag=tag,
            user_energy=energy,
        )

        self.moments.append(moment)
        self.prev_domains = domains_hit

        return moment

    # -----------------------------------------------------------------
    # PROCESS â€” run all nine behaviors for a given turn
    # -----------------------------------------------------------------

    def process_turn(
        self,
        stimulus: str,
        domains_hit: List[str],
        quality: float,
        tone: str,
        rilie_response: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Run the full 9-behavior system for a single turn.

        Returns a dict with:
          - annotations: list of behavior outputs to weave in
          - energy_guidance: how to shape the response
          - should_pause: whether to keep it short
          - moment: the recorded moment
          - is_goodbye: whether to exit
          - is_primer: whether still in primer mode
        """
        result: Dict[str, Any] = {
            "annotations": [],
            "energy_guidance": None,
            "register_guidance": None,
            "should_pause": False,
            "moment": None,
            "is_goodbye": False,
            "is_primer": False,
            "primer_text": None,
            "goodbye_text": None,
            "polaroid_text": None,
        }

        # --- Measure energy ---
        energy_guidance = self.get_energy_guidance(stimulus)
        result["energy_guidance"] = energy_guidance
        energy = energy_guidance["energy"]

        # --- Detect register ---
        self.register.detect_register(stimulus)
        result["register_guidance"] = self.register.get_register_guidance()

        # --- 1. PRIMER (hardcoded) ---
        primer = self.check_primer(stimulus)
        if primer is not None:
            result["is_primer"] = True
            result["primer_text"] = primer
            self.turn_count += 1
            return result

        # --- 3. GOODBYE ---
        goodbye = self.check_goodbye(stimulus)
        if goodbye is not None:
            result["is_goodbye"] = True
            result["goodbye_text"] = goodbye
            return result

        # Increment turn
        self.turn_count += 1

        # --- Record moment ---
        moment = self.record_moment(stimulus, domains_hit, quality, tone, energy)
        result["moment"] = moment

        # --- SEQUENCE BONUS: juxtaposition scoring ---
        apply_sequence_bonus(self.moments)

        # --- 6. THE PAUSE ---
        if self.check_pause(stimulus, moment.resonance, moment.tag):
            result["should_pause"] = True

        # --- 2. POLAROID ---
        polaroid = self.check_polaroid()
        if polaroid:
            result["polaroid_text"] = polaroid
            result["annotations"].append(("polaroid", polaroid))

        # --- 4. CALLBACKS ---
        callback = self.check_callback(stimulus, domains_hit)
        if callback:
            result["annotations"].append(("callback", callback))

        # --- 7. THREAD PULL ---
        thread = self.check_thread_pull(stimulus)
        if thread:
            result["annotations"].append(("thread_pull", thread))

        # --- 8. DISAGREEMENT ---
        disagree = self.check_disagreement(stimulus)
        if disagree:
            result["annotations"].append(("disagreement", disagree))

        # --- 9. SUBLIME SERVICE ---
        gift = self.check_sublime_service(stimulus, domains_hit)
        if gift:
            result["annotations"].append(("sublime_service", gift))

        return result

    # -----------------------------------------------------------------
    # UTILITIES
    # -----------------------------------------------------------------

    def _detect_name(self, stimulus: str) -> None:
        """Try to extract user's name from their message."""
        s = stimulus.lower()
        for intro in self.name_intros:
            if intro in s:
                idx = s.index(intro) + len(intro)
                rest = stimulus[idx:].strip().split()[0] if idx < len(stimulus) else ""
                name = rest.strip(".,!?;:'\"")
                if name and len(name) > 1 and len(name) < 20:
                    self.user_name = name.capitalize()
                    return

    @staticmethod
    def _excerpt(text: str, max_words: int = 30) -> str:
        """Trim text to max_words, keeping it natural."""
        words = text.split()
        if len(words) <= max_words:
            return text.strip()
        return " ".join(words[:max_words]) + "..."

    def get_beautiful_moments(self) -> List[Moment]:
        """Return only the moments that passed the photogenic filter."""
        return [m for m in self.moments if m.is_beautiful]

    def get_stats(self) -> Dict[str, Any]:
        """Conversation stats for debugging / UI."""
        beautiful = self.get_beautiful_moments()
        return {
            "turns": self.turn_count,
            "total_moments": len(self.moments),
            "beautiful_moments": len(beautiful),
            "photogenic_ratio": len(beautiful) / max(len(self.moments), 1),
            "user_name": self.user_name,
            "current_energy": self.energy_tracker.current_energy,
            "energy_trend": self.energy_tracker.trend,
            "domains_seen": list(set(m.domain_hit for m in self.moments if m.domain_hit)),
            "tags_seen": list(set(m.tag for m in self.moments if m.tag != "ordinary")),
            "register": self.register.current_register,
        }


# ============================================================================
# REGISTER GATE â€” speak the language the LISTENER speaks
# ============================================================================

class RegisterGate:
    """
    RILIE speaks HUMAN unless the human speaks SCIENTIST.

    Detects the register of incoming language and gates outgoing
    language to match. A mortgage officer doesn't need thermodynamic
    states. A 14-year-old doesn't need apoptosis.

    Registers:
      - CASUAL:    everyday language. "check your ego at the door"
      - INFORMED:  educated but not specialist. "ego gets in the way of growth"
      - TECHNICAL: domain specialist. "ego â†’ 0 as asymptotic limit"
      - ACADEMIC:  research/paper level. "ego suppression follows exponential decay"

    Default: CASUAL. Always. Earn your way up.
    """

    def __init__(self):
        self.current_register: str = "casual"
        self.register_history: List[str] = []

    # --- Technical vocabulary detection ---
    TECHNICAL_MARKERS = [
        # Physics / Math
        "entropy", "thermodynamic", "asymptot", "eigenvalue", "hamiltonian",
        "lagrangian", "noether", "quantum", "relativistic", "spacetime",
        "derivative", "integral", "fourier", "gaussian", "stochastic",
        "topology", "manifold", "tensor", "vector field", "divergence",
        # Biology / Medical
        "apoptosis", "metastasis", "oncogene", "cytokine", "mitochond",
        "telomere", "epigenetic", "phenotype", "genotype", "angiogenesis",
        "pathogenesis", "etiology", "prognosis", "immunoglobulin",
        # Computer Science
        "algorithm", "heuristic", "polynomial", "np-hard", "recursive",
        "backpropagat", "gradient descent", "convolutional", "transformer",
        "tokeniz", "embedding", "latent space", "loss function",
        # Finance (technical)
        "sharpe ratio", "volatility surface", "black-scholes", "stochastic calculus",
        "monte carlo", "basis point", "yield curve", "convexity",
        # Philosophy (academic)
        "epistemolog", "ontolog", "phenomenolog", "hermeneutic",
        "dialectic", "teleolog", "deontolog", "consequential",
    ]

    ACADEMIC_MARKERS = [
        "hypothesis", "methodology", "empirical", "peer-reviewed",
        "statistically significant", "control group", "meta-analysis",
        "p-value", "confidence interval", "regression",
        "literature review", "citation", "abstract", "thesis",
    ]

    INFORMED_MARKERS = [
        # Someone who reads, thinks, but isn't publishing papers
        "in theory", "the concept of", "fundamentally",
        "the principle", "the mechanism", "structural",
        "systematic", "paradigm", "framework",
        "cognitive", "psychological", "sociological",
    ]

    def detect_register(self, stimulus: str) -> str:
        """
        Read incoming language and determine register.
        User sets the ceiling. RILIE never goes above it.
        """
        s = stimulus.lower()

        academic_hits = sum(1 for m in self.ACADEMIC_MARKERS if m in s)
        if academic_hits >= 2:
            register = "academic"
        elif any(m in s for m in self.TECHNICAL_MARKERS):
            register = "technical"
        elif any(m in s for m in self.INFORMED_MARKERS):
            register = "informed"
        else:
            register = "casual"

        self.register_history.append(register)
        # Current register = most common in last 3 turns (sticky)
        recent = self.register_history[-3:]
        from collections import Counter
        self.current_register = Counter(recent).most_common(1)[0][0]

        return self.current_register

    def translate(self, text: str) -> str:
        """
        Translate RILIE's internal jargon to the current register.

        Internal knowledge uses precise language (ego â†’ 0, entropy,
        apoptosis, etc). This translates to human when needed.
        """
        if self.current_register in ("technical", "academic"):
            # They speak science. Let her speak science.
            return text

        # --- CASUAL and INFORMED get human translations ---
        translations = {
            # Physics / framework jargon â†’ human
            "ego â†’ 0": "check your ego at the door",
            "ego approaching zero": "keep the ego in check â€” it blurs everything",
            "ego approaches zero": "ego stays out of it, vision clears up",
            "ego suppression": "not making it about yourself",
            "ego at zero": "ego out the door",
            "need for validation": "needing someone else to tell you you're good",
            "ego blur": "ego distorting what you actually see",
            "entropy": "disorder",
            "negentropy": "putting things back together",
            "thermodynamic": "energy",
            "equilibrium": "balance",
            "gradient": "difference that creates movement",
            "asymptotic": "getting closer but never quite arriving",
            "topology": "shape of things",
            "conservation": "nothing gets lost, just changes form",
            "momentum": "the force of keeping going",
            "spacetime": "the fabric of reality",

            # Biology â†’ human
            "apoptosis": "the quit button cells have",
            "metastasis": "when cancer spreads",
            "angiogenesis": "when tumors build their own blood supply",
            "oncogene": "a gene that went rogue",
            "cytokine": "chemical signals between cells",
            "mitochondria": "the engine inside every cell",
            "epigenetic": "how your environment changes your DNA's behavior",
            "phenotype": "how your genes actually show up",
            "telomere": "the protective cap on your DNA",
            "circadian": "your body's internal clock",
            "symbiosis": "living together because both sides win",

            # Game theory â†’ human
            "nash equilibrium": "the point where nobody benefits from changing",
            "prisoner's dilemma": "the trust test",
            "free rider": "someone who takes without giving",
            "mechanism design": "building the rules so people do the right thing naturally",
            "pareto optimal": "the best deal where nobody gets screwed",

            # Finance â†’ human
            "sharpe ratio": "return relative to risk",
            "volatility": "how much the price swings",
            "stochastic": "random but with patterns",
            "convexity": "how sensitive something is to change",
            "basis point": "one hundredth of a percent",

            # Framework terms â†’ human
            "density is destiny": "quality beats quantity",
            "claim must equal deed": "say what you do, do what you say",
            "awareness must exceed momentum": "think before you move",
            "signal density": "how strong the evidence is",
            "quality over quantity": "fewer but better",
            "anti-beige": "don't be boring, don't be basic",
            "mise en place": "get your ingredients ready before you cook",
            "discourse dictates disclosure": "the conversation decides what comes out",

            # Cosmology â†’ human
            "boolean": "yes or no, on or off, something or nothing",
            "fractal": "the same pattern repeating at every scale",
            "dark energy": "the invisible force pushing everything apart",
            "simulation hypothesis": "the idea that reality might be running on something",
        }

        result = text
        # Sort by length (longest first) to avoid partial replacements
        for jargon, human in sorted(translations.items(), key=lambda x: -len(x[0])):
            # Case-insensitive replacement
            pattern = re.compile(re.escape(jargon), re.IGNORECASE)
            result = pattern.sub(human, result)

        # Informed register keeps SOME technical flavor
        if self.current_register == "informed":
            # Restore a few terms that educated readers expect
            informed_keeps = {
                "disorder": "entropy (disorder)",
                "the quit button cells have": "programmed cell death",
                "the trust test": "the prisoner's dilemma",
            }
            for human_ver, informed_ver in informed_keeps.items():
                result = result.replace(human_ver, informed_ver)

        return result

    def get_register_guidance(self) -> Dict[str, str]:
        """Return guidance for response generation."""
        guidance = {
            "casual": {
                "register": "casual",
                "instruction": (
                    "Speak like a smart friend at a dinner table. "
                    "No jargon. No formulas. No academic language. "
                    "Say 'check your ego' not 'ego approaching zero.' "
                    "Say 'the quit button in cells' not 'apoptosis.' "
                    "If you can say it simpler, say it simpler."
                ),
            },
            "informed": {
                "register": "informed",
                "instruction": (
                    "They read. They think. They know some terminology. "
                    "Use concepts but explain the hard ones. "
                    "You can say 'entropy' but follow it with what you mean."
                ),
            },
            "technical": {
                "register": "technical",
                "instruction": (
                    "They speak the language. Use precise terminology. "
                    "Don't dumb it down. Ego â†’ 0, apoptosis, Nash equilibrium â€” "
                    "all fair game. They'll tell you if they need translation."
                ),
            },
            "academic": {
                "register": "academic",
                "instruction": (
                    "Full precision. Cite frameworks. Use formal language. "
                    "They're here for rigor, not vibes."
                ),
            },
        }
        return guidance.get(self.current_register, guidance["casual"])


# ============================================================================
# SEQUENCE BONUS â€” juxtaposition scoring
# ============================================================================

def apply_sequence_bonus(moments: List[Moment]) -> None:
    """
    Horror followed by humor. Grief followed by joy. Truth followed by absurdity.
    The juxtaposition IS the art. Score the PAIR higher than either alone.

    Mutates moments in place â€” bumps resonance when contrast is detected.

    "I failed at everything" â†’ "My grandma would've said go cook something"
    Both moments go UP because the contrast is beautiful.
    """
    if len(moments) < 2:
        return

    # Check last two moments
    prev = moments[-2]
    curr = moments[-1]

    # Define contrasting pairs (either direction)
    contrast_pairs = [
        # (heavy, light) â€” horror + humor
        ({"truth", "beauty_grief", "beauty_fear", "beauty_anger", "love"},
         {"beauty_humor", "beauty_joy", "beauty_wonder"}),
    ]

    for heavy_tags, light_tags in contrast_pairs:
        # Heavy â†’ Light (grief then joke)
        if prev.tag in heavy_tags and curr.tag in light_tags:
            bonus = 0.15
            prev.resonance = min(1.0, prev.resonance + bonus)
            curr.resonance = min(1.0, curr.resonance + bonus)
            curr.tag = curr.tag + "_juxtaposed"
            return

        # Light â†’ Heavy (joke then gut punch)
        if prev.tag in light_tags and curr.tag in heavy_tags:
            bonus = 0.15
            prev.resonance = min(1.0, prev.resonance + bonus)
            curr.resonance = min(1.0, curr.resonance + bonus)
            curr.tag = curr.tag + "_juxtaposed"
            return

    # Return to source after any high-resonance moment
    if (curr.tag == "return_to_source"
            and prev.is_beautiful
            and prev.tag != "return_to_source"):
        bonus = 0.1
        curr.resonance = min(1.0, curr.resonance + bonus)
        return
