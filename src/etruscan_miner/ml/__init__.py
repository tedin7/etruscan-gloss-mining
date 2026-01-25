"""Machine Learning module for advanced Etruscan discovery.

This module provides ML-based approaches to finding Etruscan vocabulary:

- embeddings: Word embeddings for semantic similarity
- semantic_search: Find passages about Etruscan topics
- foreign_word_ner: Named Entity Recognition for foreign words
- etymology_detector: Detect etymology discussion passages
"""

from .embeddings import (
    WordEmbeddings,
    EmbeddingModel,
    find_similar_words,
    cluster_vocabulary,
)

from .semantic_search import (
    SemanticSearch,
    SearchResult,
    search_etruscan_topics,
    rank_passages_by_relevance,
)

from .foreign_word_ner import (
    ForeignWordNER,
    ForeignWordCandidate,
    detect_foreign_words,
    classify_word_origin,
)

from .etymology_detector import (
    EtymologyDetector,
    EtymologyPassage,
    detect_etymology_passages,
    extract_etymology_candidates,
)

__all__ = [
    # Embeddings
    "WordEmbeddings",
    "EmbeddingModel",
    "find_similar_words",
    "cluster_vocabulary",
    # Semantic search
    "SemanticSearch",
    "SearchResult",
    "search_etruscan_topics",
    "rank_passages_by_relevance",
    # Foreign word NER
    "ForeignWordNER",
    "ForeignWordCandidate",
    "detect_foreign_words",
    "classify_word_origin",
    # Etymology detection
    "EtymologyDetector",
    "EtymologyPassage",
    "detect_etymology_passages",
    "extract_etymology_candidates",
]
