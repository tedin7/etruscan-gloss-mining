"""Author reliability profiler for weighting discoveries.

Different ancient authors have different levels of reliability
when discussing Etruscan matters. Varro was a careful scholar
who consulted Etruscan sources; Isidore often invented fanciful
etymologies. This module provides author reliability scores.
"""

import re
from dataclasses import dataclass
from typing import Optional

from ..config import AUTHOR_RELIABILITY


@dataclass
class AuthorProfile:
    """Profile of an ancient author's reliability."""

    name: str
    canonical_name: str  # Normalized name for lookup
    reliability_score: float
    specialty: str  # e.g., "antiquarian", "encyclopedist", "historian"
    notes: str
    etruscan_expertise: bool = False  # Had direct knowledge of Etruscan


# Extended author profiles with expertise information
AUTHOR_PROFILES = {
    "varro": AuthorProfile(
        name="Marcus Terentius Varro",
        canonical_name="varro",
        reliability_score=0.95,
        specialty="antiquarian",
        notes="Most reliable source; consulted Etruscan books directly",
        etruscan_expertise=True,
    ),
    "verrius_flaccus": AuthorProfile(
        name="Verrius Flaccus",
        canonical_name="verrius_flaccus",
        reliability_score=0.92,
        specialty="grammarian",
        notes="Augustan scholar; source for Festus",
        etruscan_expertise=True,
    ),
    "festus": AuthorProfile(
        name="Sextus Pompeius Festus",
        canonical_name="festus",
        reliability_score=0.90,
        specialty="grammarian",
        notes="Epitomized Verrius Flaccus; preserves ancient material",
        etruscan_expertise=False,
    ),
    "pliny": AuthorProfile(
        name="Pliny the Elder",
        canonical_name="pliny",
        reliability_score=0.75,
        specialty="encyclopedist",
        notes="Compiled many sources; sometimes uncritical",
        etruscan_expertise=False,
    ),
    "dionysius": AuthorProfile(
        name="Dionysius of Halicarnassus",
        canonical_name="dionysius",
        reliability_score=0.70,
        specialty="historian",
        notes="Greek historian; biased but informed on Roman origins",
        etruscan_expertise=False,
    ),
    "strabo": AuthorProfile(
        name="Strabo",
        canonical_name="strabo",
        reliability_score=0.70,
        specialty="geographer",
        notes="Greek geographer; good on Etruscan geography",
        etruscan_expertise=False,
    ),
    "livy": AuthorProfile(
        name="Titus Livius",
        canonical_name="livy",
        reliability_score=0.65,
        specialty="historian",
        notes="Historian; some Etruscan material but not specialist",
        etruscan_expertise=False,
    ),
    "suetonius": AuthorProfile(
        name="Gaius Suetonius Tranquillus",
        canonical_name="suetonius",
        reliability_score=0.65,
        specialty="biographer",
        notes="Imperial biographer; occasional etymological notes",
        etruscan_expertise=False,
    ),
    "macrobius": AuthorProfile(
        name="Macrobius",
        canonical_name="macrobius",
        reliability_score=0.70,
        specialty="antiquarian",
        notes="Late antiquity; preserves earlier material on religion",
        etruscan_expertise=False,
    ),
    "servius": AuthorProfile(
        name="Servius",
        canonical_name="servius",
        reliability_score=0.65,
        specialty="grammarian",
        notes="Virgil commentator; some Etruscan religious material",
        etruscan_expertise=False,
    ),
    "arnobius": AuthorProfile(
        name="Arnobius",
        canonical_name="arnobius",
        reliability_score=0.60,
        specialty="apologist",
        notes="Christian apologist; preserves pagan religious terms",
        etruscan_expertise=False,
    ),
    "isidore": AuthorProfile(
        name="Isidore of Seville",
        canonical_name="isidore",
        reliability_score=0.40,
        specialty="encyclopedist",
        notes="Medieval; often fanciful etymologies, but preserves some ancient material",
        etruscan_expertise=False,
    ),
    "virgil": AuthorProfile(
        name="Publius Vergilius Maro",
        canonical_name="virgil",
        reliability_score=0.60,
        specialty="poet",
        notes="Epic poet; some Etruscan names and terms in Aeneid",
        etruscan_expertise=False,
    ),
    "ovid": AuthorProfile(
        name="Publius Ovidius Naso",
        canonical_name="ovid",
        reliability_score=0.55,
        specialty="poet",
        notes="Poet; Fasti contains some religious/calendar material",
        etruscan_expertise=False,
    ),
    "cato": AuthorProfile(
        name="Marcus Porcius Cato",
        canonical_name="cato",
        reliability_score=0.85,
        specialty="antiquarian",
        notes="Early Roman historian; Origines discussed Etruscan origins",
        etruscan_expertise=False,
    ),
    "cicero": AuthorProfile(
        name="Marcus Tullius Cicero",
        canonical_name="cicero",
        reliability_score=0.75,
        specialty="orator",
        notes="Discusses haruspicy and divination; educated perspective",
        etruscan_expertise=False,
    ),
}

# Name variants for author detection
AUTHOR_VARIANTS = {
    "varro": ["varro", "varroni", "varronem", "m. terentius varro", "terentius varro"],
    "festus": ["festus", "festo", "festum", "pompeius festus", "s. pompeius festus"],
    "pliny": ["plinius", "pliny", "plinio", "plinii", "pliny the elder", "c. plinius"],
    "dionysius": ["dionysius", "dionysii", "dionysio", "dionysius halicarnassensis"],
    "strabo": ["strabo", "straboni", "strabonem"],
    "livy": ["livius", "livy", "livii", "livio", "titus livius", "t. livius"],
    "isidore": ["isidorus", "isidore", "isidori", "isidoro", "isidore of seville"],
    "servius": ["servius", "servii", "servio"],
    "macrobius": ["macrobius", "macrobii", "macrobio"],
    "virgil": ["vergilius", "virgil", "vergilii", "vergilio", "publius vergilius"],
    "cicero": ["cicero", "ciceronis", "ciceroni", "m. tullius cicero"],
    "cato": ["cato", "catonis", "catoni", "m. porcius cato"],
    "suetonius": ["suetonius", "suetonii", "suetonio"],
    "arnobius": ["arnobius", "arnobii", "arnobio"],
    "ovid": ["ovidius", "ovid", "ovidii", "ovidio"],
}


class AuthorProfiler:
    """Profile authors for reliability scoring."""

    def __init__(self):
        """Initialize profiler."""
        self._build_variant_lookup()

    def _build_variant_lookup(self) -> None:
        """Build lookup from variant names to canonical names."""
        self.variant_to_canonical = {}
        for canonical, variants in AUTHOR_VARIANTS.items():
            for variant in variants:
                self.variant_to_canonical[variant.lower()] = canonical

    def identify_author(self, text: str) -> Optional[str]:
        """Identify author mentioned in text.

        Args:
            text: Text that may mention an author

        Returns:
            Canonical author name if found, None otherwise
        """
        text_lower = text.lower()

        # Check for author mentions
        for variant, canonical in self.variant_to_canonical.items():
            if variant in text_lower:
                return canonical

        return None

    def get_profile(self, author: str) -> Optional[AuthorProfile]:
        """Get profile for an author.

        Args:
            author: Author name (canonical or variant)

        Returns:
            AuthorProfile if found, None otherwise
        """
        canonical = self.variant_to_canonical.get(author.lower(), author.lower())
        return AUTHOR_PROFILES.get(canonical)

    def get_reliability(self, author: str) -> float:
        """Get reliability score for an author.

        Args:
            author: Author name

        Returns:
            Reliability score (0.0 to 1.0), defaults to 0.5 for unknown
        """
        profile = self.get_profile(author)
        if profile:
            return profile.reliability_score
        return AUTHOR_RELIABILITY.get("unknown", 0.5)

    def apply_author_weight(
        self,
        base_score: float,
        author: str,
        weight_factor: float = 0.3
    ) -> float:
        """Apply author reliability weight to a score.

        Args:
            base_score: Original confidence score
            author: Author name
            weight_factor: How much author reliability affects score (0-1)

        Returns:
            Weighted score
        """
        reliability = self.get_reliability(author)

        # Blend base score with reliability
        weighted = (base_score * (1 - weight_factor)) + (base_score * reliability * weight_factor)

        return min(1.0, max(0.0, weighted))

    def has_etruscan_expertise(self, author: str) -> bool:
        """Check if author had direct Etruscan expertise.

        Args:
            author: Author name

        Returns:
            True if author had direct Etruscan knowledge
        """
        profile = self.get_profile(author)
        return profile.etruscan_expertise if profile else False


def get_author_reliability(author: str) -> float:
    """Get reliability score for an author.

    Args:
        author: Author name

    Returns:
        Reliability score (0.0 to 1.0)
    """
    profiler = AuthorProfiler()
    return profiler.get_reliability(author)


def apply_author_weight(base_score: float, author: str, weight_factor: float = 0.3) -> float:
    """Apply author reliability weight to a score.

    Args:
        base_score: Original confidence score
        author: Author name
        weight_factor: How much author reliability affects score

    Returns:
        Weighted score
    """
    profiler = AuthorProfiler()
    return profiler.apply_author_weight(base_score, author, weight_factor)
