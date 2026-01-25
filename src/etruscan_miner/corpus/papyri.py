"""Papyri database integration for Etruscan discovery.

Greek papyri from Egypt and other regions occasionally mention
Tyrrhenians (Τυρρηνοί) and contain references to Italian peoples
and their customs. This module integrates with papyri databases
to find potential Etruscan vocabulary.

Key sources:
- Papyri.info (Duke Databank of Documentary Papyri)
- Trismegistos database
- Greek documentary papyri with Italian references
"""

import re
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Iterator
from urllib.request import urlopen, Request
from urllib.error import URLError

from ..config import PAPYRI_CACHE_DIR


@dataclass
class PapyrusDocument:
    """A papyrus document with text and metadata."""

    doc_id: str
    title: str
    text: str
    transliteration: str
    date: str
    provenance: str
    language: str  # 'greek', 'latin', 'demotic', 'coptic'
    source_database: str
    url: Optional[str] = None
    has_tyrrhenian_reference: bool = False
    notes: str = ""


@dataclass
class PapyrusMatch:
    """A match found in papyri."""

    doc_id: str
    matched_text: str
    context: str
    match_type: str  # 'tyrrhenian_mention', 'italian_reference', 'loanword'
    confidence: float
    notes: str = ""


# Greek terms for searching papyri
TYRRHENIAN_SEARCH_TERMS = [
    # Greek names for Etruscans/Tyrrhenians
    "Τυρρηνοί",
    "Τυρρηνοῖς",
    "Τυρρηνῶν",
    "Τυρρηνικός",
    "Τυρσηνοί",
    "Τυρσηνῶν",
    "Τυρσανοί",

    # Transliterated forms
    "tyrrheno",
    "tyrseno",
    "tyrsano",
    "tursen",

    # Italian references
    "Ἰταλία",
    "Ἰταλικός",
    "Italia",
]


class PapyriLoader:
    """Loader for papyri databases."""

    def __init__(self, cache_dir: Path = None):
        """Initialize loader.

        Args:
            cache_dir: Directory for caching results
        """
        self.cache_dir = cache_dir or PAPYRI_CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.rate_limit = 2.0  # seconds between API calls
        self._last_request = 0

    def _rate_limit_wait(self) -> None:
        """Wait to respect rate limiting."""
        elapsed = time.time() - self._last_request
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self._last_request = time.time()

    def search_papyri_info(self, query: str, limit: int = 100) -> Iterator[PapyrusMatch]:
        """Search Papyri.info for a query term.

        Note: This is a simplified interface. Full implementation
        would use the Papyri.info API.

        Args:
            query: Search term
            limit: Maximum results

        Yields:
            PapyrusMatch objects
        """
        # Check cache
        cache_key = re.sub(r'[^\w]', '_', query)
        cache_file = self.cache_dir / f"search_{cache_key}.json"

        if cache_file.exists():
            with open(cache_file) as f:
                data = json.load(f)
                for match in data:
                    yield PapyrusMatch(**match)
                return

        # For now, return known matches
        # In production, this would query the Papyri.info API
        known_matches = self._get_known_papyri_matches(query)
        for match in known_matches[:limit]:
            yield match

    def _get_known_papyri_matches(self, query: str) -> list[PapyrusMatch]:
        """Get known papyri mentions of Tyrrhenians.

        This is a curated list of papyri with Italian/Etruscan references.
        """
        # Example known references (would be expanded with real data)
        all_matches = [
            PapyrusMatch(
                doc_id="P.Oxy. 1380",
                matched_text="Τυρρηνικῆς θαλάσσης",
                context="Reference to the Tyrrhenian Sea",
                match_type="tyrrhenian_mention",
                confidence=0.70,
                notes="Geographic reference",
            ),
            PapyrusMatch(
                doc_id="P.Tebt. 703",
                matched_text="ἐξ Ἰταλίας",
                context="Import from Italy mentioned",
                match_type="italian_reference",
                confidence=0.50,
                notes="Trade document",
            ),
        ]

        query_lower = query.lower()
        return [m for m in all_matches if query_lower in m.matched_text.lower()
                or query_lower in m.context.lower()]

    def find_tyrrhenian_references(self) -> Iterator[PapyrusMatch]:
        """Find all papyri with Tyrrhenian/Italian references.

        Yields:
            PapyrusMatch objects
        """
        for term in TYRRHENIAN_SEARCH_TERMS[:5]:  # Limit API calls
            yield from self.search_papyri_info(term)

    def load_document(self, doc_id: str) -> Optional[PapyrusDocument]:
        """Load a specific papyrus document.

        Args:
            doc_id: Document identifier (e.g., "P.Oxy. 1380")

        Returns:
            PapyrusDocument if found
        """
        # Normalize document ID
        normalized = doc_id.replace(" ", "").lower()
        cache_file = self.cache_dir / f"doc_{normalized}.json"

        if cache_file.exists():
            with open(cache_file) as f:
                data = json.load(f)
                return PapyrusDocument(**data)

        # Would fetch from API in production
        return None


def search_papyri(query: str) -> list[PapyrusMatch]:
    """Search papyri databases for a term.

    Args:
        query: Search term

    Returns:
        List of PapyrusMatch objects
    """
    loader = PapyriLoader()
    return list(loader.search_papyri_info(query))


def find_etruscan_in_papyri() -> list[PapyrusMatch]:
    """Find all Etruscan/Tyrrhenian references in papyri.

    Returns:
        List of PapyrusMatch objects
    """
    loader = PapyriLoader()
    return list(loader.find_tyrrhenian_references())
