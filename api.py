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
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from guvna import Guvna, LibraryIndex
from banks import ensure_curiosity_table
from curiosity import CuriosityEngine

logger = logging.getLogger("api")

# ---------------------------------------------------------------------------
# Base dir and .env loader (no external deps)
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent


def load_env_file(path: Path) -> None:
    """
    Minimal .env loader: KEY=VALUE per line, # comments allowed.
    Values in OS env win; .env only fills missing ones.
    """
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        os.environ.setdefault(key, value)


load_env_file(BASE_DIR / ".env")

# ---------------------------------------------------------------------------
# Paths and Roux loading (RILIE's 9-track soul)
# ---------------------------------------------------------------------------

ROUX_PATH = BASE_DIR / "ROUX.json"
RINITIALS_DIR = BASE_DIR / "RInitials"
GENERATED_DIR = BASE_DIR / "generated"


def load_roux() -> Dict[str, Dict[str, Any]]:
    """
    Load RILIE's 9-track roux from ROUX.json and the RInitials/*.txt files.
    The raw texts never leave this process; they are just used as invisible seeds.
    """
    if not ROUX_PATH.exists():
        return {}

    with ROUX_PATH.open("r", encoding="utf-8") as f:
        config = json.load(f)

    seeds: Dict[str, Dict[str, Any]] = {}
    for key, meta in config.items():
        file_name = meta.get("file")
        weight = meta.get("weight", 1.0)
        role = meta.get("role", "")
        text = ""
        if file_name:
            path = RINITIALS_DIR / file_name
            if path.exists():
                try:
                    text = path.read_text(encoding="utf-8")
                except Exception:
                    text = ""
        seeds[key] = {
            "text": text,
            "weight": float(weight),
            "role": role,
        }
    return seeds


GENERATED_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Catch 44 domain engines — library index builder
# ---------------------------------------------------------------------------
# One-time "study pass" for RILIE at boot. Each module is imported
# conditionally (graceful fallback if not yet present on disk).
# The index gives Guvna a structured map of what domain functions are
# available so she can pick the right tools per question.
# ---------------------------------------------------------------------------

def build_library_index() -> LibraryIndex:
    """
    One-time 'study pass' for RILIE.
    - Attempts to import each Catch-44 domain module via importlib.
    - Builds a lightweight index of key functions with tags.
    - Gracefully skips any module not present or with syntax errors.
    - importlib.import_module catches SyntaxError where bare import may not.
    """
    import importlib
    import importlib.util

    index: LibraryIndex = {}

    def _safe_import(module_name: str, index_key: str, tags: list) -> None:
        """Import a module safely, catching ALL errors including SyntaxError."""
        try:
            mod = importlib.import_module(module_name)
            index[index_key] = {
                "module": mod,
                "functions": {
                    name: getattr(mod, name)
                    for name in dir(mod)
                    if callable(getattr(mod, name, None))
                    and not name.startswith("_")
                },
                "tags": tags,
            }
            logger.info("Library index: %s loaded (%d functions)",
                         index_key, len(index[index_key]["functions"]))
        except Exception as e:
            logger.info("Library index: %s not available (%s: %s)",
                         index_key, type(e).__name__, e)

    # --- Physics ---
    _safe_import("physics", "physics",
        ["limits", "conservation", "time", "energy", "entropy",
         "mass", "velocity", "force", "quantum", "relativity"])

    # --- Life / biology ---
    _safe_import("life", "life",
        ["cancer", "health", "evolution", "ecosystems", "cell",
         "apoptosis", "mutation", "growth", "biology", "organism"])

    # --- Games / incentives ---
    _safe_import("games", "games",
        ["trust", "incentives", "governance", "coordination",
         "strategy", "reputation", "public good", "game theory",
         "nash", "prisoner"])

    # --- Thermodynamics / harm-repair ---
    _safe_import("thermodynamics", "thermodynamics",
        ["harm", "repair", "irreversibility", "cost", "entropy",
         "heat", "energy", "equilibrium", "damage", "restore"])

    # --- DuckSauce / universe kernel ---
    _safe_import("DuckSauce", "ducksauce",
        ["cosmology", "simulation", "universe", "boolean",
         "reality", "existence", "origin", "creation"])

    # --- ChompkyAtTheBit / NLP engine ---
    _safe_import("ChompkyAtTheBit", "chompky",
        ["language", "parsing", "nlp", "grammar", "syntax",
         "semantics", "chomsky", "linguistics", "tokenize"])

    # --- SOi sauc-e / main sauce engine (has hyphens in filename) ---
    try:
        soi_spec = importlib.util.spec_from_file_location(
            "soi_sauce", str(BASE_DIR / "SOi sauc-e.py")
        )
        if soi_spec and soi_spec.loader:
            soi_module = importlib.util.module_from_spec(soi_spec)
            soi_spec.loader.exec_module(soi_module)  # type: ignore
            index["soi_sauce"] = {
                "module": soi_module,
                "functions": {
                    name: getattr(soi_module, name)
                    for name in dir(soi_module)
                    if callable(getattr(soi_module, name, None))
                    and not name.startswith("_")
                },
                "tags": ["sauce", "framework", "catch44", "integration",
                         "architecture", "system", "core", "engine"],
            }
            logger.info("Library index: SOi sauc-e loaded (%d functions)",
                         len(index["soi_sauce"]["functions"]))
    except Exception as e:
        logger.info("Library index: SOi sauc-e not available (%s: %s)",
                     type(e).__name__, e)

    # --- SOiOS / OS layer ---
    _safe_import("SOiOS", "soios",
        ["os", "system", "kernel", "process", "runtime",
         "operating", "boot", "init"])

    # --- Network theory (if present) ---
    _safe_import("network_theory", "network_theory",
        ["karma", "network", "topology", "propagation",
         "cascade", "grace", "hub", "node", "dharma"])

    logger.info("Library index complete: %d domain engines loaded", len(index))
    return index


# ---------------------------------------------------------------------------
# Brave Search configuration (replaces Google Custom Search)
# ---------------------------------------------------------------------------

BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")
BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"

SearchFn = Callable[[str], List[Dict[str, str]]]


async def brave_web_search(
    query: str,
    num_results: int = 5,
) -> List[Dict[str, str]]:
    """
    Call Brave Search API and return a small, clean list of results
    with keys: title, link, snippet.
    """
    if not BRAVE_API_KEY:
        raise RuntimeError("Brave Search API not configured (BRAVE_API_KEY).")

    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": BRAVE_API_KEY,
    }
    params = {
        "q": query,
        "count": max(1, min(num_results, 10)),
    }

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
    """Synchronous wrapper so we can pass Brave into RILIE's SearchFn slot."""
    import asyncio
    return asyncio.run(brave_web_search(query, num_results))


HAS_BRAVE_SEARCH = bool(BRAVE_API_KEY)

# ---------------------------------------------------------------------------
# Google Vision OCR configuration (kept as-is)
# ---------------------------------------------------------------------------

GOOGLE_VISION_API_KEY = os.getenv("GOOGLE_VISION_API_KEY")
VISION_URL = "https://vision.googleapis.com/v1/images:annotate"


def google_ocr(image_bytes: bytes) -> str:
    """
    Call Google Cloud Vision OCR (TEXT_DETECTION) on raw image bytes and
    return the extracted text (fullTextAnnotation.text if available).
    """
    if not GOOGLE_VISION_API_KEY:
        raise RuntimeError("Google Vision OCR not configured (GOOGLE_VISION_API_KEY).")

    content_b64 = base64.b64encode(image_bytes).decode("utf-8")
    payload = {
        "requests": [{
            "image": {"content": content_b64},
            "features": [{"type": "TEXT_DETECTION"}],
        }]
    }

    url = VISION_URL + "?key=" + urllib.parse.quote(GOOGLE_VISION_API_KEY)
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
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
    return "\n".join(parts)


HAS_GOOGLE_VISION = bool(GOOGLE_VISION_API_KEY)

# ---------------------------------------------------------------------------
# BANKS configuration (PRE-RESPONSE target)
# ---------------------------------------------------------------------------

BANKS_URL = os.getenv("BANKS_URL", "http://127.0.0.1:8001")

# ---------------------------------------------------------------------------
# FastAPI app + The Governor (Act 5) + Library Index + Curiosity Engine
# ---------------------------------------------------------------------------

app = FastAPI(title="RILIE API", version="0.8.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Roux once at startup and wire it + search_fn into the Governor.
roux_seeds: Dict[str, Dict[str, Any]] = load_roux()

# Wire Brave into RILIE instead of Google
wired_search_fn: Optional[SearchFn] = brave_search_sync if HAS_BRAVE_SEARCH else None

# Build the library index — RILIE's one-time study pass of all domain engines.
# This gives her a structured map of what's available before any user talks.
library_index: LibraryIndex = build_library_index()

# The Governor now receives the library index + optional manifesto path.
guvna = Guvna(
    roux_seeds=roux_seeds,
    search_fn=wired_search_fn,
    library_index=library_index,
    manifesto_path=str(BASE_DIR / "CHARCULTERIE-MANIFESTO.docx"),
)

# ---------------------------------------------------------------------------
# Curiosity Engine — RILIE's subconscious
# ---------------------------------------------------------------------------

curiosity_engine = CuriosityEngine(
    search_fn=wired_search_fn,
    triangle_fn=None,  # Wire to Triangle later for full processing
    max_per_cycle=3,
    cycle_interval=60.0,
)

# ---------------------------------------------------------------------------
# Startup / Shutdown events
# ---------------------------------------------------------------------------

@app.on_event("startup")
def on_startup():
    """Boot sequence: ensure tables, start curiosity background thread."""
    # Ensure curiosity table exists
    try:
        ensure_curiosity_table()
        logger.info("Banks curiosity table ready.")
    except Exception as e:
        logger.warning("Could not ensure curiosity table on startup: %s", e)

    # Start the background curiosity thread
    if wired_search_fn:
        curiosity_engine.start_background()
        logger.info("Curiosity engine started — she thinks when nobody's talking.")
    else:
        logger.info("Curiosity engine idle — no search_fn wired.")

    # Log boot summary
    logger.info(
        "RILIE API v0.8.0 booted — Roux: %d tracks, Library: %d engines, "
        "Brave: %s, Vision: %s, Manifesto: %s",
        len(roux_seeds),
        len(library_index),
        "ON" if HAS_BRAVE_SEARCH else "OFF",
        "ON" if HAS_GOOGLE_VISION else "OFF",
        "LOADED" if guvna.self_state.constitution_loaded else "DEFAULTS",
    )


@app.on_event("shutdown")
def on_shutdown():
    """Clean shutdown: stop curiosity thread."""
    curiosity_engine.stop_background()
    logger.info("Curiosity engine stopped.")

# ---------------------------------------------------------------------------
# Serve RILIE client at root + static assets (3Dent.png, etc.)
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
# Pydantic models
# ---------------------------------------------------------------------------

class RilieRequest(BaseModel):
    stimulus: str
    max_pass: int = 3

class SearchRequest(BaseModel):
    query: str
    num_results: int = 5

class GenerateFileRequest(BaseModel):
    stimulus: str
    ext: str  # md, js, py, json, txt, docx, pdf

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

class PreResponseRequest(BaseModel):
    question: str
    shallow: bool = True
    numresults: int = 9

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
# Helpers for generated files
# ---------------------------------------------------------------------------

ALLOWED_EXTENSIONS = {"md", "js", "py", "json", "txt", "docx", "pdf"}


def sanitize_ext(ext: str) -> str:
    ext = ext.lower().lstrip(".")
    if ext not in ALLOWED_EXTENSIONS:
        return "txt"
    return ext


def save_generated_file(ext: str, content: str) -> str:
    """Save content into generated/ and return the filename."""
    ext = sanitize_ext(ext)
    ts = int(time.time())
    token = uuid.uuid4().hex[:8]
    filename = f"rilie_{ts}_{token}.{ext}"
    path = GENERATED_DIR / filename
    path.write_text(content, encoding="utf-8")
    return filename

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """
    Health check: confirms API is alive, roux is loaded,
    Brave/Vision configured, library index status, and curiosity engine status.
    """
    c_status = curiosity_engine.status()
    return HealthResponse(
        status="OK",
        has_brave_search=HAS_BRAVE_SEARCH,
        has_google_vision=HAS_GOOGLE_VISION,
        roux_tracks=len(roux_seeds),
        library_engines=len(library_index),
        architecture="5-act-guvna+library+curiosity",
        curiosity_queue=c_status["queue_size"],
        curiosity_kept=c_status["db_kept"],
        manifesto_loaded=guvna.self_state.constitution_loaded,
        dna_active=guvna.self_state.dna_active,
    )


@app.post("/v1/rilie")
def run_rilie(req: RilieRequest) -> Dict[str, Any]:
    """
    Main RILIE endpoint — routes through the Guvna (Act 5).
    The Governor delegates to RILIE (Act 4), which orchestrates Acts 1-3.
    After responding, any tangents generated are queued for curiosity.
    """
    stimulus = req.stimulus.strip()
    if not stimulus:
        return {
            "stimulus": "",
            "result": "Drop something in. A question, a thought, a vibe. Then hit Go.",
            "quality_score": 0.0,
            "priorities_met": 0,
            "anti_beige_score": 0.0,
            "status": "EMPTY",
            "depth": 0,
            "pass": 0,
        }

    result = guvna.process(stimulus, maxpass=req.max_pass)

    # If the Guvna produced tangents, queue them for curiosity
    tangents = result.get("tangents", [])
    queued_count = 0
    for t in tangents:
        if curiosity_engine.queue_tangent(
            tangent=t.get("text", ""),
            seed_query=stimulus,
            relevance=t.get("relevance", 0.3),
            interest=t.get("interest", 0.8),
        ):
            queued_count += 1

    if queued_count > 0:
        result["curiosity_queued"] = queued_count

    return result


@app.post("/v1/google_search")
async def google_search_endpoint(req: SearchRequest) -> Dict[str, Any]:
    """Thin wrapper around Brave Search API (legacy name)."""
    try:
        results = await brave_web_search(req.query, req.num_results)
        return {"query": req.query, "results": results, "status": "OK"}
    except Exception as e:
        return {"query": req.query, "results": [], "status": f"ERROR: {e}"}


@app.post("/v1/generate_file")
def generate_file(req: GenerateFileRequest) -> Dict[str, Any]:
    """
    Use RILIE to answer the stimulus, then save that answer as a file
    and return both the text and a download URL.
    """
    stimulus = req.stimulus.strip()
    if not stimulus:
        return {
            "stimulus": "",
            "ext": sanitize_ext(req.ext),
            "content": "",
            "status": "EMPTY",
            "filename": "",
            "download_url": "",
        }

    result = guvna.process(stimulus, maxpass=3)
    content = str(result.get("result", ""))
    ext = sanitize_ext(req.ext)
    filename = save_generated_file(ext, content)

    return {
        "stimulus": stimulus,
        "ext": ext,
        "content": content,
        "status": "OK",
        "filename": filename,
        "download_url": f"/download/{filename}",
    }


@app.get("/download/{filename}")
def download_file(filename: str):
    """Serve a previously generated file from the generated/ directory."""
    path = GENERATED_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(
        path,
        media_type="application/octet-stream",
        filename=filename,
    )


@app.post("/v1/ocr")
async def ocr_image(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Accept an image upload and return text extracted via Google Cloud Vision OCR."""
    try:
        image_bytes = await file.read()
        if not image_bytes:
            return {"filename": file.filename, "text": "", "status": "EMPTY"}
        text = google_ocr(image_bytes)
        return {"filename": file.filename, "text": text, "status": "OK"}
    except Exception as e:
        return {"filename": file.filename, "text": "", "status": f"ERROR: {e}"}


# ---------------------------------------------------------------------------
# PRE-RESPONSE endpoint
# ---------------------------------------------------------------------------

@app.post("/pre-response", response_model=PreResponseResponse)
async def pre_response(req: PreResponseRequest) -> PreResponseResponse:
    """
    PRE-RESPONSE pattern:
    - Brave-search the question, count results.
    - Later: expand across Roux grid and store in BANKS.
    """
    q = req.question.strip()
    if not q:
        return PreResponseResponse(
            question=q, shallow=req.shallow, harvested=0, status="EMPTY",
        )

    harvested = 0
    try:
        results = await brave_web_search(q, req.numresults)
        harvested = len(results)
    except Exception as e:
        return PreResponseResponse(
            question=q, shallow=req.shallow, harvested=0, status=f"ERROR: {e}",
        )

    return PreResponseResponse(
        question=q, shallow=req.shallow, harvested=harvested, status="OK",
    )


# ---------------------------------------------------------------------------
# Curiosity endpoints — peek into her subconscious
# ---------------------------------------------------------------------------

@app.get("/v1/curiosity/status")
def curiosity_status() -> Dict[str, Any]:
    """Full curiosity engine status — queue, stored insights, stats."""
    return curiosity_engine.status()


@app.post("/v1/curiosity/queue")
def curiosity_queue_add(req: CuriosityQueueRequest) -> Dict[str, Any]:
    """
    Manually queue a tangent for RILIE to explore.
    Useful for testing or for feeding her ideas directly.
    """
    queued = curiosity_engine.queue_tangent(
        tangent=req.tangent,
        seed_query=req.seed_query,
        relevance=req.relevance,
        interest=req.interest,
    )
    return {
        "tangent": req.tangent,
        "queued": queued,
        "queue_size": curiosity_engine.queue.size,
    }


@app.post("/v1/curiosity/drain")
def curiosity_drain() -> Dict[str, Any]:
    """
    Force-drain the curiosity queue right now.
    She processes her tangents immediately instead of waiting for the timer.
    """
    result = curiosity_engine.drain()
    return {
        "processed": result["processed"],
        "kept": result["kept"],
        "queue_remaining": curiosity_engine.queue.size,
    }


@app.get("/v1/curiosity/search")
def curiosity_search(q: str, limit: int = 5) -> Dict[str, Any]:
    """
    Search RILIE's self-generated insights.
    What has she been thinking about on her own?
    """
    from banks import search_curiosity
    hits = search_curiosity(q, limit=limit)
    return {
        "query": q,
        "results": hits,
        "count": len(hits),
    }


# ---------------------------------------------------------------------------
# Library index inspection endpoint
# ---------------------------------------------------------------------------

@app.get("/v1/library")
def library_status() -> Dict[str, Any]:
    """
    Inspect RILIE's library index — which domain engines are loaded,
    what functions are available, and what tags they respond to.
    """
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
# RILIE self-state inspection endpoint
# ---------------------------------------------------------------------------

@app.get("/v1/self")
def self_state() -> Dict[str, Any]:
    """
    Inspect RILIE's current self-state — who she thinks she is,
    her last quality score, any DNA violations, and social calibration.
    """
    ss = guvna.self_state
    soc = guvna.social_state
    return {
        "name": ss.name,
        "role": ss.role,
        "version": ss.version,
        "libraries": ss.libraries,
        "ethics_source": ss.ethics_source,
        "dna_active": ss.dna_active,
        "last_quality_score": ss.last_quality_score,
        "last_violations": ss.last_violations,
        "constitution_loaded": ss.constitution_loaded,
        "constitution_flags": ss.constitution_flags,
        "social": {
            "user_status": soc.user_status,
            "self_status": soc.self_status,
        },
    }
