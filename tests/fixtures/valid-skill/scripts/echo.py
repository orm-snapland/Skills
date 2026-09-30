#!/usr/bin/env python3
"""Fixture script: print one JSON object to stdout. Not a product skill."""

from __future__ import annotations

import argparse
import json
import sys


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Echo a fixture message as JSON on stdout."
    )
    parser.add_argument("--message", default="ok", help="Value of the message field.")
    args = parser.parse_args()
    json.dump({"message": args.message}, sys.stdout)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
