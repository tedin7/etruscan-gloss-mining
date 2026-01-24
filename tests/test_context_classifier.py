"""Tests for the ContextClassifier module."""

import json
import sys
import pytest
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from etruscan_miner.validation.context_classifier import (
    ContextClassifier,
    get_available_backends,
    SKLEARN_AVAILABLE,
)


# Sample training data for tests
SAMPLE_TRAINING_DATA = [
    # Positive (Etruscan) examples
    {"word": "subulo", "context_before": "Varro says that", "full_match": "Tusci vocant subulo",
     "context_after": "quod nos tibicinem appellamus", "label": "etruscan"},
    {"word": "lanista", "context_before": "gladiatorum magistri", "full_match": "lingua Etrusca lanista dicitur",
     "context_after": "carnifex enim praesidens", "label": "etruscan"},
    {"word": "atrium", "context_before": "nomen est Tuscum", "full_match": "atrium appellatur Etrusca voce",
     "context_after": "ab atro colore fumo", "label": "etruscan"},
    {"word": "histrio", "context_before": "quod Tusci", "full_match": "hister appellabantur histriones",
     "context_after": "qui ludi ab Etruria vocati", "label": "etruscan"},
    {"word": "cassis", "context_before": "galea ex corio fit", "full_match": "cassis Etruscum nomen est",
     "context_after": "ab aere fit", "label": "etruscan"},
    {"word": "mundus", "context_before": "locus subterraneus", "full_match": "mundus appellatur Tusco nomine",
     "context_after": "ut caeli mundus", "label": "etruscan"},
    # Negative (Latin) examples
    {"word": "rex", "context_before": "qui populo imperat", "full_match": "rex vocatur a regendo",
     "context_after": "quod alios regat", "label": "latin"},
    {"word": "consul", "context_before": "magistratus summus", "full_match": "consul dicitur a consulendo",
     "context_after": "civibus consulit", "label": "latin"},
    {"word": "senator", "context_before": "patres conscripti", "full_match": "senatores a senectute vocati",
     "context_after": "quod senes essent", "label": "latin"},
    {"word": "aqua", "context_before": "elementum liquidum", "full_match": "aqua dicta ab aequore",
     "context_after": "quod superficies eius aequa", "label": "latin"},
    {"word": "terra", "context_before": "elementum solidum", "full_match": "terra vocatur quod teritur",
     "context_after": "pedibus calcatur", "label": "latin"},
    {"word": "ignis", "context_before": "elementum calidum", "full_match": "ignis dicitur ab igne",
     "context_after": "quod omnia gignat", "label": "latin"},
]


class TestContextClassifierInitialization:
    """Tests for classifier initialization."""

    def test_initialization(self):
        """Test that classifier initializes correctly."""
        classifier = ContextClassifier()
        assert classifier is not None
        assert classifier.backend in get_available_backends()

    def test_predict_without_training_raises(self):
        """Test that predicting without training raises an error."""
        classifier = ContextClassifier()
        with pytest.raises(ValueError, match="not been trained"):
            classifier.predict("some context")

    def test_predict_proba_alias(self):
        """Test that predict_proba is an alias for predict."""
        classifier = ContextClassifier(backend='tfidf')
        classifier.train(SAMPLE_TRAINING_DATA)
        context = "Tusci vocant subulo"
        assert classifier.predict(context) == classifier.predict_proba(context)


@pytest.mark.skipif(not SKLEARN_AVAILABLE, reason="sklearn not available")
class TestContextClassifierTraining:
    """Tests for classifier training."""

    def test_train_basic(self):
        """Test basic training."""
        classifier = ContextClassifier(backend='tfidf')
        results = classifier.train(SAMPLE_TRAINING_DATA)

        assert results['backend'] == 'tfidf'
        assert results['train_size'] > 0
        assert results['val_size'] > 0
        assert 0 <= results['val_accuracy'] <= 1

    def test_train_produces_valid_predictions(self):
        """Test that trained classifier produces valid predictions."""
        classifier = ContextClassifier(backend='tfidf')
        classifier.train(SAMPLE_TRAINING_DATA)

        prob = classifier.predict("Tusci vocant subulo quod nos tibicinem")
        assert 0 <= prob <= 1

    def test_train_with_different_label_formats(self):
        """Test training with various label formats."""
        mixed_data = [
            {"word": "w1", "full_match": "Etrusca lingua dicitur", "label": "etruscan"},
            {"word": "w2", "full_match": "Etrusca voce appellatur", "label": 1},
            {"word": "w3", "full_match": "Tusci vocant nomen", "label": True},
            {"word": "w4", "full_match": "accept this Etruscan", "decision": "accept"},
            {"word": "w5", "full_match": "Etruria oritur verbum", "label": "accept"},
            {"word": "w6", "full_match": "a regendo dicitur", "label": "latin"},
            {"word": "w7", "full_match": "consul a consulendo", "label": 0},
            {"word": "w8", "full_match": "aqua dicta ab", "label": False},
            {"word": "w9", "full_match": "terra quod teritur", "label": "reject"},
            {"word": "w10", "full_match": "ignis ab igne", "label": "latin"},
            {"word": "w11", "full_match": "sol quod solus", "label": "latin"},
            {"word": "w12", "full_match": "luna a lucendo", "label": "latin"},
        ]
        classifier = ContextClassifier(backend='tfidf')
        results = classifier.train(mixed_data)
        assert results['backend'] == 'tfidf'

    def test_train_insufficient_data_raises(self):
        """Test that training with too few examples raises an error."""
        classifier = ContextClassifier(backend='tfidf')
        with pytest.raises(ValueError, match="at least 10"):
            classifier.train(SAMPLE_TRAINING_DATA[:5])


@pytest.mark.skipif(not SKLEARN_AVAILABLE, reason="sklearn not available")
class TestContextClassifierPersistence:
    """Tests for save/load functionality."""

    def test_save_and_load(self, tmp_path):
        """Test saving and loading a model."""
        # Train and save
        classifier = ContextClassifier(backend='tfidf')
        classifier.train(SAMPLE_TRAINING_DATA)
        classifier.save(tmp_path / "test_model")

        # Load and verify
        loaded = ContextClassifier.load(tmp_path / "test_model")
        assert loaded.backend == 'tfidf'

        # Verify predictions match
        context = "Tusci vocant subulo quod nos tibicinem"
        original_pred = classifier.predict(context)
        loaded_pred = loaded.predict(context)
        assert abs(original_pred - loaded_pred) < 0.001

    def test_load_nonexistent_raises(self):
        """Test that loading from non-existent path raises error."""
        with pytest.raises(FileNotFoundError):
            ContextClassifier.load(Path("/nonexistent/path"))


@pytest.mark.skipif(not SKLEARN_AVAILABLE, reason="sklearn not available")
class TestContextClassifierExplanation:
    """Tests for prediction explanation."""

    def test_explain_prediction(self):
        """Test that explain_prediction returns expected keys."""
        classifier = ContextClassifier(backend='tfidf')
        classifier.train(SAMPLE_TRAINING_DATA)

        explanation = classifier.explain_prediction("Tusci vocant subulo")

        assert 'probability' in explanation
        assert 'prediction' in explanation
        assert 'backend' in explanation
        assert explanation['prediction'] in ('etruscan', 'latin')
        assert 0 <= explanation['probability'] <= 1

    def test_explain_prediction_tfidf_features(self):
        """Test that TF-IDF backend provides feature explanations."""
        classifier = ContextClassifier(backend='tfidf')
        classifier.train(SAMPLE_TRAINING_DATA)

        explanation = classifier.explain_prediction("Tusci vocant subulo")

        assert 'etruscan_indicators' in explanation
        assert 'latin_indicators' in explanation


class TestGetAvailableBackends:
    """Tests for get_available_backends function."""

    def test_returns_list(self):
        """Test that function returns a list."""
        backends = get_available_backends()
        assert isinstance(backends, list)

    def test_tfidf_available_when_sklearn_available(self):
        """Test that tfidf is available when sklearn is available."""
        if SKLEARN_AVAILABLE:
            backends = get_available_backends()
            assert 'tfidf' in backends


@pytest.mark.skipif(not SKLEARN_AVAILABLE, reason="sklearn not available")
class TestContextClassifierPredictBatch:
    """Tests for batch prediction."""

    def test_predict_batch(self):
        """Test batch prediction returns correct number of results."""
        classifier = ContextClassifier(backend='tfidf')
        classifier.train(SAMPLE_TRAINING_DATA)

        contexts = [
            "Tusci vocant subulo",
            "rex vocatur a regendo",
            "Etrusca lingua dicitur",
        ]
        probs = classifier.predict_batch(contexts)

        assert len(probs) == len(contexts)
        assert all(0 <= p <= 1 for p in probs)
