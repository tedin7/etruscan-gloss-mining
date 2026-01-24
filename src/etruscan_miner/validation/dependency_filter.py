"""Dependency parsing filter for validating Etruscan attributions.

Uses spaCy (or stanza as fallback) to check if a sentence grammatically
attributes a word to the Etruscans. This filters out generic Latin etymology
patterns that don't specifically mention Etruscan origin.

Layer 1 of the three-layer NLP filter:
- Layer 1: Dependency parsing (this module) - grammatical attribution check
- Layer 2: Character n-gram classifier - Etruscan phonotactics
- Layer 3: Context classifier - semantic validation

Example:
    >>> df = DependencyFilter()
    >>> df.has_etruscan_attribution('Tusci vocant subulo')  # True
    >>> df.has_etruscan_attribution('Lanterna vocatur quod...')  # False
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class AttributionDetails:
    """Detailed results from attribution analysis."""

    text: str
    has_attribution: bool
    method: str  # 'spacy', 'stanza', 'regex', 'fallback'
    subject_found: Optional[str] = None
    verb_found: Optional[str] = None
    object_found: Optional[str] = None
    etruscan_markers: list[str] = field(default_factory=list)
    confidence: float = 0.0
    reason: str = ""


class DependencyFilter:
    """Filter candidates based on grammatical attribution to Etruscans.

    Checks if the subject of a sentence contains Etruscan marker words
    (Tusci, Etrusci, Tyrrheni, etc.) to validate that the extracted word
    is attributed to the Etruscans, not just a generic Latin etymology.
    """

    # Latin markers for Etruscan attribution
    LATIN_MARKERS = {
        # Nominative forms (subject)
        "tusci", "etrusci", "tyrrheni", "tuscos", "etruscos", "tyrrhenos",
        "tuscus", "etruscus", "tyrrhenus",
        # Ablative forms (context)
        "tuscis", "etruscis", "tyrrhenis",
        # Adjective forms
        "tusca", "etrusca", "tyrrhena",
        "tuscum", "etruscum", "tyrrhenum",
        "tusco", "etrusco", "tyrrheno",
    }

    # Greek markers (Tyrrhenians)
    GREEK_MARKERS = {
        # Nominative plural
        "tyrrheni", "tyrsenoi",  # Latin transliteration
        # Unicode Greek
        "\u03a4\u03c5\u03c1\u03c1\u03b7\u03bd\u03bf\u03af",  # Tyrrhenoi
        "\u03a4\u03c5\u03c1\u03c3\u03b7\u03bd\u03bf\u03af",  # Tyrsenoi
        # Common variants
        "\u03c4\u03c5\u03c1\u03c1\u03b7\u03bd\u03bf\u03af",  # lowercase
        "\u03c4\u03c5\u03c1\u03c3\u03b7\u03bd\u03bf\u03af",
        # Nominative singular
        "\u03a4\u03c5\u03c1\u03c1\u03b7\u03bd\u03cc\u03c2",
        "\u03c4\u03c5\u03c1\u03c1\u03b7\u03bd\u03cc\u03c2",
    }

    # Verbs indicating naming/calling
    ATTRIBUTION_VERBS_LATIN = {
        "vocat", "vocant", "vocatur", "vocantur",
        "appellat", "appellant", "appellatur", "appellantur",
        "dicit", "dicunt", "dicitur", "dicuntur",
        "nominat", "nominant", "nominatur", "nominantur",
    }

    ATTRIBUTION_VERBS_GREEK = {
        # kaleo forms (to call)
        "\u03ba\u03b1\u03bb\u03bf\u03cd\u03c3\u03b9",  # kalousi
        "\u03ba\u03b1\u03bb\u03b5\u03af\u03c4\u03b1\u03b9",  # kaleitai
        "\u03ba\u03b1\u03bb\u03bf\u03cd\u03bc\u03b5\u03bd\u03bf\u03c2",  # kaloumenos
        # onomazo forms (to name)
        "\u03bf\u03bd\u03bf\u03bc\u03ac\u03b6\u03bf\u03c5\u03c3\u03b9",
        "\u03bf\u03bd\u03bf\u03bc\u03ac\u03b6\u03b5\u03c4\u03b1\u03b9",
    }

    # Generic etymology patterns (no Etruscan subject)
    GENERIC_PATTERNS = [
        r"vocatur\s+(?:quod|quia|ab?)\b",  # "is called because/from"
        r"dicitur\s+(?:quod|quia|ab?)\b",  # "is said because/from"
        r"appellatur\s+(?:quod|quia|ab?)\b",  # "is named because/from"
        r"nominatur\s+(?:quod|quia|ab?)\b",  # "is named because/from"
        r"dictum\s+(?:est\s+)?(?:quod|quia|ab?)\b",  # "was said because/from"
        r"nomen\s+(?:habet|accepit)\s+(?:quod|quia|ab?)\b",  # "has name because"
    ]

    def __init__(self, use_spacy: bool = True, use_stanza: bool = True):
        """Initialize the dependency filter.

        Args:
            use_spacy: Try to use spaCy for dependency parsing
            use_stanza: Try to use stanza as fallback if spaCy unavailable
        """
        self._nlp = None
        self._method = "fallback"
        self._model_error: Optional[str] = None

        # Try to load NLP model
        if use_spacy:
            self._try_load_spacy()

        if self._nlp is None and use_stanza:
            self._try_load_stanza()

        if self._nlp is None:
            logger.warning(
                "No NLP model available. Using regex fallback. "
                "Install spaCy (python -m spacy download la_core_web_sm) or "
                "stanza for better accuracy."
            )
            if self._model_error:
                logger.debug(f"Model loading error: {self._model_error}")

        # Compile generic patterns
        self._generic_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.GENERIC_PATTERNS
        ]

    def _try_load_spacy(self) -> None:
        """Try to load spaCy Latin model."""
        try:
            import spacy

            # Try la_core_web_sm first, then la_core_news_sm
            for model_name in ["la_core_web_sm", "la_core_news_sm"]:
                try:
                    self._nlp = spacy.load(model_name)
                    self._method = "spacy"
                    logger.info(f"Loaded spaCy model: {model_name}")
                    return
                except OSError:
                    continue

            # Model not found
            self._model_error = (
                "spaCy installed but Latin model not found. "
                "Run: python -m spacy download la_core_web_sm"
            )
            logger.debug(self._model_error)

        except ImportError:
            self._model_error = "spaCy not installed"
            logger.debug("spaCy not available")
        except Exception as e:
            self._model_error = f"spaCy error: {e}"
            logger.debug(f"spaCy loading error: {e}")

    def _try_load_stanza(self) -> None:
        """Try to load stanza Latin model."""
        try:
            import stanza

            # Check if Latin model is downloaded
            try:
                self._nlp = stanza.Pipeline(
                    "la",
                    processors="tokenize,pos,lemma,depparse",
                    verbose=False,
                )
                self._method = "stanza"
                logger.info("Loaded stanza Latin model")
                return
            except Exception:
                # Try downloading
                try:
                    stanza.download("la", verbose=False)
                    self._nlp = stanza.Pipeline(
                        "la",
                        processors="tokenize,pos,lemma,depparse",
                        verbose=False,
                    )
                    self._method = "stanza"
                    logger.info("Downloaded and loaded stanza Latin model")
                    return
                except Exception as e:
                    self._model_error = f"stanza model error: {e}"

        except ImportError:
            if not self._model_error:
                self._model_error = "Neither spaCy nor stanza installed"
            logger.debug("stanza not available")
        except Exception as e:
            self._model_error = f"stanza error: {e}"
            logger.debug(f"stanza loading error: {e}")

    def _find_markers(self, text: str) -> list[str]:
        """Find Etruscan marker words in text."""
        text_lower = text.lower()
        found = []

        # Check Latin markers
        for marker in self.LATIN_MARKERS:
            if re.search(rf"\b{re.escape(marker)}\b", text_lower):
                found.append(marker)

        # Check Greek markers
        for marker in self.GREEK_MARKERS:
            if marker.lower() in text_lower:
                found.append(marker)

        return found

    def _is_generic_etymology(self, text: str) -> bool:
        """Check if text matches generic etymology patterns without Etruscan subject."""
        for pattern in self._generic_patterns:
            if pattern.search(text):
                # Found generic pattern - check if Etruscan marker present
                markers = self._find_markers(text)
                if not markers:
                    return True
        return False

    def _check_with_spacy(self, text: str) -> AttributionDetails:
        """Use spaCy dependency parsing for attribution check."""
        doc = self._nlp(text)

        markers_found = []
        verb_found = None
        subject_found = None
        object_found = None
        has_etruscan_subject = False

        for sent in doc.sents:
            for token in sent:
                # Check for Etruscan markers
                if token.text.lower() in self.LATIN_MARKERS:
                    markers_found.append(token.text)
                    # Check if it's a subject
                    if token.dep_ in ("nsubj", "nsubj:pass"):
                        has_etruscan_subject = True
                        subject_found = token.text

                # Track verbs
                if token.pos_ == "VERB" and token.lemma_.lower() in {
                    "vocare", "appellare", "dicere", "nominare"
                }:
                    verb_found = token.text

                # Track objects
                if token.dep_ in ("obj", "dobj", "obl"):
                    if not object_found:
                        object_found = token.text

        # Also check for markers in the full text (spaCy might miss some)
        text_markers = self._find_markers(text)
        markers_found = list(set(markers_found + text_markers))

        has_attribution = bool(markers_found) and not self._is_generic_etymology(text)

        # Higher confidence if we found an Etruscan subject
        confidence = 0.9 if has_etruscan_subject else (0.7 if markers_found else 0.0)

        return AttributionDetails(
            text=text,
            has_attribution=has_attribution,
            method="spacy",
            subject_found=subject_found,
            verb_found=verb_found,
            object_found=object_found,
            etruscan_markers=markers_found,
            confidence=confidence,
            reason=(
                f"Etruscan subject found: {subject_found}"
                if has_etruscan_subject
                else (
                    f"Etruscan markers found: {markers_found}"
                    if markers_found
                    else "No Etruscan attribution found"
                )
            ),
        )

    def _check_with_stanza(self, text: str) -> AttributionDetails:
        """Use stanza dependency parsing for attribution check."""
        doc = self._nlp(text)

        markers_found = []
        verb_found = None
        subject_found = None
        object_found = None
        has_etruscan_subject = False

        for sent in doc.sentences:
            for word in sent.words:
                # Check for Etruscan markers
                if word.text.lower() in self.LATIN_MARKERS:
                    markers_found.append(word.text)
                    # Check if it's a subject
                    if word.deprel in ("nsubj", "nsubj:pass"):
                        has_etruscan_subject = True
                        subject_found = word.text

                # Track verbs
                if word.upos == "VERB" and word.lemma and word.lemma.lower() in {
                    "vocare", "appellare", "dicere", "nominare"
                }:
                    verb_found = word.text

                # Track objects
                if word.deprel in ("obj", "obl"):
                    if not object_found:
                        object_found = word.text

        # Also check for markers in the full text
        text_markers = self._find_markers(text)
        markers_found = list(set(markers_found + text_markers))

        has_attribution = bool(markers_found) and not self._is_generic_etymology(text)

        confidence = 0.9 if has_etruscan_subject else (0.7 if markers_found else 0.0)

        return AttributionDetails(
            text=text,
            has_attribution=has_attribution,
            method="stanza",
            subject_found=subject_found,
            verb_found=verb_found,
            object_found=object_found,
            etruscan_markers=markers_found,
            confidence=confidence,
            reason=(
                f"Etruscan subject found: {subject_found}"
                if has_etruscan_subject
                else (
                    f"Etruscan markers found: {markers_found}"
                    if markers_found
                    else "No Etruscan attribution found"
                )
            ),
        )

    def _check_with_regex(self, text: str) -> AttributionDetails:
        """Fallback regex-based check when no NLP model available."""
        markers = self._find_markers(text)

        # Check for generic etymology (no Etruscan subject)
        is_generic = self._is_generic_etymology(text)

        # Look for attribution verbs
        text_lower = text.lower()
        verb_found = None
        for verb in self.ATTRIBUTION_VERBS_LATIN:
            if verb in text_lower:
                verb_found = verb
                break

        # Simple heuristic: markers + verb = attribution
        # Unless it's a generic pattern
        has_attribution = bool(markers) and not is_generic

        # Lower confidence for regex-only
        confidence = 0.6 if has_attribution else 0.0

        return AttributionDetails(
            text=text,
            has_attribution=has_attribution,
            method="regex",
            subject_found=markers[0] if markers else None,
            verb_found=verb_found,
            object_found=None,
            etruscan_markers=markers,
            confidence=confidence,
            reason=(
                f"Regex match: markers={markers}, verb={verb_found}"
                if has_attribution
                else (
                    "Generic etymology pattern (no Etruscan subject)"
                    if is_generic
                    else "No Etruscan markers found"
                )
            ),
        )

    def get_attribution_details(self, text: str) -> AttributionDetails:
        """Get detailed attribution analysis for a text.

        Args:
            text: Latin or Greek text to analyze

        Returns:
            AttributionDetails with full analysis results
        """
        if not text or not text.strip():
            return AttributionDetails(
                text=text or "",
                has_attribution=False,
                method="fallback",
                confidence=0.0,
                reason="Empty text",
            )

        # Use available NLP method
        if self._method == "spacy" and self._nlp:
            return self._check_with_spacy(text)
        elif self._method == "stanza" and self._nlp:
            return self._check_with_stanza(text)
        else:
            return self._check_with_regex(text)

    def has_etruscan_attribution(self, text: str) -> bool:
        """Check if text has Etruscan attribution.

        This is the main method for filtering. Returns True if the text
        grammatically attributes a word to the Etruscans.

        Args:
            text: Latin or Greek text to analyze

        Returns:
            True if Etruscan attribution found, False otherwise.
            Returns True (permissive) if no NLP model available and
            regex check is inconclusive.
        """
        details = self.get_attribution_details(text)

        # If using fallback with no markers found, be permissive
        # (don't block potentially valid candidates)
        if details.method == "regex" and not details.etruscan_markers:
            # If we can't tell, don't block
            logger.debug(
                f"Regex fallback inconclusive for: {text[:50]}... "
                "Returning True (permissive)"
            )
            return True

        return details.has_attribution

    def has_etruscan_subject(self, text: str) -> bool:
        """Alias for has_etruscan_attribution.

        Args:
            text: Latin or Greek text to analyze

        Returns:
            True if Etruscan subject/attribution found
        """
        return self.has_etruscan_attribution(text)

    @property
    def method(self) -> str:
        """Get the NLP method being used."""
        return self._method

    @property
    def is_model_available(self) -> bool:
        """Check if an NLP model is loaded."""
        return self._nlp is not None

    @property
    def model_error(self) -> Optional[str]:
        """Get any error from model loading."""
        return self._model_error


# Convenience alias
DepFilter = DependencyFilter
