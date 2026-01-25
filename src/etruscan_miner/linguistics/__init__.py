"""Cross-linguistic analysis module for Etruscan discovery.

This module provides tools for finding Etruscan vocabulary through
comparison with related and neighboring languages:

- lemnian: Lemnian language corpus (only known Etruscan relative)
- raetic: Raetic inscriptions from the Alpine region
- loanword_detector: Latin words with suspected Etruscan origin
- greek_substrate: Pre-Greek Tyrrhenian substrate words
- italic_parallels: Umbrian/Oscan parallels and borrowings
- morphology: Etruscan morphological analysis (Phase 6)
- form_predictor: Predict unattested Etruscan forms (Phase 6)
- name_expander: Expand theonyms and anthroponyms (Phase 6)
"""

from .lemnian import (
    LEMNIAN_CORPUS,
    LemnianWord,
    LemnianAnalyzer,
    find_etruscan_parallels,
    get_lemnian_roots,
)

from .raetic import (
    RAETIC_CORPUS,
    RaeticInscription,
    RaeticAnalyzer,
    find_raetic_parallels,
)

from .loanword_detector import (
    LatinLoanwordDetector,
    LoanwordCandidate,
    detect_etruscan_loanwords,
    KNOWN_ETRUSCAN_LOANS,
)

from .greek_substrate import (
    GreekSubstrateDetector,
    SubstrateCandidate,
    detect_tyrrhenian_substrate,
)

from .italic_parallels import (
    ItalicParallelFinder,
    ItalicParallel,
    find_italic_parallels,
    UMBRIAN_RELIGIOUS_TERMS,
)

from .morphology import (
    EtruscanMorphology,
    MorphologicalAnalysis,
    analyze_morphology,
    decompose_word,
    KNOWN_MORPHEMES,
)

from .form_predictor import (
    FormPredictor,
    PredictedForm,
    predict_forms,
    search_predicted_forms,
)

from .name_expander import (
    NameExpander,
    ExpandedName,
    expand_theonyms,
    expand_anthroponyms,
    ETRUSCAN_THEONYMS,
)

__all__ = [
    # Lemnian
    "LEMNIAN_CORPUS",
    "LemnianWord",
    "LemnianAnalyzer",
    "find_etruscan_parallels",
    "get_lemnian_roots",
    # Raetic
    "RAETIC_CORPUS",
    "RaeticInscription",
    "RaeticAnalyzer",
    "find_raetic_parallels",
    # Loanword detection
    "LatinLoanwordDetector",
    "LoanwordCandidate",
    "detect_etruscan_loanwords",
    "KNOWN_ETRUSCAN_LOANS",
    # Greek substrate
    "GreekSubstrateDetector",
    "SubstrateCandidate",
    "detect_tyrrhenian_substrate",
    # Italic parallels
    "ItalicParallelFinder",
    "ItalicParallel",
    "find_italic_parallels",
    "UMBRIAN_RELIGIOUS_TERMS",
    # Morphology
    "EtruscanMorphology",
    "MorphologicalAnalysis",
    "analyze_morphology",
    "decompose_word",
    "KNOWN_MORPHEMES",
    # Form prediction
    "FormPredictor",
    "PredictedForm",
    "predict_forms",
    "search_predicted_forms",
    # Name expansion
    "NameExpander",
    "ExpandedName",
    "expand_theonyms",
    "expand_anthroponyms",
    "ETRUSCAN_THEONYMS",
]
