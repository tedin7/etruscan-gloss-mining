"""Italic language parallels for Etruscan vocabulary.

The Italic peoples (Umbrians, Oscans, etc.) were neighbors of
the Etruscans and borrowed terminology, especially for religion
and ritual. Identifying shared vocabulary helps validate
Etruscan terms and may reveal unknown Etruscan words.

Key sources:
- Iguvine Tables (Umbrian religious texts)
- Oscan inscriptions
- Latin texts discussing Italic traditions
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class ItalicParallel:
    """A parallel between Etruscan and Italic languages."""

    italic_word: str
    italic_language: str  # 'umbrian', 'oscan', 'faliscan', 'venetic'
    meaning: str
    source: str
    etruscan_parallel: Optional[str] = None
    relationship: str = "borrowed"  # 'borrowed_from_etruscan', 'shared', 'uncertain'
    confidence: float = 0.0
    notes: str = ""


# Umbrian religious terms from Iguvine Tables with Etruscan connections
UMBRIAN_RELIGIOUS_TERMS = [
    ItalicParallel(
        italic_word="ařfertur",
        italic_language="umbrian",
        meaning="priest, officiant",
        source="Iguvine Tables",
        etruscan_parallel="?",
        relationship="uncertain",
        confidence=0.40,
        notes="May have Etruscan influence on form",
    ),
    ItalicParallel(
        italic_word="persklum",
        italic_language="umbrian",
        meaning="prayer formula",
        source="Iguvine Tables",
        etruscan_parallel="?",
        relationship="uncertain",
        confidence=0.35,
    ),
    ItalicParallel(
        italic_word="vuçra",
        italic_language="umbrian",
        meaning="?",
        source="Iguvine Tables",
        etruscan_parallel="?",
        relationship="uncertain",
        confidence=0.30,
    ),
    ItalicParallel(
        italic_word="mantrahklu",
        italic_language="umbrian",
        meaning="bundle, lot",
        source="Iguvine Tables",
        etruscan_parallel="mantisa? (Latin loan)",
        relationship="shared",
        confidence=0.50,
        notes="Compare Latin mantisa from Etruscan",
    ),
    ItalicParallel(
        italic_word="tursa",
        italic_language="umbrian",
        meaning="incense, offering?",
        source="Iguvine Tables",
        etruscan_parallel="θura-?",
        relationship="borrowed_from_etruscan",
        confidence=0.55,
        notes="Religious context suggests Etruscan influence",
    ),
    ItalicParallel(
        italic_word="çerfie",
        italic_language="umbrian",
        meaning="of Ceres",
        source="Iguvine Tables",
        etruscan_parallel="?",
        relationship="uncertain",
        confidence=0.35,
    ),
    ItalicParallel(
        italic_word="pihaklu",
        italic_language="umbrian",
        meaning="piacular, expiatory",
        source="Iguvine Tables",
        etruscan_parallel="?",
        relationship="uncertain",
        confidence=0.30,
    ),
]

# Oscan vocabulary with possible Etruscan connections
OSCAN_PARALLELS = [
    ItalicParallel(
        italic_word="safinim",
        italic_language="oscan",
        meaning="Samnite",
        source="inscriptions",
        etruscan_parallel="?",
        relationship="uncertain",
        confidence=0.25,
    ),
    ItalicParallel(
        italic_word="meddíss",
        italic_language="oscan",
        meaning="magistrate",
        source="inscriptions",
        etruscan_parallel="maru?",
        relationship="uncertain",
        confidence=0.40,
        notes="Both may reflect shared Italic magistrate term",
    ),
    ItalicParallel(
        italic_word="vereia",
        italic_language="oscan",
        meaning="door?",
        source="inscriptions",
        etruscan_parallel="?",
        relationship="uncertain",
        confidence=0.30,
    ),
]

# Faliscan (closest Latin relative, Etruscan neighbor)
FALISCAN_PARALLELS = [
    ItalicParallel(
        italic_word="loifirta",
        italic_language="faliscan",
        meaning="freedwoman",
        source="inscriptions",
        etruscan_parallel="lautni (freedman)",
        relationship="borrowed_from_etruscan",
        confidence=0.65,
        notes="Faliscan heavily influenced by Etruscan",
    ),
    ItalicParallel(
        italic_word="carefo",
        italic_language="faliscan",
        meaning="I will make",
        source="inscriptions",
        etruscan_parallel="?",
        relationship="uncertain",
        confidence=0.30,
    ),
]

# Combined corpus
ALL_ITALIC_PARALLELS = UMBRIAN_RELIGIOUS_TERMS + OSCAN_PARALLELS + FALISCAN_PARALLELS


class ItalicParallelFinder:
    """Finder for Etruscan-Italic vocabulary parallels."""

    def __init__(self):
        """Initialize finder."""
        self.parallels = ALL_ITALIC_PARALLELS
        self._build_indices()

    def _build_indices(self) -> None:
        """Build lookup indices."""
        self.by_italic = {p.italic_word.lower(): p for p in self.parallels}
        self.by_language = {}
        for p in self.parallels:
            self.by_language.setdefault(p.italic_language, []).append(p)

    def find_by_etruscan(self, etruscan_word: str) -> list[ItalicParallel]:
        """Find Italic parallels for an Etruscan word.

        Args:
            etruscan_word: Etruscan word to check

        Returns:
            List of ItalicParallel objects
        """
        results = []
        word_lower = etruscan_word.lower()

        for parallel in self.parallels:
            if parallel.etruscan_parallel:
                # Clean up the parallel reference
                etr = parallel.etruscan_parallel.lower().rstrip("?").strip("*")
                if etr and (etr in word_lower or word_lower in etr):
                    results.append(parallel)

        return results

    def get_by_language(self, language: str) -> list[ItalicParallel]:
        """Get all parallels for a specific Italic language.

        Args:
            language: Language name (umbrian, oscan, faliscan)

        Returns:
            List of ItalicParallel objects
        """
        return self.by_language.get(language.lower(), [])

    def get_high_confidence(self, min_confidence: float = 0.50) -> list[ItalicParallel]:
        """Get high-confidence parallels.

        Args:
            min_confidence: Minimum confidence threshold

        Returns:
            List of ItalicParallel objects
        """
        return [p for p in self.parallels if p.confidence >= min_confidence]

    def get_borrowed_from_etruscan(self) -> list[ItalicParallel]:
        """Get words borrowed from Etruscan into Italic languages.

        Returns:
            List of ItalicParallel objects
        """
        return [p for p in self.parallels if p.relationship == "borrowed_from_etruscan"]

    def validate_etruscan_word(self, word: str) -> tuple[bool, float, str]:
        """Check if an Etruscan word has Italic language support.

        Args:
            word: Word to validate

        Returns:
            Tuple of (has_parallel, confidence, notes)
        """
        parallels = self.find_by_etruscan(word)

        if not parallels:
            return False, 0.0, "No Italic parallel found"

        best = max(parallels, key=lambda p: p.confidence)
        notes = f"Italic parallel: {best.italic_word} ({best.italic_language})"
        if best.meaning:
            notes += f" '{best.meaning}'"

        return True, best.confidence, notes


def find_italic_parallels(etruscan_words: list[str]) -> list[tuple[str, ItalicParallel]]:
    """Find Italic parallels for a list of Etruscan words.

    Args:
        etruscan_words: List of Etruscan words

    Returns:
        List of (etruscan_word, ItalicParallel) tuples
    """
    finder = ItalicParallelFinder()
    results = []

    for word in etruscan_words:
        parallels = finder.find_by_etruscan(word)
        for parallel in parallels:
            results.append((word, parallel))

    return sorted(results, key=lambda x: x[1].confidence, reverse=True)
