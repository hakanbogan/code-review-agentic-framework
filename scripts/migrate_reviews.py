#!/usr/bin/env python3
"""Migrate existing review files to new storage structure."""

import json
import re
from pathlib import Path
from datetime import datetime
from uuid import uuid4

from app.config import get_settings
from app.review_storage import ReviewStorage
from domain import PRReviewResult, PRMetadata, SystemType, Finding, FindingType, Severity, AgentRole, Evidence


def parse_markdown_review(md_path: Path) -> dict:
    """Parse markdown review file to extract basic info."""
    content = md_path.read_text()

    # Extract PR ID from filename
    pr_id = md_path.parent.name

    # Extract summary
    summary_match = re.search(r'Reviewed PR #(\w+): (.+?)\n', content)
    pr_number = summary_match.group(1) if summary_match else pr_id
    title = summary_match.group(2) if summary_match else "Unknown"

    # Count findings by severity
    findings_count = {
        "critical": len(re.findall(r'## 🔴 Critical Issues', content)),
        "major": len(re.findall(r'## 🟠 Major Issues', content)),
        "minor": len(re.findall(r'## 🟡 Minor Issues', content)),
        "nit": len(re.findall(r'## 💬 Nits', content)),
    }

    # Count total findings
    total_findings = sum(findings_count.values())

    return {
        "pr_id": pr_id,
        "title": title,
        "findings_count": total_findings,
        "findings_by_severity": findings_count,
        "markdown": content,
    }


def create_review_result(parsed: dict) -> PRReviewResult:
    """Create PRReviewResult from parsed data."""
    # Create minimal PR metadata
    pr_metadata = PRMetadata(
        pr_id=parsed["pr_id"],
        repository="unknown",
        branch_source="unknown",
        branch_target="main",
        title=parsed["title"],
        description="",
        author="unknown",
        language="python",
    )

    # Create minimal findings (we don't have full data from markdown)
    findings = []
    for severity_name, count in parsed["findings_by_severity"].items():
        if count > 0:
            severity = Severity(severity_name)
            for i in range(count):
                findings.append(Finding(
                    type=FindingType.OTHER,
                    severity=severity,
                    source_agent=AgentRole.SUPERVISOR,
                    evidence=Evidence(tool="migrated", reference="unknown", snippet=""),
                    title=f"Migrated finding {i+1}",
                    description="Migrated from markdown review",
                    location="unknown",
                ))

    return PRReviewResult(
        correlation_id=uuid4(),
        pr_id=parsed["pr_id"],
        system_type=SystemType.MULTI_AGENT,
        change_summary=f"Migrated review for PR {parsed['pr_id']}",
        findings=findings,
        agent_decisions=[],
        final_comment_md=parsed["markdown"],
        review_time_s=0.0,
        token_cost_estimate=0.0,
        prompt_versions={},
        metadata={
            "repository": "unknown",
            "title": parsed["title"],
            "author": "unknown",
            "migrated": True,
            "migrated_at": datetime.now().isoformat(),
        },
    )


def main():
    """Migrate existing reviews."""
    settings = get_settings()
    storage = ReviewStorage(settings)

    reviews_dir = Path("reviews")
    if not reviews_dir.exists():
        print("No reviews directory found")
        return

    migrated = 0
    for pr_dir in reviews_dir.iterdir():
        if not pr_dir.is_dir():
            continue

        md_path = pr_dir / "review.md"
        if not md_path.exists():
            continue

        try:
            parsed = parse_markdown_review(md_path)
            result = create_review_result(parsed)

            # Save JSON if not exists
            json_path = pr_dir / "review.json"
            if not json_path.exists():
                json_path.write_text(json.dumps(result.model_dump(mode="json"), indent=2))

            # Update index
            storage._update_index(result)
            migrated += 1
            print(f"Migrated: {parsed['pr_id']}")
        except Exception as e:
            print(f"Error migrating {pr_dir.name}: {e}")

    print(f"\nMigrated {migrated} reviews")


if __name__ == "__main__":
    main()
