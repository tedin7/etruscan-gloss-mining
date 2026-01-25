"""Etruscan name expander.

Expands known Etruscan theonyms (god names) and anthroponyms
(personal names) to predict variant forms that may appear in
Latin and Greek texts. Names are particularly valuable because
they preserve Etruscan morphology even when embedded in other languages.

Examples:
- Tinia → Tinial, Tinias, Tinas, Tiniae
- Larth → Larthal, Larthia, Larthi
"""

import re
from dataclasses import dataclass, field
from typing import Optional

from .morphology import KNOWN_MORPHEMES


@dataclass
class ExpandedName:
    """An expanded form of an Etruscan name."""

    base_name: str
    expanded_form: str
    form_type: str  # 'genitive', 'nominative', 'latinized', 'grecized'
    language_context: str  # 'etruscan', 'latin', 'greek'
    confidence: float
    search_pattern: str
    notes: str = ""


# Known Etruscan theonyms with their forms
ETRUSCAN_THEONYMS = {
    "tinia": {
        "meaning": "Jupiter/Sky God",
        "latin_form": "Tina",
        "greek_form": "Zeus (identified)",
        "variants": ["tins", "tinas", "tinia", "tini"],
    },
    "uni": {
        "meaning": "Juno/Queen of Gods",
        "latin_form": "Iuno",
        "greek_form": "Hera (identified)",
        "variants": ["uni", "unia", "unis"],
    },
    "menrva": {
        "meaning": "Minerva/Wisdom Goddess",
        "latin_form": "Minerva",
        "greek_form": "Athena (identified)",
        "variants": ["menrva", "menerva", "menfra", "menrvas"],
    },
    "turan": {
        "meaning": "Venus/Love Goddess",
        "latin_form": "Venus (identified)",
        "greek_form": "Aphrodite (identified)",
        "variants": ["turan", "turans", "turanna"],
    },
    "sethlans": {
        "meaning": "Vulcan/Smith God",
        "latin_form": "Vulcanus",
        "greek_form": "Hephaistos (identified)",
        "variants": ["sethlans", "sethlan", "seθlan"],
    },
    "velchans": {
        "meaning": "Vulcan (variant)",
        "latin_form": "Vulcanus",
        "greek_form": "Hephaistos",
        "variants": ["velchans", "velchan", "velχan"],
    },
    "fufluns": {
        "meaning": "Dionysus/Wine God",
        "latin_form": "Liber",
        "greek_form": "Dionysos (identified)",
        "variants": ["fufluns", "fuflun", "pacha"],
    },
    "aplu": {
        "meaning": "Apollo",
        "latin_form": "Apollo",
        "greek_form": "Apollon",
        "variants": ["aplu", "apulu", "aplus"],
    },
    "aritimi": {
        "meaning": "Artemis/Hunt Goddess",
        "latin_form": "Diana",
        "greek_form": "Artemis",
        "variants": ["aritimi", "artimi", "artumes"],
    },
    "nethuns": {
        "meaning": "Neptune/Sea God",
        "latin_form": "Neptunus",
        "greek_form": "Poseidon (identified)",
        "variants": ["nethuns", "nethun", "neθuns"],
    },
    "maris": {
        "meaning": "Mars (child deity)",
        "latin_form": "Mars",
        "greek_form": "Ares (identified)",
        "variants": ["maris", "mari", "mares"],
    },
    "laran": {
        "meaning": "War God",
        "latin_form": "Mars?",
        "greek_form": "Ares?",
        "variants": ["laran", "larans", "larun"],
    },
    "cilens": {
        "meaning": "Fate/Night Goddess",
        "latin_form": "?",
        "greek_form": "?",
        "variants": ["cilens", "cilen", "cilans"],
    },
    "cautha": {
        "meaning": "Sun Goddess",
        "latin_form": "?",
        "greek_form": "Eos?",
        "variants": ["cautha", "cavtha", "cauθa"],
    },
    "thesan": {
        "meaning": "Dawn Goddess",
        "latin_form": "Aurora",
        "greek_form": "Eos",
        "variants": ["thesan", "θesan", "thesans"],
    },
    "selvans": {
        "meaning": "Forest God",
        "latin_form": "Silvanus",
        "greek_form": "?",
        "variants": ["selvans", "selvan", "silvan"],
    },
}

# Common Etruscan personal name elements
ANTHROPONYM_ELEMENTS = {
    "larth": {"meaning": "lord/title", "gender": "male"},
    "vel": {"meaning": "?", "gender": "male"},
    "avle": {"meaning": "?", "gender": "male"},
    "arnth": {"meaning": "?", "gender": "male"},
    "sethre": {"meaning": "?", "gender": "male"},
    "laris": {"meaning": "?", "gender": "male"},
    "thanchvil": {"meaning": "?", "gender": "female"},
    "ramtha": {"meaning": "?", "gender": "female"},
    "velia": {"meaning": "?", "gender": "female"},
    "larthia": {"meaning": "?", "gender": "female"},
    "hastia": {"meaning": "?", "gender": "female"},
}

# Common Etruscan family names (gentilicia)
FAMILY_NAMES = [
    "velna", "spurina", "tarchna", "caecina", "porsenna",
    "mastarna", "tarquinia", "cilnia", "petronia", "maecenas",
]


class NameExpander:
    """Expander for Etruscan names."""

    def __init__(self):
        """Initialize expander."""
        self.theonyms = ETRUSCAN_THEONYMS
        self.anthroponyms = ANTHROPONYM_ELEMENTS
        self.family_names = FAMILY_NAMES
        self.morphemes = KNOWN_MORPHEMES

    def expand_theonym(self, name: str) -> list[ExpandedName]:
        """Expand a theonym to all possible forms.

        Args:
            name: Base theonym

        Returns:
            List of ExpandedName objects
        """
        expansions = []
        name_lower = name.lower()

        # Check if known theonym
        theonym_info = self.theonyms.get(name_lower, {})

        # Add base forms
        if theonym_info.get("variants"):
            for variant in theonym_info["variants"]:
                expansions.append(ExpandedName(
                    base_name=name,
                    expanded_form=variant,
                    form_type="nominative",
                    language_context="etruscan",
                    confidence=0.90,
                    search_pattern=self._build_pattern(variant),
                ))

        # Add case forms
        root = name_lower.rstrip("s").rstrip("n")
        for morpheme in self.morphemes.get("genitive", []):
            gen_form = root + morpheme.form
            expansions.append(ExpandedName(
                base_name=name,
                expanded_form=gen_form,
                form_type="genitive",
                language_context="etruscan",
                confidence=0.70,
                search_pattern=self._build_pattern(gen_form),
            ))

        # Add Latinized forms
        latin_endings = ["ae", "is", "i", "um", "us"]
        for ending in latin_endings:
            latin_form = root + ending
            expansions.append(ExpandedName(
                base_name=name,
                expanded_form=latin_form,
                form_type="latinized",
                language_context="latin",
                confidence=0.60,
                search_pattern=self._build_pattern(latin_form),
            ))

        # Add Grecized forms
        greek_endings = ["os", "on", "es", "as"]
        for ending in greek_endings:
            greek_form = root + ending
            expansions.append(ExpandedName(
                base_name=name,
                expanded_form=greek_form,
                form_type="grecized",
                language_context="greek",
                confidence=0.55,
                search_pattern=self._build_pattern(greek_form),
            ))

        return expansions

    def expand_anthroponym(self, name: str) -> list[ExpandedName]:
        """Expand a personal name to possible forms.

        Args:
            name: Base personal name

        Returns:
            List of ExpandedName objects
        """
        expansions = []
        name_lower = name.lower()

        # Get info if known
        info = self.anthroponyms.get(name_lower, {})

        # Generate case forms
        for category in ["genitive", "locative", "ablative"]:
            for morpheme in self.morphemes.get(category, []):
                form = name_lower + morpheme.form
                expansions.append(ExpandedName(
                    base_name=name,
                    expanded_form=form,
                    form_type=category,
                    language_context="etruscan",
                    confidence=0.65,
                    search_pattern=self._build_pattern(form),
                ))

        # Generate feminine/masculine variants
        if name_lower.endswith("th") or name_lower.endswith("s"):
            # Probably male, generate female variant
            fem_form = name_lower.rstrip("ths") + "ia"
            expansions.append(ExpandedName(
                base_name=name,
                expanded_form=fem_form,
                form_type="feminine",
                language_context="etruscan",
                confidence=0.60,
                search_pattern=self._build_pattern(fem_form),
            ))

        # Latinized forms
        root = name_lower.rstrip("aeiou")
        for ending in ["us", "a", "ius", "ia"]:
            latin_form = root + ending
            expansions.append(ExpandedName(
                base_name=name,
                expanded_form=latin_form,
                form_type="latinized",
                language_context="latin",
                confidence=0.55,
                search_pattern=self._build_pattern(latin_form),
            ))

        return expansions

    def _build_pattern(self, form: str) -> str:
        """Build search pattern for a name form.

        Args:
            form: Name form

        Returns:
            Regex pattern
        """
        # Allow for spelling variations
        pattern = form.lower()

        # Handle Etruscan special characters
        subs = [
            ("th", "(?:th|θ)"),
            ("ch", "(?:ch|χ)"),
            ("ph", "(?:ph|φ)"),
        ]
        for old, new in subs:
            pattern = pattern.replace(old, new)

        return f"\\b{pattern}\\b"

    def search_names_in_text(self, text: str, names: list[str] = None) -> list[ExpandedName]:
        """Search for expanded name forms in text.

        Args:
            text: Text to search
            names: Specific names to expand (or all known if None)

        Returns:
            List of found ExpandedName objects
        """
        found = []
        text_lower = text.lower()

        # Get names to search
        if names is None:
            names = list(self.theonyms.keys()) + list(self.anthroponyms.keys())

        for name in names:
            # Try theonym expansion
            if name.lower() in self.theonyms:
                expansions = self.expand_theonym(name)
            else:
                expansions = self.expand_anthroponym(name)

            for exp in expansions:
                pattern = re.compile(exp.search_pattern, re.IGNORECASE)
                if pattern.search(text_lower):
                    exp.notes = "Found in text"
                    found.append(exp)

        return found


def expand_theonyms(names: list[str] = None) -> list[ExpandedName]:
    """Expand theonyms to all possible forms.

    Args:
        names: List of theonym bases (or all known if None)

    Returns:
        List of ExpandedName objects
    """
    expander = NameExpander()

    if names is None:
        names = list(ETRUSCAN_THEONYMS.keys())

    all_expansions = []
    for name in names:
        all_expansions.extend(expander.expand_theonym(name))

    return all_expansions


def expand_anthroponyms(names: list[str] = None) -> list[ExpandedName]:
    """Expand anthroponyms to all possible forms.

    Args:
        names: List of personal names (or all known if None)

    Returns:
        List of ExpandedName objects
    """
    expander = NameExpander()

    if names is None:
        names = list(ANTHROPONYM_ELEMENTS.keys())

    all_expansions = []
    for name in names:
        all_expansions.extend(expander.expand_anthroponym(name))

    return all_expansions
