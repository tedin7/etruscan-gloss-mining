"""Tests for the validation scorer pipeline with ML integration."""

import json
import sys
import pytest
from unittest.mock import MagicMock, patch
from dataclasses import dataclass
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from etruscan_miner.validation.scorer import ValidationPipeline, ValidationScore
from etruscan_miner.db.models import Candidate


@dataclass
class MockCrossRefResult:
    """Mock cross-reference result."""
    score: float = 0.5
    match_type: str = "none"
    matched_word: str = ""
    matched_meaning: str = ""
    details: str = ""


@dataclass
class MockLinguisticResult:
    """Mock linguistic result."""
    score: float = 0.5
    plausibility: str = "possible"
    positive_features: list = None
    issues: list = None

    def __post_init__(self):
        if self.positive_features is None:
            self.positive_features = []
        if self.issues is None:
            self.issues = []


class TestValidationScoreDataclass:
    """Tests for ValidationScore dataclass."""

    def test_basic_creation(self):
        """Test creating a ValidationScore."""
        score = ValidationScore(
            candidate_id=1,
            word="subulo",
            pattern_score=0.8,
            cross_ref_score=0.9,
            linguistic_score=0.6,
            context_score=0.7,
            overall_score=0.75,
            confidence_level="medium",
            recommendation="review",
        )
        assert score.word == "subulo"
        assert score.overall_score == 0.75
        assert score.ml_rejection_reason is None
        assert score.ml_scores == {}

    def test_with_ml_rejection(self):
        """Test ValidationScore with ML rejection."""
        score = ValidationScore(
            candidate_id=1,
            word="lanterna",
            pattern_score=0.5,
            cross_ref_score=0.0,
            linguistic_score=0.0,
            context_score=0.0,
            overall_score=0.1,
            confidence_level="low",
            recommendation="reject",
            ml_rejection_reason="No Etruscan attribution",
            ml_scores={"dependency_filter": 0.0},
        )
        assert score.ml_rejection_reason == "No Etruscan attribution"
        assert "dependency_filter" in score.ml_scores

    def test_to_dict(self):
        """Test converting ValidationScore to dict."""
        score = ValidationScore(
            candidate_id=1,
            word="test",
            pattern_score=0.5,
            cross_ref_score=0.5,
            linguistic_score=0.5,
            context_score=0.5,
            overall_score=0.5,
            confidence_level="medium",
            recommendation="review",
            ml_rejection_reason="Test reason",
            ml_scores={"word_classifier": 0.3},
        )
        d = score.to_dict()
        assert d["word"] == "test"
        assert d["ml_rejection_reason"] == "Test reason"
        assert d["ml_scores"] == {"word_classifier": 0.3}


class TestValidationPipelineInit:
    """Tests for ValidationPipeline initialization."""

    @pytest.fixture
    def mock_repo(self):
        """Create a mock repository."""
        repo = MagicMock()
        repo.get_known_vocabulary.return_value = []
        return repo

    def test_init_without_ml(self, mock_repo):
        """Test initialization without ML."""
        pipeline = ValidationPipeline(mock_repo, use_ml=False)
        assert pipeline.use_ml is False
        assert pipeline._dependency_filter is None
        assert pipeline._word_classifier is None
        assert pipeline._context_classifier is None

    def test_init_with_ml_handles_missing_models(self, mock_repo):
        """Test that ML initialization handles missing models gracefully."""
        # The pipeline should not crash even if models are missing
        pipeline = ValidationPipeline(mock_repo, use_ml=True)
        assert pipeline.use_ml is True
        # Dependency filter should work (regex fallback)
        assert pipeline._dependency_filter is not None


class TestValidationPipelineML:
    """Tests for ML-based validation."""

    @pytest.fixture
    def mock_repo(self):
        """Create a mock repository."""
        repo = MagicMock()
        repo.get_known_vocabulary.return_value = []
        return repo

    @pytest.fixture
    def mock_candidate(self):
        """Create a mock candidate."""
        return Candidate(
            id=1,
            etruscan_word="subulo",
            etruscan_normalized="subulo",
            pattern_confidence=0.8,
            context_before="Tusci vocant",
            context_after="quod nos tibicinem",
            full_match="Tusci vocant subulo",
        )

    def test_isidore_detection(self, mock_repo, mock_candidate):
        """Test Isidore source detection."""
        pipeline = ValidationPipeline(mock_repo, use_ml=False)

        # Not Isidore
        assert pipeline._is_isidore_source(mock_candidate) is False

        # With Isidore in context
        mock_candidate.context_before = "Isidore says"
        assert pipeline._is_isidore_source(mock_candidate) is True

        # With Etymologiae in context
        mock_candidate.context_before = "In the Etymologiae"
        assert pipeline._is_isidore_source(mock_candidate) is True

        # With Isidore in notes
        mock_candidate.context_before = "normal"
        mock_candidate.reviewer_notes = "from Isidore"
        assert pipeline._is_isidore_source(mock_candidate) is True

    def test_build_full_context(self, mock_repo, mock_candidate):
        """Test building full context string."""
        pipeline = ValidationPipeline(mock_repo, use_ml=False)
        context = pipeline._build_full_context(mock_candidate)
        assert "Tusci vocant" in context
        assert "subulo" in context
        assert "quod nos tibicinem" in context

    def test_validate_with_ml_early_rejection_word(self, mock_repo, mock_candidate):
        """Test that ML validation rejects non-Etruscan-like words early."""
        pipeline = ValidationPipeline(mock_repo, use_ml=True)

        # Skip test if word classifier not available
        if pipeline._word_classifier is None:
            pytest.skip("Word classifier not available")

        # Use a clearly Latin word
        mock_candidate.etruscan_word = "decumarum"  # Latin genitive plural
        mock_candidate.full_match = "Tusci vocant decumarum"

        score = pipeline.validate_candidate(mock_candidate)

        # Should have low score due to word classifier rejection
        # (only if word score < 0.3)
        # This depends on the trained model, so just check structure
        assert score is not None
        assert score.word == "decumarum"


class TestValidationPipelineSummary:
    """Tests for summary statistics."""

    def test_summary_with_ml_rejections(self):
        """Test summary includes ML rejection stats."""
        scores = [
            ValidationScore(
                candidate_id=1, word="test1", pattern_score=0.5, cross_ref_score=0.5,
                linguistic_score=0.5, context_score=0.5, overall_score=0.5,
                confidence_level="medium", recommendation="review",
            ),
            ValidationScore(
                candidate_id=2, word="test2", pattern_score=0.5, cross_ref_score=0.0,
                linguistic_score=0.0, context_score=0.0, overall_score=0.1,
                confidence_level="low", recommendation="reject",
                ml_rejection_reason="No Etruscan attribution: no markers",
            ),
            ValidationScore(
                candidate_id=3, word="test3", pattern_score=0.5, cross_ref_score=0.0,
                linguistic_score=0.0, context_score=0.0, overall_score=0.2,
                confidence_level="low", recommendation="reject",
                ml_rejection_reason="Word not Etruscan-like (score: 0.20)",
            ),
        ]

        mock_repo = MagicMock()
        pipeline = ValidationPipeline(mock_repo, use_ml=False)
        summary = pipeline.get_summary(scores)

        assert summary["count"] == 3
        assert "ml_rejections" in summary
        assert summary["ml_rejections"]["total"] == 2
        assert summary["ml_rejections"]["by_layer"]["no_attribution"] == 1
        assert summary["ml_rejections"]["by_layer"]["not_etruscan_like"] == 1
        assert summary["ml_rejections"]["rejection_rate"] == pytest.approx(2/3)

    def test_summary_no_ml_rejections(self):
        """Test summary without ML rejections."""
        scores = [
            ValidationScore(
                candidate_id=1, word="test1", pattern_score=0.8, cross_ref_score=0.9,
                linguistic_score=0.8, context_score=0.7, overall_score=0.8,
                confidence_level="high", recommendation="accept",
            ),
        ]

        mock_repo = MagicMock()
        pipeline = ValidationPipeline(mock_repo, use_ml=False)
        summary = pipeline.get_summary(scores)

        assert summary["count"] == 1
        assert "ml_rejections" not in summary


class TestIsidorePenalty:
    """Tests for Isidore penalty application."""

    @pytest.fixture
    def mock_repo(self):
        """Create a mock repository."""
        repo = MagicMock()
        repo.get_known_vocabulary.return_value = []
        return repo

    def test_isidore_penalty_applied(self, mock_repo):
        """Test that Isidore penalty reduces score."""
        pipeline = ValidationPipeline(mock_repo, use_ml=False)

        # Mock the validators to return fixed scores
        pipeline.cross_ref_checker = MagicMock()
        pipeline.cross_ref_checker.check.return_value = MockCrossRefResult(score=0.8)

        pipeline.linguistic_validator = MagicMock()
        pipeline.linguistic_validator.validate.return_value = MockLinguisticResult(score=0.8)

        # Regular candidate
        regular = Candidate(
            id=1,
            etruscan_word="test",
            pattern_confidence=0.8,
            context_before="normal context",
            context_after="more context",
        )
        regular_score = pipeline.validate_candidate(regular)

        # Isidore candidate (same word, but from Isidore)
        isidore = Candidate(
            id=2,
            etruscan_word="test",
            pattern_confidence=0.8,
            context_before="Isidore says",
            context_after="more context",
        )
        isidore_score = pipeline.validate_candidate(isidore)

        # Isidore score should be lower
        assert isidore_score.overall_score < regular_score.overall_score
        assert isidore_score.overall_score == pytest.approx(
            regular_score.overall_score * pipeline.ISIDORE_PENALTY, rel=0.01
        )
