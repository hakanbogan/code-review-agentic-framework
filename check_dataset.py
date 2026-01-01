"""Check dataset status."""

from pathlib import Path
from app.config import get_settings
from eval.run_eval import DatasetLoader

def main():
    settings = get_settings()
    dataset_loader = DatasetLoader(settings.eval_dataset_path)
    
    print("=" * 70)
    print("DATASET STATUS CHECK")
    print("=" * 70)
    
    # Load PR list
    print("\nLoading PR list...")
    pr_list = dataset_loader.load_pr_list()
    print(f"Total PRs in dataset: {len(pr_list)}")
    
    # Load ground truth
    print("\nLoading ground truth...")
    ground_truth = dataset_loader.load_ground_truth()
    print(f"Total ground truth entries: {len(ground_truth)}")
    
    # Load benchmarks
    print("\nLoading benchmarks...")
    benchmarks = dataset_loader.load_category_benchmarks()
    if benchmarks:
        print(f"Benchmark categories: {', '.join(benchmarks.keys())}")
    else:
        print("No benchmarks found")
    
    # Category breakdown
    if pr_list:
        from eval.run_eval import categorize_pr
        categories = {}
        for pr in pr_list:
            cat = categorize_pr(pr)
            categories[cat] = categories.get(cat, 0) + 1
        
        print("\nPRs by category:")
        for cat, count in sorted(categories.items()):
            print(f"  {cat}: {count}")

if __name__ == "__main__":
    main()

