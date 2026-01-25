"""Unified validation pipeline combining all 9 scoring methods.

This module provides a single source of truth for validating Etruscan word
candidates, combining methods from the old validate and verify commands:

Methods:
1. Pattern - confidence from pattern matching (e.g., "Tusci vocant")
2. Cross-reference - matches against known Etruscan vocabulary
3. Linguistic - Etruscan phonotactic rules (no voiced stops, typical endings)
4. Phonotactic - fingerprinting for substrate detection
5. Context - contextual coherence (rule-based or ML)
6. Inscription - matches against CIEW inscription corpus
7. Semantic - domain classification (divination, theatre, religion, etc.)
8. Lemnian - parallels with Lemnian (Etruscan's only known relative)
9. Raetic - parallels with Raetic inscriptions

Usage:
    from etruscan_miner.validation.unified import UnifiedValidator, UnifiedScore

    validator = UnifiedValidator(repo)
    score = validator.validate("harena", context="...", pattern_confidence=0.8)
    print(f"{score.word}: {score.final_score:.2f} ({score.recommendation})")
"""

from dataclasses import dataclass, field
from typing import Optional
import logging

from ..db.repository import Repository

logger = logging.getLogger(__name__)


# Default weights for each method (total = 1.0)
DEFAULT_WEIGHTS = {
    "pattern": 0.10,
    "cross_ref": 0.15,
    "linguistic": 0.10,
    "phonotactic": 0.15,
    "context": 0.10,
    "inscription": 0.15,
    "semantic": 0.10,
    "lemnian": 0.10,
    "raetic": 0.05,
}


@dataclass
class UnifiedScore:
    """Complete validation score from all 9 methods."""

    word: str
    final_score: float  # 0.0 - 1.0
    methods_confirmed: int  # how many of 9 methods passed (score >= 0.5)
    recommendation: str  # 'accept', 'review', 'reject'
    confidence_level: str  # 'high', 'medium', 'low'

    # Component scores (all 0.0 - 1.0)
    pattern_score: float = 0.0
    cross_ref_score: float = 0.0
    linguistic_score: float = 0.0
    phonotactic_score: float = 0.0
    context_score: float = 0.0
    inscription_score: float = 0.0
    semantic_score: float = 0.0
    lemnian_score: float = 0.0
    raetic_score: float = 0.0

    # Detailed results
    cross_ref_match: Optional[str] = None
    cross_ref_meaning: Optional[str] = None
    cross_ref_type: Optional[str] = None

    inscription_match: Optional[str] = None
    inscription_meaning: Optional[str] = None
    inscription_domain: Optional[str] = None

    semantic_domain: Optional[str] = None
    semantic_probability: float = 0.0

    lemnian_parallel: Optional[str] = None
    raetic_parallel: Optional[str] = None

    phonotactic_features: list[str] = field(default_factory=list)
    linguistic_positives: list[str] = field(default_factory=list)
    linguistic_issues: list[str] = field(default_factory=list)

    # Flags
    known_loan: bool = False
    is_isidore: bool = False

    # ML scores (optional)
    ml_scores: dict = field(default_factory=dict)
    ml_rejection_reason: Optional[str] = None

    def get_confirmed_methods(self) -> list[str]:
        """Return list of methods that confirmed (score >= 0.5)."""
        methods = []
        if self.pattern_score >= 0.5:
            methods.append("PATTERN")
        if self.cross_ref_score >= 0.5:
            methods.append("CROSS_REF")
        if self.linguistic_score >= 0.5:
            methods.append("LINGUISTIC")
        if self.phonotactic_score >= 0.5:
            methods.append("PHONOTACTIC")
        if self.context_score >= 0.5:
            methods.append("CONTEXT")
        if self.inscription_score >= 0.5:
            methods.append("INSCRIPTION")
        if self.semantic_score >= 0.5:
            methods.append("SEMANTIC")
        if self.lemnian_score >= 0.5:
            methods.append("LEMNIAN")
        if self.raetic_score >= 0.5:
            methods.append("RAETIC")
        return methods

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON export."""
        return {
            "word": self.word,
            "final_score": self.final_score,
            "methods_confirmed": self.methods_confirmed,
            "confirmed_methods": self.get_confirmed_methods(),
            "recommendation": self.recommendation,
            "confidence_level": self.confidence_level,
            "scores": {
                "pattern": self.pattern_score,
                "cross_ref": self.cross_ref_score,
                "linguistic": self.linguistic_score,
                "phonotactic": self.phonotactic_score,
                "context": self.context_score,
                "inscription": self.inscription_score,
                "semantic": self.semantic_score,
                "lemnian": self.lemnian_score,
                "raetic": self.raetic_score,
            },
            "details": {
                "cross_ref_match": self.cross_ref_match,
                "cross_ref_meaning": self.cross_ref_meaning,
                "inscription_match": self.inscription_match,
                "inscription_meaning": self.inscription_meaning,
                "semantic_domain": self.semantic_domain,
                "lemnian_parallel": self.lemnian_parallel,
                "raetic_parallel": self.raetic_parallel,
                "phonotactic_features": self.phonotactic_features,
            },
            "flags": {
                "known_loan": self.known_loan,
                "is_isidore": self.is_isidore,
            },
        }


class UnifiedValidator:
    """Single source of truth for all validation methods.

    Combines the validation approaches from both the validate and verify
    commands into a unified 9-method scoring system.
    """

    # Known Etruscan loanwords for reference
    KNOWN_LOANS = {
        'histrio', 'histriones', 'persona', 'personae',
        'haruspex', 'haruspices', 'lanista', 'lanistae',
        'subulo', 'subulones', 'atrium', 'atria',
        'lucumo', 'lucumones', 'lar', 'lares',
        'catena', 'catenae', 'fenestra', 'fenestrae',
        'balteus', 'baltei', 'mantisa', 'satelles',
        'spurius', 'elementum', 'elementa', 'mundus',
    }

    # Confidence thresholds
    CONFIDENCE_HIGH = 0.85
    CONFIDENCE_MEDIUM = 0.65

    # Isidore penalty factor
    ISIDORE_PENALTY = 0.6

    def __init__(
        self,
        repo: Optional[Repository] = None,
        weights: Optional[dict] = None,
        use_ml: bool = False,
    ):
        """Initialize unified validator with all analysis components.

        Args:
            repo: Database repository (optional, for cross-reference checking)
            weights: Custom weights for each method (defaults to DEFAULT_WEIGHTS)
            use_ml: Enable ML-based classifiers (word classifier, context classifier)
        """
        self.repo = repo
        self.weights = weights or DEFAULT_WEIGHTS.copy()
        self.use_ml = use_ml
        self._warnings: list[str] = []

        # Initialize validators
        self._cross_ref = None
        self._linguistic = None
        self._phonotactic = None
        self._inscriptions = None
        self._semantic = None
        self._lemnian = None
        self._raetic = None

        # ML components
        self._word_classifier = None
        self._context_classifier = None
        self._dependency_filter = None

        self._initialize_components()

    def _initialize_components(self) -> None:
        """Initialize all analysis components."""
        # Cross-reference checker (requires repo)
        if self.repo:
            try:
                from .cross_reference import CrossReferenceChecker
                self._cross_ref = CrossReferenceChecker(self.repo)
            except Exception as e:
                self._warnings.append(f"Cross-reference checker: {e}")

        # Linguistic validator (always available)
        try:
            from .linguistic import LinguisticValidator
            self._linguistic = LinguisticValidator()
        except Exception as e:
            self._warnings.append(f"Linguistic validator: {e}")

        # Phonotactic fingerprinter
        try:
            from ..analysis import PhonotacticFingerprinter
            self._phonotactic = PhonotacticFingerprinter()
        except Exception as e:
            self._warnings.append(f"Phonotactic fingerprinter: {e}")

        # Inscription matcher
        try:
            from ..analysis import InscriptionMatcher
            self._inscriptions = InscriptionMatcher()
        except Exception as e:
            self._warnings.append(f"Inscription matcher: {e}")

        # Semantic domain classifier
        try:
            from ..analysis import SemanticDomainClassifier
            self._semantic = SemanticDomainClassifier()
        except Exception as e:
            self._warnings.append(f"Semantic domain classifier: {e}")

        # Cross-linguistic analyzers
        try:
            from ..linguistics import LemnianAnalyzer
            self._lemnian = LemnianAnalyzer()
        except Exception as e:
            self._warnings.append(f"Lemnian analyzer: {e}")

        try:
            from ..linguistics import RaeticAnalyzer
            self._raetic = RaeticAnalyzer()
        except Exception as e:
            self._warnings.append(f"Raetic analyzer: {e}")

        # ML components (optional)
        if self.use_ml:
            self._initialize_ml_components()

    def _initialize_ml_components(self) -> None:
        """Initialize ML-based classifiers."""
        # Dependency filter (Layer 1)
        try:
            from .dependency_filter import DependencyFilter
            self._dependency_filter = DependencyFilter()
            logger.info(f"Loaded dependency filter (method: {self._dependency_filter.method})")
        except Exception as e:
            self._warnings.append(f"Dependency filter: {e}")

        # Word classifier (Layer 2)
        try:
            from .word_classifier import WordClassifier
            self._word_classifier = WordClassifier.load()
            logger.info("Loaded word classifier model")
        except FileNotFoundError:
            self._warnings.append("Word classifier not trained")
        except Exception as e:
            self._warnings.append(f"Word classifier: {e}")

        # Context classifier (Layer 3)
        try:
            from .context_classifier import ContextClassifier
            self._context_classifier = ContextClassifier.load()
            logger.info(f"Loaded context classifier (backend: {self._context_classifier.backend})")
        except FileNotFoundError:
            self._warnings.append("Context classifier not trained")
        except Exception as e:
            self._warnings.append(f"Context classifier: {e}")

    @property
    def warnings(self) -> list[str]:
        """Return initialization warnings."""
        return self._warnings

    def _check_isidore(self, context: str) -> bool:
        """Check if context is from Isidore's Etymologiae."""
        context_lower = context.lower()
        markers = ["isidore", "isidor", "etymologiae", "etym.", "isid."]
        return any(marker in context_lower for marker in markers)

    def _calculate_context_score(self, context: str) -> float:
        """Calculate contextual coherence score (rule-based fallback)."""
        if not context:
            return 0.5

        score = 0.5
        context_lower = context.lower()

        # Positive indicators
        meaning_indicators = ["means", "significat", "dicitur", "vocant", "appellant", "that is"]
        for indicator in meaning_indicators:
            if indicator in context_lower:
                score += 0.1
                break

        if "id est" in context_lower or "quod est" in context_lower:
            score += 0.15

        # Negative indicators
        noise_indicators = ["perhaps", "maybe", "some say", "fortasse", "nonnulli"]
        for indicator in noise_indicators:
            if indicator in context_lower:
                score -= 0.1
                break

        return max(0.0, min(1.0, score))

    def validate(
        self,
        word: str,
        context: str = "",
        pattern_confidence: float = 0.0,
    ) -> UnifiedScore:
        """Run ALL validation methods and return unified score.

        Args:
            word: The word to validate
            context: Surrounding context (optional)
            pattern_confidence: Confidence from pattern extraction (0.0 - 1.0)

        Returns:
            UnifiedScore with all method scores and final recommendation
        """
        word_lower = word.lower()
        ml_scores = {}

        # Check if known loan
        known_loan = word_lower in self.KNOWN_LOANS

        # Check if Isidore source (unreliable)
        is_isidore = self._check_isidore(context)

        # ML early rejection (if enabled)
        if self.use_ml and self._dependency_filter and context:
            has_attribution = self._dependency_filter.has_etruscan_attribution(context)
            details = self._dependency_filter.get_attribution_details(context)
            ml_scores["dependency_filter"] = details.confidence

            if not has_attribution:
                return UnifiedScore(
                    word=word,
                    final_score=0.1,
                    methods_confirmed=0,
                    recommendation="reject",
                    confidence_level="low",
                    pattern_score=pattern_confidence,
                    ml_scores=ml_scores,
                    ml_rejection_reason=f"No Etruscan attribution: {details.reason}",
                )

        if self.use_ml and self._word_classifier:
            word_score = self._word_classifier.predict(word)
            ml_scores["word_classifier"] = word_score

            if word_score < 0.3:
                return UnifiedScore(
                    word=word,
                    final_score=0.2,
                    methods_confirmed=0,
                    recommendation="reject",
                    confidence_level="low",
                    pattern_score=pattern_confidence,
                    ml_scores=ml_scores,
                    ml_rejection_reason=f"Word not Etruscan-like (score: {word_score:.2f})",
                )

        # 1. Pattern score (passed in)
        pattern_score = pattern_confidence

        # 2. Cross-reference score
        cross_ref_score = 0.0
        cross_ref_match = None
        cross_ref_meaning = None
        cross_ref_type = None

        if self._cross_ref:
            try:
                result = self._cross_ref.check(word)
                cross_ref_score = result.score
                cross_ref_match = result.matched_word
                cross_ref_meaning = result.matched_meaning
                cross_ref_type = result.match_type
            except Exception as e:
                logger.debug(f"Cross-reference check failed: {e}")

        # 3. Linguistic score
        linguistic_score = 0.0
        linguistic_positives = []
        linguistic_issues = []

        if self._linguistic:
            try:
                result = self._linguistic.validate(word)
                linguistic_score = result.score
                linguistic_positives = result.positive_features or []
                linguistic_issues = result.issues or []
            except Exception as e:
                logger.debug(f"Linguistic validation failed: {e}")

        # 4. Phonotactic score
        phonotactic_score = 0.0
        phonotactic_features = []

        if self._phonotactic:
            try:
                fp = self._phonotactic.fingerprint(word)
                phonotactic_score = fp.substrate_probability
                phonotactic_features = fp.etruscan_features or []
            except Exception as e:
                logger.debug(f"Phonotactic fingerprinting failed: {e}")

        # 5. Context score
        if self.use_ml and self._context_classifier and context:
            context_score = self._context_classifier.predict(context)
            ml_scores["context_classifier"] = context_score
        else:
            context_score = self._calculate_context_score(context)

        # 6. Inscription score
        inscription_score = 0.0
        inscription_match = None
        inscription_meaning = None
        inscription_domain = None

        if self._inscriptions:
            try:
                for etr_word, info in self._inscriptions.inscription_vocab.items():
                    etr_norm = etr_word.lower()

                    if etr_norm == word_lower:
                        inscription_score = 1.0
                        inscription_match = etr_word
                        inscription_meaning = info.get("meaning", "")
                        inscription_domain = info.get("domain", "")
                        break

                    if len(etr_norm) >= 3 and word_lower.startswith(etr_norm):
                        inscription_score = 0.7
                        inscription_match = etr_word
                        inscription_meaning = info.get("meaning", "")
                        inscription_domain = info.get("domain", "")
                        break
            except Exception as e:
                logger.debug(f"Inscription matching failed: {e}")

        # 7. Semantic score
        semantic_score = 0.0
        semantic_domain = None
        semantic_probability = 0.0

        if self._semantic:
            try:
                classification = self._semantic.classify_word(word)
                semantic_domain = classification.primary_domain.name
                semantic_probability = classification.loan_probability
                semantic_score = classification.loan_probability
            except Exception as e:
                logger.debug(f"Semantic classification failed: {e}")

        # 8. Lemnian score
        lemnian_score = 0.0
        lemnian_parallel = None

        if self._lemnian:
            try:
                match = self._lemnian.find_parallel(word)
                if match:
                    lemnian_score = 0.8
                    lemnian_parallel = match.lemnian_word
            except Exception as e:
                logger.debug(f"Lemnian parallel search failed: {e}")

        # 9. Raetic score
        raetic_score = 0.0
        raetic_parallel = None

        if self._raetic:
            try:
                match = self._raetic.find_parallel(word)
                if match:
                    raetic_score = 0.8
                    raetic_parallel = match.raetic_word
            except Exception as e:
                logger.debug(f"Raetic parallel search failed: {e}")

        # Calculate weighted final score
        final_score = (
            pattern_score * self.weights["pattern"]
            + cross_ref_score * self.weights["cross_ref"]
            + linguistic_score * self.weights["linguistic"]
            + phonotactic_score * self.weights["phonotactic"]
            + context_score * self.weights["context"]
            + inscription_score * self.weights["inscription"]
            + semantic_score * self.weights["semantic"]
            + lemnian_score * self.weights["lemnian"]
            + raetic_score * self.weights["raetic"]
        )

        # Apply Isidore penalty
        if is_isidore:
            final_score *= self.ISIDORE_PENALTY

        # Count confirmed methods (score >= 0.5)
        scores = [
            pattern_score, cross_ref_score, linguistic_score,
            phonotactic_score, context_score, inscription_score,
            semantic_score, lemnian_score, raetic_score
        ]
        methods_confirmed = sum(1 for s in scores if s >= 0.5)

        # Determine confidence level and recommendation
        if final_score >= self.CONFIDENCE_HIGH:
            confidence_level = "high"
            recommendation = "accept"
        elif final_score >= self.CONFIDENCE_MEDIUM:
            confidence_level = "medium"
            recommendation = "review"
        else:
            confidence_level = "low"
            recommendation = "reject"

        # Boost for exact cross-reference match
        if cross_ref_type == "exact":
            confidence_level = "high"
            recommendation = "accept"

        return UnifiedScore(
            word=word,
            final_score=final_score,
            methods_confirmed=methods_confirmed,
            recommendation=recommendation,
            confidence_level=confidence_level,
            pattern_score=pattern_score,
            cross_ref_score=cross_ref_score,
            linguistic_score=linguistic_score,
            phonotactic_score=phonotactic_score,
            context_score=context_score,
            inscription_score=inscription_score,
            semantic_score=semantic_score,
            lemnian_score=lemnian_score,
            raetic_score=raetic_score,
            cross_ref_match=cross_ref_match,
            cross_ref_meaning=cross_ref_meaning,
            cross_ref_type=cross_ref_type,
            inscription_match=inscription_match,
            inscription_meaning=inscription_meaning,
            inscription_domain=inscription_domain,
            semantic_domain=semantic_domain,
            semantic_probability=semantic_probability,
            lemnian_parallel=lemnian_parallel,
            raetic_parallel=raetic_parallel,
            phonotactic_features=phonotactic_features,
            linguistic_positives=linguistic_positives,
            linguistic_issues=linguistic_issues,
            known_loan=known_loan,
            is_isidore=is_isidore,
            ml_scores=ml_scores,
        )

    def validate_batch(
        self,
        words: list[tuple[str, str, float]],
    ) -> list[UnifiedScore]:
        """Validate a batch of words.

        Args:
            words: List of (word, context, pattern_confidence) tuples

        Returns:
            List of UnifiedScore objects, sorted by final_score descending
        """
        results = []
        for word, context, confidence in words:
            score = self.validate(word, context, confidence)
            results.append(score)

        return sorted(results, key=lambda s: s.final_score, reverse=True)

    def get_summary(self, scores: list[UnifiedScore]) -> dict:
        """Get summary statistics for a batch of scores."""
        if not scores:
            return {"count": 0}

        return {
            "count": len(scores),
            "avg_score": sum(s.final_score for s in scores) / len(scores),
            "high_confidence": sum(1 for s in scores if s.confidence_level == "high"),
            "medium_confidence": sum(1 for s in scores if s.confidence_level == "medium"),
            "low_confidence": sum(1 for s in scores if s.confidence_level == "low"),
            "recommendations": {
                "accept": sum(1 for s in scores if s.recommendation == "accept"),
                "review": sum(1 for s in scores if s.recommendation == "review"),
                "reject": sum(1 for s in scores if s.recommendation == "reject"),
            },
            "multi_method": sum(1 for s in scores if s.methods_confirmed >= 2),
            "known_loans": sum(1 for s in scores if s.known_loan),
        }
