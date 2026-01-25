"""Archaeological database integration for Etruscan discovery.

New Etruscan inscriptions are regularly discovered through
archaeological excavations and museum digitization projects.
This module integrates with archaeological databases to find
new vocabulary from inscriptions.

Key sources:
- EAGLE Europeana inscriptions network
- Etruscan Texts Project (UMass)
- Thesaurus Linguae Etruscae (TLE) updates
- Museum digital collections
"""

import re
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Iterator
from datetime import datetime

from ..config import CORPUS_DIR


@dataclass
class Inscription:
    """An Etruscan inscription."""

    inscription_id: str
    text: str
    transliteration: str
    translation: Optional[str] = None
    provenance: str = ""
    site: str = ""
    object_type: str = ""  # 'mirror', 'cippus', 'tile', 'vase', etc.
    date_range: str = ""  # e.g., "6th-5th c. BCE"
    discovery_date: str = ""
    museum: str = ""
    database_source: str = ""
    words: list[str] = field(default_factory=list)
    new_vocabulary: list[str] = field(default_factory=list)  # Words not in TLE
    confidence: float = 0.7
    notes: str = ""


@dataclass
class ArchaeologicalDatabase:
    """An archaeological database source."""

    name: str
    abbreviation: str
    description: str
    url: Optional[str] = None
    api_available: bool = False
    inscription_count: int = 0
    last_updated: Optional[datetime] = None


# Known archaeological databases
ARCHAEOLOGICAL_DATABASES = [
    ArchaeologicalDatabase(
        name="EAGLE Europeana",
        abbreviation="EAGLE",
        description="European network of ancient inscriptions",
        url="https://www.eagle-network.eu/",
        api_available=True,
        inscription_count=500000,  # Total, not just Etruscan
    ),
    ArchaeologicalDatabase(
        name="Etruscan Texts Project",
        abbreviation="ETP",
        description="UMass Amherst Etruscan inscription project",
        url="https://etp.classics.umass.edu/",
        api_available=False,
        inscription_count=10000,
    ),
    ArchaeologicalDatabase(
        name="Thesaurus Linguae Etruscae",
        abbreviation="TLE",
        description="Standard reference for Etruscan inscriptions",
        api_available=False,
        inscription_count=13000,
    ),
    ArchaeologicalDatabase(
        name="Corpus Inscriptionum Etruscarum",
        abbreviation="CIE",
        description="Historical corpus of Etruscan inscriptions",
        api_available=False,
        inscription_count=12000,
    ),
    ArchaeologicalDatabase(
        name="CIEW Digital",
        abbreviation="CIEW",
        description="Comprehensive Etruscan wordlist from inscriptions",
        url="https://archive.org/details/ciew-data",
        api_available=False,
        inscription_count=0,  # Word database, not inscriptions
    ),
]


class ArchaeologicalLoader:
    """Loader for archaeological inscription databases."""

    def __init__(self, data_dir: Path = None):
        """Initialize loader.

        Args:
            data_dir: Directory for data files
        """
        self.data_dir = data_dir or CORPUS_DIR / "archaeological"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.databases = ARCHAEOLOGICAL_DATABASES

    def search_eagle(self, query: str) -> Iterator[Inscription]:
        """Search EAGLE Europeana for Etruscan inscriptions.

        Note: Full implementation would use EAGLE API.

        Args:
            query: Search term

        Yields:
            Inscription objects
        """
        # Check for cached results
        cache_file = self.data_dir / "eagle_etruscan.json"

        if cache_file.exists():
            with open(cache_file) as f:
                data = json.load(f)
                for insc in data:
                    if query.lower() in str(insc).lower():
                        yield Inscription(**insc)
                return

        # Return sample known inscriptions
        known = self._get_sample_inscriptions()
        query_lower = query.lower()

        for insc in known:
            if (query_lower in insc.text.lower() or
                query_lower in insc.transliteration.lower()):
                yield insc

    def _get_sample_inscriptions(self) -> list[Inscription]:
        """Get sample Etruscan inscriptions."""
        return [
            Inscription(
                inscription_id="CIE 5237",
                text="mi laris velχas",
                transliteration="mi laris velchas",
                translation="I (am) of Laris Velcha",
                provenance="Orvieto",
                site="Necropolis",
                object_type="mirror",
                date_range="5th c. BCE",
                database_source="CIE",
                words=["mi", "laris", "velchas"],
                confidence=0.90,
            ),
            Inscription(
                inscription_id="TLE 131",
                text="avil χiis lupu",
                transliteration="avil chiis lupu",
                translation="died at age 60?",
                provenance="Tarquinia",
                object_type="sarcophagus",
                date_range="4th c. BCE",
                database_source="TLE",
                words=["avil", "chiis", "lupu"],
                confidence=0.85,
            ),
            Inscription(
                inscription_id="ET Cl 1.1",
                text="mi flereri turce laris halχnas alpnas",
                transliteration="mi flereri turce laris halchnas alpnas",
                translation="I was dedicated as an offering; Laris Halchnas Alpnas (gave me)",
                provenance="Chiusi",
                object_type="cippus",
                date_range="5th c. BCE",
                database_source="ET",
                words=["mi", "flereri", "turce", "laris", "halchnas", "alpnas"],
                confidence=0.80,
            ),
        ]

    def find_new_inscriptions(self, since_year: int = 2020) -> Iterator[Inscription]:
        """Find recently discovered inscriptions.

        Args:
            since_year: Year to search from

        Yields:
            Inscription objects discovered since given year
        """
        # In production, would query databases for recent additions
        # For now, return sample recent discoveries

        recent = [
            Inscription(
                inscription_id="NEW-2022-001",
                text="tular rasnal",
                transliteration="tular rasnal",
                translation="boundary of Rasna (Etruria)?",
                provenance="Volterra",
                discovery_date="2022",
                object_type="boundary stone",
                database_source="excavation report",
                words=["tular", "rasnal"],
                new_vocabulary=["tular"],  # Variant spelling
                confidence=0.70,
                notes="Recently excavated; preliminary reading",
            ),
        ]

        for insc in recent:
            if insc.discovery_date and int(insc.discovery_date[:4]) >= since_year:
                yield insc

    def extract_vocabulary(self, inscriptions: list[Inscription] = None) -> set[str]:
        """Extract all vocabulary from inscriptions.

        Args:
            inscriptions: List of inscriptions (or all cached if None)

        Returns:
            Set of unique words
        """
        if inscriptions is None:
            inscriptions = list(self.search_eagle(""))

        vocabulary = set()
        for insc in inscriptions:
            vocabulary.update(insc.words)
            vocabulary.update(insc.new_vocabulary)

        return vocabulary

    def find_unattested_words(self, known_vocabulary: set[str]) -> list[tuple[str, Inscription]]:
        """Find words in inscriptions not in known vocabulary.

        Args:
            known_vocabulary: Set of known Etruscan words

        Returns:
            List of (word, source_inscription) tuples
        """
        unattested = []

        for insc in self._get_sample_inscriptions():
            for word in insc.words:
                if word.lower() not in known_vocabulary:
                    unattested.append((word, insc))

        return unattested


def search_archaeological_databases(query: str) -> list[Inscription]:
    """Search all archaeological databases.

    Args:
        query: Search term

    Returns:
        List of Inscription objects
    """
    loader = ArchaeologicalLoader()
    return list(loader.search_eagle(query))


def find_new_etruscan_inscriptions(since_year: int = 2020) -> list[Inscription]:
    """Find recently discovered Etruscan inscriptions.

    Args:
        since_year: Year to search from

    Returns:
        List of Inscription objects
    """
    loader = ArchaeologicalLoader()
    return list(loader.find_new_inscriptions(since_year))
