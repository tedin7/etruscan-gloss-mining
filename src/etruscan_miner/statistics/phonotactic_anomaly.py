"""Phonotactic anomaly detector for finding non-Latin words.

Identifies words in Latin texts that violate Latin phonotactics
but conform to Etruscan phonotactic patterns:
- Absence of voiced stops (b, d, g)
- Presence of aspirates (ph, th, ch)
- Etruscan-typical consonant clusters
- Etruscan-typical word endings
"""

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AnomalyResult:
    """Result of phonotactic anomaly detection."""

    word: str
    anomaly_score: float  # 0-1, higher = more anomalous for Latin
    etruscan_score: float  # 0-1, higher = more Etruscan-like
    combined_score: float  # Product of the two
    latin_violations: list[str] = field(default_factory=list)
    etruscan_features: list[str] = field(default_factory=list)
    is_candidate: bool = False


class PhonotacticAnomalyDetector:
    """Detect phonotactically anomalous words in Latin texts."""

    # Features that violate typical Latin patterns
    LATIN_UNUSUAL = {
        # Initial clusters rare in Latin
        "initial_cluster": [
            "θ", "χ", "φ",  # Greek/Etruscan aspirates
            "zn", "zl", "zr",  # z-clusters
            "pn", "cn", "gn",  # nasal clusters at start
        ],
        # Vowel patterns unusual for Latin
        "vowel_pattern": [
            "ao", "eo", "uo",  # hiatus rare in Latin
            "ui", "iu",  # rare diphthongs
        ],
        # Ending patterns rare in Latin
        "ending": [
            "θ", "χ", "φ",
            "rn", "ln", "mn",  # consonant clusters at end
        ],
    }

    # Features typical of Etruscan
    ETRUSCAN_TYPICAL = {
        "no_voiced_stops": True,  # b, d, g absent
        "aspirates": ["th", "ch", "ph", "θ", "χ", "φ"],
        "typical_endings": [
            "a", "i", "e", "u",
            "al", "el", "il", "ul",
            "na", "ne", "ni",
            "s", "as", "es", "is",
            "ce", "χe", "che",
            "r", "ar", "er",
        ],
        "typical_clusters": [
            "pr", "tr", "cr", "kr",
            "sp", "st", "sc", "sk",
            "mn", "ln", "rn",
            "nt", "nc", "ns",
            "χv", "chv", "cv",
            "θn", "thn",
        ],
    }

    # Latin-typical patterns (for negative scoring)
    LATIN_TYPICAL = {
        "voiced_stops": ["b", "d", "g"],
        "typical_endings": [
            "us", "um", "os", "is", "es", "as",
            "orum", "arum", "ibus", "ibus",
            "nt", "tur", "ntur",
            "tio", "sio", "tia", "tius",
        ],
        "typical_clusters": [
            "qu", "gu",  # qu-cluster
            "ct", "pt", "gn",
            "nct", "mpt",
        ],
    }

    def __init__(self):
        """Initialize the detector."""
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns for efficiency."""
        self.voiced_stop_pattern = re.compile(r'[bdg]', re.IGNORECASE)
        self.aspirate_pattern = re.compile(r'(th|ch|ph|θ|χ|φ)', re.IGNORECASE)
        self.latin_ending_pattern = re.compile(
            r'(orum|arum|ibus|orum|orum|onis|tio|sio|nt|tur|ntur)$',
            re.IGNORECASE
        )

    def detect_anomaly(self, word: str) -> AnomalyResult:
        """Detect phonotactic anomalies in a word.

        Args:
            word: Word to analyze

        Returns:
            AnomalyResult with scores and features
        """
        latin_violations = []
        etruscan_features = []

        word_lower = word.lower()

        # === Latin anomaly detection ===

        # Check for absence of voiced stops (unusual for Latin if word is long)
        has_voiced = bool(self.voiced_stop_pattern.search(word))
        if not has_voiced and len(word) >= 5:
            latin_violations.append("no_voiced_stops")

        # Check for aspirates (uncommon in native Latin)
        if self.aspirate_pattern.search(word):
            latin_violations.append("has_aspirates")

        # Check for unusual Latin initial clusters
        for cluster in self.LATIN_UNUSUAL["initial_cluster"]:
            if word_lower.startswith(cluster):
                latin_violations.append(f"unusual_initial_{cluster}")

        # Check for hiatus
        for pattern in self.LATIN_UNUSUAL["vowel_pattern"]:
            if pattern in word_lower:
                latin_violations.append(f"hiatus_{pattern}")

        # Check if ending is atypical for Latin
        if not self.latin_ending_pattern.search(word):
            # Not a typical Latin ending
            if len(word) >= 4:
                latin_violations.append("atypical_ending")

        # === Etruscan feature detection ===

        # No voiced stops is positive for Etruscan
        if not has_voiced:
            etruscan_features.append("no_voiced_stops")

        # Aspirates are positive for Etruscan
        if self.aspirate_pattern.search(word):
            etruscan_features.append("has_aspirates")

        # Check for typical Etruscan endings
        for ending in self.ETRUSCAN_TYPICAL["typical_endings"]:
            if word_lower.endswith(ending):
                etruscan_features.append(f"etruscan_ending_{ending}")
                break

        # Check for typical Etruscan clusters
        for cluster in self.ETRUSCAN_TYPICAL["typical_clusters"]:
            if cluster in word_lower:
                etruscan_features.append(f"etruscan_cluster_{cluster}")

        # === Negative Latin features ===

        # Penalize clear Latin features
        latin_penalties = 0
        for stop in self.LATIN_TYPICAL["voiced_stops"]:
            if stop in word_lower:
                latin_penalties += 1

        if "qu" in word_lower:
            latin_penalties += 2  # Very Latin feature

        if self.latin_ending_pattern.search(word):
            latin_penalties += 1

        # === Score calculation ===

        # Anomaly score (how unusual for Latin)
        anomaly_score = min(1.0, len(latin_violations) * 0.2)

        # Etruscan score (how Etruscan-like)
        etruscan_score = min(1.0, len(etruscan_features) * 0.25)

        # Apply Latin penalties
        etruscan_score = max(0.0, etruscan_score - latin_penalties * 0.15)

        # Combined score
        combined_score = (anomaly_score + etruscan_score) / 2

        is_candidate = combined_score >= 0.4 and len(etruscan_features) >= 1

        return AnomalyResult(
            word=word,
            anomaly_score=anomaly_score,
            etruscan_score=etruscan_score,
            combined_score=combined_score,
            latin_violations=latin_violations,
            etruscan_features=etruscan_features,
            is_candidate=is_candidate,
        )

    def detect_anomalies_in_text(
        self,
        text: str,
        min_word_length: int = 4,
        min_score: float = 0.4
    ) -> list[AnomalyResult]:
        """Find all anomalous words in a text.

        Args:
            text: Text to analyze
            min_word_length: Minimum word length to consider
            min_score: Minimum combined score threshold

        Returns:
            List of AnomalyResult objects for anomalous words
        """
        # Tokenize
        words = re.findall(r'\b[a-zA-ZθχφΘΧΦ]+\b', text)
        words = [w for w in words if len(w) >= min_word_length]

        # Deduplicate
        unique_words = list(set(words))

        results = []
        for word in unique_words:
            result = self.detect_anomaly(word)
            if result.combined_score >= min_score:
                results.append(result)

        # Sort by combined score descending
        results.sort(key=lambda r: r.combined_score, reverse=True)

        return results


def detect_anomalies_in_text(
    text: str,
    min_word_length: int = 4,
    min_score: float = 0.4
) -> list[AnomalyResult]:
    """Convenience function to detect phonotactic anomalies.

    Args:
        text: Text to analyze
        min_word_length: Minimum word length
        min_score: Minimum score threshold

    Returns:
        List of AnomalyResult objects
    """
    detector = PhonotacticAnomalyDetector()
    return detector.detect_anomalies_in_text(text, min_word_length, min_score)


def score_word_anomaly(word: str) -> AnomalyResult:
    """Score a single word for phonotactic anomaly.

    Args:
        word: Word to analyze

    Returns:
        AnomalyResult with scores
    """
    detector = PhonotacticAnomalyDetector()
    return detector.detect_anomaly(word)
