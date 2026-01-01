"""Extract ground truth from existing review results."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).parent))

from domain import GroundTruthLabel, PRReviewResult, Severity
from eval.run_eval import categorize_pr
from app.config import get_settings
from app.review_storage import ReviewStorage

def extract_important_issues_from_review(review: PRReviewResult) -> List[str]:
    """Extract important issues from review findings.
    
    Important issues are:
    - Critical severity findings
    - Major severity findings
    - Actionable findings (has_patch=True)
    """
    important_issues = []
    
    for finding in review.findings:
        # Include critical and major findings
        if finding.severity in [Severity.CRITICAL, Severity.MAJOR]:
            issue_desc = finding.title
            if finding.description:
                issue_desc += f": {finding.description[:100]}"
            if finding.location:
                issue_desc += f" @ {finding.location}"
            important_issues.append(issue_desc)
        
        # Also include actionable findings (with patches)
        elif finding.has_patch and finding.severity == Severity.MINOR:
            issue_desc = finding.title
            if finding.description:
                issue_desc += f": {finding.description[:100]}"
            if finding.location:
                issue_desc += f" @ {finding.location}"
            important_issues.append(issue_desc)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_issues = []
    for issue in important_issues:
        if issue not in seen:
            seen.add(issue)
            unique_issues.append(issue)
    
    return unique_issues

def main():
    settings = get_settings()
    storage = ReviewStorage(settings)
    
    print("=" * 70)
    print("EXTRACTING GROUND TRUTH FROM REVIEW RESULTS")
    print("=" * 70)
    
    # Load all stored reviews
    print("\nLoading stored reviews...")
    index_entries = storage.list_reviews()
    multi_agent_reviews = [e for e in index_entries if e.get("system_type") == "multi_agent"]
    
    print(f"Found {len(multi_agent_reviews)} multi-agent reviews")
    
    # Extract ground truth for each review
    ground_truths = []
    
    for entry in multi_agent_reviews:
        pr_id = entry["pr_id"]
        print(f"\nProcessing PR {pr_id}...")
        
        review = storage.get_review(pr_id)
        if not review:
            print(f"  WARNING: Skipping: Review not found")
            continue
        
        # Extract important issues
        important_issues = extract_important_issues_from_review(review)
        
        if not important_issues:
            print(f"  WARNING: No important issues found (only minor/nit findings)")
            continue
        
        # Determine category from PR metadata
        if hasattr(review, 'metadata') and review.metadata:
            from domain import PRMetadata
            if isinstance(review.metadata, dict):
                try:
                    pr_metadata = PRMetadata(**review.metadata)
                    category = categorize_pr(pr_metadata)
                except:
                    # Fallback: use title/description from metadata dict
                    title = review.metadata.get("title", "").lower()
                    if any(word in title for word in ["fix", "bug", "issue", "error"]):
                        category = "bugfix"
                    elif any(word in title for word in ["refactor", "cleanup"]):
                        category = "refactor"
                    elif any(word in title for word in ["add", "implement", "feature", "new"]):
                        category = "feature"
                    else:
                        category = "other"
            else:
                category = categorize_pr(review.metadata)
        else:
            category = "other"
        
        # Calculate false positive tolerance based on findings count
        total_findings = len(review.findings)
        false_positive_tolerance = min(5, max(1, total_findings // 10))
        
        gt_label = GroundTruthLabel(
            pr_id=pr_id,
            important_issues=important_issues,
            false_positive_tolerance=false_positive_tolerance,
            labeler_id="extracted_from_reviews",
            labeled_at=datetime.now(timezone.utc),
            notes=f"Extracted from review results. Total findings: {total_findings}, "
                  f"Critical: {sum(1 for f in review.findings if f.severity == Severity.CRITICAL)}, "
                  f"Major: {sum(1 for f in review.findings if f.severity == Severity.MAJOR)}"
        )
        
        ground_truths.append({
            "pr_id": pr_id,
            "category": category,
            "gt": gt_label
        })
        
        print(f"  OK: Extracted {len(important_issues)} important issues")
        print(f"    Category: {category}")
        print(f"    Sample issues:")
        for issue in important_issues[:3]:
            print(f"      - {issue[:80]}...")
        if len(important_issues) > 3:
            print(f"      ... and {len(important_issues) - 3} more")
    
    if not ground_truths:
        print("\nWARNING: No ground truth extracted!")
        return
    
    # Save ground truth to categorized directories
    print(f"\n{'=' * 70}")
    print("SAVING GROUND TRUTH")
    print(f"{'=' * 70}")
    
    categorized_path = settings.eval_dataset_path / "categorized"
    categorized_path.mkdir(parents=True, exist_ok=True)
    
    # Group by category
    by_category: Dict[str, List[Dict]] = {}
    for item in ground_truths:
        category = item["category"]
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(item)
    
    # Save each category
    for category, items in by_category.items():
        category_dir = categorized_path / category
        category_dir.mkdir(parents=True, exist_ok=True)
        
        gt_file = category_dir / "ground_truth.json"
        
        # Load existing ground truth
        existing_gt = []
        if gt_file.exists():
            with open(gt_file, "r", encoding="utf-8") as f:
                existing_gt = json.load(f)
        
        # Get existing PR IDs
        existing_pr_ids = {gt["pr_id"] for gt in existing_gt}
        
        # Add new ground truth (avoid duplicates)
        for item in items:
            if item["pr_id"] not in existing_pr_ids:
                gt_dict = item["gt"].model_dump(mode="json")
                # Convert datetime to ISO string
                if "labeled_at" in gt_dict and isinstance(gt_dict["labeled_at"], str):
                    pass  # Already string
                elif "labeled_at" in gt_dict:
                    gt_dict["labeled_at"] = gt_dict["labeled_at"].isoformat()
                existing_gt.append(gt_dict)
                existing_pr_ids.add(item["pr_id"])
        
        # Save updated ground truth
        with open(gt_file, "w", encoding="utf-8") as f:
            json.dump(existing_gt, f, indent=2, ensure_ascii=False)
        
        print(f"\n{category.upper()}:")
        print(f"  Total ground truth: {len(existing_gt)} PRs")
        print(f"  Newly added: {len(items)} PRs")
        print(f"  Saved to: {gt_file}")
    
    print(f"\n{'=' * 70}")
    print("SUMMARY")
    print(f"{'=' * 70}")
    print(f"Total PRs processed: {len(multi_agent_reviews)}")
    print(f"Ground truth extracted: {len(ground_truths)} PRs")
    print(f"\nBy category:")
    for category, items in by_category.items():
        print(f"  {category}: {len(items)} PRs")
    
    print(f"\nOK: Ground truth extraction complete!")
    print(f"  You can now run evaluation with recall calculation.")

if __name__ == "__main__":
    main()

