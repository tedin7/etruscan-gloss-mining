"""Greek substrate detector for Tyrrhenian words.

The Tyrsenian language family (Etruscan, Lemnian, possibly Raetic)
may have contributed to the pre-Greek substrate in the Aegean.
This module identifies Greek words that may have Tyrrhenian origins,
particularly those marked as "barbarous" or of unknown etymology
in ancient lexica like Hesychius.
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class SubstrateCandidate:
    """A Greek word that may have Tyrrhenian/pre-Greek origin."""

    greek_word: str
    transliteration: str
    meaning: str
    source: str  # e.g., "Hesychius", "Homer", "Herodotus"
    evidence: list[str]
    confidence: float
    etruscan_parallel: Optional[str] = None
    lemnian_parallel: Optional[str] = None
    notes: str = ""


# Known or suspected Tyrrhenian substrate in Greek
TYRRHENIAN_SUBSTRATE = [
    SubstrateCandidate(
        greek_word="τύραννος",
        transliteration="tyrannos",
        meaning="absolute ruler",
        source="widespread",
        evidence=["Non-IE etymology", "Possibly from Tyrrhenian *turan 'lord'", "Ancient controversy over origin"],
        confidence=0.70,
        etruscan_parallel="turan (goddess)",
        notes="Much debated; may be Lydian rather than Etruscan",
    ),
    SubstrateCandidate(
        greek_word="θάλασσα",
        transliteration="thalassa",
        meaning="sea",
        source="widespread",
        evidence=["Pre-Greek substrate word", "Non-IE etymology", "-ss- suffix typical of substrate"],
        confidence=0.50,
        notes="Pre-Greek but not specifically Tyrrhenian",
    ),
    SubstrateCandidate(
        greek_word="λάρναξ",
        transliteration="larnax",
        meaning="chest, coffin",
        source="Homer",
        evidence=["Non-IE etymology", "Possibly related to Etruscan lar-?", "Funeral context"],
        confidence=0.45,
        etruscan_parallel="lar-?",
    ),
    SubstrateCandidate(
        greek_word="κύμβη",
        transliteration="kymbē",
        meaning="bowl, cup",
        source="widespread",
        evidence=["Non-IE etymology", "Possibly Mediterranean wanderwort"],
        confidence=0.40,
        notes="May be pre-Greek but unclear if Tyrrhenian",
    ),
    SubstrateCandidate(
        greek_word="πύργος",
        transliteration="pyrgos",
        meaning="tower",
        source="widespread",
        evidence=["Pre-Greek substrate", "Non-IE etymology"],
        confidence=0.45,
        notes="Pre-Greek substrate but not necessarily Tyrrhenian",
    ),
    SubstrateCandidate(
        greek_word="ἀσάμινθος",
        transliteration="asáminthos",
        meaning="bathtub",
        source="Homer",
        evidence=["Pre-Greek substrate", "-nth- suffix", "Mycenaean attestation"],
        confidence=0.35,
        notes="Pre-Greek substrate; -nth- suffix",
    ),
    SubstrateCandidate(
        greek_word="κιθάρα",
        transliteration="kithara",
        meaning="lyre",
        source="widespread",
        evidence=["Non-IE etymology", "Musical instrument wanderwort"],
        confidence=0.40,
        notes="Cultural borrowing, possibly Mediterranean",
    ),

    # From Hesychius marked as Tyrrhenian
    SubstrateCandidate(
        greek_word="αἰσοι",
        transliteration="aisoi",
        meaning="gods (among Tyrrhenians)",
        source="Hesychius",
        evidence=["Explicitly marked Tyrrhenian", "Compare Etruscan ais 'god'"],
        confidence=0.95,
        etruscan_parallel="ais/aisar (god/gods)",
        notes="Direct gloss in Hesychius",
    ),
    SubstrateCandidate(
        greek_word="ἀρίμοι",
        transliteration="arimoi",
        meaning="apes (Tyrrhenian)",
        source="Hesychius",
        evidence=["Marked as Tyrrhenian in Hesychius"],
        confidence=0.85,
        notes="Hesychius: 'apes, among Tyrrhenians'",
    ),
    SubstrateCandidate(
        greek_word="φάλαρα",
        transliteration="phalara",
        meaning="metal discs on helmet",
        source="Hesychius",
        evidence=["Non-IE etymology", "Military/decorative context"],
        confidence=0.50,
        notes="Possible Etruscan origin",
    ),
    SubstrateCandidate(
        greek_word="γάλεος",
        transliteration="galeos",
        meaning="shark, weasel",
        source="Aristotle",
        evidence=["Non-IE etymology", "Possibly Mediterranean substrate"],
        confidence=0.35,
    ),
    SubstrateCandidate(
        greek_word="λέρνη",
        transliteration="lernē",
        meaning="Lerna (place name)",
        source="mythology",
        evidence=["Pre-Greek toponym", "Non-IE structure"],
        confidence=0.40,
        notes="Pre-Greek place name; possibly Tyrrhenian?",
    ),
    SubstrateCandidate(
        greek_word="μάνθη",
        transliteration="manthē",
        meaning="basket (Tyrrhenian)",
        source="Hesychius",
        evidence=["Marked as Tyrrhenian", "Etruscan connection possible"],
        confidence=0.80,
        etruscan_parallel="?",
    ),
]


class GreekSubstrateDetector:
    """Detector for Tyrrhenian substrate in Greek."""

    def __init__(self):
        """Initialize detector."""
        self.substrate_words = TYRRHENIAN_SUBSTRATE
        self._build_indices()

    def _build_indices(self) -> None:
        """Build lookup indices."""
        self.by_translit = {w.transliteration.lower(): w for w in self.substrate_words}
        self.by_greek = {w.greek_word: w for w in self.substrate_words}

    def is_known_substrate(self, word: str) -> Optional[SubstrateCandidate]:
        """Check if word is known Tyrrhenian substrate.

        Args:
            word: Greek word (transliteration or Greek script)

        Returns:
            SubstrateCandidate if known, None otherwise
        """
        # Check transliteration
        result = self.by_translit.get(word.lower())
        if result:
            return result

        # Check Greek
        return self.by_greek.get(word)

    def get_hesychius_glosses(self) -> list[SubstrateCandidate]:
        """Get all words marked as Tyrrhenian in Hesychius.

        Returns:
            List of SubstrateCandidate from Hesychius
        """
        return [w for w in self.substrate_words if w.source == "Hesychius"]

    def get_high_confidence(self, min_confidence: float = 0.70) -> list[SubstrateCandidate]:
        """Get high-confidence Tyrrhenian substrate words.

        Args:
            min_confidence: Minimum confidence threshold

        Returns:
            List of SubstrateCandidate objects
        """
        return [w for w in self.substrate_words if w.confidence >= min_confidence]

    def analyze_greek_word(self, word: str, meaning: str = "") -> SubstrateCandidate:
        """Analyze a Greek word for Tyrrhenian substrate features.

        Args:
            word: Greek word (transliteration)
            meaning: Word meaning if known

        Returns:
            SubstrateCandidate with analysis
        """
        # Check if known
        known = self.is_known_substrate(word)
        if known:
            return known

        # Analyze unknown word
        evidence = []
        confidence = 0.2

        word_lower = word.lower()

        # Check for pre-Greek substrate markers
        if self._has_substrate_phonology(word_lower):
            evidence.append("Pre-Greek phonological features")
            confidence += 0.15

        # Check for non-IE structure
        if self._has_non_ie_structure(word_lower):
            evidence.append("Non-Indo-European structure")
            confidence += 0.10

        # Check for Etruscan-like features
        if self._has_etruscan_features(word_lower):
            evidence.append("Etruscan-like phonology")
            confidence += 0.15

        return SubstrateCandidate(
            greek_word=word,
            transliteration=word_lower,
            meaning=meaning or "?",
            source="analysis",
            evidence=evidence,
            confidence=min(confidence, 0.75),
            notes="Automatically analyzed",
        )

    def _has_substrate_phonology(self, word: str) -> bool:
        """Check for pre-Greek substrate phonological markers."""
        # -nth-, -ss-, -mn- clusters typical of pre-Greek
        substrate_patterns = ["nth", "ss", "mn", "gn", "kn", "pn"]
        return any(p in word for p in substrate_patterns)

    def _has_non_ie_structure(self, word: str) -> bool:
        """Check for non-Indo-European word structure."""
        # Reduplicated consonants, unusual clusters
        if len(word) >= 4:
            # Check for initial clusters unusual in IE
            if word[:2] in ["pt", "kt", "ps", "ks", "mn", "gn"]:
                return True
        return False

    def _has_etruscan_features(self, word: str) -> bool:
        """Check for specifically Etruscan-like features."""
        # No voiced stops, typical Etruscan endings
        if not any(c in word for c in "bdg"):
            if any(word.endswith(e) for e in ["na", "al", "as", "is"]):
                return True
        return False

    def find_etruscan_parallel(self, word: str) -> Optional[str]:
        """Try to find Etruscan parallel for a Greek substrate word.

        Args:
            word: Greek word

        Returns:
            Etruscan parallel if found
        """
        known = self.is_known_substrate(word)
        if known and known.etruscan_parallel:
            return known.etruscan_parallel
        return None


def detect_tyrrhenian_substrate(greek_words: list[str]) -> list[SubstrateCandidate]:
    """Detect Tyrrhenian substrate words in a list of Greek words.

    Args:
        greek_words: List of Greek words (transliterated)

    Returns:
        List of SubstrateCandidate objects
    """
    detector = GreekSubstrateDetector()
    results = []

    for word in greek_words:
        candidate = detector.analyze_greek_word(word)
        if candidate.confidence >= 0.35:
            results.append(candidate)

    return sorted(results, key=lambda x: x.confidence, reverse=True)
