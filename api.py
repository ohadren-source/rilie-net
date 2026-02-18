"""
api.py — RILIE API v0.9.0
==========================
Session persistence wired in.
She remembers who you are between visits.

Changes from v0.8.0:
  - Import session module
  - ensure_session_table() on startup
  - /v1/rilie: load session → process → save session
  - Request object passed for IP extraction
  - Christening result flows through to response
  - Topic recording after every turn
"""

import os
import json
import time
import uuid
import base64
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
import urllib.parse
import urllib.request

import httpx  # Brave HTTP client
from fastapi import FastAPI, HTTPException, Request, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from guvna import Guvna, LibraryIndex
from banks import ensure_curiosity_table
from curiosity import CuriosityEngine
from session import (
    ensure_session_table,
    load_session,
    save_session,
    get_client_ip,
    restore_guvna_state,
    snapshot_guvna_state,
    restore_talk_memory,
    snapshot_talk_memory,
    record_topics,
    DEFAULT_NAME,
)

logger = logging.getLogger("api")

# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent


def load_env_file(path: Path = None):
    """Minimal .env loader. KEY=VALUE per line, comments allowed."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


load_env_file(BASE_DIR / ".env")

# ---------------------------------------------------------------------------

ROUX_PATH = BASE_DIR / "ROUX.json"
R_INITIALS_DIR = BASE_DIR / "RInitials"
GENERATED_DIR = BASE_DIR / "generated"


def load_roux() -> Dict[str, Dict[str, Any]]:
    """Load RILIE's 9-track roux from ROUX.json and the RInitials .txt files."""
    if not ROUX_PATH.exists():
        return {}
    with ROUX_PATH.open("r", encoding="utf-8") as f:
        config = json.load(f)

    seeds: Dict[str, Dict[str, Any]] = {}
    for key, meta in config.items():
        filename = meta.get("file")
        weight = meta.get("weight", 1.0)
        role = meta.get("role", "text")
        if filename:
            path = R_INITIALS_DIR / filename
            if path.exists():
                try:
                    text = path.read_text(encoding="utf-8")
                except Exception:
                    text = ""
                seeds[key] = {"text": text, "weight": float(weight), "role": role}
    return seeds


GENERATED_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------


def build_library_index() -> LibraryIndex:
    """One-time study pass for RILIE. Import each Catch-44 domain module."""
    import importlib
    import importlib.util
    import sys

    library_dir = str(BASE_DIR / "library")
    if library_dir not in sys.path:
        sys.path.insert(0, library_dir)

    index: LibraryIndex = {}

    def safe_import(module_name: str, index_key: str, tags: list) -> None:
        try:
            mod = importlib.import_module(module_name)
            index[index_key] = {
                "module": mod,
                "functions": {
                    name: getattr(mod, name)
                    for name in dir(mod)
                    if callable(getattr(mod, name, None)) and not name.startswith("_")
                },
                "tags": tags,
            }
            logger.info("Library index: %s loaded (%d functions)",
                        index_key, len(index[index_key]["functions"]))
        except Exception as e:
            logger.info("Library index: %s not available (%s: %s)",
                        index_key, type(e).__name__, e)

    safe_import("physics", "physics", ["limits", "conservation", "time", "energy", "entropy", "mass", "velocity", "force", "quantum", "relativity"])
    safe_import("life", "life", ["cancer", "health", "evolution", "ecosystems", "cell", "apoptosis", "mutation", "growth", "biology", "organism"])
    safe_import("games", "games", ["trust", "incentives", "governance", "coordination", "strategy", "reputation", "public good", "game theory", "nash", "prisoner"])
    safe_import("thermodynamics", "thermodynamics", ["harm", "repair", "irreversibility", "cost", "entropy", "heat", "energy", "equilibrium", "damage", "restore"])
    safe_import("DuckSauce", "ducksauce", ["cosmology", "simulation", "universe", "boolean", "reality", "existence", "origin", "creation"])
    safe_import("ChomskyAtTheBit", "chomsky", ["language", "parsing", "nlp", "grammar", "syntax", "semantics", "chomsky", "linguistics", "tokenize"])

    # SOi sauc-e.py (has hyphens in filename)
    try:
        soi_spec = importlib.util.spec_from_file_location("soisauce", str(BASE_DIR / "SOi sauc-e.py"))
        if soi_spec and soi_spec.loader:
            soi_module = importlib.util.module_from_spec(soi_spec)
            soi_spec.loader.exec_module(soi_module)
            index["soisauce"] = {
                "module": soi_module,
                "functions": {
                    name: getattr(soi_module, name)
                    for name in dir(soi_module)
                    if callable(getattr(soi_module, name, None)) and not name.startswith("_")
                },
                "tags": ["sauce", "framework", "catch44", "integration", "architecture", "system", "core", "engine"],
            }
            logger.info("Library index: SOi sauc-e loaded (%d functions)",
                        len(index["soisauce"]["functions"]))
    except Exception as e:
        logger.info("Library index: SOi sauc-e not available (%s: %s)", type(e).__name__, e)

    safe_import("SOiOS", "soios", ["os", "system", "kernel", "process", "runtime", "operating", "boot", "init"])
    safe_import("networktheory", "networktheory", ["karma", "network", "topology", "propagation", "cascade", "grace", "hub", "node", "dharma"])
    safe_import("bigbang", "bigbang", ["universe", "boolean", "bang", "inflation", "radiation", "matter", "dark energy", "horizon", "stars", "quack"])
    safe_import("biochemuniverse", "biochemuniverse", ["biochem", "atp", "enzyme", "genotype", "cognition", "emergence", "soulpower", "flow", "gates", "dimensions"])
    safe_import("chemistry", "chemistry", ["molecule", "bond", "reaction", "catalyst", "ph", "stoichiometry", "gibbs", "resonance", "electronegativity", "concentration", "acid", "base", "element", "compound"])
    safe_import("civics", "civics", ["government", "rights", "voting", "amendment", "constitution", "federalism", "due process", "equal protection", "jury", "impeach", "democracy", "civic", "law", "justice"])
    safe_import("climatecatch44model", "climate", ["climate", "warming", "carbon", "emission", "temperature", "feedback", "tipping point", "atmosphere", "ocean", "weather"])
    safe_import("computerscience", "computerscience", ["algorithm", "complexity", "throughput", "big o", "hash", "tree", "consensus", "load", "compute", "data structure", "code", "software", "programming", "binary"])
    safe_import("deeptimegeo", "geology", ["geology", "erosion", "tectonic", "sediment", "fossil", "deep time", "threshold", "collapse", "irreversible", "earth", "mineral", "rock", "volcano", "earthquake"])
    safe_import("developmentalbio", "developmentalbio", ["development", "embryo", "critical period", "growth", "nurture", "child", "potential", "maturation", "stem cell", "differentiation", "aging", "birth", "pregnancy"])
    safe_import("ecology", "ecology", ["ecosystem", "species", "population", "carrying capacity", "keystone", "predator", "prey", "biodiversity", "habitat", "extinction", "food chain", "conservation", "nature"])
    safe_import("evolve", "evolution", ["evolution", "natural selection", "mutation", "adaptation", "cooperation", "exploit", "fitness", "survival", "darwin", "reproduction", "gene", "trait", "species"])
    safe_import("genomics", "genomics", ["genome", "dna", "rna", "gene", "crispr", "sequencing", "protein", "expression", "heredity", "chromosome", "genetic", "mutation", "epigenetic"])
    safe_import("linguisticscognition", "linguistics", ["language", "semantics", "syntax", "pragmatics", "cognition", "bilingual", "translation", "metaphor", "code switch", "broca", "wernicke", "meaning", "speech", "communication"])
    safe_import("nanotechnology", "nanotechnology", ["nano", "nanoscale", "self assembly", "swarm", "delivery", "coating", "surface", "molecular", "fabrication", "nanoparticle", "quantum dot", "microscale"])
    safe_import("QuantumTrading", "nighttrader", ["trading", "density", "signal", "market", "regime", "position", "risk", "portfolio", "stock", "finance", "investment", "capital", "hedge"])
    safe_import("urbandesign", "urbandesign", ["urban", "city", "district", "architecture", "housing", "affordable", "gentrification", "infrastructure", "civic", "zoning", "density", "community", "planning"])

    logger.info("Library index complete: %d domain engines loaded", len(index))
    return index


# ---------------------------------------------------------------------------
# Brave Search
# ---------------------------------------------------------------------------

BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")
BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"

SearchFn = Callable[[str], List[Dict[str, str]]]


async def brave_web_search(query: str, num_results: int = 5) -> List[Dict[str, str]]:
    """Call Brave Search API and return clean results."""
    if not BRAVE_API_KEY:
        raise RuntimeError("Brave Search API not configured (BRAVE_API_KEY).")
    headers = {"Accept": "application/json", "X-Subscription-Token": BRAVE_API_KEY}
    params = {"q": query, "count": max(1, min(num_results, 10))}
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(BRAVE_SEARCH_URL, headers=headers, params=params)
        resp.raise_for_status()
    data = resp.json()
    items: List[Dict[str, str]] = []
    for item in data.get("web", {}).get("results", []):
        items.append({
            "title": item.get("title", ""),
            "link": item.get("url", ""),
            "snippet": item.get("description", ""),
        })
    return items


def brave_search_sync(query: str, num_results: int = 5) -> List[Dict[str, str]]:
    """Synchronous Brave Search — safe to call from sync code inside async event loop."""
    if not BRAVE_API_KEY:
        raise RuntimeError("Brave Search API not configured (BRAVE_API_KEY).")
    headers = {"Accept": "application/json", "X-Subscription-Token": BRAVE_API_KEY}
    params = {"q": query, "count": max(1, min(num_results, 10))}
    with httpx.Client(timeout=10) as client:
        resp = client.get(BRAVE_SEARCH_URL, headers=headers, params=params)
        resp.raise_for_status()
    data = resp.json()
    items: List[Dict[str, str]] = []
    for item in data.get("web", {}).get("results", []):
        items.append({
            "title": item.get("title", ""),
            "link": item.get("url", ""),
            "snippet": item.get("description", ""),
        })
    return items


HAS_BRAVE_SEARCH = bool(BRAVE_API_KEY)

# ---------------------------------------------------------------------------
# Google Vision OCR
# ---------------------------------------------------------------------------

GOOGLE_VISION_API_KEY = os.getenv("GOOGLE_VISION_API_KEY")
VISION_URL = "https://vision.googleapis.com/v1/images:annotate"


def google_ocr(image_bytes: bytes) -> str:
    """Call Google Cloud Vision OCR on raw image bytes."""
    if not GOOGLE_VISION_API_KEY:
        raise RuntimeError("Google Vision OCR not configured (GOOGLE_VISION_API_KEY).")
    content_b64 = base64.b64encode(image_bytes).decode("utf-8")
    payload = {
        "requests": [{"image": {"content": content_b64}, "features": [{"type": "TEXT_DETECTION"}]}]
    }
    url = VISION_URL + "?key=" + urllib.parse.quote(GOOGLE_VISION_API_KEY)
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        resp_data = json.loads(resp.read().decode("utf-8"))
    responses = resp_data.get("responses", [])
    if not responses:
        return ""
    res0 = responses[0]
    full = res0.get("fullTextAnnotation", {})
    text = full.get("text")
    if text:
        return text
    ann = res0.get("textAnnotations", [])
    if not ann:
        return ""
    parts = [a.get("description", "") for a in ann]
    return " ".join(parts)


HAS_GOOGLE_VISION = bool(GOOGLE_VISION_API_KEY)

# ---------------------------------------------------------------------------
# Banks URL
# ---------------------------------------------------------------------------

BANKS_URL = os.getenv("BANKS_URL", "http://127.0.0.1:8001")

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="RILIE API", version="0.9.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Boot
# ---------------------------------------------------------------------------

roux_seeds: Dict[str, Dict[str, Any]] = load_roux()

wired_search_fn: Optional[SearchFn] = brave_search_sync if HAS_BRAVE_SEARCH else None

library_index: LibraryIndex = build_library_index()

guvna = Guvna(
    roux_seeds=roux_seeds,
    search_fn=wired_search_fn,
    library_index=library_index,
    manifesto_path=str(BASE_DIR / "CHARCULTERIE-MANIFESTO.docx"),
)

curiosity_engine = CuriosityEngine(
    search_fn=wired_search_fn,
    triangle_fn=None,
    max_per_cycle=3,
    cycle_interval=60.0,
)

# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

@app.on_event("startup")
def on_startup():
    """Boot sequence: ensure tables, start curiosity background thread."""
    try:
        ensure_curiosity_table()
        logger.info("Banks curiosity table ready.")
    except Exception as e:
        logger.warning("Could not ensure curiosity table on startup: %s", e)

    # --- NEW: Session table ---
    try:
        ensure_session_table()
        logger.info("Banks sessions table ready.")
    except Exception as e:
        logger.warning("Could not ensure sessions table on startup: %s", e)

    if wired_search_fn:
        curiosity_engine.start_background()
        logger.info("Curiosity engine started — she thinks when nobody's talking.")
    else:
        logger.info("Curiosity engine idle — no search_fn wired.")


@app.on_event("shutdown")
def on_shutdown():
    """Clean shutdown: stop curiosity thread."""
    curiosity_engine.stop_background()
    logger.info("Curiosity engine stopped.")


# ---------------------------------------------------------------------------
# Static / Client
# ---------------------------------------------------------------------------

@app.get("/")
def serve_client():
    """Serve the RILIE test console at root."""
    client_path = BASE_DIR / "rilie-client.html"
    if not client_path.exists():
        raise HTTPException(status_code=404, detail="Client HTML not found")
    return FileResponse(client_path, media_type="text/html")


app.mount("/static", StaticFiles(directory=str(BASE_DIR)), name="static")


# ---------------------------------------------------------------------------
# Boot log
# ---------------------------------------------------------------------------

logger.info(
    "RILIE API v0.9.0 booted | Roux: %d tracks | Library: %d engines | "
    "Brave: %s | Vision: %s | Manifesto: %s | Sessions: ON",
    len(roux_seeds), len(library_index),
    "ON" if HAS_BRAVE_SEARCH else "OFF",
    "ON" if HAS_GOOGLE_VISION else "OFF",
    "LOADED" if guvna.self_state.constitution_loaded else "DEFAULTS",
)

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class RilieRequest(BaseModel):
    stimulus: str
    max_pass: int = 3
    chef_mode: bool = False


class SearchRequest(BaseModel):
    query: str
    num_results: int = 5


class GenerateFileRequest(BaseModel):
    stimulus: str
    ext: str = "md"  # js, py, json, txt, docx, pdf


class HealthResponse(BaseModel):
    status: str
    has_brave_search: bool
    has_google_vision: bool
    roux_tracks: int
    library_engines: int
    architecture: str
    curiosity_queue: int
    curiosity_kept: int
    manifesto_loaded: bool
    dna_active: bool
    sessions_active: bool


class PreResponseRequest(BaseModel):
    question: str
    shallow: bool = True
    num_results: int = 9


class PreResponseResponse(BaseModel):
    question: str
    shallow: bool
    harvested: int
    status: str


class CuriosityQueueRequest(BaseModel):
    tangent: str
    seed_query: str = ""
    relevance: float = 0.2
    interest: float = 0.8


# ---------------------------------------------------------------------------
# Talk (the waitress)
# ---------------------------------------------------------------------------

from talk import talk, TalkMemory

talk_memory = TalkMemory()


def build_plate(raw_envelope):
    """Format the Guvna's output into a clean plate for the client."""
    result_text = raw_envelope.get("result", "")
    priorities_met = int(raw_envelope.get("priorities_met", 0) or 0)
    qs = raw_envelope.get("quality_scores", {})
    vibe = {}
    if qs:
        for p in ["amusing", "insightful", "nourishing", "compassionate", "strategic"]:
            vibe[p] = qs.get(p, 0) + 0.3
    else:
        for i, p in enumerate(["amusing", "insightful", "nourishing", "compassionate", "strategic"]):
            vibe[p] = i + priorities_met

    rs = str(raw_envelope.get("status", "OK")).upper()
    smap = {
        "COMPRESSED": "served", "OK": "served", "GUESS": "served",
        "DEJAVU": "revisited", "COURTESY_EXIT": "exploring",
        "DISCOURSE": "warming up", "SAFETY_REDIRECT": "redirected",
        "EMPTY": "waiting", "GREETING": "served", "PRIMER": "served",
        "GOODBYE": "served", "SELF_REFLECTION": "served",
        "RESEARCHED": "served", "TALK_EXHAUSTED": "thinking",
        "DEJAVU_BLOCKED": "revisited",
    }

    plate = {
        "result": result_text,
        "vibe": vibe,
        "status": smap.get(rs, "served"),
    }
    if "talk_attempts" in raw_envelope:
        plate["talk_attempts"] = raw_envelope["talk_attempts"]
    if "talk_rejections" in raw_envelope:
        plate["talk_rejections"] = raw_envelope["talk_rejections"]

    # --- NEW: Christening announcement ---
    if "christening" in raw_envelope and raw_envelope["christening"]:
        plate["christening"] = raw_envelope["christening"]

    return plate


# ---------------------------------------------------------------------------
# /v1/hello — DOORMAN → HOSTESS (name extraction, one call ever)
# ---------------------------------------------------------------------------

class HelloRequest(BaseModel):
    text: str = ""

@app.post("/v1/hello")
def hello(req: HelloRequest) -> Dict[str, str]:
    """
    Parse a name from whatever they typed. Return it.
    If no name found, return 'mate'. That's it. Hanzo.
    """
    text = (req.text or "").strip()
    if not text:
        return {"name": "mate"}

    # Common non-name responses
    _skip = {"hi", "hello", "hey", "sup", "yo", "ok", "okay", "no",
             "yes", "yeah", "nah", "nothing", "idk", "skip", "nope",
             "what", "who", "why", "how", "huh", "lol", "haha",
             "hi there", "hello there", "hey there"}

    # If they just typed a name (1-3 words, no question marks)
    clean = text.rstrip(".!?,;:)").strip()
    if clean.lower() in _skip:
        return {"name": "mate"}

    # Try to extract name from common patterns
    import re
    # "My name is X" / "I'm X" / "call me X" / "it's X" / "I am X"
    patterns = [
        r"(?:my name is|i'm|im|i am|call me|it's|its|they call me|people call me|name's|names)\s+([A-Za-z][A-Za-z\-']{0,20})",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return {"name": m.group(1).strip().title()}

    # If it's short and looks like just a name (1-2 words, no weird chars)
    words = clean.split()
    if 1 <= len(words) <= 5 and all(w.isalpha() and len(w) <= 20 for w in words):
        return {"name": clean.title()}

    # Couldn't parse — mate it is
    return {"name": "mate"}


# ---------------------------------------------------------------------------
# /v1/rilie — MAIN ENDPOINT (SESSION-AWARE)
# ---------------------------------------------------------------------------

@app.post("/v1/rilie")


def _is_multi_question_response(result: Dict[str, Any]) -> bool:
    """
    Check if the Kitchen/Guvna returned a multi-question response.

    Indicators:
    - status == "MULTI_QUESTION_SPLIT"
    - result contains "question_parts" or "multi_question_parts"
    - result text mentions "noticed" and "questions"
    """
    if not isinstance(result, dict):
        return False

    status = str(result.get("status", "")).upper()

    if status == "MULTI_QUESTION_SPLIT":
        return True

    if result.get("multi_question_parts"):
        return True

    if result.get("question_parts"):
        return True

    metadata = result.get("metadata", {}) or {}
    if isinstance(metadata, dict) and metadata.get("multi_question_parts"):
        return True

    result_text = str(result.get("result", "")).lower()
    if "noticed" in result_text and "questions" in result_text:
        return True

    return False


def _extract_question_parts(result: Dict[str, Any]) -> List[str]:
    """
    Extract the individual question parts from Kitchen/Guvna response.

    Kitchen may provide them in:
    - result["multi_question_parts"]
    - result["question_parts"]
    - result["metadata"]["multi_question_parts"]
    """
    if not isinstance(result, dict):
        return []

    if result.get("multi_question_parts"):
        return list(result["multi_question_parts"])

    if result.get("question_parts"):
        return list(result["question_parts"])

    metadata = result.get("metadata", {}) or {}
    if isinstance(metadata, dict) and metadata.get("multi_question_parts"):
        return list(metadata["multi_question_parts"])

    return []


def _process_multi_question_parts(
    parts: List[str],
    guvna_instance,
    max_pass: int = 3,
    session: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Process each question part separately through the full Guvna pipeline.

    Each part:
      1. Gets full guvna_instance.process() with all gates
      2. Generates its own response
      3. Gets its own quality_score, status, tone
      4. Is stored separately in results

    Returns:
      {
        "part_count": int,
        "parts": [ {index, question, result, status, quality_score, tone, response_type}, ... ],
        "combined_result": str,
        "all_passed": bool,
      }
    """
    part_results: List[Dict[str, Any]] = []

    for i, part in enumerate(parts, 1):
        if not part or not str(part).strip():
            continue

        text = str(part).strip()

        try:
            part_result = guvna_instance.process(text, maxpass=max_pass)
        except Exception as e:
            logger.error("Error processing multi-Q part %d: %s", i, e)
            part_result = {
                "result": f"Error processing question {i}",
                "status": "ERROR",
                "quality_score": 0.0,
                "tone": "neutral",
            }

        part_response = {
            "index": i,
            "question": text,
            "result": part_result.get("result", ""),
            "status": part_result.get("status", "OK"),
            "quality_score": part_result.get("quality_score", 0.0),
            "tone": part_result.get("tone", "neutral"),
            "response_type": part_result.get("response_type", {}),
        }

        part_results.append(part_response)

    combined_result = ""
    for part in part_results:
        combined_result += f"\n\n**Question {part['index']}: {part['question']}**\n\n"
        combined_result += str(part["result"])

    combined_result = combined_result.strip()

    all_passed = all(
        str(p.get("status", "")).upper() in ("OK", "GUESS", "BASELINE_WIN")
        for p in part_results
    )

    return {
        "part_count": len(part_results),
        "parts": part_results,
        "combined_result": combined_result,
        "all_passed": all_passed,
    }




@app.post("/v1/rilie")
def run_rilie(req: RilieRequest, request: Request) -> Dict[str, Any]:
    """
    Main RILIE endpoint — routes through the Guvna (Act 5).
    NOW SESSION-AWARE:
      1. Load session from Postgres by IP
      2. Restore Guvna + TalkMemory state from session
      3. Process the stimulus (with multi-question support)
      4. Run conversation memory behaviors (including Christening)
      5. Snapshot state back to session
      6. Save session to Postgres
      7. Return the plate
    """
    stimulus = req.stimulus.strip()
    if not stimulus:
        return {
            "stimulus": "",
            "result": "Drop something in. A question, a thought, a vibe. Then hit Go.",
            "quality_score": 0.0, "priorities_met": 0,
            "anti_beige_score": 0.0, "status": "EMPTY",
            "depth": 0, "pass": 0,
        }

    # --- 1. Load session ---
    client_ip = get_client_ip(request)
    session = load_session(client_ip)

    # --- 2. Restore state ---
    restore_guvna_state(guvna, session)
    restore_talk_memory(talk_memory, session)

    # --- 3. Process through Guvna ---
    result = guvna.process(stimulus, maxpass=req.max_pass)

    # --- 3b. Multi-question handling (NEW) ---
    if _is_multi_question_response(result):
        logger.info("MULTI_QUESTION detected: %s", stimulus[:120])

        parts = _extract_question_parts(result)
        if parts:
            multi = _process_multi_question_parts(
                parts=parts,
                guvna_instance=guvna,
                max_pass=req.max_pass,
                session=session,
            )

            # Aggregate quality scores across parts
            qs = [
                p.get("quality_score", 0.0)
                for p in multi["parts"]
                if isinstance(p.get("quality_score"), (int, float))
            ]
            combined_q = (
                sum(qs) / len(qs)
                if qs
                else float(result.get("quality_score", 0.0) or 0.0)
            )

            # Merge multi-question structure back into main result envelope
            result = {
                **result,
                "result": multi["combined_result"],
                "status": "MULTI_QUESTION_PROCESSED",
                "is_multi_question": True,
                "part_count": multi["part_count"],
                "parts": multi["parts"],
                "all_parts_passed": multi["all_passed"],
                "quality_score": combined_q,
            }

    # --- 4. Conversation memory behaviors ---
    # Extract domains and quality from result for memory recording
    domains_hit = result.get("domains_hit", [])
    quality = result.get("quality_score", 0.0)
    tone = result.get("tone", "insightful")

    # Run 10 behaviors (including Christening)
    mem_result = guvna.memory.process_turn(
        stimulus=stimulus,
        domains_hit=domains_hit,
        quality=quality,
        tone=tone,
        topics=session.get("topics", {}),
    )

    # If christening fired, add to result for plate
    if mem_result.get("christening"):
        result["christening"] = mem_result["christening"]
        # Update session name via session module
        from session import update_name

        session = update_name(
            session,
            mem_result["christening"]["nickname"],
            "christened",
        )

    # --- 5. Record topics for future Christening ---
    session = record_topics(
        session,
        domains_hit,
        [
            mem_result.get("moment", {}) and mem_result["moment"].tag
            if mem_result.get("moment")
            else ""
        ],
    )

    # --- 6. Talk (the waitress) ---
    def retry(stim):
        return guvna.process(stim, maxpass=req.max_pass)

    def self_search(sentence):
        try:
            results = brave_search_sync(sentence, num_results=1)
            if results:
                return results[0].get("snippet", "")
        except Exception:
            pass
        return ""

    def wilden_swift_score(text):
        from guvna import wilden_swift, WitState

        return wilden_swift(text, WitState())

    served = talk(
        plate=result,
        stimulus=stimulus,
        memory=talk_memory,
        max_retries=2,
        retry_fn=retry,
        search_fn=self_search,
        wilden_swift_fn=wilden_swift_score,
    )

    # --- 7. Snapshot state ---
    session = snapshot_guvna_state(guvna, session)
    session = snapshot_talk_memory(talk_memory, session)

    # --- 8. Save session ---
    save_session(session)

    # --- 9. Build and return plate ---
    if req.chef_mode:
        return served

    return build_plate(served)

# ---------------------------------------------------------------------------
# /v1/rilie (MULTIPART — file uploads with optional OCR)
# ---------------------------------------------------------------------------

@app.post("/v1/rilie-upload")
async def run_rilie_upload(
    request: Request,
    stimulus: str = Form(...),
    max_pass: int = Form(3),
    files: List[UploadFile] = File(default=[]),
) -> Dict[str, Any]:
    """
    Multipart version of /v1/rilie.
    Accepts files, OCRs images via Google Vision, prepends extracted text
    to the stimulus, then delegates to the same Guvna pipeline.
    """
    file_context_parts = []
    for f in files:
        raw_bytes = await f.read()
        if not raw_bytes:
            continue
        content_type = (f.content_type or "").lower()
        if content_type.startswith("image/"):
            # OCR via Google Vision
            try:
                ocr_text = google_ocr(raw_bytes)
                if ocr_text:
                    file_context_parts.append(f"[Image: {f.filename}]\n{ocr_text}")
            except Exception as e:
                file_context_parts.append(f"[Image: {f.filename} — OCR failed: {e}]")
        elif content_type.startswith("text/") or f.filename.endswith((".txt", ".md", ".csv", ".json", ".py", ".js", ".html")):
            # Plain text files — read directly
            try:
                text = raw_bytes.decode("utf-8", errors="replace")
                file_context_parts.append(f"[File: {f.filename}]\n{text}")
            except Exception:
                file_context_parts.append(f"[File: {f.filename} — could not decode]")
        elif f.filename.endswith(".docx"):
            # Word documents — extract text via python-docx
            try:
                import io
                from docx import Document
                doc = Document(io.BytesIO(raw_bytes))
                text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
                if text:
                    file_context_parts.append(f"[Document: {f.filename}]\n{text}")
                else:
                    file_context_parts.append(f"[Document: {f.filename} — no text found]")
            except Exception as e:
                file_context_parts.append(f"[Document: {f.filename} — parse failed: {e}]")
        else:
            file_context_parts.append(f"[File: {f.filename} — unsupported type: {content_type}]")

    # Prepend file context to stimulus
    if file_context_parts:
        file_block = "\n\n".join(file_context_parts)
        combined = f"{file_block}\n\n---\n\n{stimulus}"
    else:
        combined = stimulus

    # Delegate to the same pipeline via a synthetic RilieRequest
    req = RilieRequest(stimulus=combined, max_pass=max_pass)
    from starlette.concurrency import run_in_threadpool
    return await run_in_threadpool(run_rilie, req, request)
# ---------------------------------------------------------------------------

@app.get("/v1/curiosity/status")
def curiosity_status() -> Dict[str, Any]:
    return curiosity_engine.status()


@app.post("/v1/curiosity/queue")
def curiosity_queue_add(req: CuriosityQueueRequest) -> Dict[str, Any]:
    queued = curiosity_engine.queue_tangent(
        tangent=req.tangent, seed_query=req.seed_query,
        relevance=req.relevance, interest=req.interest,
    )
    return {"tangent": req.tangent, "queued": queued, "queue_size": curiosity_engine.queue.size}


@app.post("/v1/curiosity/drain")
def curiosity_drain() -> Dict[str, Any]:
    result = curiosity_engine.drain()
    return {"processed": result["processed"], "kept": result["kept"],
            "queue_remaining": curiosity_engine.queue.size}


@app.get("/v1/curiosity/search")
def curiosity_search(q: str, limit: int = 5) -> Dict[str, Any]:
    from banks import search_curiosity
    hits = search_curiosity(q, limit=limit)
    return {"query": q, "results": hits, "count": len(hits)}


# ---------------------------------------------------------------------------
# Library status
# ---------------------------------------------------------------------------

@app.get("/v1/library")
def library_status() -> Dict[str, Any]:
    summary = {}
    for domain_name, domain_info in library_index.items():
        summary[domain_name] = {
            "functions": list(domain_info.get("functions", {}).keys()),
            "tags": domain_info.get("tags", []),
            "function_count": len(domain_info.get("functions", {})),
        }
    return {
        "engines_loaded": len(library_index),
        "domains": summary,
        "dna_active": guvna.self_state.dna_active,
        "manifesto_loaded": guvna.self_state.constitution_loaded,
    }


# ---------------------------------------------------------------------------
# Self state
# ---------------------------------------------------------------------------

@app.get("/v1/self")
def self_state() -> Dict[str, Any]:
    ss = guvna.self_state
    soc = guvna.social_state
    return {
        "name": ss.name, "role": ss.role, "version": ss.version,
        "libraries": ss.libraries, "ethics_source": ss.ethics_source,
        "dna_active": ss.dna_active, "last_quality_score": ss.last_quality_score,
        "last_violations": ss.last_violations,
        "constitution_loaded": ss.constitution_loaded,
        "constitution_flags": ss.constitution_flags,
        "social": {"user_status": soc.user_status, "self_status": soc.self_status},
    }


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

@app.post("/v1/google-search")
async def google_search_endpoint(req: SearchRequest) -> Dict[str, Any]:
    try:
        results = await brave_web_search(req.query, req.num_results)
        return {"query": req.query, "results": results, "status": "OK"}
    except Exception as e:
        return {"query": req.query, "results": [], "status": f"ERROR: {e}"}


# ---------------------------------------------------------------------------
# Pre-response
# ---------------------------------------------------------------------------

@app.post("/pre-response", response_model=PreResponseResponse)
async def pre_response(req: PreResponseRequest) -> PreResponseResponse:
    q = req.question.strip()
    if not q:
        return PreResponseResponse(question=q, shallow=req.shallow, harvested=0, status="EMPTY")
    harvested = 0
    try:
        results = await brave_web_search(q, req.num_results)
        harvested = len(results)
    except Exception as e:
        return PreResponseResponse(question=q, shallow=req.shallow, harvested=0, status=f"ERROR: {e}")
    return PreResponseResponse(question=q, shallow=req.shallow, harvested=harvested, status="OK")


# ---------------------------------------------------------------------------
# File generation
# ---------------------------------------------------------------------------

ALLOWED_EXTENSIONS = {"md", "js", "py", "json", "txt", "docx", "pdf"}


def sanitize_ext(ext: str) -> str:
    ext = ext.lower().lstrip(".")
    if ext not in ALLOWED_EXTENSIONS:
        return "txt"
    return ext


def save_generated_file(ext: str, content: str) -> str:
    ext = sanitize_ext(ext)
    ts = int(time.time())
    token = uuid.uuid4().hex[:8]
    filename = f"rilie_{ts}_{token}.{ext}"
    path = GENERATED_DIR / filename
    path.write_text(content, encoding="utf-8")
    return filename


@app.post("/v1/generate-file")
def generate_file(req: GenerateFileRequest) -> Dict[str, Any]:
    stimulus = req.stimulus.strip()
    if not stimulus:
        return {"stimulus": "", "ext": sanitize_ext(req.ext), "content": "", "status": "EMPTY", "filename": "", "download_url": ""}
    result = guvna.process(stimulus, maxpass=3)
    content = str(result.get("result", ""))
    ext = sanitize_ext(req.ext)
    filename = save_generated_file(ext, content)
    return {
        "stimulus": stimulus, "ext": ext, "content": content,
        "status": "OK", "filename": filename,
        "download_url": f"/download/{filename}",
    }


@app.get("/download/{filename}")
def download_file(filename: str):
    path = GENERATED_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, media_type="application/octet-stream", filename=filename)


# ---------------------------------------------------------------------------
# OCR
# ---------------------------------------------------------------------------

@app.post("/v1/ocr")
async def ocr_image(file: UploadFile = File(...)) -> Dict[str, Any]:
    try:
        image_bytes = await file.read()
        if not image_bytes:
            return {"filename": file.filename, "text": "", "status": "EMPTY"}
        text = google_ocr(image_bytes)
        return {"filename": file.filename, "text": text, "status": "OK"}
    except Exception as e:
        return {"filename": file.filename, "text": "", "status": f"ERROR: {e}"}


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    c_status = curiosity_engine.status()
    return HealthResponse(
        status="OK",
        has_brave_search=HAS_BRAVE_SEARCH,
        has_google_vision=HAS_GOOGLE_VISION,
        roux_tracks=len(roux_seeds),
        library_engines=len(library_index),
        architecture="5-act-guvna+library+curiosity+session",
        curiosity_queue=c_status["queue_size"],
        curiosity_kept=c_status["db_kept"],
        manifesto_loaded=guvna.self_state.constitution_loaded,
        dna_active=guvna.self_state.dna_active,
        sessions_active=True,
    )
