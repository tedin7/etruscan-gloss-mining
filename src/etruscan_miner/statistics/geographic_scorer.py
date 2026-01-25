"""Geographic context scorer for Etruscan-related passages.

Words appearing in passages that mention Etruscan geographic locations
are more likely to be Etruscan terms. This module detects Etruscan
geographic context and provides confidence boosts.
"""

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class GeographicContext:
    """Geographic context information for a passage."""

    has_etruscan_geography: bool
    locations_found: list[str]
    boost_factor: float
    passage_snippet: str = ""


class GeographicScorer:
    """Score passages for Etruscan geographic context."""

    # Etruscan cities and regions
    ETRUSCAN_PLACES = {
        # Major cities (highest boost)
        "tier_1": [
            "tarquinii", "tarquinia", "tarquiniis", "tarquiniensis",
            "veii", "veios", "veientis", "veientium", "veiente",
            "caere", "caeretes", "caeretanus", "caeritis",
            "clusium", "clusini", "clusio", "clusinus",
            "volsinii", "volsiniis", "volsiniensis",
            "vulci", "vulcis", "vulcentis",
            "perusia", "perusini", "perusinus",
            "arretium", "arretini", "arretinus",
            "cortona", "cortonensis",
            "populonia", "populoniensis",
            "rusellae", "rusellanus",
            "vetulonia", "vetuloniensis",
            "volaterrae", "volaterrani",
        ],
        # Regions (high boost)
        "tier_2": [
            "etruria", "etruriae", "etruriam",
            "tuscia", "tusciae", "tusciam",
            "tyrrhenia", "tyrrheniae",
        ],
        # Related areas (medium boost)
        "tier_3": [
            "falerii", "faliscus", "faliscorum",
            "capena", "capenatis",
            "falisci", "faliscorum",
            "sutrium", "sutrinus",
            "nepet", "nepete",
        ],
        # Rivers and geography
        "tier_4": [
            "tiberis", "tiberim", "tybris",  # Tiber
            "arnus", "arnum",  # Arno
            "clanis", "clani",  # Clanis
            "trasumenus", "trasimeni",  # Lake Trasimene
        ],
    }

    # Etruscan ethnic/demonyms
    ETRUSCAN_ETHNONYMS = [
        "tuscus", "tusci", "tuscorum", "tusco", "tuscis",
        "etruscus", "etrusci", "etruscorum", "etrusco", "etruscis",
        "tyrrhenus", "tyrrheni", "tyrrhenorum", "tyrrheno", "tyrrhenis",
        "rasenna", "rasna",  # Etruscan self-designation
    ]

    # Boost factors by tier
    TIER_BOOSTS = {
        "tier_1": 0.20,  # Major Etruscan cities
        "tier_2": 0.18,  # Regions
        "tier_3": 0.12,  # Related areas
        "tier_4": 0.08,  # Geography
        "ethnonym": 0.15,  # Ethnic references
    }

    def __init__(self):
        """Initialize the scorer."""
        self._build_lookup()

    def _build_lookup(self) -> None:
        """Build efficient lookup structures."""
        self.place_to_tier = {}
        for tier, places in self.ETRUSCAN_PLACES.items():
            for place in places:
                self.place_to_tier[place.lower()] = tier

    def detect_context(self, text: str, context_window: int = 500) -> GeographicContext:
        """Detect Etruscan geographic context in text.

        Args:
            text: Text to analyze
            context_window: Characters to include in snippet

        Returns:
            GeographicContext with detection results
        """
        text_lower = text.lower()
        locations_found = []
        max_boost = 0.0

        # Check for place names
        for place, tier in self.place_to_tier.items():
            if place in text_lower:
                locations_found.append(place)
                boost = self.TIER_BOOSTS[tier]
                max_boost = max(max_boost, boost)

        # Check for ethnonyms
        for ethnonym in self.ETRUSCAN_ETHNONYMS:
            if ethnonym in text_lower:
                locations_found.append(ethnonym)
                boost = self.TIER_BOOSTS["ethnonym"]
                max_boost = max(max_boost, boost)

        # Calculate combined boost (diminishing returns for multiple)
        if len(locations_found) > 1:
            # Add small bonus for multiple mentions
            max_boost = min(0.30, max_boost + len(locations_found) * 0.02)

        # Extract snippet around first match
        snippet = ""
        if locations_found:
            pattern = re.compile(rf'\b{re.escape(locations_found[0])}\b', re.IGNORECASE)
            match = pattern.search(text)
            if match:
                start = max(0, match.start() - context_window // 2)
                end = min(len(text), match.end() + context_window // 2)
                snippet = text[start:end]

        return GeographicContext(
            has_etruscan_geography=len(locations_found) > 0,
            locations_found=list(set(locations_found)),  # Dedupe
            boost_factor=max_boost,
            passage_snippet=snippet,
        )

    def calculate_boost(self, text: str) -> float:
        """Calculate geographic boost factor for a text.

        Args:
            text: Text to analyze

        Returns:
            Boost factor (0.0 to 0.30)
        """
        context = self.detect_context(text)
        return context.boost_factor

    def is_etruscan_related(self, text: str) -> bool:
        """Quick check if text mentions Etruscan geography.

        Args:
            text: Text to check

        Returns:
            True if Etruscan geographic context found
        """
        text_lower = text.lower()

        # Quick check with most common terms first
        quick_terms = ["etruri", "tusci", "tuscus", "etrusc", "tyrrhen"]
        if any(term in text_lower for term in quick_terms):
            return True

        # Full check if quick check fails
        context = self.detect_context(text)
        return context.has_etruscan_geography


def detect_etruscan_geography(text: str) -> GeographicContext:
    """Detect Etruscan geographic context in text.

    Args:
        text: Text to analyze

    Returns:
        GeographicContext with results
    """
    scorer = GeographicScorer()
    return scorer.detect_context(text)


def calculate_geographic_boost(text: str) -> float:
    """Calculate geographic boost factor.

    Args:
        text: Text to analyze

    Returns:
        Boost factor (0.0 to 0.30)
    """
    scorer = GeographicScorer()
    return scorer.calculate_boost(text)
