"""Calculate chi-square statistics for comparing systems."""

import json
from pathlib import Path
from typing import Dict, Any
from eval.metrics.statistical import proportion_test

def load_evaluation_result(file_path: Path) -> Dict[str, Any]:
    """Load evaluation result from JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def calculate_actionability_test(baseline: Dict, optimized: Dict) -> Dict[str, Any]:
    """Calculate chi-square test for actionability rates."""
    baseline_actionable = baseline.get("metadata", {}).get("actionable_findings", 0)
    baseline_total = baseline.get("metadata", {}).get("total_findings", 0)
    
    optimized_actionable = optimized.get("metadata", {}).get("actionable_findings", 0)
    optimized_total = optimized.get("metadata", {}).get("total_findings", 0)
    
    return proportion_test(
        successes_a=optimized_actionable,
        total_a=optimized_total,
        successes_b=baseline_actionable,
        total_b=baseline_total,
    )

def calculate_precision_test(baseline: Dict, optimized: Dict) -> Dict[str, Any]:
    """Calculate chi-square test for precision."""
    baseline_precision = baseline.get("metadata", {}).get("precision", 0)
    baseline_total = baseline.get("metadata", {}).get("total_findings", 0)
    baseline_actionable = int(baseline_precision * baseline_total) if baseline_total > 0 else 0
    
    optimized_precision = optimized.get("metadata", {}).get("precision", 0)
    optimized_total = optimized.get("metadata", {}).get("total_findings", 0)
    optimized_actionable = int(optimized_precision * optimized_total) if optimized_total > 0 else 0
    
    return proportion_test(
        successes_a=optimized_actionable,
        total_a=optimized_total,
        successes_b=baseline_actionable,
        total_b=baseline_total,
    )

def main():
    import typer
    
    app = typer.Typer()
    
    @app.command()
    def compare(
        baseline_file: Path = typer.Argument(..., help="Baseline evaluation JSON"),
        optimized_file: Path = typer.Argument(..., help="Optimized evaluation JSON"),
    ):
        """Compare baseline and optimized systems using chi-square tests."""
        print("=" * 70)
        print("CHI-SQUARE STATISTICAL TEST")
        print("=" * 70)
        
        baseline = load_evaluation_result(baseline_file)
        optimized = load_evaluation_result(optimized_file)
        
        # Actionability test
        print("\n1. Actionability Rate Test:")
        actionability_test = calculate_actionability_test(baseline, optimized)
        print(f"   Chi-square: {actionability_test['chi2']:.4f}")
        print(f"   p-value: {actionability_test['p_value']:.4f}")
        print(f"   Significant: {actionability_test['significant']}")
        
        # Precision test
        print("\n2. Precision Test:")
        precision_test = calculate_precision_test(baseline, optimized)
        print(f"   Chi-square: {precision_test['chi2']:.4f}")
        print(f"   p-value: {precision_test['p_value']:.4f}")
        print(f"   Significant: {precision_test['significant']}")
        
        # Summary
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        baseline_actionability = baseline.get("actionability_rate", 0)
        optimized_actionability = optimized.get("actionability_rate", 0)
        print(f"Baseline Actionability: {baseline_actionability:.2%}")
        print(f"Optimized Actionability: {optimized_actionability:.2%}")
        print(f"Improvement: {(optimized_actionability - baseline_actionability):.2%}")
    
    app()

if __name__ == "__main__":
    main()

