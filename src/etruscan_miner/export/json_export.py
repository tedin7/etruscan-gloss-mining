"""Export results to JSON format."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from ..db.models import Candidate, VerifiedGloss
from ..db.repository import Repository


class JSONExporter:
    """Export mining results to JSON files."""

    def __init__(self, repo: Repository):
        """Initialize exporter.

        Args:
            repo: Database repository
        """
        self.repo = repo

    def _to_dict(self, obj: Any) -> dict:
        """Convert dataclass to dict, handling None values."""
        if hasattr(obj, "__dataclass_fields__"):
            return {
                k: v for k, v in obj.__dict__.items()
                if v is not None and not k.startswith("_")
            }
        return obj

    def export_verified_glosses(self, output_path: Path) -> int:
        """Export verified glosses to JSON.

        Args:
            output_path: Path to output file

        Returns:
            Number of glosses exported
        """
        glosses = self.repo.get_all_verified_glosses()

        data = {
            "metadata": {
                "type": "verified_glosses",
                "generated": datetime.now().isoformat(),
                "count": len(glosses),
            },
            "glosses": [self._to_dict(g) for g in glosses],
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return len(glosses)

    def export_vocabulary(self, output_path: Path) -> int:
        """Export vocabulary to JSON.

        Args:
            output_path: Path to output file

        Returns:
            Number of words exported
        """
        vocab = self.repo.get_all_vocabulary()

        data = {
            "metadata": {
                "type": "etruscan_vocabulary",
                "generated": datetime.now().isoformat(),
                "count": len(vocab),
            },
            "vocabulary": [self._to_dict(v) for v in vocab],
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return len(vocab)

    def export_candidates(
        self,
        output_path: Path,
        status: Optional[str] = None,
        min_confidence: float = 0.0,
        include_validations: bool = False,
    ) -> int:
        """Export candidates to JSON.

        Args:
            output_path: Path to output file
            status: Filter by status
            min_confidence: Minimum pattern confidence
            include_validations: Include validation scores

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

        candidate_data = []
        for c in candidates:
            c_dict = self._to_dict(c)

            if include_validations and c.id:
                validations = self.repo.get_validations_for_candidate(c.id)
                c_dict["validations"] = {
                    v.validation_type: {
                        "score": v.score,
                        "weight": v.weight,
                        "details": json.loads(v.details) if v.details else None,
                    }
                    for v in validations
                }

            candidate_data.append(c_dict)

        data = {
            "metadata": {
                "type": "mining_candidates",
                "generated": datetime.now().isoformat(),
                "count": len(candidates),
                "filters": {
                    "status": status,
                    "min_confidence": min_confidence,
                },
            },
            "candidates": candidate_data,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return len(candidates)

    def export_complete_database(self, output_path: Path) -> dict[str, int]:
        """Export complete database to a single JSON file.

        Args:
            output_path: Path to output file

        Returns:
            Dict of section -> count
        """
        glosses = self.repo.get_all_verified_glosses()
        vocab = self.repo.get_all_vocabulary()
        patterns = self.repo.get_active_patterns()
        stats = self.repo.get_stats()

        # Get all candidates
        candidates = []
        for status in ["accepted", "reviewing", "pending", "rejected"]:
            candidates.extend(self.repo.get_candidates_by_status(status))

        data = {
            "metadata": {
                "type": "etruscan_gloss_mining_database",
                "generated": datetime.now().isoformat(),
                "statistics": stats,
            },
            "verified_glosses": [self._to_dict(g) for g in glosses],
            "vocabulary": [self._to_dict(v) for v in vocab],
            "patterns": [self._to_dict(p) for p in patterns],
            "candidates": [self._to_dict(c) for c in candidates],
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return {
            "verified_glosses": len(glosses),
            "vocabulary": len(vocab),
            "patterns": len(patterns),
            "candidates": len(candidates),
        }

    def export_for_web(self, output_path: Path) -> int:
        """Export data optimized for web visualization.

        Args:
            output_path: Path to output file

        Returns:
            Total items exported
        """
        glosses = self.repo.get_all_verified_glosses()
        vocab = self.repo.get_all_vocabulary()
        accepted = self.repo.get_candidates_by_status("accepted")

        # Create simplified structure for web
        data = {
            "generated": datetime.now().isoformat(),
            "glosses": [
                {
                    "word": g.etruscan_word,
                    "meaning": g.meaning,
                    "source": g.source_author,
                    "reliability": g.reliability,
                }
                for g in glosses
            ],
            "discoveries": [
                {
                    "word": c.etruscan_word,
                    "context": c.full_match,
                    "confidence": c.pattern_confidence,
                }
                for c in accepted
            ],
            "vocabulary_count": len(vocab),
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return len(glosses) + len(accepted)
