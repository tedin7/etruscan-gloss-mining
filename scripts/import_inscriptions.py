#!/usr/bin/env python3
"""Import Etruscan inscription vocabulary into the database.

This script:
1. Parses the Materials for the Study of Etruscan Language corpus
2. Extracts unique Etruscan words from inscriptions
3. Imports them into the etruscan_vocabulary table for cross-reference validation

Usage:
    python scripts/import_inscriptions.py [--stats] [--dry-run]
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from etruscan_miner.config import DB_PATH
from etruscan_miner.corpus.inscriptions import InscriptionLoader
from etruscan_miner.db.repository import Repository


def main():
    parser = argparse.ArgumentParser(
        description="Import Etruscan inscription vocabulary into database"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show statistics only, don't import",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be imported without writing to database",
    )
    parser.add_argument(
        "--corpus-dir",
        type=Path,
        help="Path to corpus/inscriptions directory",
    )
    parser.add_argument(
        "--show-words",
        action="store_true",
        help="Show extracted words",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limit number of words to show/import",
    )

    args = parser.parse_args()

    # Initialize loader
    loader = InscriptionLoader(args.corpus_dir)

    if args.stats:
        print("\nInscription Corpus Statistics")
        print("=" * 50)
        stats = loader.get_statistics()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        return

    # Extract vocabulary
    print("\nExtracting vocabulary from inscriptions...")
    vocabulary = loader.extract_vocabulary()
    print(f"Found {len(vocabulary)} unique words")

    if args.show_words:
        sorted_words = sorted(vocabulary)
        if args.limit:
            sorted_words = sorted_words[:args.limit]
        print("\nExtracted words:")
        for i, word in enumerate(sorted_words):
            print(f"  {i+1:4}. {word}")
        if args.limit and len(vocabulary) > args.limit:
            print(f"  ... and {len(vocabulary) - args.limit} more")

    if args.dry_run:
        print(f"\nDry run: Would import {len(vocabulary)} words")
        return

    # Import to database
    print(f"\nImporting to database: {DB_PATH}")
    repo = Repository(DB_PATH)

    count = loader.import_to_db(repo, source="CIEW inscriptions")
    print(f"Imported {count} new vocabulary words")

    # Show updated stats
    db_stats = repo.get_stats()
    print(f"\nDatabase now has {db_stats['etruscan_vocabulary']} vocabulary words")


if __name__ == "__main__":
    main()
