import io, unittest
from unittest.mock import patch
from hermes_nerve import cli

class SetupCliTests(unittest.TestCase):
    def test_show(self):
        fake=type("R",(),{"profile":"legacy","enabled":lambda self,k:False})()
        out=io.StringIO()
        with patch.object(cli,"_current",lambda:fake), patch("sys.stdout",out):
            self.assertEqual(cli.main(["setup","--show"]),0)
        self.assertIn("Profile: Legacy",out.getvalue())
    def test_profile_order(self):
        self.assertEqual(cli._ORDER,("fat_cat","operator","lean","marie_kondo"))

    def test_noninteractive_profile_reconciles_shared_context(self):
        fake_path=type("P",(),{"__str__":lambda self:"/tmp/profile.json"})()
        with patch.object(cli,"save_profile",return_value=fake_path), \
             patch.object(cli.shared_context,"reconcile_enabled",return_value={"changed":True}) as rec:
            self.assertEqual(cli.main(["setup","--profile","lean"]),0)
            rec.assert_called_once_with(False)
