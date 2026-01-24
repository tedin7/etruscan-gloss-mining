"""Validation scoring pipeline for candidate glosses.

Combines multiple validation methods:
1. Pattern confidence (from extraction)
2. Cross-reference with known vocabulary
3. Linguistic plausibility (phonotactics)
4. Contextual coherence (TODO: LLM-based)

Each method contributes a weighted score to the final result.
"""

import json
from dataclasses import dataclass
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

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
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


class ValidationPipeline:
    """Pipeline for validating candidate glosses."""

    def __init__(
        self,
        repo: Repository,
        weight_pattern: float = WEIGHT_PATTERN,
        weight_cross_ref: float = WEIGHT_CROSS_REF,
        weight_linguistic: float = WEIGHT_LINGUISTIC,
        weight_context: float = WEIGHT_CONTEXT,
    ):
        """Initialize validation pipeline.

        Args:
            repo: Database repository
            weight_pattern: Weight for pattern confidence
            weight_cross_ref: Weight for cross-reference score
            weight_linguistic: Weight for linguistic plausibility
            weight_context: Weight for contextual coherence
        """
        self.repo = repo
        self.weights = {
            "pattern": weight_pattern,
            "cross_ref": weight_cross_ref,
            "linguistic": weight_linguistic,
            "context": weight_context,
        }

        # Initialize validators
        self.cross_ref_checker = CrossReferenceChecker(repo)
        self.linguistic_validator = LinguisticValidator()

    def _calculate_context_score(self, candidate: Candidate) -> float:
        """Calculate contextual coherence score.

        This is a simplified version. A full implementation would use
        LLM-based analysis of the context.

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

    def validate_candidate(self, candidate: Candidate) -> ValidationScore:
        """Validate a single candidate.

        Args:
            candidate: Candidate to validate

        Returns:
            ValidationScore with all scores
        """
        # 1. Pattern confidence (already computed during extraction)
        pattern_score = candidate.pattern_confidence or 0.5

        # 2. Cross-reference check
        cross_ref_result = self.cross_ref_checker.check(candidate.etruscan_word)
        cross_ref_score = cross_ref_result.score

        # 3. Linguistic plausibility
        linguistic_result = self.linguistic_validator.validate(candidate.etruscan_word)
        linguistic_score = linguistic_result.score

        # 4. Context score
        context_score = self._calculate_context_score(candidate)

        # Calculate weighted overall score
        overall_score = (
            pattern_score * self.weights["pattern"]
            + cross_ref_score * self.weights["cross_ref"]
            + linguistic_score * self.weights["linguistic"]
            + context_score * self.weights["context"]
        )

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
                details=json.dumps({"method": "rule_based"}),
            ),
        ]

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

        return {
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
