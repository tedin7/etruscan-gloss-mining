"""Latin Library corpus loader.

The Latin Library (https://www.thelatinlibrary.com/) hosts plain-text versions
of many Latin texts that are NOT available via Perseus CTS API.

Key texts for Etruscan gloss mining available here:
- Varro's De Lingua Latina (Books 5-10)
- Festus' De Verborum Significatione (epitome)
- Isidore's Etymologiae (excerpts)

Note: We already have Varro cached in data/corpus/latin_library/
"""

import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

from ..config import CORPUS_CACHE_DIR


@dataclass
class LatinLibraryText:
    """A text from the Latin Library."""

    title: str
    author: str
    book: Optional[str]
    text: str
    source_url: str
    local_path: Optional[Path] = None


# Known URLs for texts relevant to Etruscan studies
LATIN_LIBRARY_URLS = {
    "varro_ll_5": "https://www.thelatinlibrary.com/varro.ling5.html",
    "varro_ll_6": "https://www.thelatinlibrary.com/varro.ling6.html",
    "varro_ll_7": "https://www.thelatinlibrary.com/varro.ling7.html",
    "varro_ll_8": "https://www.thelatinlibrary.com/varro.ling8.html",
    "varro_ll_9": "https://www.thelatinlibrary.com/varro.ling9.html",
    "varro_ll_10": "https://www.thelatinlibrary.com/varro.ling10.html",
    # Festus is not directly available, but summaries exist
    # Isidore excerpts
}


class LatinLibraryClient:
    """Client for downloading texts from the Latin Library."""

    BASE_URL = "https://www.thelatinlibrary.com"

    def __init__(self, cache_dir: Optional[Path] = None, rate_limit: float = 2.0):
        """Initialize client.

        Args:
            cache_dir: Directory to cache downloaded texts
            rate_limit: Minimum seconds between requests
        """
        self.cache_dir = cache_dir or CORPUS_CACHE_DIR / "latin_library"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.rate_limit = rate_limit
        self._last_request = 0.0
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "EtruscanGlossMiner/1.0 (Academic research)"
        })

    def _wait_for_rate_limit(self):
        """Wait to respect rate limit."""
        elapsed = time.time() - self._last_request
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self._last_request = time.time()

    def _get_cache_path(self, text_id: str) -> Path:
        """Get cache file path for a text ID."""
        return self.cache_dir / f"{text_id}.html"

    def download_text(self, text_id: str, url: Optional[str] = None) -> Optional[str]:
        """Download a text from the Latin Library.

        Args:
            text_id: Text identifier (e.g., "varro_ll_5")
            url: URL to download from (uses known URL if not specified)

        Returns:
            HTML content or None on error
        """
        # Check cache first
        cache_path = self._get_cache_path(text_id)
        if cache_path.exists():
            print(f"Loading {text_id} from cache...")
            return cache_path.read_text(encoding="utf-8")

        # Get URL
        if url is None:
            url = LATIN_LIBRARY_URLS.get(text_id)
            if url is None:
                print(f"Unknown text ID: {text_id}")
                return None

        # Download
        print(f"Downloading {text_id} from {url}...")
        self._wait_for_rate_limit()

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            html = response.text

            # Cache it
            cache_path.write_text(html, encoding="utf-8")
            print(f"  Cached to {cache_path}")

            return html
        except requests.exceptions.RequestException as e:
            print(f"Download error: {e}")
            return None

    def parse_html(self, html: str) -> str:
        """Extract text content from Latin Library HTML.

        Args:
            html: Raw HTML content

        Returns:
            Extracted Latin text
        """
        soup = BeautifulSoup(html, "lxml")

        # Remove script and style elements
        for element in soup(["script", "style", "head"]):
            element.decompose()

        # Get text from body
        body = soup.find("body")
        if not body:
            return ""

        # Extract text, preserving paragraph structure
        text_parts = []
        for elem in body.find_all(["p", "div", "span", "br"]):
            text = elem.get_text(separator=" ", strip=True)
            if text:
                text_parts.append(text)

        # If no paragraphs found, get all text
        if not text_parts:
            text_parts = [body.get_text(separator=" ", strip=True)]

        text = "\n\n".join(text_parts)

        # Clean up
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"\n\s*\n", "\n\n", text)
        return text.strip()

    def get_text(self, text_id: str) -> Optional[LatinLibraryText]:
        """Get a text by ID, downloading if necessary.

        Args:
            text_id: Text identifier (e.g., "varro_ll_5")

        Returns:
            LatinLibraryText or None
        """
        html = self.download_text(text_id)
        if not html:
            return None

        text_content = self.parse_html(html)

        # Parse metadata from text_id
        if text_id.startswith("varro_ll_"):
            book = text_id.split("_")[-1]
            return LatinLibraryText(
                title="De Lingua Latina",
                author="Varro",
                book=f"Book {book}",
                text=text_content,
                source_url=LATIN_LIBRARY_URLS.get(text_id, ""),
                local_path=self._get_cache_path(text_id),
            )

        return LatinLibraryText(
            title=text_id,
            author="Unknown",
            book=None,
            text=text_content,
            source_url=LATIN_LIBRARY_URLS.get(text_id, ""),
            local_path=self._get_cache_path(text_id),
        )

    def get_varro_de_lingua_latina(self) -> list[LatinLibraryText]:
        """Get all books of Varro's De Lingua Latina.

        Returns:
            List of LatinLibraryText objects for books 5-10
        """
        texts = []
        for book in range(5, 11):
            text_id = f"varro_ll_{book}"
            text = self.get_text(text_id)
            if text:
                texts.append(text)
        return texts


def load_cached_varro() -> list[LatinLibraryText]:
    """Load Varro from cache if already downloaded.

    Returns:
        List of LatinLibraryText objects
    """
    client = LatinLibraryClient()
    texts = []

    for book in range(5, 11):
        text_id = f"varro_ll_{book}"
        cache_path = client._get_cache_path(text_id)
        if cache_path.exists():
            html = cache_path.read_text(encoding="utf-8")
            text_content = client.parse_html(html)
            texts.append(LatinLibraryText(
                title="De Lingua Latina",
                author="Varro",
                book=f"Book {book}",
                text=text_content,
                source_url=LATIN_LIBRARY_URLS.get(text_id, ""),
                local_path=cache_path,
            ))

    return texts
