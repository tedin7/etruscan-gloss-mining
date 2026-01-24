"""Linguistic validation based on Etruscan phonotactics.

Etruscan has distinctive phonological characteristics that can help
validate whether a candidate word is plausibly Etruscan:

1. No voiced stops (b, d, g) in native words - only voiceless (p, t, c/k)
2. Aspirated stops (ph, th, ch/kh) are common
3. No distinction between o and u (typically written as u)
4. Distinctive sibilants: s, z, and the special ś
5. Common word endings: -a, -i, -e, -al, -na, -s
6. Certain consonant clusters are typical or atypical
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class LinguisticResult:
    """Result of linguistic validation."""

    word: str
    score: float
    plausibility: str  # 'high', 'medium', 'low', 'unlikely'
    issues: list[str]
    positive_features: list[str]
    details: Optional[str] = None


class LinguisticValidator:
    """Validate words against Etruscan phonotactic patterns."""

    # Etruscan alphabet characters (Latin equivalents)
    ETRUSCAN_VOWELS = set("aeiuAEIU")  # Note: no 'o' in native words
    ETRUSCAN_CONSONANTS = set("cklmnprstvzxfhCKLMNPRSTVZXFH")

    # Voiced stops are NOT native to Etruscan
    VOICED_STOPS = set("bdgBDG")

    # Common Etruscan word endings
    COMMON_ENDINGS = [
        "a", "i", "e", "u",  # Vowel endings
        "al", "el", "il", "ul",  # Genitive -al
        "s", "as", "es", "is",  # -s endings
        "na", "ne", "ni",  # Adjectival -na
        "θi", "ti", "θ", "th",  # Locative
        "ce", "χe", "che",  # Past tense
        "r", "ar", "er", "ir",  # Plural -r
    ]

    # Typical Etruscan consonant clusters
    TYPICAL_CLUSTERS = [
        "pr", "tr", "cr", "kr",
        "pl", "cl", "kl",
        "sp", "st", "sc", "sk",
        "mn", "ln", "rn",
        "nt", "nc", "ns",
        "χv", "chv", "cv",  # Very Etruscan
        "θn", "thn", "tn",
    ]

    # Atypical/unlikely clusters for Etruscan
    UNLIKELY_CLUSTERS = [
        "bd", "bg", "gd", "gb",  # Voiced stop clusters
        "dg", "db", "gdr",
        "qu",  # Latin feature, not Etruscan
        "oo", "aa", "ee", "ii", "uu",  # Long vowels rare
    ]

    # Known Etruscan roots and morphemes
    KNOWN_ROOTS = [
        "ais", "ar", "cer", "cel", "clan", "cver",
        "hus", "laut", "lup", "maru", "mul", "nef",
        "pur", "sac", "spur", "sur", "tev", "tin",
        "tur", "zil", "zin", "θez", "θu",
    ]

    # Known Etruscan suffixes
    KNOWN_SUFFIXES = [
        "al", "s", "na", "ni", "sa", "la", "le",
        "θi", "θ", "ce", "χe", "r", "va", "cva",
        "eri", "il", "u", "θa", "ta",
    ]

    def __init__(self, strict: bool = False):
        """Initialize validator.

        Args:
            strict: If True, be stricter about violations
        """
        self.strict = strict

    def _has_voiced_stops(self, word: str) -> bool:
        """Check if word contains voiced stops."""
        return any(c in self.VOICED_STOPS for c in word)

    def _has_latin_o(self, word: str) -> bool:
        """Check if word has 'o' (typically 'u' in Etruscan)."""
        return "o" in word.lower()

    def _check_ending(self, word: str) -> tuple[bool, str]:
        """Check if word has a typical Etruscan ending."""
        word_lower = word.lower()
        for ending in sorted(self.COMMON_ENDINGS, key=len, reverse=True):
            if word_lower.endswith(ending):
                return True, ending
        return False, ""

    def _check_clusters(self, word: str) -> tuple[list[str], list[str]]:
        """Check consonant clusters.

        Returns:
            Tuple of (typical clusters found, unlikely clusters found)
        """
        word_lower = word.lower()
        typical = []
        unlikely = []

        for cluster in self.TYPICAL_CLUSTERS:
            if cluster in word_lower:
                typical.append(cluster)

        for cluster in self.UNLIKELY_CLUSTERS:
            if cluster in word_lower:
                unlikely.append(cluster)

        return typical, unlikely

    def _check_roots(self, word: str) -> list[str]:
        """Check for known Etruscan roots."""
        word_lower = word.lower()
        found = []
        for root in self.KNOWN_ROOTS:
            if root in word_lower:
                found.append(root)
        return found

    def _check_suffixes(self, word: str) -> list[str]:
        """Check for known Etruscan suffixes."""
        word_lower = word.lower()
        found = []
        for suffix in sorted(self.KNOWN_SUFFIXES, key=len, reverse=True):
            if word_lower.endswith(suffix):
                found.append(suffix)
                break  # Only count one suffix
        return found

    def _vowel_consonant_ratio(self, word: str) -> float:
        """Calculate vowel to consonant ratio."""
        vowels = sum(1 for c in word if c in self.ETRUSCAN_VOWELS)
        consonants = sum(1 for c in word if c.isalpha() and c not in self.ETRUSCAN_VOWELS)
        if consonants == 0:
            return float("inf")
        return vowels / consonants

    def validate(self, word: str) -> LinguisticResult:
        """Validate a word for Etruscan plausibility.

        Args:
            word: Word to validate

        Returns:
            LinguisticResult with score and details
        """
        issues = []
        positives = []
        score = 0.5  # Start neutral

        # Length check
        if len(word) < 2:
            return LinguisticResult(
                word=word,
                score=0.0,
                plausibility="unlikely",
                issues=["Word too short"],
                positive_features=[],
                details="Minimum 2 characters required",
            )

        if len(word) > 15:
            issues.append("Unusually long for Etruscan")
            score -= 0.1

        # Check for voiced stops
        if self._has_voiced_stops(word):
            issues.append("Contains voiced stops (b/d/g) - rare in Etruscan")
            score -= 0.25 if self.strict else 0.15

        # Check for Latin 'o'
        if self._has_latin_o(word):
            issues.append("Contains 'o' - typically 'u' in Etruscan")
            score -= 0.1

        # Check ending
        has_ending, ending = self._check_ending(word)
        if has_ending:
            positives.append(f"Typical Etruscan ending: -{ending}")
            score += 0.15
        else:
            issues.append("No typical Etruscan ending")
            score -= 0.1

        # Check consonant clusters
        typical_clusters, unlikely_clusters = self._check_clusters(word)
        if typical_clusters:
            positives.append(f"Typical clusters: {', '.join(typical_clusters)}")
            score += 0.1 * min(len(typical_clusters), 2)
        if unlikely_clusters:
            issues.append(f"Unlikely clusters: {', '.join(unlikely_clusters)}")
            score -= 0.15 * len(unlikely_clusters)

        # Check for known roots
        roots = self._check_roots(word)
        if roots:
            positives.append(f"Contains known roots: {', '.join(roots)}")
            score += 0.2

        # Check for known suffixes
        suffixes = self._check_suffixes(word)
        if suffixes:
            positives.append(f"Known suffix: -{suffixes[0]}")
            score += 0.1

        # Vowel-consonant ratio (Etruscan tends toward balanced or consonant-heavy)
        ratio = self._vowel_consonant_ratio(word)
        if 0.3 <= ratio <= 0.7:
            positives.append("Balanced vowel-consonant ratio")
            score += 0.05
        elif ratio > 1.0:
            issues.append("Too vowel-heavy for Etruscan")
            score -= 0.1

        # Latin-looking features
        if re.search(r"(tion|ment|icus|orum|arum|ibus)$", word.lower()):
            issues.append("Latin morphology detected")
            score -= 0.3

        # Clamp score
        score = max(0.0, min(1.0, score))

        # Determine plausibility category
        if score >= 0.7:
            plausibility = "high"
        elif score >= 0.5:
            plausibility = "medium"
        elif score >= 0.3:
            plausibility = "low"
        else:
            plausibility = "unlikely"

        return LinguisticResult(
            word=word,
            score=score,
            plausibility=plausibility,
            issues=issues,
            positive_features=positives,
            details=f"Linguistic score: {score:.2f}",
        )

    def batch_validate(self, words: list[str]) -> list[LinguisticResult]:
        """Validate multiple words.

        Args:
            words: List of words to validate

        Returns:
            List of LinguisticResult objects
        """
        return [self.validate(word) for word in words]
