"""Corpus access module for Perseus and other text sources.

Available clients:
- PerseusClient: CTS API for texts IN the Perseus inventory (Pliny, Livy, Virgil)
- LatinLibraryClient: HTML scraping for texts NOT in Perseus (Varro, Festus)
- GitHubCorpusReader: Pre-scraped CLTK Latin Library texts (~2000 files)
- GreekCorpusClient: Greek texts from Perseus (Dionysius, Strabo, Herodotus)
- InscriptionLoader: Etruscan inscriptions from CIE/CIEW corpus
- HesychiusParser: Greek lexicon with Tyrrhenian glosses

See individual modules for documentation on API status and available texts.
"""

from .github_corpus import GitHubCorpusReader, GitHubText, load_github_corpus
from .greek_texts import (
    GREEK_WORKS,
    GreekCorpusClient,
    GreekPassage,
    fetch_greek_etruscan_passages,
    get_available_greek_works,
)
from .hesychius import (
    HesychiusParser,
    LexiconEntry,
    get_all_greek_etruscan_glosses,
    get_hesychius_glosses,
)
from .inscriptions import (
    Inscription,
    InscriptionLoader,
    load_inscription_vocabulary,
)
from .latin_library import LatinLibraryClient, load_cached_varro
from .perseus import (
    AVAILABLE_WORKS,
    PerseusClient,
    fetch_livy,
    fetch_pliny,
    fetch_varro,
)

__all__ = [
    # Perseus (Latin)
    "PerseusClient",
    "AVAILABLE_WORKS",
    "fetch_pliny",
    "fetch_livy",
    "fetch_varro",
    # Latin Library
    "LatinLibraryClient",
    "load_cached_varro",
    # GitHub corpus
    "GitHubCorpusReader",
    "GitHubText",
    "load_github_corpus",
    # Greek texts
    "GreekCorpusClient",
    "GreekPassage",
    "GREEK_WORKS",
    "get_available_greek_works",
    "fetch_greek_etruscan_passages",
    # Inscriptions
    "InscriptionLoader",
    "Inscription",
    "load_inscription_vocabulary",
    # Hesychius
    "HesychiusParser",
    "LexiconEntry",
    "get_hesychius_glosses",
    "get_all_greek_etruscan_glosses",
]
