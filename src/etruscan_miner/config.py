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
MEDIEVAL_CACHE_DIR = CORPUS_DIR / "medieval"
PAPYRI_CACHE_DIR = CORPUS_DIR / "papyri"
BYZANTINE_CACHE_DIR = CORPUS_DIR / "byzantine"
MODELS_DIR = DATA_DIR / "models"
DB_PATH = DATA_DIR / "etruscan_glosses.db"

# Perseus API
PERSEUS_BASE_URL = "http://www.perseus.tufts.edu/hopper/CTS"
PERSEUS_RATE_LIMIT = 1.0  # requests per second
CACHE_EXPIRY_DAYS = 30

# Validation thresholds
CONFIDENCE_HIGH = 0.85
CONFIDENCE_MEDIUM = 0.65

# Validation weights (standard pattern-based discovery)
WEIGHT_PATTERN = 0.30
WEIGHT_CROSS_REF = 0.30
WEIGHT_LINGUISTIC = 0.20
WEIGHT_CONTEXT = 0.20

# Discovery method weights (for new discovery approaches)
WEIGHT_EXPLICIT_PATTERN = 0.90    # "Tusci vocant X" type - highest confidence
WEIGHT_IMPLICIT_PATTERN = 0.70    # "antiqui vocabant X" type - needs more validation
WEIGHT_SEMANTIC_DISCOVERY = 0.60  # Embedding-based discovery
WEIGHT_ANOMALY_DETECTION = 0.50   # Statistical anomaly (hapax, phonotactic)
WEIGHT_MORPHOLOGICAL = 0.40       # Predicted forms from known roots
WEIGHT_CROSS_LINGUISTIC = 0.75    # Lemnian/Raetic parallel - high value

# Author reliability scores (for weighting discoveries)
AUTHOR_RELIABILITY = {
    "varro": 0.95,
    "verrius_flaccus": 0.92,
    "festus": 0.90,
    "pliny": 0.75,
    "dionysius": 0.70,
    "strabo": 0.70,
    "livy": 0.65,
    "virgil": 0.60,
    "suetonius": 0.65,
    "macrobius": 0.70,
    "servius": 0.65,
    "isidore": 0.40,  # Known for fanciful etymologies
    "unknown": 0.50,
}

# Semantic domain boosts (words in these domains more likely Etruscan)
DOMAIN_BOOST = {
    "divination": 0.15,      # haruspicy, augury, lightning interpretation
    "religion": 0.12,        # gods, rituals, temples
    "theatre": 0.10,         # performance, masks, actors
    "luxury": 0.08,          # gold, textiles, wine, banquets
    "political": 0.05,       # magistracies, governance
    "afterlife": 0.12,       # death, tombs, underworld
    "calendar": 0.10,        # months, sacred days
    "military": 0.05,        # weapons, warfare (less distinctively Etruscan)
}

# Etruscan semantic domain keywords
DOMAIN_KEYWORDS = {
    "divination": [
        "haruspex", "haruspic", "extispic", "fulg", "auspic", "augur",
        "liver", "iecur", "fulgur", "lightning", "omen", "prodig",
        "sacr", "divin", "presag", "portentu"
    ],
    "religion": [
        "deus", "dea", "god", "goddess", "templum", "sacr", "ritus",
        "sacrific", "libat", "votiv", "lar", "manes", "genius", "penas"
    ],
    "theatre": [
        "histrio", "histrion", "actor", "scaen", "persona", "mask",
        "ludus", "ludi", "spectacul", "theatr", "fabul"
    ],
    "luxury": [
        "aurum", "gold", "argentum", "silver", "gemma", "vinum", "wine",
        "textil", "purpur", "ivory", "ebur", "conviv", "banquet"
    ],
    "afterlife": [
        "mors", "mort", "sepulc", "tumul", "tomb", "inferi", "manes",
        "funer", "urna", "ciner", "underworld", "mania", "larva"
    ],
    "calendar": [
        "mensis", "month", "idus", "kalend", "dies", "festus", "feri",
        "ann", "saecul", "lustrum"
    ],
}

# Cross-linguistic analysis settings
LEMNIAN_WORDS = [
    # Known Lemnian vocabulary from Kaminia stele and other inscriptions
    "holaie", "sivai", "avis", "mav", "sialchveis", "rom", "maraz",
    "aviš", "zeronai", "ziazi", "morail", "φoke", "holaiez"
]

RAETIC_ROOTS = [
    # Known Raetic roots/morphemes
    "tin", "upiku", "lasive", "pitave", "rituske", "φelna", "kve"
]

# Phonotactic settings for anomaly detection
ETRUSCAN_TYPICAL_ENDINGS = [
    "a", "i", "e", "u", "al", "el", "il", "ul", "na", "ne", "ni",
    "s", "as", "es", "is", "ce", "χe", "che", "r", "ar", "er", "θi"
]

ETRUSCAN_FORBIDDEN_CLUSTERS = ["bd", "bg", "gd", "gb", "dg", "db", "qu"]
ETRUSCAN_TYPICAL_CLUSTERS = ["pr", "tr", "cr", "sp", "st", "sc", "χv", "θn", "mn"]

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
MEDIEVAL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
PAPYRI_CACHE_DIR.mkdir(parents=True, exist_ok=True)
BYZANTINE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)
