"""Quotation and gloss marker patterns.

Ancient authors often used structural markers to introduce glosses
without explicit language attribution:
- "id est" (that is)
- "hoc est" (this is)
- "sive" (or)
- "quem/quam vocant" (which they call)

These patterns can identify glossed terms even without Etruscan attribution.
"""

import re
from dataclasses import dataclass
from typing import Optional

from .latin_patterns import LatinPattern


# Explanatory gloss patterns
EXPLANATORY_PATTERNS = [
    LatinPattern(
        name="id_est_gloss",
        regex=r"(\w+)\s+id\s+est\s+(\w+)",
        description="X id est Y - X, that is, Y",
        confidence=0.45,
        meaning_group=2,
    ),
    LatinPattern(
        name="hoc_est_gloss",
        regex=r"(\w+)\s+hoc\s+est\s+(\w+)",
        description="X hoc est Y - X, this is, Y",
        confidence=0.45,
        meaning_group=2,
    ),
    LatinPattern(
        name="quod_est_gloss",
        regex=r"(\w+)\s+quod\s+est\s+(\w+)",
        description="X quod est Y - X, which is, Y",
        confidence=0.45,
        meaning_group=2,
    ),
    LatinPattern(
        name="id_est_word",
        regex=r"id\s+est\s+(\w+)",
        description="id est X - that is, X",
        confidence=0.40,
    ),
    LatinPattern(
        name="scilicet_gloss",
        regex=r"(\w+)\s+scilicet\s+(\w+)",
        description="X scilicet Y - X, namely Y",
        confidence=0.45,
        meaning_group=2,
    ),
    LatinPattern(
        name="videlicet_gloss",
        regex=r"(\w+)\s+videlicet\s+(\w+)",
        description="X videlicet Y - X, evidently Y",
        confidence=0.45,
        meaning_group=2,
    ),
]

# Alternative name patterns
ALTERNATIVE_PATTERNS = [
    LatinPattern(
        name="sive_alternative",
        regex=r"(\w+)\s+sive\s+(\w+)",
        description="X sive Y - X or Y (alternative names)",
        confidence=0.40,
    ),
    LatinPattern(
        name="vel_alternative",
        regex=r"(\w+)\s+vel\s+(\w+)",
        description="X vel Y - X or Y",
        confidence=0.35,
    ),
    LatinPattern(
        name="aut_alternative",
        regex=r"(\w+)\s+aut\s+(\w+)\s+(?:vocant|dicunt)",
        description="X aut Y vocant - they call X or Y",
        confidence=0.45,
    ),
    LatinPattern(
        name="quod_et",
        regex=r"(\w+)\s+quod\s+et\s+(\w+)",
        description="X quod et Y - X which also [called] Y",
        confidence=0.45,
    ),
]

# Unnamed speaker patterns
UNNAMED_SPEAKER_PATTERNS = [
    LatinPattern(
        name="quem_vocant",
        regex=r"(\w+)\s+quem\s+vocant",
        description="X quem vocant - X, which they call",
        confidence=0.50,
    ),
    LatinPattern(
        name="quam_vocant",
        regex=r"(\w+)\s+quam\s+vocant",
        description="X quam vocant - X, which they call",
        confidence=0.50,
    ),
    LatinPattern(
        name="quod_vocant",
        regex=r"(\w+)\s+quod\s+vocant",
        description="X quod vocant - X, which they call",
        confidence=0.50,
    ),
    LatinPattern(
        name="ut_vocant",
        regex=r"(\w+)\s+ut\s+vocant",
        description="X ut vocant - X, as they call [it]",
        confidence=0.50,
    ),
    LatinPattern(
        name="quos_appellant",
        regex=r"(\w+)\s+quos\s+appellant",
        description="X quos appellant - X, whom they call",
        confidence=0.50,
    ),
    LatinPattern(
        name="qui_dicuntur",
        regex=r"(\w+)\s+qui\s+dicuntur",
        description="X qui dicuntur - X, who are called",
        confidence=0.45,
    ),
    LatinPattern(
        name="quae_dicitur",
        regex=r"(\w+)\s+quae\s+dicitur",
        description="X quae dicitur - X, which is called",
        confidence=0.45,
    ),
]

# Definition patterns
DEFINITION_PATTERNS = [
    LatinPattern(
        name="significat",
        regex=r"(\w+)\s+significat\s+(\w+)",
        description="X significat Y - X means Y",
        confidence=0.50,
        meaning_group=2,
    ),
    LatinPattern(
        name="interpretatur",
        regex=r"(\w+)\s+interpretatur\s+(\w+)",
        description="X interpretatur Y - X is interpreted as Y",
        confidence=0.55,
        meaning_group=2,
    ),
    LatinPattern(
        name="dicitur_pro",
        regex=r"(\w+)\s+dicitur\s+pro\s+(\w+)",
        description="X dicitur pro Y - X is said for Y",
        confidence=0.45,
        meaning_group=2,
    ),
    LatinPattern(
        name="idem_quod",
        regex=r"(\w+)\s+idem\s+quod\s+(\w+)",
        description="X idem quod Y - X, the same as Y",
        confidence=0.50,
        meaning_group=2,
    ),
    LatinPattern(
        name="est_word_for",
        regex=r"(\w+)\s+est\s+(\w+)\s+(?:apud|pro)",
        description="X est Y apud - X is Y among...",
        confidence=0.45,
    ),
]

# Parenthetical gloss patterns
PARENTHETICAL_PATTERNS = [
    LatinPattern(
        name="parenthetical_quod",
        regex=r"\((\w+)\s+quod\s+(\w+)\)",
        description="(X quod Y) - parenthetical gloss",
        confidence=0.50,
    ),
    LatinPattern(
        name="parenthetical_id_est",
        regex=r"\(id\s+est\s+(\w+)\)",
        description="(id est X) - parenthetical definition",
        confidence=0.45,
    ),
]

# Collect all quotation patterns
ALL_QUOTATION_PATTERNS = (
    EXPLANATORY_PATTERNS
    + ALTERNATIVE_PATTERNS
    + UNNAMED_SPEAKER_PATTERNS
    + DEFINITION_PATTERNS
    + PARENTHETICAL_PATTERNS
)


@dataclass
class GlossMatch:
    """A match from a quotation/gloss pattern."""

    pattern_name: str
    term: str
    gloss: Optional[str]  # The explanation/meaning if captured
    full_match: str
    start_pos: int
    end_pos: int
    confidence: float
    has_meaning: bool = False


def get_quotation_patterns(min_confidence: float = 0.0) -> list[LatinPattern]:
    """Get all quotation patterns with confidence >= min_confidence."""
    return [p for p in ALL_QUOTATION_PATTERNS if p.confidence >= min_confidence]


def extract_gloss_pairs(text: str) -> list[GlossMatch]:
    """Extract term-gloss pairs from text using quotation patterns.

    This function finds glossed terms even without explicit language
    attribution, which can then be cross-referenced against known
    Etruscan vocabulary or validated linguistically.

    Args:
        text: The text to search

    Returns:
        List of GlossMatch objects
    """
    matches = []

    for pattern in ALL_QUOTATION_PATTERNS:
        compiled = pattern.compile()
        for m in compiled.finditer(text):
            term = m.group(pattern.word_group)
            gloss = None
            has_meaning = False

            if pattern.meaning_group:
                try:
                    gloss = m.group(pattern.meaning_group)
                    has_meaning = True
                except IndexError:
                    pass

            matches.append(GlossMatch(
                pattern_name=pattern.name,
                term=term,
                gloss=gloss,
                full_match=m.group(0),
                start_pos=m.start(),
                end_pos=m.end(),
                confidence=pattern.confidence,
                has_meaning=has_meaning,
            ))

    # Remove duplicates (same term at same position)
    seen = set()
    unique_matches = []
    for m in matches:
        key = (m.term.lower(), m.start_pos)
        if key not in seen:
            seen.add(key)
            unique_matches.append(m)

    return unique_matches


def is_likely_latin_gloss(term: str, gloss: Optional[str]) -> bool:
    """Check if a gloss pair appears to be Latin-to-Latin.

    Returns True if both term and gloss look like standard Latin,
    suggesting this is not a foreign word gloss.
    """
    if not gloss:
        return False

    # Common Latin endings that suggest both are Latin
    latin_endings = ["um", "us", "a", "ae", "orum", "arum", "is", "em", "am"]

    term_latin = any(term.lower().endswith(e) for e in latin_endings)
    gloss_latin = any(gloss.lower().endswith(e) for e in latin_endings)

    return term_latin and gloss_latin
