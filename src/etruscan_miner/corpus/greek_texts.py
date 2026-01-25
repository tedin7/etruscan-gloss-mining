"""Greek corpus client for Perseus Digital Library.

Accesses Greek texts via CTS (Canonical Text Services) protocol.
Focuses on texts that discuss Etruscan/Tyrrhenian culture and vocabulary.

Key Greek authors on Etruria:
- Dionysius of Halicarnassus: Roman Antiquities (extensive Etruscan discussion)
- Strabo: Geography (Etruscan geography and customs)
- Herodotus: Histories (Etruscan origins)
- Plutarch: Various works mentioning Etruscans
"""

import re
import time
from dataclasses import dataclass
from typing import Optional
from xml.etree import ElementTree as ET

import requests

from ..config import PERSEUS_BASE_URL, PERSEUS_RATE_LIMIT


@dataclass
class GreekPassage:
    """A passage of Greek text."""

    urn: str
    reference: str
    text: str
    author: str = ""
    work: str = ""
    source_url: Optional[str] = None

    @property
    def contains_tyrrhenian_ref(self) -> bool:
        """Check if passage mentions Tyrrhenians/Etruscans."""
        # Greek terms for Etruscans
        patterns = [
            r"Τυρ[ρσ]ην",  # Τυρρηνοί, Τυρσηνοί
            r"Τυρ[ρσ]ανι",  # variant
            r"Ἐτρούσκ",  # Ἐτρούσκοι (rare)
            r"Ῥασέννα",  # Rasenna (Etruscan self-name)
        ]
        for pattern in patterns:
            if re.search(pattern, self.text):
                return True
        return False


# Greek works with Etruscan content
# URN format: urn:cts:greekLit:tlgXXXX.tlgYYY.perseus-grc1
GREEK_WORKS = {
    "dionysius_ant_rom": {
        "urn": "urn:cts:greekLit:tlg0081.tlg001.perseus-grc1",
        "author": "Dionysius of Halicarnassus",
        "title": "Roman Antiquities",
        "books": 20,
        "sections_per_book": 100,
        "priority": "HIGH",
        "notes": "Extensive discussion of Etruscan origins and customs",
    },
    "strabo_geography": {
        "urn": "urn:cts:greekLit:tlg0099.tlg001.perseus-grc1",
        "author": "Strabo",
        "title": "Geography",
        "books": 17,
        "sections_per_book": 50,
        "priority": "HIGH",
        "notes": "Book 5 covers Etruria in detail",
    },
    "herodotus_histories": {
        "urn": "urn:cts:greekLit:tlg0016.tlg001.perseus-grc1",
        "author": "Herodotus",
        "title": "Histories",
        "books": 9,
        "sections_per_book": 200,
        "priority": "MEDIUM",
        "notes": "Discusses Etruscan origins (Lydian theory)",
    },
    "plutarch_romulus": {
        "urn": "urn:cts:greekLit:tlg0007.tlg003.perseus-grc1",
        "author": "Plutarch",
        "title": "Life of Romulus",
        "books": 1,
        "sections_per_book": 40,
        "priority": "MEDIUM",
        "notes": "Early Roman-Etruscan relations",
    },
    "plutarch_numa": {
        "urn": "urn:cts:greekLit:tlg0007.tlg006.perseus-grc1",
        "author": "Plutarch",
        "title": "Life of Numa",
        "books": 1,
        "sections_per_book": 30,
        "priority": "MEDIUM",
        "notes": "Etruscan religious influence",
    },
}


class GreekCorpusClient:
    """Client for Greek texts from Perseus Digital Library."""

    PASSAGE_ENDPOINT = "?request=GetPassage&urn={urn}"

    def __init__(
        self,
        base_url: str = PERSEUS_BASE_URL,
        rate_limit: float = PERSEUS_RATE_LIMIT,
        timeout: int = 30,
    ):
        """Initialize Greek corpus client.

        Args:
            base_url: Base URL for CTS API
            rate_limit: Minimum seconds between requests
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.rate_limit = rate_limit
        self.timeout = timeout
        self._last_request = 0.0
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "EtruscanGlossMiner/1.0 (Greek texts research)"
        })

    def _wait_for_rate_limit(self):
        """Wait to respect rate limit."""
        elapsed = time.time() - self._last_request
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self._last_request = time.time()

    def _make_request(self, url: str) -> Optional[str]:
        """Make an HTTP request with rate limiting."""
        self._wait_for_rate_limit()
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return None

    def get_passage(self, urn: str) -> Optional[GreekPassage]:
        """Get a specific passage by URN.

        Args:
            urn: Passage URN

        Returns:
            GreekPassage or None
        """
        url = f"{self.base_url}{self.PASSAGE_ENDPOINT.format(urn=urn)}"
        xml_text = self._make_request(url)

        if not xml_text:
            return None

        # Check for CTS error
        if "<CTSError" in xml_text or "CTSError" in xml_text:
            return None

        try:
            root = ET.fromstring(xml_text)

            # Extract text content
            text_parts = []
            for elem in root.iter():
                if elem.text:
                    text_parts.append(elem.text.strip())
                if elem.tail:
                    text_parts.append(elem.tail.strip())

            text = " ".join(text_parts)
            text = re.sub(r"\s+", " ", text).strip()

            if len(text) < 10:
                return None

            # Extract reference from URN
            ref_match = re.search(r":([^:]+)$", urn)
            reference = ref_match.group(1) if ref_match else urn

            return GreekPassage(
                urn=urn,
                reference=reference,
                text=text,
                source_url=url,
            )
        except ET.ParseError:
            return None

    def generate_refs(self, work_key: str) -> list[str]:
        """Generate reference URNs for a work.

        Args:
            work_key: Key from GREEK_WORKS dict

        Returns:
            List of URNs to try
        """
        if work_key not in GREEK_WORKS:
            return []

        work = GREEK_WORKS[work_key]
        urn = work["urn"]
        refs = []

        for book in range(1, work["books"] + 1):
            for section in range(1, work["sections_per_book"] + 1):
                ref = f"{urn}:{book}.{section}"
                refs.append(ref)

        return refs

    def fetch_work(self, work_key: str, max_passages: int = 500) -> list[GreekPassage]:
        """Fetch passages from a Greek work.

        Args:
            work_key: Key from GREEK_WORKS dict
            max_passages: Maximum passages to fetch

        Returns:
            List of GreekPassage objects
        """
        if work_key not in GREEK_WORKS:
            print(f"Unknown work: {work_key}")
            return []

        work = GREEK_WORKS[work_key]
        refs = self.generate_refs(work_key)

        print(f"Fetching {work['title']} by {work['author']}...")

        passages = []
        consecutive_failures = 0
        max_failures = 30

        for ref_urn in refs:
            if len(passages) >= max_passages:
                break

            passage = self.get_passage(ref_urn)
            if passage:
                passage.author = work["author"]
                passage.work = work["title"]
                passages.append(passage)
                consecutive_failures = 0
            else:
                consecutive_failures += 1
                if consecutive_failures >= max_failures:
                    break

            if len(passages) % 20 == 0 and len(passages) > 0:
                print(f"  Fetched {len(passages)} passages...")

        print(f"  Total: {len(passages)} passages from {work['title']}")
        return passages

    def search_tyrrhenian(
        self, work_key: Optional[str] = None, max_passages: int = 500
    ) -> list[GreekPassage]:
        """Search for passages mentioning Tyrrhenians/Etruscans.

        Args:
            work_key: Specific work to search, or None for all
            max_passages: Maximum passages to fetch per work

        Returns:
            Passages with Tyrrhenian references
        """
        results = []

        if work_key:
            works = {work_key: GREEK_WORKS[work_key]}
        else:
            works = GREEK_WORKS

        for key, work_info in works.items():
            passages = self.fetch_work(key, max_passages)
            tyrr_passages = [p for p in passages if p.contains_tyrrhenian_ref]
            results.extend(tyrr_passages)
            print(f"  Found {len(tyrr_passages)} Tyrrhenian references in {work_info['title']}")

        return results

    def fetch_dionysius_book5(self) -> list[GreekPassage]:
        """Fetch Dionysius book 5 specifically (rich in Etruscan content).

        Returns:
            Passages from book 5
        """
        work = GREEK_WORKS["dionysius_ant_rom"]
        urn = work["urn"]
        passages = []

        print("Fetching Dionysius Roman Antiquities Book 5...")

        for section in range(1, 100):
            ref = f"{urn}:5.{section}"
            passage = self.get_passage(ref)
            if passage:
                passage.author = work["author"]
                passage.work = work["title"]
                passages.append(passage)

        print(f"  Fetched {len(passages)} passages from Book 5")
        return passages

    def fetch_strabo_book5(self) -> list[GreekPassage]:
        """Fetch Strabo book 5 specifically (covers Etruria).

        Returns:
            Passages from book 5
        """
        work = GREEK_WORKS["strabo_geography"]
        urn = work["urn"]
        passages = []

        print("Fetching Strabo Geography Book 5...")

        for section in range(1, 50):
            ref = f"{urn}:5.{section}"
            passage = self.get_passage(ref)
            if passage:
                passage.author = work["author"]
                passage.work = work["title"]
                passages.append(passage)

        print(f"  Fetched {len(passages)} passages from Book 5")
        return passages


def get_available_greek_works() -> dict:
    """Get dictionary of available Greek works."""
    return GREEK_WORKS


def fetch_greek_etruscan_passages(max_per_work: int = 200) -> list[GreekPassage]:
    """Convenience function to fetch all Greek passages with Etruscan refs.

    Args:
        max_per_work: Maximum passages to fetch per work

    Returns:
        List of passages mentioning Etruscans
    """
    client = GreekCorpusClient()
    return client.search_tyrrhenian(max_passages=max_per_work)
