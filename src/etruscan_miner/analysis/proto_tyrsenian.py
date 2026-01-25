"""Proto-Tyrsenian reconstruction for loan identification.

This module reconstructs Proto-Tyrsenian forms using comparative evidence
from the three attested Tyrsenian languages:

1. Etruscan (~10,000 inscriptions, 8th-1st c. BCE)
2. Lemnian (~40 words from Kaminia stele, 6th c. BCE)
3. Raetic (~200 texts from Alpine region, 5th-1st c. BCE)

By establishing sound correspondences between these languages, we can:
- Reconstruct ancestral Proto-Tyrsenian forms
- Identify Latin words that may derive from Proto-Tyrsenian
- Find systematic phonetic adaptations in Latin loanwords

The key insight is that if a Latin word matches a reconstructed
Proto-Tyrsenian form, it's a strong candidate for being a loanword.
"""

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ProtoForm:
    """A reconstructed Proto-Tyrsenian form."""

    proto_form: str  # Reconstructed form with *
    etruscan_reflex: str  # Attested Etruscan form
    lemnian_reflex: str  # Attested Lemnian form (if any)
    raetic_reflex: str  # Attested Raetic form (if any)
    meaning: str
    confidence: float  # 0.0 to 1.0
    latin_matches: list[str] = field(default_factory=list)
    sound_correspondences: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class LatinMatch:
    """A Latin word matching a Proto-Tyrsenian reconstruction."""

    latin_word: str
    proto_form: str
    match_type: str  # 'exact', 'regular', 'irregular'
    confidence: float
    phonetic_changes: list[str] = field(default_factory=list)
    semantic_plausibility: float = 0.5
    notes: str = ""


class ProtoTyrsenianReconstructor:
    """Reconstructs Proto-Tyrsenian forms and finds Latin matches.

    Uses established sound correspondences between Etruscan, Lemnian,
    and Raetic to reconstruct ancestral forms, then searches for
    Latin words that could be cognates or loanwords.
    """

    def __init__(self):
        """Initialize reconstructor with comparative data."""
        self._init_sound_correspondences()
        self._init_cognate_sets()
        self._init_reconstructions()

    def _init_sound_correspondences(self) -> None:
        """Initialize Tyrsenian sound correspondences.

        Based on Helmut Rix and other comparative work on the
        Tyrsenian hypothesis.
        """
        # Proto-Tyrsenian to daughter language correspondences
        self.correspondences = {
            # Vowels
            "*a": {"etruscan": "a", "lemnian": "a", "raetic": "a"},
            "*e": {"etruscan": "e", "lemnian": "e", "raetic": "e"},
            "*i": {"etruscan": "i", "lemnian": "i", "raetic": "i"},
            "*u": {"etruscan": "u", "lemnian": "u", "raetic": "u"},

            # Stops
            "*p": {"etruscan": "p", "lemnian": "φ/p", "raetic": "p"},
            "*t": {"etruscan": "t", "lemnian": "t", "raetic": "t"},
            "*k": {"etruscan": "c/k", "lemnian": "k", "raetic": "k/χ"},

            # Aspirates
            "*pʰ": {"etruscan": "ph/φ", "lemnian": "φ", "raetic": "p"},
            "*tʰ": {"etruscan": "th/θ", "lemnian": "θ", "raetic": "t"},
            "*kʰ": {"etruscan": "ch/χ", "lemnian": "χ", "raetic": "χ"},

            # Fricatives
            "*s": {"etruscan": "s", "lemnian": "s/ś", "raetic": "s/ś"},
            "*ś": {"etruscan": "ś", "lemnian": "ś", "raetic": "ś"},
            "*h": {"etruscan": "h", "lemnian": "h", "raetic": "h"},
            "*f": {"etruscan": "f", "lemnian": "?", "raetic": "f"},

            # Nasals
            "*m": {"etruscan": "m", "lemnian": "m", "raetic": "m"},
            "*n": {"etruscan": "n", "lemnian": "n", "raetic": "n"},

            # Liquids
            "*l": {"etruscan": "l", "lemnian": "l", "raetic": "l"},
            "*r": {"etruscan": "r", "lemnian": "r", "raetic": "r"},

            # Semi-vowels
            "*w": {"etruscan": "v", "lemnian": "v", "raetic": "u/v"},
            "*y": {"etruscan": "i", "lemnian": "i", "raetic": "i"},
        }

        # Sound changes from Proto-Tyrsenian to Latin adaptation
        self.latin_adaptations = {
            # Voiceless stops preserved
            "p": "p",
            "t": "t",
            "c": "c",
            "k": "c",

            # Aspirates > Latin fricatives or plain stops
            "ph": "f",  # or "p"
            "th": "t",  # sometimes "f"
            "ch": "c",  # or "h"

            # Etruscan u > Latin o (sometimes)
            "u": "o",

            # Etruscan endings > Latin endings
            "na": "na",  # Often preserved
            "ra": "ra",
            "la": "la",
            "al": "al",
        }

    def _init_cognate_sets(self) -> None:
        """Initialize established Tyrsenian cognate sets.

        These are the relatively secure correspondences between
        Etruscan, Lemnian, and Raetic.
        """
        self.cognate_sets = [
            # Year
            {
                "proto": "*awil",
                "etruscan": "avil",
                "lemnian": "aviś",
                "raetic": "",
                "meaning": "year",
                "confidence": 0.95,
            },
            # Magistrate
            {
                "proto": "*maru",
                "etruscan": "maru",
                "lemnian": "maraśm",
                "raetic": "",
                "meaning": "magistrate/official",
                "confidence": 0.85,
            },
            # Grandson/descendant
            {
                "proto": "*neptis",
                "etruscan": "nefts",
                "lemnian": "naphoth",
                "raetic": "",
                "meaning": "grandson/nephew",
                "confidence": 0.80,
            },
            # God
            {
                "proto": "*ais",
                "etruscan": "ais",
                "lemnian": "",
                "raetic": "",
                "meaning": "god",
                "confidence": 0.90,
            },
            # Genitive suffix
            {
                "proto": "*-al",
                "etruscan": "-al",
                "lemnian": "-ale",
                "raetic": "-ale",
                "meaning": "genitive suffix",
                "confidence": 0.95,
            },
            # This
            {
                "proto": "*ita",
                "etruscan": "ita",
                "lemnian": "ita",
                "raetic": "",
                "meaning": "this",
                "confidence": 0.90,
            },
            # Sacred/holy
            {
                "proto": "*hera",
                "etruscan": "hera",
                "lemnian": "",
                "raetic": "",
                "meaning": "sacred",
                "confidence": 0.70,
            },
            # Mask/face (theatre connection!)
            {
                "proto": "*pʰersu",
                "etruscan": "phersu",
                "lemnian": "",
                "raetic": "",
                "meaning": "mask/masked figure",
                "confidence": 0.85,
            },
            # Mother
            {
                "proto": "*ati",
                "etruscan": "ati",
                "lemnian": "",
                "raetic": "",
                "meaning": "mother",
                "confidence": 0.90,
            },
            # Son
            {
                "proto": "*klan",
                "etruscan": "clan",
                "lemnian": "",
                "raetic": "",
                "meaning": "son",
                "confidence": 0.90,
            },
            # Daughter
            {
                "proto": "*sek",
                "etruscan": "sec",
                "lemnian": "",
                "raetic": "",
                "meaning": "daughter",
                "confidence": 0.90,
            },
            # To give/dedicate
            {
                "proto": "*tur",
                "etruscan": "tur-",
                "lemnian": "",
                "raetic": "",
                "meaning": "to give/dedicate",
                "confidence": 0.85,
            },
            # Write/book
            {
                "proto": "*zik",
                "etruscan": "zic/zich",
                "lemnian": "śialχ?",
                "raetic": "",
                "meaning": "writing/book",
                "confidence": 0.70,
            },
            # Tinia/Jupiter
            {
                "proto": "*tinia",
                "etruscan": "tinia",
                "lemnian": "",
                "raetic": "tinake",
                "meaning": "sky god/Jupiter",
                "confidence": 0.90,
            },
            # Haruspex (entrail diviner)
            {
                "proto": "*haru-spik",
                "etruscan": "netsvis/trutnvt",
                "lemnian": "haralio?",
                "raetic": "",
                "meaning": "haruspex/diviner",
                "confidence": 0.75,
            },
        ]

    def _init_reconstructions(self) -> None:
        """Build reconstruction dictionary from cognate sets."""
        self.reconstructions: dict[str, ProtoForm] = {}

        for cs in self.cognate_sets:
            proto = cs["proto"]
            self.reconstructions[proto] = ProtoForm(
                proto_form=proto,
                etruscan_reflex=cs["etruscan"],
                lemnian_reflex=cs.get("lemnian", ""),
                raetic_reflex=cs.get("raetic", ""),
                meaning=cs["meaning"],
                confidence=cs["confidence"],
            )

    def reconstruct(self, etruscan_word: str) -> Optional[ProtoForm]:
        """Attempt to reconstruct Proto-Tyrsenian form from Etruscan.

        Args:
            etruscan_word: Attested Etruscan word

        Returns:
            ProtoForm if reconstruction possible, else None
        """
        etruscan_word = etruscan_word.lower()

        # Check known reconstructions
        for proto, form in self.reconstructions.items():
            if etruscan_word == form.etruscan_reflex:
                return form

        # Attempt rule-based reconstruction
        proto = self._apply_reconstruction_rules(etruscan_word)
        if proto:
            return ProtoForm(
                proto_form=proto,
                etruscan_reflex=etruscan_word,
                lemnian_reflex="",
                raetic_reflex="",
                meaning="unknown",
                confidence=0.50,  # Uncertain without cognates
                notes="Reconstructed by rule, not attested cognates",
            )

        return None

    def _apply_reconstruction_rules(self, word: str) -> Optional[str]:
        """Apply reconstruction rules to create proto-form.

        Args:
            word: Etruscan word

        Returns:
            Reconstructed proto-form with *
        """
        proto = word

        # Apply reverse sound changes
        replacements = [
            ('ph', 'pʰ'),
            ('th', 'tʰ'),
            ('ch', 'kʰ'),
            ('v', 'w'),
            ('f', 'pʰ'),
        ]

        for etr, proto_sound in replacements:
            proto = proto.replace(etr, proto_sound)

        return f"*{proto}"

    def find_latin_matches(self, proto_form: ProtoForm) -> list[LatinMatch]:
        """Find Latin words that could derive from a Proto-Tyrsenian form.

        Args:
            proto_form: Reconstructed Proto-Tyrsenian form

        Returns:
            List of potential Latin matches
        """
        matches = []
        proto = proto_form.proto_form.lstrip('*')

        # Generate possible Latin adaptations
        latin_variants = self._generate_latin_variants(proto)

        # Known Latin words that might match
        latin_vocabulary = self._get_latin_vocabulary()

        for latin_word in latin_vocabulary:
            latin_normalized = latin_word.lower()

            for variant in latin_variants:
                similarity = self._calculate_similarity(variant, latin_normalized)

                if similarity >= 0.7:
                    changes = self._identify_phonetic_changes(proto, latin_normalized)

                    matches.append(LatinMatch(
                        latin_word=latin_word,
                        proto_form=proto_form.proto_form,
                        match_type="regular" if changes else "exact",
                        confidence=similarity * proto_form.confidence,
                        phonetic_changes=changes,
                        notes=f"Via variant: {variant}",
                    ))

        # Sort by confidence
        matches.sort(key=lambda m: m.confidence, reverse=True)
        return matches[:10]  # Top 10

    def _generate_latin_variants(self, proto: str) -> list[str]:
        """Generate possible Latin adaptations of a proto-form.

        Args:
            proto: Proto-Tyrsenian form (without *)

        Returns:
            List of possible Latin forms
        """
        variants = [proto]

        # Apply Latin adaptation rules
        adaptations = [
            ('pʰ', 'f'), ('pʰ', 'p'),
            ('tʰ', 't'), ('tʰ', 'f'),
            ('kʰ', 'c'), ('kʰ', 'h'),
            ('w', 'v'), ('w', 'u'),
            ('ai', 'ae'), ('ei', 'i'),
            ('u', 'o'),  # Etruscan u > Latin o sometimes
        ]

        for proto_sound, latin_sound in adaptations:
            new_variants = []
            for v in variants:
                if proto_sound in v:
                    new_variants.append(v.replace(proto_sound, latin_sound))
            variants.extend(new_variants)

        # Add common Latin endings
        endings = ['us', 'um', 'a', 'o', 'io', 'ia', 'ius', 'ium']
        with_endings = []
        for v in variants:
            for ending in endings:
                with_endings.append(v + ending)
        variants.extend(with_endings)

        return list(set(variants))

    def _calculate_similarity(self, form1: str, form2: str) -> float:
        """Calculate phonetic similarity between two forms."""
        if form1 == form2:
            return 1.0

        # Check if one contains the other
        if form1 in form2 or form2 in form1:
            shorter = min(len(form1), len(form2))
            longer = max(len(form1), len(form2))
            return shorter / longer

        # Simple character overlap
        set1 = set(form1)
        set2 = set(form2)
        overlap = len(set1 & set2)
        total = len(set1 | set2)

        return overlap / total if total > 0 else 0.0

    def _identify_phonetic_changes(self, proto: str, latin: str) -> list[str]:
        """Identify phonetic changes from proto to Latin."""
        changes = []

        if 'pʰ' in proto and 'f' in latin:
            changes.append("*pʰ > f (aspiration > fricative)")
        if 'tʰ' in proto and 't' in latin:
            changes.append("*tʰ > t (deaspiration)")
        if 'u' in proto and 'o' in latin:
            changes.append("*u > o (vowel change)")

        return changes

    def _get_latin_vocabulary(self) -> list[str]:
        """Get Latin vocabulary for matching.

        In production, this would load from a comprehensive Latin lexicon.
        Here we include words in domains likely for Etruscan loans.
        """
        return [
            # Theatre
            "histrio", "histriones", "persona", "personae", "scaena",
            "ludius", "ludio", "mimus", "pantomimus",
            # Religion
            "haruspex", "haruspices", "augur", "augures",
            "lar", "lares", "lemures", "manes",
            "fanum", "templum", "sacellum",
            # Political
            "lucumo", "lucumones", "lictor", "lictores",
            "fasces", "trabea", "curule",
            # Music
            "subulo", "subulones", "tibicen", "tibicines",
            "tuba", "lituus",
            # Architecture
            "atrium", "atria", "vestibulum",
            # Military
            "lanista", "lanistae", "gladiator", "gladiatores",
            "arena", "harena",
            # Misc
            "catena", "catenae", "fenestra", "fenestrae",
            "balteus", "baltei", "mantisa",
            "spurius", "elementum", "elementa",
            # Potential new
            "persona", "antenna", "cisterna", "caverna",
            "lanterna", "taberna", "taverna",
            "popina", "culina",
        ]

    def find_all_latin_loans(self) -> list[LatinMatch]:
        """Find all potential Latin loans from Proto-Tyrsenian.

        Returns:
            List of all potential matches
        """
        all_matches = []

        for proto_form in self.reconstructions.values():
            matches = self.find_latin_matches(proto_form)
            all_matches.extend(matches)

        # Deduplicate and sort
        seen = set()
        unique = []
        for match in all_matches:
            if match.latin_word not in seen:
                seen.add(match.latin_word)
                unique.append(match)

        unique.sort(key=lambda m: m.confidence, reverse=True)
        return unique

    def get_high_confidence_reconstructions(self) -> list[ProtoForm]:
        """Get reconstructions with good attestation.

        Returns:
            List of well-supported proto-forms
        """
        return [
            form for form in self.reconstructions.values()
            if form.confidence >= 0.75
        ]


def reconstruct_proto_form(etruscan_word: str) -> Optional[ProtoForm]:
    """Reconstruct Proto-Tyrsenian form from Etruscan.

    Args:
        etruscan_word: Attested Etruscan word

    Returns:
        ProtoForm if reconstruction possible
    """
    reconstructor = ProtoTyrsenianReconstructor()
    return reconstructor.reconstruct(etruscan_word)
