"""
library.py – Domain Engine Library Index

Boot-time registry for RILIE's domain engines.

Loaded by the Governor (guvna.py) to provide a LibraryIndex:
    {domain_name: {display_name, description, tags, public,
                   meaning_unidirectional, entrypoints}}

20 public libraries + 1 secret vault (quantum_trading).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, Any, Callable, List
import importlib.util

# Add library folder to path for imports
library_path = Path(__file__).parent / "library"
if library_path.exists():
    sys.path.insert(0, str(library_path))


def _import_module(name: str, filepath: str = None):
    """Import a module, handling spaces in filenames."""
    if filepath:
        spec = importlib.util.spec_from_file_location(name, filepath)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
            return module
    else:
        try:
            return __import__(name)
        except ImportError:
            return None


# Core domain modules – all verified clean
QuantumTrading = _import_module("QuantumTrading")
bigbang = _import_module("bigbang")
biochem_universe = _import_module("biochem_universe")
chemistry = _import_module("chemistry")
civics = _import_module("civics")
climate_catch44_model = _import_module("climate_catch44_model")
computerscience = _import_module("computerscience")
developmental_bio = _import_module("developmental_bio")
ecology = _import_module("ecology")
evolve = _import_module("evolve")
games = _import_module("games")
genomics = _import_module("genomics")
life = _import_module("life")
linguistics_cognition = _import_module("linguistics_cognition")
nanotechnology = _import_module("nanotechnology")
physics = _import_module("physics")
thermodynamics = _import_module("thermodynamics")
urban_design = _import_module("urban_design")

# Handle modules with spaces in filenames
deep_time_geo = _import_module("deep_time_geo", str(library_path / "deep time geo.py"))
network_theory = _import_module("network_theory", str(library_path / "network theory.py"))

# DuckSauce IS bigbang
DuckSauce = bigbang

# Match guvna.LibraryIndex shape
LibraryIndex = Dict[str, Dict[str, Any]]


def _entry(
    display_name: str,
    description: str,
    tags: List[str],
    public: bool = True,
    meaning_unidirectional: bool = False,
    entrypoints: Dict[str, Callable[..., Any]] | None = None,
) -> Dict[str, Any]:
    return {
        "display_name": display_name,
        "description": description,
        "tags": set(tags),
        "public": public,
        # If True: engine may tune internal risk/knobs but cannot write to
        # global truth/meaning about the user or the world.
        "meaning_unidirectional": meaning_unidirectional,
        "entrypoints": entrypoints or {},
    }


def build_library_index() -> LibraryIndex:
    """
    Build the full domain library index.

    Intended to be called once at boot by the Governor:
        self.library_index = library.build_library_index()
    """
    index: LibraryIndex = {}

    # 1. Physics OS
    index["physics"] = _entry(
        display_name="Physics OS",
        description="Classical, relativistic, quantum, thermo, and cosmology lenses.",
        tags=["physics", "force", "energy", "entropy", "quantum", "relativity", "cosmology"],
        entrypoints={
            "density": getattr(physics, "density", None),
            "newtons_second_law": getattr(physics, "newtons_second_law", None),
            "mass_energy_equivalence": getattr(physics, "mass_energy_equivalence", None),
            "heisenberg_uncertainty": getattr(physics, "heisenberg_uncertainty", None),
            "quantum_tunneling": getattr(physics, "quantum_tunneling", None),
            "hubble_expansion": getattr(physics, "hubble_expansion", None),
        },
    )

    # 2. Thermodynamics
    index["thermodynamics"] = _entry(
        display_name="Thermodynamics OS",
        description="Entropy, order, harm, and irreversibility constraints.",
        tags=["thermodynamics", "entropy", "order", "harm", "repair", "irreversible"],
        entrypoints={
            "ThermodynamicSystem": getattr(thermodynamics, "ThermodynamicSystem", None),
            "catch44_integrity_check": getattr(thermodynamics, "catch44_integrity_check", None),
        },
    )

    # 3. Chemistry
    index["chemistry"] = _entry(
        display_name="Chemistry OS",
        description="Molecular gates for concentration, bonds, catalysis, and emergence.",
        tags=["chemistry", "molecules", "bonds", "catalyst", "ph", "gibbs"],
        entrypoints={
            "ChemistryKernel": getattr(chemistry, "ChemistryKernel", None),
        },
    )

    # 4. Biochem Universe
    index["biochem_universe"] = _entry(
        display_name="Biochem Universe OS",
        description="Bridge between biochemistry and cosmic scales.",
        tags=["biochemistry", "universe", "metabolism", "cosmos"],
        entrypoints={},
    )

    # 5. Life / Biology
    index["life"] = _entry(
        display_name="Life OS",
        description="Natural selection, cancer, apoptosis, immune, ecosystems.",
        tags=["biology", "evolution", "cancer", "apoptosis", "immune", "ecosystem"],
        entrypoints={
            "natural_selection": getattr(life, "natural_selection", None),
            "multicellular_cooperation": getattr(life, "multicellular_cooperation", None),
            "cancer_formation": getattr(life, "cancer_formation", None),
            "apoptosis_decision": getattr(life, "apoptosis_decision", None),
            "ecosystem_stability": getattr(life, "ecosystem_stability", None),
            "trophic_cascade": getattr(life, "trophic_cascade", None),
        },
    )

    # 6. Genomics
    index["genomics"] = _entry(
        display_name="Genomics OS",
        description="Genetic architecture and information flow.",
        tags=["genomics", "genes", "dna", "expression"],
        entrypoints={},
    )

    # 7. Developmental Biology
    index["developmental_bio"] = _entry(
        display_name="Developmental Biology OS",
        description="Patterning, morphogenesis, and developmental lenses.",
        tags=["development", "morphogenesis", "embryo", "patterning"],
        entrypoints={},
    )

    # 8. Ecology
    index["ecology"] = _entry(
        display_name="Ecology OS",
        description="Ecosystems, niches, stability, and cascades.",
        tags=["ecology", "ecosystem", "niche", "biodiversity"],
        entrypoints={},
    )

    # 9. Evolution (macro)
    index["evolve"] = _entry(
        display_name="Evolution OS",
        description="Evolutionary dynamics and macro patterns.",
        tags=["evolution", "selection", "fitness", "speciation"],
        entrypoints={},
    )

    # 10. Nanotechnology
    index["nanotechnology"] = _entry(
        display_name="Nanotechnology OS",
        description="Nanoscale precision, swarms, coatings, and safety.",
        tags=["nanotech", "nano", "swarm", "coating", "targeted delivery"],
        entrypoints={
            "nano_precision": getattr(nanotechnology, "nano_precision", None),
            "safety_moo": getattr(nanotechnology, "safety_moo", None),
            "targeted_delivery_index": getattr(nanotechnology, "targeted_delivery_index", None),
            "swarm_coverage": getattr(nanotechnology, "swarm_coverage", None),
            "nano_power_density": getattr(nanotechnology, "nano_power_density", None),
        },
    )

    # 11. Game Theory
    index["games"] = _entry(
        display_name="Game Theory OS",
        description="Incentives, equilibria, cooperation, signaling, and reputation.",
        tags=["games", "strategy", "equilibrium", "cooperation", "signals"],
        entrypoints={
            "information_quality": getattr(games, "information_quality", None),
            "cooperative_equilibrium": getattr(games, "cooperative_equilibrium", None),
            "pure_nash_equilibria": getattr(games, "pure_nash_equilibria", None),
            "grim_trigger_equilibrium": getattr(games, "grim_trigger_equilibrium", None),
            "public_good_payoff": getattr(games, "public_good_payoff", None),
            "reputation_update": getattr(games, "reputation_update", None),
        },
    )

    # 12. Network Theory
    index["network_theory"] = _entry(
        display_name="Network Karma OS",
        description="Consequence propagation through networks (karma/dharma).",
        tags=["network", "graph", "karma", "consequence", "hubs", "grace"],
        entrypoints={
            "Network": getattr(network_theory, "Network", None) if network_theory else None,
            "Node": getattr(network_theory, "Node", None) if network_theory else None,
        },
    )

    # 13. Linguistics & Cognition
    index["linguistics_cognition"] = _entry(
        display_name="Language & Cognition OS",
        description="Semantic density, empathy, frames, translation, neurolinguistics.",
        tags=["language", "linguistics", "semantics", "pragmatics", "empathy"],
        entrypoints={
            "semantic_density": getattr(linguistics_cognition, "semantic_density", None),
            "collective_meaning": getattr(linguistics_cognition, "collective_meaning", None),
            "speech_act_integrity": getattr(linguistics_cognition, "speech_act_integrity", None),
            "cognitive_load": getattr(linguistics_cognition, "cognitive_load", None),
            "conversational_implicature": getattr(linguistics_cognition, "conversational_implicature", None),
            "translation_loss": getattr(linguistics_cognition, "translation_loss", None),
        },
    )

    # 14. Civics
    index["civics"] = _entry(
        display_name="Civics OS",
        description="Institutions, power, and civic structures.",
        tags=["civics", "governance", "institutions", "rights"],
        entrypoints={},
    )

    # 15. Climate
    index["climate"] = _entry(
        display_name="Climate Catch-44 OS",
        description="Climate dynamics under Catch-44 constraints.",
        tags=["climate", "carbon", "warming", "risk"],
        entrypoints={},
    )

    # 16. Computer Science
    index["computerscience"] = _entry(
        display_name="Computer Science OS",
        description="Algorithms, computation, and CS metaphors.",
        tags=["computing", "algorithms", "cs", "complexity"],
        entrypoints={},
    )

    # 17. Big Bang / Cosmology (ALSO: DuckSauce Taste OS)
    index["bigbang"] = _entry(
        display_name="Big Bang OS",
        description="Early universe and cosmological emergence.",
        tags=["cosmology", "big bang", "early universe"],
        entrypoints={},
    )

    # 18. Deep Time Geology
    index["deep_time_geo"] = _entry(
        display_name="Deep Time Geo OS",
        description="Geological deep time and planetary change.",
        tags=["geology", "deep time", "earth history"],
        entrypoints={},
    )

    # 19. Urban Design
    index["urban_design"] = _entry(
        display_name="Urban Design OS",
        description="SaucelitoCivic Ravena-scale brutalist-Zaha-Dada-Deco city generator.",
        tags=["urban", "city", "housing", "gentrification", "ravena"],
        entrypoints={
            "SaucelitoCivic": getattr(urban_design, "SaucelitoCivic", None),
        },
    )

    # 20. DuckSauce (Taste OS) — ALIASED TO bigbang.py
    index["DuckSauce"] = _entry(
        display_name="DuckSauce OS",
        description="Taste, flavor, and sauce metaphors for meaning.",
        tags=["taste", "flavor", "sauce", "duck"],
        entrypoints={},
    )

    # Secret 21st: QuantumTrading (non-public, unidirectional meaning)
    index["quantum_trading"] = _entry(
        display_name="Quantum Trading OS",
        description="Night Trader v7.0 density engine (performance earns risk).",
        tags=["trading", "markets", "risk", "density"],
        public=False,
        meaning_unidirectional=True,
        entrypoints={
            "NightTraderEngine": getattr(QuantumTrading, "NightTraderEngine", None),
        },
    )

    return index


def get_library_entry(index: LibraryIndex, name: str) -> Dict[str, Any] | None:
    """
    Convenience accessor; Guvna/Kitchen can use:

        entry = get_library_entry(self.library_index, "physics")
        funcs = entry["entrypoints"]
    """
    return index.get(name)
