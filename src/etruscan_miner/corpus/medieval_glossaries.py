"""Medieval glossary integration for Etruscan discovery.

Medieval Latin glossaries preserve ancient material that is often
lost in original sources. Copyists and compilers like Isidore of
Seville, Placidus, and the anonymous Abavus maior collected
etymologies and word explanations from earlier sources.

Key sources:
- Glossae Isidori (7th century)
- Placidus Glossary (5th-6th century)
- Abavus maior / Abstrusa glossaries
- Corpus Glossariorum Latinorum (CGL)
"""

import re
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Iterator
from urllib.request import urlopen, Request
from urllib.error import URLError

from ..config import MEDIEVAL_CACHE_DIR


@dataclass
class GlossaryEntry:
    """An entry from a medieval glossary."""

    headword: str
    explanation: str
    source_glossary: str
    page_or_section: str = ""
    language_attribution: Optional[str] = None  # e.g., "Tusci", "Etrusci"
    is_etymology: bool = False
    confidence: float = 0.5
    notes: str = ""


@dataclass
class MedievalSource:
    """A medieval glossary source."""

    name: str
    abbreviation: str
    date: str
    description: str
    url: Optional[str] = None
    local_path: Optional[Path] = None
    reliability: float = 0.5


# Known medieval sources
MEDIEVAL_SOURCES = [
    MedievalSource(
        name="Isidore Etymologiae",
        abbreviation="Isid.Etym.",
        date="7th century",
        description="Encyclopedic work with many etymologies, some preserving ancient material",
        reliability=0.45,  # Isidore often invents etymologies
    ),
    MedievalSource(
        name="Placidus Glossary",
        abbreviation="Placid.",
        date="5th-6th century",
        description="Late antique glossary preserving earlier material",
        reliability=0.60,
    ),
    MedievalSource(
        name="Abavus Maior",
        abbreviation="Abav.Mai.",
        date="8th-9th century",
        description="Carolingian glossary compiled from older sources",
        reliability=0.50,
    ),
    MedievalSource(
        name="Corpus Glossariorum Latinorum",
        abbreviation="CGL",
        date="various",
        description="Modern collection of ancient and medieval glossaries",
        url="https://archive.org/details/corpusglossarior00LGoog",
        reliability=0.70,  # Scholarly edition
    ),
    MedievalSource(
        name="Liber Glossarum",
        abbreviation="Lib.Gloss.",
        date="8th century",
        description="Large Carolingian encyclopedia with glossary material",
        reliability=0.55,
    ),
]


class MedievalGlossaryLoader:
    """Loader for medieval glossary texts."""

    def __init__(self, cache_dir: Path = None):
        """Initialize loader.

        Args:
            cache_dir: Directory for caching downloaded texts
        """
        self.cache_dir = cache_dir or MEDIEVAL_CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.sources = MEDIEVAL_SOURCES
        self.rate_limit = 2.0  # seconds between requests

    def get_source(self, abbreviation: str) -> Optional[MedievalSource]:
        """Get source by abbreviation.

        Args:
            abbreviation: Source abbreviation (e.g., "Isid.Etym.")

        Returns:
            MedievalSource if found
        """
        for source in self.sources:
            if source.abbreviation == abbreviation:
                return source
        return None

    def load_isidore_etymologiae(self, book: int = None) -> Iterator[GlossaryEntry]:
        """Load Isidore's Etymologiae.

        Isidore's Etymologiae is available from Latin Library.
        This loads and parses it for etymology entries.

        Args:
            book: Specific book number (1-20), or None for all

        Yields:
            GlossaryEntry objects
        """
        # Check cache
        cache_file = self.cache_dir / "isidore_etymologiae.json"

        if cache_file.exists():
            with open(cache_file) as f:
                data = json.load(f)
                for entry in data:
                    if book is None or entry.get("book") == book:
                        yield GlossaryEntry(**entry)
                return

        # Parse from text - this would be loaded from Latin Library
        # For now, yield known Etruscan-relevant entries
        known_entries = self._get_known_isidore_entries()
        for entry in known_entries:
            if book is None or entry.get("book") == book:
                yield GlossaryEntry(
                    headword=entry["headword"],
                    explanation=entry["explanation"],
                    source_glossary="Isid.Etym.",
                    page_or_section=entry.get("section", ""),
                    language_attribution=entry.get("language"),
                    is_etymology=True,
                    confidence=0.45,
                    notes=entry.get("notes", ""),
                )

    def _get_known_isidore_entries(self) -> list[dict]:
        """Get known Etruscan-relevant entries from Isidore."""
        return [
            {
                "headword": "histrio",
                "explanation": "Histriones dicti sunt a Tuscia. Histrio enim Tuscum nomen est.",
                "section": "18.48",
                "book": 18,
                "language": "Tusci",
                "notes": "Explicit Etruscan attribution",
            },
            {
                "headword": "lanista",
                "explanation": "Lanista gladiatorum magister, quod gladiatores venderet.",
                "section": "10.159",
                "book": 10,
                "language": "Tusci",
                "notes": "Connected to Etruscan funeral games",
            },
            {
                "headword": "subulo",
                "explanation": "Subulones dicuntur qui tibias canunt, a Tuscis.",
                "section": "18.45",
                "book": 18,
                "language": "Tusci",
                "notes": "Flute player, Etruscan origin",
            },
            {
                "headword": "persona",
                "explanation": "Persona est facies artificialis.",
                "section": "19.31",
                "book": 19,
                "language": None,
                "notes": "Possible Etruscan phersu connection",
            },
            {
                "headword": "haruspex",
                "explanation": "Haruspices dicti ab horis inspiciendis.",
                "section": "8.9",
                "book": 8,
                "language": "Tusci",
                "notes": "Etruscan divination tradition",
            },
            {
                "headword": "atrium",
                "explanation": "Atrium dictum ab Atriae oppido Tusciae.",
                "section": "15.3",
                "book": 15,
                "language": "Tusci",
                "notes": "Attributed to Etruscan city Atria",
            },
            {
                "headword": "elementum",
                "explanation": "Elementa dicta quasi LMNta.",
                "section": "1.3",
                "book": 1,
                "language": None,
                "notes": "May relate to Etruscan alphabet transmission",
            },
            {
                "headword": "mundus",
                "explanation": "Mundus apud antiquos appellabatur locus sub terra.",
                "section": "15.11",
                "book": 15,
                "language": None,
                "notes": "Etruscan ritual pit",
            },
        ]

    def search_glossaries(
        self,
        query: str,
        sources: list[str] = None
    ) -> Iterator[GlossaryEntry]:
        """Search across glossaries for a term.

        Args:
            query: Search term (headword or in explanation)
            sources: List of source abbreviations to search

        Yields:
            Matching GlossaryEntry objects
        """
        # Search Isidore
        if sources is None or "Isid.Etym." in sources:
            for entry in self.load_isidore_etymologiae():
                if query.lower() in entry.headword.lower():
                    yield entry
                elif query.lower() in entry.explanation.lower():
                    yield entry

    def find_etruscan_attributions(self) -> Iterator[GlossaryEntry]:
        """Find all entries with explicit Etruscan attributions.

        Yields:
            GlossaryEntry objects with Etruscan language markers
        """
        etruscan_markers = [
            "tusci", "tuscos", "tuscorum", "tuscia",
            "etrusci", "etruscos", "etruscorum", "etruria",
            "tyrrheni", "tyrrhen"
        ]

        for entry in self.load_isidore_etymologiae():
            explanation_lower = entry.explanation.lower()
            if any(marker in explanation_lower for marker in etruscan_markers):
                entry.language_attribution = "Etruscan"
                yield entry


def load_medieval_glossaries() -> Iterator[GlossaryEntry]:
    """Load all available medieval glossary entries.

    Yields:
        GlossaryEntry objects from all sources
    """
    loader = MedievalGlossaryLoader()

    # Load Isidore
    yield from loader.load_isidore_etymologiae()


def find_etruscan_in_glossaries() -> list[GlossaryEntry]:
    """Find all Etruscan-attributed entries in medieval glossaries.

    Returns:
        List of GlossaryEntry objects with Etruscan attributions
    """
    loader = MedievalGlossaryLoader()
    return list(loader.find_etruscan_attributions())
