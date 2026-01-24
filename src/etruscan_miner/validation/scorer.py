"""Validation scoring pipeline for candidate glosses.

Combines multiple validation methods:
1. Pattern confidence (from extraction)
2. Cross-reference with known vocabulary
3. Linguistic plausibility (phonotactics)
4. Contextual coherence (rule-based or ML-based)

Optional ML-based three-layer filter:
- Layer 1: Dependency parsing (Etruscan attribution check)
- Layer 2: Character n-gram classifier (word looks Etruscan)
- Layer 3: Context classifier (context discusses Etruscan etymology)

Each method contributes a weighted score to the final result.
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from ..config import (
    CONFIDENCE_HIGH,
    CONFIDENCE_MEDIUM,
    WEIGHT_CONTEXT,
    WEIGHT_CROSS_REF,
    WEIGHT_LINGUISTIC,
    WEIGHT_PATTERN,
)
from ..db.models import Candidate, Validation
from ..db.repository import Repository
from .cross_reference import CrossReferenceChecker, CrossRefResult
from .linguistic import LinguisticResult, LinguisticValidator

logger = logging.getLogger(__name__)


@dataclass
class ValidationScore:
    """Complete validation score for a candidate."""

    candidate_id: int
    word: str
    pattern_score: float
    cross_ref_score: float
    linguistic_score: float
    context_score: float
    overall_score: float
    confidence_level: str  # 'high', 'medium', 'low'
    recommendation: str  # 'accept', 'review', 'reject'

    # Detailed results
    cross_ref_result: Optional[CrossRefResult] = None
    linguistic_result: Optional[LinguisticResult] = None

    # ML filter results (optional, when use_ml=True)
    ml_rejection_reason: Optional[str] = None
    ml_scores: dict = field(default_factory=dict)  # layer -> score

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        result = {
            "candidate_id": self.candidate_id,
            "word": self.word,
            "pattern_score": self.pattern_score,
            "cross_ref_score": self.cross_ref_score,
            "linguistic_score": self.linguistic_score,
            "context_score": self.context_score,
            "overall_score": self.overall_score,
            "confidence_level": self.confidence_level,
            "recommendation": self.recommendation,
            "cross_ref_match": self.cross_ref_result.matched_word if self.cross_ref_result else None,
            "linguistic_plausibility": self.linguistic_result.plausibility if self.linguistic_result else None,
        }
        if self.ml_rejection_reason:
            result["ml_rejection_reason"] = self.ml_rejection_reason
        if self.ml_scores:
            result["ml_scores"] = self.ml_scores
        return result


class ValidationPipeline:
    """Pipeline for validating candidate glosses.

    Supports optional ML-based three-layer filtering when use_ml=True:
    - Layer 1: Dependency parsing - checks Etruscan attribution
    - Layer 2: Word classifier - checks if word looks Etruscan
    - Layer 3: Context classifier - checks if context is about Etruscan etymology
    """

    # Isidore penalty factor - his etymologies are often fanciful
    ISIDORE_PENALTY = 0.6

    def __init__(
        self,
        repo: Repository,
        weight_pattern: float = WEIGHT_PATTERN,
        weight_cross_ref: float = WEIGHT_CROSS_REF,
        weight_linguistic: float = WEIGHT_LINGUISTIC,
        weight_context: float = WEIGHT_CONTEXT,
        use_ml: bool = False,
    ):
        """Initialize validation pipeline.

        Args:
            repo: Database repository
            weight_pattern: Weight for pattern confidence
            weight_cross_ref: Weight for cross-reference score
            weight_linguistic: Weight for linguistic plausibility
            weight_context: Weight for contextual coherence
            use_ml: Enable ML-based three-layer filtering
        """
        self.repo = repo
        self.weights = {
            "pattern": weight_pattern,
            "cross_ref": weight_cross_ref,
            "linguistic": weight_linguistic,
            "context": weight_context,
        }
        self.use_ml = use_ml

        # Initialize validators
        self.cross_ref_checker = CrossReferenceChecker(repo)
        self.linguistic_validator = LinguisticValidator()

        # ML components (loaded lazily when use_ml=True)
        self._dependency_filter = None
        self._word_classifier = None
        self._context_classifier = None
        self._ml_initialized = False
        self._ml_warnings: list[str] = []

        if use_ml:
            self._initialize_ml_components()

    def _initialize_ml_components(self) -> None:
        """Initialize ML components for three-layer filtering.

        Handles missing models gracefully by warning and disabling that layer.
        """
        # Layer 1: Dependency filter (always available, uses regex fallback)
        try:
            from .dependency_filter import DependencyFilter
            self._dependency_filter = DependencyFilter()
            logger.info(f"Loaded dependency filter (method: {self._dependency_filter.method})")
        except Exception as e:
            msg = f"Could not load dependency filter: {e}"
            logger.warning(msg)
            self._ml_warnings.append(msg)

        # Layer 2: Word classifier (requires trained model)
        try:
            from .word_classifier import WordClassifier
            self._word_classifier = WordClassifier.load()
            logger.info("Loaded word classifier model")
        except FileNotFoundError:
            msg = "Word classifier model not found. Train with: python scripts/train_word_classifier.py"
            logger.warning(msg)
            self._ml_warnings.append(msg)
        except Exception as e:
            msg = f"Could not load word classifier: {e}"
            logger.warning(msg)
            self._ml_warnings.append(msg)

        # Layer 3: Context classifier (requires trained model)
        try:
            from .context_classifier import ContextClassifier
            self._context_classifier = ContextClassifier.load()
            logger.info(f"Loaded context classifier (backend: {self._context_classifier.backend})")
        except FileNotFoundError:
            msg = "Context classifier model not found. Train with: python scripts/train_context_classifier.py"
            logger.warning(msg)
            self._ml_warnings.append(msg)
        except Exception as e:
            msg = f"Could not load context classifier: {e}"
            logger.warning(msg)
            self._ml_warnings.append(msg)

        self._ml_initialized = True

        if self._ml_warnings:
            logger.warning(f"ML filtering partially enabled. Issues: {len(self._ml_warnings)}")
        else:
            logger.info("All ML components loaded successfully")

    @property
    def ml_warnings(self) -> list[str]:
        """Return any warnings from ML initialization."""
        return self._ml_warnings

    def _is_isidore_source(self, candidate: Candidate) -> bool:
        """Check if the candidate comes from Isidore's Etymologiae.

        Isidore's etymologies are often fanciful and unreliable, so we
        apply a penalty to candidates from this source.

        Args:
            candidate: The candidate to check

        Returns:
            True if the candidate is from Isidore
        """
        # Check reviewer notes (might contain source info)
        notes = (candidate.reviewer_notes or "").lower()
        if "isidore" in notes or "etymologiae" in notes or "isidor" in notes:
            return True

        # Check context for Isidore references
        context = (
            (candidate.context_before or "") + " " +
            (candidate.full_match or "") + " " +
            (candidate.context_after or "")
        ).lower()

        isidore_markers = ["isidore", "isidor", "etymologiae", "etym.", "isid."]
        return any(marker in context for marker in isidore_markers)

    def _build_full_context(self, candidate: Candidate) -> str:
        """Build the full context string from a candidate.

        Args:
            candidate: The candidate

        Returns:
            Full context string
        """
        parts = []
        if candidate.context_before:
            parts.append(candidate.context_before.strip())
        if candidate.full_match:
            parts.append(candidate.full_match.strip())
        if candidate.context_after:
            parts.append(candidate.context_after.strip())
        return " ".join(parts)

    def _calculate_context_score(self, candidate: Candidate) -> float:
        """Calculate contextual coherence score (rule-based).

        This is the baseline rule-based version. When use_ml=True and the
        context classifier is available, ML predictions are used instead.

        Args:
            candidate: Candidate to score

        Returns:
            Context score between 0 and 1
        """
        score = 0.5  # Neutral starting point

        # Check if context contains meaning hints
        context = (candidate.context_before or "") + " " + (candidate.context_after or "")
        context_lower = context.lower()

        # Positive indicators
        meaning_indicators = ["means", "significat", "dicitur", "vocant", "appellant", "that is"]
        for indicator in meaning_indicators:
            if indicator in context_lower:
                score += 0.1
                break

        # Check for translation patterns
        if "id est" in context_lower or "quod est" in context_lower:
            score += 0.15

        # Negative indicators (might be noise)
        noise_indicators = ["perhaps", "maybe", "some say", "fortasse", "nonnulli"]
        for indicator in noise_indicators:
            if indicator in context_lower:
                score -= 0.1
                break

        return max(0.0, min(1.0, score))

    def _validate_with_ml(self, candidate: Candidate) -> tuple[Optional[ValidationScore], dict]:
        """Run ML-based three-layer validation.

        Returns early with a low score if any layer rejects the candidate.

        Args:
            candidate: Candidate to validate

        Returns:
            Tuple of (ValidationScore if rejected early, ml_scores dict)
            If first element is None, continue with standard validation.
        """
        ml_scores = {}
        full_context = self._build_full_context(candidate)

        # Layer 1: Dependency filter - check Etruscan attribution
        if self._dependency_filter is not None:
            has_attribution = self._dependency_filter.has_etruscan_attribution(full_context)
            details = self._dependency_filter.get_attribution_details(full_context)
            ml_scores["dependency_filter"] = details.confidence

            if not has_attribution:
                # Early return with low score
                return ValidationScore(
                    candidate_id=candidate.id or 0,
                    word=candidate.etruscan_word,
                    pattern_score=candidate.pattern_confidence or 0.5,
                    cross_ref_score=0.0,
                    linguistic_score=0.0,
                    context_score=0.0,
                    overall_score=0.1,
                    confidence_level="low",
                    recommendation="reject",
                    ml_rejection_reason=f"No Etruscan attribution: {details.reason}",
                    ml_scores=ml_scores,
                ), ml_scores

        # Layer 2: Word classifier - check if word looks Etruscan
        if self._word_classifier is not None:
            word_score = self._word_classifier.predict(candidate.etruscan_word)
            ml_scores["word_classifier"] = word_score

            if word_score < 0.3:
                # Early return with low score
                return ValidationScore(
                    candidate_id=candidate.id or 0,
                    word=candidate.etruscan_word,
                    pattern_score=candidate.pattern_confidence or 0.5,
                    cross_ref_score=0.0,
                    linguistic_score=0.0,
                    context_score=0.0,
                    overall_score=0.2,
                    confidence_level="low",
                    recommendation="reject",
                    ml_rejection_reason=f"Word not Etruscan-like (score: {word_score:.2f})",
                    ml_scores=ml_scores,
                ), ml_scores

        # Layer 3: Context classifier - check if context is about Etruscan
        if self._context_classifier is not None:
            context_score = self._context_classifier.predict(full_context)
            ml_scores["context_classifier"] = context_score

        # All layers passed, continue with standard validation
        return None, ml_scores

    def validate_candidate(self, candidate: Candidate) -> ValidationScore:
        """Validate a single candidate.

        When use_ml=True, first runs three-layer ML filtering which can
        reject candidates early. Then runs standard validation pipeline.

        Args:
            candidate: Candidate to validate

        Returns:
            ValidationScore with all scores
        """
        ml_scores = {}

        # Run ML filtering if enabled
        if self.use_ml:
            early_rejection, ml_scores = self._validate_with_ml(candidate)
            if early_rejection is not None:
                return early_rejection

        # 1. Pattern confidence (already computed during extraction)
        pattern_score = candidate.pattern_confidence or 0.5

        # 2. Cross-reference check
        cross_ref_result = self.cross_ref_checker.check(candidate.etruscan_word)
        cross_ref_score = cross_ref_result.score

        # 3. Linguistic plausibility
        linguistic_result = self.linguistic_validator.validate(candidate.etruscan_word)
        linguistic_score = linguistic_result.score

        # 4. Context score - use ML context classifier if available, else rule-based
        if self.use_ml and "context_classifier" in ml_scores:
            context_score = ml_scores["context_classifier"]
        else:
            context_score = self._calculate_context_score(candidate)

        # Calculate weighted overall score
        overall_score = (
            pattern_score * self.weights["pattern"]
            + cross_ref_score * self.weights["cross_ref"]
            + linguistic_score * self.weights["linguistic"]
            + context_score * self.weights["context"]
        )

        # Apply Isidore penalty if applicable
        is_isidore = self._is_isidore_source(candidate)
        if is_isidore:
            overall_score *= self.ISIDORE_PENALTY
            logger.debug(f"Applied Isidore penalty to '{candidate.etruscan_word}': {overall_score:.2f}")

        # Determine confidence level
        if overall_score >= CONFIDENCE_HIGH:
            confidence_level = "high"
            recommendation = "accept"
        elif overall_score >= CONFIDENCE_MEDIUM:
            confidence_level = "medium"
            recommendation = "review"
        else:
            confidence_level = "low"
            recommendation = "reject"

        # Boost if cross-reference found exact match
        if cross_ref_result.match_type == "exact":
            confidence_level = "high"
            recommendation = "accept"

        return ValidationScore(
            candidate_id=candidate.id or 0,
            word=candidate.etruscan_word,
            pattern_score=pattern_score,
            cross_ref_score=cross_ref_score,
            linguistic_score=linguistic_score,
            context_score=context_score,
            overall_score=overall_score,
            confidence_level=confidence_level,
            recommendation=recommendation,
            cross_ref_result=cross_ref_result,
            linguistic_result=linguistic_result,
            ml_rejection_reason="Isidore source penalty applied" if is_isidore else None,
            ml_scores=ml_scores if ml_scores else {},
        )

    def validate_and_store(self, candidate: Candidate) -> ValidationScore:
        """Validate a candidate and store results in database.

        Args:
            candidate: Candidate to validate

        Returns:
            ValidationScore
        """
        score = self.validate_candidate(candidate)

        # Store individual validation scores
        validations = [
            Validation(
                candidate_id=candidate.id,
                validation_type="pattern",
                score=score.pattern_score,
                weight=self.weights["pattern"],
                details=json.dumps({"source": "extraction"}),
            ),
            Validation(
                candidate_id=candidate.id,
                validation_type="cross_reference",
                score=score.cross_ref_score,
                weight=self.weights["cross_ref"],
                details=json.dumps({
                    "match_type": score.cross_ref_result.match_type if score.cross_ref_result else None,
                    "matched_word": score.cross_ref_result.matched_word if score.cross_ref_result else None,
                }),
            ),
            Validation(
                candidate_id=candidate.id,
                validation_type="linguistic",
                score=score.linguistic_score,
                weight=self.weights["linguistic"],
                details=json.dumps({
                    "plausibility": score.linguistic_result.plausibility if score.linguistic_result else None,
                    "issues": score.linguistic_result.issues if score.linguistic_result else [],
                }),
            ),
            Validation(
                candidate_id=candidate.id,
                validation_type="context",
                score=score.context_score,
                weight=self.weights["context"],
                details=json.dumps({
                    "method": "ml" if self.use_ml and "context_classifier" in score.ml_scores else "rule_based"
                }),
            ),
        ]

        # Store ML validation results if present
        if score.ml_scores:
            for ml_type, ml_score_value in score.ml_scores.items():
                validations.append(
                    Validation(
                        candidate_id=candidate.id,
                        validation_type=ml_type,
                        score=ml_score_value,
                        weight=0.0,  # ML scores used for filtering, not weighting
                        details=json.dumps({
                            "rejection_reason": score.ml_rejection_reason,
                            "method": "ml_filter",
                        }),
                    )
                )

        for v in validations:
            self.repo.insert_validation(v)

        return score

    def validate_pending(self, limit: int = 100) -> list[ValidationScore]:
        """Validate all pending candidates.

        Args:
            limit: Maximum candidates to validate

        Returns:
            List of ValidationScore objects
        """
        candidates = self.repo.get_candidates_by_status("pending")[:limit]
        results = []

        for candidate in candidates:
            score = self.validate_and_store(candidate)
            results.append(score)

            # Update candidate status based on recommendation
            if score.recommendation == "accept":
                self.repo.update_candidate_status(
                    candidate.id, "accepted", f"Auto-accepted: {score.overall_score:.2f}"
                )
            elif score.recommendation == "review":
                self.repo.update_candidate_status(
                    candidate.id, "reviewing", f"Needs review: {score.overall_score:.2f}"
                )
            # Keep 'reject' as pending for manual review

        return results

    def get_summary(self, scores: list[ValidationScore]) -> dict:
        """Get summary statistics for a batch of scores.

        Args:
            scores: List of ValidationScore objects

        Returns:
            Summary dictionary
        """
        if not scores:
            return {"count": 0}

        summary = {
            "count": len(scores),
            "avg_overall": sum(s.overall_score for s in scores) / len(scores),
            "avg_pattern": sum(s.pattern_score for s in scores) / len(scores),
            "avg_cross_ref": sum(s.cross_ref_score for s in scores) / len(scores),
            "avg_linguistic": sum(s.linguistic_score for s in scores) / len(scores),
            "high_confidence": sum(1 for s in scores if s.confidence_level == "high"),
            "medium_confidence": sum(1 for s in scores if s.confidence_level == "medium"),
            "low_confidence": sum(1 for s in scores if s.confidence_level == "low"),
            "recommendations": {
                "accept": sum(1 for s in scores if s.recommendation == "accept"),
                "review": sum(1 for s in scores if s.recommendation == "review"),
                "reject": sum(1 for s in scores if s.recommendation == "reject"),
            },
        }

        # Add ML rejection statistics if ML filtering was used
        ml_rejections = [s for s in scores if s.ml_rejection_reason]
        if ml_rejections:
            summary["ml_rejections"] = {
                "total": len(ml_rejections),
                "by_layer": {
                    "no_attribution": sum(
                        1 for s in ml_rejections if "No Etruscan attribution" in (s.ml_rejection_reason or "")
                    ),
                    "not_etruscan_like": sum(
                        1 for s in ml_rejections if "not Etruscan-like" in (s.ml_rejection_reason or "")
                    ),
                    "isidore_penalty": sum(
                        1 for s in ml_rejections if "Isidore" in (s.ml_rejection_reason or "")
                    ),
                },
                "rejection_rate": len(ml_rejections) / len(scores) if scores else 0,
            }

        return summary
