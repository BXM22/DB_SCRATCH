#!/usr/bin/env python3
"""Backward-compatible wrapper — prefer `python -m db_scratch` or `./run.sh`."""

from db_scratch.cli.main import main

if __name__ == "__main__":
    main()
