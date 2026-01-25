"""Metalinguistic discussion detector.

Detects passages where ancient authors explicitly discuss language,
etymology, or word origins. Such passages are high-value targets
for finding foreign vocabulary, including Etruscan terms.
"""

import re
from dataclasses import dataclass
from typing import Optional

from .latin_patterns import LatinPattern


@dataclass
class MetalinguisticPassage:
    """A passage identified as discussing language/etymology."""

    text: str
    start_pos: int
    end_pos: int
    discussion_type: str  # 'etymology', 'definition', 'translation', 'comparison'
    trigger_phrase: str
    confidence: float
    candidate_words: list[str]  # Words that might be foreign terms


# Etymology discussion triggers
ETYMOLOGY_TRIGGERS = [
    LatinPattern(
        name="etymologia_discussion",
        regex=r"etymologi[ae]\s+(?:eius|huius|illius)?\s*(?:est|sunt)?\s*(\w+)",
        description="etymology discussion",
        confidence=0.70,
    ),
    LatinPattern(
        name="origo_verbi",
        regex=r"orig[oi]\s+(?:huius\s+)?verb[io]\s+(\w+)",
        description="origin of the word",
        confidence=0.70,
    ),
    LatinPattern(
        name="dictum_a",
        regex=r"(\w+)\s+dict\w+\s+(?:est\s+)?[ae]b?\s+(\w+)",
        description="X dictum a/ab Y - X said from Y",
        confidence=0.65,
    ),
    LatinPattern(
        name="appellatum_a",
        regex=r"(\w+)\s+appellat\w+\s+(?:est\s+)?[ae]b?\s+(\w+)",
        description="X appellatum a/ab Y - X named from Y",
        confidence=0.65,
    ),
    LatinPattern(
        name="derivatur",
        regex=r"(\w+)\s+derivat\w+\s+(?:est\s+)?(?:[ae]b?\s+)?(\w+)?",
        description="X derivatur - X is derived",
        confidence=0.65,
    ),
    LatinPattern(
        name="trahitur",
        regex=r"(\w+)\s+(?:trahitur|tractum)\s+(?:[ae]b?\s+)?(\w+)?",
        description="X trahitur - X is drawn from",
        confidence=0.60,
    ),
    LatinPattern(
        name="ductum",
        regex=r"(\w+)\s+ductum\s+(?:est\s+)?(?:[ae]b?\s+)?(\w+)?",
        description="X ductum - X is led/derived",
        confidence=0.60,
    ),
    LatinPattern(
        name="nomen_inde",
        regex=r"nomen\s+inde\s+(\w+)",
        description="nomen inde X - hence the name X",
        confidence=0.60,
    ),
    LatinPattern(
        name="unde_nomen",
        regex=r"unde\s+(?:et\s+)?nomen\s+(\w+)",
        description="unde nomen X - whence the name X",
        confidence=0.60,
    ),
]

# Language comparison triggers
LANGUAGE_TRIGGERS = [
    LatinPattern(
        name="lingua_context",
        regex=r"(?:in\s+)?lingua\s+(\w+)\s+(\w+)",
        description="in lingua X Y - in language X, [word] Y",
        confidence=0.70,
    ),
    LatinPattern(
        name="graece_latine",
        regex=r"[Gg]raece\s+(\w+),?\s+[Ll]atine\s+(\w+)",
        description="Graece X, Latine Y - in Greek X, in Latin Y",
        confidence=0.65,
    ),
    LatinPattern(
        name="latine_graece",
        regex=r"[Ll]atine\s+(\w+),?\s+[Gg]raece\s+(\w+)",
        description="Latine X, Graece Y - in Latin X, in Greek Y",
        confidence=0.65,
    ),
    LatinPattern(
        name="nos_dicimus",
        regex=r"(\w+)\s+nos\s+dicimus",
        description="X nos dicimus - we call X",
        confidence=0.55,
    ),
    LatinPattern(
        name="illi_vocant",
        regex=r"illi\s+(\w+)\s+vocant",
        description="illi X vocant - they call X",
        confidence=0.60,
    ),
    LatinPattern(
        name="barbari_dicunt",
        regex=r"barbari\s+(\w+)\s+dicunt",
        description="barbari X dicunt - barbarians say X",
        confidence=0.65,
    ),
]

# Definition/meaning triggers
DEFINITION_TRIGGERS = [
    LatinPattern(
        name="quid_sit",
        regex=r"quid\s+sit\s+(\w+)",
        description="quid sit X - what X is",
        confidence=0.55,
    ),
    LatinPattern(
        name="quid_significet",
        regex=r"quid\s+significet\s+(\w+)",
        description="quid significet X - what X means",
        confidence=0.60,
    ),
    LatinPattern(
        name="quod_significat",
        regex=r"(\w+)\s+quod\s+significat\s+(\w+)",
        description="X quod significat Y - X which means Y",
        confidence=0.60,
        meaning_group=2,
    ),
    LatinPattern(
        name="dicitur_quia",
        regex=r"(\w+)\s+dicitur\s+quia",
        description="X dicitur quia - X is called because",
        confidence=0.55,
    ),
    LatinPattern(
        name="vocatur_quod",
        regex=r"(\w+)\s+vocatur\s+quod",
        description="X vocatur quod - X is called because",
        confidence=0.55,
    ),
    LatinPattern(
        name="appellatur_quod",
        regex=r"(\w+)\s+appellatur\s+quod",
        description="X appellatur quod - X is named because",
        confidence=0.55,
    ),
]

# All metalinguistic patterns
ALL_METALINGUISTIC_PATTERNS = (
    ETYMOLOGY_TRIGGERS
    + LANGUAGE_TRIGGERS
    + DEFINITION_TRIGGERS
)


def get_metalinguistic_patterns() -> list[LatinPattern]:
    """Get all metalinguistic discussion patterns."""
    return ALL_METALINGUISTIC_PATTERNS


def detect_metalinguistic_passages(text: str, context_window: int = 100) -> list[MetalinguisticPassage]:
    """Detect passages that discuss language or etymology.

    Args:
        text: Full text to analyze
        context_window: Characters of context to extract around triggers

    Returns:
        List of MetalinguisticPassage objects
    """
    passages = []

    # Quick pre-filter for texts likely to contain etymology discussions
    etymology_hints = [
        "etymolog", "derivat", "dict", "vocat", "appell",
        "lingua", "signific", "origin", "nomen"
    ]
    text_lower = text.lower()
    if not any(hint in text_lower for hint in etymology_hints):
        return []

    for pattern in ALL_METALINGUISTIC_PATTERNS:
        compiled = pattern.compile()

        for m in compiled.finditer(text):
            # Extract context
            start = max(0, m.start() - context_window)
            end = min(len(text), m.end() + context_window)
            passage_text = text[start:end]

            # Determine discussion type
            if pattern.name in [p.name for p in ETYMOLOGY_TRIGGERS]:
                disc_type = "etymology"
            elif pattern.name in [p.name for p in LANGUAGE_TRIGGERS]:
                disc_type = "translation"
            else:
                disc_type = "definition"

            # Extract candidate words (all words in the match)
            candidates = re.findall(r'\b(\w{3,})\b', m.group(0))
            # Filter out common Latin function words
            stopwords = {
                "est", "sunt", "quod", "quia", "quae", "quem", "qui",
                "hoc", "haec", "hic", "ille", "illa", "illud",
                "enim", "autem", "sed", "nec", "neque", "vel",
                "unde", "inde", "idem", "eius", "huius"
            }
            candidates = [w for w in candidates if w.lower() not in stopwords]

            passages.append(MetalinguisticPassage(
                text=passage_text,
                start_pos=start,
                end_pos=end,
                discussion_type=disc_type,
                trigger_phrase=m.group(0),
                confidence=pattern.confidence,
                candidate_words=candidates,
            ))

    # Merge overlapping passages
    merged = merge_overlapping_passages(passages)

    return merged


def merge_overlapping_passages(passages: list[MetalinguisticPassage]) -> list[MetalinguisticPassage]:
    """Merge passages that overlap in the text."""
    if not passages:
        return []

    # Sort by start position
    sorted_passages = sorted(passages, key=lambda p: p.start_pos)

    merged = [sorted_passages[0]]

    for passage in sorted_passages[1:]:
        last = merged[-1]

        # Check for overlap
        if passage.start_pos <= last.end_pos:
            # Merge: extend end, combine candidates, take higher confidence
            last.end_pos = max(last.end_pos, passage.end_pos)
            last.candidate_words = list(set(last.candidate_words + passage.candidate_words))
            last.confidence = max(last.confidence, passage.confidence)
        else:
            merged.append(passage)

    return merged


def extract_foreign_candidates_from_passage(passage: MetalinguisticPassage) -> list[str]:
    """Extract likely foreign word candidates from a metalinguistic passage.

    Uses heuristics to identify which words in the passage might be
    the foreign terms being discussed:
    - Words immediately following trigger phrases
    - Words that don't look like standard Latin
    - Words in quotation-like contexts
    """
    from ..validation.linguistic import LinguisticValidator

    candidates = []
    validator = LinguisticValidator()

    for word in passage.candidate_words:
        # Quick Latin check
        if _is_common_latin(word):
            continue

        # Check phonotactics
        result = validator.validate(word)
        if result.plausibility in ("high", "medium"):
            candidates.append(word)
        elif result.plausibility == "low" and not _has_obvious_latin_morphology(word):
            candidates.append(word)

    return candidates


def _is_common_latin(word: str) -> bool:
    """Check if word is common Latin vocabulary."""
    common_latin = {
        "lingua", "verbum", "vocabulum", "nomen", "vox",
        "dicere", "vocare", "appellare", "significare",
        "latinus", "graecus", "romanus"
    }
    return word.lower() in common_latin


def _has_obvious_latin_morphology(word: str) -> bool:
    """Check for obvious Latin word endings."""
    latin_endings = [
        "orum", "arum", "ibus", "orum", "onis", "ionis",
        "mentum", "tudo", "itas", "atio", "itio"
    ]
    return any(word.lower().endswith(e) for e in latin_endings)
