"""Greek patterns for detecting Etruscan glosses in Greek texts.

Greek authors (Dionysius of Halicarnassus, Strabo, Plutarch, etc.)
sometimes discuss Etruscan/Tyrrhenian vocabulary. These patterns
detect such mentions in Greek text.

Note: Greek text handling requires proper Unicode support.
These patterns use both Greek characters and transliterated forms.
"""

import re
from dataclasses import dataclass
from typing import Optional

from .latin_patterns import LatinPattern


@dataclass
class GreekPattern(LatinPattern):
    """A pattern for detecting Etruscan glosses in Greek text."""

    # Uses Greek script
    uses_greek_script: bool = True


# Greek patterns using Greek script
# Τυρρηνοί = Tyrrhenoi (Tyrrhenians/Etruscans)
# Τυρσηνοί = Tyrsenoi (variant)
# καλοῦσι = kalousi (they call)
# λέγουσι = legousi (they say)
# φωνή = phone (language/voice)

GREEK_SCRIPT_PATTERNS = [
    GreekPattern(
        name="tyrrhenoi_kalousi",
        regex=r"Τυρ[ρσ]ηνο[ίι]\s+καλο[ῦυ]σι\s+(\w+)",
        description="Τυρρηνοί καλοῦσι X - The Tyrrhenians call X",
        confidence=0.90,
        uses_greek_script=True,
    ),
    GreekPattern(
        name="tyrrhenoi_legousi",
        regex=r"Τυρ[ρσ]ηνο[ίι]\s+λ[έε]γουσι\s+(\w+)",
        description="Τυρρηνοί λέγουσι X - The Tyrrhenians say X",
        confidence=0.90,
        uses_greek_script=True,
    ),
    GreekPattern(
        name="tyrrhenia_phone",
        regex=r"Τυρ[ρσ]ην[ίι][κκ]?[ῇη]\s+φων[ῇη]\s+(\w+)",
        description="Τυρρηνικῇ φωνῇ X - in Tyrrhenian language X",
        confidence=0.85,
        uses_greek_script=True,
    ),
    GreekPattern(
        name="para_tyrrhenois",
        regex=r"παρ[ὰα]\s+Τυρ[ρσ]ηνο[ῖι]ς\s+(\w+)",
        description="παρὰ Τυρρηνοῖς X - among the Tyrrhenians X",
        confidence=0.85,
        uses_greek_script=True,
    ),
    GreekPattern(
        name="tyrrhenisti",
        regex=r"Τυρ[ρσ]ηνιστ[ίι]\s+(\w+)",
        description="Τυρρηνιστί X - in Tyrrhenian, X",
        confidence=0.90,
        uses_greek_script=True,
    ),
]

# Transliterated patterns (for texts in Latin script or mixed)
TRANSLITERATED_PATTERNS = [
    GreekPattern(
        name="tyrrhenoi_kalousi_lat",
        regex=r"[Tt]yr[rs]h?enoi\s+kalou?si\s+(\w+)",
        description="Tyrrhenoi kalousi X (transliterated)",
        confidence=0.85,
        uses_greek_script=False,
    ),
    GreekPattern(
        name="tyrrhenia_glosse",
        regex=r"[Tt]yr[rs]h?eni[kc]?[ea]\s+gloss[ea]\s+(\w+)",
        description="Tyrrhenia glosse X - Tyrrhenian word X",
        confidence=0.80,
        uses_greek_script=False,
    ),
]

# Dionysius of Halicarnassus specific patterns
# He wrote extensively about Rome's Etruscan connections
DIONYSIUS_PATTERNS = [
    GreekPattern(
        name="dionysius_tyrsenoi",
        regex=r"Τυρσηνο[ίι]\s+(?:δ[ὲε]\s+)?(\w+)\s+(?:καλο[ῦυ]σι|ὀνομ[άα]ζουσι)",
        description="Dionysius: Tyrsenoi X kalousi",
        confidence=0.90,
        uses_greek_script=True,
    ),
]

# Strabo patterns (Geography contains Etruscan references)
STRABO_PATTERNS = [
    GreekPattern(
        name="strabo_tyrrhenian",
        regex=r"[οὁ]ἱ\s+Τυρ[ρσ]ηνο[ίι]\s+(\w+)\s+καλο[ῦυ]σι",
        description="Strabo: οἱ Τυρρηνοί X καλοῦσι",
        confidence=0.90,
        uses_greek_script=True,
    ),
]

# Hesychius lexicon patterns (contains many glosses)
HESYCHIUS_PATTERNS = [
    GreekPattern(
        name="hesychius_tyrr",
        regex=r"(\w+)[·:]\s+(?:παρ[ὰα]\s+)?Τυρ[ρσ]ηνο[ῖι]ς",
        description="Hesychius: X: παρὰ Τυρρηνοῖς",
        confidence=0.85,
        uses_greek_script=True,
    ),
]

# Collect all Greek patterns
ALL_GREEK_PATTERNS: list[GreekPattern] = (
    GREEK_SCRIPT_PATTERNS
    + TRANSLITERATED_PATTERNS
    + DIONYSIUS_PATTERNS
    + STRABO_PATTERNS
    + HESYCHIUS_PATTERNS
)


def get_greek_patterns(include_transliterated: bool = True) -> list[GreekPattern]:
    """Get all Greek patterns, optionally including transliterated ones."""
    if include_transliterated:
        return ALL_GREEK_PATTERNS
    return [p for p in ALL_GREEK_PATTERNS if p.uses_greek_script]


def get_greek_pattern_by_name(name: str) -> Optional[GreekPattern]:
    """Get a Greek pattern by its name."""
    for p in ALL_GREEK_PATTERNS:
        if p.name == name:
            return p
    return None
