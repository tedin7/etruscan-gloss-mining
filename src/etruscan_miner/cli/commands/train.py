"""Train ML models command."""

import random
import click
from pathlib import Path

from ...config import DATA_DIR
from ...corpus.inscriptions import InscriptionLoader
from ...validation.word_classifier import WordClassifier


@click.group()
def train():
    """Train ML models (word-classifier, context-classifier)."""
    pass


@train.command("word-classifier")
@click.option("--test", is_flag=True, help="Run test predictions after training")
@click.option("--importance", is_flag=True, help="Show feature importance after training")
@click.option("--latin-vocab", type=click.Path(exists=True, path_type=Path),
              default=None, help="Path to Latin vocabulary file")
@click.option("--output", type=click.Path(path_type=Path),
              default=None, help="Path to save trained model")
@click.option("--min-positive", type=int, default=100,
              help="Minimum number of positive examples required")
@click.option("--min-negative", type=int, default=100,
              help="Minimum number of negative examples required")
def word_classifier(test: bool, importance: bool, latin_vocab: Path,
                    output: Path, min_positive: int, min_negative: int):
    """Train the Etruscan word classifier.

    Uses character n-gram features to distinguish Etruscan words
    from Latin words. Trains on inscription corpus (positive) and
    Latin vocabulary (negative).
    """
    if latin_vocab is None:
        latin_vocab = DATA_DIR / "latin_vocabulary.txt"
    if output is None:
        output = DATA_DIR / "models" / "word_classifier.pkl"

    click.echo("=" * 60)
    click.echo("Etruscan Word Classifier Training")
    click.echo("=" * 60)

    # Load positive examples
    click.echo("\n1. Loading Etruscan vocabulary from inscriptions...")
    etruscan_words = _load_etruscan_vocabulary()
    click.echo(f"   Loaded {len(etruscan_words)} Etruscan words")

    if len(etruscan_words) < min_positive:
        raise click.ClickException(
            f"Need at least {min_positive} positive examples. "
            "Make sure the inscription corpus is available. "
            "Run: etruscan corpus import-inscriptions"
        )

    # Load negative examples
    click.echo("\n2. Loading Latin vocabulary...")
    latin_words = _load_latin_vocabulary(latin_vocab)
    click.echo(f"   Loaded {len(latin_words)} Latin words")

    if len(latin_words) < min_negative:
        raise click.ClickException(
            f"Need at least {min_negative} negative examples. "
            f"Latin vocabulary file: {latin_vocab}"
        )

    # Balance dataset
    if len(etruscan_words) > len(latin_words):
        click.echo(f"\n   Note: More Etruscan ({len(etruscan_words)}) than Latin ({len(latin_words)}) words")
        click.echo(f"   Using all {len(latin_words)} Latin words and {len(latin_words)} Etruscan words")
        random.seed(42)
        etruscan_words = random.sample(etruscan_words, len(latin_words))
    elif len(latin_words) > len(etruscan_words):
        click.echo(f"\n   Note: More Latin ({len(latin_words)}) than Etruscan ({len(etruscan_words)}) words")
        click.echo(f"   Using all {len(etruscan_words)} Etruscan words and {len(etruscan_words)} Latin words")
        random.seed(42)
        latin_words = random.sample(latin_words, len(etruscan_words))

    # Show samples
    click.echo("\n3. Sample positive (Etruscan) words:")
    for word in sorted(etruscan_words)[:10]:
        click.echo(f"      {word}")
    click.echo("      ...")

    click.echo("\n4. Sample negative (Latin) words:")
    for word in sorted(latin_words)[:10]:
        click.echo(f"      {word}")
    click.echo("      ...")

    # Train
    click.echo("\n5. Training classifier...")
    classifier = WordClassifier()
    classifier.train(etruscan_words, latin_words)

    # Save
    click.echo(f"\n6. Saving model to {output}...")
    output.parent.mkdir(parents=True, exist_ok=True)
    classifier.save(output)

    # Test
    if test:
        click.echo("\n7. Test predictions:")
        click.echo("-" * 40)

        test_cases = [
            ("ais", "Etruscan (god)"),
            ("clan", "Etruscan (son)"),
            ("puia", "Etruscan (wife)"),
            ("zilath", "Etruscan (magistrate)"),
            ("lauchum", "Etruscan (king)"),
            ("subulo", "Etruscan via Varro"),
            ("lanista", "Etruscan via Isidore"),
            ("dominus", "Latin"),
            ("imperium", "Latin"),
            ("aqua", "Latin"),
            ("terra", "Latin"),
            ("victoria", "Latin"),
        ]

        click.echo(f"{'Word':<15} {'Score':>8}  {'Expected':<25}")
        click.echo("-" * 50)
        for word, expected in test_cases:
            score = classifier.predict(word)
            indicator = "+" if score > 0.5 else "-"
            click.echo(f"{word:<15} {score:>7.3f}  {indicator} ({expected})")

    # Feature importance
    if importance:
        click.echo("\n8. Feature importance:")
        click.echo("-" * 40)
        importance_data = classifier.get_feature_importance(top_n=15)

        click.echo("\nTop Etruscan indicators (positive coefficients):")
        for name, coef in importance_data['etruscan_indicators'][:15]:
            click.echo(f"  {name:<20} {coef:>8.4f}")

        click.echo("\nTop Latin indicators (negative coefficients):")
        for name, coef in importance_data['latin_indicators'][:15]:
            click.echo(f"  {name:<20} {coef:>8.4f}")

    click.echo("\n" + "=" * 60)
    click.echo("Training complete!")
    click.echo("=" * 60)


@train.command("context-classifier")
@click.option("--test", is_flag=True, help="Run test predictions after training")
@click.option("--labeled-data", type=click.Path(exists=True, path_type=Path),
              default=None, help="Path to labeled candidates JSON file")
@click.option("--output", type=click.Path(path_type=Path),
              default=None, help="Path to save trained model")
def context_classifier(test: bool, labeled_data: Path, output: Path):
    """Train the context classifier.

    Uses TF-IDF or embeddings to classify whether a context
    passage is truly discussing Etruscan vocabulary.
    """
    if labeled_data is None:
        labeled_data = DATA_DIR / "labeled_candidates.json"
    if output is None:
        output = DATA_DIR / "models" / "context_classifier"

    if not labeled_data.exists():
        raise click.ClickException(
            f"Labeled data not found: {labeled_data}. "
            "Create labeled training data first."
        )

    click.echo("=" * 60)
    click.echo("Context Classifier Training")
    click.echo("=" * 60)

    from ...validation.context_classifier import ContextClassifier

    click.echo(f"\nLoading labeled data from {labeled_data}...")
    classifier = ContextClassifier()

    import json
    with open(labeled_data) as f:
        data = json.load(f)

    positive = [item["context"] for item in data if item.get("is_etruscan", False)]
    negative = [item["context"] for item in data if not item.get("is_etruscan", True)]

    click.echo(f"  Positive examples: {len(positive)}")
    click.echo(f"  Negative examples: {len(negative)}")

    if len(positive) < 10 or len(negative) < 10:
        raise click.ClickException(
            "Need at least 10 positive and 10 negative examples. "
            "Add more labeled data."
        )

    click.echo("\nTraining classifier...")
    classifier.train(positive, negative)

    click.echo(f"\nSaving model to {output}...")
    output.mkdir(parents=True, exist_ok=True)
    classifier.save(output)

    if test:
        click.echo("\nTest predictions:")
        test_contexts = [
            "Tusci vocant subulo quod nos tibicinem dicimus",
            "The quick brown fox jumps over the lazy dog",
            "Etrusca disciplina teaches the art of haruspicy",
        ]
        for ctx in test_contexts:
            score = classifier.predict(ctx)
            click.echo(f"  {ctx[:50]}... -> {score:.2f}")

    click.echo("\nTraining complete!")


def _load_etruscan_vocabulary() -> list[str]:
    """Load Etruscan vocabulary from inscription corpus."""
    loader = InscriptionLoader()
    vocabulary = loader.extract_vocabulary()
    return list(vocabulary)


def _load_latin_vocabulary(path: Path) -> list[str]:
    """Load Latin vocabulary from text file."""
    if not path.exists():
        click.echo(f"Warning: Latin vocabulary file not found: {path}")
        return []

    words = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            word = line.lower().strip()
            if len(word) >= 2:
                words.append(word)

    return words
