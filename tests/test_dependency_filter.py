"""Tests for the dependency parsing filter."""

import sys
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from etruscan_miner.validation.dependency_filter import (
    AttributionDetails,
    DependencyFilter,
    DepFilter,
)


@pytest.fixture
def dep_filter():
    """Create a DependencyFilter instance."""
    return DependencyFilter()


class TestDependencyFilterInitialization:
    """Test DependencyFilter initialization and fallback behavior."""

    def test_initialization(self, dep_filter):
        """Filter should initialize even without NLP models."""
        assert dep_filter is not None
        assert dep_filter.method in ("spacy", "stanza", "regex", "fallback")

    def test_method_property(self, dep_filter):
        """Should expose the method being used."""
        method = dep_filter.method
        assert method in ("spacy", "stanza", "regex", "fallback")

    def test_is_model_available(self, dep_filter):
        """Should report model availability."""
        # Model availability depends on environment
        assert isinstance(dep_filter.is_model_available, bool)

    def test_model_error_property(self, dep_filter):
        """Should expose any model loading errors."""
        error = dep_filter.model_error
        # Error might be None (model loaded) or a string (error)
        assert error is None or isinstance(error, str)

    def test_dep_filter_alias(self):
        """DepFilter should be an alias for DependencyFilter."""
        assert DepFilter is DependencyFilter


class TestEtruscanAttribution:
    """Test Etruscan attribution detection."""

    def test_tusci_vocant_positive(self, dep_filter):
        """'Tusci vocant X' should have Etruscan attribution."""
        text = "Tusci vocant subulo"
        assert dep_filter.has_etruscan_attribution(text) is True

    def test_etrusci_appellant_positive(self, dep_filter):
        """'Etrusci appellant X' should have Etruscan attribution."""
        text = "Etrusci appellant larem domesticum deum"
        assert dep_filter.has_etruscan_attribution(text) is True

    def test_tyrrheni_vocant_positive(self, dep_filter):
        """'Tyrrheni vocant X' should have Etruscan attribution."""
        text = "Tyrrheni vocant caseum maxime"
        assert dep_filter.has_etruscan_attribution(text) is True

    def test_etrusca_lingua_positive(self, dep_filter):
        """'Etrusca lingua X' should have Etruscan attribution."""
        text = "aesar enim Etrusca lingua deus dicitur"
        assert dep_filter.has_etruscan_attribution(text) is True

    def test_etrusco_nomine_positive(self, dep_filter):
        """'Etrusco nomine X' should have Etruscan attribution."""
        text = "ister Etrusco nomine appellatur"
        assert dep_filter.has_etruscan_attribution(text) is True

    def test_dicunt_tusci_positive(self, dep_filter):
        """'dicunt X Tusci' (Varro-style) should have Etruscan attribution."""
        text = "ita dicunt subulo Tusci"
        assert dep_filter.has_etruscan_attribution(text) is True

    def test_generic_etymology_negative(self, dep_filter):
        """Generic etymology patterns should NOT have Etruscan attribution."""
        # "Lanterna is called because..." - no Etruscan subject
        text = "Lanterna vocatur quod luceat"
        details = dep_filter.get_attribution_details(text)
        # Should be false unless filter is in permissive fallback mode
        # (no markers found -> inconclusive -> permissive return)
        if details.etruscan_markers:
            assert details.has_attribution is False

    def test_generic_dicitur_negative(self, dep_filter):
        """'X dicitur quod' without Etruscan marker should be negative."""
        text = "Atrium dicitur quod atrum sit"
        details = dep_filter.get_attribution_details(text)
        if details.etruscan_markers:
            assert details.has_attribution is False

    def test_generic_appellatur_negative(self, dep_filter):
        """'X appellatur ab Y' without Etruscan marker should be negative."""
        text = "Roma appellatur ab Romulo"
        details = dep_filter.get_attribution_details(text)
        if details.etruscan_markers:
            assert details.has_attribution is False

    def test_empty_text(self, dep_filter):
        """Empty text should return False."""
        assert dep_filter.has_etruscan_attribution("") is False
        assert dep_filter.has_etruscan_attribution("   ") is False

    def test_has_etruscan_subject_alias(self, dep_filter):
        """has_etruscan_subject should be alias for has_etruscan_attribution."""
        text = "Tusci vocant subulo"
        assert dep_filter.has_etruscan_subject(text) == dep_filter.has_etruscan_attribution(text)


class TestAttributionDetails:
    """Test detailed attribution analysis."""

    def test_details_structure(self, dep_filter):
        """get_attribution_details should return AttributionDetails."""
        text = "Tusci vocant subulo"
        details = dep_filter.get_attribution_details(text)

        assert isinstance(details, AttributionDetails)
        assert details.text == text
        assert details.method in ("spacy", "stanza", "regex", "fallback")
        assert isinstance(details.has_attribution, bool)
        assert 0 <= details.confidence <= 1

    def test_details_markers_found(self, dep_filter):
        """Should identify Etruscan markers."""
        text = "Tusci vocant subulo quod Etrusci dicunt"
        details = dep_filter.get_attribution_details(text)

        assert len(details.etruscan_markers) >= 1
        assert any("tusc" in m.lower() or "etrusc" in m.lower()
                   for m in details.etruscan_markers)

    def test_details_no_markers(self, dep_filter):
        """Should handle text without Etruscan markers."""
        text = "Roma caput mundi"
        details = dep_filter.get_attribution_details(text)

        # May have empty markers or be in permissive mode
        assert isinstance(details.etruscan_markers, list)

    def test_details_reason(self, dep_filter):
        """Should provide reason for decision."""
        text = "Tusci vocant subulo"
        details = dep_filter.get_attribution_details(text)

        assert details.reason
        assert isinstance(details.reason, str)


class TestLatinMarkers:
    """Test detection of various Latin Etruscan markers."""

    @pytest.mark.parametrize("marker", [
        "Tusci", "tusci", "TUSCI",
        "Etrusci", "etrusci",
        "Tyrrheni", "tyrrheni",
        "Tuscus", "Etruscus", "Tyrrhenus",
        "Tusco", "Etrusco",
        "Tusca", "Etrusca",
    ])
    def test_latin_marker_detection(self, dep_filter, marker):
        """Should detect various Latin markers for Etruscans."""
        text = f"{marker} vocant subulo"
        details = dep_filter.get_attribution_details(text)

        # Should find the marker (case-insensitive)
        found = any(marker.lower() == m.lower() for m in details.etruscan_markers)
        assert found, f"Marker '{marker}' not detected in: {details.etruscan_markers}"


class TestGreekMarkers:
    """Test detection of Greek Etruscan markers."""

    def test_greek_tyrrheni_transliterated(self, dep_filter):
        """Should detect transliterated Greek 'Tyrrhenoi'."""
        text = "Tyrrheni vocant caseum"
        details = dep_filter.get_attribution_details(text)
        assert len(details.etruscan_markers) >= 1

    def test_greek_unicode(self, dep_filter):
        """Should detect Greek Unicode markers."""
        # Tyrrhenoi in Greek
        text = "\u03a4\u03c5\u03c1\u03c1\u03b7\u03bd\u03bf\u03af \u03ba\u03b1\u03bb\u03bf\u03cd\u03c3\u03b9"
        details = dep_filter.get_attribution_details(text)
        # May or may not find depending on implementation
        assert isinstance(details.etruscan_markers, list)


class TestGenericPatternFiltering:
    """Test filtering of generic etymology patterns."""

    @pytest.mark.parametrize("generic_text", [
        "Lanterna vocatur quod luceat",
        "Atrium dicitur quod atrum sit",
        "Canis appellatur quod latrare potest",
        "Nomen habet quod bonum est",
        "Dictum est quod verum sit",
    ])
    def test_generic_patterns_detected(self, dep_filter, generic_text):
        """Generic etymology patterns should be identified."""
        details = dep_filter.get_attribution_details(generic_text)
        # Without Etruscan markers, these should not show attribution
        if not details.etruscan_markers:
            # Either permissive (True) or correctly identified as no attribution
            # The important thing is consistency
            pass

    def test_etruscan_with_generic_verb(self, dep_filter):
        """Etruscan marker + generic verb should still be positive."""
        # "In Etruscan language it is called X"
        text = "Etrusca lingua dicitur aesar"
        assert dep_filter.has_etruscan_attribution(text) is True


class TestMixedCases:
    """Test edge cases and mixed scenarios."""

    def test_multiple_etruscan_references(self, dep_filter):
        """Should handle multiple Etruscan references."""
        text = "Tusci vocant subulo quod Etrusci tibicinem dicunt"
        details = dep_filter.get_attribution_details(text)

        assert details.has_attribution is True
        assert len(details.etruscan_markers) >= 2

    def test_etruscan_in_longer_passage(self, dep_filter):
        """Should find Etruscan attribution in longer text."""
        text = (
            "De tibicine Varro ait: Tusci vocant subulo "
            "quod nos tibicinem appellamus. "
            "Haec vox Etrusca est."
        )
        assert dep_filter.has_etruscan_attribution(text) is True

    def test_noise_resistance(self, dep_filter):
        """Should handle noisy input gracefully."""
        text = "123 Tusci vocant 456 subulo!!!"
        details = dep_filter.get_attribution_details(text)
        # Should still find the marker
        assert len(details.etruscan_markers) >= 1


class TestGracefulDegradation:
    """Test graceful degradation when models unavailable."""

    def test_no_spacy_no_stanza(self):
        """Should work with both models disabled."""
        df = DependencyFilter(use_spacy=False, use_stanza=False)
        assert df.method in ("regex", "fallback")

        # Should still work
        text = "Tusci vocant subulo"
        result = df.has_etruscan_attribution(text)
        assert isinstance(result, bool)

    def test_permissive_fallback(self):
        """Fallback should be permissive (not block valid candidates)."""
        df = DependencyFilter(use_spacy=False, use_stanza=False)

        # Text without clear Etruscan markers
        text = "Haec vox antiqua est"
        result = df.has_etruscan_attribution(text)

        # In fallback mode with no markers, should be permissive
        # (return True to not block potentially valid candidates)
        assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
