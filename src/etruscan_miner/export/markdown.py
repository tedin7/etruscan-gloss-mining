"""Export results to Markdown format."""

from datetime import datetime
from pathlib import Path
from typing import Optional

from ..db.models import Candidate, VerifiedGloss
from ..db.repository import Repository


class MarkdownExporter:
    """Export mining results to Markdown files."""

    def __init__(self, repo: Repository):
        """Initialize exporter.

        Args:
            repo: Database repository
        """
        self.repo = repo

    def _format_date(self) -> str:
        """Get formatted date string."""
        return datetime.now().strftime("%Y-%m-%d")

    def export_verified_glosses(self, output_path: Path) -> int:
        """Export verified glosses to Markdown.

        Args:
            output_path: Path to output file

        Returns:
            Number of glosses exported
        """
        glosses = self.repo.get_all_verified_glosses()

        lines = [
            f"# Verified Etruscan Glosses",
            f"**Generated:** {self._format_date()}",
            f"**Total:** {len(glosses)} glosses",
            "",
            "---",
            "",
        ]

        # Group by reliability
        by_reliability: dict[int, list[VerifiedGloss]] = {}
        for g in glosses:
            rel = g.reliability or 3
            if rel not in by_reliability:
                by_reliability[rel] = []
            by_reliability[rel].append(g)

        for rel in sorted(by_reliability.keys(), reverse=True):
            stars = "⭐" * rel
            lines.append(f"## Reliability {rel}/5 {stars}")
            lines.append("")

            for gloss in sorted(by_reliability[rel], key=lambda x: x.etruscan_word.lower()):
                lines.append(f"### {gloss.etruscan_word}")
                lines.append(f"**Meaning:** {gloss.meaning}")
                if gloss.source_author:
                    lines.append(f"**Source:** {gloss.source_author}")
                if gloss.source_work:
                    lines.append(f"**Work:** {gloss.source_work}")
                if gloss.source_quote:
                    lines.append(f"**Quote:** \"{gloss.source_quote}\"")
                if gloss.notes:
                    lines.append(f"**Notes:** {gloss.notes}")
                lines.append("")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return len(glosses)

    def export_candidates(
        self,
        output_path: Path,
        status: Optional[str] = None,
        min_confidence: float = 0.0,
    ) -> int:
        """Export candidates to Markdown.

        Args:
            output_path: Path to output file
            status: Filter by status (pending, reviewing, accepted, rejected)
            min_confidence: Minimum pattern confidence

        Returns:
            Number of candidates exported
        """
        if status:
            candidates = self.repo.get_candidates_by_status(status)
        else:
            # Get all candidates
            candidates = []
            for s in ["accepted", "reviewing", "pending", "rejected"]:
                candidates.extend(self.repo.get_candidates_by_status(s))

        # Filter by confidence
        candidates = [c for c in candidates if (c.pattern_confidence or 0) >= min_confidence]

        lines = [
            f"# Mining Candidates",
            f"**Generated:** {self._format_date()}",
            f"**Total:** {len(candidates)} candidates",
            f"**Status Filter:** {status or 'all'}",
            f"**Min Confidence:** {min_confidence}",
            "",
            "---",
            "",
        ]

        # Group by status
        by_status: dict[str, list[Candidate]] = {}
        for c in candidates:
            s = c.status or "unknown"
            if s not in by_status:
                by_status[s] = []
            by_status[s].append(c)

        status_order = ["accepted", "reviewing", "pending", "rejected"]
        for s in status_order:
            if s not in by_status:
                continue

            lines.append(f"## {s.upper()} ({len(by_status[s])})")
            lines.append("")

            # Sort by confidence descending
            sorted_candidates = sorted(
                by_status[s],
                key=lambda x: x.pattern_confidence or 0,
                reverse=True,
            )

            for c in sorted_candidates:
                conf = c.pattern_confidence or 0
                lines.append(f"### {c.etruscan_word} (confidence: {conf:.2f})")
                lines.append(f"**Pattern Match:** `{c.full_match}`")
                if c.meaning_proposed:
                    lines.append(f"**Proposed Meaning:** {c.meaning_proposed}")
                lines.append(f"**Context:**")
                lines.append(f"> ...{c.context_before} **[{c.full_match}]** {c.context_after}...")
                if c.reviewer_notes:
                    lines.append(f"**Notes:** {c.reviewer_notes}")
                lines.append("")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return len(candidates)

    def export_findings_report(self, output_path: Path) -> None:
        """Export a comprehensive findings report.

        Args:
            output_path: Path to output file
        """
        stats = self.repo.get_stats()
        glosses = self.repo.get_all_verified_glosses()
        accepted = self.repo.get_candidates_by_status("accepted")
        reviewing = self.repo.get_candidates_by_status("reviewing")

        lines = [
            f"# Etruscan Gloss Mining - Findings Report",
            f"**Generated:** {self._format_date()}",
            "",
            "---",
            "",
            "## Executive Summary",
            "",
            f"This report summarizes the results of computational mining for Etruscan",
            f"glosses in ancient Latin and Greek texts.",
            "",
            "### Statistics",
            "",
            f"| Metric | Count |",
            f"|--------|-------|",
            f"| Verified Glosses (seed data) | {stats['verified_glosses']} |",
            f"| Known Vocabulary | {stats['etruscan_vocabulary']} |",
            f"| Mining Patterns | {stats['patterns']} |",
            f"| Total Candidates | {stats['candidates']} |",
            f"| Accepted Candidates | {len(accepted)} |",
            f"| Under Review | {len(reviewing)} |",
            "",
            "---",
            "",
            "## New Discoveries",
            "",
        ]

        if accepted:
            lines.append("### High-Confidence Candidates")
            lines.append("")
            lines.append("| Word | Confidence | Context |")
            lines.append("|------|------------|---------|")

            for c in sorted(accepted, key=lambda x: x.pattern_confidence or 0, reverse=True)[:20]:
                conf = c.pattern_confidence or 0
                ctx = f"{c.context_before[:30]}...{c.context_after[:30]}" if c.context_before else ""
                lines.append(f"| **{c.etruscan_word}** | {conf:.2f} | {ctx} |")

            lines.append("")

        if reviewing:
            lines.append("### Candidates Under Review")
            lines.append("")
            lines.append("The following candidates require expert review:")
            lines.append("")

            for c in reviewing[:10]:
                lines.append(f"- **{c.etruscan_word}**: `{c.full_match}`")

            lines.append("")

        lines.extend([
            "---",
            "",
            "## Methodology",
            "",
            "### Pattern Matching",
            "",
            "Latin texts were searched for phrases indicating Etruscan vocabulary:",
            "",
            "- `Tusci vocant X` - The Etruscans call X",
            "- `Etrusca lingua X` - In Etruscan language, X",
            "- `Etrusco vocabulo X` - With Etruscan word X",
            "- And 20+ additional patterns",
            "",
            "### Validation Pipeline",
            "",
            "Each candidate was scored on:",
            "",
            "1. **Pattern Confidence** (30%) - Match quality",
            "2. **Cross-Reference** (30%) - Known vocabulary match",
            "3. **Linguistic Plausibility** (20%) - Etruscan phonotactics",
            "4. **Contextual Coherence** (20%) - Meaning indicators",
            "",
            "---",
            "",
            "## References",
            "",
            "- Perseus Digital Library",
            "- Bonfante & Bonfante, *The Etruscan Language*",
            "- Rix, *Etruskische Texte*",
            "",
            "---",
            "",
            "*Report generated by Etruscan Gloss Miner*",
        ])

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
