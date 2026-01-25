#!/usr/bin/env python3
"""Download and parse Hesychius lexicon for Etruscan glosses.

This script:
1. Downloads Hesychius text from Internet Archive (if available)
2. Falls back to known scholarly glosses if download fails
3. Extracts Tyrrhenian/Etruscan entries
4. Optionally imports them into the database

Usage:
    python scripts/download_hesychius.py [--import] [--stats]
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from etruscan_miner.config import DB_PATH
from etruscan_miner.corpus.hesychius import (
    HesychiusParser,
    SCHOLARLY_GLOSSES,
    get_all_greek_etruscan_glosses,
)
from etruscan_miner.db.models import EtruscanWord, VerifiedGloss
from etruscan_miner.db.repository import Repository


def download_hesychius_text(corpus_dir: Path) -> bool:
    """Attempt to download Hesychius text from Internet Archive.

    Note: The full text is in a scanned PDF, which is difficult to parse.
    This function creates a placeholder with known entries.

    Args:
        corpus_dir: Directory to save the text

    Returns:
        True if successful
    """
    import requests

    corpus_dir.mkdir(parents=True, exist_ok=True)
    text_path = corpus_dir / "hesychius_text.txt"

    # The Internet Archive has scanned editions but not easily parseable text
    # For now, create a file with known Tyrrhenian entries from scholarship

    print("Creating Hesychius corpus from scholarly sources...")
    print("(Full Hesychius text would require OCR of scanned editions)")

    # Write known entries
    with open(text_path, "w", encoding="utf-8") as f:
        f.write("# Hesychius Lexicon - Tyrrhenian Entries\n")
        f.write("# Extracted from scholarly sources\n\n")

        for greek, etr, meaning, source, conf in SCHOLARLY_GLOSSES:
            f.write(f"{greek}· {meaning}. παρὰ Τυρρηνοῖς {etr}.\n")

    print(f"Created: {text_path}")
    return True


def show_glosses():
    """Display all known Hesychius Etruscan glosses."""
    glosses = get_all_greek_etruscan_glosses()

    print("\nTyrrhenian Glosses from Greek Sources")
    print("=" * 60)
    print(f"{'Etruscan':<15} {'Meaning':<25} {'Confidence':<10} Source")
    print("-" * 60)

    for etr_word, meaning, source, confidence in glosses:
        conf_str = f"{confidence:.0%}"
        print(f"{etr_word:<15} {meaning:<25} {conf_str:<10} {source[:25]}")

    print("-" * 60)
    print(f"Total: {len(glosses)} glosses")


def import_to_database(repo: Repository) -> tuple[int, int]:
    """Import Hesychius glosses to database.

    Args:
        repo: Database repository

    Returns:
        Tuple of (vocabulary_count, verified_gloss_count)
    """
    glosses = get_all_greek_etruscan_glosses()

    vocab_count = 0
    gloss_count = 0

    for etr_word, meaning, source, confidence in glosses:
        # Add to vocabulary
        word = EtruscanWord(
            word=etr_word,
            word_normalized=etr_word.lower(),
            meaning=meaning,
            source=source,
            category="gloss",
            reliability=int(confidence * 5),  # Scale to 1-5
            notes=f"From Hesychius/Greek sources. Confidence: {confidence:.0%}",
        )
        try:
            repo.insert_vocabulary(word)
            vocab_count += 1
        except Exception:
            pass  # Skip duplicates

        # Add as verified gloss if confidence is high enough
        if confidence >= 0.70:
            gloss = VerifiedGloss(
                etruscan_word=etr_word,
                etruscan_normalized=etr_word.lower(),
                meaning=meaning,
                source_author="Hesychius/Greek",
                source_work="Greek Lexicographical Sources",
                source_citation=source,
                reliability=int(confidence * 5),
                is_seed=True,
                notes=f"Confidence: {confidence:.0%}",
            )
            try:
                repo.insert_verified_gloss(gloss)
                gloss_count += 1
            except Exception:
                pass  # Skip duplicates

    return vocab_count, gloss_count


def main():
    parser = argparse.ArgumentParser(
        description="Download and parse Hesychius lexicon for Etruscan glosses"
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help="Download/create Hesychius corpus file",
    )
    parser.add_argument(
        "--import-db",
        action="store_true",
        help="Import glosses to database",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show statistics",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all known Tyrrhenian glosses",
    )

    args = parser.parse_args()

    corpus_dir = Path(__file__).parent.parent / "data" / "corpus" / "hesychius"

    if args.download:
        download_hesychius_text(corpus_dir)

    if args.list:
        show_glosses()
        return

    if args.stats:
        parser_obj = HesychiusParser(corpus_dir)
        corpus = parser_obj.load_corpus()

        print("\nHesychius Corpus Statistics")
        print("=" * 40)
        print(f"  Total entries: {len(corpus.entries)}")
        print(f"  Tyrrhenian entries: {len(corpus.tyrrhenian_entries)}")
        print(f"  Source file: {corpus.source_path}")
        print(f"  File exists: {corpus.source_path.exists() if corpus.source_path else False}")
        return

    if args.import_db:
        print(f"\nImporting to database: {DB_PATH}")
        repo = Repository(DB_PATH)
        vocab, glosses = import_to_database(repo)
        print(f"Imported {vocab} vocabulary words, {glosses} verified glosses")

        db_stats = repo.get_stats()
        print(f"\nDatabase now has:")
        print(f"  Vocabulary: {db_stats['etruscan_vocabulary']} words")
        print(f"  Verified glosses: {db_stats['verified_glosses']} glosses")
        return

    # Default: show help
    if not any([args.download, args.import_db, args.stats, args.list]):
        show_glosses()


if __name__ == "__main__":
    main()
