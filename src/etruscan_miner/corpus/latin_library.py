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
# Organized by priority for gloss mining
LATIN_LIBRARY_URLS = {
    # === HIGH PRIORITY: Primary sources for Etruscan glosses ===

    # Varro De Lingua Latina (Books 5-10 survive) - already cached
    "varro_ll_5": "https://www.thelatinlibrary.com/varro.ling5.html",
    "varro_ll_6": "https://www.thelatinlibrary.com/varro.ling6.html",
    "varro_ll_7": "https://www.thelatinlibrary.com/varro.ling7.html",
    "varro_ll_8": "https://www.thelatinlibrary.com/varro.ling8.html",
    "varro_ll_9": "https://www.thelatinlibrary.com/varro.ling9.html",
    "varro_ll_10": "https://www.thelatinlibrary.com/varro.ling10.html",

    # Festus Breviarium (Note: De Verborum Significatione not available here)
    "festus": "https://www.thelatinlibrary.com/festus.shtml",

    # Isidore Etymologiae (20 books) - rich in etymological content
    "isidore_1": "https://www.thelatinlibrary.com/isidore/1.shtml",
    "isidore_2": "https://www.thelatinlibrary.com/isidore/2.shtml",
    "isidore_3": "https://www.thelatinlibrary.com/isidore/3.shtml",
    "isidore_4": "https://www.thelatinlibrary.com/isidore/4.shtml",
    "isidore_5": "https://www.thelatinlibrary.com/isidore/5.shtml",
    "isidore_6": "https://www.thelatinlibrary.com/isidore/6.shtml",
    "isidore_7": "https://www.thelatinlibrary.com/isidore/7.shtml",
    "isidore_8": "https://www.thelatinlibrary.com/isidore/8.shtml",
    "isidore_9": "https://www.thelatinlibrary.com/isidore/9.shtml",
    "isidore_10": "https://www.thelatinlibrary.com/isidore/10.shtml",
    "isidore_11": "https://www.thelatinlibrary.com/isidore/11.shtml",
    "isidore_12": "https://www.thelatinlibrary.com/isidore/12.shtml",
    "isidore_13": "https://www.thelatinlibrary.com/isidore/13.shtml",
    "isidore_14": "https://www.thelatinlibrary.com/isidore/14.shtml",
    "isidore_15": "https://www.thelatinlibrary.com/isidore/15.shtml",
    "isidore_16": "https://www.thelatinlibrary.com/isidore/16.shtml",
    "isidore_17": "https://www.thelatinlibrary.com/isidore/17.shtml",
    "isidore_18": "https://www.thelatinlibrary.com/isidore/18.shtml",
    "isidore_19": "https://www.thelatinlibrary.com/isidore/19.shtml",
    "isidore_20": "https://www.thelatinlibrary.com/isidore/20.shtml",

    # Solinus De Mirabilibus Mundi - geographical/etymological content
    "solinus_mommsen2": "https://www.thelatinlibrary.com/solinus5.html",
    "solinus_1a": "https://www.thelatinlibrary.com/solinus1a.html",
    "solinus_2a": "https://www.thelatinlibrary.com/solinus2a.html",
    "solinus_3a": "https://www.thelatinlibrary.com/solinus3a.html",
    "solinus_4a": "https://www.thelatinlibrary.com/solinus4a.html",

    # === MEDIUM PRIORITY: Historical sources with Etruscan references ===

    # Suetonius Lives of the Caesars
    "suetonius_caesar": "https://www.thelatinlibrary.com/suetonius/suet.caesar.html",
    "suetonius_augustus": "https://www.thelatinlibrary.com/suetonius/suet.aug.html",
    "suetonius_tiberius": "https://www.thelatinlibrary.com/suetonius/suet.tib.html",
    "suetonius_caligula": "https://www.thelatinlibrary.com/suetonius/suet.cal.html",
    "suetonius_claudius": "https://www.thelatinlibrary.com/suetonius/suet.claudius.html",
    "suetonius_nero": "https://www.thelatinlibrary.com/suetonius/suet.nero.html",
    "suetonius_galba": "https://www.thelatinlibrary.com/suetonius/suet.galba.html",
    "suetonius_otho": "https://www.thelatinlibrary.com/suetonius/suet.otho.html",
    "suetonius_vitellius": "https://www.thelatinlibrary.com/suetonius/suet.vit.html",
    "suetonius_vespasian": "https://www.thelatinlibrary.com/suetonius/suet.vesp.html",
    "suetonius_titus": "https://www.thelatinlibrary.com/suetonius/suet.titus.html",
    "suetonius_domitian": "https://www.thelatinlibrary.com/suetonius/suet.dom.html",
    # Suetonius De Poetis
    "suetonius_terence": "https://www.thelatinlibrary.com/suetonius/suet.terence.html",
    "suetonius_virgil": "https://www.thelatinlibrary.com/suetonius/suet.virgil.html",
    "suetonius_horace": "https://www.thelatinlibrary.com/suetonius/suet.horace.html",
    "suetonius_tibullus": "https://www.thelatinlibrary.com/suetonius/suet.tibullus.html",
    "suetonius_persius": "https://www.thelatinlibrary.com/suetonius/suet.persius.html",
    "suetonius_lucan": "https://www.thelatinlibrary.com/suetonius/suet.lucan.html",
    "suetonius_pliny": "https://www.thelatinlibrary.com/suetonius/suet.pliny.html",
    "suetonius_crispus": "https://www.thelatinlibrary.com/suetonius/suet.crispus.html",
    "suetonius_grammaticis": "https://www.thelatinlibrary.com/suetonius/suet.gram.html",
    "suetonius_rhetoribus": "https://www.thelatinlibrary.com/suetonius/suet.rhet.html",

    # Livy Ab Urbe Condita (surviving books)
    "livy_praef": "https://www.thelatinlibrary.com/livy/liv.pr.shtml",
    "livy_1": "https://www.thelatinlibrary.com/livy/liv.1.shtml",
    "livy_2": "https://www.thelatinlibrary.com/livy/liv.2.shtml",
    "livy_3": "https://www.thelatinlibrary.com/livy/liv.3.shtml",
    "livy_4": "https://www.thelatinlibrary.com/livy/liv.4.shtml",
    "livy_5": "https://www.thelatinlibrary.com/livy/liv.5.shtml",
    "livy_6": "https://www.thelatinlibrary.com/livy/liv.6.shtml",
    "livy_7": "https://www.thelatinlibrary.com/livy/liv.7.shtml",
    "livy_8": "https://www.thelatinlibrary.com/livy/liv.8.shtml",
    "livy_9": "https://www.thelatinlibrary.com/livy/liv.9.shtml",
    "livy_10": "https://www.thelatinlibrary.com/livy/liv.10.shtml",
    # Books 11-20 lost
    "livy_21": "https://www.thelatinlibrary.com/livy/liv.21.shtml",
    "livy_22": "https://www.thelatinlibrary.com/livy/liv.22.shtml",
    "livy_23": "https://www.thelatinlibrary.com/livy/liv.23.shtml",
    "livy_24": "https://www.thelatinlibrary.com/livy/liv.24.shtml",
    "livy_25": "https://www.thelatinlibrary.com/livy/liv.25.shtml",
    "livy_26": "https://www.thelatinlibrary.com/livy/liv.26.shtml",
    "livy_27": "https://www.thelatinlibrary.com/livy/liv.27.shtml",
    "livy_28": "https://www.thelatinlibrary.com/livy/liv.28.shtml",
    "livy_29": "https://www.thelatinlibrary.com/livy/liv.29.shtml",
    "livy_30": "https://www.thelatinlibrary.com/livy/liv.30.shtml",
    "livy_31": "https://www.thelatinlibrary.com/livy/liv.31.shtml",
    "livy_32": "https://www.thelatinlibrary.com/livy/liv.32.shtml",
    "livy_33": "https://www.thelatinlibrary.com/livy/liv.33.shtml",
    "livy_34": "https://www.thelatinlibrary.com/livy/liv.34.shtml",
    "livy_35": "https://www.thelatinlibrary.com/livy/liv.35.shtml",
    "livy_36": "https://www.thelatinlibrary.com/livy/liv.36.shtml",
    "livy_37": "https://www.thelatinlibrary.com/livy/liv.37.shtml",
    "livy_38": "https://www.thelatinlibrary.com/livy/liv.38.shtml",
    "livy_39": "https://www.thelatinlibrary.com/livy/liv.39.shtml",
    "livy_40": "https://www.thelatinlibrary.com/livy/liv.40.shtml",
    "livy_41": "https://www.thelatinlibrary.com/livy/liv.41.shtml",
    "livy_42": "https://www.thelatinlibrary.com/livy/liv.42.shtml",
    "livy_43": "https://www.thelatinlibrary.com/livy/liv.43.shtml",
    "livy_44": "https://www.thelatinlibrary.com/livy/liv.44.shtml",
    "livy_45": "https://www.thelatinlibrary.com/livy/liv.45.shtml",
    "livy_periochae": "https://www.thelatinlibrary.com/livy/liv.per.shtml",

    # === COMPLETENESS: Other miscellaneous texts ===

    # Miscellany authors with potential etymological content
    "ampelius": "https://www.thelatinlibrary.com/ampelius.shtml",
    "censorinus": "https://www.thelatinlibrary.com/censorinus.html",
    "donatus": "https://www.thelatinlibrary.com/don.html",
    "fulgentius": "https://www.thelatinlibrary.com/fulgentius.html",
    "hyginus": "https://www.thelatinlibrary.com/hyginus.html",
    "manilius": "https://www.thelatinlibrary.com/manilius.html",
    "orosius": "https://www.thelatinlibrary.com/orosius.html",
    "pomponius_mela": "https://www.thelatinlibrary.com/pomponius.html",

    # Note: Pliny Natural History and Servius Commentary not available on Latin Library
    # Use Perseus CTS API for Pliny NH
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
