"""CLI entry point. Implementation in STEP 4."""
import click


@click.command()
@click.argument('plugin_type', type=click.Choice(['indicators', 'options', 'patterns', 'dark-pool']))
@click.argument('slug')
def main(plugin_type: str, slug: str):
    """Scaffold a new plugin."""
    click.echo(f"Scaffolding {plugin_type}/{slug} — implementation in STEP 4")


if __name__ == '__main__':
    main()
