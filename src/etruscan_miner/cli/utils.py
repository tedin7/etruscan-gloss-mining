"""Shared CLI utilities."""

import click
from pathlib import Path

from ..config import DB_PATH, DATA_DIR, CORPUS_CACHE_DIR


def ensure_database(ctx: click.Context) -> None:
    """Ensure the database exists before running a command.

    Args:
        ctx: Click context

    Raises:
        click.ClickException: If database doesn't exist
    """
    if not DB_PATH.exists():
        raise click.ClickException(
            f"Database not found at {DB_PATH}. "
            "Run 'etruscan db setup' first."
        )


def print_stats(stats: dict[str, int]) -> None:
    """Print database statistics in a formatted way.

    Args:
        stats: Dictionary of table names to counts
    """
    click.echo("\nDatabase statistics:")
    for table, count in stats.items():
        click.echo(f"  {table}: {count}")


def format_confidence(confidence: float) -> str:
    """Format confidence level with color.

    Args:
        confidence: Confidence value 0-1

    Returns:
        Colored string
    """
    if confidence >= 0.85:
        return click.style(f"{confidence:.2f}", fg="green", bold=True)
    elif confidence >= 0.65:
        return click.style(f"{confidence:.2f}", fg="yellow")
    else:
        return click.style(f"{confidence:.2f}", fg="red")


def validate_path(path: Path, must_exist: bool = False) -> Path:
    """Validate a file path.

    Args:
        path: Path to validate
        must_exist: Whether the path must exist

    Returns:
        Resolved path

    Raises:
        click.BadParameter: If validation fails
    """
    path = Path(path).resolve()
    if must_exist and not path.exists():
        raise click.BadParameter(f"Path does not exist: {path}")
    return path


def get_corpus_info() -> dict[str, dict]:
    """Get information about available corpus sources.

    Returns:
        Dictionary of corpus sources and their info
    """
    return {
        "latin_library": {
            "name": "Latin Library",
            "description": "HTML texts from thelatinlibrary.com",
            "cache_dir": CORPUS_CACHE_DIR / "latin_library",
        },
        "perseus": {
            "name": "Perseus CTS (Latin)",
            "description": "XML passages from Perseus CTS API",
            "cache_dir": CORPUS_CACHE_DIR / "perseus",
        },
        "greek": {
            "name": "Perseus CTS (Greek)",
            "description": "Greek texts with Etruscan references",
            "cache_dir": CORPUS_CACHE_DIR / "greek",
        },
        "github": {
            "name": "GitHub CLTK",
            "description": "Cloned CLTK repositories",
            "cache_dir": CORPUS_CACHE_DIR / "github",
        },
        "inscriptions": {
            "name": "Inscriptions",
            "description": "CIEW Etruscan inscription corpus",
            "cache_dir": CORPUS_CACHE_DIR / "inscriptions",
        },
    }
