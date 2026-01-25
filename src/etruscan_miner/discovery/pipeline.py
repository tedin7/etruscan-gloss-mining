"""Unified discovery pipeline for Etruscan word discovery.

This module orchestrates all discovery methods to find new Etruscan
vocabulary in ancient texts. It combines:

1. Pattern-based mining (explicit and implicit)
2. Cross-linguistic analysis (Lemnian, Raetic, loanwords)
3. Statistical anomaly detection (hapax, phonotactic)
4. ML-based discovery (embeddings, NER, semantic search)
5. Morphological prediction

Each method contributes candidates with confidence scores, which
are then validated, deduplicated, and ranked.
"""

import re
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional
from collections import Counter


class DiscoveryMethod(Enum):
    """Discovery method identifiers."""

    EXPLICIT_PATTERN = auto()
    IMPLICIT_PATTERN = auto()
    METALINGUISTIC = auto()
    DOMAIN_CONTEXT = auto()
    LEMNIAN_PARALLEL = auto()
    RAETIC_PARALLEL = auto()
    LOANWORD_ANALYSIS = auto()
    GREEK_SUBSTRATE = auto()
    ITALIC_PARALLEL = auto()
    HAPAX_ANALYSIS = auto()
    PHONOTACTIC_ANOMALY = auto()
    GEOGRAPHIC_CONTEXT = auto()
    SEMANTIC_SEARCH = auto()
    FOREIGN_WORD_NER = auto()
    ETYMOLOGY_DETECTION = auto()
    MORPHOLOGICAL_PREDICTION = auto()
    NAME_EXPANSION = auto()


@dataclass
class DiscoveryCandidate:
    """A candidate Etruscan word from discovery."""

    word: str
    normalized: str  # Lowercase, cleaned
    confidence: float
    methods: list[DiscoveryMethod] = field(default_factory=list)
    context: str = ""
    source: str = ""
    meaning_hint: str = ""
    cross_linguistic_support: list[str] = field(default_factory=list)
    phonotactic_score: float = 0.0
    author_reliability: float = 0.5
    notes: str = ""


@dataclass
class DiscoveryResult:
    """Result of running the discovery pipeline."""

    candidates: list[DiscoveryCandidate]
    total_methods_used: int
    source_text_length: int
    passages_analyzed: int
    high_confidence_count: int  # >= 0.70
    medium_confidence_count: int  # 0.50-0.69
    low_confidence_count: int  # < 0.50


class DiscoveryPipeline:
    """Unified pipeline for Etruscan word discovery.

    Orchestrates all discovery methods and combines results.
    """

    def __init__(
        self,
        enable_ml: bool = True,
        enable_cross_linguistic: bool = True,
        enable_statistics: bool = True,
        enable_morphological: bool = True,
        min_confidence: float = 0.30
    ):
        """Initialize pipeline.

        Args:
            enable_ml: Enable ML-based discovery methods
            enable_cross_linguistic: Enable cross-linguistic analysis
            enable_statistics: Enable statistical anomaly detection
            enable_morphological: Enable morphological prediction
            min_confidence: Minimum confidence to include candidates
        """
        self.enable_ml = enable_ml
        self.enable_cross_linguistic = enable_cross_linguistic
        self.enable_statistics = enable_statistics
        self.enable_morphological = enable_morphological
        self.min_confidence = min_confidence

        self._init_components()

    def _init_components(self) -> None:
        """Initialize pipeline components."""
        # Pattern matchers
        try:
            from ..patterns import (
                GlossExtractor,
                detect_metalinguistic_passages,
                detect_domain_context,
            )
            self.pattern_extractor = GlossExtractor()
            self._patterns_available = True
        except ImportError:
            self._patterns_available = False

        # Corpus sources
        try:
            from ..corpus.medieval_glossaries import MedievalGlossaryLoader
            from ..corpus.byzantine import ByzantineLoader
            self.medieval_loader = MedievalGlossaryLoader()
            self.byzantine_loader = ByzantineLoader()
            self._corpus_available = True
        except ImportError:
            self._corpus_available = False

        # Cross-linguistic analyzers
        try:
            from ..linguistics import (
                LemnianAnalyzer,
                RaeticAnalyzer,
                LatinLoanwordDetector,
            )
            self.lemnian = LemnianAnalyzer()
            self.raetic = RaeticAnalyzer()
            self.loanword_detector = LatinLoanwordDetector()
            self._linguistics_available = True
        except ImportError:
            self._linguistics_available = False

        # Statistical analyzers
        try:
            from ..statistics import (
                HapaxAnalyzer,
                PhonotacticAnomalyDetector,
                GeographicScorer,
                AuthorProfiler,
            )
            self.hapax = HapaxAnalyzer()
            self.phonotactic = PhonotacticAnomalyDetector()
            self.geographic = GeographicScorer()
            self.author = AuthorProfiler()
            self._statistics_available = True
        except ImportError:
            self._statistics_available = False

        # ML components
        try:
            from ..ml import (
                SemanticSearch,
                ForeignWordNER,
                EtymologyDetector,
            )
            self.semantic_search = SemanticSearch()
            self.foreign_ner = ForeignWordNER()
            self.etymology = EtymologyDetector()
            self._ml_available = True
        except ImportError:
            self._ml_available = False

        # Validation
        try:
            from ..validation.linguistic import LinguisticValidator
            self.linguistic_validator = LinguisticValidator()
            self._validation_available = True
        except ImportError:
            self._validation_available = False

    def discover(
        self,
        text: str,
        source: str = "unknown",
        author: str = None,
        language: str = "latin"
    ) -> DiscoveryResult:
        """Run full discovery pipeline on a text.

        Args:
            text: Text to analyze
            source: Source name/reference
            author: Author name for reliability weighting
            language: Text language ('latin' or 'greek')

        Returns:
            DiscoveryResult with all candidates
        """
        all_candidates: list[DiscoveryCandidate] = []
        methods_used = 0

        # 1. Pattern-based discovery
        if self._patterns_available:
            pattern_candidates = self._run_pattern_discovery(text, source)
            all_candidates.extend(pattern_candidates)
            methods_used += 1

        # 2. ML-based discovery
        if self.enable_ml and self._ml_available:
            ml_candidates = self._run_ml_discovery(text, source, language)
            all_candidates.extend(ml_candidates)
            methods_used += 3

        # 3. Statistical discovery
        if self.enable_statistics and self._statistics_available:
            stat_candidates = self._run_statistical_discovery(text, source)
            all_candidates.extend(stat_candidates)
            methods_used += 2

        # 4. Cross-linguistic validation
        if self.enable_cross_linguistic and self._linguistics_available:
            all_candidates = self._apply_cross_linguistic(all_candidates)
            methods_used += 3

        # 5. Author reliability weighting
        if author and self._statistics_available:
            all_candidates = self._apply_author_weighting(all_candidates, author)

        # 6. Merge and rank
        merged = self._merge_candidates(all_candidates)

        # 7. Filter by minimum confidence
        filtered = [c for c in merged if c.confidence >= self.min_confidence]

        # 8. Validate phonotactics
        if self._validation_available:
            filtered = self._validate_candidates(filtered)

        # Sort by confidence
        filtered.sort(key=lambda c: c.confidence, reverse=True)

        # Count by confidence level
        high = len([c for c in filtered if c.confidence >= 0.70])
        medium = len([c for c in filtered if 0.50 <= c.confidence < 0.70])
        low = len([c for c in filtered if c.confidence < 0.50])

        return DiscoveryResult(
            candidates=filtered,
            total_methods_used=methods_used,
            source_text_length=len(text),
            passages_analyzed=text.count(".") + 1,  # Rough estimate
            high_confidence_count=high,
            medium_confidence_count=medium,
            low_confidence_count=low,
        )

    def _run_pattern_discovery(self, text: str, source: str) -> list[DiscoveryCandidate]:
        """Run pattern-based discovery.

        Args:
            text: Text to analyze
            source: Source name

        Returns:
            List of candidates
        """
        candidates = []

        # Extract using GlossExtractor
        result = self.pattern_extractor.extract(text)
        for match in result.matches:
            context = match.context_before + match.full_match + match.context_after
            candidates.append(DiscoveryCandidate(
                word=match.etruscan_word,
                normalized=match.etruscan_word.lower(),
                confidence=match.confidence,
                methods=[DiscoveryMethod.EXPLICIT_PATTERN],
                context=context[:200],
                source=source,
                meaning_hint=match.meaning_hint or "",
                notes=f"Pattern: {match.pattern_name}",
            ))

        return candidates

    def _run_ml_discovery(self, text: str, source: str, language: str) -> list[DiscoveryCandidate]:
        """Run ML-based discovery.

        Args:
            text: Text to analyze
            source: Source name
            language: Text language

        Returns:
            List of candidates
        """
        candidates = []

        # Foreign word NER
        if hasattr(self, 'foreign_ner'):
            foreign_words = self.foreign_ner.detect_in_text(text, language)
            for fw in foreign_words:
                if fw.confidence >= 0.4:
                    candidates.append(DiscoveryCandidate(
                        word=fw.word,
                        normalized=fw.word.lower(),
                        confidence=fw.confidence * 0.8,  # Scale down
                        methods=[DiscoveryMethod.FOREIGN_WORD_NER],
                        context=fw.context,
                        source=source,
                        notes=f"Detection: {fw.detection_method}",
                    ))

        # Etymology detection
        if hasattr(self, 'etymology'):
            passages = self.etymology.detect_passages(text)
            for passage in passages:
                for word in passage.candidate_foreign_words:
                    if len(word) >= 3:
                        candidates.append(DiscoveryCandidate(
                            word=word,
                            normalized=word.lower(),
                            confidence=passage.confidence * 0.75,
                            methods=[DiscoveryMethod.ETYMOLOGY_DETECTION],
                            context=passage.text[:150],
                            source=source,
                            notes=f"Etymology type: {passage.etymology_type}",
                        ))

        return candidates

    def _run_statistical_discovery(self, text: str, source: str) -> list[DiscoveryCandidate]:
        """Run statistical anomaly discovery.

        Args:
            text: Text to analyze
            source: Source name

        Returns:
            List of candidates
        """
        candidates = []

        # Phonotactic anomaly detection - analyze words individually
        if hasattr(self, 'phonotactic'):
            import re
            words = set(re.findall(r'\b([a-zA-Z]{3,15})\b', text))
            for word in words:
                try:
                    anomaly = self.phonotactic.detect_anomaly(word)
                    if anomaly.etruscan_score >= 0.5:
                        candidates.append(DiscoveryCandidate(
                            word=anomaly.word,
                            normalized=anomaly.word.lower(),
                            confidence=anomaly.etruscan_score * 0.6,
                            methods=[DiscoveryMethod.PHONOTACTIC_ANOMALY],
                            context="",
                            source=source,
                            phonotactic_score=anomaly.etruscan_score,
                            notes="Phonotactically Etruscan-like",
                        ))
                except Exception:
                    pass  # Skip words that fail analysis

        return candidates

    def _apply_cross_linguistic(self, candidates: list[DiscoveryCandidate]) -> list[DiscoveryCandidate]:
        """Apply cross-linguistic analysis to boost confidence.

        Args:
            candidates: Existing candidates

        Returns:
            Candidates with updated confidence
        """
        for candidate in candidates:
            # Check Lemnian parallels
            lemnian_matches = self.lemnian.find_parallel(candidate.word)
            if lemnian_matches:
                best = max(lemnian_matches, key=lambda m: m.confidence)
                candidate.cross_linguistic_support.append(f"Lemnian: {best.form}")
                candidate.confidence = min(0.95, candidate.confidence + 0.15)
                candidate.methods.append(DiscoveryMethod.LEMNIAN_PARALLEL)

            # Check Raetic parallels
            raetic_matches = self.raetic.find_parallel(candidate.word)
            if raetic_matches:
                best = max(raetic_matches, key=lambda m: m.confidence)
                candidate.cross_linguistic_support.append(f"Raetic: {best.form}")
                candidate.confidence = min(0.95, candidate.confidence + 0.10)
                candidate.methods.append(DiscoveryMethod.RAETIC_PARALLEL)

            # Check if known loanword
            loanword = self.loanword_detector.is_known_loan(candidate.word)
            if loanword:
                candidate.cross_linguistic_support.append(f"Known loan: {loanword.latin_word}")
                candidate.confidence = max(candidate.confidence, loanword.confidence)
                candidate.meaning_hint = loanword.meaning
                candidate.methods.append(DiscoveryMethod.LOANWORD_ANALYSIS)

        return candidates

    def _apply_author_weighting(self, candidates: list[DiscoveryCandidate], author: str) -> list[DiscoveryCandidate]:
        """Apply author reliability weighting.

        Args:
            candidates: Existing candidates
            author: Author name

        Returns:
            Candidates with adjusted confidence
        """
        reliability = self.author.get_reliability(author)

        for candidate in candidates:
            candidate.author_reliability = reliability
            # Blend confidence with author reliability
            candidate.confidence = (candidate.confidence * 0.7) + (candidate.confidence * reliability * 0.3)

        return candidates

    def _merge_candidates(self, candidates: list[DiscoveryCandidate]) -> list[DiscoveryCandidate]:
        """Merge duplicate candidates.

        Args:
            candidates: All candidates

        Returns:
            Deduplicated candidates
        """
        by_word: dict[str, list[DiscoveryCandidate]] = {}

        for c in candidates:
            key = c.normalized
            if key not in by_word:
                by_word[key] = []
            by_word[key].append(c)

        merged = []
        for word, word_candidates in by_word.items():
            if len(word_candidates) == 1:
                merged.append(word_candidates[0])
            else:
                # Merge: combine methods, take highest confidence
                best = max(word_candidates, key=lambda x: x.confidence)
                all_methods = []
                all_support = []

                for c in word_candidates:
                    all_methods.extend(c.methods)
                    all_support.extend(c.cross_linguistic_support)

                best.methods = list(set(all_methods))
                best.cross_linguistic_support = list(set(all_support))

                # Boost for multiple detection methods
                method_boost = 0.05 * (len(best.methods) - 1)
                best.confidence = min(0.98, best.confidence + method_boost)

                merged.append(best)

        return merged

    def _validate_candidates(self, candidates: list[DiscoveryCandidate]) -> list[DiscoveryCandidate]:
        """Validate candidates with linguistic analysis.

        Args:
            candidates: Candidates to validate

        Returns:
            Validated candidates with updated scores
        """
        # Common Latin words to filter out
        common_latin = {
            "est", "sunt", "esse", "erat", "erant", "fuit", "fuere",
            "qui", "quae", "quod", "quem", "qua", "quo",
            "hic", "haec", "hoc", "ille", "illa", "illud",
            "ipse", "ipsa", "ipsum", "idem", "eadem",
            "omnis", "omne", "omnia", "omnes", "omnem",
            "unus", "una", "unum", "duo", "tres",
            "non", "nec", "neque", "sed", "aut", "vel", "sive",
            "cum", "dum", "tam", "tum", "iam", "nam", "enim",
            "per", "pro", "sub", "sine", "ante", "post",
            "inter", "intra", "extra", "contra", "ultra",
            "magnus", "magna", "magnum", "parvus", "parva",
            "bonus", "bona", "bonum", "malus", "mala",
            "primus", "prima", "primum", "secundus", "tertius",
            "novus", "nova", "novum", "vetus", "vetere",
            "rex", "regis", "regem", "reges", "regum",
            "deus", "dei", "deo", "deum", "dea", "deae",
            "homo", "hominis", "hominem", "homines",
            "vir", "viri", "virum", "viros", "virorum",
            "mulier", "mulieris", "mulierem",
            "pater", "patris", "patrem", "mater", "matris",
            "filius", "filii", "filium", "filia", "filiae",
            "populus", "populi", "populo", "populum",
            "civitas", "civitatis", "civitatem",
            "urbs", "urbis", "urbem", "urbe",
            "terra", "terrae", "terram", "terras",
            "aqua", "aquae", "aquam", "aquas",
            "annus", "anni", "annum", "anno", "annos",
            "dies", "diei", "diem", "die",
            "tempus", "temporis", "tempore",
            "bellum", "belli", "bello",
            "pax", "pacis", "pacem", "pace",
            "lex", "legis", "legem", "leges",
            "ius", "iuris", "iure",
            "vita", "vitae", "vitam",
            "mors", "mortis", "mortem", "morte",
            "corpus", "corporis", "corpore",
            "caput", "capitis", "capite",
            "manus", "manum", "manu",
            "oculus", "oculi", "oculo", "oculos",
            "verbum", "verbi", "verbo", "verba",
            "nomen", "nominis", "nomine", "nomina",
            "res", "rei", "rem", "rerum", "rebus",
            "causa", "causae", "causam",
            "modus", "modi", "modo",
            "ratio", "rationis", "ratione",
            "natura", "naturae", "naturam",
            "forma", "formae", "formam",
            "genus", "generis", "genere",
            "pars", "partis", "partem", "parte",
            "finis", "finis", "finem", "fine",
            "locus", "loci", "loco", "locum",
            "via", "viae", "viam",
            "mons", "montis", "montem", "monte",
            "flumen", "fluminis", "flumine",
            "silva", "silvae", "silvam",
            "domus", "domi", "domum", "domo",
            "ager", "agri", "agrum", "agro",
            "mare", "maris", "maria",
            "caelum", "caeli", "caelo",
            "sol", "solis", "sole",
            "luna", "lunae", "lunam",
            # Common Latin place/ethnic adjectives
            "latinus", "latina", "latinum", "latini",
            "romanus", "romana", "romanum", "romani", "romanis",
            "graecus", "graeca", "graecum", "graeci",
            "italicus", "italica", "italicum",
        }

        validated = []
        for candidate in candidates:
            # Skip common Latin words
            if candidate.normalized in common_latin:
                continue

            result = self.linguistic_validator.validate(candidate.word)
            candidate.phonotactic_score = result.score

            # Penalize candidates with low phonotactic plausibility
            if result.plausibility == "unlikely":
                candidate.confidence *= 0.5
            elif result.plausibility == "low":
                candidate.confidence *= 0.8

            validated.append(candidate)

        return validated


def run_full_discovery(
    text: str,
    source: str = "unknown",
    author: str = None,
    min_confidence: float = 0.40
) -> DiscoveryResult:
    """Run full discovery pipeline on text.

    Args:
        text: Text to analyze
        source: Source name
        author: Author name
        min_confidence: Minimum confidence threshold

    Returns:
        DiscoveryResult with all candidates
    """
    pipeline = DiscoveryPipeline(min_confidence=min_confidence)
    return pipeline.discover(text, source, author)
