"""Tests for persisted settings, CLI routing, and the MCP settings protocol."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import settings_server as server
import settings_store as store


class VaultTestCase(unittest.TestCase):
    """Isolate settings and the Obsidian registry from the user's environment."""

    def setUp(self):
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        self.home_dir = Path(temporary_directory.name)

        environment = patch.dict(
            os.environ,
            {
                "CODEX_HOME": str(self.home_dir / "codex"),
                "HOME": str(self.home_dir),
                "XDG_CONFIG_HOME": str(self.home_dir / ".config"),
            },
        )
        environment.start()
        self.addCleanup(environment.stop)

        self.vault_path = self.home_dir / "Notes with spaces"
        (self.vault_path / ".obsidian").mkdir(parents=True)
        self.registry = {"id-one": {"path": str(self.vault_path)}}

        # Populate both supported registry locations so tests run on either OS.
        registry_directories = (
            "Library/Application Support/obsidian",
            ".config/obsidian",
        )
        for directory in registry_directories:
            registry_path = self.home_dir / directory / "obsidian.json"
            registry_path.parent.mkdir(parents=True, exist_ok=True)
            registry_path.write_text(
                json.dumps({"vaults": self.registry}), encoding="utf-8"
            )

    def configured_settings(self, **overrides):
        return {
            **store.DEFAULTS,
            "vault_path": str(self.vault_path),
            **overrides,
        }

    def run_script(self, script_name, *arguments, input_text=None):
        return subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / script_name), *arguments],
            input=input_text,
            text=True,
            capture_output=True,
            check=True,
        )


class SettingsTests(VaultTestCase):
    def test_read_exposes_schema_and_values_without_creating_settings_file(self):
        response = server.dispatch(
            "tools/call", {"name": "settings.read", "arguments": {}}
        )
        document = response["structuredContent"]

        self.assertEqual(set(document["schema"]["properties"]), set(document["values"]))
        self.assertIn("vault_path", document["values"])
        self.assertNotIn("vault_name", document["values"])
        self.assertFalse(store.settings_path().exists())

    def test_partial_update_survives_new_process(self):
        store.update_values({"vault_path": str(self.vault_path)})
        server.dispatch(
            "tools/call",
            {"name": "settings.update", "arguments": {"set": {"read_only": True}}},
        )
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "settings.read", "arguments": {}},
        }

        process = self.run_script(
            "settings_server.py", input_text=json.dumps(request) + "\n"
        )
        values = json.loads(process.stdout)["result"]["structuredContent"]["values"]

        self.assertTrue(values["read_only"])
        self.assertEqual(values["vault_path"], str(self.vault_path))
        self.assertEqual(store.settings_path().stat().st_mode & 0o777, 0o600)

    def test_invalid_updates_leave_saved_settings_unchanged(self):
        store.update_values({"vault_path": str(self.vault_path)})
        saved_contents = store.settings_path().read_bytes()
        invalid_updates = {
            "empty update": {},
            "non-string vault path": {"vault_path": 2},
            "relative vault path": {"vault_path": "relative/path"},
            "multiline vault path": {"vault_path": "/a\nb"},
            "non-boolean read-only setting": {"read_only": "yes"},
            "relative CLI path": {"cli_path": "relative/path"},
            "unsupported setting": {"vault_name": "old"},
        }

        for case, changes in invalid_updates.items():
            with self.subTest(case=case):
                response = server.dispatch(
                    "tools/call",
                    {"name": "settings.update", "arguments": {"set": changes}},
                )

                self.assertTrue(response["isError"])
                self.assertEqual(store.settings_path().read_bytes(), saved_contents)


class CliTests(VaultTestCase):
    def test_command_preserves_arguments_with_spaces(self):
        arguments = ["read", "path=Folder/My note.md"]

        with patch.object(store, "cli_executable", return_value="/mock/obsidian"):
            command = store.command_line(arguments, self.configured_settings())

        self.assertEqual(command, ["/mock/obsidian", "vault=id-one", *arguments])

    def test_read_requires_a_configured_vault(self):
        with self.assertRaises(ValueError):
            store.command_line(["read"], store.DEFAULTS)

    def test_command_rejects_vault_override(self):
        with self.assertRaises(ValueError):
            store.command_line(["read", "vault=Other"], self.configured_settings())

    def test_listing_vaults_does_not_require_a_configured_vault(self):
        with patch.object(store, "cli_executable", return_value="/mock/obsidian"):
            command = store.command_line(["vaults"], store.DEFAULTS)

        self.assertEqual(command, ["/mock/obsidian", "vaults"])

    def test_read_only_mode_allows_reading(self):
        settings = self.configured_settings(read_only=True)

        with patch.object(store, "cli_executable", return_value="/mock/obsidian"):
            command = store.command_line(["read", "path=note.md"], settings)

        self.assertEqual(
            command, ["/mock/obsidian", "vault=id-one", "read", "path=note.md"]
        )

    def test_read_only_mode_blocks_mutations_before_vault_resolution(self):
        settings = self.configured_settings(read_only=True)
        blocked_commands = (
            "create", "append", "delete", "eval",
            "command", "task", "sync", "plugin:install",
        )

        with patch.object(store, "resolve_vault_id") as resolve_vault:
            for command in blocked_commands:
                with self.subTest(command=command):
                    with self.assertRaises(ValueError):
                        store.command_line([command], settings)

            resolve_vault.assert_not_called()

    def test_wrapper_passes_vault_id_and_arguments_to_executable(self):
        fake_cli = self.home_dir / "fake-cli"
        fake_cli.write_text(
            f"#!{sys.executable}\n"
            "import json\n"
            "import sys\n"
            "print(json.dumps(sys.argv[1:]))\n",
            encoding="utf-8",
        )
        fake_cli.chmod(0o700)
        store.update_values(
            {"vault_path": str(self.vault_path), "cli_path": str(fake_cli)}
        )

        process = self.run_script("obsidian.py", "read", "path=Notes/a b.md")

        self.assertEqual(
            json.loads(process.stdout),
            ["vault=id-one", "read", "path=Notes/a b.md"],
        )


class VaultResolutionTests(VaultTestCase):
    def test_tilde_path_resolves_to_registered_vault(self):
        self.assertEqual(store.resolve_vault_id("~/Notes with spaces"), "id-one")

    def test_symlink_resolves_to_registered_vault(self):
        alias_path = self.home_dir / "shortcut"
        alias_path.symlink_to(self.vault_path)

        self.assertEqual(store.resolve_vault_id(str(alias_path)), "id-one")

    def test_vaults_with_same_name_are_distinguished_by_path(self):
        other_vault = self.home_dir / "elsewhere" / self.vault_path.name
        (other_vault / ".obsidian").mkdir(parents=True)
        registry = {**self.registry, "id-two": {"path": str(other_vault)}}

        with patch.object(store, "vault_registry", return_value=registry):
            self.assertEqual(store.resolve_vault_id(str(self.vault_path)), "id-one")
            self.assertEqual(store.resolve_vault_id(str(other_vault)), "id-two")

    def test_missing_folder_is_rejected(self):
        with self.assertRaises(ValueError):
            store.resolve_vault_id(str(self.vault_path / "missing"))

    def test_unregistered_folder_is_rejected(self):
        with patch.object(store, "vault_registry", return_value={}):
            with self.assertRaises(ValueError):
                store.resolve_vault_id(str(self.vault_path))

    def test_folder_registered_under_multiple_ids_is_rejected(self):
        registry = {**self.registry, "id-two": {"path": str(self.vault_path)}}

        with patch.object(store, "vault_registry", return_value=registry):
            with self.assertRaises(ValueError):
                store.resolve_vault_id(str(self.vault_path))


class ProtocolTests(unittest.TestCase):
    def test_initialize_advertises_native_settings_read_tool(self):
        response = server.dispatch("initialize", {"protocolVersion": "2025-11-25"})
        extension = response["capabilities"]["experimental"]["openai/settings"]

        self.assertEqual(extension["readTool"], "settings.read")

    def test_notifications_do_not_produce_a_response(self):
        notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
        }

        self.assertIsNone(server.process(json.dumps(notification)))

    def test_malformed_json_returns_parse_error(self):
        response = server.process("not json")

        self.assertEqual(response["error"]["code"], -32700)

    def test_non_object_request_returns_invalid_request_error(self):
        response = server.process("[]")

        self.assertEqual(response["error"]["code"], -32600)


if __name__ == "__main__":
    unittest.main()
