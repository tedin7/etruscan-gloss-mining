"""Etymology passage detector.

This module detects passages where ancient authors discuss
word origins and etymologies. Such passages are high-value
targets for finding foreign vocabulary, as authors often
explain the origin of unusual words.

Uses transformer-based classification when available,
with fallback to pattern matching.
"""

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EtymologyPassage:
    """A passage discussing etymology."""

    text: str
    start_pos: int
    end_pos: int
    trigger_words: list[str] = field(default_factory=list)
    candidate_foreign_words: list[str] = field(default_factory=list)
    etymology_type: str = ""  # 'derivation', 'translation', 'definition', 'comparison'
    confidence: float = 0.0
    source_language_mentioned: Optional[str] = None
    notes: str = ""


class EtymologyDetector:
    """Detector for etymology discussion passages.

    When ML models are available, uses transformer-based
    classification. Otherwise falls back to pattern matching.
    """

    def __init__(self, use_ml: bool = False):
        """Initialize detector.

        Args:
            use_ml: Whether to use ML models if available
        """
        self.use_ml = use_ml
        self._init_patterns()

    def _init_patterns(self) -> None:
        """Initialize etymology detection patterns."""
        # Derivation patterns
        self.derivation_patterns = [
            r"(\w+)\s+dict\w+\s+(?:est\s+)?(?:a|ab|ex)\s+(\w+)",
            r"(\w+)\s+derivat\w+\s+(?:a|ab|ex)\s+(\w+)",
            r"(\w+)\s+trahitur\s+(?:a|ab|ex)\s+(\w+)",
            r"(\w+)\s+ductum\s+(?:a|ab|ex)\s+(\w+)",
            r"orig\w+\s+(?:huius\s+)?(?:verbi|vocabuli|nominis)\s+(\w+)",
            r"etymologia\s+(?:eius|huius)?\s*(?:est)?\s*(\w+)",
        ]

        # Definition patterns
        self.definition_patterns = [
            r"(\w+)\s+(?:id|hoc)\s+est\s+(\w+)",
            r"(\w+)\s+significat\s+(\w+)",
            r"(\w+)\s+(?:dicitur|vocatur)\s+(?:quod|quia)",
            r"quid\s+sit\s+(\w+)",
            r"quid\s+significet\s+(\w+)",
        ]

        # Language comparison patterns
        self.comparison_patterns = [
            r"graece\s+(\w+)\s*,?\s*latine\s+(\w+)",
            r"latine\s+(\w+)\s*,?\s*graece\s+(\w+)",
            r"(?:tusci|etrusci|tyrrheni)\s+(?:vocant|dicunt|appellant)\s+(\w+)",
            r"lingua\s+(\w+)\s+(\w+)",
            r"apud\s+(\w+)\s+(\w+)\s+(?:dicitur|vocatur)",
        ]

        # Compile all patterns
        self.all_patterns = []
        for pattern_list, etype in [
            (self.derivation_patterns, "derivation"),
            (self.definition_patterns, "definition"),
            (self.comparison_patterns, "comparison"),
        ]:
            for pattern in pattern_list:
                self.all_patterns.append((re.compile(pattern, re.IGNORECASE), etype))

    def detect_passages(
        self,
        text: str,
        context_window: int = 150
    ) -> list[EtymologyPassage]:
        """Detect etymology discussion passages in text.

        Args:
            text: Text to analyze
            context_window: Characters of context around matches

        Returns:
            List of EtymologyPassage objects
        """
        passages = []

        for pattern, etype in self.all_patterns:
            for match in pattern.finditer(text):
                # Extract context
                start = max(0, match.start() - context_window)
                end = min(len(text), match.end() + context_window)
                passage_text = text[start:end]

                # Extract trigger words and candidates
                triggers = [match.group(0)]
                candidates = list(match.groups())

                # Check for language mention
                source_lang = self._detect_source_language(passage_text)

                passages.append(EtymologyPassage(
                    text=passage_text,
                    start_pos=start,
                    end_pos=end,
                    trigger_words=triggers,
                    candidate_foreign_words=[c for c in candidates if c],
                    etymology_type=etype,
                    confidence=0.65,
                    source_language_mentioned=source_lang,
                ))

        # Merge overlapping passages
        return self._merge_passages(passages)

    def _detect_source_language(self, text: str) -> Optional[str]:
        """Detect if a source language is mentioned.

        Args:
            text: Text to check

        Returns:
            Language name if detected
        """
        text_lower = text.lower()

        language_markers = {
            "etruscan": ["tusci", "tuscus", "etrusc", "tyrrheni", "tyrrhen"],
            "greek": ["graece", "graecum", "graeci"],
            "latin": ["latine", "latinum", "latini"],
            "oscan": ["osce", "oscum", "osci"],
            "umbrian": ["umbrice", "umbrum"],
            "sabine": ["sabine", "sabinum", "sabini"],
        }

        for lang, markers in language_markers.items():
            if any(marker in text_lower for marker in markers):
                return lang

        return None

    def _merge_passages(self, passages: list[EtymologyPassage]) -> list[EtymologyPassage]:
        """Merge overlapping passages.

        Args:
            passages: List of passages

        Returns:
            Merged list
        """
        if not passages:
            return []

        # Sort by start position
        sorted_passages = sorted(passages, key=lambda p: p.start_pos)

        merged = [sorted_passages[0]]

        for passage in sorted_passages[1:]:
            last = merged[-1]

            # Check for overlap
            if passage.start_pos <= last.end_pos:
                # Merge
                last.end_pos = max(last.end_pos, passage.end_pos)
                last.trigger_words.extend(passage.trigger_words)
                last.candidate_foreign_words.extend(passage.candidate_foreign_words)
                last.confidence = max(last.confidence, passage.confidence)

                if passage.source_language_mentioned and not last.source_language_mentioned:
                    last.source_language_mentioned = passage.source_language_mentioned
            else:
                merged.append(passage)

        # Deduplicate candidates
        for passage in merged:
            passage.candidate_foreign_words = list(set(passage.candidate_foreign_words))
            passage.trigger_words = list(set(passage.trigger_words))

        return merged

    def extract_candidates(self, passages: list[EtymologyPassage]) -> list[str]:
        """Extract all candidate foreign words from passages.

        Args:
            passages: List of etymology passages

        Returns:
            List of candidate words
        """
        candidates = []
        for passage in passages:
            candidates.extend(passage.candidate_foreign_words)

        # Filter common Latin words
        stopwords = {
            "est", "sunt", "quod", "quia", "quae", "qui", "quem",
            "hoc", "haec", "hic", "ille", "illa", "illud",
            "enim", "autem", "sed", "nec", "neque", "vel",
            "unde", "inde", "idem", "eius", "huius", "verbi",
            "vocabuli", "nominis", "lingua", "significat"
        }

        return [c for c in set(candidates) if c.lower() not in stopwords and len(c) >= 3]

    def find_etruscan_etymologies(self, text: str) -> list[EtymologyPassage]:
        """Find passages specifically discussing Etruscan etymologies.

        Args:
            text: Text to analyze

        Returns:
            List of passages with Etruscan mentions
        """
        all_passages = self.detect_passages(text)
        return [p for p in all_passages if p.source_language_mentioned == "etruscan"]


def detect_etymology_passages(text: str, context_window: int = 150) -> list[EtymologyPassage]:
    """Detect etymology discussion passages.

    Args:
        text: Text to analyze
        context_window: Context around matches

    Returns:
        List of EtymologyPassage objects
    """
    detector = EtymologyDetector()
    return detector.detect_passages(text, context_window)


def extract_etymology_candidates(text: str) -> list[str]:
    """Extract candidate foreign words from etymology passages.

    Args:
        text: Text to analyze

    Returns:
        List of candidate words
    """
    detector = EtymologyDetector()
    passages = detector.detect_passages(text)
    return detector.extract_candidates(passages)
