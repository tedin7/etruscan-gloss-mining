"""Validation module for candidate gloss scoring."""

from .cross_reference import CrossRefResult, CrossReferenceChecker
from .dependency_filter import AttributionDetails, DependencyFilter, DepFilter
from .linguistic import LinguisticResult, LinguisticValidator
from .scorer import ValidationPipeline, ValidationScore
from .word_classifier import WordClassifier

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
    # Linguistic validation
    "LinguisticResult",
    "LinguisticValidator",
    # Scoring pipeline
    "ValidationPipeline",
    "ValidationScore",
]
