"""Database operations command group."""

import re
import click
from pathlib import Path

from ...config import DB_PATH, DATA_DIR, PROJECT_ROOT
from ...db.models import EtruscanWord, VerifiedGloss
from ...db.repository import Repository
from ..utils import print_stats


@click.group()
def db():
    """Database operations (setup, stats, reset, import-seeds)."""
    pass


@db.command()
def setup():
    """Create the database and initialize schema."""
    # Ensure data directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Read schema
    schema_path = Path(__file__).parents[2] / "db" / "schema.sql"
    if not schema_path.exists():
        raise click.ClickException(f"Schema not found: {schema_path}")

    with open(schema_path) as f:
        schema_sql = f.read()

    # Create database
    repo = Repository(DB_PATH)
    with repo.connection() as conn:
        conn.executescript(schema_sql)

    click.echo(f"Database created at: {DB_PATH}")

    # Verify
    stats = repo.get_stats()
    print_stats(stats)

    # Show patterns loaded
    patterns = repo.get_active_patterns()
    click.echo(f"\nLoaded {len(patterns)} patterns:")
    for p in patterns:
        click.echo(f"  - {p.name}: {p.description}")


@db.command()
def stats():
    """Show database statistics."""
    if not DB_PATH.exists():
        raise click.ClickException(
            f"Database not found at {DB_PATH}. Run 'etruscan db setup' first."
        )

    repo = Repository(DB_PATH)
    db_stats = repo.get_stats()
    print_stats(db_stats)


@db.command()
@click.option("--force", "-f", is_flag=True, help="Skip confirmation prompt")
def reset(force: bool):
    """Reset the database (delete and recreate)."""
    if not force:
        click.confirm(
            "This will delete all data. Are you sure?",
            abort=True,
        )

    if DB_PATH.exists():
        DB_PATH.unlink()
        click.echo(f"Deleted: {DB_PATH}")

    # Recreate
    ctx = click.get_current_context()
    ctx.invoke(setup)


@db.command("import-seeds")
def import_seeds():
    """Import seed data from markdown files."""
    if not DB_PATH.exists():
        raise click.ClickException(
            f"Database not found at {DB_PATH}. Run 'etruscan db setup' first."
        )

    repo = Repository(DB_PATH)

    # Import ancient glosses
    ancient_glosses_path = PROJECT_ROOT / "ANCIENT_GLOSSES_VERIFIED.md"
    if ancient_glosses_path.exists():
        click.echo(f"Parsing {ancient_glosses_path.name}...")
        with open(ancient_glosses_path, encoding="utf-8") as f:
            content = f.read()
        glosses = _parse_ancient_glosses(content)
        click.echo(f"  Found {len(glosses)} glosses")

        imported = 0
        for gloss in glosses:
            try:
                repo.insert_verified_gloss(gloss)
                imported += 1
            except Exception as e:
                click.echo(f"  Warning: Could not import {gloss.etruscan_word}: {e}")
        click.echo(f"  Imported {imported} verified glosses")
    else:
        click.echo(f"Warning: {ancient_glosses_path} not found")

    # Import Forni consensus vocabulary
    forni_path = PROJECT_ROOT / "CONSENSUS_GLOSSES_FORNI.md"
    if forni_path.exists():
        click.echo(f"\nParsing {forni_path.name}...")
        with open(forni_path, encoding="utf-8") as f:
            content = f.read()
        words = _parse_forni_consensus(content)
        click.echo(f"  Found {len(words)} vocabulary words")

        imported = 0
        for word in words:
            try:
                repo.insert_vocabulary(word)
                imported += 1
            except Exception as e:
                click.echo(f"  Warning: Could not import {word.word}: {e}")
        click.echo(f"  Imported {imported} vocabulary words")
    else:
        click.echo(f"Warning: {forni_path} not found")

    # Print final stats
    print_stats(repo.get_stats())


def _parse_ancient_glosses(content: str) -> list[VerifiedGloss]:
    """Parse ANCIENT_GLOSSES_VERIFIED.md and extract glosses."""
    glosses = []

    entry_pattern = re.compile(
        r"###\s+\d+\.\s+\*\*([^*]+)\*\*\s*=\s*[\"']([^\"']+)[\"']",
        re.MULTILINE
    )

    for match in entry_pattern.finditer(content):
        word_part = match.group(1).strip()
        meaning = match.group(2).strip()
        words = [w.strip() for w in word_part.split("/")]

        start_pos = match.end()
        next_match = entry_pattern.search(content, start_pos)
        end_pos = next_match.start() if next_match else len(content)
        context = content[start_pos:end_pos]

        source_author = None
        source_match = re.search(r"\*\*Fonte[^:]*:\*\*\s*([^\n]+)", context)
        if source_match:
            source_text = source_match.group(1).strip()
            if "Svetonio" in source_text or "Suetonius" in source_text:
                source_author = "Suetonius"
            elif "Varrone" in source_text or "Varro" in source_text:
                source_author = "Varro"
            elif "Livio" in source_text or "Livy" in source_text:
                source_author = "Livy"
            elif "Isidoro" in source_text or "Isidore" in source_text:
                source_author = "Isidore"
            elif "Festo" in source_text or "Festus" in source_text:
                source_author = "Festus"
            elif "Plinio" in source_text or "Pliny" in source_text:
                source_author = "Pliny"
            else:
                source_author = source_text.split(",")[0].split("(")[0].strip()

        citation = None
        citation_match = re.search(r"\*\*Citazione:\*\*\s*[\"']([^\"']+)[\"']", context)
        if citation_match:
            citation = citation_match.group(1).strip()

        reliability = 3
        stars = context.count("⭐")
        if stars >= 5:
            reliability = 5
        elif stars >= 4:
            reliability = 4
        elif stars >= 3:
            reliability = 3
        elif stars >= 2:
            reliability = 2
        elif stars >= 1:
            reliability = 1

        for word in words:
            word = word.strip()
            if not word:
                continue
            gloss = VerifiedGloss(
                etruscan_word=word,
                etruscan_normalized=word.lower(),
                meaning=meaning,
                source_author=source_author,
                source_quote=citation,
                reliability=reliability,
                is_seed=True,
            )
            glosses.append(gloss)

    return glosses


def _parse_forni_consensus(content: str) -> list[EtruscanWord]:
    """Parse CONSENSUS_GLOSSES_FORNI.md and extract vocabulary."""
    words = []

    table_pattern = re.compile(
        r"\|\s*\d+\s*\|\s*\*\*([^*]+)\*\*\s*\|\s*[\"']?([^|\"']+)[\"']?\s*\|",
        re.MULTILINE
    )

    current_category = "basic"
    sections = {
        "LESSICO BASE CON SIGNIFICATO CERTO": "basic",
        "LESSICO NON-BASE CON SIGNIFICATO CERTO": "non-basic",
        "MORFEMI LEGATI": "morpheme",
        "LESSICO BASE CON SIGNIFICATO DUBBIO": "basic-uncertain",
        "LESSICO NON-BASE CON SIGNIFICATO DUBBIO": "non-basic-uncertain",
    }

    lines = content.split("\n")
    for line in lines:
        for section_name, category in sections.items():
            if section_name in line:
                current_category = category
                break

        match = table_pattern.match(line)
        if match:
            word_text = match.group(1).strip()
            meaning = match.group(2).strip()
            word_variants = [w.strip() for w in re.split(r"[,/]", word_text)]
            uncertain = "uncertain" in current_category or "?" in meaning

            for word in word_variants:
                if not word or word == "-":
                    continue
                word = re.sub(r"\s*\([^)]*\)\s*$", "", word).strip()
                word = word.strip("-").strip()

                if not word:
                    continue

                vocab = EtruscanWord(
                    word=word,
                    word_normalized=word.lower(),
                    meaning=meaning,
                    meaning_uncertain=uncertain,
                    category=current_category.replace("-uncertain", ""),
                    source="Forni",
                    reliability=4 if not uncertain else 3,
                )
                words.append(vocab)

    return words
