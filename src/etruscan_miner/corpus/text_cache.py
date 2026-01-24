"""Text caching for downloaded corpus texts.

Caches texts locally to avoid repeated API calls.
Supports expiry and invalidation.
"""

import hashlib
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

from ..config import CACHE_EXPIRY_DAYS, PERSEUS_CACHE_DIR
from .perseus import TextPassage


@dataclass
class CacheEntry:
    """A cached text entry."""

    urn: str
    text: str
    reference: str
    language: str
    source_url: Optional[str]
    cached_at: float
    expires_at: float


class TextCache:
    """Local file cache for downloaded texts."""

    def __init__(
        self,
        cache_dir: Path = PERSEUS_CACHE_DIR,
        expiry_days: int = CACHE_EXPIRY_DAYS,
    ):
        """Initialize text cache.

        Args:
            cache_dir: Directory to store cached texts
            expiry_days: Number of days before cache expires
        """
        self.cache_dir = cache_dir
        self.expiry_seconds = expiry_days * 24 * 60 * 60
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Index file for quick lookups
        self.index_path = cache_dir / "index.json"
        self._index: dict[str, str] = {}  # URN -> filename mapping
        self._load_index()

    def _load_index(self):
        """Load the cache index from disk."""
        if self.index_path.exists():
            try:
                with open(self.index_path) as f:
                    self._index = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._index = {}

    def _save_index(self):
        """Save the cache index to disk."""
        with open(self.index_path, "w") as f:
            json.dump(self._index, f, indent=2)

    def _urn_to_filename(self, urn: str) -> str:
        """Convert URN to a safe filename.

        Args:
            urn: Text URN

        Returns:
            Safe filename for cache storage
        """
        # Create a hash for long URNs
        urn_hash = hashlib.md5(urn.encode()).hexdigest()[:12]
        # Also include a readable prefix
        safe_urn = urn.replace(":", "_").replace("/", "_")[:50]
        return f"{safe_urn}_{urn_hash}.json"

    def get(self, urn: str) -> Optional[TextPassage]:
        """Get a cached text passage.

        Args:
            urn: Text URN

        Returns:
            TextPassage if cached and not expired, None otherwise
        """
        if urn not in self._index:
            return None

        filename = self._index[urn]
        cache_path = self.cache_dir / filename

        if not cache_path.exists():
            # Remove stale index entry
            del self._index[urn]
            self._save_index()
            return None

        try:
            with open(cache_path) as f:
                data = json.load(f)
                entry = CacheEntry(**data)

                # Check expiry
                if time.time() > entry.expires_at:
                    self.invalidate(urn)
                    return None

                return TextPassage(
                    urn=entry.urn,
                    reference=entry.reference,
                    text=entry.text,
                    language=entry.language,
                    source_url=entry.source_url,
                )
        except (json.JSONDecodeError, IOError, TypeError) as e:
            print(f"Cache read error for {urn}: {e}")
            return None

    def put(self, passage: TextPassage):
        """Cache a text passage.

        Args:
            passage: TextPassage to cache
        """
        now = time.time()
        entry = CacheEntry(
            urn=passage.urn,
            text=passage.text,
            reference=passage.reference,
            language=passage.language,
            source_url=passage.source_url,
            cached_at=now,
            expires_at=now + self.expiry_seconds,
        )

        filename = self._urn_to_filename(passage.urn)
        cache_path = self.cache_dir / filename

        with open(cache_path, "w") as f:
            json.dump(asdict(entry), f, indent=2)

        self._index[passage.urn] = filename
        self._save_index()

    def put_many(self, passages: list[TextPassage]):
        """Cache multiple passages.

        Args:
            passages: List of TextPassage objects
        """
        for passage in passages:
            self.put(passage)

    def invalidate(self, urn: str):
        """Remove a cached entry.

        Args:
            urn: URN to invalidate
        """
        if urn in self._index:
            filename = self._index[urn]
            cache_path = self.cache_dir / filename
            if cache_path.exists():
                cache_path.unlink()
            del self._index[urn]
            self._save_index()

    def clear(self):
        """Clear all cached entries."""
        for filename in self._index.values():
            cache_path = self.cache_dir / filename
            if cache_path.exists():
                cache_path.unlink()
        self._index = {}
        self._save_index()

    def get_stats(self) -> dict:
        """Get cache statistics.

        Returns:
            Dict with cache stats
        """
        total_entries = len(self._index)
        total_size = sum(
            (self.cache_dir / f).stat().st_size
            for f in self._index.values()
            if (self.cache_dir / f).exists()
        )

        return {
            "entries": total_entries,
            "size_bytes": total_size,
            "size_mb": total_size / (1024 * 1024),
            "cache_dir": str(self.cache_dir),
        }

    def list_cached_urns(self) -> list[str]:
        """List all cached URNs.

        Returns:
            List of cached URNs
        """
        return list(self._index.keys())


class WorkCache:
    """Higher-level cache for complete works."""

    def __init__(self, cache_dir: Path = PERSEUS_CACHE_DIR):
        """Initialize work cache.

        Args:
            cache_dir: Base cache directory
        """
        self.cache_dir = cache_dir / "works"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _work_urn_to_filename(self, urn: str) -> str:
        """Convert work URN to filename."""
        safe = urn.replace(":", "_").replace("/", "_")
        return f"{safe}.json"

    def get_work(self, urn: str) -> Optional[list[TextPassage]]:
        """Get a complete cached work.

        Args:
            urn: Work URN

        Returns:
            List of passages if cached, None otherwise
        """
        filename = self._work_urn_to_filename(urn)
        cache_path = self.cache_dir / filename

        if not cache_path.exists():
            return None

        try:
            with open(cache_path) as f:
                data = json.load(f)

            return [
                TextPassage(
                    urn=p["urn"],
                    reference=p["reference"],
                    text=p["text"],
                    language=p.get("language", "lat"),
                    source_url=p.get("source_url"),
                )
                for p in data["passages"]
            ]
        except (json.JSONDecodeError, IOError, KeyError) as e:
            print(f"Work cache read error: {e}")
            return None

    def put_work(self, urn: str, passages: list[TextPassage]):
        """Cache a complete work.

        Args:
            urn: Work URN
            passages: All passages in the work
        """
        filename = self._work_urn_to_filename(urn)
        cache_path = self.cache_dir / filename

        data = {
            "urn": urn,
            "cached_at": time.time(),
            "passage_count": len(passages),
            "passages": [
                {
                    "urn": p.urn,
                    "reference": p.reference,
                    "text": p.text,
                    "language": p.language,
                    "source_url": p.source_url,
                }
                for p in passages
            ],
        }

        with open(cache_path, "w") as f:
            json.dump(data, f, indent=2)

    def list_works(self) -> list[str]:
        """List all cached work URNs."""
        works = []
        for path in self.cache_dir.glob("*.json"):
            try:
                with open(path) as f:
                    data = json.load(f)
                    works.append(data.get("urn", path.stem))
            except (json.JSONDecodeError, IOError):
                continue
        return works
