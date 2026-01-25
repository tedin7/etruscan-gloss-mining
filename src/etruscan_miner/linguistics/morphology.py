"""Etruscan morphological analysis.

This module provides tools for analyzing Etruscan word structure,
decomposing words into roots and affixes, and understanding
morphological patterns. This enables prediction of unattested forms.

Etruscan morphology includes:
- Agglutinative suffixation
- Genitive in -s, -al, -la
- Plural in -r, -χva
- Locative in -θi
- Ablative in -θ
- Pertinentive in -si, -śi
- Past tense in -ce, -χe
"""

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Morpheme:
    """An Etruscan morpheme (root or affix)."""

    form: str
    type: str  # 'root', 'suffix', 'prefix', 'infix'
    function: str  # 'genitive', 'plural', 'locative', 'past_tense', etc.
    meaning: Optional[str] = None
    allomorphs: list[str] = field(default_factory=list)  # Variant forms
    notes: str = ""


@dataclass
class MorphologicalAnalysis:
    """Result of morphological analysis."""

    word: str
    root: Optional[str] = None
    root_meaning: Optional[str] = None
    suffixes: list[Morpheme] = field(default_factory=list)
    prefixes: list[Morpheme] = field(default_factory=list)
    analysis_confidence: float = 0.0
    reconstructed_meaning: str = ""
    notes: str = ""


# Known Etruscan morphemes
KNOWN_MORPHEMES = {
    # Case suffixes
    "genitive": [
        Morpheme("s", "suffix", "genitive", "of", allomorphs=["ś"]),
        Morpheme("al", "suffix", "genitive", "of (relational)", allomorphs=["el", "il", "ul", "l"]),
        Morpheme("la", "suffix", "genitive", "of (possessive)", allomorphs=["le", "li"]),
    ],
    "plural": [
        Morpheme("r", "suffix", "plural", "-s/plural", allomorphs=["ar", "er", "ur"]),
        Morpheme("χva", "suffix", "plural", "collective", allomorphs=["cva", "chva"]),
    ],
    "locative": [
        Morpheme("θi", "suffix", "locative", "in/at", allomorphs=["ti", "thi"]),
    ],
    "ablative": [
        Morpheme("θ", "suffix", "ablative", "from", allomorphs=["t", "th"]),
    ],
    "pertinentive": [
        Morpheme("si", "suffix", "pertinentive", "for/pertaining to", allomorphs=["śi", "se"]),
    ],
    "accusative": [
        Morpheme("ni", "suffix", "accusative", "direct object", allomorphs=["ne", "n"]),
    ],

    # Verbal suffixes
    "past_tense": [
        Morpheme("ce", "suffix", "past_tense", "did/made", allomorphs=["χe", "che", "ke"]),
    ],
    "passive": [
        Morpheme("χe", "suffix", "passive", "was done", allomorphs=["che"]),
    ],

    # Derivational suffixes
    "adjective": [
        Morpheme("na", "suffix", "adjective", "-an/-ish", allomorphs=["ne", "ni"]),
        Morpheme("c", "suffix", "adjective", "pertaining to", allomorphs=["k", "ch"]),
    ],
    "agent": [
        Morpheme("θas", "suffix", "agent", "one who", allomorphs=["tas"]),
    ],
    "diminutive": [
        Morpheme("za", "suffix", "diminutive", "little", allomorphs=["sa"]),
    ],
}

# Known Etruscan roots with meanings
KNOWN_ROOTS = {
    # Kinship
    "clan": {"meaning": "son", "pos": "noun"},
    "sec": {"meaning": "daughter", "pos": "noun"},
    "ati": {"meaning": "mother", "pos": "noun"},
    "nef": {"meaning": "grandson/nephew", "pos": "noun"},
    "pui": {"meaning": "wife", "pos": "noun"},
    "laut": {"meaning": "family/freedman", "pos": "noun"},

    # Divine/religious
    "ais": {"meaning": "god", "pos": "noun"},
    "θu": {"meaning": "one (sacred)", "pos": "numeral"},
    "zal": {"meaning": "two", "pos": "numeral"},
    "ci": {"meaning": "three", "pos": "numeral"},
    "śa": {"meaning": "four", "pos": "numeral"},
    "hut": {"meaning": "six", "pos": "numeral"},
    "sem": {"meaning": "seven", "pos": "numeral"},
    "cez": {"meaning": "eight", "pos": "numeral"},
    "nur": {"meaning": "nine", "pos": "numeral"},
    "śar": {"meaning": "ten", "pos": "numeral"},

    # Titles/social
    "lauch": {"meaning": "king/chief", "pos": "noun"},
    "maru": {"meaning": "magistrate", "pos": "noun"},
    "zil": {"meaning": "magistrate (zilath)", "pos": "noun"},
    "spur": {"meaning": "city", "pos": "noun"},
    "ras": {"meaning": "Etruscan (rasna)", "pos": "adjective"},

    # Actions
    "tur": {"meaning": "give", "pos": "verb"},
    "mul": {"meaning": "dedicate/offer", "pos": "verb"},
    "ar": {"meaning": "make/do", "pos": "verb"},
    "zic": {"meaning": "write", "pos": "verb"},
    "lup": {"meaning": "die", "pos": "verb"},
    "sval": {"meaning": "live", "pos": "verb"},
    "ten": {"meaning": "hold/act as", "pos": "verb"},

    # Objects/concepts
    "avil": {"meaning": "year", "pos": "noun"},
    "tiv": {"meaning": "moon/month", "pos": "noun"},
    "suθ": {"meaning": "tomb/place", "pos": "noun"},
    "vin": {"meaning": "wine", "pos": "noun"},
    "cer": {"meaning": "make/build", "pos": "verb"},
    "fler": {"meaning": "offering/statue", "pos": "noun"},
    "hin": {"meaning": "below", "pos": "adverb"},
    "nac": {"meaning": "how/as", "pos": "adverb"},

    # Theonyms (deity name roots)
    "tin": {"meaning": "Tinia (Jupiter)", "pos": "theonym"},
    "uni": {"meaning": "Uni (Juno)", "pos": "theonym"},
    "men": {"meaning": "Menrva (Minerva)", "pos": "theonym"},
    "tur": {"meaning": "Turan (Venus)", "pos": "theonym"},
    "velch": {"meaning": "Velchans (Vulcan)", "pos": "theonym"},
    "seθ": {"meaning": "Sethlans (Vulcan)", "pos": "theonym"},
    "fufl": {"meaning": "Fufluns (Dionysus)", "pos": "theonym"},
    "aplu": {"meaning": "Aplu (Apollo)", "pos": "theonym"},
    "ari": {"meaning": "Aritimi (Artemis)", "pos": "theonym"},
}


class EtruscanMorphology:
    """Analyzer for Etruscan word morphology."""

    def __init__(self):
        """Initialize analyzer."""
        self.morphemes = KNOWN_MORPHEMES
        self.roots = KNOWN_ROOTS
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile suffix patterns for matching."""
        self.suffix_patterns = []

        for category, morphemes in self.morphemes.items():
            for m in morphemes:
                # Build pattern from form and allomorphs
                forms = [m.form] + m.allomorphs
                pattern = "|".join(re.escape(f) for f in sorted(forms, key=len, reverse=True))
                self.suffix_patterns.append({
                    "pattern": re.compile(f"({pattern})$"),
                    "morpheme": m,
                    "category": category,
                })

    def analyze(self, word: str) -> MorphologicalAnalysis:
        """Analyze the morphology of an Etruscan word.

        Args:
            word: Etruscan word to analyze

        Returns:
            MorphologicalAnalysis with decomposition
        """
        word_lower = word.lower()
        analysis = MorphologicalAnalysis(word=word)
        remaining = word_lower

        # Try to identify suffixes (right to left)
        suffixes_found = []
        iterations = 0
        max_iterations = 5  # Prevent infinite loops

        while remaining and iterations < max_iterations:
            matched = False
            for sp in self.suffix_patterns:
                match = sp["pattern"].search(remaining)
                if match:
                    suffix = match.group(1)
                    # Don't strip if it would leave nothing
                    if len(remaining) - len(suffix) >= 2:
                        suffixes_found.insert(0, sp["morpheme"])
                        remaining = remaining[:-len(suffix)]
                        matched = True
                        break

            if not matched:
                break
            iterations += 1

        analysis.suffixes = suffixes_found

        # Try to identify root
        if remaining:
            for root, info in self.roots.items():
                if remaining == root or remaining.startswith(root):
                    analysis.root = root
                    analysis.root_meaning = info["meaning"]
                    break

        # Calculate confidence
        if analysis.root:
            analysis.analysis_confidence = 0.6
            if analysis.suffixes:
                analysis.analysis_confidence += 0.1 * min(len(analysis.suffixes), 3)
        elif analysis.suffixes:
            analysis.analysis_confidence = 0.3 + 0.1 * min(len(analysis.suffixes), 2)
        else:
            analysis.analysis_confidence = 0.1

        # Reconstruct meaning
        if analysis.root_meaning:
            meaning_parts = [analysis.root_meaning]
            for suffix in analysis.suffixes:
                if suffix.meaning:
                    meaning_parts.append(f"[{suffix.function}: {suffix.meaning}]")
            analysis.reconstructed_meaning = " ".join(meaning_parts)

        return analysis

    def find_root(self, word: str) -> Optional[tuple[str, dict]]:
        """Find the root of an Etruscan word.

        Args:
            word: Word to analyze

        Returns:
            Tuple of (root, info) if found, None otherwise
        """
        word_lower = word.lower()

        # Try exact match first
        if word_lower in self.roots:
            return word_lower, self.roots[word_lower]

        # Try prefix match
        for root, info in sorted(self.roots.items(), key=lambda x: len(x[0]), reverse=True):
            if word_lower.startswith(root):
                return root, info

        return None

    def get_morphemes_by_function(self, function: str) -> list[Morpheme]:
        """Get all morphemes with a specific function.

        Args:
            function: Function name (genitive, plural, etc.)

        Returns:
            List of Morpheme objects
        """
        return self.morphemes.get(function, [])


def analyze_morphology(word: str) -> MorphologicalAnalysis:
    """Analyze the morphology of an Etruscan word.

    Args:
        word: Word to analyze

    Returns:
        MorphologicalAnalysis object
    """
    analyzer = EtruscanMorphology()
    return analyzer.analyze(word)


def decompose_word(word: str) -> dict:
    """Decompose an Etruscan word into components.

    Args:
        word: Word to decompose

    Returns:
        Dict with root, suffixes, and analysis
    """
    analysis = analyze_morphology(word)
    return {
        "word": word,
        "root": analysis.root,
        "root_meaning": analysis.root_meaning,
        "suffixes": [{"form": s.form, "function": s.function, "meaning": s.meaning} for s in analysis.suffixes],
        "confidence": analysis.analysis_confidence,
        "reconstructed_meaning": analysis.reconstructed_meaning,
    }
