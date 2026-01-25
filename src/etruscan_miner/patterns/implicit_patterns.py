"""Implicit attribution patterns for detecting indirect Etruscan references.

These patterns capture cases where authors discuss Etruscan words without
explicitly naming the language, using phrases like "antiqui vocabant",
"prisci Latini dicebant", or "vocabulum rusticum".
"""

import re
from dataclasses import dataclass
from typing import Optional

from .latin_patterns import LatinPattern, PatternMatch


# Implicit attribution patterns - reference ancient/archaic usage
IMPLICIT_ANCIENT_PATTERNS = [
    LatinPattern(
        name="antiqui_vocant",
        regex=r"antiqui\s+voca(?:n)?t\s+(\w+)",
        description="antiqui vocant X - the ancients call X",
        confidence=0.60,
    ),
    LatinPattern(
        name="antiqui_dicebant",
        regex=r"antiqui\s+dice?bant\s+(\w+)",
        description="antiqui dicebant X - the ancients used to say X",
        confidence=0.60,
    ),
    LatinPattern(
        name="prisci_latini",
        regex=r"prisci\s+[Ll]atini\s+(?:dicebant|vocabant)\s+(\w+)",
        description="prisci Latini - early Latins said X (may preserve Etruscan substrate)",
        confidence=0.55,
    ),
    LatinPattern(
        name="veteres_dixerunt",
        regex=r"veteres\s+dix(?:erunt|ere)\s+(\w+)",
        description="veteres dixerunt X - the elders said X",
        confidence=0.55,
    ),
    LatinPattern(
        name="maiores_nostri",
        regex=r"maiores\s+nostri\s+(?:vocabant|dicebant|appellabant)\s+(\w+)",
        description="maiores nostri - our ancestors called X",
        confidence=0.50,
    ),
    LatinPattern(
        name="apud_antiquos",
        regex=r"apud\s+antiquos\s+(\w+)",
        description="apud antiquos X - among the ancients, X",
        confidence=0.55,
    ),
    LatinPattern(
        name="word_apud_veteres",
        regex=r"(\w+)\s+apud\s+veteres",
        description="X apud veteres - X among the elders",
        confidence=0.55,
    ),
]

# Rustic/archaic vocabulary patterns
RUSTIC_PATTERNS = [
    LatinPattern(
        name="vocabulum_rusticum",
        regex=r"vocabulum\s+rusticum\s+(\w+)",
        description="vocabulum rusticum X - rustic word X (often Etruscan substrate)",
        confidence=0.50,
    ),
    LatinPattern(
        name="word_rusticum",
        regex=r"(\w+)\s+(?:est\s+)?vocabulum\s+rusticum",
        description="X vocabulum rusticum - X is a rustic word",
        confidence=0.50,
    ),
    LatinPattern(
        name="verbum_obsoletum",
        regex=r"verbum\s+obsoletum\s+(\w+)",
        description="verbum obsoletum X - obsolete word X",
        confidence=0.45,
    ),
    LatinPattern(
        name="word_obsoletum",
        regex=r"(\w+)\s+(?:est\s+)?verbum\s+obsoletum",
        description="X est verbum obsoletum - X is an obsolete word",
        confidence=0.45,
    ),
    LatinPattern(
        name="vox_antiqua",
        regex=r"vox\s+antiqua\s+(\w+)",
        description="vox antiqua X - ancient word X",
        confidence=0.50,
    ),
    LatinPattern(
        name="vox_prisca",
        regex=r"vox\s+prisca\s+(\w+)",
        description="vox prisca X - archaic word X",
        confidence=0.50,
    ),
    LatinPattern(
        name="word_nunc_obsoletum",
        regex=r"(\w+)\s+nunc\s+obsolet\w+",
        description="X nunc obsoletum - X now obsolete",
        confidence=0.45,
    ),
]

# Foreign/barbaric word patterns
FOREIGN_PATTERNS = [
    LatinPattern(
        name="vox_peregrina",
        regex=r"vox\s+peregrina\s+(\w+)",
        description="vox peregrina X - foreign word X",
        confidence=0.55,
    ),
    LatinPattern(
        name="word_peregrinum",
        regex=r"(\w+)\s+(?:est\s+)?(?:vocabulum\s+)?peregrinum",
        description="X peregrinum - X is a foreign [word]",
        confidence=0.55,
    ),
    LatinPattern(
        name="verbum_barbarum",
        regex=r"verbum\s+barbarum\s+(\w+)",
        description="verbum barbarum X - barbarian word X",
        confidence=0.50,
    ),
    LatinPattern(
        name="word_barbarum",
        regex=r"(\w+)\s+(?:est\s+)?verbum\s+barbarum",
        description="X est verbum barbarum - X is a barbarian word",
        confidence=0.50,
    ),
    LatinPattern(
        name="non_latinum",
        regex=r"(\w+)\s+non\s+[Ll]atinum\s+(?:est|vocabulum)",
        description="X non Latinum - X is not Latin",
        confidence=0.55,
    ),
    LatinPattern(
        name="alienum_verbum",
        regex=r"alienum\s+verbum\s+(\w+)",
        description="alienum verbum X - foreign word X",
        confidence=0.50,
    ),
]

# Regional/Italic attribution patterns
ITALIC_PATTERNS = [
    LatinPattern(
        name="sabine_word",
        regex=r"[Ss]abini\s+(?:vocant|dicunt)\s+(\w+)",
        description="Sabini vocant X - Sabines call X (neighboring dialect)",
        confidence=0.60,
    ),
    LatinPattern(
        name="umbrian_word",
        regex=r"[Uu]mbri\s+(?:vocant|dicunt)\s+(\w+)",
        description="Umbri vocant X - Umbrians call X",
        confidence=0.60,
    ),
    LatinPattern(
        name="oscan_word",
        regex=r"[Oo]sci\s+(?:vocant|dicunt)\s+(\w+)",
        description="Osci vocant X - Oscans call X",
        confidence=0.55,
    ),
    LatinPattern(
        name="italic_lingua",
        regex=r"[Ii]talic(?:a|o)\s+lingua\s+(\w+)",
        description="Italica lingua X - in Italic language X",
        confidence=0.50,
    ),
    LatinPattern(
        name="faliscan_word",
        regex=r"[Ff]alisci\s+(?:vocant|dicunt)\s+(\w+)",
        description="Falisci vocant X - Faliscans call X",
        confidence=0.65,  # Close to Etruscan territory
    ),
]

# Unknown origin patterns
UNKNOWN_ORIGIN_PATTERNS = [
    LatinPattern(
        name="origo_incerta",
        regex=r"(\w+)\s+(?:cuius\s+)?origo\s+incerta",
        description="X origo incerta - X of uncertain origin",
        confidence=0.40,
    ),
    LatinPattern(
        name="etymon_ignotum",
        regex=r"(\w+)\s+(?:cuius\s+)?etymon\s+ignot\w+",
        description="X etymon ignotum - X of unknown etymology",
        confidence=0.40,
    ),
    LatinPattern(
        name="nescio_unde",
        regex=r"(\w+)\s+nescio\s+unde\s+(?:dictum|derivatum)",
        description="X nescio unde - X, I know not whence",
        confidence=0.35,
    ),
    LatinPattern(
        name="sine_origine",
        regex=r"(\w+)\s+sine\s+origine\s+(?:latina|certa)",
        description="X sine origine Latina - X without Latin origin",
        confidence=0.45,
    ),
]

# Collect all implicit patterns
ALL_IMPLICIT_PATTERNS = (
    IMPLICIT_ANCIENT_PATTERNS
    + RUSTIC_PATTERNS
    + FOREIGN_PATTERNS
    + ITALIC_PATTERNS
    + UNKNOWN_ORIGIN_PATTERNS
)


def get_implicit_patterns(min_confidence: float = 0.0) -> list[LatinPattern]:
    """Get all implicit patterns with confidence >= min_confidence."""
    return [p for p in ALL_IMPLICIT_PATTERNS if p.confidence >= min_confidence]


def requires_etruscan_context_boost(pattern_name: str) -> bool:
    """Check if pattern needs Etruscan context to boost confidence.

    Implicit patterns should have their confidence boosted when
    found in passages that also mention Etruria, Tuscans, etc.
    """
    return pattern_name in [p.name for p in ALL_IMPLICIT_PATTERNS]


@dataclass
class ImplicitMatch:
    """A match from an implicit pattern that needs context validation."""

    pattern_match: PatternMatch
    needs_context_boost: bool = True
    etruscan_context_found: bool = False
    boosted_confidence: float = 0.0

    def calculate_boosted_confidence(self, has_etruscan_context: bool) -> float:
        """Calculate confidence with optional context boost."""
        base = self.pattern_match.confidence
        if has_etruscan_context:
            # Boost by 20-30% if Etruscan context found
            self.etruscan_context_found = True
            self.boosted_confidence = min(0.90, base + 0.25)
        else:
            self.boosted_confidence = base
        return self.boosted_confidence
