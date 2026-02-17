"""
guvna.service.py

Service-layer wiring for the Guvna (Act 5 – The Governor).

- Owns a process-wide Guvna singleton.
- Keeps the API layer thin: init at startup, then call run_rilie_service().
"""

from __future__ import annotations

from typing import Optional, Dict, Any

from guvna import Guvna, LibraryIndex  # core behavior lives in guvna.py


# ---------------------------------------------------------------------------
# Internal singleton
# ---------------------------------------------------------------------------

_guvna_singleton: Optional[Guvna] = None


# ---------------------------------------------------------------------------
# Initialization / access
# ---------------------------------------------------------------------------

def init_guvna(
    roux_seeds: Dict[str, Dict[str, Any]],
    search_fn = None,
    library_index: Optional[LibraryIndex] = None,
    manifesto_path: Optional[str] = None,
) -> None:
    """
    Initialize the process-wide Guvna instance.

    Call this once at startup (e.g., in api.py after loading Roux and wiring
    Brave search). Subsequent calls overwrite the singleton.
    """
    global _guvna_singleton
    _guvna_singleton = Guvna(
        roux_seeds=roux_seeds,
        search_fn=search_fn,
        library_index=library_index or {},
        manifesto_path=manifesto_path,
    )


def get_guvna() -> Guvna:
    """
    Return the initialized Guvna singleton.

    Raises if init_guvna(...) has not been called yet.
    """
    if _guvna_singleton is None:
        raise RuntimeError(
            "Guvna has not been initialized. "
            "Call init_guvna(roux_seeds=..., search_fn=...) at startup."
        )
    return _guvna_singleton


def run_rilie_service(stimulus: str, max_pass: int = 3) -> Dict[str, Any]:
    """
    Thin wrapper around Guvna.process for use by API handlers.
    """
    guvna = get_guvna()
    return guvna.process(stimulus, maxpass=max_pass)
