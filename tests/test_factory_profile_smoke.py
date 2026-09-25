import unittest
from hermes_nerve.config_resolver import resolve_config

class FactoryProfileSmokeTests(unittest.TestCase):
    def test_lean_factory_defaults(self):
        r=resolve_config(profile={"version":1,"nerve_profile":"lean","nerve_modules":{},"advanced":{}})
        self.assertTrue(r.enabled("work_supervision"))
        self.assertTrue(r.enabled("token_trajectory"))
        self.assertTrue(r.enabled("reflex"))
        for module in ("assistant_loops","assistant_audit","shared_context","remote_workers","context_governor","shadow_testing"):
            self.assertFalse(r.enabled(module))

    def test_marie_kondo_has_no_qol_modules(self):
        r=resolve_config(profile={"version":1,"nerve_profile":"marie_kondo","nerve_modules":{},"advanced":{}})
        for module in ("assistant_loops","assistant_audit","shared_context","remote_workers","context_governor","action_gate","shadow_testing"):
            self.assertFalse(r.enabled(module))