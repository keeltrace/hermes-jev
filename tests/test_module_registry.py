import unittest
from hermes_nerve.modules import MODULES
from hermes_nerve.profiles import PROFILES

class ModuleRegistryTests(unittest.TestCase):
    def test_registry_and_profiles_use_same_module_ids(self):
        expected=set(MODULES)
        self.assertGreaterEqual(len(expected),13)
        for name in ("fat_cat","operator","lean","marie_kondo"):
            self.assertEqual(set(PROFILES[name]),expected)

    def test_dependency_contract(self):
        self.assertIn("work_supervision",MODULES["token_trajectory"].dependencies)
        self.assertIn("assistant_loops",MODULES["assistant_audit"].dependencies)
        self.assertIn("reflex",MODULES["assistant_audit"].dependencies)
