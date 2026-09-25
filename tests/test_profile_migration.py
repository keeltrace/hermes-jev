import json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from hermes_nerve.config_resolver import resolve_config
from hermes_nerve.profiles import load_profile, normalize_profile_name

class ProfileMigrationTests(unittest.TestCase):
    def test_legacy_preserves_v023_without_reading_real_home(self):
        with tempfile.TemporaryDirectory() as td:
            r=resolve_config(get_config=lambda k,d=None:d, home=Path(td), profile=None)
        self.assertEqual(r.profile,"legacy"); self.assertTrue(r.enabled("work_supervision")); self.assertTrue(r.enabled("context_governor")); self.assertFalse(r.enabled("action_gate"))

    def test_explicit_hermes_profile_does_not_inherit_different_sidecar_overrides(self):
        side={"version":1,"nerve_profile":"fat_cat","nerve_modules":{"assistant_loops":True,"context_governor":True},"advanced":{"gate_mode":"precommit"}}
        r=resolve_config(get_config=lambda k,d=None: "lean" if k=="nerve_profile" else d, profile=side)
        self.assertEqual(r.profile,"lean"); self.assertFalse(r.enabled("assistant_loops")); self.assertFalse(r.enabled("context_governor")); self.assertEqual(r.advanced,{})

    def test_corrupt_profile_recovers_backup_then_falls_back_legacy(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/"nerve"; root.mkdir(); (root/"profile.json").write_text("{bad")
            (root/"profile.json.bak").write_text(json.dumps({"version":1,"nerve_profile":"Lean","nerve_modules":{},"advanced":{}}))
            with self.assertLogs("hermes_nerve.profiles",level="WARNING"):
                self.assertEqual(load_profile(Path(td))["nerve_profile"],"lean")
            (root/"profile.json.bak").write_text("also bad")
            with self.assertLogs("hermes_nerve.profiles",level="WARNING"):
                self.assertIsNone(load_profile(Path(td)))

    def test_profile_name_normalization(self):
        self.assertEqual(normalize_profile_name("Fat-Cat"),"fat_cat")
        self.assertEqual(normalize_profile_name("Marie Kondo"),"marie_kondo")
