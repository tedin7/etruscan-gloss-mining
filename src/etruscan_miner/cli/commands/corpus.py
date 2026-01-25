"""Corpus download and management command group."""

import json
import subprocess
import click
from pathlib import Path

from ...config import CORPUS_CACHE_DIR, TARGET_WORKS
from ...corpus.latin_library import LatinLibraryClient, LATIN_LIBRARY_URLS
from ...corpus.perseus import PerseusClient
from ...corpus.text_cache import WorkCache
from ...corpus.greek_texts import GreekCorpusClient, GREEK_WORKS
from ..utils import get_corpus_info


@click.group()
def corpus():
    """Download and manage corpus texts."""
    pass


@corpus.command()
@click.option("--all", "-a", "download_all", is_flag=True, help="Download from all sources")
@click.option("--source", "-s", type=click.Choice([
    "latin_library", "perseus", "greek", "github", "cltk"
]), multiple=True, help="Specific source(s) to download")
@click.option("--priority", "-p", type=click.Choice(["high", "medium", "all"]),
              default="all", help="Priority filter (default: all)")
@click.option("--force", "-f", is_flag=True, help="Force re-download even if cached")
def download(download_all: bool, source: tuple, priority: str, force: bool):
    """Download corpus texts from various sources."""
    CORPUS_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    sources = set(source) if source else set()
    if download_all:
        sources = {"latin_library", "perseus", "greek", "github"}

    if not sources:
        click.echo("Specify --all or one or more --source options. Use 'etruscan corpus download --help'.")
        return

    if "latin_library" in sources:
        _download_latin_library(priority, force)

    if "perseus" in sources:
        _download_perseus(priority, force)

    if "greek" in sources:
        _download_greek(priority, force)

    if "github" in sources:
        _clone_github_repos(force)

    if "cltk" in sources:
        _download_cltk()

    # Show final stats
    _show_corpus_stats()


@corpus.command()
def stats():
    """Show corpus download statistics."""
    _show_corpus_stats()


@corpus.command("import-inscriptions")
@click.option("--dry-run", is_flag=True, help="Preview without importing")
@click.option("--stats-only", is_flag=True, help="Show statistics only")
def import_inscriptions(dry_run: bool, stats_only: bool):
    """Import Etruscan inscription vocabulary from CIEW corpus."""
    from ...corpus.inscriptions import InscriptionLoader

    loader = InscriptionLoader()

    if stats_only:
        stats = loader.get_stats()
        click.echo("\nInscription corpus statistics:")
        for key, value in stats.items():
            click.echo(f"  {key}: {value}")
        return

    vocabulary = loader.extract_vocabulary()
    click.echo(f"\nExtracted {len(vocabulary)} unique words from inscriptions")

    if dry_run:
        click.echo("\nDry run - no changes made")
        click.echo("\nSample words:")
        for word in sorted(vocabulary)[:20]:
            click.echo(f"  {word}")
        return

    # Import to database
    from ...config import DB_PATH
    from ...db.repository import Repository

    if not DB_PATH.exists():
        raise click.ClickException("Database not found. Run 'etruscan db setup' first.")

    repo = Repository(DB_PATH)
    imported = 0
    for word in vocabulary:
        try:
            repo.add_inscription_word(word)
            imported += 1
        except Exception:
            pass

    click.echo(f"Imported {imported} inscription words to database")


def _download_latin_library(priority: str, force: bool):
    """Download texts from the Latin Library."""
    client = LatinLibraryClient(rate_limit=2.0)

    high_priority = [k for k in LATIN_LIBRARY_URLS
                     if k.startswith(("varro_", "festus", "isidore_", "solinus_"))]
    medium_priority = [k for k in LATIN_LIBRARY_URLS
                       if k.startswith(("suetonius_", "livy_"))]
    other = [k for k in LATIN_LIBRARY_URLS
             if k not in high_priority and k not in medium_priority]

    if priority == "high":
        text_ids = high_priority
    elif priority == "medium":
        text_ids = high_priority + medium_priority
    else:
        text_ids = high_priority + medium_priority + other

    click.echo(f"\n{'='*60}")
    click.echo("LATIN LIBRARY DOWNLOAD")
    click.echo(f"{'='*60}")
    click.echo(f"Total texts to download: {len(text_ids)}")
    click.echo(f"Cache directory: {client.cache_dir}")

    downloaded = skipped = failed = 0

    with click.progressbar(text_ids, label="Downloading") as bar:
        for text_id in bar:
            cache_path = client._get_cache_path(text_id)

            if cache_path.exists() and not force:
                skipped += 1
                continue

            url = LATIN_LIBRARY_URLS[text_id]
            html = client.download_text(text_id, url)
            if html:
                downloaded += 1
            else:
                failed += 1

    click.echo(f"\nLatin Library: {downloaded} downloaded, {skipped} skipped, {failed} failed")


def _download_perseus(priority: str, force: bool):
    """Download Latin texts from Perseus CTS API."""
    click.echo(f"\n{'='*60}")
    click.echo("PERSEUS CTS DOWNLOAD (Latin)")
    click.echo(f"{'='*60}")

    client = PerseusClient()
    cache = WorkCache()

    works_to_download = []
    for key, work in TARGET_WORKS.items():
        if not work.get("urn"):
            continue
        work_priority = work.get("priority", "LOW")
        if priority == "high" and work_priority != "HIGH":
            continue
        if priority == "medium" and work_priority == "LOW":
            continue
        works_to_download.append((key, work))

    click.echo(f"Works to download: {len(works_to_download)}")

    downloaded = skipped = failed = 0

    for key, work in works_to_download:
        urn = work["urn"]

        if not force:
            cached = cache.get_work(urn)
            if cached:
                click.echo(f"  {key}: cached ({len(cached)} passages)")
                skipped += 1
                continue

        click.echo(f"  {key}: downloading...")
        passages = client.get_work_text(urn)

        if passages:
            cache.put_work(urn, passages)
            click.echo(f"    -> saved ({len(passages)} passages)")
            downloaded += 1
        else:
            click.echo(f"    -> FAILED")
            failed += 1

    click.echo(f"\nPerseus Latin: {downloaded} downloaded, {skipped} skipped, {failed} failed")


def _download_greek(priority: str, force: bool):
    """Download Greek texts from Perseus CTS API."""
    click.echo(f"\n{'='*60}")
    click.echo("PERSEUS CTS DOWNLOAD (Greek)")
    click.echo(f"{'='*60}")

    client = GreekCorpusClient()
    greek_dir = CORPUS_CACHE_DIR / "greek"
    greek_dir.mkdir(parents=True, exist_ok=True)

    works_to_download = []
    for key, work in GREEK_WORKS.items():
        work_priority = work.get("priority", "LOW")
        if priority == "high" and work_priority != "HIGH":
            continue
        if priority == "medium" and work_priority == "LOW":
            continue
        works_to_download.append((key, work))

    click.echo(f"Works to download: {len(works_to_download)}")
    click.echo(f"Cache directory: {greek_dir}")

    downloaded = skipped = failed = 0

    for key, work in works_to_download:
        cache_path = greek_dir / f"{key}.json"

        if cache_path.exists() and not force:
            with open(cache_path, "r", encoding="utf-8") as f:
                cached = json.load(f)
            click.echo(f"  {key}: cached ({len(cached)} passages)")
            skipped += 1
            continue

        click.echo(f"  {key}: downloading ({work['title']})...")

        if key == "dionysius_ant_rom":
            passages = client.fetch_dionysius_book5()
        elif key == "strabo_geography":
            passages = client.fetch_strabo_book5()
        else:
            passages = client.fetch_work(key, max_passages=200)

        if passages:
            data = [
                {
                    "urn": p.urn,
                    "reference": p.reference,
                    "text": p.text,
                    "author": p.author,
                    "work": p.work,
                    "source_url": p.source_url,
                    "has_tyrrhenian_ref": p.contains_tyrrhenian_ref,
                }
                for p in passages
            ]
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            tyrr_count = sum(1 for p in passages if p.contains_tyrrhenian_ref)
            click.echo(f"    -> saved ({len(passages)} passages, {tyrr_count} Tyrrhenian refs)")
            downloaded += 1
        else:
            click.echo(f"    -> FAILED")
            failed += 1

    click.echo(f"\nPerseus Greek: {downloaded} downloaded, {skipped} skipped, {failed} failed")


def _clone_github_repos(force: bool):
    """Clone GitHub repositories with Latin texts."""
    click.echo(f"\n{'='*60}")
    click.echo("GITHUB REPOSITORIES")
    click.echo(f"{'='*60}")

    github_dir = CORPUS_CACHE_DIR / "github"
    github_dir.mkdir(parents=True, exist_ok=True)

    repos = [
        ("cltk/lat_text_latin_library", "lat_text_latin_library"),
    ]

    for repo, dirname in repos:
        target = github_dir / dirname

        if target.exists() and not force:
            click.echo(f"{repo}: already cloned (skipping)")
            continue

        click.echo(f"Cloning {repo}...")
        cmd = ["git", "clone", "--depth", "1",
               f"https://github.com/{repo}.git", str(target)]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            click.echo(f"  -> cloned to {target}")
        else:
            click.echo(f"  -> FAILED: {result.stderr}")


def _download_cltk():
    """Download CLTK corpora."""
    click.echo(f"\n{'='*60}")
    click.echo("CLTK CORPORA DOWNLOAD")
    click.echo(f"{'='*60}")

    try:
        from cltk.corpus.utils.importer import CorpusImporter
    except ImportError:
        click.echo("CLTK not installed. Install with: pip install cltk")
        return

    importer = CorpusImporter("lat")
    corpora = ["lat_text_latin_library", "lat_text_perseus"]

    for corpus_name in corpora:
        click.echo(f"Downloading {corpus_name}...")
        try:
            importer.import_corpus(corpus_name)
            click.echo(f"  -> {corpus_name} downloaded")
        except Exception as e:
            click.echo(f"  -> {corpus_name} failed: {e}")


def _show_corpus_stats():
    """Show download statistics."""
    click.echo(f"\n{'='*60}")
    click.echo("CORPUS STATISTICS")
    click.echo(f"{'='*60}")

    if not CORPUS_CACHE_DIR.exists():
        click.echo("No corpus directory found")
        return

    total_files = 0
    total_size = 0

    for subdir in sorted(CORPUS_CACHE_DIR.iterdir()):
        if subdir.is_dir():
            files = list(subdir.rglob("*"))
            file_count = sum(1 for f in files if f.is_file())
            dir_size = sum(f.stat().st_size for f in files if f.is_file())
            total_files += file_count
            total_size += dir_size

            if subdir.name == "greek":
                tyrr_count = 0
                for json_file in subdir.glob("*.json"):
                    try:
                        with open(json_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        tyrr_count += sum(1 for p in data if p.get("has_tyrrhenian_ref"))
                    except Exception:
                        pass
                click.echo(f"  {subdir.name}: {file_count} files, "
                          f"{dir_size / 1024:.1f} KB ({tyrr_count} Tyrrhenian refs)")
            else:
                click.echo(f"  {subdir.name}: {file_count} files, {dir_size / 1024:.1f} KB")

    click.echo(f"\n  Total: {total_files} files, {total_size / 1024 / 1024:.1f} MB")
