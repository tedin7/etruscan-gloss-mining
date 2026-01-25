#!/usr/bin/env python3
"""Train the context classifier for Etruscan gloss detection.

This script:
1. Loads labeled data from data/labeled_candidates.json
2. Trains a context classifier (DistilBERT, embeddings, or TF-IDF)
3. Saves the model to data/models/context_classifier/
4. Shows training/validation accuracy

Usage:
    python scripts/train_context_classifier.py
    python scripts/train_context_classifier.py --backend tfidf
    python scripts/train_context_classifier.py --backend embeddings
    python scripts/train_context_classifier.py --backend distilbert
    python scripts/train_context_classifier.py --test  # Run test predictions
"""

import argparse
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from etruscan_miner.config import DATA_DIR
from etruscan_miner.validation.context_classifier import (
    ContextClassifier,
    get_available_backends,
)


def load_labeled_data(path: Path) -> list[dict]:
    """Load labeled data from JSON file.

    Args:
        path: Path to labeled_candidates.json

    Returns:
        List of labeled data dicts with normalized labels
    """
    if not path.exists():
        return []

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Handle various formats
    if isinstance(data, list):
        examples = data
    elif isinstance(data, dict) and 'examples' in data:
        examples = data['examples']
    elif isinstance(data, dict) and 'candidates' in data:
        examples = data['candidates']
    elif isinstance(data, dict):
        # Might be dict keyed by ID
        examples = list(data.values())
    else:
        return []

    # Normalize labels to 'etruscan' / 'latin' format expected by classifier
    normalized = []
    for item in examples:
        normalized_item = item.copy()
        label = item.get('label', '')

        # Map true_etruscan -> etruscan, false_positive -> latin
        if label == 'true_etruscan':
            normalized_item['label'] = 'etruscan'
        elif label == 'false_positive':
            normalized_item['label'] = 'latin'

        # Build context string if not present
        if 'context' not in normalized_item:
            parts = []
            if 'context_before' in item:
                parts.append(item['context_before'])
            if 'full_match' in item:
                parts.append(item['full_match'])
            if 'context_after' in item:
                parts.append(item['context_after'])
            normalized_item['context'] = ' '.join(parts)

        normalized.append(normalized_item)

    return normalized


def create_synthetic_data() -> list[dict]:
    """Create synthetic training data from known examples.

    This provides a starting point when no labeled data exists.

    Returns:
        List of synthetic labeled examples
    """
    synthetic = []

    # Positive examples (genuinely discussing Etruscan etymology)
    etruscan_contexts = [
        {
            "word": "subulo",
            "context_before": "Varro says that",
            "full_match": "Tusci vocant subulo",
            "context_after": "quod nos tibicinem appellamus",
            "label": "etruscan",
        },
        {
            "word": "lanista",
            "context_before": "gladiatorum magistri",
            "full_match": "lingua Etrusca lanista dicitur",
            "context_after": "carnifex enim praesidens",
            "label": "etruscan",
        },
        {
            "word": "atrium",
            "context_before": "nomen est Tuscum",
            "full_match": "atrium appellatur Etrusca voce",
            "context_after": "ab atro colore fumo",
            "label": "etruscan",
        },
        {
            "word": "histrio",
            "context_before": "quod Tusci",
            "full_match": "hister appellabantur histriones",
            "context_after": "qui ludi ab Etruria vocati",
            "label": "etruscan",
        },
        {
            "word": "cassis",
            "context_before": "galea ex corio fit",
            "full_match": "cassis Etruscum nomen est",
            "context_after": "ab aere fit",
            "label": "etruscan",
        },
        {
            "word": "mundus",
            "context_before": "locus subterraneus",
            "full_match": "mundus appellatur Tusco nomine",
            "context_after": "ut caeli mundus",
            "label": "etruscan",
        },
        {
            "word": "mantissa",
            "context_before": "additamentum ponderi",
            "full_match": "Tusci vocant mantissa",
            "context_after": "quod appenditur",
            "label": "etruscan",
        },
        {
            "word": "lucumo",
            "context_before": "regum Etruscorum nomen",
            "full_match": "lucumo Etrusca lingua rex vocatur",
            "context_after": "princeps gentis",
            "label": "etruscan",
        },
        {
            "word": "lar",
            "context_before": "domestici dei",
            "full_match": "Lares Etrusco vocabulo",
            "context_after": "praesides domus",
            "label": "etruscan",
        },
        {
            "word": "persona",
            "context_before": "facies larvata",
            "full_match": "persona Etrusca voce dicta",
            "context_after": "a personando",
            "label": "etruscan",
        },
    ]

    # Negative examples (generic Latin etymology, not Etruscan)
    latin_contexts = [
        {
            "word": "rex",
            "context_before": "qui populo imperat",
            "full_match": "rex vocatur a regendo",
            "context_after": "quod alios regat",
            "label": "latin",
        },
        {
            "word": "consul",
            "context_before": "magistratus summus",
            "full_match": "consul dicitur a consulendo",
            "context_after": "civibus consulit",
            "label": "latin",
        },
        {
            "word": "senator",
            "context_before": "patres conscripti",
            "full_match": "senatores a senectute vocati",
            "context_after": "quod senes essent",
            "label": "latin",
        },
        {
            "word": "aqua",
            "context_before": "elementum liquidum",
            "full_match": "aqua dicta ab aequore",
            "context_after": "quod superficies eius aequa",
            "label": "latin",
        },
        {
            "word": "terra",
            "context_before": "elementum solidum",
            "full_match": "terra vocatur quod teritur",
            "context_after": "pedibus calcatur",
            "label": "latin",
        },
        {
            "word": "ignis",
            "context_before": "elementum calidum",
            "full_match": "ignis dicitur ab igne",
            "context_after": "quod omnia gignat",
            "label": "latin",
        },
        {
            "word": "sol",
            "context_before": "astrum maximum",
            "full_match": "sol vocatur quod solus lucet",
            "context_after": "inter sidera",
            "label": "latin",
        },
        {
            "word": "luna",
            "context_before": "nocturnum sidus",
            "full_match": "luna dicta a lucendo nocte",
            "context_after": "quasi lucina",
            "label": "latin",
        },
        {
            "word": "vir",
            "context_before": "homo masculus",
            "full_match": "vir vocatur a vi",
            "context_after": "quod maior vis in eo",
            "label": "latin",
        },
        {
            "word": "femina",
            "context_before": "homo mulier",
            "full_match": "femina dicitur a feminibus",
            "context_after": "ubi sexus cognoscitur",
            "label": "latin",
        },
        {
            "word": "puer",
            "context_before": "infans masculus",
            "full_match": "puer vocatur a puritate",
            "context_after": "quod purus sit",
            "label": "latin",
        },
        {
            "word": "domus",
            "context_before": "aedificium habitandi",
            "full_match": "domus dicta a domando",
            "context_after": "quod ibi dometur familia",
            "label": "latin",
        },
    ]

    synthetic.extend(etruscan_contexts)
    synthetic.extend(latin_contexts)

    return synthetic


def main():
    parser = argparse.ArgumentParser(
        description="Train the context classifier for Etruscan gloss detection"
    )
    parser.add_argument(
        "--backend",
        choices=['distilbert', 'embeddings', 'tfidf', 'auto'],
        default='auto',
        help="Backend to use for classification (default: auto-select best available)",
    )
    parser.add_argument(
        "--labeled-data",
        type=Path,
        default=DATA_DIR / "labeled_candidates.json",
        help="Path to labeled data JSON file",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DATA_DIR / "models" / "context_classifier",
        help="Path to save trained model",
    )
    parser.add_argument(
        "--use-synthetic",
        action="store_true",
        help="Use synthetic data if no labeled data is available",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run test predictions after training",
    )
    parser.add_argument(
        "--validation-split",
        type=float,
        default=0.2,
        help="Fraction of data to use for validation",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Context Classifier Training")
    print("=" * 60)

    # Check available backends
    available = get_available_backends()
    print(f"\nAvailable backends: {', '.join(available)}")

    if not available:
        print("\nError: No ML backends available!")
        print("Please install at least one of:")
        print("  pip install transformers torch  # For DistilBERT")
        print("  pip install sentence-transformers scikit-learn  # For embeddings")
        print("  pip install scikit-learn  # For TF-IDF")
        sys.exit(1)

    # Determine backend to use
    if args.backend == 'auto':
        backend = None  # Let ContextClassifier auto-select
        print(f"Auto-selecting best backend: {available[0]}")
    else:
        if args.backend not in available:
            print(f"\nError: Backend '{args.backend}' is not available.")
            print(f"Available backends: {', '.join(available)}")
            sys.exit(1)
        backend = args.backend
        print(f"Using backend: {backend}")

    # Load labeled data
    print(f"\n1. Loading labeled data from {args.labeled_data}...")
    labeled_data = load_labeled_data(args.labeled_data)
    print(f"   Found {len(labeled_data)} labeled examples")

    # Check if we need synthetic data
    if len(labeled_data) < 10:
        if args.use_synthetic:
            print("\n   Insufficient labeled data. Using synthetic data...")
            synthetic = create_synthetic_data()
            labeled_data.extend(synthetic)
            print(f"   Added {len(synthetic)} synthetic examples")
            print(f"   Total: {len(labeled_data)} examples")
        else:
            print("\n" + "=" * 60)
            print("INSUFFICIENT LABELED DATA")
            print("=" * 60)
            print(f"\nNeed at least 10 labeled examples, found {len(labeled_data)}.")
            print("\nTo create labeled data, use the labeling tool:")
            print("  python scripts/label_candidates.py")
            print("\nAlternatively, run with --use-synthetic to use synthetic data:")
            print("  python scripts/train_context_classifier.py --use-synthetic")
            print("\nSynthetic data provides a starting point with known Etruscan")
            print("glosses and Latin etymologies, but real labeled data will")
            print("give better results.")
            sys.exit(1)

    # Count positive/negative
    positive = sum(1 for item in labeled_data
                   if item.get('label') in ('etruscan', 'accept', 1, True)
                   or item.get('decision') in ('accept',))
    negative = len(labeled_data) - positive
    print(f"\n2. Data distribution:")
    print(f"   Positive (Etruscan): {positive}")
    print(f"   Negative (Latin): {negative}")

    # Check for class imbalance
    if positive < 3 or negative < 3:
        print("\nWarning: Severe class imbalance. Need at least 3 of each class.")
        if args.use_synthetic:
            print("Adding more synthetic data to balance...")
            synthetic = create_synthetic_data()
            labeled_data.extend(synthetic)
        else:
            sys.exit(1)

    # Train classifier
    print(f"\n3. Training classifier...")
    try:
        classifier = ContextClassifier(backend=backend)
        results = classifier.train(labeled_data, validation_split=args.validation_split)
    except Exception as e:
        print(f"\nError during training: {e}")
        sys.exit(1)

    # Print results
    print(f"\n4. Training Results:")
    print(f"   Backend: {results['backend']}")
    print(f"   Training examples: {results['train_size']}")
    print(f"   Validation examples: {results['val_size']}")
    print(f"   Validation accuracy: {results['val_accuracy']:.2%}")

    # Save model
    print(f"\n5. Saving model to {args.output}...")
    classifier.save(args.output)

    # Run test predictions if requested
    if args.test:
        print("\n6. Test predictions:")
        print("-" * 60)

        test_contexts = [
            # Genuine Etruscan contexts (should score high)
            ("Tusci vocant subulo quod nos tibicinem appellamus", "Etruscan (subulo)"),
            ("lingua Etrusca lanista dicitur carnifex", "Etruscan (lanista)"),
            ("atrium appellatur Etrusca voce ab atro", "Etruscan (atrium)"),

            # Latin etymology contexts (should score low)
            ("rex vocatur a regendo quod alios regat", "Latin (rex)"),
            ("consul dicitur a consulendo civibus", "Latin (consul)"),
            ("aqua dicta ab aequore quod superficies", "Latin (aqua)"),
        ]

        print(f"{'Context (truncated)':<45} {'Score':>8}  Expected")
        print("-" * 70)
        for context, expected in test_contexts:
            score = classifier.predict(context)
            indicator = "+" if score > 0.5 else "-"
            truncated = context[:42] + "..." if len(context) > 45 else context
            print(f"{truncated:<45} {score:>7.3f}  {indicator} ({expected})")

    print("\n" + "=" * 60)
    print("Training complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
