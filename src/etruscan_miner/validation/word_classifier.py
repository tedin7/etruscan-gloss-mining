"""Character n-gram classifier for Etruscan word classification.

This module provides a machine learning classifier that determines whether
a word "looks" Etruscan based on character-level features. It uses:
- Character 2-grams and 3-grams with TF-IDF weighting
- Phonotactic features (voiced stops, typical endings)
- Vowel/consonant patterns

This is Layer 2 of the three-layer NLP filter for reducing false positives
in Etruscan gloss mining.
"""

import pickle
import re
from pathlib import Path
from typing import Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from scipy.sparse import hstack, csr_matrix


# Default model path
DEFAULT_MODEL_PATH = Path(__file__).parent.parent.parent.parent / "data" / "models" / "word_classifier.pkl"


class WordClassifier:
    """Character n-gram classifier for determining if a word looks Etruscan.

    Features used:
    - Character 2-grams and 3-grams (TF-IDF weighted)
    - Presence of voiced stops (b, d, g) - Etruscan lacks these
    - Common Etruscan word endings (-al, -na, -s, -i, -a)
    - Vowel/consonant patterns and ratios

    Example:
        >>> classifier = WordClassifier()
        >>> classifier.train(etruscan_words, latin_words)
        >>> classifier.predict('subulo')  # Should be high (Etruscan-like)
        0.85
        >>> classifier.predict('lanterna')  # Should be low (Latin-like)
        0.25
    """

    # Voiced stops - rare/absent in native Etruscan
    VOICED_STOPS = set('bdg')

    # Common Etruscan word endings
    ETRUSCAN_ENDINGS = [
        'al', 'el', 'il', 'ul',  # Genitive -al
        'na', 'ne', 'ni',  # Adjectival -na
        'as', 'es', 'is', 'us',  # -s endings
        'a', 'e', 'i', 'u',  # Vowel endings
        'ar', 'er', 'ir', 'ur',  # Plural -r
        'ce', 'the', 'che',  # Past tense
    ]

    # Latin-typical endings (negative indicators)
    LATIN_ENDINGS = [
        'um', 'us', 'am', 'em', 'im',  # Declension endings
        'orum', 'arum', 'ibus',  # Plural endings
        'tion', 'sion', 'ment',  # Abstract noun endings
        'tas', 'tis', 'nus',  # Adjective/noun endings
        'que', 'bus',  # Other Latin
    ]

    # Etruscan vowels (note: 'o' is rare, usually written as 'u')
    VOWELS = set('aeiou')

    def __init__(self):
        """Initialize the classifier."""
        self.bigram_vectorizer: Optional[TfidfVectorizer] = None
        self.trigram_vectorizer: Optional[TfidfVectorizer] = None
        self.classifier: Optional[LogisticRegression] = None
        self._is_trained = False

    def _add_char_boundaries(self, word: str) -> str:
        """Add word boundary markers for n-gram extraction."""
        return f'^{word.lower()}$'

    def _extract_handcrafted_features(self, word: str) -> np.ndarray:
        """Extract handcrafted linguistic features from a word.

        Features:
        0. Has voiced stops (b, d, g)
        1. Has 'o' (rare in Etruscan, usually 'u')
        2-7. Etruscan ending matches (top 6)
        8-13. Latin ending matches (top 6)
        14. Vowel ratio
        15. Word length (normalized)
        16. Has doubled consonants
        17. Has 'qu' (Latin feature)
        18. Has aspirates (th, ph, ch)

        Returns:
            numpy array of shape (19,)
        """
        word_lower = word.lower()
        features = []

        # Feature 0: Has voiced stops
        has_voiced = int(any(c in self.VOICED_STOPS for c in word_lower))
        features.append(has_voiced)

        # Feature 1: Has 'o'
        has_o = int('o' in word_lower)
        features.append(has_o)

        # Features 2-7: Etruscan endings (top 6)
        etruscan_endings_check = ['al', 'na', 's', 'i', 'a', 'ar']
        for ending in etruscan_endings_check:
            features.append(int(word_lower.endswith(ending)))

        # Features 8-13: Latin endings (top 6)
        latin_endings_check = ['um', 'us', 'orum', 'tion', 'que', 'ibus']
        for ending in latin_endings_check:
            features.append(int(word_lower.endswith(ending)))

        # Feature 14: Vowel ratio
        vowel_count = sum(1 for c in word_lower if c in self.VOWELS)
        total_alpha = sum(1 for c in word_lower if c.isalpha())
        vowel_ratio = vowel_count / max(total_alpha, 1)
        features.append(vowel_ratio)

        # Feature 15: Normalized word length (Etruscan words tend to be 3-8 chars)
        length_normalized = min(len(word_lower), 15) / 15.0
        features.append(length_normalized)

        # Feature 16: Has doubled consonants
        has_doubled = int(bool(re.search(r'([bcdfghjklmnpqrstvwxyz])\1', word_lower)))
        features.append(has_doubled)

        # Feature 17: Has 'qu' (Latin feature, not Etruscan)
        has_qu = int('qu' in word_lower)
        features.append(has_qu)

        # Feature 18: Has aspirates (common in Etruscan)
        has_aspirates = int(bool(re.search(r'(th|ph|ch)', word_lower)))
        features.append(has_aspirates)

        return np.array(features, dtype=np.float64)

    def _extract_features(self, words: list[str]) -> csr_matrix:
        """Extract all features for a list of words.

        Combines TF-IDF n-gram features with handcrafted features.

        Args:
            words: List of words to extract features from

        Returns:
            Sparse feature matrix
        """
        # Prepare words with boundary markers
        words_with_boundaries = [self._add_char_boundaries(w) for w in words]

        # Get n-gram features
        bigram_features = self.bigram_vectorizer.transform(words_with_boundaries)
        trigram_features = self.trigram_vectorizer.transform(words_with_boundaries)

        # Get handcrafted features
        handcrafted = np.array([self._extract_handcrafted_features(w) for w in words])
        handcrafted_sparse = csr_matrix(handcrafted)

        # Combine all features
        return hstack([bigram_features, trigram_features, handcrafted_sparse])

    def train(self, positive_words: list[str], negative_words: list[str]) -> None:
        """Train the classifier on positive (Etruscan) and negative (non-Etruscan) examples.

        Args:
            positive_words: List of known Etruscan words
            negative_words: List of non-Etruscan words (e.g., Latin)
        """
        # Combine data
        all_words = positive_words + negative_words
        labels = [1] * len(positive_words) + [0] * len(negative_words)

        # Prepare words with boundary markers
        words_with_boundaries = [self._add_char_boundaries(w) for w in all_words]

        # Initialize and fit vectorizers
        self.bigram_vectorizer = TfidfVectorizer(
            analyzer='char',
            ngram_range=(2, 2),
            max_features=500,
            min_df=2,
        )
        self.trigram_vectorizer = TfidfVectorizer(
            analyzer='char',
            ngram_range=(3, 3),
            max_features=500,
            min_df=2,
        )

        # Fit vectorizers
        bigram_features = self.bigram_vectorizer.fit_transform(words_with_boundaries)
        trigram_features = self.trigram_vectorizer.fit_transform(words_with_boundaries)

        # Get handcrafted features
        handcrafted = np.array([self._extract_handcrafted_features(w) for w in all_words])
        handcrafted_sparse = csr_matrix(handcrafted)

        # Combine all features
        X = hstack([bigram_features, trigram_features, handcrafted_sparse])
        y = np.array(labels)

        # Train classifier
        self.classifier = LogisticRegression(
            max_iter=1000,
            class_weight='balanced',
            random_state=42,
            C=1.0,
        )
        self.classifier.fit(X, y)
        self._is_trained = True

        print(f"Trained on {len(positive_words)} positive and {len(negative_words)} negative examples")
        print(f"Features: {X.shape[1]} (bigrams: {bigram_features.shape[1]}, "
              f"trigrams: {trigram_features.shape[1]}, handcrafted: {handcrafted.shape[1]})")

    def predict(self, word: str) -> float:
        """Predict the probability that a word is Etruscan.

        Args:
            word: Word to classify

        Returns:
            Probability between 0 and 1 (higher = more Etruscan-like)

        Raises:
            ValueError: If classifier has not been trained
        """
        if not self._is_trained:
            raise ValueError("Classifier has not been trained. Call train() or load() first.")

        features = self._extract_features([word])
        proba = self.classifier.predict_proba(features)[0]

        # Return probability of positive class (Etruscan)
        return float(proba[1])

    def predict_proba(self, word: str) -> float:
        """Alias for predict() - returns probability that word is Etruscan.

        Args:
            word: Word to classify

        Returns:
            Probability between 0 and 1
        """
        return self.predict(word)

    def predict_batch(self, words: list[str]) -> list[float]:
        """Predict probabilities for multiple words.

        Args:
            words: List of words to classify

        Returns:
            List of probabilities
        """
        if not self._is_trained:
            raise ValueError("Classifier has not been trained. Call train() or load() first.")

        features = self._extract_features(words)
        probas = self.classifier.predict_proba(features)

        return [float(p[1]) for p in probas]

    def save(self, path: Optional[Path] = None) -> None:
        """Save the trained classifier to disk.

        Args:
            path: Path to save the model. Defaults to data/models/word_classifier.pkl
        """
        if not self._is_trained:
            raise ValueError("Cannot save untrained classifier")

        if path is None:
            path = DEFAULT_MODEL_PATH

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        model_data = {
            'bigram_vectorizer': self.bigram_vectorizer,
            'trigram_vectorizer': self.trigram_vectorizer,
            'classifier': self.classifier,
        }

        with open(path, 'wb') as f:
            pickle.dump(model_data, f)

        print(f"Model saved to {path}")

    @classmethod
    def load(cls, path: Optional[Path] = None) -> 'WordClassifier':
        """Load a trained classifier from disk.

        Args:
            path: Path to load the model from. Defaults to data/models/word_classifier.pkl

        Returns:
            Loaded WordClassifier instance
        """
        if path is None:
            path = DEFAULT_MODEL_PATH

        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Model file not found: {path}")

        with open(path, 'rb') as f:
            model_data = pickle.load(f)

        instance = cls()
        instance.bigram_vectorizer = model_data['bigram_vectorizer']
        instance.trigram_vectorizer = model_data['trigram_vectorizer']
        instance.classifier = model_data['classifier']
        instance._is_trained = True

        return instance

    def get_feature_importance(self, top_n: int = 20) -> dict:
        """Get the most important features for classification.

        Args:
            top_n: Number of top features to return

        Returns:
            Dictionary with 'etruscan_indicators' and 'latin_indicators'
        """
        if not self._is_trained:
            raise ValueError("Classifier has not been trained")

        # Get feature names
        bigram_names = self.bigram_vectorizer.get_feature_names_out()
        trigram_names = self.trigram_vectorizer.get_feature_names_out()
        handcrafted_names = [
            'has_voiced_stops', 'has_o',
            'ends_al', 'ends_na', 'ends_s', 'ends_i', 'ends_a', 'ends_ar',
            'ends_um', 'ends_us', 'ends_orum', 'ends_tion', 'ends_que', 'ends_ibus',
            'vowel_ratio', 'length_norm', 'has_doubled', 'has_qu', 'has_aspirates',
        ]

        all_names = list(bigram_names) + list(trigram_names) + handcrafted_names

        # Get coefficients
        coeffs = self.classifier.coef_[0]

        # Sort by coefficient value
        sorted_indices = np.argsort(coeffs)

        # Top Etruscan indicators (positive coefficients)
        etruscan_indices = sorted_indices[-top_n:][::-1]
        etruscan_indicators = [
            (all_names[i], float(coeffs[i]))
            for i in etruscan_indices
            if coeffs[i] > 0
        ]

        # Top Latin indicators (negative coefficients)
        latin_indices = sorted_indices[:top_n]
        latin_indicators = [
            (all_names[i], float(coeffs[i]))
            for i in latin_indices
            if coeffs[i] < 0
        ]

        return {
            'etruscan_indicators': etruscan_indicators,
            'latin_indicators': latin_indicators,
        }
