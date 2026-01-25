"""Unified discovery pipeline for finding new Etruscan words.

This module orchestrates all discovery methods:
- Pattern-based mining (explicit and implicit)
- Cross-linguistic analysis (Lemnian, Raetic, loanwords)
- Statistical anomaly detection (hapax, phonotactic)
- ML-based discovery (embeddings, NER, semantic search)
- Morphological prediction

Usage:
    from etruscan_miner.discovery import DiscoveryPipeline

    pipeline = DiscoveryPipeline()
    results = pipeline.discover(text, source="Varro De Lingua Latina")

    for candidate in results.candidates:
        print(f"{candidate.word}: {candidate.confidence:.2f}")
"""

from .pipeline import (
    DiscoveryPipeline,
    DiscoveryResult,
    DiscoveryCandidate,
    DiscoveryMethod,
    run_full_discovery,
)

__all__ = [
    "DiscoveryPipeline",
    "DiscoveryResult",
    "DiscoveryCandidate",
    "DiscoveryMethod",
    "run_full_discovery",
]
