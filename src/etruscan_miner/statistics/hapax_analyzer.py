"""Hapax legomena analyzer for finding rare words.

Hapax legomena (words appearing only once) are prime candidates for
foreign vocabulary, as borrowed words often weren't widely adopted.
This module identifies hapax in Latin texts, especially those
appearing in Etruscan-related passages.
"""

import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import sqlite3
import json


@dataclass
class HapaxCandidate:
    """A hapax legomenon candidate for Etruscan discovery."""

    word: str
    word_normalized: str
    passage_text: str
    passage_id: Optional[int] = None
    work_title: Optional[str] = None
    author: Optional[str] = None
    etruscan_context: bool = False
    phonotactic_score: float = 0.0
    context_keywords: list[str] = field(default_factory=list)
    is_likely_etruscan: bool = False


class HapaxAnalyzer:
    """Analyze texts for hapax legomena in Etruscan contexts."""

    # Common Latin words to exclude (function words, common verbs, etc.)
    LATIN_STOPWORDS = {
        # Pronouns
        "qui", "quae", "quod", "quis", "quid", "hic", "haec", "hoc",
        "ille", "illa", "illud", "is", "ea", "id", "ipse", "ipsa", "ipsum",
        "ego", "tu", "nos", "vos", "se", "sui", "sibi",
        # Conjunctions & particles
        "et", "ac", "atque", "sed", "aut", "vel", "nec", "neque",
        "nam", "enim", "autem", "tamen", "igitur", "ergo", "itaque",
        "cum", "dum", "si", "nisi", "ut", "ne", "quod", "quia", "quam",
        # Prepositions
        "in", "ex", "de", "ab", "ad", "per", "pro", "cum", "sine",
        "inter", "ante", "post", "sub", "super", "trans", "contra",
        # Common verbs
        "est", "sunt", "erat", "esse", "fuit", "fuisse",
        "habet", "habere", "habuit", "dicit", "dicere", "dixit",
        "facit", "facere", "fecit", "fieri", "fit",
        # Common nouns/adjectives
        "res", "rei", "causa", "modo", "parte", "loco",
        "magnus", "magna", "magnum", "bonus", "bona", "bonum",
        "omnis", "omne", "multus", "multa", "multum",
        # Numbers
        "unus", "duo", "tres", "primus", "secundus", "tertius",
        # Other common
        "non", "iam", "nunc", "tunc", "sic", "ita", "tam", "quoque",
        "etiam", "adhuc", "semper", "numquam", "saepe",
    }

    # Etruscan context keywords
    ETRUSCAN_KEYWORDS = {
        "tuscus", "tusci", "tuscorum", "tusco", "tuscis",
        "etruscus", "etrusci", "etruscorum", "etrusco", "etruscis",
        "etrusca", "etruria", "etruriae", "tyrrhenus", "tyrrheni",
        "tarquinius", "tarquinii", "clusium", "veii", "volsinii",
        "caere", "arretium", "perusia", "cortona", "vulci",
        "haruspex", "haruspices", "haruspicina", "disciplina",
        "lucumo", "lucumones", "lauchme",
    }

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize analyzer.

        Args:
            db_path: Path to SQLite database for word frequency lookup
        """
        self.db_path = db_path
        self.word_frequencies: Counter = Counter()
        self.corpus_size = 0

    def build_frequency_index(self, texts: list[str]) -> None:
        """Build word frequency index from corpus texts.

        Args:
            texts: List of text strings to analyze
        """
        for text in texts:
            words = self._tokenize(text)
            self.word_frequencies.update(words)
            self.corpus_size += len(words)

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize text into normalized words."""
        # Remove punctuation, lowercase
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = text.split()
        # Filter short words and numbers
        words = [w for w in words if len(w) >= 3 and not w.isdigit()]
        return words

    def _normalize_word(self, word: str) -> str:
        """Normalize a word for comparison."""
        # Lowercase, remove diacritics (simplified)
        word = word.lower()
        # Handle common Latin spelling variants
        word = word.replace("v", "u").replace("j", "i")
        return word

    def _has_etruscan_context(self, text: str) -> tuple[bool, list[str]]:
        """Check if text mentions Etruscan-related terms.

        Returns:
            Tuple of (has_context, list of keywords found)
        """
        text_lower = text.lower()
        found = [kw for kw in self.ETRUSCAN_KEYWORDS if kw in text_lower]
        return len(found) > 0, found

    def find_hapax(self, text: str, context_window: int = 200) -> list[HapaxCandidate]:
        """Find hapax legomena in a text.

        Args:
            text: Text to analyze
            context_window: Characters of context to extract around hapax

        Returns:
            List of HapaxCandidate objects
        """
        words = self._tokenize(text)
        local_freq = Counter(words)

        candidates = []

        for word, count in local_freq.items():
            # Skip common Latin words
            if word in self.LATIN_STOPWORDS:
                continue

            # Check if hapax in local text
            if count > 1:
                continue

            # Check global frequency if available
            if self.word_frequencies:
                global_count = self.word_frequencies.get(word, 0)
                if global_count > 2:  # Allow some tolerance
                    continue

            # Find the word in original text to extract context
            pattern = re.compile(rf'\b{re.escape(word)}\b', re.IGNORECASE)
            match = pattern.search(text)

            if match:
                start = max(0, match.start() - context_window)
                end = min(len(text), match.end() + context_window)
                context = text[start:end]

                has_etruscan, keywords = self._has_etruscan_context(context)

                candidates.append(HapaxCandidate(
                    word=match.group(0),  # Original case
                    word_normalized=self._normalize_word(word),
                    passage_text=context,
                    etruscan_context=has_etruscan,
                    context_keywords=keywords,
                ))

        return candidates

    def score_hapax_candidate(self, candidate: HapaxCandidate) -> float:
        """Score a hapax candidate for Etruscan likelihood.

        Args:
            candidate: HapaxCandidate to score

        Returns:
            Score between 0 and 1
        """
        from ..validation.linguistic import LinguisticValidator

        score = 0.3  # Base score for being hapax

        # Etruscan context boost
        if candidate.etruscan_context:
            score += 0.25
            # Additional boost for multiple keywords
            score += min(0.15, len(candidate.context_keywords) * 0.05)

        # Phonotactic scoring
        validator = LinguisticValidator()
        result = validator.validate(candidate.word)
        candidate.phonotactic_score = result.score

        if result.plausibility == "high":
            score += 0.25
        elif result.plausibility == "medium":
            score += 0.15
        elif result.plausibility == "low":
            score += 0.05

        # Penalize if looks like obvious Latin
        if self._looks_like_latin(candidate.word):
            score -= 0.2

        return max(0.0, min(1.0, score))

    def _looks_like_latin(self, word: str) -> bool:
        """Check if word has obvious Latin morphology."""
        latin_endings = [
            "orum", "arum", "ibus", "orum", "onis", "tionis",
            "mentum", "tudo", "itas", "atio", "itio", "arius"
        ]
        return any(word.lower().endswith(e) for e in latin_endings)

    def filter_etruscan_candidates(
        self,
        candidates: list[HapaxCandidate],
        min_score: float = 0.5
    ) -> list[HapaxCandidate]:
        """Filter hapax candidates to likely Etruscan terms.

        Args:
            candidates: List of HapaxCandidate objects
            min_score: Minimum score threshold

        Returns:
            Filtered list of likely Etruscan candidates
        """
        scored = []

        for candidate in candidates:
            score = self.score_hapax_candidate(candidate)
            if score >= min_score:
                candidate.is_likely_etruscan = True
                scored.append((score, candidate))

        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)

        return [c for _, c in scored]


def analyze_text_for_hapax(
    text: str,
    context_window: int = 200
) -> list[HapaxCandidate]:
    """Convenience function to analyze text for hapax legomena.

    Args:
        text: Text to analyze
        context_window: Context characters around each hapax

    Returns:
        List of HapaxCandidate objects
    """
    analyzer = HapaxAnalyzer()
    return analyzer.find_hapax(text, context_window)


def get_hapax_in_etruscan_context(
    text: str,
    min_score: float = 0.5
) -> list[HapaxCandidate]:
    """Find hapax legomena specifically in Etruscan contexts.

    Args:
        text: Text to analyze
        min_score: Minimum score threshold

    Returns:
        List of filtered HapaxCandidate objects
    """
    analyzer = HapaxAnalyzer()
    candidates = analyzer.find_hapax(text)
    return analyzer.filter_etruscan_candidates(candidates, min_score)
