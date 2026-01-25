"""Inscription corpus loader for Etruscan texts.

Loads and parses Etruscan inscription data from:
1. Zenodo Digital Concordance CSV (reference IDs and cross-references)
2. Materials for the Study of Etruscan Language text (actual inscription texts)

The inscription data provides ground-truth vocabulary for validation.
"""

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, Optional

from ..db.models import EtruscanWord
from ..db.repository import Repository


@dataclass
class Inscription:
    """An Etruscan inscription."""

    corpus_id: str  # CIE, TLE, ET reference number
    text: str  # Etruscan text
    line_number: int = 1
    transliteration: str = ""
    provenance: str = ""
    date_range: str = ""
    source: str = ""
    notes: str = ""

    @property
    def words(self) -> list[str]:
        """Extract words from inscription text."""
        # Remove interpuncts, brackets, special markers
        clean = re.sub(r"[·•.,:;\[\]<>{}()+/\\~\-]", " ", self.text)
        # Remove numbers
        clean = re.sub(r"\d+", " ", clean)
        # Split and filter
        words = [w.strip().lower() for w in clean.split() if len(w.strip()) >= 2]
        # Filter out Latin markers and obvious fragments
        words = [w for w in words if not w.startswith("{") and not w.endswith("}")]
        return words


@dataclass
class ConcordanceEntry:
    """Entry from the Zenodo concordance CSV."""

    trismegistos: str = ""
    cie: str = ""
    et1: str = ""  # Etruskische Texte 1st edition
    et2: str = ""  # Etruskische Texte 2nd edition
    tle: str = ""  # Testimonia Linguae Etruscae
    bakkum: str = ""
    cil_i: str = ""
    cil_i2: str = ""
    cil_iii: str = ""
    cil_vi: str = ""
    cil_xi: str = ""
    cii: str = ""
    cii_suppl: str = ""
    cii_app: str = ""
    multiple_refs: bool = False
    notes: str = ""
    source: str = ""
    edit_log: str = ""


class InscriptionLoader:
    """Load Etruscan inscriptions from corpus files."""

    def __init__(self, corpus_dir: Optional[Path] = None):
        """Initialize loader.

        Args:
            corpus_dir: Path to corpus/inscriptions directory.
                       Defaults to data/corpus/inscriptions/
        """
        if corpus_dir is None:
            # Default path relative to project
            corpus_dir = Path(__file__).parent.parent.parent.parent / "data" / "corpus" / "inscriptions"
        self.corpus_dir = corpus_dir
        self.concordance_path = corpus_dir / "etruscan_concordance.csv"
        self.materials_path = corpus_dir / "etruscan_materials.txt"

    def load_concordance(self) -> list[ConcordanceEntry]:
        """Load the Zenodo concordance CSV.

        Returns:
            List of concordance entries with cross-references.
        """
        if not self.concordance_path.exists():
            print(f"Concordance file not found: {self.concordance_path}")
            return []

        entries = []
        with open(self.concordance_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                entry = ConcordanceEntry(
                    trismegistos=row.get("Trismegistos", ""),
                    cie=row.get("CIE", ""),
                    et1=row.get("Rix. ET1", ""),
                    et2=row.get("Meiser. ET2", ""),
                    tle=row.get("TLE", ""),
                    bakkum=row.get("Bakkum", ""),
                    cil_i=row.get("CIL I", ""),
                    cil_i2=row.get("CIL I(2)", ""),
                    cil_iii=row.get("CIL III", ""),
                    cil_vi=row.get("CIL VI", ""),
                    cil_xi=row.get("CIL XI", ""),
                    cii=row.get("CII", ""),
                    cii_suppl=row.get("CII Suppl.", ""),
                    cii_app=row.get("CII App", ""),
                    multiple_refs=row.get("Multiple references?", "").lower() == "yes",
                    notes=row.get("Notes", ""),
                    source=row.get("Source", ""),
                    edit_log=row.get("Edit log", ""),
                )
                entries.append(entry)

        return entries

    def parse_materials_text(self) -> Iterator[Inscription]:
        """Parse inscriptions from Materials for the Study of Etruscan Language.

        This file has OCR formatting issues. The format is roughly:
        inscription_number (on its own line, sometimes with line number)
        followed by inscription text (uppercase Latin letters)

        Yields:
            Inscription objects
        """
        if not self.materials_path.exists():
            print(f"Materials file not found: {self.materials_path}")
            return

        with open(self.materials_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        lines = content.split("\n")
        current_id = None

        # Find the corpus section (look for first inscription number after preface)
        in_corpus = False

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Skip until we hit the corpus section (after line ~420)
            if not in_corpus:
                if i > 400 and re.match(r"^[1-9]$", stripped):
                    in_corpus = True
                else:
                    continue

            # Check if this looks like an inscription number (standalone 1-9999)
            if re.match(r"^\d{1,5}$", stripped):
                num = int(stripped)
                if 1 <= num <= 9999:
                    current_id = str(num)
                continue

            # Skip line numbers (usually 1-9 on their own)
            if re.match(r"^[1-9]$", stripped):
                continue

            # Skip page numbers and headers
            if re.match(r"^\d+\s+(Corpus|Alphabet|Frequency|Index)", stripped):
                continue

            # Check if this looks like inscription text
            # Etruscan text: uppercase Latin letters, special chars, interpuncts
            if stripped and current_id:
                # Must have at least some uppercase letters
                # Must not be just numbers or punctuation
                if re.search(r"[A-Z]{2,}", stripped):
                    # Filter out English text (preface/headers)
                    if not re.search(r"\b(the|and|of|to|in|is|for|with)\b", stripped.lower()):
                        yield Inscription(
                            corpus_id=f"CIE {current_id}",
                            text=stripped,
                            line_number=1,
                            source="Materials for the Study of Etruscan Language",
                        )

    def extract_vocabulary(self) -> set[str]:
        """Extract unique Etruscan words from all inscriptions.

        Returns:
            Set of unique words (lowercase, cleaned)
        """
        vocabulary = set()

        for inscription in self.parse_materials_text():
            for word in inscription.words:
                # Clean OCR artifacts - keep only letters
                clean = re.sub(r"[^a-zA-Z]", "", word).lower()
                if clean and len(clean) >= 2:
                    vocabulary.add(clean)

        # Filter valid words
        vocabulary = {w for w in vocabulary if self._is_valid_word(w)}

        return vocabulary

    def _is_valid_word(self, word: str) -> bool:
        """Check if a word looks like valid Etruscan.

        Etruscan characteristics:
        - No voiced stops (b, d, g) - but OCR might have errors
        - Common endings: -al, -s, -na, -i, -a
        - Length typically 2-15 characters
        """
        # Clean OCR artifacts first
        clean = re.sub(r"[^a-z]", "", word.lower())

        if len(clean) < 2 or len(clean) > 20:
            return False

        # Must be mostly alphabetic (at least 80%)
        if len(clean) < len(word) * 0.6:
            return False

        # Must have at least one vowel
        if not re.search(r"[aeiouy]", clean):
            return False

        # Skip common Latin words that might have slipped in
        latin_words = {"et", "de", "in", "ad", "cum", "per", "pro", "ab", "ex", "la", "mi"}
        if clean in latin_words:
            return False

        # Skip if word is all consonants or all vowels (OCR error)
        vowels = len(re.findall(r"[aeiouy]", clean))
        consonants = len(clean) - vowels
        if consonants == 0 or vowels == 0:
            return False

        return True

    def import_to_db(self, repo: Repository, source: str = "inscriptions") -> int:
        """Import inscription vocabulary into the database.

        Args:
            repo: Database repository
            source: Source identifier for the vocabulary entries

        Returns:
            Number of words imported
        """
        vocabulary = self.extract_vocabulary()
        count = 0

        for word in vocabulary:
            etruscan_word = EtruscanWord(
                word=word,
                word_normalized=word.lower(),
                source=source,
                category="inscription",
                reliability=4,  # High reliability - from actual inscriptions
                notes="Extracted from Corpus Inscriptionum Etruscarum",
            )
            try:
                repo.insert_vocabulary(etruscan_word)
                count += 1
            except Exception as e:
                # Skip duplicates
                pass

        return count

    def get_statistics(self) -> dict:
        """Get statistics about the inscription corpus.

        Returns:
            Dictionary with corpus statistics
        """
        concordance = self.load_concordance()
        vocabulary = self.extract_vocabulary()

        inscriptions = list(self.parse_materials_text())

        return {
            "concordance_entries": len(concordance),
            "inscriptions_parsed": len(inscriptions),
            "unique_words": len(vocabulary),
            "concordance_file": str(self.concordance_path),
            "materials_file": str(self.materials_path),
            "concordance_exists": self.concordance_path.exists(),
            "materials_exists": self.materials_path.exists(),
        }


def load_inscription_vocabulary(corpus_dir: Optional[Path] = None) -> set[str]:
    """Convenience function to load inscription vocabulary.

    Args:
        corpus_dir: Optional path to corpus directory

    Returns:
        Set of unique Etruscan words from inscriptions
    """
    loader = InscriptionLoader(corpus_dir)
    return loader.extract_vocabulary()
