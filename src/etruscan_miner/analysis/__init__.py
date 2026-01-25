"""Advanced analysis modules for Etruscan word discovery.

This package contains sophisticated analysis tools for finding
genuinely new Etruscan vocabulary through:

1. Inscription cross-reference - matching inscription words to Latin
2. Semantic domain analysis - Etruscan cultural field detection
3. Phonotactic fingerprinting - language-specific sound patterns
4. Proto-Tyrsenian reconstruction - ancestral form prediction
"""

from .inscription_matcher import (
    InscriptionMatcher,
    InscriptionMatch,
    cross_reference_inscriptions,
)
from .semantic_domains import (
    SemanticDomainClassifier,
    EtruscanDomain,
    classify_semantic_domain,
)
from .phonotactic_fingerprint import (
    PhonotacticFingerprinter,
    LanguageFingerprint,
    fingerprint_word,
)
from .proto_tyrsenian import (
    ProtoTyrsenianReconstructor,
    ProtoForm,
    reconstruct_proto_form,
)

__all__ = [
    # Inscription matching
    "InscriptionMatcher",
    "InscriptionMatch",
    "cross_reference_inscriptions",
    # Semantic domains
    "SemanticDomainClassifier",
    "EtruscanDomain",
    "classify_semantic_domain",
    # Phonotactic fingerprinting
    "PhonotacticFingerprinter",
    "LanguageFingerprint",
    "fingerprint_word",
    # Proto-Tyrsenian
    "ProtoTyrsenianReconstructor",
    "ProtoForm",
    "reconstruct_proto_form",
]
