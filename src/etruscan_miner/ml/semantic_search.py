"""Semantic search for Etruscan-related passages.

This module provides semantic search capabilities to find
passages discussing Etruscan topics regardless of exact
keyword matches. Uses TF-IDF and optional transformer
embeddings for relevance ranking.

Use cases:
- Find passages about Etruscan religion without explicit "Etruscan" mention
- Discover divination texts that may contain Etruscan terminology
- Locate etymology discussions in unexpected places
"""

import re
import math
from dataclasses import dataclass, field
from collections import Counter
from pathlib import Path
from typing import Optional, Iterator


@dataclass
class SearchResult:
    """A semantic search result."""

    text: str
    source: str
    relevance_score: float
    matched_topics: list[str] = field(default_factory=list)
    key_terms: list[str] = field(default_factory=list)
    position: int = 0  # Character position in source


@dataclass
class TopicProfile:
    """A topic profile for semantic matching."""

    name: str
    keywords: list[str]
    weight: float = 1.0
    description: str = ""


# Pre-defined Etruscan-related topic profiles
ETRUSCAN_TOPICS = [
    TopicProfile(
        name="divination",
        keywords=[
            "haruspex", "haruspic", "extispic", "fulgurator", "fulgur",
            "auspic", "augur", "omen", "prodig", "portent", "presag",
            "iecur", "liver", "sacr", "divin", "caeli", "lightning"
        ],
        weight=1.5,
        description="Etruscan divination practices",
    ),
    TopicProfile(
        name="theatre",
        keywords=[
            "histrio", "histrion", "actor", "scaen", "fabul", "lud",
            "spectacul", "theatr", "persona", "mask", "mim"
        ],
        weight=1.3,
        description="Theatre and performance (Etruscan origins)",
    ),
    TopicProfile(
        name="religion",
        keywords=[
            "templum", "sacr", "ritus", "deus", "dea", "sacrific",
            "libat", "votiv", "lar", "lares", "penates", "manes",
            "genius", "mania", "larvae"
        ],
        weight=1.2,
        description="Religious practices with Etruscan influence",
    ),
    TopicProfile(
        name="etruscan_identity",
        keywords=[
            "tusci", "tuscus", "tuscia", "etruri", "etrusc",
            "tyrrheni", "tyrrhen", "rasenna", "rasna", "tarchon"
        ],
        weight=2.0,
        description="Explicit Etruscan identity markers",
    ),
    TopicProfile(
        name="etymology",
        keywords=[
            "etymolog", "appell", "vocat", "dicit", "dict",
            "nomin", "signific", "lingua", "verbum", "vocabul",
            "orig", "deriv", "unde", "inde"
        ],
        weight=1.4,
        description="Etymology and word origin discussions",
    ),
    TopicProfile(
        name="luxury",
        keywords=[
            "aurum", "gold", "purpur", "ebur", "ivory",
            "argentum", "silver", "gemm", "conviv", "banquet",
            "vinum", "wine"
        ],
        weight=1.0,
        description="Luxury goods (Etruscan trade specialty)",
    ),
    TopicProfile(
        name="afterlife",
        keywords=[
            "mors", "mort", "sepulcr", "tumul", "inferi",
            "manes", "funer", "ciner", "urna", "tomb"
        ],
        weight=1.1,
        description="Death and afterlife (Etruscan focus)",
    ),
    TopicProfile(
        name="governance",
        keywords=[
            "lucumo", "princep", "rex", "regn", "magistrat",
            "praefect", "imperium", "potestas"
        ],
        weight=1.0,
        description="Governance and political titles",
    ),
]


class SemanticSearch:
    """Semantic search engine for ancient texts."""

    def __init__(self, topics: list[TopicProfile] = None):
        """Initialize search engine.

        Args:
            topics: Topic profiles to use (default: ETRUSCAN_TOPICS)
        """
        self.topics = topics or ETRUSCAN_TOPICS
        self.documents: list[tuple[str, str]] = []  # (text, source)
        self.idf: dict[str, float] = {}
        self._indexed = False

    def index_documents(self, documents: list[tuple[str, str]]) -> None:
        """Index documents for search.

        Args:
            documents: List of (text, source_name) tuples
        """
        self.documents = documents

        # Calculate IDF scores
        doc_count = len(documents)
        term_doc_counts: Counter = Counter()

        for text, _ in documents:
            terms = set(self._tokenize(text))
            term_doc_counts.update(terms)

        self.idf = {
            term: math.log(doc_count / (count + 1))
            for term, count in term_doc_counts.items()
        }

        self._indexed = True

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize text for indexing.

        Args:
            text: Text to tokenize

        Returns:
            List of tokens
        """
        text = text.lower()
        # Keep Latin characters and common diacritics
        text = re.sub(r"[^\w\s]", " ", text)
        return [w for w in text.split() if len(w) >= 2]

    def search(
        self,
        query: str = None,
        topic_names: list[str] = None,
        top_n: int = 10,
        min_score: float = 0.1
    ) -> list[SearchResult]:
        """Search indexed documents.

        Args:
            query: Free text query (optional)
            topic_names: Topic profiles to match (optional)
            top_n: Maximum results
            min_score: Minimum relevance score

        Returns:
            List of SearchResult objects
        """
        if not self._indexed:
            return []

        results = []

        # Build query terms
        query_terms = []
        if query:
            query_terms.extend(self._tokenize(query))

        # Add topic keywords
        topics_to_use = []
        if topic_names:
            topics_to_use = [t for t in self.topics if t.name in topic_names]
        else:
            topics_to_use = self.topics

        for topic in topics_to_use:
            query_terms.extend(topic.keywords)

        query_counter = Counter(query_terms)

        # Score each document
        for text, source in self.documents:
            doc_terms = self._tokenize(text)
            doc_counter = Counter(doc_terms)

            # Calculate TF-IDF score
            score = 0.0
            matched_topics = []
            key_terms_found = []

            for term, query_count in query_counter.items():
                if term in doc_counter:
                    tf = doc_counter[term] / len(doc_terms) if doc_terms else 0
                    idf = self.idf.get(term, 0)
                    term_score = tf * idf * query_count

                    # Apply topic weights
                    for topic in topics_to_use:
                        if term in topic.keywords:
                            term_score *= topic.weight
                            if topic.name not in matched_topics:
                                matched_topics.append(topic.name)

                    score += term_score
                    if term_score > 0.01:
                        key_terms_found.append(term)

            if score >= min_score:
                results.append(SearchResult(
                    text=text[:500] + "..." if len(text) > 500 else text,
                    source=source,
                    relevance_score=score,
                    matched_topics=matched_topics,
                    key_terms=key_terms_found[:10],
                ))

        # Sort by score
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results[:top_n]

    def search_for_etruscan_context(self, top_n: int = 20) -> list[SearchResult]:
        """Search for passages in Etruscan-relevant contexts.

        Finds passages that discuss Etruscan-related topics even
        without explicit Etruscan mentions.

        Args:
            top_n: Maximum results

        Returns:
            List of SearchResult objects
        """
        return self.search(
            topic_names=["divination", "theatre", "religion", "etruscan_identity"],
            top_n=top_n,
            min_score=0.2
        )

    def find_etymology_passages(self, top_n: int = 20) -> list[SearchResult]:
        """Find passages discussing word origins.

        These passages are high-value targets for finding
        foreign vocabulary including Etruscan terms.

        Args:
            top_n: Maximum results

        Returns:
            List of SearchResult objects
        """
        return self.search(
            topic_names=["etymology"],
            top_n=top_n,
            min_score=0.15
        )


def search_etruscan_topics(texts: list[tuple[str, str]], top_n: int = 20) -> list[SearchResult]:
    """Search texts for Etruscan-related topics.

    Args:
        texts: List of (text, source) tuples
        top_n: Maximum results

    Returns:
        List of SearchResult objects
    """
    search = SemanticSearch()
    search.index_documents(texts)
    return search.search_for_etruscan_context(top_n)


def rank_passages_by_relevance(
    passages: list[str],
    query: str,
    source: str = "unknown"
) -> list[SearchResult]:
    """Rank passages by relevance to a query.

    Args:
        passages: List of text passages
        query: Search query
        source: Source name for all passages

    Returns:
        List of SearchResult objects sorted by relevance
    """
    search = SemanticSearch()
    docs = [(p, source) for p in passages]
    search.index_documents(docs)
    return search.search(query=query, top_n=len(passages))
