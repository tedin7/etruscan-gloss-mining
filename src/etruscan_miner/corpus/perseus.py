"""Perseus Digital Library API client.

Accesses texts via the CTS (Canonical Text Services) protocol.
Documentation: https://www.perseus.tufts.edu/hopper/CTS

Note: Perseus has rate limits. This client implements polite crawling
with delays between requests.

IMPORTANT - Perseus CTS API Status (as of 2026-01):
====================================================
- GetCapabilities: WORKS (returns XML inventory)
- GetValidReff: BROKEN (returns 500 / NullPointerException)
- GetPassage: WORKS for texts that exist in inventory

AVAILABLE texts (via CTS GetPassage):
- Pliny's Natural History: urn:cts:latinLit:phi0978.phi001.perseus-lat1
- Livy's Ab Urbe Condita: urn:cts:latinLit:phi0914.phi001.perseus-lat1
- Virgil's Aeneid: urn:cts:latinLit:phi0690.phi003.perseus-lat1

NOT AVAILABLE via CTS (use Latin Library instead):
- Varro's De Lingua Latina (phi0684) - NOT IN INVENTORY
- Festus' De Verborum Significatione - NOT IN INVENTORY
- Servius' Aeneid Commentary - NOT IN INVENTORY
- Isidore's Etymologiae - NOT IN INVENTORY

Use latin_library.py for texts not in Perseus CTS inventory.
"""

import re
import time
from dataclasses import dataclass
from typing import Optional
from xml.etree import ElementTree as ET

import requests

from ..config import PERSEUS_BASE_URL, PERSEUS_RATE_LIMIT


@dataclass
class TextPassage:
    """A passage of text from Perseus."""

    urn: str
    reference: str
    text: str
    language: str = "lat"
    source_url: Optional[str] = None


@dataclass
class WorkInfo:
    """Information about a work in Perseus."""

    urn: str
    title: str
    author: str
    language: str
    description: Optional[str] = None


class PerseusClient:
    """Client for Perseus Digital Library CTS API.

    The Perseus CTS API provides access to classical texts in TEI XML format.
    This client handles the API calls and parsing.
    """

    # CTS API endpoints
    CAPABILITIES_ENDPOINT = "?request=GetCapabilities"
    VALID_REFS_ENDPOINT = "?request=GetValidReff&urn={urn}"
    PASSAGE_ENDPOINT = "?request=GetPassage&urn={urn}"
    FIRST_URN_ENDPOINT = "?request=GetFirstUrn&urn={urn}"

    # Alternative: Scaife Viewer API (newer Perseus interface)
    SCAIFE_API_BASE = "https://scaife.perseus.org/library/urn:cts:"

    def __init__(
        self,
        base_url: str = PERSEUS_BASE_URL,
        rate_limit: float = PERSEUS_RATE_LIMIT,
        timeout: int = 30,
    ):
        """Initialize Perseus client.

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
            "User-Agent": "EtruscanGlossMiner/1.0 (Research project; contact@example.com)"
        })

    def _wait_for_rate_limit(self):
        """Wait to respect rate limit."""
        elapsed = time.time() - self._last_request
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self._last_request = time.time()

    def _make_request(self, url: str) -> Optional[str]:
        """Make an HTTP request with rate limiting.

        Args:
            url: Full URL to request

        Returns:
            Response text or None on error
        """
        self._wait_for_rate_limit()

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return None

    def get_capabilities(self) -> Optional[str]:
        """Get CTS capabilities (available texts).

        Returns:
            XML string of capabilities or None
        """
        url = f"{self.base_url}{self.CAPABILITIES_ENDPOINT}"
        return self._make_request(url)

    def get_valid_refs(self, urn: str) -> list[str]:
        """Get valid reference URNs for a work.

        WARNING: As of 2026-01, GetValidReff is BROKEN on Perseus server.
        It returns 500/NullPointerException or Freemarker template errors.
        Use generate_refs() for known citation schemes instead.

        Args:
            urn: Work URN (e.g., urn:cts:latinLit:phi0978.phi001)

        Returns:
            List of valid passage URNs (likely empty due to server bug)
        """
        url = f"{self.base_url}{self.VALID_REFS_ENDPOINT.format(urn=urn)}"
        xml_text = self._make_request(url)

        if not xml_text:
            return []

        # Check for CTS error response
        if "<CTSError" in xml_text or "CTSError" in xml_text:
            print(f"CTS API error for {urn} - text may not be in inventory")
            return []

        # Check for server error HTML response
        if "<html" in xml_text.lower() and "error occurred" in xml_text.lower():
            print(f"Server error for GetValidReff - this endpoint is broken on Perseus")
            return []

        refs = []
        try:
            # Parse XML to extract references
            root = ET.fromstring(xml_text)
            # CTS uses namespaces - handle both with and without
            for reff in root.iter():
                if reff.tag.endswith("reff") or reff.tag == "reff":
                    for urn_elem in reff:
                        if urn_elem.text:
                            refs.append(urn_elem.text.strip())
        except ET.ParseError as e:
            print(f"XML parse error: {e}")

        return refs

    def generate_refs(self, urn: str, citation_scheme: str = "book.section") -> list[str]:
        """Generate reference URNs for known citation schemes.

        Since GetValidReff is broken, we generate refs based on known
        citation patterns for specific works.

        Args:
            urn: Work URN (e.g., urn:cts:latinLit:phi0978.phi001.perseus-lat1)
            citation_scheme: One of "book.section", "book.chapter", "book.line"

        Returns:
            List of generated URNs to try
        """
        # Known citation schemes for important works
        CITATION_SCHEMES = {
            # Pliny Natural History: 37 books, variable sections per book
            "phi0978.phi001": {
                "scheme": "book.section",
                "books": 37,
                "sections_per_book": 50,  # Approximate max
            },
            # Livy Ab Urbe Condita: 142 books (only 35 survive)
            "phi0914.phi001": {
                "scheme": "book.chapter",
                "books": 45,  # Available books
                "sections_per_book": 60,
            },
            # Virgil Aeneid: 12 books
            "phi0690.phi003": {
                "scheme": "book.line",
                "books": 12,
                "sections_per_book": 1000,  # Lines per book
            },
        }

        # Extract work identifier from URN
        work_id = None
        for wid in CITATION_SCHEMES:
            if wid in urn:
                work_id = wid
                break

        if not work_id:
            print(f"Unknown work citation scheme for {urn}")
            return []

        scheme = CITATION_SCHEMES[work_id]
        refs = []

        for book in range(1, scheme["books"] + 1):
            for section in range(1, scheme["sections_per_book"] + 1):
                ref = f"{urn}:{book}.{section}"
                refs.append(ref)

        return refs

    def get_passage(self, urn: str) -> Optional[TextPassage]:
        """Get a specific passage by URN.

        Args:
            urn: Passage URN (e.g., urn:cts:latinLit:phi0978.phi001.perseus-lat1:1.1)

        Returns:
            TextPassage or None
        """
        url = f"{self.base_url}{self.PASSAGE_ENDPOINT.format(urn=urn)}"
        xml_text = self._make_request(url)

        if not xml_text:
            return None

        # Check for CTS error response (invalid URN, etc.)
        if "<CTSError" in xml_text or "CTSError" in xml_text:
            # This is normal for non-existent passages, don't log
            return None

        try:
            root = ET.fromstring(xml_text)

            # Extract text content - CTS returns TEI XML
            text_parts = []
            for elem in root.iter():
                if elem.text:
                    text_parts.append(elem.text.strip())
                if elem.tail:
                    text_parts.append(elem.tail.strip())

            text = " ".join(text_parts)
            # Clean up whitespace
            text = re.sub(r"\s+", " ", text).strip()

            # Skip if no meaningful text extracted
            if len(text) < 10:
                return None

            # Extract reference from URN
            ref_match = re.search(r":([^:]+)$", urn)
            reference = ref_match.group(1) if ref_match else urn

            return TextPassage(
                urn=urn,
                reference=reference,
                text=text,
                source_url=url,
            )
        except ET.ParseError as e:
            print(f"XML parse error for {urn}: {e}")
            return None

    def get_work_text(self, urn: str, max_passages: int = 1000) -> list[TextPassage]:
        """Get all passages for a work.

        Since GetValidReff is broken, this uses generate_refs() to enumerate
        possible passages and tries each one until max_passages are fetched.

        Args:
            urn: Work URN (e.g., urn:cts:latinLit:phi0978.phi001.perseus-lat1)
            max_passages: Maximum passages to fetch

        Returns:
            List of TextPassage objects
        """
        # First try GetValidReff (in case it starts working)
        refs = self.get_valid_refs(urn)

        # If that fails (which it will), generate refs
        if not refs:
            print("GetValidReff failed, using generated refs...")
            refs = self.generate_refs(urn)

        if not refs:
            print(f"No refs available for {urn}")
            return []

        passages = []
        consecutive_failures = 0
        max_failures = 20  # Stop after 20 consecutive invalid refs

        for i, ref_urn in enumerate(refs):
            if len(passages) >= max_passages:
                break

            passage = self.get_passage(ref_urn)
            if passage:
                passages.append(passage)
                consecutive_failures = 0
            else:
                consecutive_failures += 1
                if consecutive_failures >= max_failures:
                    print(f"  Stopping after {max_failures} consecutive failures")
                    break

            if len(passages) % 10 == 0 and len(passages) > 0:
                print(f"  Fetched {len(passages)} passages so far...")

        print(f"  Total: {len(passages)} passages fetched")
        return passages

    def search_text(self, urn: str, pattern: str) -> list[TextPassage]:
        """Search for pattern in a work's text.

        Args:
            urn: Work URN
            pattern: Regex pattern to search

        Returns:
            List of matching passages
        """
        compiled = re.compile(pattern, re.IGNORECASE)
        matches = []

        refs = self.get_valid_refs(urn)
        for ref_urn in refs:
            passage = self.get_passage(ref_urn)
            if passage and compiled.search(passage.text):
                matches.append(passage)

        return matches


class PerseusAltClient:
    """Alternative client using direct text file access.

    Some Perseus texts are available as plain text files, which is faster
    than the CTS XML API for bulk downloading.
    """

    # Direct text URLs (when available)
    TEXT_URLS = {
        "varro_de_lingua_latina": "https://www.perseus.tufts.edu/hopper/text?doc=Perseus%3Atext%3A1999.02.0017",
        "pliny_naturalis_historia": "https://www.perseus.tufts.edu/hopper/text?doc=Perseus%3Atext%3A1999.02.0138",
    }

    def __init__(self, timeout: int = 30):
        """Initialize alternative client."""
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "EtruscanGlossMiner/1.0 (Research project)"
        })

    def get_text_page(self, url: str) -> Optional[str]:
        """Fetch a text page and extract content.

        Args:
            url: URL to fetch

        Returns:
            Extracted text content
        """
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            # Extract text from HTML - look for main content
            html = response.text

            # Simple extraction: find content between markers
            # This is fragile and may need adjustment based on page structure
            text_match = re.search(
                r'<div[^>]*class="[^"]*text_container[^"]*"[^>]*>(.*?)</div>',
                html,
                re.DOTALL | re.IGNORECASE,
            )
            if text_match:
                text = text_match.group(1)
                # Strip HTML tags
                text = re.sub(r"<[^>]+>", " ", text)
                text = re.sub(r"\s+", " ", text).strip()
                return text

            return None
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return None


# Known work URNs that ARE available via Perseus CTS
AVAILABLE_WORKS = {
    "pliny_nh": "urn:cts:latinLit:phi0978.phi001.perseus-lat1",
    "livy_auc": "urn:cts:latinLit:phi0914.phi001.perseus-lat1",
    "virgil_aeneid": "urn:cts:latinLit:phi0690.phi003.perseus-lat1",
}

# Works NOT available via Perseus CTS (use Latin Library)
UNAVAILABLE_WORKS = {
    "varro_dll": "urn:cts:latinLit:phi0684.phi002",  # NOT IN INVENTORY
    "festus": None,  # NOT IN INVENTORY
    "servius": None,  # NOT IN INVENTORY
    "isidore": None,  # NOT IN INVENTORY
}


# Convenience functions
def fetch_varro() -> list[TextPassage]:
    """Fetch Varro's De Lingua Latina.

    WARNING: Varro is NOT in Perseus CTS inventory!
    This function will return empty. Use latin_library.py instead.
    """
    print("WARNING: Varro is NOT available via Perseus CTS API.")
    print("Use latin_library.py or download from Latin Library instead.")
    return []


def fetch_pliny(max_passages: int = 500) -> list[TextPassage]:
    """Fetch Pliny's Natural History.

    This work IS available via Perseus CTS.
    """
    client = PerseusClient()
    urn = AVAILABLE_WORKS["pliny_nh"]
    return client.get_work_text(urn, max_passages=max_passages)


def fetch_livy(max_passages: int = 500) -> list[TextPassage]:
    """Fetch Livy's Ab Urbe Condita.

    This work IS available via Perseus CTS.
    """
    client = PerseusClient()
    urn = AVAILABLE_WORKS["livy_auc"]
    return client.get_work_text(urn, max_passages=max_passages)


def search_for_etruscan_refs(client: PerseusClient, urn: str) -> list[TextPassage]:
    """Search a work for Etruscan references.

    Args:
        client: Perseus client
        urn: Work URN

    Returns:
        Passages mentioning Etruscan/Tuscan
    """
    # Pattern to match any Etruscan/Tuscan mention
    pattern = r"[Ee]trusc|[Tt]usc|[Tt]yrrhen"
    return client.search_text(urn, pattern)
