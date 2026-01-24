"""Cross-reference validation against known Etruscan vocabulary."""

import unicodedata
from dataclasses import dataclass
from typing import Optional

from ..db.models import EtruscanWord, VerifiedGloss
from ..db.repository import Repository


@dataclass
class CrossRefResult:
    """Result of cross-reference check."""

    word: str
    normalized: str
    score: float
    match_type: str  # 'exact', 'partial', 'root', 'similar', 'none'
    matched_word: Optional[str] = None
    matched_meaning: Optional[str] = None
    details: Optional[str] = None


class CrossReferenceChecker:
    """Check candidate words against known Etruscan vocabulary."""

    def __init__(self, repo: Repository):
        """Initialize with database repository.

        Args:
            repo: Database repository with vocabulary
        """
        self.repo = repo
        self._vocab_cache: Optional[dict[str, EtruscanWord]] = None
        self._gloss_cache: Optional[dict[str, VerifiedGloss]] = None

    def _load_vocabulary(self):
        """Load vocabulary into memory for fast lookup."""
        if self._vocab_cache is None:
            vocab = self.repo.get_all_vocabulary()
            self._vocab_cache = {w.word_normalized: w for w in vocab}

    def _load_glosses(self):
        """Load verified glosses into memory."""
        if self._gloss_cache is None:
            glosses = self.repo.get_all_verified_glosses()
            self._gloss_cache = {g.etruscan_normalized: g for g in glosses}

    def _normalize(self, word: str) -> str:
        """Normalize a word for comparison."""
        # Lowercase
        word = word.lower()
        # Remove diacritics
        normalized = unicodedata.normalize("NFD", word)
        word = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
        # Remove common Latin endings that might be added
        for ending in ["um", "us", "em", "is", "os", "ae", "am"]:
            if word.endswith(ending) and len(word) > len(ending) + 2:
                word = word[:-len(ending)]
                break
        return word

    def _similarity_score(self, word1: str, word2: str) -> float:
        """Calculate similarity between two words.

        Uses a simple character-based metric.
        """
        if word1 == word2:
            return 1.0

        # Length-adjusted Levenshtein-like scoring
        len1, len2 = len(word1), len(word2)
        if len1 == 0 or len2 == 0:
            return 0.0

        # Count matching characters
        matches = sum(1 for c1, c2 in zip(word1, word2) if c1 == c2)

        # Bonus for common prefix
        prefix_len = 0
        for c1, c2 in zip(word1, word2):
            if c1 == c2:
                prefix_len += 1
            else:
                break

        # Calculate score
        base_score = matches / max(len1, len2)
        prefix_bonus = prefix_len / max(len1, len2) * 0.3

        return min(1.0, base_score + prefix_bonus)

    def check(self, word: str) -> CrossRefResult:
        """Check a word against known vocabulary.

        Args:
            word: Candidate Etruscan word

        Returns:
            CrossRefResult with match information
        """
        self._load_vocabulary()
        self._load_glosses()

        normalized = self._normalize(word)
        original_normalized = word.lower()

        # Check exact match in verified glosses
        if original_normalized in self._gloss_cache:
            gloss = self._gloss_cache[original_normalized]
            return CrossRefResult(
                word=word,
                normalized=normalized,
                score=1.0,
                match_type="exact",
                matched_word=gloss.etruscan_word,
                matched_meaning=gloss.meaning,
                details="Exact match in verified glosses",
            )

        # Check normalized match in verified glosses
        for norm_key, gloss in self._gloss_cache.items():
            if self._normalize(norm_key) == normalized:
                return CrossRefResult(
                    word=word,
                    normalized=normalized,
                    score=0.95,
                    match_type="exact",
                    matched_word=gloss.etruscan_word,
                    matched_meaning=gloss.meaning,
                    details="Normalized match in verified glosses",
                )

        # Check exact match in vocabulary
        if original_normalized in self._vocab_cache:
            vocab = self._vocab_cache[original_normalized]
            return CrossRefResult(
                word=word,
                normalized=normalized,
                score=0.90,
                match_type="exact",
                matched_word=vocab.word,
                matched_meaning=vocab.meaning,
                details="Exact match in known vocabulary",
            )

        # Check for root matches (word is contained in or contains known word)
        best_root_match = None
        best_root_score = 0.0

        for norm_key, vocab in self._vocab_cache.items():
            vocab_norm = self._normalize(norm_key)

            # Check if candidate contains known root
            if vocab_norm in normalized and len(vocab_norm) >= 3:
                score = len(vocab_norm) / len(normalized) * 0.8
                if score > best_root_score:
                    best_root_score = score
                    best_root_match = vocab

            # Check if known word contains candidate
            if normalized in vocab_norm and len(normalized) >= 3:
                score = len(normalized) / len(vocab_norm) * 0.7
                if score > best_root_score:
                    best_root_score = score
                    best_root_match = vocab

        if best_root_match and best_root_score > 0.4:
            return CrossRefResult(
                word=word,
                normalized=normalized,
                score=best_root_score,
                match_type="root",
                matched_word=best_root_match.word,
                matched_meaning=best_root_match.meaning,
                details="Root/stem match with known vocabulary",
            )

        # Check for similar words
        best_similar = None
        best_similar_score = 0.0

        for norm_key, vocab in self._vocab_cache.items():
            vocab_norm = self._normalize(norm_key)
            sim = self._similarity_score(normalized, vocab_norm)
            if sim > best_similar_score and sim > 0.6:
                best_similar_score = sim
                best_similar = vocab

        if best_similar and best_similar_score > 0.6:
            return CrossRefResult(
                word=word,
                normalized=normalized,
                score=best_similar_score * 0.6,  # Reduce score for similarity
                match_type="similar",
                matched_word=best_similar.word,
                matched_meaning=best_similar.meaning,
                details=f"Similar to known word (similarity: {best_similar_score:.2f})",
            )

        # No match found
        return CrossRefResult(
            word=word,
            normalized=normalized,
            score=0.0,
            match_type="none",
            details="No match in known vocabulary",
        )

    def batch_check(self, words: list[str]) -> list[CrossRefResult]:
        """Check multiple words.

        Args:
            words: List of candidate words

        Returns:
            List of CrossRefResult objects
        """
        return [self.check(word) for word in words]
