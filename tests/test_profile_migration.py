import unittest
from hermes_nerve.config_resolver import resolve_config

class ProfileMigrationTests(unittest.TestCase):
    def test_legacy_preserves_v023(self):
        r=resolve_config(get_config=lambda k,d=None:d, profile=None)
        self.assertEqual(r.profile,"legacy")
        self.assertTrue(r.enabled("work_supervision"))
        self.assertTrue(r.enabled("context_governor"))
        self.assertFalse(r.enabled("action_gate"))

    def test_explicit_hermes_profile_overrides_sidecar_profile(self):
        side={"version":1,"nerve_profile":"fat_cat","nerve_modules":{},"advanced":{}}
        r=resolve_config(get_config=lambda k,d=None: "lean" if k=="nerve_profile" else d, profile=side)
        self.assertEqual(r.profile,"lean")
        self.assertFalse(r.enabled("assistant_loops"))
