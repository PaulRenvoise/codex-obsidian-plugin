#!/usr/bin/env python3
"""Run the official Obsidian CLI using the plugin's persisted settings."""
import sys
from settings_store import run_cli

if __name__ == '__main__':
    try:
        raise SystemExit(run_cli(sys.argv[1:]))
    except (ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
