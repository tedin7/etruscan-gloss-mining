"""GitHub corpus reader for CLTK Latin Library texts.

The GitHub corpus at data/corpus/github/lat_text_latin_library/ contains
pre-scraped Latin texts from The Latin Library. This module provides
a reader to iterate over all 2000+ text files for mining.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional

from ..config import CORPUS_CACHE_DIR


@dataclass
class GitHubText:
    """A text file from the GitHub corpus."""

    filename: str
    author: str
    title: str
    text: str
    file_path: Path


class GitHubCorpusReader:
    """Reader for the GitHub CLTK Latin Library corpus.

    The corpus contains ~2000 text files in various subdirectories.
    Files are plain text Latin with minimal markup.
    """

    def __init__(self, corpus_dir: Optional[Path] = None):
        """Initialize the reader.

        Args:
            corpus_dir: Path to corpus directory. Defaults to
                data/corpus/github/lat_text_latin_library/
        """
        if corpus_dir is None:
            corpus_dir = CORPUS_CACHE_DIR / "github" / "lat_text_latin_library"
        self.corpus_dir = corpus_dir

    def list_files(self) -> list[Path]:
        """List all .txt files in the corpus.

        Returns:
            List of paths to text files, sorted by path.
        """
        if not self.corpus_dir.exists():
            return []

        files = list(self.corpus_dir.rglob("*.txt"))
        return sorted(files)

    def read_file(self, path: Path) -> GitHubText:
        """Read a single text file.

        Args:
            path: Path to the text file.

        Returns:
            GitHubText object with parsed metadata and content.
        """
        text = path.read_text(encoding="utf-8", errors="replace")

        # Parse author and title from path
        # Files are like: cicero/cic.att1.txt or ammianus/amm1.txt
        relative = path.relative_to(self.corpus_dir)
        parts = list(relative.parts)

        if len(parts) > 1:
            # Subdirectory structure: author/title.txt
            author = parts[0].title()
            title = path.stem
        else:
            # Top-level file: filename.txt
            author = self._guess_author(path.stem)
            title = path.stem

        # Clean up text - remove excessive whitespace
        text = self._clean_text(text)

        return GitHubText(
            filename=path.name,
            author=author,
            title=title,
            text=text,
            file_path=path,
        )

    def _guess_author(self, filename: str) -> str:
        """Guess author from filename patterns.

        Args:
            filename: Filename without extension.

        Returns:
            Best guess at author name.
        """
        # Common prefixes -> authors
        author_prefixes = {
            "cic": "Cicero",
            "verg": "Virgil",
            "hor": "Horace",
            "ovid": "Ovid",
            "liv": "Livy",
            "tac": "Tacitus",
            "plin": "Pliny",
            "sen": "Seneca",
            "caes": "Caesar",
            "sall": "Sallust",
            "ter": "Terence",
            "plaut": "Plautus",
            "cat": "Catullus",
            "luc": "Lucan",
            "juv": "Juvenal",
            "mart": "Martial",
            "prop": "Propertius",
            "tib": "Tibullus",
            "apul": "Apuleius",
            "gell": "Gellius",
            "varro": "Varro",
            "isid": "Isidore",
            "fest": "Festus",
            "serv": "Servius",
            "suet": "Suetonius",
            "amm": "Ammianus",
            "aug": "Augustine",
            "hier": "Jerome",
            "boed": "Boethius",
        }

        filename_lower = filename.lower()
        for prefix, author in author_prefixes.items():
            if filename_lower.startswith(prefix):
                return author

        return "Unknown"

    def _clean_text(self, text: str) -> str:
        """Clean up text content.

        Args:
            text: Raw text content.

        Returns:
            Cleaned text.
        """
        # Normalize whitespace
        text = re.sub(r"\s+", " ", text)
        # Restore paragraph breaks
        text = re.sub(r"\s*\n\s*\n\s*", "\n\n", text)
        return text.strip()

    def iter_texts(self) -> Iterator[GitHubText]:
        """Iterate over all texts in the corpus.

        Yields:
            GitHubText objects for each file.
        """
        for path in self.list_files():
            try:
                yield self.read_file(path)
            except Exception as e:
                print(f"Error reading {path}: {e}")
                continue

    def count_files(self) -> int:
        """Count total text files in corpus.

        Returns:
            Number of .txt files.
        """
        return len(self.list_files())

    def search_files(self, pattern: str) -> list[GitHubText]:
        """Search for files matching a pattern in filename or content.

        Args:
            pattern: Regex pattern to match.

        Returns:
            List of matching GitHubText objects.
        """
        regex = re.compile(pattern, re.IGNORECASE)
        matches = []

        for text in self.iter_texts():
            if regex.search(text.filename) or regex.search(text.text):
                matches.append(text)

        return matches

    def get_etruscan_mentions(self) -> list[GitHubText]:
        """Find all files mentioning Etruscans/Tuscans.

        Returns:
            List of GitHubText objects with Etruscan mentions.
        """
        return self.search_files(
            r"\b(etrusc|tusci?|tyrrhen|rasenn)\w*\b"
        )


def load_github_corpus() -> list[GitHubText]:
    """Load all texts from the GitHub corpus.

    Returns:
        List of all GitHubText objects.
    """
    reader = GitHubCorpusReader()
    return list(reader.iter_texts())
