"""Configuration for Etruscan gloss mining pipeline."""

from pathlib import Path

# Project paths
# config.py is at src/etruscan_miner/config.py, so go up 3 levels
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CORPUS_DIR = DATA_DIR / "corpus"
CORPUS_CACHE_DIR = CORPUS_DIR  # General cache for all corpus sources
PERSEUS_CACHE_DIR = CORPUS_DIR / "perseus"
LATIN_LIBRARY_CACHE_DIR = CORPUS_DIR / "latin_library"
DB_PATH = DATA_DIR / "etruscan_glosses.db"

# Perseus API
PERSEUS_BASE_URL = "http://www.perseus.tufts.edu/hopper/CTS"
PERSEUS_RATE_LIMIT = 1.0  # requests per second
CACHE_EXPIRY_DAYS = 30

# Validation thresholds
CONFIDENCE_HIGH = 0.85
CONFIDENCE_MEDIUM = 0.65

# Validation weights
WEIGHT_PATTERN = 0.30
WEIGHT_CROSS_REF = 0.30
WEIGHT_LINGUISTIC = 0.20
WEIGHT_CONTEXT = 0.20

# Target works for mining (prioritized)
TARGET_WORKS = {
    "varro_de_lingua_latina": {
        "author": "Varro",
        "title": "De Lingua Latina",
        "urn": "urn:cts:latinLit:phi0684.phi002",
        "priority": "HIGH",
    },
    "pliny_naturalis_historia": {
        "author": "Pliny the Elder",
        "title": "Naturalis Historia",
        "urn": "urn:cts:latinLit:phi0978.phi001",
        "priority": "HIGH",
    },
    "festus_de_verborum": {
        "author": "Festus",
        "title": "De verborum significatione",
        "urn": None,  # epitome - needs special handling
        "priority": "HIGH",
    },
    "servius_aeneid": {
        "author": "Servius",
        "title": "In Vergilii Aeneidem commentarii",
        "urn": "urn:cts:latinLit:stoa0272.stoa001",
        "priority": "MEDIUM",
    },
    "isidore_etymologiae": {
        "author": "Isidore of Seville",
        "title": "Etymologiae",
        "urn": None,  # needs special handling
        "priority": "MEDIUM",
    },
}

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
CORPUS_DIR.mkdir(parents=True, exist_ok=True)
PERSEUS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
LATIN_LIBRARY_CACHE_DIR.mkdir(parents=True, exist_ok=True)
