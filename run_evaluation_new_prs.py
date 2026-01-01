"""Run evaluation for new PRs with optimized system."""

from pathlib import Path
from app.config import get_settings
from eval.run_eval import EvaluationRunner
from domain import SystemType

def main():
    settings = get_settings()
    runner = EvaluationRunner(settings)
    
    # New PR IDs (10 Django + 10 FastAPI)
    new_prs = ["20446", "20447", "20448", "20449", "20450", 
               "20451", "20452", "20453", "20454", "20455",
               "14584", "14585", "14586", "14587", "14588", 
               "14589", "14591", "14592", "14593", "14594"]
    
    print("=" * 70)
    print("NEW PR EVALUATION (OPTIMIZED SYSTEM)")
    print("=" * 70)
    print(f"Evaluating {len(new_prs)} new PRs...")
    
    result = runner.run_evaluation(
        system_type=SystemType.MULTI_AGENT,
        use_stored_reviews=True,
        pr_ids=new_prs,
        aggregate=True
    )
    
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"Actionability Rate: {result.actionability_rate:.2%}")
    print(f"Noise Rate: {result.noise_rate:.2%}")
    print(f"Important Issue Coverage: {result.important_issue_coverage:.2%}")
    print(f"Precision: {result.metadata.get('precision', 0):.2%}")
    print(f"Recall: {result.metadata.get('recall', 0):.2%}")
    print(f"F1-Score: {result.metadata.get('f1_score', 0):.2%}")

if __name__ == "__main__":
    main()

