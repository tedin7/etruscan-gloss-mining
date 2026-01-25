"""Foreign word Named Entity Recognition.

This module detects foreign (non-Latin/non-Greek) words embedded
in ancient texts. Ancient authors often marked foreign words with
contextual cues, or the words stand out phonologically.

Uses:
- Phonotactic analysis (Etruscan phonology differs from Latin)
- Context markers ("vocant", "dicunt", "appellant")
- Morphological anomalies (non-Latin endings)
- Integration with existing word classifier
"""

import re
from dataclasses import dataclass, field
from typing import Optional
from collections import Counter


@dataclass
class ForeignWordCandidate:
    """A candidate foreign word detected in text."""

    word: str
    position: int
    context: str
    origin_probability: dict[str, float] = field(default_factory=dict)
    detection_method: str = ""  # 'phonotactic', 'context', 'morphological'
    confidence: float = 0.0
    notes: str = ""


class ForeignWordNER:
    """Named Entity Recognizer for foreign words in Latin/Greek texts."""

    def __init__(self):
        """Initialize NER."""
        self._init_patterns()
        self._init_phonotactics()

    def _init_patterns(self) -> None:
        """Initialize context marker patterns."""
        # Latin markers for foreign words
        self.latin_foreign_markers = [
            r"\b(\w+)\s+(?:quod|quem)\s+(?:vocant|dicunt|appellant)",
            r"(?:vocant|dicunt)\s+(\w+)",
            r"lingua\s+\w+\s+(\w+)",
            r"(?:id|hoc)\s+est\s+(\w+)",
            r"(?:graece|latine|tuscice)\s+(\w+)",
            r"barbarum\s+vocabulum\s+(\w+)",
        ]

        # Greek markers for foreign words
        self.greek_foreign_markers = [
            r"(?:καλοῦσι|λέγουσι)\s+(\w+)",
            r"τῇ\s+\w+\s+φωνῇ\s+(\w+)",
            r"βάρβαροι\s+(\w+)",
        ]

        # Compile patterns
        self.latin_patterns = [re.compile(p, re.IGNORECASE) for p in self.latin_foreign_markers]
        self.greek_patterns = [re.compile(p) for p in self.greek_foreign_markers]

    def _init_phonotactics(self) -> None:
        """Initialize phonotactic rules for different languages."""
        # Latin phonotactic characteristics
        self.latin_features = {
            "voiced_stops": True,  # b, d, g allowed
            "qu_cluster": True,
            "common_endings": ["us", "um", "is", "it", "nt", "re", "ae", "orum"],
        }

        # Etruscan phonotactic characteristics
        self.etruscan_features = {
            "voiced_stops": False,  # No b, d, g
            "aspirates": True,  # ph, th, ch common
            "common_endings": ["a", "i", "e", "u", "al", "na", "s"],
            "typical_clusters": ["sp", "st", "sc", "pr", "tr", "cr"],
        }

        # Greek phonotactic characteristics
        self.greek_features = {
            "voiced_stops": True,
            "aspirates": True,
            "common_endings": ["os", "on", "es", "is", "ou"],
        }

    def detect_in_text(self, text: str, source_language: str = "latin") -> list[ForeignWordCandidate]:
        """Detect foreign words in a text.

        Args:
            text: Text to analyze
            source_language: Language of the text ('latin' or 'greek')

        Returns:
            List of ForeignWordCandidate objects
        """
        candidates = []

        # Method 1: Context markers
        candidates.extend(self._detect_by_context(text, source_language))

        # Method 2: Phonotactic anomalies
        candidates.extend(self._detect_by_phonotactics(text, source_language))

        # Method 3: Morphological anomalies
        candidates.extend(self._detect_by_morphology(text, source_language))

        # Merge duplicates and boost confidence
        return self._merge_candidates(candidates)

    def _detect_by_context(self, text: str, source_language: str) -> list[ForeignWordCandidate]:
        """Detect foreign words by context markers.

        Args:
            text: Text to analyze
            source_language: Source language

        Returns:
            List of candidates
        """
        candidates = []
        patterns = self.latin_patterns if source_language == "latin" else self.greek_patterns

        for pattern in patterns:
            for match in pattern.finditer(text):
                word = match.group(1) if match.groups() else match.group(0)

                # Get context
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end]

                candidates.append(ForeignWordCandidate(
                    word=word,
                    position=match.start(),
                    context=context,
                    detection_method="context",
                    confidence=0.70,
                    notes=f"Found with pattern: {pattern.pattern[:30]}..."
                ))

        return candidates

    def _detect_by_phonotactics(self, text: str, source_language: str) -> list[ForeignWordCandidate]:
        """Detect foreign words by phonotactic analysis.

        Args:
            text: Text to analyze
            source_language: Source language

        Returns:
            List of candidates
        """
        candidates = []

        # Extract words
        words = re.findall(r'\b([a-zA-Z]{3,15})\b', text)
        word_positions = {m.group(1): m.start() for m in re.finditer(r'\b([a-zA-Z]{3,15})\b', text)}

        for word in set(words):
            score = self._score_phonotactic_foreignness(word, source_language)

            if score >= 0.5:
                position = word_positions.get(word, 0)
                start = max(0, position - 30)
                end = min(len(text), position + len(word) + 30)

                candidates.append(ForeignWordCandidate(
                    word=word,
                    position=position,
                    context=text[start:end],
                    origin_probability={"etruscan": score, "greek": 1 - score if source_language == "latin" else 0},
                    detection_method="phonotactic",
                    confidence=score,
                    notes="Phonotactically unusual for source language"
                ))

        return candidates

    def _score_phonotactic_foreignness(self, word: str, source_language: str) -> float:
        """Score how foreign a word seems phonotactically.

        Args:
            word: Word to analyze
            source_language: Expected source language

        Returns:
            Score 0-1 (higher = more foreign)
        """
        word_lower = word.lower()
        score = 0.0

        if source_language == "latin":
            # Check for features unusual in Latin but common in Etruscan

            # No voiced stops is very Etruscan
            if not any(c in word_lower for c in "bdg"):
                score += 0.2

            # Etruscan-type endings
            etruscan_endings = ["na", "al", "el", "ul", "ce", "χe", "as"]
            if any(word_lower.endswith(e) for e in etruscan_endings):
                score += 0.2

            # Aspirate clusters (ph, th, ch)
            if any(cluster in word_lower for cluster in ["ph", "th", "ch"]):
                score += 0.1

            # Lacks Latin case endings
            latin_endings = ["us", "um", "is", "ibus", "orum", "arum"]
            if not any(word_lower.endswith(e) for e in latin_endings):
                score += 0.15

            # Unusual for Latin initial clusters
            if word_lower[:2] in ["sp", "st", "sc"] and len(word_lower) <= 6:
                score += 0.1

        return min(score, 1.0)

    def _detect_by_morphology(self, text: str, source_language: str) -> list[ForeignWordCandidate]:
        """Detect foreign words by morphological anomalies.

        Args:
            text: Text to analyze
            source_language: Source language

        Returns:
            List of candidates
        """
        candidates = []

        # Look for words that don't decline/conjugate like Latin
        # This is simplified - full implementation would use morphological parser

        # Pattern: repeated word with same form in different cases
        # (suggests uninflected foreign word)
        words = re.findall(r'\b([a-zA-Z]{3,15})\b', text.lower())
        word_counts = Counter(words)

        # Find words that appear multiple times unchanged
        # (unusual for Latin which heavily inflects)
        for word, count in word_counts.items():
            if count >= 3 and len(word) >= 4:
                # Check if it looks uninflected
                if not self._looks_inflected(word):
                    positions = [m.start() for m in re.finditer(rf'\b{word}\b', text.lower())]
                    if positions:
                        candidates.append(ForeignWordCandidate(
                            word=word,
                            position=positions[0],
                            context=f"Appears {count} times uninflected",
                            detection_method="morphological",
                            confidence=0.45,
                            notes="Appears uninflected, may be foreign"
                        ))

        return candidates

    def _looks_inflected(self, word: str) -> bool:
        """Check if word looks like it has Latin inflection.

        Args:
            word: Word to check

        Returns:
            True if word appears to be inflected
        """
        latin_inflections = [
            "orum", "arum", "ibus", "erum", "uum",  # Genitive/dative plurals
            "orum", "ium", "uum",  # Genitive plurals
            "ntur", "mur", "tur",  # Verb endings
        ]
        return any(word.endswith(i) for i in latin_inflections)

    def _merge_candidates(self, candidates: list[ForeignWordCandidate]) -> list[ForeignWordCandidate]:
        """Merge duplicate candidates and boost confidence.

        Args:
            candidates: List of candidates

        Returns:
            Merged and deduplicated list
        """
        by_word: dict[str, list[ForeignWordCandidate]] = {}

        for c in candidates:
            word_lower = c.word.lower()
            if word_lower not in by_word:
                by_word[word_lower] = []
            by_word[word_lower].append(c)

        merged = []
        for word, word_candidates in by_word.items():
            if len(word_candidates) == 1:
                merged.append(word_candidates[0])
            else:
                # Merge: take highest confidence, combine methods
                best = max(word_candidates, key=lambda x: x.confidence)
                methods = list(set(c.detection_method for c in word_candidates))

                # Boost confidence for multiple detection methods
                boost = 0.1 * (len(methods) - 1)

                merged.append(ForeignWordCandidate(
                    word=best.word,
                    position=best.position,
                    context=best.context,
                    origin_probability=best.origin_probability,
                    detection_method=", ".join(methods),
                    confidence=min(best.confidence + boost, 0.95),
                    notes=f"Detected by multiple methods: {methods}"
                ))

        return sorted(merged, key=lambda x: x.confidence, reverse=True)


def detect_foreign_words(text: str, source_language: str = "latin") -> list[ForeignWordCandidate]:
    """Detect foreign words in a text.

    Args:
        text: Text to analyze
        source_language: Language of the text

    Returns:
        List of ForeignWordCandidate objects
    """
    ner = ForeignWordNER()
    return ner.detect_in_text(text, source_language)


def classify_word_origin(word: str, context: str = "") -> dict[str, float]:
    """Classify the probable origin of a word.

    Args:
        word: Word to classify
        context: Surrounding context

    Returns:
        Dict mapping language to probability
    """
    ner = ForeignWordNER()
    score = ner._score_phonotactic_foreignness(word, "latin")

    return {
        "latin": max(0, 1 - score - 0.2),
        "etruscan": score,
        "greek": max(0, 0.3 - score * 0.5),
        "unknown": 0.1,
    }
