"""CLI for stage-gate checklist."""
import click
from rich.console import Console
from rich.table import Table
from .checker import StageGateChecker


@click.command()
@click.option("--stage", required=True, type=int, help="Stage number to check")
@click.option("--root", default=".", help="Project root directory")
def main(stage: int, root: str):
    """Run stage-gate checklist for a given stage."""
    console = Console()
    checker = StageGateChecker(project_root=root)
    report = checker.check_stage(stage)

    # Print summary table
    table = Table(title=f"Stage {stage} Gate Report")
    table.add_column("Criterion", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Details")

    for r in report.results:
        status = "[green]PASS[/green]" if r.passed else "[red]FAIL[/red]"
        table.add_row(r.name, status, r.details)

    console.print(table)
    console.print()
    console.print(f"[bold]Overall: {'PASS' if report.all_passed else 'FAIL'}[/bold]")
    console.print(f"  Passed: {report.pass_count}/{len(report.results)}")
    console.print(f"  Failed: {report.fail_count}")


if __name__ == "__main__":
    main()
