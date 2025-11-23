"""Command-line interface for code review framework."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from app.config import get_settings
from app.logging import setup_logging
from domain import PRMetadata, SystemType
from eval import ComparisonAnalyzer, EvaluationRunner
from flows import ReviewFlow

app = typer.Typer(
    name="code-review",
    help="Multi-agent code review framework",
    add_completion=False,
)

console = Console()


@app.callback()
def callback():
    """Initialize logging and configuration."""
    setup_logging()


@app.command()
def review(
    repo_path: Path = typer.Argument(..., help="Path to repository"),
    pr_id: str = typer.Option(..., "--pr-id", help="PR identifier"),
    title: str = typer.Option(..., "--title", help="PR title"),
    description: str = typer.Option("", "--description", help="PR description"),
    language: str = typer.Option("python", "--language", help="Primary language"),
    multi_agent: bool = typer.Option(True, "--multi-agent/--single-agent", help="Use multi-agent system"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """Run code review on a repository."""
    settings = get_settings()
    
    console.print(f"[bold]Starting review for PR {pr_id}[/bold]")
    
    # Create PR metadata
    pr_metadata = PRMetadata(
        pr_id=pr_id,
        repository=repo_path.name,
        branch_source="feature",
        branch_target="main",
        title=title,
        description=description,
        author="unknown",
        language=language,
    )
    
    # Run review
    flow = ReviewFlow(settings)
    
    try:
        if multi_agent:
            console.print("[cyan]Running multi-agent review...[/cyan]")
            result = flow.run_multi_agent_review(pr_metadata, repo_path)
        else:
            console.print("[cyan]Running single-agent review...[/cyan]")
            result = flow.run_single_agent_review(pr_metadata, repo_path)
        
        # Display results
        _display_review_result(result)
        
        # Save output if requested
        if output:
            import json
            output.write_text(json.dumps(result.model_dump(mode="json"), indent=2))
            console.print(f"[green]Results saved to {output}[/green]")
        
        # Save markdown comment
        comment_path = Path(f"review_{pr_id}.md")
        comment_path.write_text(result.final_comment_md)
        console.print(f"[green]Review comment saved to {comment_path}[/green]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def evaluate(
    repo_path: Path = typer.Argument(..., help="Path to repository"),
    system: SystemType = typer.Option(SystemType.MULTI_AGENT, "--system", help="System type to evaluate"),
):
    """Run evaluation on dataset."""
    settings = get_settings()
    
    console.print(f"[bold]Running evaluation for {system.value}[/bold]")
    
    runner = EvaluationRunner(settings)
    
    try:
        result = runner.run_evaluation(system, repo_path)
        
        # Display results
        _display_evaluation_result(result)
        
        console.print(f"[green]Evaluation complete. Results saved to {settings.eval_results_path}[/green]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def compare(
    baseline_file: Path = typer.Argument(..., help="Baseline evaluation results (JSON)"),
    proposed_file: Path = typer.Argument(..., help="Proposed evaluation results (JSON)"),
    latex_output: Optional[Path] = typer.Option(None, "--latex", help="Output LaTeX table"),
):
    """Compare two evaluation results."""
    import json
    from domain import EvaluationResult
    
    settings = get_settings()
    
    # Load results
    with open(baseline_file) as f:
        baseline_data = json.load(f)
    baseline = EvaluationResult(**baseline_data)
    
    with open(proposed_file) as f:
        proposed_data = json.load(f)
    proposed = EvaluationResult(**proposed_data)
    
    # Compare
    analyzer = ComparisonAnalyzer(settings)
    comparison = analyzer.compare_systems(baseline, proposed)
    
    # Display comparison
    _display_comparison(comparison)
    
    # Export LaTeX if requested
    if latex_output:
        analyzer.export_latex_table([baseline, proposed], latex_output)
        console.print(f"[green]LaTeX table exported to {latex_output}[/green]")


@app.command()
def init_dataset(
    dataset_path: Path = typer.Argument(..., help="Path to dataset directory"),
):
    """Initialize evaluation dataset structure."""
    dataset_path.mkdir(parents=True, exist_ok=True)
    
    # Create sample files
    pr_list_file = dataset_path / "pr_list.json"
    ground_truth_file = dataset_path / "ground_truth.json"
    
    if not pr_list_file.exists():
        import json
        pr_list_file.write_text(json.dumps([], indent=2))
        console.print(f"[green]Created {pr_list_file}[/green]")
    
    if not ground_truth_file.exists():
        import json
        ground_truth_file.write_text(json.dumps([], indent=2))
        console.print(f"[green]Created {ground_truth_file}[/green]")
    
    console.print(f"[bold green]Dataset structure initialized at {dataset_path}[/bold green]")


def _display_review_result(result):
    """Display review result in terminal."""
    from domain import Severity
    
    console.print("\n[bold]Review Summary[/bold]")
    console.print(f"PR ID: {result.pr_id}")
    console.print(f"System: {result.system_type.value}")
    console.print(f"Review time: {result.review_time_s:.2f}s")
    console.print(f"Estimated cost: ${result.token_cost_estimate:.4f}")
    
    # Findings table
    table = Table(title="Findings")
    table.add_column("Severity", style="cyan")
    table.add_column("Count", justify="right", style="magenta")
    table.add_column("With Patch", justify="right", style="green")
    
    by_severity = result.findings_by_severity
    for severity in [Severity.CRITICAL, Severity.MAJOR, Severity.MINOR, Severity.NIT]:
        findings = by_severity[severity]
        with_patch = sum(1 for f in findings if f.has_patch)
        table.add_row(
            severity.value,
            str(len(findings)),
            str(with_patch),
        )
    
    console.print(table)


def _display_evaluation_result(result):
    """Display evaluation result in terminal."""
    console.print("\n[bold]Evaluation Results[/bold]")
    console.print(f"System: {result.system_type.value}")
    console.print(f"Dataset size: {result.dataset_size} PRs")
    
    table = Table(title="Metrics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right", style="magenta")
    
    table.add_row("Actionability Rate", f"{result.actionability_rate:.2%}")
    table.add_row("Noise Rate", f"{result.noise_rate:.2%}")
    table.add_row("Important Issue Coverage", f"{result.important_issue_coverage:.2%}")
    table.add_row("Avg Findings per PR", f"{result.avg_findings_per_pr:.1f}")
    table.add_row("Avg Review Time", f"{result.avg_review_time_s:.1f}s")
    table.add_row("Avg Token Cost", f"${result.avg_token_cost:.4f}")
    
    console.print(table)


def _display_comparison(comparison):
    """Display comparison results."""
    console.print("\n[bold]System Comparison[/bold]")
    console.print(f"Baseline: {comparison['baseline']}")
    console.print(f"Proposed: {comparison['proposed']}")
    
    table = Table(title="Metric Improvements")
    table.add_column("Metric", style="cyan")
    table.add_column("Baseline", justify="right", style="yellow")
    table.add_column("Proposed", justify="right", style="green")
    table.add_column("Improvement", justify="right", style="magenta")
    
    for metric_name, values in comparison["metrics"].items():
        improvement = values["improvement"]
        improvement_str = f"+{improvement:.2%}" if improvement > 0 else f"{improvement:.2%}"
        
        table.add_row(
            metric_name.capitalize(),
            f"{values['baseline']:.2%}",
            f"{values['proposed']:.2%}",
            improvement_str,
        )
    
    console.print(table)


if __name__ == "__main__":
    app()

