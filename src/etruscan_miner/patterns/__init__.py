"""Pattern matching module for Latin/Greek text mining.

This module provides multiple pattern types for detecting Etruscan glosses:

- latin_patterns: Core explicit attribution patterns (e.g., "Tusci vocant")
- greek_patterns: Greek text patterns (e.g., "Tyrrenoi kaleousi")
- implicit_patterns: Indirect attribution (e.g., "antiqui vocabant")
- domain_patterns: Semantic domain context (divination, theatre, religion)
- quotation_patterns: Gloss markers (e.g., "id est", "sive")
- metalinguistic: Etymology discussion detection
"""

from .latin_patterns import (
    LatinPattern,
    PatternMatch,
    ALL_PATTERNS,
    get_patterns_by_confidence,
    get_pattern_by_name,
)

from .extractor import GlossExtractor

# New pattern modules for expanded discovery
from .implicit_patterns import (
    ALL_IMPLICIT_PATTERNS,
    get_implicit_patterns,
    requires_etruscan_context_boost,
    ImplicitMatch,
)

from .domain_patterns import (
    ALL_DOMAIN_PATTERNS,
    DomainContext,
    detect_domain_context,
    get_domain_patterns,
    calculate_domain_boost,
)

from .quotation_patterns import (
    ALL_QUOTATION_PATTERNS,
    GlossMatch,
    get_quotation_patterns,
    extract_gloss_pairs,
)

from .metalinguistic import (
    ALL_METALINGUISTIC_PATTERNS,
    MetalinguisticPassage,
    get_metalinguistic_patterns,
    detect_metalinguistic_passages,
    extract_foreign_candidates_from_passage,
)

__all__ = [
    # Core patterns
    "LatinPattern",
    "PatternMatch",
    "ALL_PATTERNS",
    "get_patterns_by_confidence",
    "get_pattern_by_name",
    "GlossExtractor",
    # Implicit patterns
    "ALL_IMPLICIT_PATTERNS",
    "get_implicit_patterns",
    "requires_etruscan_context_boost",
    "ImplicitMatch",
    # Domain patterns
    "ALL_DOMAIN_PATTERNS",
    "DomainContext",
    "detect_domain_context",
    "get_domain_patterns",
    "calculate_domain_boost",
    # Quotation patterns
    "ALL_QUOTATION_PATTERNS",
    "GlossMatch",
    "get_quotation_patterns",
    "extract_gloss_pairs",
    # Metalinguistic patterns
    "ALL_METALINGUISTIC_PATTERNS",
    "MetalinguisticPassage",
    "get_metalinguistic_patterns",
    "detect_metalinguistic_passages",
    "extract_foreign_candidates_from_passage",
]
