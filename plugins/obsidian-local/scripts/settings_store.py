"""Shared, host-local settings for the Obsidian CLI and MCP settings extension."""
import contextlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

DEFAULTS = {'vault_path': '', 'cli_path': '', 'read_only': False}
PROPERTIES = {
    'vault_path': {'type': 'string', 'title': 'Vault folder', 'description': 'Absolute path to a vault folder on this computer. A leading ~ is supported. Open the folder in Obsidian first to register it.', 'maxLength': 4096},
    'cli_path': {'type': 'string', 'title': 'CLI executable (optional)', 'description': 'Leave blank to detect the official Obsidian CLI. Otherwise enter an absolute executable path on this computer.', 'maxLength': 4096},
    'read_only': {'type': 'boolean', 'title': 'Read-only access', 'description': 'Allow supported read operations through the CLI wrapper and block changes.'},
}
READ_COMMANDS = frozenset('help version vault vaults files folders file folder read search search:context backlinks links unresolved orphans deadends outline aliases properties property:read daily:path daily:read tasks tags tag templates template:read bookmarks bases base:query base:views diff history history:list history:read sync:status sync:history sync:read plugins plugins:enabled plugin hotkeys hotkey recents tabs workspace wordcount'.split())

def settings_path():
    # A stable location shared by cached plugin versions and shell invocations.
    home = Path(os.environ.get('CODEX_HOME') or Path.home() / '.codex').expanduser()
    return home / 'plugin-data' / 'obsidian' / 'settings.json'

def validate(values):
    if not isinstance(values, dict) or set(values) - set(DEFAULTS):
        raise ValueError('Settings must contain only vault_path, cli_path, and read_only.')
    for key, value in values.items():
        if key == 'read_only':
            if type(value) is not bool:
                raise ValueError('read_only must be a boolean.')
        elif not isinstance(value, str) or len(value) > PROPERTIES[key]['maxLength'] or any(ord(c) < 32 for c in value):
            raise ValueError(f'{key} must be a single-line string of at most {PROPERTIES[key]["maxLength"]} characters.')
        elif value != value.strip():
            raise ValueError(f'{key} must not start or end with whitespace.')
        elif key in ('cli_path', 'vault_path') and value and not Path(value).expanduser().is_absolute():
            raise ValueError(f'{key} must be an absolute path, a path starting with ~, or blank.')
    return values

def read_values():
    path = settings_path()
    if not path.exists():
        return dict(DEFAULTS)
    try:
        values = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise ValueError(f'Cannot read Obsidian settings at {path}: {exc}') from exc
    return {**DEFAULTS, **validate(values)}

@contextlib.contextmanager
def write_lock():
    import fcntl
    directory = settings_path().parent
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (directory / 'settings.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield

def update_values(changes):
    validate(changes)
    if not changes:
        raise ValueError('Provide at least one setting to update.')
    with write_lock():
        values = {**read_values(), **changes}
        path = settings_path()
        fd, temporary = tempfile.mkstemp(dir=path.parent, prefix='.settings-')
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as stream:
                json.dump(values, stream, ensure_ascii=False, indent=2)
                stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    return values

def settings_document():
    return {
        'schema': {'type': 'object', 'properties': PROPERTIES},
        'values': read_values(),
        'layout': [{'kind': 'group', 'title': 'Obsidian connection', 'items': [
            {'kind': 'property', 'property': key} for key in DEFAULTS
        ]}],
    }

def cli_executable(settings):
    override = settings['cli_path']
    if override:
        path = Path(override).expanduser()
        if not path.is_file() or not os.access(path, os.X_OK):
            raise ValueError('Configured Obsidian CLI executable does not exist or is not executable.')
        return str(path)
    for name in ('obsidian', 'obsidian-cli'):
        path = shutil.which(name)
        if path:
            return path
    if sys.platform == 'darwin':
        for apps in (Path('/Applications'), Path.home() / 'Applications'):
            path = apps / 'Obsidian.app/Contents/MacOS/obsidian-cli'
            if path.is_file() and os.access(path, os.X_OK):
                return str(path)
    raise ValueError('Obsidian CLI was not found. Enable it in Obsidian, or set CLI executable in the plugin settings.')

def vault_registry():
    """Read vault IDs from Obsidian's local application registry."""
    if sys.platform == 'darwin':
        config = Path.home() / 'Library/Application Support/obsidian/obsidian.json'
    elif sys.platform.startswith('linux'):
        config = Path(os.environ.get('XDG_CONFIG_HOME') or Path.home() / '.config') / 'obsidian/obsidian.json'
    else:
        raise ValueError('Path-based vault resolution currently supports macOS and Linux.')
    try:
        registry = json.loads(config.read_text(encoding='utf-8'))['vaults']
        if not isinstance(registry, dict):
            raise ValueError('Invalid vault registry.')
        return registry
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise ValueError('Cannot read the Obsidian vault registry. Open the vault folder in Obsidian first.') from exc

def resolve_vault_id(folder):
    if not folder:
        raise ValueError('Choose a vault folder in the Obsidian plugin settings before accessing notes.')
    path = Path(folder).expanduser()
    if not path.is_absolute():
        raise ValueError('Vault folder must be an absolute path or start with ~.')
    path = path.resolve()
    if not path.is_dir() or not (path / '.obsidian').is_dir():
        raise ValueError('Vault folder is unavailable or does not contain an .obsidian directory.')
    matches = []
    for vault_id, entry in vault_registry().items():
        if isinstance(entry, dict) and isinstance(entry.get('path'), str):
            registered = Path(entry['path']).expanduser()
            if registered.is_absolute() and registered.resolve() == path:
                matches.append(vault_id)
    if len(matches) != 1:
        raise ValueError('Vault folder must match exactly one registered Obsidian vault. Open this folder in Obsidian and check the plugin setting.')
    return matches[0]


def command_line(args, settings):
    args = args or ['help']
    if any(arg.startswith('vault=') for arg in args):
        raise ValueError('Select the vault in the plugin settings; do not override it in CLI arguments.')
    if settings['read_only'] and args[0] not in READ_COMMANDS:
        raise ValueError('This command is blocked by the read-only plugin setting.')
    target = [] if args[0] in ('help', 'version', 'vaults') else ['vault=' + resolve_vault_id(settings['vault_path'])]
    return [cli_executable(settings), *target, *args]

def run_cli(args):
    return subprocess.run(command_line(args, read_values()), check=False).returncode
