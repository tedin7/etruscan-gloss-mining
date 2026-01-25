"""Validation module for candidate gloss scoring."""

from .cross_reference import CrossRefResult, CrossReferenceChecker
from .dependency_filter import AttributionDetails, DependencyFilter, DepFilter
from .linguistic import LinguisticResult, LinguisticValidator
from .scorer import ValidationPipeline, ValidationScore
from .unified import UnifiedScore, UnifiedValidator
from .word_classifier import WordClassifier
from .context_classifier import ContextClassifier, get_available_backends

__all__ = [
    # Cross-reference
    "CrossRefResult",
    "CrossReferenceChecker",
    # Dependency filter (Layer 1)
    "AttributionDetails",
    "DependencyFilter",
    "DepFilter",
    # Word classifier (Layer 2)
    "WordClassifier",
    # Context classifier (Layer 3)
    "ContextClassifier",
    "get_available_backends",
    # Linguistic validation
    "LinguisticResult",
    "LinguisticValidator",
    # Scoring pipeline (legacy)
    "ValidationPipeline",
    "ValidationScore",
    # Unified scoring (new)
    "UnifiedScore",
    "UnifiedValidator",
]
