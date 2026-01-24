"""Tests for Etruscan gloss pattern matching."""

import json
import sys
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from etruscan_miner.patterns.extractor import GlossExtractor
from etruscan_miner.patterns.latin_patterns import (
    ALL_PATTERNS,
    get_pattern_by_name,
    get_patterns_by_confidence,
)


@pytest.fixture
def extractor():
    """Create a GlossExtractor instance."""
    return GlossExtractor(min_confidence=0.0)


@pytest.fixture
def sample_passages():
    """Load sample passages from fixtures."""
    fixtures_path = Path(__file__).parent / "fixtures" / "sample_passages.json"
    with open(fixtures_path) as f:
        return json.load(f)


class TestLatinPatterns:
    """Test Latin pattern definitions."""

    def test_all_patterns_have_required_fields(self):
        """All patterns should have name, regex, description, confidence."""
        for pattern in ALL_PATTERNS:
            assert pattern.name, "Pattern missing name"
            assert pattern.regex, f"Pattern {pattern.name} missing regex"
            assert pattern.description, f"Pattern {pattern.name} missing description"
            assert 0 <= pattern.confidence <= 1, f"Pattern {pattern.name} invalid confidence"

    def test_get_pattern_by_name(self):
        """Should retrieve pattern by name."""
        pattern = get_pattern_by_name("tusci_vocant")
        assert pattern is not None
        assert pattern.name == "tusci_vocant"
        assert pattern.confidence == 0.90

    def test_get_patterns_by_confidence(self):
        """Should filter patterns by confidence threshold."""
        high_conf = get_patterns_by_confidence(0.85)
        assert len(high_conf) > 0
        assert all(p.confidence >= 0.85 for p in high_conf)

        low_conf = get_patterns_by_confidence(0.0)
        assert len(low_conf) >= len(high_conf)


class TestGlossExtractor:
    """Test GlossExtractor functionality."""

    def test_extractor_initialization(self, extractor):
        """Extractor should initialize with patterns."""
        stats = extractor.get_pattern_stats()
        assert stats["latin_patterns"] > 0
        assert stats["total_patterns"] > 0

    def test_extract_empty_text(self, extractor):
        """Empty text should return empty result."""
        result = extractor.extract("")
        assert not result.found_glosses
        assert len(result.matches) == 0

    def test_extract_no_match(self, extractor):
        """Text without Etruscan references should not match."""
        result = extractor.extract("Roma caput mundi est.")
        assert not result.found_glosses

    def test_extract_tusci_vocant(self, extractor):
        """Should match 'Tusci vocant' pattern."""
        text = "Tusci vocant subulo quod nos tibicinem"
        result = extractor.extract(text)

        assert result.found_glosses
        assert len(result.matches) >= 1

        match = result.matches[0]
        assert match.etruscan_word.lower() == "subulo"
        assert match.pattern_name == "tusci_vocant"
        assert match.confidence == 0.90

    def test_extract_etrusca_lingua(self, extractor):
        """Should match 'Etrusca lingua' pattern."""
        text = "aesar enim Etrusca lingua deus dicitur"
        result = extractor.extract(text)

        assert result.found_glosses
        words = result.get_unique_words()
        # Should find something after "Etrusca lingua"
        assert len(words) >= 1

    def test_extract_etrusco_vocabulo(self, extractor):
        """Should match 'Etrusco vocabulo' pattern."""
        text = "lanista Etrusco vocabulo appellatur"
        result = extractor.extract(text)

        assert result.found_glosses
        assert any(m.etruscan_word.lower() == "appellatur" for m in result.matches)

    def test_extract_apud_etruscos(self, extractor):
        """Should match 'apud Etruscos' pattern."""
        text = "apud Etruscos caseus maxime laudatur"
        result = extractor.extract(text)

        assert result.found_glosses
        assert any(m.pattern_name == "apud_etruscos" for m in result.matches)

    def test_extract_context(self, extractor):
        """Should extract context around matches."""
        text = "Varro scribit: Tusci vocant subulo quod nos tibicinem dicimus"
        result = extractor.extract(text)

        assert result.found_glosses
        match = result.matches[0]
        assert match.context_before  # Should have "Varro scribit:"
        assert match.context_after   # Should have "quod nos tibicinem"

    def test_extract_multiple_matches(self, extractor):
        """Should find multiple glosses in one text."""
        text = "Tusci vocant subulo tibicinem, et Tyrrheni vocant larem deum"
        result = extractor.extract(text)

        assert result.found_glosses
        assert len(result.matches) >= 2

    def test_high_confidence_filter(self, extractor):
        """Should filter high confidence matches."""
        text = "Tusci vocant subulo et atrium Etrusca origine est"
        result = extractor.extract(text)

        high_conf = result.get_high_confidence_matches(0.85)
        # tusci_vocant has 0.90, etrusca_origine has 0.70
        assert all(m.confidence >= 0.85 for m in high_conf)

    def test_case_insensitive(self, extractor):
        """Patterns should be case insensitive for Latin."""
        text1 = "TUSCI VOCANT subulo"
        text2 = "tusci vocant subulo"

        result1 = extractor.extract(text1)
        result2 = extractor.extract(text2)

        assert result1.found_glosses
        assert result2.found_glosses


class TestKnownGlosses:
    """Test against known glosses from fixtures."""

    def test_known_glosses(self, extractor, sample_passages):
        """All known glosses should be detected."""
        known = sample_passages["known_glosses"]
        detected = 0
        failed = []

        for gloss in known:
            result = extractor.extract(gloss["text"])
            expected = gloss["expected_word"].lower()

            found_words = [m.etruscan_word.lower() for m in result.matches]

            if expected in found_words or any(expected in w for w in found_words):
                detected += 1
            else:
                failed.append({
                    "id": gloss["id"],
                    "text": gloss["text"],
                    "expected": expected,
                    "found": found_words,
                })

        # Calculate recall
        recall = detected / len(known)
        print(f"\nKnown gloss detection: {detected}/{len(known)} = {recall:.1%}")

        if failed:
            print("Failed cases:")
            for f in failed:
                print(f"  - {f['id']}: expected '{f['expected']}', found {f['found']}")

        # We should detect at least 70% of known glosses
        assert recall >= 0.70, f"Recall too low: {recall:.1%}"

    def test_negative_examples(self, extractor, sample_passages):
        """Negative examples should not match Etruscan patterns."""
        negatives = sample_passages["negative_examples"]
        false_positives = []

        for neg in negatives:
            result = extractor.extract(neg["text"])
            # Check if any match looks like an Etruscan gloss
            # (some matches might be valid Latin words, but shouldn't trigger
            # Etruscan-specific patterns with high confidence)
            high_conf = result.get_high_confidence_matches(0.80)
            if high_conf:
                false_positives.append({
                    "id": neg["id"],
                    "text": neg["text"],
                    "matches": [(m.pattern_name, m.etruscan_word) for m in high_conf],
                })

        if false_positives:
            print("\nFalse positives:")
            for fp in false_positives:
                print(f"  - {fp['id']}: {fp['matches']}")

        # Should have very few false positives
        precision = 1 - (len(false_positives) / len(negatives))
        assert precision >= 0.80, f"Precision too low: {precision:.1%}"

    def test_complex_passages(self, extractor, sample_passages):
        """Complex passages with multiple glosses."""
        complex_tests = sample_passages["complex_passages"]

        for test in complex_tests:
            result = extractor.extract(test["text"])
            expected_words = [w.lower() for w in test["expected_words"]]
            found_words = result.get_unique_words()

            for expected in expected_words:
                assert any(
                    expected in w or w in expected for w in found_words
                ), f"Expected '{expected}' in {test['id']}, found {found_words}"


class TestPatternSpecific:
    """Test specific patterns."""

    def test_varro_pattern(self, extractor):
        """Test Varro-specific pattern."""
        text = "Tusci enim tibicinem subulo vocant"
        result = extractor.extract(text)

        assert result.found_glosses
        # Should match either varro_tusci or tusci_vocant
        pattern_names = [m.pattern_name for m in result.matches]
        assert any("tusci" in p or "varro" in p for p in pattern_names)

    def test_tyrrheni_pattern(self, extractor):
        """Test Tyrrheni (Greek name for Etruscans) pattern."""
        text = "Tyrrheni vocant larem domesticum deum"
        result = extractor.extract(text)

        assert result.found_glosses
        assert any(m.pattern_name == "tyrrheni_vocant" for m in result.matches)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
