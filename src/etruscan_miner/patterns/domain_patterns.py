"""Semantic domain patterns for Etruscan-heavy vocabulary areas.

Etruscan cultural influence on Rome was concentrated in specific domains:
- Divination (haruspicy, augury, lightning interpretation)
- Theatre (histrio, persona, scaena)
- Religion (lars, mania, genius, penates)
- Luxury goods (gold work, textiles, wine)
- Political terminology (certain magistracies)

Words found in passages discussing these domains are more likely to be Etruscan.
"""

import re
from dataclasses import dataclass
from typing import Optional

from .latin_patterns import LatinPattern


@dataclass
class DomainContext:
    """Semantic domain context for a passage or word."""

    domain: str
    keywords_found: list[str]
    boost_factor: float
    passage_text: Optional[str] = None


# Divination domain patterns
DIVINATION_PATTERNS = [
    LatinPattern(
        name="haruspex_term",
        regex=r"(?:haruspex|haruspic\w*)\s+(?:vocant|dicunt|appellant)\s+(\w+)",
        description="Term used by haruspices",
        confidence=0.80,
    ),
    LatinPattern(
        name="extispicium_vocab",
        regex=r"(?:in\s+)?extispicio\s+(\w+)\s+(?:dicitur|vocatur)",
        description="Term in extispicy (entrail reading)",
        confidence=0.80,
    ),
    LatinPattern(
        name="fulgur_term",
        regex=r"(?:fulgur|fulmen)\s+(?:quod|quem)\s+(\w+)\s+vocant",
        description="Lightning terminology",
        confidence=0.75,
    ),
    LatinPattern(
        name="disciplina_etrusca",
        regex=r"disciplina\s+[Ee]trusca\s+(\w+)",
        description="In Etruscan discipline X",
        confidence=0.85,
    ),
    LatinPattern(
        name="libri_haruspicini",
        regex=r"libr[io]s?\s+haruspicin\w*\s+(\w+)",
        description="In haruspical books X",
        confidence=0.80,
    ),
    LatinPattern(
        name="libri_fulgurales",
        regex=r"libr[io]s?\s+fulgural\w*\s+(\w+)",
        description="In fulgural books X",
        confidence=0.80,
    ),
    LatinPattern(
        name="iecur_term",
        regex=r"(?:iecur|iecore|hepat\w*)\s+(?:pars|locus)\s+(?:quae?m?\s+)?(\w+)",
        description="Liver terminology",
        confidence=0.75,
    ),
]

# Theatre domain patterns
THEATRE_PATTERNS = [
    LatinPattern(
        name="histrio_term",
        regex=r"(?:histrio|histrion\w*)\s+(?:vocant|dicunt)\s+(\w+)",
        description="Term used by actors/in theatre",
        confidence=0.75,
    ),
    LatinPattern(
        name="scaena_vocab",
        regex=r"(?:in\s+)?scaena\s+(\w+)\s+(?:dicitur|vocatur)",
        description="Stage terminology",
        confidence=0.70,
    ),
    LatinPattern(
        name="persona_term",
        regex=r"persona\s+(?:quae?m?\s+)?(\w+)\s+(?:vocant|appellant)",
        description="Mask/character terminology",
        confidence=0.70,
    ),
    LatinPattern(
        name="ludus_vocab",
        regex=r"(?:in\s+)?lud[io]s?\s+scaenic\w*\s+(\w+)",
        description="In scenic games X",
        confidence=0.65,
    ),
]

# Religion domain patterns
RELIGION_PATTERNS = [
    LatinPattern(
        name="sacerdos_etruscan",
        regex=r"sacerdotes?\s+[Ee]trusc\w*\s+(?:vocant|dicunt)\s+(\w+)",
        description="Etruscan priests call X",
        confidence=0.85,
    ),
    LatinPattern(
        name="ritu_tusco",
        regex=r"ritu\s+[Tt]usco\s+(\w+)",
        description="In Tuscan rite X",
        confidence=0.80,
    ),
    LatinPattern(
        name="lar_term",
        regex=r"[Ll]ar(?:es|ibus)?\s+(?:quos|quem)\s+(\w+)\s+vocant",
        description="Lar terminology",
        confidence=0.75,
    ),
    LatinPattern(
        name="genius_term",
        regex=r"genius\s+(?:quem|qui)\s+[Ee]trusc\w*\s+(\w+)",
        description="Genius in Etruscan X",
        confidence=0.80,
    ),
    LatinPattern(
        name="manes_term",
        regex=r"[Mm]anes\s+(?:quos|quem)\s+(\w+)\s+(?:vocant|dicunt)",
        description="Manes terminology",
        confidence=0.70,
    ),
    LatinPattern(
        name="templum_etruscan",
        regex=r"templ\w+\s+[Ee]trusc\w*\s+(?:more|ritu)\s+(\w+)",
        description="Temple in Etruscan manner X",
        confidence=0.75,
    ),
]

# Luxury/material culture patterns
LUXURY_PATTERNS = [
    LatinPattern(
        name="aurum_etruscan",
        regex=r"aur\w+\s+[Ee]trusc\w*\s+(\w+)",
        description="Etruscan gold terminology",
        confidence=0.70,
    ),
    LatinPattern(
        name="vas_etruscum",
        regex=r"vas[ai]?\s+[Ee]trusc\w*\s+(?:quod|quae)\s+(\w+)",
        description="Etruscan vessel X",
        confidence=0.75,
    ),
    LatinPattern(
        name="vestis_etrusca",
        regex=r"vest\w+\s+[Ee]trusc\w*\s+(?:quam|quod)\s+(\w+)",
        description="Etruscan garment X",
        confidence=0.70,
    ),
    LatinPattern(
        name="convivium_term",
        regex=r"(?:in\s+)?convivi[io]\s+[Ee]trusc\w*\s+(\w+)",
        description="Etruscan banquet terminology",
        confidence=0.70,
    ),
]

# Political/civic patterns
POLITICAL_PATTERNS = [
    LatinPattern(
        name="magistratus_etruscan",
        regex=r"magistrat\w+\s+[Ee]trusc\w*\s+(?:quem|qui)\s+(\w+)",
        description="Etruscan magistracy X",
        confidence=0.80,
    ),
    LatinPattern(
        name="rex_etruscan",
        regex=r"reg\w+\s+[Ee]trusc\w*\s+(?:vocant|dicunt)\s+(\w+)",
        description="Etruscan royal terminology",
        confidence=0.75,
    ),
    LatinPattern(
        name="lucumo_context",
        regex=r"lucumo(?:n\w*)?\s+(?:id\s+est|quod\s+est)\s+(\w+)",
        description="Lucumo (Etruscan title) meaning",
        confidence=0.85,
    ),
    LatinPattern(
        name="princeps_etruscan",
        regex=r"princip\w+\s+[Ee]trusc\w*\s+(\w+)",
        description="Etruscan leader terminology",
        confidence=0.70,
    ),
]

# Afterlife/funerary patterns
AFTERLIFE_PATTERNS = [
    LatinPattern(
        name="infernus_etruscan",
        regex=r"infern\w+\s+[Ee]trusc\w*\s+(\w+)",
        description="Etruscan underworld terminology",
        confidence=0.75,
    ),
    LatinPattern(
        name="sepulcrum_etruscan",
        regex=r"sepulcr\w+\s+[Ee]trusc\w*\s+(?:more|ritu)\s+(\w+)",
        description="Etruscan tomb terminology",
        confidence=0.70,
    ),
    LatinPattern(
        name="mania_term",
        regex=r"[Mm]ania\s+(?:quam|quae)\s+[Ee]trusc\w*\s+(\w+)",
        description="Mania (Etruscan death goddess) X",
        confidence=0.80,
    ),
    LatinPattern(
        name="funus_etruscan",
        regex=r"funer\w+\s+[Ee]trusc\w*\s+(?:more|ritu)\s+(\w+)",
        description="Etruscan funeral terminology",
        confidence=0.70,
    ),
]

# All domain patterns
ALL_DOMAIN_PATTERNS = (
    DIVINATION_PATTERNS
    + THEATRE_PATTERNS
    + RELIGION_PATTERNS
    + LUXURY_PATTERNS
    + POLITICAL_PATTERNS
    + AFTERLIFE_PATTERNS
)

# Domain keywords for context detection
DOMAIN_KEYWORDS = {
    "divination": [
        "haruspex", "haruspic", "extispic", "auspic", "augur", "omen",
        "fulgur", "fulmen", "prodig", "portentu", "iecur", "hepat",
        "disciplina", "libri", "fulgural", "ritual"
    ],
    "theatre": [
        "histrio", "histrion", "scaena", "scaenic", "persona", "actor",
        "ludus", "ludi", "fabula", "spectacul", "theatr", "mimus"
    ],
    "religion": [
        "sacerd", "ritus", "templum", "sacrific", "lar", "lares",
        "genius", "manes", "penates", "votiv", "sacr", "numen"
    ],
    "luxury": [
        "aurum", "argentum", "gemma", "vas", "vasis", "vestis",
        "conviv", "epul", "purpur", "ebur", "ivory"
    ],
    "political": [
        "magistrat", "rex", "regis", "lucumo", "princep", "praetor",
        "consul", "imperium", "fasces", "lictor"
    ],
    "afterlife": [
        "infern", "manes", "mania", "larva", "sepulcr", "tumul",
        "funus", "funer", "mort", "ciner", "urna"
    ],
}


def detect_domain_context(text: str) -> list[DomainContext]:
    """Detect semantic domains present in a text.

    Args:
        text: The passage text to analyze

    Returns:
        List of DomainContext objects for detected domains
    """
    from ..config import DOMAIN_BOOST

    contexts = []
    text_lower = text.lower()

    for domain, keywords in DOMAIN_KEYWORDS.items():
        found = [kw for kw in keywords if kw in text_lower]
        if found:
            boost = DOMAIN_BOOST.get(domain, 0.0)
            contexts.append(DomainContext(
                domain=domain,
                keywords_found=found,
                boost_factor=boost,
                passage_text=text[:200] if len(text) > 200 else text
            ))

    return contexts


def get_domain_patterns(domain: Optional[str] = None) -> list[LatinPattern]:
    """Get patterns for a specific domain or all domains."""
    if domain is None:
        return ALL_DOMAIN_PATTERNS

    domain_map = {
        "divination": DIVINATION_PATTERNS,
        "theatre": THEATRE_PATTERNS,
        "religion": RELIGION_PATTERNS,
        "luxury": LUXURY_PATTERNS,
        "political": POLITICAL_PATTERNS,
        "afterlife": AFTERLIFE_PATTERNS,
    }
    return domain_map.get(domain, [])


def calculate_domain_boost(word: str, passage: str) -> tuple[float, list[str]]:
    """Calculate confidence boost based on domain context.

    Args:
        word: The candidate word
        passage: The surrounding passage text

    Returns:
        Tuple of (total_boost, list of domain names)
    """
    contexts = detect_domain_context(passage)
    if not contexts:
        return 0.0, []

    total_boost = sum(c.boost_factor for c in contexts)
    domains = [c.domain for c in contexts]

    # Cap boost at 0.25
    return min(0.25, total_boost), domains
