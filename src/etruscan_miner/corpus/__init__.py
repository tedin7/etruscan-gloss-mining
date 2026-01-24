"""Corpus access module for Perseus and other text sources.

Available clients:
- PerseusClient: CTS API for texts IN the Perseus inventory (Pliny, Livy, Virgil)
- LatinLibraryClient: HTML scraping for texts NOT in Perseus (Varro, Festus)

See individual modules for documentation on API status and available texts.
"""

from .latin_library import LatinLibraryClient, load_cached_varro
from .perseus import (
    AVAILABLE_WORKS,
    PerseusClient,
    fetch_livy,
    fetch_pliny,
    fetch_varro,
)

__all__ = [
    "PerseusClient",
    "LatinLibraryClient",
    "AVAILABLE_WORKS",
    "fetch_pliny",
    "fetch_livy",
    "fetch_varro",
    "load_cached_varro",
]
