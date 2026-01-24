#!/usr/bin/env python3
"""Download and cache corpus texts from Perseus Digital Library."""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from etruscan_miner.config import TARGET_WORKS
from etruscan_miner.corpus.perseus import PerseusClient
from etruscan_miner.corpus.text_cache import WorkCache


def download_work(work_key: str, client: PerseusClient, cache: WorkCache, force: bool = False):
    """Download a specific work.

    Args:
        work_key: Key from TARGET_WORKS
        client: Perseus client
        cache: Work cache
        force: Force re-download even if cached
    """
    if work_key not in TARGET_WORKS:
        print(f"Unknown work: {work_key}")
        print(f"Available works: {', '.join(TARGET_WORKS.keys())}")
        return

    work = TARGET_WORKS[work_key]
    urn = work.get("urn")

    if not urn:
        print(f"Work {work_key} has no Perseus URN - needs special handling")
        return

    print(f"\n{'='*60}")
    print(f"Work: {work['title']} by {work['author']}")
    print(f"URN: {urn}")
    print(f"Priority: {work['priority']}")
    print(f"{'='*60}")

    # Check cache
    if not force:
        cached = cache.get_work(urn)
        if cached:
            print(f"Found in cache: {len(cached)} passages")
            return

    # Download
    print("Downloading from Perseus...")
    passages = client.get_work_text(urn)

    if passages:
        cache.put_work(urn, passages)
        print(f"Downloaded and cached: {len(passages)} passages")

        # Show sample
        if passages:
            print("\nSample passage:")
            print(f"  Reference: {passages[0].reference}")
            print(f"  Text: {passages[0].text[:200]}...")
    else:
        print("No passages retrieved - check URN and network connection")


def list_works():
    """List available and cached works."""
    cache = WorkCache()
    cached = cache.list_works()

    print("\nTarget works for mining:")
    print("-" * 60)
    for key, work in TARGET_WORKS.items():
        status = "[CACHED]" if work.get("urn") in cached else ""
        urn_status = work.get("urn") or "(no URN)"
        print(f"  {key}")
        print(f"    {work['author']}: {work['title']}")
        print(f"    URN: {urn_status} {status}")
        print(f"    Priority: {work['priority']}")
        print()


def main():
    parser = argparse.ArgumentParser(description="Download corpus texts from Perseus")
    parser.add_argument(
        "--work",
        "-w",
        help="Work to download (from TARGET_WORKS)",
    )
    parser.add_argument(
        "--all",
        "-a",
        action="store_true",
        help="Download all works with URNs",
    )
    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="List available works",
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force re-download even if cached",
    )
    parser.add_argument(
        "--priority",
        "-p",
        choices=["HIGH", "MEDIUM", "LOW"],
        help="Download all works of specified priority",
    )

    args = parser.parse_args()

    if args.list:
        list_works()
        return

    client = PerseusClient()
    cache = WorkCache()

    if args.work:
        download_work(args.work, client, cache, args.force)

    elif args.all or args.priority:
        for key, work in TARGET_WORKS.items():
            if args.priority and work["priority"] != args.priority:
                continue
            if work.get("urn"):
                download_work(key, client, cache, args.force)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
