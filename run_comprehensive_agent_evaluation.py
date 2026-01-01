"""Run evaluation for comprehensive agent."""

from pathlib import Path
from app.config import get_settings
from eval.run_eval import EvaluationRunner

def main():
    settings = get_settings()
    runner = EvaluationRunner(settings)
    
    print("=" * 70)
    print("COMPREHENSIVE AGENT EVALUATION")
    print("=" * 70)
    
    # PR IDs
    pr_ids = ["14584", "14585", "14586", "14587", "14588", 
              "14589", "14591", "14592", "14593", "14594",
              "20446", "20447", "20448", "20449", "20450", 
              "20451", "20452", "20453", "20454", "20455"]
    
    print(f"\nEvaluating {len(pr_ids)} PRs...")
    print("NOTE: Comprehensive agent has been removed from the system.")
    print("This script is kept for reference only.")

if __name__ == "__main__":
    main()

