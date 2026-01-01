"""Find correct optimized system results from evaluation files."""

import json
from pathlib import Path
from app.config import get_settings

def main():
    settings = get_settings()
    results_dir = settings.eval_results_path
    
    print("=" * 70)
    print("SEARCHING FOR OPTIMIZED SYSTEM RESULTS")
    print("=" * 70)
    
    # Search all aggregated files
    aggregated_files = list(results_dir.glob("evaluation_*_aggregated_*.json"))
    
    print(f"\nFound {len(aggregated_files)} aggregated evaluation files:")
    
    for file_path in sorted(aggregated_files):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            system_type = data.get("system_type", "unknown")
            dataset_size = data.get("dataset_size", 0)
            actionability = data.get("actionability_rate", 0)
            precision = data.get("metadata", {}).get("precision", 0)
            pr_ids = data.get("pr_ids", [])
            
            # Check if this looks like optimized results (high actionability, 20 PRs)
            if actionability > 0.9 and dataset_size == 20:
                print(f"\n{'=' * 70}")
                print(f"POTENTIAL OPTIMIZED RESULTS: {file_path.name}")
                print(f"{'=' * 70}")
                print(f"System Type: {system_type}")
                print(f"Dataset Size: {dataset_size}")
                print(f"Actionability Rate: {actionability:.2%}")
                print(f"Precision: {precision:.2%}")
                print(f"PR IDs: {pr_ids[:5]}... ({len(pr_ids)} total)")
                print(f"File: {file_path}")
            
            # Also show all files with high actionability
            elif actionability > 0.5:
                print(f"\n{file_path.name}:")
                print(f"  System: {system_type}, Size: {dataset_size}, Actionability: {actionability:.2%}, Precision: {precision:.2%}")
                
        except Exception as e:
            print(f"Error reading {file_path.name}: {e}")
    
    print("\n" + "=" * 70)
    print("RECOMMENDED FILES FOR OPTIMIZED RESULTS:")
    print("=" * 70)
    print("Based on OPTIMIZED_SYSTEM_RESULTS.md:")
    print("  - Actionability: 97.14%")
    print("  - Precision: 97.14%")
    print("  - F1-Score: 98.55%")
    print("  - 20 PRs (10 Django + 10 FastAPI)")
    print("\nIf no file matches, the results may need to be recalculated.")

if __name__ == "__main__":
    main()

