"""Gloss extractor for mining Etruscan glosses from ancient texts."""

import re
from dataclasses import dataclass, field
from typing import Optional

from .latin_patterns import (
    ALL_PATTERNS as LATIN_PATTERNS,
    LatinPattern,
    PatternMatch,
    get_pattern_by_name,
)
from .greek_patterns import ALL_GREEK_PATTERNS, GreekPattern


@dataclass
class ExtractionResult:
    """Result of extracting glosses from a text."""

    text: str
    matches: list[PatternMatch] = field(default_factory=list)
    patterns_applied: int = 0
    language: str = "latin"

    @property
    def found_glosses(self) -> bool:
        """Whether any glosses were found."""
        return len(self.matches) > 0

    def get_unique_words(self) -> list[str]:
        """Get unique Etruscan words found."""
        return list(set(m.etruscan_word.lower() for m in self.matches))

    def get_high_confidence_matches(self, threshold: float = 0.85) -> list[PatternMatch]:
        """Get matches above confidence threshold."""
        return [m for m in self.matches if m.confidence >= threshold]


class GlossExtractor:
    """Extract Etruscan glosses from Latin and Greek texts."""

    def __init__(
        self,
        min_confidence: float = 0.0,
        context_chars: int = 100,
        include_greek: bool = True,
    ):
        """Initialize extractor.

        Args:
            min_confidence: Minimum pattern confidence to use
            context_chars: Number of characters of context to extract
            include_greek: Whether to include Greek patterns
        """
        self.min_confidence = min_confidence
        self.context_chars = context_chars
        self.include_greek = include_greek

        # Compile patterns
        self._latin_patterns: list[tuple[LatinPattern, re.Pattern]] = []
        self._greek_patterns: list[tuple[GreekPattern, re.Pattern]] = []

        for p in LATIN_PATTERNS:
            if p.confidence >= min_confidence:
                try:
                    compiled = re.compile(p.regex, re.IGNORECASE | re.MULTILINE)
                    self._latin_patterns.append((p, compiled))
                except re.error as e:
                    print(f"Warning: Invalid regex in pattern {p.name}: {e}")

        if include_greek:
            for p in ALL_GREEK_PATTERNS:
                if p.confidence >= min_confidence:
                    try:
                        compiled = re.compile(p.regex, re.MULTILINE)
                        self._greek_patterns.append((p, compiled))
                    except re.error as e:
                        print(f"Warning: Invalid regex in pattern {p.name}: {e}")

    def _get_context(self, text: str, start: int, end: int) -> tuple[str, str]:
        """Extract context before and after a match."""
        ctx_start = max(0, start - self.context_chars)
        ctx_end = min(len(text), end + self.context_chars)

        context_before = text[ctx_start:start].strip()
        context_after = text[end:ctx_end].strip()

        # Clean up context (remove excessive whitespace)
        context_before = " ".join(context_before.split())
        context_after = " ".join(context_after.split())

        return context_before, context_after

    def _normalize_word(self, word: str) -> str:
        """Normalize an extracted word."""
        # Remove leading/trailing punctuation
        word = word.strip(".,;:!?()[]{}\"'")
        return word

    def extract(self, text: str, language: str = "auto") -> ExtractionResult:
        """Extract Etruscan glosses from text.

        Args:
            text: The text to search
            language: 'latin', 'greek', or 'auto' to detect

        Returns:
            ExtractionResult with all matches
        """
        if not text:
            return ExtractionResult(text=text)

        # Auto-detect language based on character set
        if language == "auto":
            # Check for Greek characters
            greek_chars = sum(1 for c in text if '\u0370' <= c <= '\u03FF' or '\u1F00' <= c <= '\u1FFF')
            if greek_chars > len(text) * 0.1:  # More than 10% Greek
                language = "greek"
            else:
                language = "latin"

        result = ExtractionResult(text=text, language=language)
        seen_matches: set[tuple[str, int]] = set()  # (word, position) to avoid duplicates

        # Apply Latin patterns
        if language in ("latin", "auto"):
            for pattern, compiled in self._latin_patterns:
                result.patterns_applied += 1
                for match in compiled.finditer(text):
                    try:
                        word = match.group(pattern.word_group)
                    except IndexError:
                        word = match.group(1)

                    word = self._normalize_word(word)
                    if not word or len(word) < 2:
                        continue

                    # Skip if we've seen this word at this position
                    key = (word.lower(), match.start())
                    if key in seen_matches:
                        continue
                    seen_matches.add(key)

                    context_before, context_after = self._get_context(
                        text, match.start(), match.end()
                    )

                    # Extract meaning hint if pattern supports it
                    meaning_hint = None
                    if pattern.meaning_group:
                        try:
                            meaning_hint = match.group(pattern.meaning_group)
                        except IndexError:
                            pass

                    pm = PatternMatch(
                        pattern_name=pattern.name,
                        etruscan_word=word,
                        full_match=match.group(0),
                        context_before=context_before,
                        context_after=context_after,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        confidence=pattern.confidence,
                        meaning_hint=meaning_hint,
                    )
                    result.matches.append(pm)

        # Apply Greek patterns
        if language in ("greek", "auto") and self.include_greek:
            for pattern, compiled in self._greek_patterns:
                result.patterns_applied += 1
                for match in compiled.finditer(text):
                    try:
                        word = match.group(pattern.word_group)
                    except IndexError:
                        word = match.group(1)

                    word = self._normalize_word(word)
                    if not word or len(word) < 2:
                        continue

                    key = (word.lower(), match.start())
                    if key in seen_matches:
                        continue
                    seen_matches.add(key)

                    context_before, context_after = self._get_context(
                        text, match.start(), match.end()
                    )

                    pm = PatternMatch(
                        pattern_name=pattern.name,
                        etruscan_word=word,
                        full_match=match.group(0),
                        context_before=context_before,
                        context_after=context_after,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        confidence=pattern.confidence,
                    )
                    result.matches.append(pm)

        # Sort by position in text
        result.matches.sort(key=lambda m: m.start_pos)

        return result

    def extract_with_pattern(self, text: str, pattern_name: str) -> ExtractionResult:
        """Extract using only a specific pattern.

        Args:
            text: The text to search
            pattern_name: Name of the pattern to use

        Returns:
            ExtractionResult with matches from that pattern only
        """
        pattern = get_pattern_by_name(pattern_name)
        if not pattern:
            return ExtractionResult(text=text)

        result = ExtractionResult(text=text, language="latin")
        compiled = re.compile(pattern.regex, re.IGNORECASE | re.MULTILINE)
        result.patterns_applied = 1

        for match in compiled.finditer(text):
            try:
                word = match.group(pattern.word_group)
            except IndexError:
                word = match.group(1)

            word = self._normalize_word(word)
            if not word or len(word) < 2:
                continue

            context_before, context_after = self._get_context(
                text, match.start(), match.end()
            )

            pm = PatternMatch(
                pattern_name=pattern.name,
                etruscan_word=word,
                full_match=match.group(0),
                context_before=context_before,
                context_after=context_after,
                start_pos=match.start(),
                end_pos=match.end(),
                confidence=pattern.confidence,
            )
            result.matches.append(pm)

        return result

    def test_pattern(self, text: str, pattern_name: str) -> bool:
        """Test if a specific pattern matches the text.

        Args:
            text: Text to test
            pattern_name: Pattern name

        Returns:
            True if pattern matches
        """
        result = self.extract_with_pattern(text, pattern_name)
        return result.found_glosses

    def get_pattern_stats(self) -> dict:
        """Get statistics about loaded patterns."""
        return {
            "latin_patterns": len(self._latin_patterns),
            "greek_patterns": len(self._greek_patterns),
            "total_patterns": len(self._latin_patterns) + len(self._greek_patterns),
            "min_confidence": self.min_confidence,
        }
