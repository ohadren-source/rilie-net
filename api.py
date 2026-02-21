"""
api.py — RILIE API v1.0 — GREETING ON FIRST REQUEST

Timeline:
1. Imports
2. GREETED = False (first thing, module-level)
3. App setup
4. Routes defined
5. Server boots
6. First request arrives → greeting fires → GREETED = True
7. All subsequent requests → Kitchen

Béton brut. Honest. One line. One check.
"""

import os
import json
import time
import uuid
import base64
import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable

import urllib.parse
import urllib.request

import httpx
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# ============================================================================
# FIRST REAL CODE AFTER IMPORTS: GREETING FLAG
# ============================================================================

GREETED = False

# ============================================================================
# APP SETUP
# ============================================================================

app = FastAPI(title="RILIE API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# CONFIG
# ============================================================================

BASE_DIR = Path(__file__).resolve().parent
ROUX_PATH = BASE_DIR / "ROUX.json"
RINITIALS_DIR = BASE_DIR / "RInitials"
GENERATED_DIR = BASE_DIR / "generated"

GENERATED_DIR.mkdir(exist_ok=True)

# ============================================================================
# LOGGING
# ============================================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rilie")

# ============================================================================
# LOAD ENV
# ============================================================================

def load_env_file(path: Path) -> None:
    """Load .env file."""
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

# ============================================================================
# BRAVE SEARCH
# ============================================================================

BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")
BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"

async def brave_web_search(
    query: str,
    num_results: int = 5,
) -> List[Dict[str, str]]:
    """Call Brave Search API."""
    if not BRAVE_API_KEY:
        raise RuntimeError("BRAVE_API_KEY not configured")
    
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
    """Sync wrapper for Brave."""
    import asyncio
    return asyncio.run(brave_web_search(query, num_results))

HAS_BRAVE = bool(BRAVE_API_KEY)

# ============================================================================
# NAME EXTRACTION
# ============================================================================

def extract_name_from_opening(opening: str) -> Optional[str]:
    """
    Extract name from opening stimulus using regex.
    Returns name or None.
    TODO: Replace with actual _extract_name_with_chomsky()
    """
    patterns = [
        r"(?:i'm|i am)\s+([A-Za-z][A-Za-z'\-]*)",
        r"(?:my name is|call me|they call me)\s+([A-Za-z][A-Za-z\s'\-]*?)(?:\.|,|!|\?|$)",
        r"^([A-Za-z][A-Za-z'\-]*?)(?:\s|[.,!?]|$)",
    ]
    
    opening_lower = opening.lower()
    for pattern in patterns:
        match = re.search(pattern, opening_lower, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if name and len(name) >= 2 and name.lower() not in {"introduce", "called", "myself"}:
                return name.capitalize()
    
    return None

DEFAULT_NAME = "Mate"

def sanitize_name(name: Optional[str]) -> str:
    """Clean and return name or default."""
    if name and isinstance(name, str):
        clean = name.strip()
        if len(clean) >= 2:
            return clean
    return DEFAULT_NAME

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class RilieRequest(BaseModel):
    stimulus: str
    max_pass: int = 3
    chef_mode: bool = False

class HealthResponse(BaseModel):
    status: str
    has_brave: bool

# ============================================================================
# ROUTES
# ============================================================================

@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Health check."""
    return HealthResponse(
        status="OK",
        has_brave=HAS_BRAVE,
    )

@app.post("/v1/rilie")
def run_rilie(req: RilieRequest) -> Dict[str, Any]:
    """
    Main RILIE endpoint.
    
    First request: Extract name, greet, set GREETED flag, return.
    Subsequent requests: Kitchen processes normally.
    """
    global GREETED
    
    stimulus = (req.stimulus or "").strip()
    
    if not stimulus:
        return {
            "stimulus": "",
            "result": "Drop something in. A question, a thought, a vibe. Then hit Go.",
            "quality_score": 0.0,
            "status": "EMPTY",
        }
    
    # FIRST REQUEST: Greet
    if not GREETED:
        GREETED = True
        
        # Extract name from opening stimulus
        opening = stimulus
        name = extract_name_from_opening(opening)
        display_name = sanitize_name(name)
        
        return {
            "stimulus": stimulus,
            "result": f"Pleasure to meet you, {display_name}! What's on your mind? 🍳",
            "status": "GREETING",
            "quality_score": 1.0,
            "display_name": display_name,
        }
    
    # SUBSEQUENT REQUESTS: Kitchen processes normally
    # TODO: Wire in guvna.process() here
    return {
        "stimulus": stimulus,
        "result": "Kitchen not yet wired in. This is turn 2+.",
        "status": "KITCHEN",
        "quality_score": 0.5,
    }

# ============================================================================
# SERVER STARTUP
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
