"""Tests for the WordClassifier (Layer 2 character n-gram classifier)."""

import os
import sys
import tempfile
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from etruscan_miner.validation.word_classifier import WordClassifier, DEFAULT_MODEL_PATH


class TestWordClassifierInitialization:
    """Test WordClassifier initialization and basic properties."""

    def test_initialization(self):
        """Test that WordClassifier initializes correctly."""
        classifier = WordClassifier()
        assert classifier._is_trained is False
        assert classifier.bigram_vectorizer is None
        assert classifier.trigram_vectorizer is None
        assert classifier.classifier is None

    def test_predict_without_training_raises(self):
        """Test that predict raises error when not trained."""
        classifier = WordClassifier()
        with pytest.raises(ValueError, match="not been trained"):
            classifier.predict("test")

    def test_predict_proba_alias(self):
        """Test that predict_proba is an alias for predict."""
        # This test will use a trained model if available
        if DEFAULT_MODEL_PATH.exists():
            classifier = WordClassifier.load()
            word = "test"
            assert classifier.predict(word) == classifier.predict_proba(word)


class TestWordClassifierTraining:
    """Test WordClassifier training functionality."""

    def test_train_basic(self):
        """Test basic training with small dataset."""
        classifier = WordClassifier()

        # Small training set
        positive = ["ais", "clan", "puia", "zilath", "lauchum", "avil", "zal", "tiv"]
        negative = ["dominus", "servus", "bellum", "aqua", "terra", "imperium"]

        # This might warn about min_df but should work
        classifier.train(positive, negative)

        assert classifier._is_trained is True
        assert classifier.bigram_vectorizer is not None
        assert classifier.trigram_vectorizer is not None
        assert classifier.classifier is not None

    def test_train_produces_valid_predictions(self):
        """Test that training produces valid probability predictions."""
        classifier = WordClassifier()

        positive = ["ais", "clan", "puia", "zilath", "lauchum", "avil", "zal", "tiv"] * 10
        negative = ["dominus", "servus", "bellum", "aqua", "terra", "imperium"] * 10

        classifier.train(positive, negative)

        # All predictions should be between 0 and 1
        test_words = ["ais", "dominus", "test", "xyz"]
        for word in test_words:
            prob = classifier.predict(word)
            assert 0.0 <= prob <= 1.0, f"Probability {prob} for {word} out of range"


class TestWordClassifierFeatures:
    """Test handcrafted feature extraction."""

    def test_voiced_stop_detection(self):
        """Test detection of voiced stops (b, d, g)."""
        classifier = WordClassifier()

        # Words with voiced stops
        features_with = classifier._extract_handcrafted_features("bellum")
        features_without = classifier._extract_handcrafted_features("ais")

        # Feature 0 is has_voiced_stops
        assert features_with[0] == 1.0  # 'bellum' has 'b'
        assert features_without[0] == 0.0  # 'ais' has no voiced stops

    def test_o_detection(self):
        """Test detection of 'o' (rare in Etruscan)."""
        classifier = WordClassifier()

        features_with_o = classifier._extract_handcrafted_features("dominus")
        features_without_o = classifier._extract_handcrafted_features("ais")

        # Feature 1 is has_o
        assert features_with_o[1] == 1.0
        assert features_without_o[1] == 0.0

    def test_etruscan_endings(self):
        """Test detection of Etruscan endings."""
        classifier = WordClassifier()

        # Test -al ending (feature 2)
        features_al = classifier._extract_handcrafted_features("larθal")
        assert features_al[2] == 1.0  # ends_al

        # Test -na ending (feature 3)
        features_na = classifier._extract_handcrafted_features("velθna")
        assert features_na[3] == 1.0  # ends_na

    def test_latin_endings(self):
        """Test detection of Latin endings."""
        classifier = WordClassifier()

        # Test -um ending (feature 8)
        features_um = classifier._extract_handcrafted_features("bellum")
        assert features_um[8] == 1.0  # ends_um

        # Test -us ending (feature 9)
        features_us = classifier._extract_handcrafted_features("dominus")
        assert features_us[9] == 1.0  # ends_us


class TestWordClassifierPersistence:
    """Test model save/load functionality."""

    def test_save_and_load(self):
        """Test that model can be saved and loaded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = Path(tmpdir) / "test_model.pkl"

            # Train and save
            classifier = WordClassifier()
            positive = ["ais", "clan", "puia"] * 20
            negative = ["dominus", "servus", "bellum"] * 20
            classifier.train(positive, negative)
            classifier.save(model_path)

            assert model_path.exists()

            # Load and verify
            loaded = WordClassifier.load(model_path)
            assert loaded._is_trained is True

            # Predictions should match
            for word in ["ais", "dominus", "test"]:
                assert abs(classifier.predict(word) - loaded.predict(word)) < 0.001

    def test_load_nonexistent_raises(self):
        """Test that loading nonexistent model raises error."""
        with pytest.raises(FileNotFoundError):
            WordClassifier.load(Path("/nonexistent/path/model.pkl"))


@pytest.mark.skipif(
    not DEFAULT_MODEL_PATH.exists(),
    reason="Pre-trained model not available"
)
class TestPretrainedModel:
    """Test with pre-trained model (if available)."""

    def test_load_default_model(self):
        """Test loading the default pre-trained model."""
        classifier = WordClassifier.load()
        assert classifier._is_trained is True

    def test_known_etruscan_words_score_high(self):
        """Test that known Etruscan words score relatively high."""
        classifier = WordClassifier.load()

        # These are well-attested Etruscan words
        etruscan_words = ["clan", "puia", "zilath", "avil", "zal"]

        for word in etruscan_words:
            score = classifier.predict(word)
            # We expect at least moderate scores for real Etruscan words
            assert score > 0.3, f"{word} scored too low: {score}"

    def test_latin_words_score_low(self):
        """Test that typical Latin words score low."""
        classifier = WordClassifier.load()

        # These are clearly Latin words
        latin_words = ["dominus", "imperium", "bellum", "victoria"]

        for word in latin_words:
            score = classifier.predict(word)
            # Latin words should score low
            assert score < 0.5, f"{word} scored too high: {score}"

    def test_batch_prediction(self):
        """Test batch prediction functionality."""
        classifier = WordClassifier.load()

        words = ["ais", "dominus", "clan", "bellum"]
        scores = classifier.predict_batch(words)

        assert len(scores) == len(words)
        for score in scores:
            assert 0.0 <= score <= 1.0

    def test_feature_importance(self):
        """Test feature importance extraction."""
        classifier = WordClassifier.load()

        importance = classifier.get_feature_importance(top_n=10)

        assert "etruscan_indicators" in importance
        assert "latin_indicators" in importance
        assert len(importance["etruscan_indicators"]) > 0
        assert len(importance["latin_indicators"]) > 0

        # Etruscan indicators should have positive coefficients
        for name, coef in importance["etruscan_indicators"]:
            assert coef > 0, f"Etruscan indicator {name} has non-positive coefficient"

        # Latin indicators should have negative coefficients
        for name, coef in importance["latin_indicators"]:
            assert coef < 0, f"Latin indicator {name} has non-negative coefficient"
