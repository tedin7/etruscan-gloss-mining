"""Etruscan form predictor.

Given known Etruscan roots and morphological patterns, this module
predicts unattested forms that could theoretically exist. These
predicted forms can then be searched for in ancient texts.

Example:
- Known: "clan" (son), genitive suffix "-al"
- Predicted: "clanal" (of the son) - can search texts for this

This approach has found attestations of forms that were previously
unrecognized as Etruscan.
"""

import re
from dataclasses import dataclass, field
from typing import Optional

from .morphology import KNOWN_ROOTS, KNOWN_MORPHEMES, Morpheme


@dataclass
class PredictedForm:
    """A morphologically predicted Etruscan form."""

    base_word: str
    predicted_form: str
    morphological_pattern: str  # e.g., "root + genitive -al"
    expected_meaning: str
    confidence: float
    search_pattern: str  # Regex for searching texts
    found_in_text: bool = False
    attestation: str = ""  # Where found
    notes: str = ""


class FormPredictor:
    """Predictor for unattested Etruscan forms."""

    def __init__(self):
        """Initialize predictor."""
        self.roots = KNOWN_ROOTS
        self.morphemes = KNOWN_MORPHEMES

    def predict_from_root(self, root: str, root_meaning: str = "") -> list[PredictedForm]:
        """Predict all possible forms from a root.

        Args:
            root: Etruscan root
            root_meaning: Meaning of root if known

        Returns:
            List of PredictedForm objects
        """
        predictions = []

        # Get meaning from known roots if not provided
        if not root_meaning and root in self.roots:
            root_meaning = self.roots[root]["meaning"]

        # Generate forms with each suffix type
        for category, morphemes in self.morphemes.items():
            for morpheme in morphemes:
                predicted = root + morpheme.form
                meaning_parts = [root_meaning] if root_meaning else ["?"]
                if morpheme.meaning:
                    meaning_parts.append(morpheme.meaning)

                predictions.append(PredictedForm(
                    base_word=root,
                    predicted_form=predicted,
                    morphological_pattern=f"{root} + {category} -{morpheme.form}",
                    expected_meaning=" ".join(meaning_parts),
                    confidence=0.6 if root in self.roots else 0.4,
                    search_pattern=self._build_search_pattern(predicted),
                ))

                # Also generate with allomorphs
                for allomorph in morpheme.allomorphs:
                    alt_form = root + allomorph
                    predictions.append(PredictedForm(
                        base_word=root,
                        predicted_form=alt_form,
                        morphological_pattern=f"{root} + {category} -{allomorph} (variant)",
                        expected_meaning=" ".join(meaning_parts),
                        confidence=0.5 if root in self.roots else 0.35,
                        search_pattern=self._build_search_pattern(alt_form),
                    ))

        # Generate compound suffixes (e.g., genitive + locative)
        predictions.extend(self._predict_compound_forms(root, root_meaning))

        return predictions

    def _predict_compound_forms(self, root: str, root_meaning: str = "") -> list[PredictedForm]:
        """Predict forms with multiple suffixes.

        Args:
            root: Etruscan root
            root_meaning: Meaning if known

        Returns:
            List of PredictedForm objects
        """
        predictions = []

        # Common compound patterns
        compounds = [
            ("genitive", "locative"),  # e.g., clan-al-θi "in (the possession) of the son"
            ("genitive", "pertinentive"),  # e.g., clan-al-si "for the son's"
            ("plural", "genitive"),  # e.g., ais-ar-al (hypothetical)
        ]

        for cat1, cat2 in compounds:
            for m1 in self.morphemes.get(cat1, [])[:1]:  # Take first morpheme
                for m2 in self.morphemes.get(cat2, [])[:1]:
                    predicted = root + m1.form + m2.form

                    predictions.append(PredictedForm(
                        base_word=root,
                        predicted_form=predicted,
                        morphological_pattern=f"{root} + {cat1} -{m1.form} + {cat2} -{m2.form}",
                        expected_meaning=f"{root_meaning or '?'} [{cat1}] [{cat2}]",
                        confidence=0.35,  # Lower confidence for compounds
                        search_pattern=self._build_search_pattern(predicted),
                        notes="Compound suffix prediction",
                    ))

        return predictions

    def _build_search_pattern(self, form: str) -> str:
        """Build a regex pattern for searching texts.

        Args:
            form: Predicted form

        Returns:
            Regex pattern string
        """
        # Allow for spelling variations
        pattern = form.lower()

        # Common letter substitutions in ancient texts
        substitutions = [
            ("th", "θ"),
            ("ch", "χ"),
            ("ph", "φ"),
            ("c", "[ck]"),
            ("v", "[uv]"),
            ("i", "[ij]"),
        ]

        for old, new in substitutions:
            if old in pattern:
                pattern = pattern.replace(old, f"(?:{old}|{new})")

        return f"\\b{pattern}\\b"

    def predict_all_known_roots(self) -> list[PredictedForm]:
        """Predict forms for all known roots.

        Returns:
            List of all PredictedForm objects
        """
        all_predictions = []

        for root, info in self.roots.items():
            predictions = self.predict_from_root(root, info["meaning"])
            all_predictions.extend(predictions)

        # Sort by confidence
        return sorted(all_predictions, key=lambda p: p.confidence, reverse=True)

    def search_in_text(self, text: str, predictions: list[PredictedForm] = None) -> list[PredictedForm]:
        """Search for predicted forms in text.

        Args:
            text: Text to search
            predictions: List of predictions to search for (or all if None)

        Returns:
            List of found PredictedForm objects with attestation info
        """
        if predictions is None:
            predictions = self.predict_all_known_roots()

        found = []
        text_lower = text.lower()

        for pred in predictions:
            pattern = re.compile(pred.search_pattern, re.IGNORECASE)
            match = pattern.search(text_lower)

            if match:
                # Extract context
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end]

                found_pred = PredictedForm(
                    base_word=pred.base_word,
                    predicted_form=pred.predicted_form,
                    morphological_pattern=pred.morphological_pattern,
                    expected_meaning=pred.expected_meaning,
                    confidence=pred.confidence + 0.2,  # Boost for attestation
                    search_pattern=pred.search_pattern,
                    found_in_text=True,
                    attestation=f"...{context}...",
                )
                found.append(found_pred)

        return found


def predict_forms(root: str, meaning: str = "") -> list[PredictedForm]:
    """Predict all possible forms from a root.

    Args:
        root: Etruscan root
        meaning: Root meaning

    Returns:
        List of PredictedForm objects
    """
    predictor = FormPredictor()
    return predictor.predict_from_root(root, meaning)


def search_predicted_forms(text: str, roots: list[str] = None) -> list[PredictedForm]:
    """Search for predicted forms in text.

    Args:
        text: Text to search
        roots: Specific roots to predict from (or all known if None)

    Returns:
        List of found PredictedForm objects
    """
    predictor = FormPredictor()

    if roots:
        predictions = []
        for root in roots:
            meaning = KNOWN_ROOTS.get(root, {}).get("meaning", "")
            predictions.extend(predictor.predict_from_root(root, meaning))
    else:
        predictions = predictor.predict_all_known_roots()

    return predictor.search_in_text(text, predictions)
