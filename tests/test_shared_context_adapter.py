import tempfile, unittest
from pathlib import Path
from hermes_nerve.integrations import shared_context

class SharedContextAdapterTests(unittest.TestCase):
    def test_detect_absent(self):
        with tempfile.TemporaryDirectory() as td:
            st=shared_context.detect(Path(td))
            self.assertFalse(st["installed"])
            self.assertEqual(st["authority"],"coordination-data-only")
    def test_install_from_source_is_external_copy(self):
        with tempfile.TemporaryDirectory() as source, tempfile.TemporaryDirectory() as home:
            src=Path(source); (src/"pyproject.toml").write_text("[project]\nname='hermes-context-bus'\n")
            (src/"plugin.yaml").write_text('name: hermes-context-bus\nversion: "0.2.0"\nprovides_tools:\n  - shared_context_health\n')
            (src/"README.md").write_text("bus")
            (src/"runtime").mkdir(); (src/"runtime"/"secret").write_text("runtime")
            (src/"state").mkdir(); (src/"state"/"db").write_text("state")
            st=shared_context.install_from_source(src,Path(home))
            self.assertTrue(st["installed"])
            target=Path(st["path"])
            self.assertTrue((target/"README.md").exists())
            self.assertFalse((target/"runtime").exists())
            self.assertFalse((target/"state").exists())
            self.assertIn("plugins doctor",st["doctor_command"])
    def test_detect_v02_manifest_and_schema(self):
        with tempfile.TemporaryDirectory() as home:
            root=Path(home)
            target=root/"plugins"/"hermes-context-bus"
            target.mkdir(parents=True)
            (target/"plugin.yaml").write_text('name: hermes-context-bus\nversion: "0.2.0"\nprovides_tools:\n  - shared_context_health\n')
            db=root/"shared-context"/"context.db"; db.parent.mkdir(parents=True)
            import sqlite3
            conn=sqlite3.connect(db); conn.execute("PRAGMA user_version=2"); conn.commit(); conn.close()
            st=shared_context.detect(root)
            self.assertEqual(st["version"],"0.2.0")
            self.assertEqual(st["schema_version"],2)
            self.assertTrue(st["health_tool"])

    def test_reconcile_uses_hermes_plugin_cli(self):
        calls=[]
        class P:
            returncode=0; stdout=""; stderr=""
        def runner(cmd,**kwargs):
            calls.append(cmd); return P()
        with tempfile.TemporaryDirectory() as home:
            target=Path(home)/"plugins"/"hermes-context-bus"; target.mkdir(parents=True)
            (target/"plugin.yaml").write_text('version: "0.2.0"\n')
            from unittest.mock import patch
            with patch.object(shared_context,"hermes_home",lambda:Path(home)):
                result=shared_context.reconcile_enabled(False,runner=runner)
            self.assertTrue(result["changed"])
            self.assertEqual(calls[0][:3],["hermes","plugins","disable"])
