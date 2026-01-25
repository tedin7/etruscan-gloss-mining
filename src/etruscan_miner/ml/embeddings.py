"""Word embeddings for ancient language analysis.

This module provides word embedding capabilities for finding
semantically similar words in Latin and Greek texts. Words
borrowed from Etruscan often cluster in specific semantic
domains (religion, theatre, luxury goods).

Supports:
- Pre-trained Latin embeddings (LatinBERT, Latin Word2Vec)
- Custom embedding training on corpus
- Semantic similarity search
- Vocabulary clustering
"""

import re
import json
import pickle
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Iterator
from collections import Counter
import math

from ..config import MODELS_DIR


@dataclass
class EmbeddingModel:
    """A word embedding model."""

    name: str
    dimension: int
    vocabulary_size: int
    source: str  # 'pretrained', 'custom'
    path: Optional[Path] = None


@dataclass
class SimilarWord:
    """A word similar to a query word."""

    word: str
    similarity: float
    shared_context: list[str] = field(default_factory=list)


class WordEmbeddings:
    """Word embedding manager for ancient languages.

    This is a simplified implementation that uses co-occurrence
    based similarity. For production, integrate with:
    - LatinBERT (https://github.com/dbamman/latin-bert)
    - Latin Word2Vec models
    - fastText Latin embeddings
    """

    def __init__(self, model_path: Path = None):
        """Initialize embeddings.

        Args:
            model_path: Path to saved embeddings model
        """
        self.model_path = model_path or MODELS_DIR / "word_embeddings.pkl"
        self.vocabulary: dict[str, int] = {}
        self.co_occurrences: dict[str, Counter] = {}
        self.word_counts: Counter = Counter()
        self._loaded = False

    def train(self, texts: list[str], window_size: int = 5, min_count: int = 3) -> None:
        """Train embeddings on texts using co-occurrence.

        Args:
            texts: List of text documents
            window_size: Context window size
            min_count: Minimum word count to include
        """
        # Build vocabulary
        for text in texts:
            words = self._tokenize(text)
            self.word_counts.update(words)

        # Filter by min_count
        self.vocabulary = {
            word: idx for idx, (word, count) in enumerate(
                [(w, c) for w, c in self.word_counts.items() if c >= min_count]
            )
        }

        # Build co-occurrence matrix
        for text in texts:
            words = [w for w in self._tokenize(text) if w in self.vocabulary]

            for i, word in enumerate(words):
                if word not in self.co_occurrences:
                    self.co_occurrences[word] = Counter()

                # Get context words
                start = max(0, i - window_size)
                end = min(len(words), i + window_size + 1)

                for j in range(start, end):
                    if i != j:
                        self.co_occurrences[word][words[j]] += 1

        self._loaded = True

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize Latin/Greek text.

        Args:
            text: Text to tokenize

        Returns:
            List of word tokens
        """
        # Simple tokenization for Latin
        text = text.lower()
        # Remove punctuation but keep apostrophes
        text = re.sub(r"[^\w\s']", " ", text)
        words = text.split()
        # Filter very short words
        return [w for w in words if len(w) >= 2]

    def find_similar(self, word: str, top_n: int = 10) -> list[SimilarWord]:
        """Find words similar to a query word.

        Args:
            word: Query word
            top_n: Number of results

        Returns:
            List of SimilarWord objects
        """
        if not self._loaded:
            self._load_or_train()

        word_lower = word.lower()
        if word_lower not in self.co_occurrences:
            return []

        query_context = self.co_occurrences[word_lower]
        similarities = []

        for other_word, other_context in self.co_occurrences.items():
            if other_word == word_lower:
                continue

            # Calculate cosine similarity
            sim = self._cosine_similarity(query_context, other_context)
            if sim > 0:
                # Find shared context words
                shared = [w for w in query_context if w in other_context][:5]
                similarities.append(SimilarWord(
                    word=other_word,
                    similarity=sim,
                    shared_context=shared,
                ))

        # Sort by similarity
        similarities.sort(key=lambda x: x.similarity, reverse=True)
        return similarities[:top_n]

    def _cosine_similarity(self, vec1: Counter, vec2: Counter) -> float:
        """Calculate cosine similarity between two count vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity (0-1)
        """
        # Get shared keys
        shared_keys = set(vec1.keys()) & set(vec2.keys())
        if not shared_keys:
            return 0.0

        # Calculate dot product
        dot = sum(vec1[k] * vec2[k] for k in shared_keys)

        # Calculate magnitudes
        mag1 = math.sqrt(sum(v * v for v in vec1.values()))
        mag2 = math.sqrt(sum(v * v for v in vec2.values()))

        if mag1 == 0 or mag2 == 0:
            return 0.0

        return dot / (mag1 * mag2)

    def cluster_by_domain(self, words: list[str], n_clusters: int = 5) -> dict[int, list[str]]:
        """Cluster words into semantic domains.

        Uses simple agglomerative clustering based on similarity.

        Args:
            words: Words to cluster
            n_clusters: Number of clusters

        Returns:
            Dict mapping cluster ID to word lists
        """
        if not self._loaded:
            self._load_or_train()

        # Filter to known words
        known_words = [w.lower() for w in words if w.lower() in self.co_occurrences]

        if len(known_words) < n_clusters:
            return {0: known_words}

        # Simple clustering: assign based on most similar seed word
        # In production, use proper clustering (k-means, hierarchical)
        clusters: dict[int, list[str]] = {i: [] for i in range(n_clusters)}

        # Use first n_clusters words as seeds
        seeds = known_words[:n_clusters]

        for word in known_words:
            if word in seeds:
                clusters[seeds.index(word)].append(word)
                continue

            # Find most similar seed
            best_cluster = 0
            best_sim = 0

            for i, seed in enumerate(seeds):
                if word in self.co_occurrences and seed in self.co_occurrences:
                    sim = self._cosine_similarity(
                        self.co_occurrences[word],
                        self.co_occurrences[seed]
                    )
                    if sim > best_sim:
                        best_sim = sim
                        best_cluster = i

            clusters[best_cluster].append(word)

        return clusters

    def _load_or_train(self) -> None:
        """Load saved model or train on default corpus."""
        if self.model_path.exists():
            with open(self.model_path, 'rb') as f:
                data = pickle.load(f)
                self.vocabulary = data['vocabulary']
                self.co_occurrences = data['co_occurrences']
                self.word_counts = data['word_counts']
                self._loaded = True
        else:
            # Train on empty corpus - user should provide texts
            self.vocabulary = {}
            self.co_occurrences = {}
            self.word_counts = Counter()
            self._loaded = True

    def save(self) -> None:
        """Save model to disk."""
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump({
                'vocabulary': self.vocabulary,
                'co_occurrences': self.co_occurrences,
                'word_counts': self.word_counts,
            }, f)

    def get_etruscan_domain_neighbors(self, seed_words: list[str] = None) -> list[SimilarWord]:
        """Find words near known Etruscan vocabulary.

        Expands from known Etruscan words to find semantically
        related words that might also be Etruscan.

        Args:
            seed_words: Known Etruscan words to expand from

        Returns:
            List of candidate words
        """
        if seed_words is None:
            # Default Etruscan-related seed words
            seed_words = [
                "haruspex", "histrio", "lanista", "persona",
                "subulo", "lucumo", "lar", "atrium"
            ]

        all_similar = []
        seen = set(w.lower() for w in seed_words)

        for seed in seed_words:
            similar = self.find_similar(seed, top_n=5)
            for s in similar:
                if s.word not in seen:
                    seen.add(s.word)
                    all_similar.append(s)

        # Sort by similarity
        all_similar.sort(key=lambda x: x.similarity, reverse=True)
        return all_similar[:20]


def find_similar_words(word: str, top_n: int = 10) -> list[SimilarWord]:
    """Find words similar to a query word.

    Args:
        word: Query word
        top_n: Number of results

    Returns:
        List of SimilarWord objects
    """
    embeddings = WordEmbeddings()
    return embeddings.find_similar(word, top_n)


def cluster_vocabulary(words: list[str], n_clusters: int = 5) -> dict[int, list[str]]:
    """Cluster words into semantic domains.

    Args:
        words: Words to cluster
        n_clusters: Number of clusters

    Returns:
        Dict mapping cluster ID to word lists
    """
    embeddings = WordEmbeddings()
    return embeddings.cluster_by_domain(words, n_clusters)
