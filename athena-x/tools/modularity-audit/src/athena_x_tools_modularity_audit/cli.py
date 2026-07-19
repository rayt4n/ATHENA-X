"""CLI for modularity audit."""
import click
from rich.console import Console
from rich.table import Table
from .audit import ModularityAuditor


@click.command()
@click.option("--root", default=".", help="Project root directory")
def main(root: str):
    """Run modularity audit."""
    console = Console()
    auditor = ModularityAuditor(root=root)
    result = auditor.audit()

    console.print()
    console.print(f"[bold]Modularity Audit Report[/bold]")
    console.print(f"  Packages: {result.total_packages}")
    console.print(f"  Imports:  {result.total_imports}")
    console.print()

    # Circular imports
    if result.circular_imports:
        console.print(f"[red]Circular Imports: {len(result.circular_imports)}[/red]")
        for cycle in result.circular_imports[:5]:
            console.print(f"  {' -> '.join(cycle)}")
    else:
        console.print("[green]Circular Imports: 0[/green]")

    # Dependency violations
    if result.dependency_violations:
        console.print(f"\n[red]Dependency Direction Violations: {len(result.dependency_violations)}[/red]")
        for v in result.dependency_violations[:5]:
            console.print(f"  {v}")
    else:
        console.print(f"\n[green]Dependency Direction Violations: 0[/green]")

    # Packages without __init__.py
    if result.packages_without_init:
        console.print(f"\n[yellow]Files without __init__.py: {len(result.packages_without_init)}[/yellow]")
    else:
        console.print(f"[green]Files without __init__.py: 0[/green]")

    # Public interfaces
    console.print(f"\n[bold]Public Interfaces:[/bold] ({len(result.public_interfaces)} packages)")
    for pkg, exports in list(result.public_interfaces.items())[:5]:
        console.print(f"  {pkg}: {', '.join(exports[:5])}")

    console.print()
    status = "[green]PASS[/green]" if result.passed else "[red]FAIL[/red]"
    console.print(f"[bold]Overall: {status}[/bold]")


if __name__ == "__main__":
    main()
