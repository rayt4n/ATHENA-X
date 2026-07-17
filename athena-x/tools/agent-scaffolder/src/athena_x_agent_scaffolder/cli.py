"""CLI entry point. Implementation in STEP 4."""
import click


@click.command()
@click.argument('layer', type=click.Choice(['data-collection', 'raw-intelligence', 'decision-intelligence', 'supervisor', 'validator', 'self-correction', 'automation']))
@click.argument('slug')
def main(layer: str, slug: str):
    """Scaffold a new agent."""
    click.echo(f"Scaffolding {layer}/{slug} — implementation in STEP 4")


if __name__ == '__main__':
    main()
