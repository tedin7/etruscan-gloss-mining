"""Phonotactic fingerprinting for language identification.

This module creates phonotactic "fingerprints" for words based on
their sound patterns, allowing us to identify words that fit Etruscan
phonology better than Latin phonology.

Key differences between Etruscan and Latin phonology:

ETRUSCAN:
- No voiced stops (b, d, g) - uses only p, t, c/k
- Four vowels: a, e, i, u (no o)
- Common endings: -na, -ra, -la, -sa, -ta, -al, -il, -ul
- Aspirated stops: ph, th, ch (χ, θ, φ)
- Fricatives: f, s, h, ś (palatalized s)
- Common clusters: sp, st, sc, tr, pr, cr
- Stress on first syllable

LATIN:
- Full voiced/voiceless stop series (b/p, d/t, g/c)
- Five vowels: a, e, i, o, u
- Common endings: -us, -um, -is, -es, -a, -ae
- Less aspiration
- Different cluster patterns

Words that score high on Etruscan patterns but low on Latin patterns
are candidates for Etruscan substrate/loanwords.
"""

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LanguageFingerprint:
    """Phonotactic fingerprint analysis result."""

    word: str
    etruscan_score: float  # 0.0 to 1.0
    latin_score: float  # 0.0 to 1.0
    substrate_probability: float  # Probability of non-Latin origin
    etruscan_features: list[str] = field(default_factory=list)
    latin_violations: list[str] = field(default_factory=list)
    analysis: str = ""


class PhonotacticFingerprinter:
    """Creates phonotactic fingerprints for language identification.

    Analyzes words against known phonotactic patterns for Etruscan
    and Latin, producing a score indicating how well the word fits
    each language's sound system.
    """

    def __init__(self):
        """Initialize phonotactic rules."""
        self._init_etruscan_rules()
        self._init_latin_rules()

    def _init_etruscan_rules(self) -> None:
        """Initialize Etruscan phonotactic patterns."""
        # Positive Etruscan features (presence = more Etruscan-like)
        self.etruscan_positive = {
            # No voiced stops - these patterns suggest Etruscan
            "voiceless_only": {
                "pattern": r'^[^bdg]*$',
                "weight": 0.15,
                "description": "No voiced stops (b/d/g)",
            },

            # No 'o' vowel - Etruscan had only a, e, i, u
            "no_o_vowel": {
                "pattern": r'^[^o]*$',
                "weight": 0.15,
                "description": "No 'o' vowel",
            },

            # Aspirated consonants
            "aspirates": {
                "pattern": r'(ph|th|ch)',
                "weight": 0.12,
                "description": "Aspirated stops (ph/th/ch)",
            },

            # Typical Etruscan endings
            "etruscan_ending_na": {
                "pattern": r'na$',
                "weight": 0.15,
                "description": "Ending -na",
            },
            "etruscan_ending_ra": {
                "pattern": r'ra$',
                "weight": 0.12,
                "description": "Ending -ra",
            },
            "etruscan_ending_la": {
                "pattern": r'la$',
                "weight": 0.12,
                "description": "Ending -la",
            },
            "etruscan_ending_al": {
                "pattern": r'al$',
                "weight": 0.10,
                "description": "Ending -al (genitive)",
            },

            # Clusters common in Etruscan
            "cluster_sp": {
                "pattern": r'sp',
                "weight": 0.05,
                "description": "Cluster sp-",
            },
            "cluster_st": {
                "pattern": r'st',
                "weight": 0.05,
                "description": "Cluster st-",
            },
            "cluster_sc": {
                "pattern": r'sc',
                "weight": 0.05,
                "description": "Cluster sc-",
            },

            # Initial clusters
            "initial_cluster": {
                "pattern": r'^(sp|st|sc|tr|pr|cr)',
                "weight": 0.05,
                "description": "Initial consonant cluster",
            },

            # Etruscan sibilant patterns
            "double_s": {
                "pattern": r'ss',
                "weight": 0.05,
                "description": "Double sibilant",
            },

            # Velar nasal (rarely in Latin)
            "velar_n": {
                "pattern": r'(nc|ng)h?$',
                "weight": 0.08,
                "description": "Velar nasal pattern",
            },

            # h- initial (common in Etruscan, less so Latin loans)
            "initial_h": {
                "pattern": r'^h[aeiur]',
                "weight": 0.08,
                "description": "Initial h-",
            },
        }

        # Negative Latin features (presence = less Latin-like)
        self.latin_negative = {
            # Voiced stops are normal in Latin
            "voiced_stop_b": {
                "pattern": r'b',
                "weight": -0.08,
                "description": "Contains 'b' (unusual in Etruscan)",
            },
            "voiced_stop_d": {
                "pattern": r'd',
                "weight": -0.08,
                "description": "Contains 'd' (unusual in Etruscan)",
            },
            "voiced_stop_g": {
                "pattern": r'g(?!h)',
                "weight": -0.08,
                "description": "Contains 'g' (unusual in Etruscan)",
            },

            # 'o' vowel is normal in Latin
            "has_o": {
                "pattern": r'o',
                "weight": -0.10,
                "description": "Contains 'o' (unusual in Etruscan)",
            },

            # Typical Latin endings
            "latin_ending_us": {
                "pattern": r'us$',
                "weight": -0.08,
                "description": "Latin ending -us",
            },
            "latin_ending_um": {
                "pattern": r'um$',
                "weight": -0.08,
                "description": "Latin ending -um",
            },
            "latin_ending_is": {
                "pattern": r'is$',
                "weight": -0.05,
                "description": "Latin ending -is",
            },
            "latin_ending_orum": {
                "pattern": r'orum$',
                "weight": -0.10,
                "description": "Latin genitive plural -orum",
            },
        }

    def _init_latin_rules(self) -> None:
        """Initialize Latin phonotactic patterns."""
        # Patterns that are normal in Latin
        self.latin_positive = {
            "standard_endings": {
                "pattern": r'(us|um|is|es|ae|am|em|os)$',
                "weight": 0.15,
                "description": "Standard Latin endings",
            },
            "voiced_stops": {
                "pattern": r'[bdg]',
                "weight": 0.10,
                "description": "Voiced stops (normal in Latin)",
            },
            "o_vowel": {
                "pattern": r'o',
                "weight": 0.08,
                "description": "Contains 'o' (normal in Latin)",
            },
            "latin_prefixes": {
                "pattern": r'^(sub|in|ex|de|ab|ad|con|dis|per|pro|re)',
                "weight": 0.15,
                "description": "Latin prefix",
            },
            "latin_suffixes": {
                "pattern": r'(tion|ment|tat|bil|tor|trix|ura|ium)$',
                "weight": 0.12,
                "description": "Latin derivational suffix",
            },
        }

    def fingerprint(self, word: str) -> LanguageFingerprint:
        """Create a phonotactic fingerprint for a word.

        Args:
            word: Word to analyze

        Returns:
            Fingerprint with Etruscan and Latin scores
        """
        word_lower = word.lower().strip()
        word_normalized = self._normalize(word_lower)

        etruscan_score = 0.5  # Start neutral
        latin_score = 0.5

        etruscan_features = []
        latin_violations = []

        # Apply Etruscan positive patterns
        for name, rule in self.etruscan_positive.items():
            if re.search(rule["pattern"], word_normalized):
                etruscan_score += rule["weight"]
                etruscan_features.append(rule["description"])

        # Apply Latin negative patterns (penalize Etruscan score)
        for name, rule in self.latin_negative.items():
            if re.search(rule["pattern"], word_normalized):
                etruscan_score += rule["weight"]  # Negative weight
                latin_violations.append(rule["description"])

        # Apply Latin positive patterns
        for name, rule in self.latin_positive.items():
            if re.search(rule["pattern"], word_normalized):
                latin_score += rule["weight"]

        # Normalize scores to 0-1 range
        etruscan_score = max(0.0, min(1.0, etruscan_score))
        latin_score = max(0.0, min(1.0, latin_score))

        # Calculate substrate probability
        # Higher if Etruscan score >> Latin score
        if etruscan_score > latin_score:
            substrate_prob = (etruscan_score - latin_score) / etruscan_score
            substrate_prob = min(1.0, substrate_prob * 1.5)  # Boost
        else:
            substrate_prob = 0.0

        # Additional boost if no Latin etymology is obvious
        if not self._has_obvious_latin_etymology(word_normalized):
            substrate_prob = min(1.0, substrate_prob + 0.2)

        analysis = self._generate_analysis(
            word, etruscan_score, latin_score,
            etruscan_features, latin_violations
        )

        return LanguageFingerprint(
            word=word,
            etruscan_score=etruscan_score,
            latin_score=latin_score,
            substrate_probability=substrate_prob,
            etruscan_features=etruscan_features,
            latin_violations=latin_violations,
            analysis=analysis,
        )

    def _normalize(self, word: str) -> str:
        """Normalize word for phonotactic analysis."""
        # Handle common Latin spelling variations
        word = word.replace('ae', 'e')
        word = word.replace('oe', 'e')
        word = word.replace('qu', 'kw')
        word = word.replace('x', 'ks')
        return word

    def _has_obvious_latin_etymology(self, word: str) -> bool:
        """Check if word has obvious Latin derivation."""
        # Common Latin roots
        latin_roots = {
            'dic', 'duc', 'fac', 'fer', 'mitt', 'pon', 'scrib',
            'ven', 'vid', 'voc', 'cap', 'cip', 'cept', 'ag', 'act',
            'aud', 'clud', 'clus', 'curr', 'curs', 'leg', 'lect',
            'mov', 'mot', 'pet', 'plic', 'port', 'rupt', 'sed',
            'sess', 'sent', 'spec', 'spect', 'sta', 'stat', 'ten',
            'tent', 'tract', 'vert', 'vers', 'volv', 'volu',
        }

        for root in latin_roots:
            if root in word:
                return True

        return False

    def _generate_analysis(
        self,
        word: str,
        etr_score: float,
        lat_score: float,
        etr_features: list[str],
        lat_violations: list[str],
    ) -> str:
        """Generate human-readable analysis."""
        lines = [f"Analysis of '{word}':"]

        if etr_score > lat_score:
            lines.append(f"  Favors ETRUSCAN origin (Etr: {etr_score:.2f}, Lat: {lat_score:.2f})")
        elif lat_score > etr_score:
            lines.append(f"  Favors LATIN origin (Lat: {lat_score:.2f}, Etr: {etr_score:.2f})")
        else:
            lines.append(f"  INDETERMINATE (Etr: {etr_score:.2f}, Lat: {lat_score:.2f})")

        if etr_features:
            lines.append(f"  Etruscan features: {', '.join(etr_features)}")

        if lat_violations:
            lines.append(f"  Un-Etruscan features: {', '.join(lat_violations)}")

        return "\n".join(lines)

    def batch_fingerprint(self, words: list[str]) -> list[LanguageFingerprint]:
        """Fingerprint multiple words.

        Args:
            words: List of words to analyze

        Returns:
            List of fingerprints sorted by substrate probability
        """
        results = [self.fingerprint(word) for word in words]
        results.sort(key=lambda f: f.substrate_probability, reverse=True)
        return results

    def find_substrate_candidates(
        self,
        words: list[str],
        min_probability: float = 0.5
    ) -> list[LanguageFingerprint]:
        """Find words likely to be substrate/loanwords.

        Args:
            words: Words to analyze
            min_probability: Minimum substrate probability

        Returns:
            List of candidate fingerprints
        """
        fingerprints = self.batch_fingerprint(words)
        return [f for f in fingerprints if f.substrate_probability >= min_probability]

    def analyze_text(self, text: str) -> list[LanguageFingerprint]:
        """Extract and fingerprint all unique words from text.

        Args:
            text: Text to analyze

        Returns:
            Fingerprints sorted by substrate probability
        """
        # Extract unique words
        words = set(re.findall(r'\b[a-zA-Z]{4,}\b', text.lower()))

        # Filter out very common Latin words
        common = {
            'quod', 'quid', 'quae', 'qui', 'quem', 'quibus',
            'esse', 'sunt', 'erat', 'fuit', 'erant',
            'habet', 'habent', 'haber', 'habuit',
            'enim', 'autem', 'tamen', 'igitur', 'ergo',
            'etiam', 'quia', 'quod', 'unde', 'inde',
            'ille', 'illa', 'illud', 'ipse', 'ipsa',
            'hunc', 'hanc', 'haec', 'huic', 'huius',
        }
        words = words - common

        return self.batch_fingerprint(list(words))


def fingerprint_word(word: str) -> LanguageFingerprint:
    """Create a phonotactic fingerprint for a word.

    Args:
        word: Word to analyze

    Returns:
        Fingerprint with language scores
    """
    fingerprinter = PhonotacticFingerprinter()
    return fingerprinter.fingerprint(word)
