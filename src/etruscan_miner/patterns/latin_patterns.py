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

# Isidore patterns - for Etymologiae-style derivations
ISIDORE_PATTERNS = [
    LatinPattern(
        name="isidore_derivatum",
        regex=r"(\w+)\s+ab?\s+(\w+)\s+derivat[ua]m",
        description="X ab Y derivatum - X derived from Y",
        confidence=0.70,
    ),
    LatinPattern(
        name="isidore_oriunda",
        regex=r"(\w+)\s+ex\s+(\w+)\s+oriund[ua]",
        description="X ex Y oriunda - X originating from Y",
        confidence=0.70,
    ),
    LatinPattern(
        name="isidore_dictum_quod",
        regex=r"(\w+)\s+dict[ua]m?\s+(?:est\s+)?quod",
        description="X dictum quod - X is called because",
        confidence=0.70,
    ),
    LatinPattern(
        name="isidore_vocatur",
        regex=r"(\w+)\s+(?:inde\s+)?vocat(?:ur|a)\s+(?:quod|quia)",
        description="X vocatur quod - X is called because",
        confidence=0.75,
    ),
    LatinPattern(
        name="isidore_appellatur",
        regex=r"(\w+)\s+appella(?:tur|ta)\s+(?:quod|quia|ab?)",
        description="X appellatur quod/ab - X is called because/from",
        confidence=0.70,
    ),
]

# Comparative patterns - bilingual glosses
COMPARATIVE_PATTERNS = [
    LatinPattern(
        name="etrusca_latina",
        regex=r"(\w+)\s+[Ee]trusc[ae],?\s+(\w+)\s+[Ll]atin[ae]",
        description="X Etrusce, Y Latine - X in Etruscan, Y in Latin",
        confidence=0.90,
        meaning_group=2,
    ),
    LatinPattern(
        name="dicunt_etrusci_nos",
        regex=r"(\w+)\s+dicunt\s+[Ee]trusci,?\s+(\w+)\s+(?:dicimus\s+)?nos",
        description="X dicunt Etrusci, Y nos - Etruscans say X, we say Y",
        confidence=0.85,
        meaning_group=2,
    ),
    LatinPattern(
        name="quod_latine_etrusce",
        regex=r"quod\s+[Ll]atine\s+(\w+),?\s+[Ee]trusce\s+(\w+)",
        description="quod Latine X, Etrusce Y - what in Latin is X, in Etruscan Y",
        confidence=0.90,
        word_group=2,
        meaning_group=1,
    ),
    LatinPattern(
        name="etrusce_latine",
        regex=r"[Ee]trusce\s+(\w+),?\s+[Ll]atine\s+(\w+)",
        description="Etrusce X, Latine Y - in Etruscan X, in Latin Y",
        confidence=0.90,
        meaning_group=2,
    ),
]

# Negative patterns - scholarly skepticism
NEGATIVE_PATTERNS = [
    LatinPattern(
        name="non_etrusca_sed",
        regex=r"(\w+)\s+non\s+[Ee]trusc[ae]\s+sed\s+[Ll]atin[ae]",
        description="X non Etrusca sed Latina - X not Etruscan but Latin",
        confidence=0.75,
    ),
    LatinPattern(
        name="quidam_putant_etrusca",
        regex=r"quidam\s+(?:putant|existimant)\s+(\w+)\s+[Ee]trusc[ae]",
        description="quidam putant X Etrusca - some think X is Etruscan",
        confidence=0.70,
    ),
    LatinPattern(
        name="falso_etrusca",
        regex=r"falso\s+(?:putant|dicunt)\s+(\w+)\s+[Ee]trusc[ae]",
        description="falso putant X Etrusca - they wrongly think X is Etruscan",
        confidence=0.65,
    ),
]

# Inscriptional patterns - epigraphic references
INSCRIPTIONAL_PATTERNS = [
    LatinPattern(
        name="in_etruscis_litteris",
        regex=r"in\s+[Ee]truscis\s+litteris\s+(\w+)",
        description="in Etruscis litteris X - in Etruscan letters/inscriptions X",
        confidence=0.85,
    ),
    LatinPattern(
        name="etrusco_charactere",
        regex=r"[Ee]trusco\s+character[ei]\s+(\w+)",
        description="Etrusco charactere X - in Etruscan script X",
        confidence=0.85,
    ),
    LatinPattern(
        name="litteris_tuscis",
        regex=r"litteris\s+[Tt]uscis\s+(\w+)",
        description="litteris Tuscis X - in Tuscan letters X",
        confidence=0.85,
    ),
]

# Authority patterns - citations of ancient scholars
AUTHORITY_PATTERNS = [
    LatinPattern(
        name="secundum_varronem",
        regex=r"secundum\s+[Vv]arronem\s+(\w+)\s+[Ee]trusc",
        description="secundum Varronem X Etrusc- - according to Varro, X is Etruscan",
        confidence=0.90,
    ),
    LatinPattern(
        name="ut_ait_festus",
        regex=r"ut\s+ait\s+[Ff]estus,?\s+(\w+)",
        description="ut ait Festus X - as Festus says, X",
        confidence=0.85,
    ),
    LatinPattern(
        name="teste_varrone",
        regex=r"teste\s+[Vv]arrone\s+(\w+)",
        description="teste Varrone X - with Varro as witness, X",
        confidence=0.90,
    ),
    LatinPattern(
        name="varro_dicit",
        regex=r"[Vv]arro\s+(?:ait|dicit|scribit)\s+(\w+)\s+[Ee]trusc",
        description="Varro dicit X Etrusc- - Varro says X is Etruscan",
        confidence=0.90,
    ),
    LatinPattern(
        name="apud_varronem",
        regex=r"apud\s+[Vv]arronem\s+(\w+)",
        description="apud Varronem X - in Varro, X",
        confidence=0.85,
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
    + ISIDORE_PATTERNS
    + COMPARATIVE_PATTERNS
    + NEGATIVE_PATTERNS
    + INSCRIPTIONAL_PATTERNS
    + AUTHORITY_PATTERNS
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
