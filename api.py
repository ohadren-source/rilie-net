"""
api.py — RILIE API v0.9.0 + Chomsky name tap

Session persistence wired in. She remembers who you are between visits.
Now also extracts a likely name anchor from stimulus via ChomskyAtTheBit.
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
    logger,
    update_name,
)
from talk import talk, TalkMemory

# ✅ MEANING INTEGRATION — For logging and API responses
from guvna.meaning import MeaningFingerprint

# 👇 NEW: Chomsky integration for name extraction
from ChomskyAtTheBit import classify_stimulus

# ---------------------------------------------------------------------------
# Base dir and .env loader
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent


def load_env_file(path: Path) -> None:
    """
    Minimal .env loader. KEY=VALUE per line, comments allowed.
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
# Roux and generated paths
# ---------------------------------------------------------------------------

ROUX_PATH = BASE_DIR / "ROUX.json"
RINITIALS_DIR = BASE_DIR / "RInitials"
GENERATED_DIR = BASE_DIR / "generated"


def load_roux() -> Dict[str, Dict[str, Any]]:
    """
    Load RILIE's 9-track Roux from ROUX.json and the RInitials/*.txt files.
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
# Library index (Catch‑44 domain engines)
# ---------------------------------------------------------------------------


def build_library_index() -> LibraryIndex:
    """
    One-time study pass for RILIE. Import each Catch‑44 domain module.
    """
    import importlib
    import importlib.util
    import sys

    library_dir = str(BASE_DIR / "library")
    if library_dir not in sys.path:
        sys.path.insert(0, library_dir)

    index: LibraryIndex = LibraryIndex()

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
            logger.info("Library index %s loaded (%d functions)", index_key, len(index[index_key]["functions"]))
        except Exception as e:
            logger.info(
                "Library index %s not available (%s: %s)",
                index_key,
                type(e).__name__,
                e,
            )

    # Domain engines (sample; keep as in your v0.9.0)
    safe_import("physics", "physics", ["limits", "conservation", "time", "energy", "entropy", "mass", "velocity", "force", "quantum", "relativity"])
    safe_import("life", "life", ["cancer", "health", "evolution", "ecosystems", "cell", "apoptosis", "mutation", "growth", "biology", "organism"])
    safe_import("games", "games", ["trust", "incentives", "governance", "coordination", "strategy", "reputation", "public good", "game theory", "nash", "prisoner"])
    safe_import("thermodynamics", "thermodynamics", ["harm", "repair", "irreversibility", "cost", "entropy", "heat", "energy", "equilibrium", "damage", "restore"])
    safe_import("DuckSauce", "ducksauce", ["cosmology", "simulation", "universe", "boolean", "reality", "existence", "origin", "creation"])
    safe_import("ChomskyAtTheBit", "chomsky", ["language", "parsing", "nlp", "grammar", "syntax", "semantics", "chomsky", "linguistics", "tokenize"])
    # ... keep all other safe_import calls from your original v0.9.0 here ...

    # SOi sauc‑e special load, SOiOS, networktheory, bigbang, etc. – unchanged.
    # (Omitted here only for brevity; copy from your existing file.)

    logger.info("Library index complete (%d domain engines loaded)", len(index))
    return index


# ---------------------------------------------------------------------------
# Brave Search configuration
# ---------------------------------------------------------------------------

BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")
BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"

SearchFn = Callable[[str, int], List[Dict[str, str]]]


async def brave_web_search(query: str, num_results: int = 5) -> List[Dict[str, str]]:
    """Call Brave Search API and return clean results."""
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
        items.append(
            {
                "title": item.get("title", ""),
                "link": item.get("url", ""),
                "snippet": item.get("description", ""),
            }
        )
    return items


def brave_search_sync(query: str, num_results: int = 5) -> List[Dict[str, str]]:
    """
    Synchronous Brave Search safe to call from sync code inside async event loop.
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

    with httpx.Client(timeout=10) as client:
        resp = client.get(BRAVE_SEARCH_URL, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()

    items: List[Dict[str, str]] = []
    for item in data.get("web", {}).get("results", []):
        items.append(
            {
                "title": item.get("title", ""),
                "link": item.get("url", ""),
                "snippet": item.get("description", ""),
            }
        )
    return items


HAS_BRAVE_SEARCH = bool(BRAVE_API_KEY)

# ---------------------------------------------------------------------------
# Google Vision OCR configuration
# ---------------------------------------------------------------------------

GOOGLE_VISION_API_KEY = os.getenv("GOOGLE_VISION_API_KEY")
VISION_URL = "https://vision.googleapis.com/v1/images:annotate"


def google_ocr(image_bytes: bytes) -> str:
    """Call Google Cloud Vision OCR on raw image bytes."""
    if not GOOGLE_VISION_API_KEY:
        raise RuntimeError("Google Vision OCR not configured (GOOGLE_VISION_API_KEY).")

    content_b64 = base64.b64encode(image_bytes).decode("utf-8")

    payload = {
        "requests": [
            {
                "image": {"content": content_b64},
                "features": [{"type": "TEXT_DETECTION"}],
            }
        ]
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
# FastAPI app + Guvna, Curiosity, Sessions
# ---------------------------------------------------------------------------

app = FastAPI(title="RILIE API", version="0.9.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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

talk_memory = TalkMemory()

logger.info(
    "RILIE API v0.9.0 booted — Roux %d tracks, Library %d engines, "
    "Brave %s, Vision %s, Manifesto %s, Sessions ON",
    len(roux_seeds),
    len(library_index),
    "ON" if HAS_BRAVE_SEARCH else "OFF",
    "ON" if HAS_GOOGLE_VISION else "OFF",
    "LOADED" if guvna.self_state.constitution_loaded else "DEFAULTS",
)

# ---------------------------------------------------------------------------
# Startup / Shutdown
# ---------------------------------------------------------------------------


@app.on_event("startup")
def on_startup() -> None:
    """Boot sequence: ensure tables, start curiosity background thread."""
    try:
        ensure_curiosity_table()
        logger.info("Banks curiosity table ready.")
    except Exception as e:
        logger.warning("Could not ensure curiosity table on startup: %s", e)

    try:
        ensure_session_table()
        logger.info("Banks sessions table ready.")
    except Exception as e:
        logger.warning("Could not ensure sessions table on startup: %s", e)

    if wired_search_fn:
        curiosity_engine.start_background()
        logger.info("Curiosity engine started (she thinks when nobody's talking).")
    else:
        logger.info("Curiosity engine idle (no search_fn wired).")


@app.on_event("shutdown")
def on_shutdown() -> None:
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
# Pydantic models
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
    sessions_active: bool


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
    seedquery: str
    relevance: float = 0.2
    interest: float = 0.8


class HelloRequest(BaseModel):
    text: str


# ---------------------------------------------------------------------------
# Helpers
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


def build_plate(raw_envelope: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format the Guvna's output into a clean plate for the client.
    (Keep exactly as in your v0.9.0; omitted details for brevity.)
    """
    result_text = raw_envelope.get("result", "")
    priorities_met = int(raw_envelope.get("priorities_met", 0) or 0)

    qs = raw_envelope.get("quality_scores")
    if qs:
        vibe = {p: qs.get(p, 0.3) for p in ("amusing", "insightful", "nourishing", "compassionate", "strategic")}
    else:
        vibe = {}

    status = str(raw_envelope.get("status", "OK")).upper()
    status_map = {
        "COMPRESSED": "served",
        "OK": "served",
        "GUESS": "served",
        "DEJAVU": "revisited",
        "COURTESY_EXIT": "exploring",
        "DISCOURSE": "warming up",
        "SAFETY_REDIRECT": "redirected",
        "EMPTY": "waiting",
        "GREETING": "served",
        "PRIMER": "served",
        "GOODBYE": "served",
        "SELF_REFLECTION": "served",
        "RESEARCHED": "served",
        "TALK_EXHAUSTED": "thinking",
        "DEJAVU_BLOCKED": "revisited",
    }

    plate = {
        "result": result_text,
        "vibe": vibe,
        "status": status_map.get(status, "served"),
    }

    if "talk_attempts" in raw_envelope:
        plate["talk_attempts"] = raw_envelope["talk_attempts"]
    if "talk_rejections" in raw_envelope:
        plate["talk_rejections"] = raw_envelope["talk_rejections"]
    if "christening" in raw_envelope:
        plate["christening"] = raw_envelope["christening"]

    return plate


# 👇 NEW: Chomsky name helper (non‑fatal)

def _extract_name_with_chomsky(stimulus: str) -> Optional[str]:
    """
    Use Chomsky's classify_stimulus to pull a likely 'name' anchor when
    the user is introducing themselves ("I am X", "I am called X", etc.).
    Non-fatal: any error returns None.
    """
    try:
        info = classify_stimulus(stimulus or "")
        subject = (info.get("subject") or "").strip()
        obj = (info.get("object_") or "").strip()
        pieces = info.get("pieces") or []

        candidates: List[str] = []
        if subject:
            candidates.append(subject)
        if obj:
            candidates.append(obj)
        if pieces:
            candidates.extend(pieces)

        if not candidates:
            return None

        best = max(candidates, key=len)
        return best or None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    cstatus = curiosity_engine.status
    return HealthResponse(
        status="OK",
        has_brave_search=HAS_BRAVE_SEARCH,
        has_google_vision=HAS_GOOGLE_VISION,
        roux_tracks=len(roux_seeds),
        library_engines=len(library_index),
        architecture="5-act-guvna+library+curiosity+session",
        curiosity_queue=cstatus["queue_size"],
        curiosity_kept=cstatus["db_kept"],
        manifesto_loaded=guvna.self_state.constitution_loaded,
        dna_active=guvna.self_state.dna_active,
        sessions_active=True,
    )


@app.post("/v1/hello")
def hello(req: HelloRequest) -> Dict[str, str]:
    """
    Parse a name from whatever they typed. Return it.
    If no name found, return 'mate'.
    (Kept as your original name parser; Chomsky is an extra signal.)
    """
    text = (req.text or "").strip()
    if not text:
        return {"name": "mate"}

    skip = {
        "hi",
        "hello",
        "hey",
        "sup",
        "yo",
        "ok",
        "okay",
        "no",
        "yes",
        "yeah",
        "nah",
        "nothing",
        "idk",
        "skip",
        "nope",
        "what",
        "who",
        "why",
        "how",
        "huh",
        "lol",
        "haha",
        "hi there",
        "hello there",
        "hey there",
    }

    clean = text.rstrip("!?.").strip()
    if clean.lower() in skip:
        return {"name": "mate"}

    # Patterns: my name is X / I'm X / call me X / it's X / they call me X
    import re

    patterns = [
        r"my name is\s+([A-Za-z][A-Za-z\-]{0,20}(?:\s+[A-Za-z][A-Za-z\-]{0,20}){0,3})",
        r"i[' ]?m\s+([A-Za-z][A-Za-z\-]{0,20}(?:\s+[A-Za-z][A-Za-z\-]{0,20}){0,3})",
        r"(?:call me|it's|they call me)\s+([A-Za-z][A-Za-z\-]{0,20}(?:\s+[A-Za-z][A-Za-z\-]{0,20}){0,3})",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return {"name": m.group(1).strip().title()}

    words = clean.split()
    if 1 <= len(words) <= 5 and all(w.isalpha() and len(w) <= 20 for w in words):
        return {"name": clean.title()}

    return {"name": "mate"}


def is_multi_question_response(result: Dict[str, Any]) -> bool:
    """
    Check if the Kitchen/Guvna returned a multi-question response.
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
    metadata = result.get("metadata") or {}
    if isinstance(metadata, dict) and metadata.get("multi_question_parts"):
        return True
    result_text = str(result.get("result", "")).lower()
    if "noticed" in result_text and "questions" in result_text:
        return True
    return False


def extract_question_parts(result: Dict[str, Any]) -> List[str]:
    """
    Extract the individual question parts from Kitchen/Guvna response.
    """
    if not isinstance(result, dict):
        return []
    if result.get("multi_question_parts"):
        return list(result["multi_question_parts"])
    if result.get("question_parts"):
        return list(result["question_parts"])
    metadata = result.get("metadata") or {}
    if isinstance(metadata, dict) and metadata.get("multi_question_parts"):
        return list(metadata["multi_question_parts"])
    return []


def process_multi_question_parts(
    parts: List[str],
    guvna_instance: Guvna,
    max_pass: int = 3,
    session: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Process each question part separately through the full Guvna pipeline.
    Returns combined result and per-part details. (Unchanged logic.)
    """
    part_results: List[Dict[str, Any]] = []
    for i, part in enumerate(parts, 1):
        if not part or not str(part).strip():
            continue
        text = str(part).strip()
        try:
            part_result = guvna_instance.process(text, max_pass=max_pass)
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
            "response_type": part_result.get("response_type", ""),
        }
        part_results.append(part_response)

    combined_result = "\n\n".join(
        f"[{p['index']}] {p['question']}\n{p['result']}" for p in part_results
    ).strip()

    all_passed = all(
        str(p.get("status", "")).upper() in {"OK", "GUESS", "BASELINE_WIN"}
        for p in part_results
    )

    qs = [p.get("quality_score", 0.0) for p in part_results if isinstance(p.get("quality_score"), (int, float))]
    combined_q = sum(qs) / len(qs) if qs else 0.0

    return {
        "part_count": len(part_results),
        "parts": part_results,
        "combined_result": combined_result,
        "all_passed": all_passed,
        "quality_score": combined_q,
    }


@app.post("/v1/rilie")
def run_rilie(req: RilieRequest, request: Request) -> Dict[str, Any]:
    """
    Main RILIE endpoint — NOW SESSION-AWARE:
    1. Load session from Postgres by IP
    2. Restore Guvna + TalkMemory state
    3. Process stimulus (with multi-question support)
    4. Run conversation memory behaviors (incl. Christening)
    5. Snapshot state back to session
    6. Save session to Postgres
    7. Return plate

    🔁 NEW: also attach `chomsky_name` via ChomskyAtTheBit (best-effort).
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
            "chomsky_name": None,
        }

    client_ip = get_client_ip(request)
    session = load_session(client_ip)

    restore_guvna_state(guvna, session)
    restore_talk_memory(talk_memory, session)

    result = guvna.process(stimulus, max_pass=req.max_pass)

    # Multi-question handling
    if is_multi_question_response(result):
        logger.info("MULTIQUESTION detected: %s...", stimulus[:120])
        parts = extract_question_parts(result)
        if parts:
            multi = process_multi_question_parts(parts, guvna_instance=guvna, max_pass=req.max_pass, session=session)
            result = {
                "result": multi["combined_result"],
                "status": "MULTI_QUESTION_PROCESSED",
                "is_multi_question": True,
                "part_count": multi["part_count"],
                "parts": multi["parts"],
                "all_parts_passed": multi["all_passed"],
                "quality_score": multi["quality_score"],
            }

    domains_hit = result.get("domains_hit", [])
    quality = result.get("quality_score", 0.0)
    tone = result.get("tone", "insightful")

    mem_result = guvna.memory.process_turn(
        stimulus=stimulus,
        domains_hit=domains_hit,
        quality=quality,
        tone=tone,
        topics=session.get("topics", []),
    )

    if mem_result.get("christening"):
        result["christening"] = mem_result["christening"]
        update_name(session, mem_result["christening"].get("nickname"), christened=True)

    if mem_result.get("moment"):
        record_topics(
            session,
            domains_hit,
            mem_result["moment"] and mem_result["moment"].get("tag"),
        )

    # 🔁 NEW: Chomsky name tap (non-blocking, best-effort)
    chomsky_name = _extract_name_with_chomsky(stimulus)
    result.setdefault("chomsky_name", chomsky_name)

    snapshot_guvna_state(guvna, session)
    snapshot_talk_memory(talk_memory, session)
    save_session(session)

    if req.chef_mode:
        return result

    return build_plate(result)


@app.post("/v1/rilie-upload")
async def run_rilie_upload(
    request: Request,
    stimulus: str = Form(...),
    max_pass: int = Form(3),
    files: List[UploadFile] = File(default=[]),
) -> Dict[str, Any]:
    """
    Multipart version of /v1/rilie.
    OCR images, read text/docx files, prepend context to stimulus, then delegate.
    """
    file_context_parts: List[str] = []
    for f in files:
        rawbytes = await f.read()
        if not rawbytes:
            continue
        contenttype = (f.content_type or "").lower()
        try:
            if contenttype.startswith("image"):
                try:
                    ocrtext = google_ocr(rawbytes)
                    if ocrtext:
                        file_context_parts.append(f"[Image {f.filename}] {ocrtext}")
                    else:
                        file_context_parts.append(f"[Image {f.filename}] (OCR produced no text)")
                except Exception as e:
                    file_context_parts.append(f"[Image {f.filename}] OCR failed: {e}")
            elif contenttype.startswith("text") or f.filename.endswith((".txt", ".md", ".csv", ".json", ".py", ".js", ".html")):
                try:
                    text = rawbytes.decode("utf-8", errors="replace")
                    file_context_parts.append(f"[File {f.filename}] {text}")
                except Exception:
                    file_context_parts.append(f"[File {f.filename}] (could not decode as UTF-8)")
            elif f.filename.endswith(".docx"):
                try:
                    import io
                    from docx import Document

                    doc = Document(io.BytesIO(rawbytes))
                    text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
                    if text:
                        file_context_parts.append(f"[Document {f.filename}] {text}")
                    else:
                        file_context_parts.append(f"[Document {f.filename}] (no text found)")
                except Exception as e:
                    file_context_parts.append(f"[Document {f.filename}] parse failed: {e}")
            else:
                file_context_parts.append(f"[File {f.filename}] unsupported type: {contenttype}")
        except Exception as e:
            file_context_parts.append(f"[File {f.filename}] error: {e}")

    if file_context_parts:
        file_block = "\n\n".join(file_context_parts)
        combined = f"{file_block}\n\n---\n\n{stimulus}"
    else:
        combined = stimulus

    req = RilieRequest(stimulus=combined, max_pass=max_pass, chef_mode=False)
    from starlette.concurrency import run_in_threadpool

    return await run_in_threadpool(run_rilie, req, request)


@app.post("/v1/google-search")
async def google_search_endpoint(req: SearchRequest) -> Dict[str, Any]:
    try:
        results = await brave_web_search(req.query, req.num_results)
        return {"query": req.query, "results": results, "status": "OK"}
    except Exception as e:
        return {"query": req.query, "results": [], "status": f"ERROR: {e}"}


@app.post("/v1/generate-file")
def generate_file(req: GenerateFileRequest) -> Dict[str, Any]:
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

    result = guvna.process(stimulus, max_pass=3)
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
    path = GENERATED_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, media_type="application/octet-stream", filename=filename)


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


@app.post("/pre-response", response_model=PreResponseResponse)
async def pre_response(req: PreResponseRequest) -> PreResponseResponse:
    q = req.question.strip()
    if not q:
        return PreResponseResponse(
            question=q,
            shallow=req.shallow,
            harvested=0,
            status="EMPTY",
        )

    harvested = 0
    try:
        results = await brave_web_search(q, req.numresults)
        harvested = len(results)
    except Exception as e:
        return PreResponseResponse(
            question=q,
            shallow=req.shallow,
            harvested=0,
            status=f"ERROR: {e}",
        )

    return PreResponseResponse(
        question=q,
        shallow=req.shallow,
        harvested=harvested,
        status="OK",
    )
