#!/usr/bin/env python3
"""Download all classical texts from multiple sources.

Sources:
- Latin Library (thelatinlibrary.com) - HTML scraping
- Perseus CTS API (Latin) - XML passages
- Perseus CTS API (Greek) - Greek texts with Etruscan references
- CLTK corpora - Pre-curated texts
- GitHub repositories - Cloned repos

Respects rate limits and saves to data/corpus/.
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from etruscan_miner.corpus.latin_library import LatinLibraryClient, LATIN_LIBRARY_URLS
from etruscan_miner.corpus.perseus import PerseusClient
from etruscan_miner.corpus.text_cache import WorkCache
from etruscan_miner.corpus.greek_texts import (
    GreekCorpusClient,
    GREEK_WORKS,
    GreekPassage,
)
from etruscan_miner.config import CORPUS_CACHE_DIR, TARGET_WORKS


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


def download_perseus_texts(priority: str = "all", force: bool = False):
    """Download Latin texts from Perseus CTS API.

    Args:
        priority: "high", "medium", "all" to filter by priority
        force: Force re-download even if cached
    """
    print(f"\n{'='*60}")
    print("PERSEUS CTS DOWNLOAD (Latin)")
    print(f"{'='*60}")

    client = PerseusClient()
    cache = WorkCache()

    # Filter by priority
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

    print(f"Works to download: {len(works_to_download)}")

    downloaded = 0
    skipped = 0
    failed = 0

    for key, work in works_to_download:
        urn = work["urn"]
        title = f"{work['author']}: {work['title']}"

        # Check cache
        if not force:
            cached = cache.get_work(urn)
            if cached:
                print(f"  {key}: cached ({len(cached)} passages)")
                skipped += 1
                continue

        print(f"  {key}: downloading...")
        passages = client.get_work_text(urn)

        if passages:
            cache.put_work(urn, passages)
            print(f"    -> saved ({len(passages)} passages)")
            downloaded += 1
        else:
            print(f"    -> FAILED (no passages)")
            failed += 1

    print(f"\n{'='*60}")
    print(f"Perseus Latin complete: {downloaded} downloaded, {skipped} skipped, {failed} failed")
    print(f"{'='*60}")


def download_greek_texts(priority: str = "all", force: bool = False):
    """Download Greek texts from Perseus CTS API.

    Focuses on texts that discuss Etruscan/Tyrrhenian culture.

    Args:
        priority: "high", "medium", "all" to filter by priority
        force: Force re-download even if cached
    """
    print(f"\n{'='*60}")
    print("PERSEUS CTS DOWNLOAD (Greek)")
    print(f"{'='*60}")

    client = GreekCorpusClient()
    greek_dir = CORPUS_CACHE_DIR / "greek"
    greek_dir.mkdir(parents=True, exist_ok=True)

    # Filter by priority
    works_to_download = []
    for key, work in GREEK_WORKS.items():
        work_priority = work.get("priority", "LOW")
        if priority == "high" and work_priority != "HIGH":
            continue
        if priority == "medium" and work_priority == "LOW":
            continue
        works_to_download.append((key, work))

    print(f"Works to download: {len(works_to_download)}")
    print(f"Cache directory: {greek_dir}")

    downloaded = 0
    skipped = 0
    failed = 0

    for key, work in works_to_download:
        cache_path = greek_dir / f"{key}.json"

        # Check cache
        if cache_path.exists() and not force:
            with open(cache_path, "r", encoding="utf-8") as f:
                cached = json.load(f)
            print(f"  {key}: cached ({len(cached)} passages)")
            skipped += 1
            continue

        print(f"  {key}: downloading ({work['title']})...")

        # Special handling for important books
        if key == "dionysius_ant_rom":
            # Focus on book 5 (Etruscan content)
            passages = client.fetch_dionysius_book5()
        elif key == "strabo_geography":
            # Focus on book 5 (Etruria)
            passages = client.fetch_strabo_book5()
        else:
            # General fetch
            passages = client.fetch_work(key, max_passages=200)

        if passages:
            # Serialize passages to JSON
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
            print(f"    -> saved ({len(passages)} passages, {tyrr_count} with Tyrrhenian refs)")
            downloaded += 1
        else:
            print(f"    -> FAILED (no passages)")
            failed += 1

    print(f"\n{'='*60}")
    print(f"Perseus Greek complete: {downloaded} downloaded, {skipped} skipped, {failed} failed")
    print(f"{'='*60}")


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

    total_files = 0
    total_size = 0

    for subdir in sorted(CORPUS_CACHE_DIR.iterdir()):
        if subdir.is_dir():
            files = list(subdir.rglob("*"))
            file_count = sum(1 for f in files if f.is_file())
            dir_size = sum(f.stat().st_size for f in files if f.is_file())
            total_files += file_count
            total_size += dir_size

            # Special handling for Greek to show Tyrrhenian refs
            if subdir.name == "greek":
                tyrr_count = 0
                for json_file in subdir.glob("*.json"):
                    try:
                        with open(json_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        tyrr_count += sum(1 for p in data if p.get("has_tyrrhenian_ref"))
                    except Exception:
                        pass
                print(f"  {subdir.name}: {file_count} files, {dir_size / 1024:.1f} KB ({tyrr_count} Tyrrhenian refs)")
            else:
                print(f"  {subdir.name}: {file_count} files, {dir_size / 1024:.1f} KB")

    print(f"\n  Total: {total_files} files, {total_size / 1024 / 1024:.1f} MB")


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
        description="Download all classical texts from multiple sources",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --all              Download everything
  %(prog)s --latin-library    Download Latin Library texts only
  %(prog)s --greek            Download Greek texts with Etruscan refs
  %(prog)s --priority high    Download high-priority texts only
  %(prog)s --stats            Show download statistics
        """,
    )

    parser.add_argument("--all", "-a", action="store_true", help="Download from all sources")
    parser.add_argument("--latin-library", "-L", action="store_true", help="Download from Latin Library")
    parser.add_argument("--perseus", "-P", action="store_true", help="Download Latin texts from Perseus")
    parser.add_argument("--greek", "-K", action="store_true", help="Download Greek texts from Perseus")
    parser.add_argument("--cltk", "-C", action="store_true", help="Download CLTK corpora")
    parser.add_argument("--github", "-G", action="store_true", help="Clone GitHub repositories")
    parser.add_argument(
        "--priority",
        "-p",
        choices=["high", "medium", "all"],
        default="all",
        help="Priority filter (default: all)",
    )
    parser.add_argument("--force", "-f", action="store_true", help="Force re-download")
    parser.add_argument("--stats", "-s", action="store_true", help="Show download statistics")

    args = parser.parse_args()

    # Ensure corpus directory exists
    CORPUS_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    if args.stats:
        show_stats()
        return

    if not any([args.all, args.latin_library, args.perseus, args.greek, args.cltk, args.github]):
        parser.print_help()
        return

    if args.all or args.latin_library:
        download_latin_library(priority=args.priority, force=args.force)

    if args.all or args.perseus:
        download_perseus_texts(priority=args.priority, force=args.force)

    if args.all or args.greek:
        download_greek_texts(priority=args.priority, force=args.force)

    if args.all or args.cltk:
        download_cltk_corpora()

    if args.all or args.github:
        clone_github_repos(force=args.force)

    show_stats()
    verify_gitignore()


if __name__ == "__main__":
    main()
