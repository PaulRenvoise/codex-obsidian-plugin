#!/usr/bin/env python3
"""Configure native Obsidian settings or install this local plugin marketplace."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'plugins/obsidian/scripts'))
from settings_store import read_values, update_values

p = argparse.ArgumentParser(description='Configure the Obsidian plugin. Prefer the native plugin settings page.')
p.add_argument('--vault', help='Absolute vault folder path (a leading ~ is supported).')
p.add_argument('--cli-path', help='Absolute CLI executable path; an empty string restores automatic discovery.')
p.add_argument('--read-only', action=argparse.BooleanOptionalAction, default=None)
p.add_argument('--install', action='store_true')
a = p.parse_args()
changes = {}
if a.vault is not None: changes['vault_path'] = a.vault
if a.cli_path is not None: changes['cli_path'] = a.cli_path
if a.read_only is not None: changes['read_only'] = a.read_only
try:
    print(json.dumps(update_values(changes) if changes else read_values(), ensure_ascii=False, indent=2))
except (ValueError, OSError) as exc:
    p.error(str(exc))
if a.install:
    subprocess.run(['codex', 'plugin', 'marketplace', 'add', str(ROOT)], check=True)
    subprocess.run(['codex', 'plugin', 'add', 'obsidian@codex-obsidian-plugin'], check=True)
