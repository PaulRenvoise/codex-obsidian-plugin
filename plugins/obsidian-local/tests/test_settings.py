import json, os
from pathlib import Path
import subprocess, sys, tempfile, unittest
from unittest.mock import patch
SCRIPTS=Path(__file__).resolve().parents[1]/'scripts'
sys.path.insert(0,str(SCRIPTS))
import settings_store as store
import settings_server as server

class SettingsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.env=patch.dict(os.environ,{'CODEX_HOME':self.tmp.name+'/codex','HOME':self.tmp.name,'XDG_CONFIG_HOME':self.tmp.name+'/.config'})
        self.env.start()
        self.vault=Path(self.tmp.name)/'Notes with spaces'; (self.vault/'.obsidian').mkdir(parents=True)
        self.registry={'id-one':{'path':str(self.vault)}}
        for directory in ['Library/Application Support/obsidian','.config/obsidian']:
            p=Path(self.tmp.name)/directory/'obsidian.json'; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps({'vaults':self.registry}))
    def tearDown(self):
        self.env.stop(); self.tmp.cleanup()
    def test_native_settings_contract_and_read_has_no_side_effects(self):
        init=server.dispatch('initialize',{'protocolVersion':'2025-11-25'})
        self.assertEqual(init['capabilities']['experimental']['openai/settings']['readTool'],'settings.read')
        r=server.dispatch('tools/call',{'name':'settings.read','arguments':{}})['structuredContent']
        self.assertEqual(set(r['schema']['properties']),set(r['values']))
        self.assertIn('vault_path',r['values']); self.assertNotIn('vault_name',r['values'])
        self.assertFalse(store.settings_path().exists())
    def test_partial_update_survives_new_process(self):
        store.update_values({'vault_path':str(self.vault)})
        server.dispatch('tools/call',{'name':'settings.update','arguments':{'set':{'read_only':True}}})
        request={'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':'settings.read','arguments':{}}}
        r=subprocess.run([sys.executable,str(SCRIPTS/'settings_server.py')],input=json.dumps(request)+'\n',text=True,capture_output=True,check=True)
        values=json.loads(r.stdout)['result']['structuredContent']['values']
        self.assertTrue(values['read_only']); self.assertEqual(values['vault_path'],str(self.vault))
        self.assertEqual(store.settings_path().stat().st_mode & 0o777,0o600)
    def test_invalid_update_keeps_saved_values(self):
        store.update_values({'vault_path':str(self.vault)})
        before=store.settings_path().read_bytes()
        for changes in [{},{'vault_path':2},{'vault_path':'relative/path'},{'vault_path':'/a\nb'},{'read_only':'yes'},{'cli_path':'relative/path'},{'vault_name':'old'}]:
            r=server.dispatch('tools/call',{'name':'settings.update','arguments':{'set':changes}})
            self.assertTrue(r['isError']); self.assertEqual(before,store.settings_path().read_bytes())
    def test_cli_preserves_arguments_and_requires_vault(self):
        with patch.object(store,'cli_executable',return_value='/mock/obsidian'):
            settings={**store.DEFAULTS,'vault_path':str(self.vault)}
            args=['read','path=Folder/My note.md']
            self.assertEqual(store.command_line(args,settings),['/mock/obsidian','vault=id-one',*args])
            with self.assertRaises(ValueError): store.command_line(['read'],store.DEFAULTS)
            with self.assertRaises(ValueError): store.command_line(['read','vault=Other'],settings)
            self.assertEqual(store.command_line(['vaults'],store.DEFAULTS),['/mock/obsidian','vaults'])
    def test_read_only_blocks_mutations_before_resolution(self):
        settings={**store.DEFAULTS,'vault_path':str(self.vault),'read_only':True}
        with patch.object(store,'cli_executable',return_value='/mock/obsidian'):
            self.assertIn('read',store.command_line(['read','path=note.md'],settings))
        with patch.object(store,'resolve_vault_id',side_effect=AssertionError('must not resolve')):
            for cmd in ['create','append','delete','eval','command','task','sync','plugin:install']:
                with self.assertRaises(ValueError): store.command_line([cmd],settings)
    def test_protocol_errors_and_notifications(self):
        self.assertIsNone(server.process('{"jsonrpc":"2.0","method":"notifications/initialized"}'))
        self.assertEqual(server.process('not json')['error']['code'],-32700)
        self.assertEqual(server.process('[]')['error']['code'],-32600)
    def test_wrapper_passes_id_to_executable(self):
        fake=Path(self.tmp.name)/'fake-cli'
        fake.write_text('#!'+sys.executable+'\nimport json,sys\nprint(json.dumps(sys.argv[1:]))\n'); fake.chmod(0o700)
        store.update_values({'vault_path':str(self.vault),'cli_path':str(fake)})
        r=subprocess.run([sys.executable,str(SCRIPTS/'obsidian.py'),'read','path=Notes/a b.md'],capture_output=True,text=True,check=True)
        self.assertEqual(json.loads(r.stdout),['vault=id-one','read','path=Notes/a b.md'])
    def test_tilde_and_symlink_paths(self):
        self.assertEqual(store.resolve_vault_id('~/Notes with spaces'),'id-one')
        alias=Path(self.tmp.name)/'shortcut'; alias.symlink_to(self.vault)
        self.assertEqual(store.resolve_vault_id(str(alias)),'id-one')
    def test_same_names_resolve_by_path(self):
        other=Path(self.tmp.name)/'elsewhere'/self.vault.name
        (other/'.obsidian').mkdir(parents=True)
        with patch.object(store,'vault_registry',return_value={**self.registry,'id-two':{'path':str(other)}}):
            self.assertEqual(store.resolve_vault_id(str(self.vault)),'id-one')
            self.assertEqual(store.resolve_vault_id(str(other)),'id-two')
    def test_missing_unregistered_and_ambiguous_folder_fail(self):
        with self.assertRaises(ValueError): store.resolve_vault_id(str(self.vault/'missing'))
        with patch.object(store,'vault_registry',return_value={}):
            with self.assertRaises(ValueError): store.resolve_vault_id(str(self.vault))
        with patch.object(store,'vault_registry',return_value={**self.registry,'id-two':{'path':str(self.vault)}}):
            with self.assertRaises(ValueError): store.resolve_vault_id(str(self.vault))

if __name__=='__main__': unittest.main()
