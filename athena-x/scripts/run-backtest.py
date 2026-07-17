#!/usr/bin/env python3
"""CLI to trigger a backtest via the Python backend."""
import argparse
import httpx


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--symbol", required=True)
    p.add_argument("--strategy", default="athena-ensemble")
    p.add_argument("--backend", default="http://localhost:8000")
    args = p.parse_args()

    r = httpx.post(
        f"{args.backend}/validator/backtest",
        json={"symbol": args.symbol, "strategy_id": args.strategy},
        timeout=300,
    )
    r.raise_for_status()
    print(r.json())


if __name__ == "__main__":
    main()
