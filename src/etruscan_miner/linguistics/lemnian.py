"""Lemnian language corpus and analysis.

Lemnian is the only known language related to Etruscan, attested
from inscriptions on the island of Lemnos in the Aegean Sea,
primarily the Kaminia stele (6th century BCE). With only ~40
attested words, every parallel with Etruscan is significant.

The Tyrsenian language family hypothesis groups:
- Etruscan (Italy)
- Lemnian (Lemnos, Greece)
- Raetic (Alpine region)
"""

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LemnianWord:
    """A Lemnian word with analysis."""

    form: str
    normalized: str  # Normalized form for comparison
    meaning: Optional[str] = None
    part_of_speech: Optional[str] = None
    morphology: Optional[str] = None  # e.g., "genitive", "past tense"
    source: str = "kaminia"  # Inscription source
    etruscan_parallel: Optional[str] = None
    confidence: float = 0.0  # Confidence in Etruscan parallel
    notes: str = ""


# Complete Lemnian corpus from known inscriptions
LEMNIAN_CORPUS = [
    # Kaminia stele - Face A
    LemnianWord(
        form="holaieś",
        normalized="holaies",
        meaning="?warrior/?title",
        part_of_speech="noun",
        source="kaminia_a",
        etruscan_parallel="?",
        notes="Possibly a name or title",
    ),
    LemnianWord(
        form="φokiasiale",
        normalized="phokiasiale",
        meaning="of Phocaea?",
        part_of_speech="adjective",
        source="kaminia_a",
        etruscan_parallel="?",
        morphology="genitive/adjective -ale",
        notes="May refer to Phocaea; -ale suffix like Etruscan",
    ),
    LemnianWord(
        form="sivai",
        normalized="sivai",
        meaning="years/lived",
        part_of_speech="noun/verb",
        source="kaminia_a",
        etruscan_parallel="sval (to live)",
        confidence=0.85,
        notes="Compare Etruscan sval- 'to live', avils 'years'",
    ),
    LemnianWord(
        form="aviś",
        normalized="avis",
        meaning="year(s)",
        part_of_speech="noun",
        source="kaminia_a",
        etruscan_parallel="avil (year)",
        confidence=0.90,
        notes="Clear cognate with Etruscan avil 'year'",
    ),
    LemnianWord(
        form="sialχvis",
        normalized="sialchvis",
        meaning="40 (years)?",
        part_of_speech="numeral",
        source="kaminia_a",
        etruscan_parallel="*śealχ (40?)",
        confidence=0.70,
        notes="Possibly numeral; compare Etruscan numerals",
    ),
    LemnianWord(
        form="maraśm",
        normalized="marasm",
        meaning="magistrate?",
        part_of_speech="noun",
        source="kaminia_a",
        etruscan_parallel="maru (magistrate)",
        confidence=0.80,
        notes="Compare Etruscan maru 'magistrate'",
    ),
    LemnianWord(
        form="avis",
        normalized="avis",
        meaning="year",
        part_of_speech="noun",
        source="kaminia_a",
        etruscan_parallel="avil",
        confidence=0.90,
        notes="Variant spelling of aviś",
    ),
    LemnianWord(
        form="eφtešio",
        normalized="ephtesio",
        meaning="?Ephesian?",
        part_of_speech="adjective",
        source="kaminia_a",
        notes="Possibly ethnic adjective",
    ),
    LemnianWord(
        form="arai",
        normalized="arai",
        meaning="?make/?set up",
        part_of_speech="verb",
        source="kaminia_a",
        etruscan_parallel="ar- (to make)",
        confidence=0.65,
        notes="Compare Etruscan ar- 'to make'",
    ),
    LemnianWord(
        form="tis",
        normalized="tis",
        meaning="?this",
        part_of_speech="demonstrative",
        source="kaminia_a",
        etruscan_parallel="ta/ita (this)",
        confidence=0.50,
        notes="Possibly demonstrative pronoun",
    ),
    LemnianWord(
        form="φoke",
        normalized="phoke",
        meaning="?Phocaean",
        part_of_speech="noun/adjective",
        source="kaminia_a",
        notes="May relate to Phocaea",
    ),

    # Kaminia stele - Face B
    LemnianWord(
        form="holaiez",
        normalized="holaiez",
        meaning="?",
        part_of_speech="noun",
        source="kaminia_b",
        notes="Variant of holaieś",
    ),
    LemnianWord(
        form="naphoth",
        normalized="naphoth",
        meaning="grandson?",
        part_of_speech="noun",
        source="kaminia_b",
        etruscan_parallel="nefts (grandson)",
        confidence=0.75,
        notes="Compare Etruscan nefts 'grandson'",
    ),
    LemnianWord(
        form="ziazi",
        normalized="ziazi",
        meaning="?performed/?made",
        part_of_speech="verb",
        source="kaminia_b",
        etruscan_parallel="zic-/zix- (to write)",
        confidence=0.60,
        notes="Possibly verbal form",
    ),
    LemnianWord(
        form="mav",
        normalized="mav",
        meaning="?",
        part_of_speech="unknown",
        source="kaminia_b",
        notes="Short form, uncertain meaning",
    ),
    LemnianWord(
        form="śialχveiś",
        normalized="sialchveis",
        meaning="60?",
        part_of_speech="numeral",
        source="kaminia_b",
        etruscan_parallel="*śealχ-",
        confidence=0.65,
        notes="Possibly numeral with genitive",
    ),
    LemnianWord(
        form="aviz",
        normalized="aviz",
        meaning="years",
        part_of_speech="noun",
        source="kaminia_b",
        etruscan_parallel="avil",
        confidence=0.90,
        morphology="plural?",
    ),
    LemnianWord(
        form="morail",
        normalized="morail",
        meaning="?dead/?tomb",
        part_of_speech="noun/adjective",
        source="kaminia_b",
        notes="Possibly related to death/burial",
    ),
    LemnianWord(
        form="rom",
        normalized="rom",
        meaning="?",
        part_of_speech="unknown",
        source="kaminia_b",
    ),
    LemnianWord(
        form="haralio",
        normalized="haralio",
        meaning="?",
        part_of_speech="noun/adjective",
        source="kaminia_b",
        morphology="-io suffix",
    ),
    LemnianWord(
        form="zeronai",
        normalized="zeronai",
        meaning="?pertaining to Hera?",
        part_of_speech="adjective",
        source="kaminia_b",
        notes="Possibly theophoric; -ai ending",
    ),
    LemnianWord(
        form="aker",
        normalized="aker",
        meaning="?make/?set up",
        part_of_speech="verb",
        source="kaminia_b",
        etruscan_parallel="acr-/?",
        confidence=0.40,
    ),
    LemnianWord(
        form="tavarsio",
        normalized="tavarsio",
        meaning="?judge/?leader",
        part_of_speech="noun",
        source="kaminia_b",
        notes="-io suffix, possibly title",
    ),
    LemnianWord(
        form="vanala",
        normalized="vanala",
        meaning="?",
        part_of_speech="noun",
        source="kaminia_b",
        morphology="-la suffix like Etruscan",
    ),
    LemnianWord(
        form="zeronaim",
        normalized="zeronaim",
        meaning="?",
        part_of_speech="unknown",
        source="kaminia_b",
        morphology="plural/collective -m?",
    ),

    # Hephaistia fragments
    LemnianWord(
        form="hulaie",
        normalized="hulaie",
        meaning="?",
        part_of_speech="noun",
        source="hephaistia",
        notes="Variant of holaie-",
    ),
    LemnianWord(
        form="šerom",
        normalized="sherom",
        meaning="?",
        part_of_speech="unknown",
        source="hephaistia",
    ),
]


class LemnianAnalyzer:
    """Analyzer for Lemnian-Etruscan comparisons."""

    def __init__(self):
        """Initialize with corpus."""
        self.corpus = LEMNIAN_CORPUS
        self._build_indices()

    def _build_indices(self) -> None:
        """Build lookup indices."""
        self.by_form = {w.normalized: w for w in self.corpus}
        self.by_parallel = {}
        for w in self.corpus:
            if w.etruscan_parallel:
                parallel = w.etruscan_parallel.replace("?", "").strip("*")
                if parallel:
                    self.by_parallel.setdefault(parallel, []).append(w)

    def find_parallel(self, etruscan_word: str) -> list[LemnianWord]:
        """Find Lemnian parallels for an Etruscan word.

        Args:
            etruscan_word: Etruscan word to check

        Returns:
            List of Lemnian words with potential parallels
        """
        word_lower = etruscan_word.lower()
        results = []

        # Direct parallel lookup
        if word_lower in self.by_parallel:
            results.extend(self.by_parallel[word_lower])

        # Check for root matches
        for lemnian_word in self.corpus:
            if lemnian_word in results:
                continue

            # Check if Etruscan word contains Lemnian root
            if len(word_lower) >= 3:
                root = word_lower[:3]
                if lemnian_word.normalized.startswith(root):
                    results.append(lemnian_word)

        return results

    def get_high_confidence_parallels(self, min_confidence: float = 0.70) -> list[LemnianWord]:
        """Get all Lemnian words with high-confidence Etruscan parallels.

        Args:
            min_confidence: Minimum confidence threshold

        Returns:
            List of LemnianWord objects
        """
        return [w for w in self.corpus if w.confidence >= min_confidence]

    def extract_shared_morphemes(self) -> dict[str, list[str]]:
        """Extract morphemes shared between Lemnian and Etruscan.

        Returns:
            Dict mapping morpheme to examples
        """
        shared = {
            # Suffixes
            "-al/-ale": ["phokiasiale (Lemn.) ~ -al genitive (Etr.)"],
            "-s/-ś": ["aviś (Lemn.) ~ -s nominative (Etr.)"],
            "-m": ["zeronaim (Lemn.) ~ -m plural? (Etr.)"],
            "-io": ["tavarsio (Lemn.) ~ -io suffix (Etr.)"],
            # Roots
            "avi-": ["aviś 'year' (Lemn.) ~ avil 'year' (Etr.)"],
            "mara-/maru-": ["maraśm (Lemn.) ~ maru 'magistrate' (Etr.)"],
            "nap-/nef-": ["naphoth (Lemn.) ~ nefts 'grandson' (Etr.)"],
            "siv-/sval-": ["sivai (Lemn.) ~ sval 'to live' (Etr.)"],
        }
        return shared

    def validate_etruscan_word(self, word: str) -> tuple[bool, float, str]:
        """Check if an Etruscan word has Lemnian support.

        Args:
            word: Word to validate

        Returns:
            Tuple of (has_parallel, confidence, notes)
        """
        parallels = self.find_parallel(word)

        if not parallels:
            return False, 0.0, "No Lemnian parallel found"

        best = max(parallels, key=lambda w: w.confidence)
        notes = f"Parallel: {best.form}"
        if best.meaning:
            notes += f" ({best.meaning})"

        return True, best.confidence, notes


def find_etruscan_parallels(etruscan_words: list[str]) -> list[tuple[str, LemnianWord, float]]:
    """Find Lemnian parallels for a list of Etruscan words.

    Args:
        etruscan_words: List of Etruscan words

    Returns:
        List of (etruscan_word, lemnian_word, confidence) tuples
    """
    analyzer = LemnianAnalyzer()
    results = []

    for word in etruscan_words:
        parallels = analyzer.find_parallel(word)
        for parallel in parallels:
            results.append((word, parallel, parallel.confidence))

    return sorted(results, key=lambda x: x[2], reverse=True)


def get_lemnian_roots() -> list[str]:
    """Get list of attested Lemnian roots for pattern matching.

    Returns:
        List of root forms (3+ characters)
    """
    roots = set()
    for word in LEMNIAN_CORPUS:
        if len(word.normalized) >= 3:
            # Extract potential root (first 3-4 chars)
            roots.add(word.normalized[:3])
            if len(word.normalized) >= 4:
                roots.add(word.normalized[:4])

    return sorted(roots)
