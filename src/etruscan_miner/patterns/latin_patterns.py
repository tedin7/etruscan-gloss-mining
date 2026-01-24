"""Latin patterns for detecting Etruscan glosses in Latin texts.

These patterns identify phrases where Latin authors explicitly mention
Etruscan words or etymology, such as "Tusci vocant", "lingua Etrusca", etc.
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class PatternMatch:
    """Result of a pattern match."""

    pattern_name: str
    etruscan_word: str
    full_match: str
    context_before: str
    context_after: str
    start_pos: int
    end_pos: int
    confidence: float
    meaning_hint: Optional[str] = None


@dataclass
class LatinPattern:
    """A pattern for detecting Etruscan glosses in Latin text."""

    name: str
    regex: str
    description: str
    confidence: float
    word_group: int = 1  # Which regex group contains the Etruscan word
    meaning_group: Optional[int] = None  # Group containing meaning hint if any

    def compile(self) -> re.Pattern:
        """Compile the regex pattern."""
        return re.compile(self.regex, re.IGNORECASE | re.MULTILINE)


# Core patterns - highest confidence
# Note: Many patterns have two versions - one for word AFTER pattern, one for word BEFORE
CORE_PATTERNS = [
    LatinPattern(
        name="tusci_vocant",
        regex=r"[Tt]usci?\s+voca(?:n)?t\s+(\w+)",
        description="Tusci vocant X - The Etruscans call [something] X",
        confidence=0.90,
    ),
    LatinPattern(
        name="etrusca_lingua",
        regex=r"[Ee]trusca\s+lingua\s+(\w+)",
        description="Etrusca lingua X - In the Etruscan language, X",
        confidence=0.90,
    ),
    LatinPattern(
        name="word_etrusca_lingua",
        regex=r"(\w+)\s+(?:enim\s+)?[Ee]trusca\s+lingua",
        description="X Etrusca lingua - X in the Etruscan language",
        confidence=0.90,
    ),
    LatinPattern(
        name="lingua_etrusca_dicitur",
        regex=r"lingua\s+[Ee]trusca\s+(?:dicitur\s+)?(\w+)",
        description="lingua Etrusca dicitur X - is called X in Etruscan",
        confidence=0.90,
    ),
    LatinPattern(
        name="etrusco_vocabulo",
        regex=r"[Ee]trusco\s+vocabulo\s+(\w+)",
        description="Etrusco vocabulo X - with Etruscan word X",
        confidence=0.90,
    ),
    LatinPattern(
        name="word_etrusco_vocabulo",
        regex=r"(\w+)\s+[Ee]trusco\s+vocabulo",
        description="X Etrusco vocabulo - X with Etruscan word",
        confidence=0.90,
    ),
    LatinPattern(
        name="etrusco_nomine",
        regex=r"[Ee]trusco\s+nomine\s+(\w+)",
        description="Etrusco nomine X - with Etruscan name X",
        confidence=0.90,
    ),
]

# Secondary patterns - high confidence
SECONDARY_PATTERNS = [
    LatinPattern(
        name="apud_etruscos",
        regex=r"apud\s+[Ee]truscos\s+(\w+)",
        description="apud Etruscos X - among the Etruscans, X",
        confidence=0.85,
    ),
    LatinPattern(
        name="quod_etrusci",
        regex=r"quod\s+[Ee]trusci\s+(\w+)",
        description="quod Etrusci X - which the Etruscans [call] X",
        confidence=0.85,
    ),
    LatinPattern(
        name="tyrrheni_vocant",
        regex=r"[Tt]yrrhen[io]s?\s+voca(?:n)?t\s+(\w+)",
        description="Tyrrheni vocant X - The Tyrrhenians call X",
        confidence=0.85,
    ),
    LatinPattern(
        name="tusco_nomine",
        regex=r"[Tt]usco\s+nomine\s+(\w+)",
        description="Tusco nomine X - with Tuscan name X",
        confidence=0.85,
    ),
    LatinPattern(
        name="word_tusco_nomine",
        regex=r"(\w+)\s+[Tt]usco\s+nomine",
        description="X Tusco nomine - X with Tuscan name",
        confidence=0.85,
    ),
    LatinPattern(
        name="tusco_sermone",
        regex=r"[Tt]usco\s+sermone\s+(\w+)",
        description="Tusco sermone X - in Tuscan speech, X",
        confidence=0.85,
    ),
    LatinPattern(
        name="tusco_verbo",
        regex=r"[Tt]usco\s+verbo\s+(\w+)",
        description="Tusco verbo X - in Tuscan word, X",
        confidence=0.85,
    ),
    LatinPattern(
        name="word_tusco_verbo",
        regex=r"(\w+)\s+[Tt]usco\s+verbo",
        description="X Tusco verbo - X in Tuscan word",
        confidence=0.85,
    ),
    LatinPattern(
        name="etrusci_appellant",
        regex=r"[Ee]trusci\s+appella(?:n)?t\s+(\w+)",
        description="Etrusci appellant X - The Etruscans call X",
        confidence=0.85,
    ),
    # Varro-style patterns: "ita dicunt X Tusci", "dicunt X Tusci"
    LatinPattern(
        name="dicunt_tusci",
        regex=r"(?:ita\s+)?dicunt\s+(\w+)\s+[Tt]usci",
        description="dicunt X Tusci - The Tuscans call X",
        confidence=0.90,
    ),
    LatinPattern(
        name="tusci_dicunt",
        regex=r"[Tt]usci\s+(?:ita\s+)?dicunt\s+(\w+)",
        description="Tusci dicunt X - The Tuscans say X",
        confidence=0.90,
    ),
    LatinPattern(
        name="dictum_a_tuscis",
        regex=r"(\w+)\s+dict\w+\s+a\s+[Tt]uscis",
        description="X dictum a Tuscis - X named by the Tuscans",
        confidence=0.85,
    ),
    LatinPattern(
        name="tuscanicum_dictum",
        regex=r"([Tt]uscanicum)\s+dict\w+\s+a\s+[Tt]uscis",
        description="Tuscanicum dictum - Tuscan style named by Tuscans",
        confidence=0.80,
    ),
    LatinPattern(
        name="sabini_dicunt",
        regex=r"[Ss]abini\s+(\w+)\s+dicunt",
        description="Sabini X dicunt - Sabines call X (related dialect)",
        confidence=0.75,
    ),
    # "X dictus quod ita dicunt ... Tusci" pattern (Varro style)
    LatinPattern(
        name="word_dictus_tusci",
        regex=r"(\w+)\s+dict\w+[,]?\s+quod\s+(?:ita\s+)?dic\w+\s+\w+\s+[Tt]usci",
        description="X dictus quod dicunt Tusci - X called because Tuscans say",
        confidence=0.90,
    ),
    # "in Etruria" context
    LatinPattern(
        name="in_etruria",
        regex=r"(\w+)\s+in\s+[Ee]truria",
        description="X in Etruria - X in Etruria (geographic context)",
        confidence=0.70,
    ),
]

# Tertiary patterns - medium confidence (need more context validation)
TERTIARY_PATTERNS = [
    LatinPattern(
        name="etrusca_origine",
        regex=r"(\w+)\s+[Ee]trusca\s+origin[ei]",
        description="X Etrusca origine - X of Etruscan origin",
        confidence=0.70,
    ),
    LatinPattern(
        name="ex_etrusco",
        regex=r"ex\s+[Ee]trusco\s+(\w+)",
        description="ex Etrusco X - from Etruscan X",
        confidence=0.70,
    ),
    LatinPattern(
        name="ab_etruscis",
        regex=r"ab\s+[Ee]truscis\s+(\w+)",
        description="ab Etruscis X - from the Etruscans X",
        confidence=0.70,
    ),
    LatinPattern(
        name="word_ab_etruscis",
        regex=r"(\w+)\s+ab\s+[Ee]truscis",
        description="X ab Etruscis - X from the Etruscans",
        confidence=0.75,
    ),
    LatinPattern(
        name="etruscum_verbum",
        regex=r"[Ee]truscum\s+verbum\s+(\w+)",
        description="Etruscum verbum X - Etruscan word X",
        confidence=0.75,
    ),
    LatinPattern(
        name="more_tusco",
        regex=r"more\s+[Tt]usco\s+(\w+)",
        description="more Tusco X - in Tuscan manner, X",
        confidence=0.65,
    ),
]

# Etymology patterns - for passages discussing word origins
ETYMOLOGY_PATTERNS = [
    LatinPattern(
        name="dictum_ab_etruscis",
        regex=r"(\w+)\s+dictum?\s+ab\s+[Ee]truscis",
        description="X dictum ab Etruscis - X said/named by the Etruscans",
        confidence=0.80,
    ),
    LatinPattern(
        name="vocabulum_etruscum",
        regex=r"(\w+)\s+vocabulum\s+[Ee]truscum",
        description="X vocabulum Etruscum - X is an Etruscan word",
        confidence=0.80,
    ),
    LatinPattern(
        name="vox_etrusca",
        regex=r"(\w+)\s+vox\s+[Ee]trusca",
        description="X vox Etrusca - X is an Etruscan word",
        confidence=0.80,
    ),
    LatinPattern(
        name="nomen_etruscum",
        regex=r"(\w+)\s+nomen\s+[Ee]truscum",
        description="X nomen Etruscum - X is an Etruscan name",
        confidence=0.80,
    ),
]

# Meaning extraction patterns - these capture word + meaning pairs
MEANING_PATTERNS = [
    LatinPattern(
        name="significat_etrusce",
        regex=r"(\w+)\s+significat\s+[Ee]trusc[ea]",
        description="X significat Etrusce - X means in Etruscan",
        confidence=0.85,
    ),
    LatinPattern(
        name="etrusce_est",
        regex=r"[Ee]trusc[ea]\s+(?:est|sunt)\s+(\w+)",
        description="Etrusce est X - in Etruscan it is X",
        confidence=0.80,
    ),
    LatinPattern(
        name="id_est_etrusce",
        regex=r"(\w+)\s+id\s+est\s+[Ee]trusc[ea]",
        description="X id est Etrusce - X that is, in Etruscan",
        confidence=0.75,
    ),
]

# Specific author patterns (variations used by known sources)
VARRO_PATTERNS = [
    LatinPattern(
        name="varro_tusci",
        regex=r"[Tt]usci\s+(?:enim\s+)?tibicinem\s+(\w+)\s+vocant",
        description="Varro's pattern: Tusci tibicinem X vocant",
        confidence=0.95,
    ),
]

FESTUS_PATTERNS = [
    LatinPattern(
        name="festus_etrusca",
        regex=r"[Ee]trusca\s+(?:voce|lingua)\s+(\w+)\s+(?:dicebatur|appellabatur)",
        description="Festus pattern: Etrusca voce X dicebatur",
        confidence=0.90,
    ),
]

# Collect all patterns
ALL_PATTERNS: list[LatinPattern] = (
    CORE_PATTERNS
    + SECONDARY_PATTERNS
    + TERTIARY_PATTERNS
    + ETYMOLOGY_PATTERNS
    + MEANING_PATTERNS
    + VARRO_PATTERNS
    + FESTUS_PATTERNS
)


def get_patterns_by_confidence(min_confidence: float = 0.0) -> list[LatinPattern]:
    """Get all patterns with confidence >= min_confidence."""
    return [p for p in ALL_PATTERNS if p.confidence >= min_confidence]


def get_pattern_by_name(name: str) -> Optional[LatinPattern]:
    """Get a pattern by its name."""
    for p in ALL_PATTERNS:
        if p.name == name:
            return p
    return None
