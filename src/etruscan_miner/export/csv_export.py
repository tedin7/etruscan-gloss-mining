"""Export results to CSV format."""

import csv
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..db.models import Candidate, VerifiedGloss
from ..db.repository import Repository


class CSVExporter:
    """Export mining results to CSV files."""

    def __init__(self, repo: Repository):
        """Initialize exporter.

        Args:
            repo: Database repository
        """
        self.repo = repo

    def export_verified_glosses(self, output_path: Path) -> int:
        """Export verified glosses to CSV.

        Args:
            output_path: Path to output file

        Returns:
            Number of glosses exported
        """
        glosses = self.repo.get_all_verified_glosses()

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "id",
                "etruscan_word",
                "meaning",
                "source_author",
                "source_work",
                "source_citation",
                "source_quote",
                "reliability",
                "is_seed",
                "notes",
            ])

            for g in glosses:
                writer.writerow([
                    g.id,
                    g.etruscan_word,
                    g.meaning,
                    g.source_author or "",
                    g.source_work or "",
                    g.source_citation or "",
                    g.source_quote or "",
                    g.reliability,
                    g.is_seed,
                    g.notes or "",
                ])

        return len(glosses)

    def export_vocabulary(self, output_path: Path) -> int:
        """Export vocabulary to CSV.

        Args:
            output_path: Path to output file

        Returns:
            Number of words exported
        """
        vocab = self.repo.get_all_vocabulary()

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "id",
                "word",
                "word_normalized",
                "meaning",
                "meaning_uncertain",
                "category",
                "source",
                "reliability",
                "notes",
            ])

            for v in vocab:
                writer.writerow([
                    v.id,
                    v.word,
                    v.word_normalized,
                    v.meaning or "",
                    v.meaning_uncertain,
                    v.category,
                    v.source or "",
                    v.reliability,
                    v.notes or "",
                ])

        return len(vocab)

    def export_candidates(
        self,
        output_path: Path,
        status: Optional[str] = None,
        min_confidence: float = 0.0,
    ) -> int:
        """Export candidates to CSV.

        Args:
            output_path: Path to output file
            status: Filter by status
            min_confidence: Minimum pattern confidence

        Returns:
            Number of candidates exported
        """
        if status:
            candidates = self.repo.get_candidates_by_status(status)
        else:
            candidates = []
            for s in ["accepted", "reviewing", "pending", "rejected"]:
                candidates.extend(self.repo.get_candidates_by_status(s))

        candidates = [c for c in candidates if (c.pattern_confidence or 0) >= min_confidence]

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "id",
                "etruscan_word",
                "etruscan_normalized",
                "meaning_proposed",
                "full_match",
                "context_before",
                "context_after",
                "pattern_confidence",
                "overall_score",
                "status",
                "reviewer_notes",
            ])

            for c in candidates:
                writer.writerow([
                    c.id,
                    c.etruscan_word,
                    c.etruscan_normalized,
                    c.meaning_proposed or "",
                    c.full_match or "",
                    c.context_before or "",
                    c.context_after or "",
                    c.pattern_confidence or "",
                    c.overall_score or "",
                    c.status,
                    c.reviewer_notes or "",
                ])

        return len(candidates)

    def export_all(self, output_dir: Path) -> dict[str, int]:
        """Export all data to CSV files.

        Args:
            output_dir: Directory to write files

        Returns:
            Dict of filename -> count
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d")

        results = {}

        # Export glosses
        path = output_dir / f"verified_glosses_{timestamp}.csv"
        results[path.name] = self.export_verified_glosses(path)

        # Export vocabulary
        path = output_dir / f"vocabulary_{timestamp}.csv"
        results[path.name] = self.export_vocabulary(path)

        # Export candidates by status
        for status in ["accepted", "reviewing", "pending"]:
            path = output_dir / f"candidates_{status}_{timestamp}.csv"
            results[path.name] = self.export_candidates(path, status=status)

        return results
