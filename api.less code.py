"""
api.py — RILIE API v0.9.0 + Chomsky name tap (Fixed)

Session persistence wired in. She remembers who you are between visits.

Now also extracts a likely name anchor from stimulus via ChomskyAtTheBit,
and uses it as a canonical `display_name` across the conversation.

Fixes applied:
- Enhanced name extraction with spaCy NER priority for PERSON entities.
- Expanded regex heuristics for common intro patterns ("I am called", etc.).
- Safeguard against bad/verb-based names like "introduce" or "called".
- Added intro_attempts session counter to detect and exit greeting loops.
- Pivot to "What's on your mind?" after 1 failed intro, using fallback name "friend".
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
# from guvna.meaning import MeaningFingerprint

# 👇 NEW: Chomsky integration for name extraction
from ChomskyAtTheBit import classify_stimulus, parse_question  # Added parse_question for NER

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

    # LibraryIndex is a typing alias; use a plain dict at runtime.
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
            logger.info(
                "Library index %s loaded (%d functions)",
                index_key,
                len(index[index_key]["functions"]),
            )
        except Exception as e:
            logger.info(
                "Library index %s not available (%s: %s)",
                index_key,
                type(e).__name__,
                e,
            )

    # Domain engines (sample; keep as in your v0.9.0)
    safe_import(
        "physics",
        "physics",
        [
            "limits",
            "conservation",
            "time",
            "energy",
            "entropy",
            "mass",
            "velocity",
            "force",
            "quantum",
            "relativity",
        ],
    )
    safe_import(
        "life",
        "life",
        [
            "cancer",
            "health",
            "evolution",
            "ecosystems",
            "cell",
            "apoptosis",
            "mutation",
            "growth",
            "biology",
            "organism",
        ],
    )
    safe_import(
        "games",
        "games",
        [
            "trust",
            "incentives",
            "governance",
            "coordination",
            "strategy",
            "reputation",
            "public good",
            "game theory",
            "nash",
            "prisoner",
        ],
    )
    safe_import(
        "thermodynamics",
        "thermodynamics",
        [
            "harm",
            "repair",
            "irreversibility",
            "cost",
            "entropy",
            "heat",
            "energy",
            "equilibrium",
            "damage",
            "restore",
        ],
    )
    safe_import(
        "DuckSauce",
        "ducksauce",
        [
            "cosmology",
            "simulation",
            "universe",
            "boolean",
            "reality",
            "existence",
            "origin",
            "creation",
        ],
    )
    safe_import(
        "ChomskyAtTheBit",
        "chomsky",
        [
            "language",
            "parsing",
            "nlp",
            "grammar",
            "syntax",
            "semantics",
            "chomsky",
            "linguistics",
            "tokenize",
        ],
    )

    # ... keep all other safe_import calls from your original v0.9.0 here ...
    # SOi sauce, SOiOS, network theory, bigbang, etc. – unchanged.

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

    resp = httpx.get(BRAVE_SEARCH_URL, headers=headers, params=params, timeout=10)
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


# ---------------------------------------------------------------------------
# Google Vision OCR for images
# ---------------------------------------------------------------------------

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_OCR_URL = "https://vision.googleapis.com/v1/images:annotate"


def google_ocr(image_bytes: bytes) -> str:
    """
    Call Google Vision API for OCR.
    """
    if not GOOGLE_API_KEY:
        raise RuntimeError("Google Vision API not configured (GOOGLE_API_KEY).")

    b64image = base64.b64encode(image_bytes).decode("utf-8")

    payload = {
        "requests": [
            {
                "image": {"content": b64image},
                "features": [{"type": "TEXT_DETECTION"}],
            }
        ]
    }

    params = {"key": GOOGLE_API_KEY}
    resp = httpx.post(
        GOOGLE_OCR_URL,
        params=params,
        json=payload,
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()

    texts = data.get("responses", [{}])[0].get("textAnnotations", [])
    if texts:
        return texts[0].get("description", "").strip()
    return ""


# ---------------------------------------------------------------------------
# Name extraction helpers (enhanced with NER and regex)
# ---------------------------------------------------------------------------

import re
from ChomskyAtTheBit import _get_nlp  # Import spaCy loader from Chomsky

def _extract_name_with_heuristics(stimulus: str) -> Optional[str]:
    """
    Regex-based name extraction with expanded patterns for common intros.
    """
    patterns = [
        r"(?:I am|I'm|my name is|call me|I am called|introduce myself(?: as)?|called)\s+([A-Za-z\s'-]+?)(?:$|\s*[.,!?]|A man of)",
        r"([A-Z][a-zA-Z'-]+(?:\s+[A-Z][a-zA-Z'-]+)+)",  # Multi-word capitalized fallback
    ]
    for pat in patterns:
        match = re.search(pat, stimulus, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if name:  # Avoid empty
                return name
    return None

def _extract_name_with_ner(stimulus: str) -> Optional[str]:
    """
    Use spaCy NER for PERSON entities.
    """
    nlp = _get_nlp()
    doc = nlp(stimulus)
    persons = [ent.text.strip() for ent in doc.ents if ent.label_ == "PERSON"]
    if persons:
        # Take longest (handles multi-word names)
        return max(persons, key=len)
    return None

def _extract_name_with_chomsky(stimulus: str) -> Optional[str]:
    """
    Enhanced: NER first, then heuristics, then Chomsky fallback.
    """
    # 1. NER priority
    name = _extract_name_with_ner(stimulus)
    if name:
        return name

    # 2. Heuristics regex
    name = _extract_name_with_heuristics(stimulus)
    if name:
        return name

    # 3. Original Chomsky
    try:
        classification = classify_stimulus(stimulus)
        subject = classification.get("subject")
        if subject:
            return subject.strip()
    except Exception:
        pass

    return None

# ---------------------------------------------------------------------------
# API setup
# ---------------------------------------------------------------------------

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.mount("/generated", StaticFiles(directory=GENERATED_DIR), name="generated")

# ---------------------------------------------------------------------------
# Guvna + RILIE singletons (global for FastAPI)
# ---------------------------------------------------------------------------

guvna: Optional[Guvna] = None
curiosity_engine: Optional[CuriosityEngine] = None
talk_memory: Optional[TalkMemory] = None
library_index: Optional[LibraryIndex] = None


def get_guvna() -> Guvna:
    global guvna
    if guvna is None:
        ensure_curiosity_table()
        curiosity_engine = CuriosityEngine()
        library_index = build_library_index()
        guvna = Guvna(
            curiosity_engine=curiosity_engine,
            library_index=library_index,
            search_fn=brave_search_sync,
            roux=load_roux(),
        )
        talk_memory = TalkMemory()
    return guvna


# ---------------------------------------------------------------------------
# Pydantic models for API
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
    ext: str = "txt"


class PreResponseRequest(BaseModel):
    question: str
    shallow: bool = False
    numresults: int = 5


class PreResponseResponse(BaseModel):
    question: str
    shallow: bool
    harvested: int
    status: str = "OK"


# ---------------------------------------------------------------------------
# Multi-question helpers (assuming these exist in your original)
# ---------------------------------------------------------------------------

def is_multi_question_response(result: Dict[str, Any]) -> bool:
    # Placeholder - implement based on your logic
    return False


def extract_question_parts(result: Dict[str, Any]) -> List[str]:
    # Placeholder
    return []


def process_multi_question_parts(parts: List[str], **kwargs) -> Dict[str, Any]:
    # Placeholder
    return {"combined_result": "", "part_count": 0, "parts": [], "all_passed": False, "quality_score": 0.0}


# ---------------------------------------------------------------------------
# Generated file helpers
# ---------------------------------------------------------------------------

def sanitize_ext(ext: str) -> str:
    if not ext:
        return "txt"
    ext = ext.strip().lstrip(".").lower()
    allowed = {
        "txt",
        "md",
        "json",
        "csv",
        "py",
        "js",
        "html",
        "css",
        "svg",
        "png",
        "jpg",
        "jpeg",
        "pdf",
    }
    return ext if ext in allowed else "txt"


def save_generated_file(ext: str, content: str) -> str:
    filename = f"generated_{uuid.uuid4().hex}.{ext}"
    path = GENERATED_DIR / filename
    path.write_text(content, encoding="utf-8")
    return filename


# ---------------------------------------------------------------------------
# Build plate (assuming this exists)
# ---------------------------------------------------------------------------

def build_plate(result: Dict[str, Any]) -> Dict[str, Any]:
    # Placeholder - your original logic
    return result


# ---------------------------------------------------------------------------
# Core RILIE endpoint
# ---------------------------------------------------------------------------

@app.post("/v1/rilie")
async def run_rilie(req: RilieRequest, request: Request) -> Dict[str, Any]:
    guvna = get_guvna()  # Singleton
    talk_memory = globals().get("talk_memory")  # Assuming global

    stimulus = req.stimulus.strip()
    if not stimulus:
        return {"result": "", "status": "EMPTY"}

    client_ip = get_client_ip(request)
    session = load_session(client_ip)

    # Restore state
    restore_guvna_state(guvna, session)
    restore_talk_memory(talk_memory, session)

    # Core Guvna call (fix kwarg name: maxpass)
    result = guvna.process(stimulus, maxpass=req.max_pass)

    # Multi-question handling
    if is_multi_question_response(result):
        logger.info("MULTIQUESTION detected: %s...", stimulus[:120])
        parts = extract_question_parts(result)
        if parts:
            multi = process_multi_question_parts(
                parts, guvna_instance=guvna, max_pass=req.max_pass, session=session
            )
            result = {
                "result": multi["combined_result"],
                "status": "MULTI_QUESTION_PROCESSED",
                "is_multi_question": True,
                "part_count": multi["part_count"],
                "parts": multi["parts"],
                "all_parts_passed": multi["all_passed"],
                "quality_score": multi["quality_score"],
            }

    # Memory behaviors
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

    # Christening → updates display_name via update_name
    if mem_result.get("christening"):
        result["christening"] = mem_result["christening"]
        update_name(
            session,
            mem_result["christening"].get("nickname"),
            christened=True,
        )

    # Topic tracking (Moment is an object, not a dict)
    if mem_result.get("moment"):
        moment = mem_result["moment"]
        tag = getattr(moment, "tag", None)
        record_topics(session, domains_hit, tag)

    # 🔁 NEW: canonical display_name tap (non-blocking, best-effort)
    # 1) Use existing session name if present
    display_name = session.get("display_name") or session.get("name")

    # 2) If none yet, let Chomsky take a first shot from this stimulus
    if not display_name:
        display_name = _extract_name_with_chomsky(stimulus)

    # 3) Safeguard bad names
    bad_names = {"introduce", "called", "myself", "allow", "please", "i"}
    if display_name and (display_name.lower() in bad_names or len(display_name) < 2):
        display_name = None

    # 4) Fallback to DEFAULT_NAME if still nothing
    display_name = display_name or DEFAULT_NAME

    # Persist on session
    session["display_name"] = display_name
    result.setdefault("display_name", display_name)

    # Hostess line on very first turn with this client_ip + loop exit
    intro_attempts = session.get("intro_attempts", 0)
    if not session.get("has_spoken"):
        intro_attempts += 1
        session["intro_attempts"] = intro_attempts
        if intro_attempts > 1 or not display_name:
            display_name = "friend"
            result["result"] = "Let's skip the formalities. What's on your mind? 🍳"
            result["status"] = "PIVOT"
        else:
            result["result"] = f"Pleasure to meet you, {display_name}! What's on your mind? 🍳"
            result["status"] = "GREETING"
        session["has_spoken"] = True
    else:
        # Normal flow; reset intro_attempts if depth achieved
        if result.get("depth", 0) > 0:  # Assuming 'depth' in result from guvna
            session["intro_attempts"] = 0

    # Snapshot state + save session
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
                        file_context_parts.append(
                            f"[Image {f.filename}] (OCR produced no text)"
                        )
                except Exception as e:
                    file_context_parts.append(
                        f"[Image {f.filename}] OCR failed: {e}"
                    )
            elif contenttype.startswith("text") or f.filename.endswith(
                (".txt", ".md", ".csv", ".json", ".py", ".js", ".html")
            ):
                try:
                    text = rawbytes.decode("utf-8", errors="replace")
                    file_context_parts.append(f"[File {f.filename}] {text}")
                except Exception:
                    file_context_parts.append(
                        f"[File {f.filename}] (could not decode as UTF-8)"
                    )
            elif f.filename.endswith(".docx"):
                try:
                    import io
                    from docx import Document

                    doc = Document(io.BytesIO(rawbytes))
                    text = "\n".join(
                        p.text for p in doc.paragraphs if p.text.strip()
                    )
                    if text:
                        file_context_parts.append(
                            f"[Document {f.filename}] {text}"
                        )
                    else:
                        file_context_parts.append(
                            f"[Document {f.filename}] (no text found)"
                        )
                except Exception as e:
                    file_context_parts.append(
                        f"[Document {f.filename}] parse failed: {e}"
                    )
            else:
                file_context_parts.append(
                    f"[File {f.filename}] unsupported type: {contenttype}"
                )
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

    # Fix kwarg name: maxpass
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