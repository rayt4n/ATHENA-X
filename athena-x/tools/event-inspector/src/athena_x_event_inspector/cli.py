"""CLI entry point. Implementation in STEP 4."""
import click


@click.command()
@click.option('--pattern', default='*', help='Event pattern to subscribe to')
@click.option('--redis-url', default='redis://localhost:6379')
def main(pattern: str, redis_url: str):
    """Inspect bus events."""
    click.echo(f"Subscribing to {pattern} on {redis_url} — implementation in STEP 4")


if __name__ == '__main__':
    main()
