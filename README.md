# Obsidian

A Codex plugin for searching, reading, and managing notes in a local Obsidian vault through the official [Obsidian CLI](https://help.obsidian.md/cli).

## Requirements

- Codex with plugin support and the `codex` command available.
- Python 3.10 or later (`python3` on your PATH).
- Obsidian running with its CLI enabled and your vault registered in the app.
- macOS or Linux. Windows and Android execution are not supported.

## Install

Clone into a folder you intend to keep, then run:

```sh
git clone https://github.com/PaulRenvoise/codex-obsidian-plugin.git
cd codex-obsidian-plugin
python3 setup.py --install
```

Reload Codex or start a new conversation after installation.

## Configure

Open the plugin settings in Codex and set:

- **Vault folder:** the absolute path to your vault. A leading `~` is supported.
- **CLI executable:** optional; leave blank for automatic discovery.
- **Read-only access:** restrict the plugin wrapper to supported read commands.

If your host does not expose plugin settings, configure the vault from the repository:

```sh
python3 setup.py --vault "/path/to/your/vault"
```

Settings stay on your computer at `$CODEX_HOME/plugin-data/obsidian/settings.json`, defaulting to `~/.codex/plugin-data/obsidian/settings.json`. No vault path, notes, or credentials are included in this repository.

The small MCP server provides settings only; note operations use the official CLI. Read-only mode applies to this plugin's wrapper. Android notes are accessible through your existing sync service and the local copy of the vault on your computer.

## Use

Ask Codex to “find my notes about gardening,” “summarize this Obsidian note,” or “add a task to my daily note.” Local CLI communication may require sandbox permission.

## Test

```sh
python3 -m unittest discover -s plugins/obsidian-local/tests -v
```

## License

[MIT](LICENSE)
