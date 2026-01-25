"""Statistical anomaly detection for Etruscan word discovery.

This module provides statistical methods to identify candidate Etruscan words:

- hapax_analyzer: Find words appearing only once in Latin literature
- phonotactic_anomaly: Detect phonotactically unusual words
- geographic_scorer: Boost scores for words in Etruscan geographic contexts
- author_profiler: Weight discoveries by author reliability
"""

from .hapax_analyzer import (
    HapaxAnalyzer,
    HapaxCandidate,
    analyze_text_for_hapax,
    get_hapax_in_etruscan_context,
)

from .phonotactic_anomaly import (
    PhonotacticAnomalyDetector,
    AnomalyResult,
    detect_anomalies_in_text,
    score_word_anomaly,
)

from .geographic_scorer import (
    GeographicScorer,
    GeographicContext,
    detect_etruscan_geography,
    calculate_geographic_boost,
)

from .author_profiler import (
    AuthorProfiler,
    AuthorProfile,
    get_author_reliability,
    apply_author_weight,
)

__all__ = [
    # Hapax analysis
    "HapaxAnalyzer",
    "HapaxCandidate",
    "analyze_text_for_hapax",
    "get_hapax_in_etruscan_context",
    # Phonotactic anomaly
    "PhonotacticAnomalyDetector",
    "AnomalyResult",
    "detect_anomalies_in_text",
    "score_word_anomaly",
    # Geographic scoring
    "GeographicScorer",
    "GeographicContext",
    "detect_etruscan_geography",
    "calculate_geographic_boost",
    # Author profiling
    "AuthorProfiler",
    "AuthorProfile",
    "get_author_reliability",
    "apply_author_weight",
]
