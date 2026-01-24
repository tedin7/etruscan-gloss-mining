#!/usr/bin/env python3
"""Train the Etruscan word classifier.

This script:
1. Loads positive examples from the inscription corpus (Etruscan words)
2. Loads negative examples from Latin vocabulary
3. Trains a character n-gram classifier
4. Saves the model to data/models/word_classifier.pkl

Usage:
    python scripts/train_word_classifier.py
    python scripts/train_word_classifier.py --test  # Run test predictions after training
    python scripts/train_word_classifier.py --importance  # Show feature importance
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from etruscan_miner.config import DATA_DIR
from etruscan_miner.corpus.inscriptions import InscriptionLoader
from etruscan_miner.validation.word_classifier import WordClassifier


def load_latin_vocabulary(path: Path) -> list[str]:
    """Load Latin vocabulary from text file.

    Args:
        path: Path to latin_vocabulary.txt

    Returns:
        List of Latin words
    """
    if not path.exists():
        print(f"Warning: Latin vocabulary file not found: {path}")
        return []

    words = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            # Clean the word
            word = line.lower().strip()
            if len(word) >= 2:
                words.append(word)

    return words


def load_etruscan_vocabulary() -> list[str]:
    """Load Etruscan vocabulary from inscription corpus.

    Returns:
        List of Etruscan words from inscriptions
    """
    loader = InscriptionLoader()
    vocabulary = loader.extract_vocabulary()
    return list(vocabulary)


def main():
    parser = argparse.ArgumentParser(
        description="Train the Etruscan word classifier"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run test predictions after training",
    )
    parser.add_argument(
        "--importance",
        action="store_true",
        help="Show feature importance after training",
    )
    parser.add_argument(
        "--latin-vocab",
        type=Path,
        default=DATA_DIR / "latin_vocabulary.txt",
        help="Path to Latin vocabulary file",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DATA_DIR / "models" / "word_classifier.pkl",
        help="Path to save trained model",
    )
    parser.add_argument(
        "--min-positive",
        type=int,
        default=100,
        help="Minimum number of positive examples required",
    )
    parser.add_argument(
        "--min-negative",
        type=int,
        default=100,
        help="Minimum number of negative examples required",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Etruscan Word Classifier Training")
    print("=" * 60)

    # Load positive examples (Etruscan words from inscriptions)
    print("\n1. Loading Etruscan vocabulary from inscriptions...")
    etruscan_words = load_etruscan_vocabulary()
    print(f"   Loaded {len(etruscan_words)} Etruscan words")

    if len(etruscan_words) < args.min_positive:
        print(f"\nError: Need at least {args.min_positive} positive examples.")
        print("Make sure the inscription corpus is available at:")
        print("  data/corpus/inscriptions/etruscan_materials.txt")
        print("\nYou can download it by running:")
        print("  python scripts/import_inscriptions.py")
        sys.exit(1)

    # Load negative examples (Latin words)
    print("\n2. Loading Latin vocabulary...")
    latin_words = load_latin_vocabulary(args.latin_vocab)
    print(f"   Loaded {len(latin_words)} Latin words")

    if len(latin_words) < args.min_negative:
        print(f"\nError: Need at least {args.min_negative} negative examples.")
        print(f"Latin vocabulary file: {args.latin_vocab}")
        sys.exit(1)

    # Balance the dataset (use roughly equal numbers)
    # Use all Etruscan words and sample Latin words to match
    max_samples = max(len(etruscan_words), len(latin_words))
    min_samples = min(len(etruscan_words), len(latin_words))

    if len(etruscan_words) > len(latin_words):
        print(f"\n   Note: More Etruscan ({len(etruscan_words)}) than Latin ({len(latin_words)}) words")
        print(f"   Using all {len(latin_words)} Latin words and {len(latin_words)} Etruscan words")
        # Sample Etruscan words to balance
        import random
        random.seed(42)
        etruscan_words = random.sample(etruscan_words, len(latin_words))
    elif len(latin_words) > len(etruscan_words):
        print(f"\n   Note: More Latin ({len(latin_words)}) than Etruscan ({len(etruscan_words)}) words")
        print(f"   Using all {len(etruscan_words)} Etruscan words and {len(etruscan_words)} Latin words")
        # Sample Latin words to balance
        import random
        random.seed(42)
        latin_words = random.sample(latin_words, len(etruscan_words))

    # Show some examples
    print("\n3. Sample positive (Etruscan) words:")
    for word in sorted(etruscan_words)[:10]:
        print(f"      {word}")
    print("      ...")

    print("\n4. Sample negative (Latin) words:")
    for word in sorted(latin_words)[:10]:
        print(f"      {word}")
    print("      ...")

    # Train classifier
    print("\n5. Training classifier...")
    classifier = WordClassifier()
    classifier.train(etruscan_words, latin_words)

    # Save model
    print(f"\n6. Saving model to {args.output}...")
    classifier.save(args.output)

    # Run tests if requested
    if args.test:
        print("\n7. Test predictions:")
        print("-" * 40)

        # Test words - mix of known Etruscan, Latin, and ambiguous
        test_cases = [
            # Known Etruscan words (should score high)
            ("ais", "Etruscan (god)"),
            ("clan", "Etruscan (son)"),
            ("puia", "Etruscan (wife)"),
            ("zilath", "Etruscan (magistrate)"),
            ("lauchum", "Etruscan (king)"),
            ("subulo", "Etruscan via Varro"),
            ("lanista", "Etruscan via Isidore"),
            ("cassis", "Etruscan via Isidore"),
            ("atrium", "Etruscan etymology"),

            # Latin words (should score low)
            ("dominus", "Latin"),
            ("imperium", "Latin"),
            ("aqua", "Latin"),
            ("terra", "Latin"),
            ("victoria", "Latin"),
            ("lanterna", "Latin"),
            ("servus", "Latin"),
            ("bellum", "Latin"),
        ]

        print(f"{'Word':<15} {'Score':>8}  {'Expected':<25}")
        print("-" * 50)
        for word, expected in test_cases:
            score = classifier.predict(word)
            indicator = "+" if score > 0.5 else "-"
            print(f"{word:<15} {score:>7.3f}  {indicator} ({expected})")

    # Show feature importance if requested
    if args.importance:
        print("\n8. Feature importance:")
        print("-" * 40)
        importance = classifier.get_feature_importance(top_n=15)

        print("\nTop Etruscan indicators (positive coefficients):")
        for name, coef in importance['etruscan_indicators'][:15]:
            print(f"  {name:<20} {coef:>8.4f}")

        print("\nTop Latin indicators (negative coefficients):")
        for name, coef in importance['latin_indicators'][:15]:
            print(f"  {name:<20} {coef:>8.4f}")

    print("\n" + "=" * 60)
    print("Training complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
