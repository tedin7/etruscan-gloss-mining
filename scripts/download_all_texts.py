#!/usr/bin/env python3
"""Download all Latin classical texts from multiple sources.

Sources:
- Latin Library (thelatinlibrary.com) - HTML scraping
- Perseus CTS API - XML passages
- CLTK corpora - Pre-curated texts
- GitHub repositories - Cloned repos

Respects rate limits and saves to data/corpus/.
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from etruscan_miner.corpus.latin_library import LatinLibraryClient, LATIN_LIBRARY_URLS
from etruscan_miner.config import CORPUS_CACHE_DIR


def download_latin_library(priority: str = "all", force: bool = False):
    """Download texts from the Latin Library.

    Args:
        priority: "high", "medium", "all" to filter by priority
        force: Force re-download even if cached
    """
    client = LatinLibraryClient(rate_limit=2.0)

    # Categorize by priority
    high_priority = [k for k in LATIN_LIBRARY_URLS if k.startswith(("varro_", "festus", "isidore_", "solinus_"))]
    medium_priority = [k for k in LATIN_LIBRARY_URLS if k.startswith(("suetonius_", "livy_"))]
    other = [k for k in LATIN_LIBRARY_URLS if k not in high_priority and k not in medium_priority]

    if priority == "high":
        text_ids = high_priority
    elif priority == "medium":
        text_ids = high_priority + medium_priority
    else:
        text_ids = high_priority + medium_priority + other

    print(f"\n{'='*60}")
    print("LATIN LIBRARY DOWNLOAD")
    print(f"{'='*60}")
    print(f"Total texts to download: {len(text_ids)}")
    print(f"Cache directory: {client.cache_dir}")
    print()

    downloaded = 0
    skipped = 0
    failed = 0

    for i, text_id in enumerate(text_ids, 1):
        cache_path = client._get_cache_path(text_id)

        if cache_path.exists() and not force:
            print(f"[{i}/{len(text_ids)}] {text_id}: cached (skipping)")
            skipped += 1
            continue

        url = LATIN_LIBRARY_URLS[text_id]
        print(f"[{i}/{len(text_ids)}] {text_id}: downloading...")

        html = client.download_text(text_id, url)
        if html:
            downloaded += 1
            print(f"  -> saved ({len(html)} bytes)")
        else:
            failed += 1
            print(f"  -> FAILED")

    print(f"\n{'='*60}")
    print(f"Latin Library complete: {downloaded} downloaded, {skipped} skipped, {failed} failed")
    print(f"{'='*60}")


def download_perseus_texts(force: bool = False):
    """Download texts from Perseus CTS API.

    Uses existing download_corpus.py infrastructure.
    """
    print(f"\n{'='*60}")
    print("PERSEUS CTS DOWNLOAD")
    print(f"{'='*60}")

    # Run existing download script
    script_path = Path(__file__).parent / "download_corpus.py"
    cmd = [sys.executable, str(script_path), "--all"]
    if force:
        cmd.append("--force")

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)

    if result.returncode == 0:
        print("\nPerseus download complete")
    else:
        print(f"\nPerseus download failed with code {result.returncode}")


def download_cltk_corpora():
    """Download CLTK Latin corpora.

    Requires: pip install cltk
    """
    print(f"\n{'='*60}")
    print("CLTK CORPORA DOWNLOAD")
    print(f"{'='*60}")

    try:
        from cltk.corpus.utils.importer import CorpusImporter
    except ImportError:
        print("CLTK not installed. Install with: pip install cltk")
        print("Skipping CLTK download.")
        return

    importer = CorpusImporter("lat")
    corpora = ["lat_text_latin_library", "lat_text_perseus"]

    for corpus in corpora:
        print(f"Downloading {corpus}...")
        try:
            importer.import_corpus(corpus)
            print(f"  -> {corpus} downloaded")
        except Exception as e:
            print(f"  -> {corpus} failed: {e}")

    # Create symlink to CLTK data if it exists
    cltk_data = Path.home() / "cltk_data" / "lat"
    cltk_link = CORPUS_CACHE_DIR / "cltk"

    if cltk_data.exists() and not cltk_link.exists():
        try:
            cltk_link.symlink_to(cltk_data)
            print(f"\nCreated symlink: {cltk_link} -> {cltk_data}")
        except Exception as e:
            print(f"\nCouldn't create symlink: {e}")

    print("\nCLTK download complete")


def clone_github_repos(force: bool = False):
    """Clone GitHub repositories with Latin texts.

    Repos:
    - cltk/lat_text_latin_library
    """
    print(f"\n{'='*60}")
    print("GITHUB REPOSITORIES")
    print(f"{'='*60}")

    github_dir = CORPUS_CACHE_DIR / "github"
    github_dir.mkdir(parents=True, exist_ok=True)

    repos = [
        ("cltk/lat_text_latin_library", "lat_text_latin_library"),
    ]

    for repo, dirname in repos:
        target = github_dir / dirname

        if target.exists() and not force:
            print(f"{repo}: already cloned (skipping)")
            continue

        print(f"Cloning {repo}...")
        cmd = ["git", "clone", "--depth", "1", f"https://github.com/{repo}.git", str(target)]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  -> cloned to {target}")
        else:
            print(f"  -> FAILED: {result.stderr}")

    print("\nGitHub clone complete")


def show_stats():
    """Show download statistics."""
    print(f"\n{'='*60}")
    print("CORPUS STATISTICS")
    print(f"{'='*60}")

    if not CORPUS_CACHE_DIR.exists():
        print("No corpus directory found")
        return

    for subdir in sorted(CORPUS_CACHE_DIR.iterdir()):
        if subdir.is_dir():
            files = list(subdir.rglob("*"))
            file_count = sum(1 for f in files if f.is_file())
            total_size = sum(f.stat().st_size for f in files if f.is_file())
            print(f"  {subdir.name}: {file_count} files, {total_size / 1024:.1f} KB")


def verify_gitignore():
    """Verify data/corpus/ is in .gitignore."""
    gitignore = Path(__file__).parent.parent / ".gitignore"
    if gitignore.exists():
        content = gitignore.read_text()
        if "data/corpus" in content or "data/corpus/" in content:
            print("\n.gitignore: data/corpus/ is excluded")
        else:
            print("\nWARNING: data/corpus/ may not be in .gitignore!")
    else:
        print("\nWARNING: No .gitignore found!")


def main():
    parser = argparse.ArgumentParser(
        description="Download all Latin classical texts from multiple sources",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --all              Download everything
  %(prog)s --latin-library    Download Latin Library texts only
  %(prog)s --priority high    Download high-priority texts only
  %(prog)s --stats            Show download statistics
        """,
    )

    parser.add_argument("--all", "-a", action="store_true", help="Download from all sources")
    parser.add_argument("--latin-library", "-L", action="store_true", help="Download from Latin Library")
    parser.add_argument("--perseus", "-P", action="store_true", help="Download from Perseus")
    parser.add_argument("--cltk", "-C", action="store_true", help="Download CLTK corpora")
    parser.add_argument("--github", "-G", action="store_true", help="Clone GitHub repositories")
    parser.add_argument(
        "--priority",
        "-p",
        choices=["high", "medium", "all"],
        default="all",
        help="Priority filter for Latin Library (default: all)",
    )
    parser.add_argument("--force", "-f", action="store_true", help="Force re-download")
    parser.add_argument("--stats", "-s", action="store_true", help="Show download statistics")

    args = parser.parse_args()

    # Ensure corpus directory exists
    CORPUS_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    if args.stats:
        show_stats()
        return

    if not any([args.all, args.latin_library, args.perseus, args.cltk, args.github]):
        parser.print_help()
        return

    if args.all or args.latin_library:
        download_latin_library(priority=args.priority, force=args.force)

    if args.all or args.perseus:
        download_perseus_texts(force=args.force)

    if args.all or args.cltk:
        download_cltk_corpora()

    if args.all or args.github:
        clone_github_repos(force=args.force)

    show_stats()
    verify_gitignore()


if __name__ == "__main__":
    main()
