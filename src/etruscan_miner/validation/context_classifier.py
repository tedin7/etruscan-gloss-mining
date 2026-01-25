"""Context classifier for Etruscan gloss detection.

This module provides a machine learning classifier that determines whether
the context of a pattern match genuinely discusses Etruscan etymology vs
generic Latin/Greek etymology.

This is Layer 3 of the three-layer NLP filter for reducing false positives
in Etruscan gloss mining.

Backends (in order of preference with fallbacks):
1. DistilBERT multilingual - best accuracy, requires transformers + GPU
2. Sentence embeddings + sklearn - good accuracy, requires sentence-transformers
3. TF-IDF + LogisticRegression - baseline, only requires sklearn
"""

import json
import pickle
import warnings
from pathlib import Path
from typing import Any, Optional

import numpy as np

# Try to import sklearn (required for all backends)
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, classification_report
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

# Try to import transformers for DistilBERT
# Catch broader exceptions (OSError, etc.) since torch can fail in various ways
TRANSFORMERS_AVAILABLE = False
torch = None
AutoModelForSequenceClassification = None
AutoTokenizer = None
Trainer = None
TrainingArguments = None
EarlyStoppingCallback = None
Dataset = None

try:
    import torch as _torch
    from transformers import (
        AutoModelForSequenceClassification as _AutoModel,
        AutoTokenizer as _AutoTokenizer,
        Trainer as _Trainer,
        TrainingArguments as _TrainingArgs,
        EarlyStoppingCallback as _EarlyStopping,
    )
    from torch.utils.data import Dataset as _Dataset

    # Assign to module-level names only if import succeeded
    torch = _torch
    AutoModelForSequenceClassification = _AutoModel
    AutoTokenizer = _AutoTokenizer
    Trainer = _Trainer
    TrainingArguments = _TrainingArgs
    EarlyStoppingCallback = _EarlyStopping
    Dataset = _Dataset
    TRANSFORMERS_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    # ImportError: package not installed
    # OSError: shared library issues (common with torch)
    # RuntimeError: CUDA/device issues
    pass

# Try to import sentence-transformers for embeddings
SENTENCE_TRANSFORMERS_AVAILABLE = False
SentenceTransformer = None

try:
    from sentence_transformers import SentenceTransformer as _ST
    SentenceTransformer = _ST
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    pass


# Default model paths
DEFAULT_MODEL_DIR = Path(__file__).parent.parent.parent.parent / "data" / "models" / "context_classifier"


# Only define ContextDataset if transformers is available
# This avoids issues with Dataset being None
if TRANSFORMERS_AVAILABLE:
    class ContextDataset(Dataset):
        """PyTorch Dataset for context classification (used with DistilBERT)."""

        def __init__(self, texts: list[str], labels: list[int], tokenizer, max_length: int = 256):
            """Initialize the dataset.

            Args:
                texts: List of context strings
                labels: List of labels (1 = Etruscan, 0 = Latin/other)
                tokenizer: HuggingFace tokenizer
                max_length: Maximum sequence length
            """
            self.texts = texts
            self.labels = labels
            self.tokenizer = tokenizer
            self.max_length = max_length

        def __len__(self):
            return len(self.texts)

        def __getitem__(self, idx):
            text = self.texts[idx]
            label = self.labels[idx]

            encoding = self.tokenizer(
                text,
                truncation=True,
                padding='max_length',
                max_length=self.max_length,
                return_tensors='pt',
            )

            return {
                'input_ids': encoding['input_ids'].flatten(),
                'attention_mask': encoding['attention_mask'].flatten(),
                'labels': torch.tensor(label, dtype=torch.long),
            }
else:
    # Placeholder when transformers not available
    ContextDataset = None


class ContextClassifier:
    """ML classifier for determining if a context genuinely discusses Etruscan.

    Supports three backends with automatic fallback:
    1. DistilBERT multilingual - best accuracy
    2. Sentence embeddings + LogisticRegression - good accuracy
    3. TF-IDF + LogisticRegression - baseline

    Example:
        >>> classifier = ContextClassifier()
        >>> classifier.train(labeled_data)  # List of dicts with word, context_*, label
        >>> prob = classifier.predict("Tusci vocant subulo quod nos tibicinem")
        0.92  # High probability = genuinely Etruscan context
    """

    # Model name for DistilBERT backend
    DISTILBERT_MODEL = "distilbert-base-multilingual-cased"

    # Model name for sentence embeddings backend
    EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    def __init__(self, backend: Optional[str] = None):
        """Initialize the classifier.

        Args:
            backend: Force a specific backend ('distilbert', 'embeddings', 'tfidf').
                    If None, auto-selects the best available backend.
        """
        self._backend = backend
        self._model = None
        self._tokenizer = None
        self._vectorizer = None
        self._embedding_model = None
        self._is_trained = False

        # Determine the actual backend to use
        self._resolved_backend = self._resolve_backend(backend)

    def _resolve_backend(self, requested: Optional[str]) -> str:
        """Resolve which backend to use based on availability.

        Args:
            requested: User-requested backend or None for auto

        Returns:
            Backend name to use
        """
        if requested:
            # User specifically requested a backend
            if requested == 'distilbert':
                if TRANSFORMERS_AVAILABLE:
                    return 'distilbert'
                else:
                    raise ImportError(
                        "DistilBERT backend requires 'transformers' and 'torch'. "
                        "Install with: pip install transformers torch"
                    )
            elif requested == 'embeddings':
                if SENTENCE_TRANSFORMERS_AVAILABLE:
                    return 'embeddings'
                else:
                    raise ImportError(
                        "Embeddings backend requires 'sentence-transformers'. "
                        "Install with: pip install sentence-transformers"
                    )
            elif requested == 'tfidf':
                if SKLEARN_AVAILABLE:
                    return 'tfidf'
                else:
                    raise ImportError(
                        "TF-IDF backend requires 'scikit-learn'. "
                        "Install with: pip install scikit-learn"
                    )
            else:
                raise ValueError(f"Unknown backend: {requested}. "
                               f"Options: 'distilbert', 'embeddings', 'tfidf'")

        # Auto-select best available backend
        if TRANSFORMERS_AVAILABLE:
            return 'distilbert'
        elif SENTENCE_TRANSFORMERS_AVAILABLE and SKLEARN_AVAILABLE:
            return 'embeddings'
        elif SKLEARN_AVAILABLE:
            return 'tfidf'
        else:
            raise ImportError(
                "No ML backends available. Install at least one of:\n"
                "  - transformers torch (for DistilBERT)\n"
                "  - sentence-transformers scikit-learn (for embeddings)\n"
                "  - scikit-learn (for TF-IDF)"
            )

    @property
    def backend(self) -> str:
        """Return the active backend name."""
        return self._resolved_backend

    def _prepare_context(self, item: dict) -> str:
        """Prepare the full context string from a labeled item.

        Args:
            item: Dict with word, context_before, context_after, full_match
                  OR a pre-combined 'context' key

        Returns:
            Full context string
        """
        # Check for pre-combined context first
        if 'context' in item and item['context']:
            return item['context'].strip()

        context_before = item.get('context_before', '')
        context_after = item.get('context_after', '')
        full_match = item.get('full_match', '')

        # Combine: context_before + full_match + context_after
        parts = []
        if context_before:
            parts.append(context_before.strip())
        if full_match:
            parts.append(full_match.strip())
        if context_after:
            parts.append(context_after.strip())

        return ' '.join(parts)

    def train(self, labeled_data: list[dict], validation_split: float = 0.2) -> dict:
        """Train the classifier on labeled data.

        Args:
            labeled_data: List of dicts with keys:
                - word: The candidate word
                - context_before: Text before the match
                - context_after: Text after the match
                - full_match: The full pattern match
                - label: 'etruscan' or 'latin' (or 1/0)
            validation_split: Fraction of data to use for validation

        Returns:
            Dict with training results (accuracy, etc.)
        """
        if not labeled_data:
            raise ValueError("No labeled data provided for training")

        # Prepare texts and labels
        texts = []
        labels = []

        for item in labeled_data:
            context = self._prepare_context(item)
            if not context:
                continue

            label = item.get('label', item.get('decision', ''))
            if label in ('etruscan', 'accept', 1, True):
                labels.append(1)
            elif label in ('latin', 'reject', 0, False):
                labels.append(0)
            else:
                # Skip items with unclear labels
                continue

            texts.append(context)

        if len(texts) < 10:
            raise ValueError(f"Need at least 10 labeled examples, got {len(texts)}")

        print(f"Training {self._resolved_backend} backend with {len(texts)} examples...")
        print(f"  Positive (Etruscan): {sum(labels)}")
        print(f"  Negative (Latin): {len(labels) - sum(labels)}")

        # Train based on backend
        if self._resolved_backend == 'distilbert':
            return self._train_distilbert(texts, labels, validation_split)
        elif self._resolved_backend == 'embeddings':
            return self._train_embeddings(texts, labels, validation_split)
        else:  # tfidf
            return self._train_tfidf(texts, labels, validation_split)

    def _train_distilbert(self, texts: list[str], labels: list[int],
                         validation_split: float) -> dict:
        """Train using DistilBERT multilingual."""
        # Split data
        train_texts, val_texts, train_labels, val_labels = train_test_split(
            texts, labels, test_size=validation_split, random_state=42, stratify=labels
        )

        # Load tokenizer and model
        print(f"Loading {self.DISTILBERT_MODEL}...")
        self._tokenizer = AutoTokenizer.from_pretrained(self.DISTILBERT_MODEL)
        self._model = AutoModelForSequenceClassification.from_pretrained(
            self.DISTILBERT_MODEL,
            num_labels=2,
        )

        # Create datasets
        train_dataset = ContextDataset(train_texts, train_labels, self._tokenizer)
        val_dataset = ContextDataset(val_texts, val_labels, self._tokenizer)

        # Training arguments
        output_dir = DEFAULT_MODEL_DIR / "checkpoints"
        output_dir.mkdir(parents=True, exist_ok=True)

        training_args = TrainingArguments(
            output_dir=str(output_dir),
            num_train_epochs=3,
            per_device_train_batch_size=8,
            per_device_eval_batch_size=8,
            warmup_steps=100,
            weight_decay=0.01,
            logging_dir=str(output_dir / "logs"),
            logging_steps=10,
            eval_strategy="epoch",
            save_strategy="epoch",
            load_best_model_at_end=True,
            metric_for_best_model="eval_loss",
            report_to="none",  # Disable wandb etc
        )

        # Custom compute_metrics function
        def compute_metrics(eval_pred):
            predictions, labels = eval_pred
            predictions = np.argmax(predictions, axis=1)
            return {"accuracy": accuracy_score(labels, predictions)}

        # Train
        trainer = Trainer(
            model=self._model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            compute_metrics=compute_metrics,
            callbacks=[EarlyStoppingCallback(early_stopping_patience=2)],
        )

        print("Training DistilBERT...")
        trainer.train()

        # Evaluate
        eval_result = trainer.evaluate()
        self._is_trained = True

        # Get predictions for classification report
        predictions = trainer.predict(val_dataset)
        pred_labels = np.argmax(predictions.predictions, axis=1)

        print("\nValidation Results:")
        print(classification_report(val_labels, pred_labels,
                                   target_names=['Latin', 'Etruscan'],
                                   zero_division=0))

        return {
            'backend': 'distilbert',
            'train_size': len(train_texts),
            'val_size': len(val_texts),
            'val_accuracy': eval_result.get('eval_accuracy', 0),
            'val_loss': eval_result.get('eval_loss', 0),
        }

    def _train_embeddings(self, texts: list[str], labels: list[int],
                         validation_split: float) -> dict:
        """Train using sentence embeddings + LogisticRegression."""
        # Split data
        train_texts, val_texts, train_labels, val_labels = train_test_split(
            texts, labels, test_size=validation_split, random_state=42, stratify=labels
        )

        # Load embedding model
        print(f"Loading {self.EMBEDDING_MODEL}...")
        self._embedding_model = SentenceTransformer(self.EMBEDDING_MODEL)

        # Generate embeddings
        print("Generating embeddings for training data...")
        train_embeddings = self._embedding_model.encode(train_texts, show_progress_bar=True)
        val_embeddings = self._embedding_model.encode(val_texts, show_progress_bar=True)

        # Train classifier
        print("Training LogisticRegression on embeddings...")
        self._model = LogisticRegression(
            max_iter=1000,
            class_weight='balanced',
            random_state=42,
        )
        self._model.fit(train_embeddings, train_labels)

        # Evaluate
        val_predictions = self._model.predict(val_embeddings)
        val_accuracy = accuracy_score(val_labels, val_predictions)

        self._is_trained = True

        print("\nValidation Results:")
        print(classification_report(val_labels, val_predictions,
                                   target_names=['Latin', 'Etruscan'],
                                   zero_division=0))

        return {
            'backend': 'embeddings',
            'train_size': len(train_texts),
            'val_size': len(val_texts),
            'val_accuracy': val_accuracy,
        }

    def _train_tfidf(self, texts: list[str], labels: list[int],
                    validation_split: float) -> dict:
        """Train using TF-IDF + LogisticRegression."""
        # Split data
        train_texts, val_texts, train_labels, val_labels = train_test_split(
            texts, labels, test_size=validation_split, random_state=42, stratify=labels
        )

        # Initialize vectorizer
        self._vectorizer = TfidfVectorizer(
            ngram_range=(1, 3),
            max_features=5000,
            min_df=2,
            max_df=0.95,
        )

        # Fit and transform
        print("Training TF-IDF vectorizer...")
        train_features = self._vectorizer.fit_transform(train_texts)
        val_features = self._vectorizer.transform(val_texts)

        # Train classifier
        print("Training LogisticRegression...")
        self._model = LogisticRegression(
            max_iter=1000,
            class_weight='balanced',
            random_state=42,
        )
        self._model.fit(train_features, train_labels)

        # Evaluate
        val_predictions = self._model.predict(val_features)
        val_accuracy = accuracy_score(val_labels, val_predictions)

        self._is_trained = True

        print("\nValidation Results:")
        print(classification_report(val_labels, val_predictions,
                                   target_names=['Latin', 'Etruscan'],
                                   zero_division=0))

        return {
            'backend': 'tfidf',
            'train_size': len(train_texts),
            'val_size': len(val_texts),
            'val_accuracy': val_accuracy,
        }

    def predict(self, context: str) -> float:
        """Predict the probability that a context discusses Etruscan etymology.

        Args:
            context: The full context string to classify

        Returns:
            Probability between 0 and 1 (higher = more likely Etruscan)

        Raises:
            ValueError: If classifier has not been trained
        """
        if not self._is_trained:
            raise ValueError("Classifier has not been trained. Call train() or load() first.")

        if self._resolved_backend == 'distilbert':
            return self._predict_distilbert(context)
        elif self._resolved_backend == 'embeddings':
            return self._predict_embeddings(context)
        else:  # tfidf
            return self._predict_tfidf(context)

    def _predict_distilbert(self, context: str) -> float:
        """Predict using DistilBERT."""
        encoding = self._tokenizer(
            context,
            truncation=True,
            padding=True,
            max_length=256,
            return_tensors='pt',
        )

        # Move to same device as model
        device = next(self._model.parameters()).device
        encoding = {k: v.to(device) for k, v in encoding.items()}

        with torch.no_grad():
            outputs = self._model(**encoding)
            probs = torch.softmax(outputs.logits, dim=1)
            return float(probs[0, 1].cpu())  # Probability of class 1 (Etruscan)

    def _predict_embeddings(self, context: str) -> float:
        """Predict using sentence embeddings."""
        embedding = self._embedding_model.encode([context])
        probs = self._model.predict_proba(embedding)
        return float(probs[0, 1])  # Probability of class 1 (Etruscan)

    def _predict_tfidf(self, context: str) -> float:
        """Predict using TF-IDF."""
        features = self._vectorizer.transform([context])
        probs = self._model.predict_proba(features)
        return float(probs[0, 1])  # Probability of class 1 (Etruscan)

    def predict_proba(self, context: str) -> float:
        """Alias for predict() - returns probability that context is Etruscan.

        Args:
            context: The context string to classify

        Returns:
            Probability between 0 and 1
        """
        return self.predict(context)

    def predict_batch(self, contexts: list[str]) -> list[float]:
        """Predict probabilities for multiple contexts.

        Args:
            contexts: List of context strings to classify

        Returns:
            List of probabilities
        """
        if not self._is_trained:
            raise ValueError("Classifier has not been trained. Call train() or load() first.")

        return [self.predict(ctx) for ctx in contexts]

    def save(self, path: Optional[Path] = None) -> None:
        """Save the trained classifier to disk.

        Args:
            path: Directory to save the model. Defaults to data/models/context_classifier/
        """
        if not self._is_trained:
            raise ValueError("Cannot save untrained classifier")

        if path is None:
            path = DEFAULT_MODEL_DIR
        else:
            path = Path(path)

        path.mkdir(parents=True, exist_ok=True)

        # Save metadata
        metadata = {
            'backend': self._resolved_backend,
        }
        with open(path / 'metadata.json', 'w') as f:
            json.dump(metadata, f)

        # Save model based on backend
        if self._resolved_backend == 'distilbert':
            self._model.save_pretrained(path / 'model')
            self._tokenizer.save_pretrained(path / 'tokenizer')
        elif self._resolved_backend == 'embeddings':
            with open(path / 'classifier.pkl', 'wb') as f:
                pickle.dump(self._model, f)
            # Note: embedding model is loaded by name, not saved
        else:  # tfidf
            with open(path / 'vectorizer.pkl', 'wb') as f:
                pickle.dump(self._vectorizer, f)
            with open(path / 'classifier.pkl', 'wb') as f:
                pickle.dump(self._model, f)

        print(f"Model saved to {path}")

    @classmethod
    def load(cls, path: Optional[Path] = None) -> 'ContextClassifier':
        """Load a trained classifier from disk.

        Args:
            path: Directory to load the model from. Defaults to data/models/context_classifier/

        Returns:
            Loaded ContextClassifier instance
        """
        if path is None:
            path = DEFAULT_MODEL_DIR
        else:
            path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Model directory not found: {path}")

        # Load metadata
        with open(path / 'metadata.json', 'r') as f:
            metadata = json.load(f)

        backend = metadata['backend']

        # Create instance with the saved backend
        instance = cls(backend=backend)

        # Load model based on backend
        if backend == 'distilbert':
            instance._model = AutoModelForSequenceClassification.from_pretrained(
                path / 'model'
            )
            instance._tokenizer = AutoTokenizer.from_pretrained(path / 'tokenizer')
        elif backend == 'embeddings':
            with open(path / 'classifier.pkl', 'rb') as f:
                instance._model = pickle.load(f)
            # Load embedding model
            instance._embedding_model = SentenceTransformer(cls.EMBEDDING_MODEL)
        else:  # tfidf
            with open(path / 'vectorizer.pkl', 'rb') as f:
                instance._vectorizer = pickle.load(f)
            with open(path / 'classifier.pkl', 'rb') as f:
                instance._model = pickle.load(f)

        instance._is_trained = True
        return instance

    def explain_prediction(self, context: str, top_n: int = 10) -> dict:
        """Explain a prediction by showing feature contributions (TF-IDF only).

        Args:
            context: The context string
            top_n: Number of top features to show

        Returns:
            Dict with prediction and feature contributions
        """
        if not self._is_trained:
            raise ValueError("Classifier has not been trained")

        prob = self.predict(context)

        result = {
            'probability': prob,
            'prediction': 'etruscan' if prob > 0.5 else 'latin',
            'backend': self._resolved_backend,
        }

        # Feature explanations only available for TF-IDF backend
        if self._resolved_backend == 'tfidf':
            features = self._vectorizer.transform([context])
            feature_names = self._vectorizer.get_feature_names_out()
            coefficients = self._model.coef_[0]

            # Get feature contributions
            feature_values = features.toarray()[0]
            contributions = feature_values * coefficients

            # Get top positive and negative contributors
            sorted_indices = np.argsort(contributions)

            top_positive = []
            for idx in sorted_indices[-top_n:][::-1]:
                if contributions[idx] > 0:
                    top_positive.append((feature_names[idx], float(contributions[idx])))

            top_negative = []
            for idx in sorted_indices[:top_n]:
                if contributions[idx] < 0:
                    top_negative.append((feature_names[idx], float(contributions[idx])))

            result['etruscan_indicators'] = top_positive
            result['latin_indicators'] = top_negative

        return result


def get_available_backends() -> list[str]:
    """Get list of available backends in order of preference.

    Returns:
        List of available backend names
    """
    available = []
    if TRANSFORMERS_AVAILABLE:
        available.append('distilbert')
    if SENTENCE_TRANSFORMERS_AVAILABLE and SKLEARN_AVAILABLE:
        available.append('embeddings')
    if SKLEARN_AVAILABLE:
        available.append('tfidf')
    return available
