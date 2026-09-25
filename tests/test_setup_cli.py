import io, unittest
from unittest.mock import patch
from hermes_nerve import cli

class SetupCliTests(unittest.TestCase):
    def _mutations(self):
        fake_path=type("P",(),{"__str__":lambda self:"/tmp/profile.json"})()
        return patch.object(cli,"save_profile",return_value=fake_path), patch.object(cli.shared_context,"reconcile_enabled",return_value={"changed":True}), patch.object(cli.assistant,"install",return_value={}), patch.object(cli.assistant,"disable",return_value={}), patch.object(cli,"load_profile",return_value=None)

    def test_show(self):
        fake=type("R",(),{"profile":"legacy","enabled":lambda self,k:False})()
        out=io.StringIO()
        with patch.object(cli,"_current",lambda:fake), patch("sys.stdout",out): self.assertEqual(cli.main(["setup","--show"]),0)
        self.assertIn("Profile: Legacy",out.getvalue())

    def test_profile_order(self): self.assertEqual(cli._ORDER,("fat_cat","operator","lean","marie_kondo"))

    def test_noninteractive_profile_reconciles_shared_context(self):
        a,b,c,d,e=self._mutations()
        with a,b as rec,c,d,e:
            self.assertEqual(cli.main(["setup","--profile","lean"]),0); rec.assert_called_once_with(False)

    def test_legacy_is_explicit_cli_target(self):
        a,b,c,d,e=self._mutations()
        with a as save,b,c,d,e:
            self.assertEqual(cli.main(["setup","--profile","legacy"]),0)
            self.assertEqual(save.call_args.args[0]["nerve_profile"],"legacy")

    def test_show_profile_is_preview_not_mutation(self):
        with patch.object(cli,"save_profile") as save, patch("sys.stdout",io.StringIO()):
            self.assertEqual(cli.main(["setup","--profile","lean","--show"]),0); save.assert_not_called()

    def test_interactive_rejects_zero_and_negative_choices(self):
        fake=type("R",(),{"modules":{mid:False for mid in cli.MODULES}})()
        for value in ("0","-1"):
            with patch.object(cli,"_current",lambda:fake), patch("sys.stdin.isatty",return_value=True), patch("builtins.input",return_value=value):
                self.assertEqual(cli.main(["setup"]),2)

    def test_selecting_same_profile_preserves_explicit_overrides(self):
        existing={"version":1,"nerve_profile":"lean","nerve_modules":{"context_governor":True},"advanced":{}}
        fake_path=type("P",(),{"__str__":lambda self:"/tmp/profile.json"})()
        with patch.object(cli,"load_profile",return_value=existing), patch.object(cli,"save_profile",return_value=fake_path) as save, \
             patch.object(cli.shared_context,"reconcile_enabled",return_value={"changed":True}), patch.object(cli.assistant,"disable",return_value={}):
            self.assertEqual(cli.main(["setup","--profile","lean"]),0)
        self.assertEqual(save.call_args.args[0]["nerve_modules"],{"context_governor":True})

    def test_reset_profile_clears_explicit_overrides(self):
        existing={"version":1,"nerve_profile":"lean","nerve_modules":{"context_governor":True},"advanced":{}}
        fake_path=type("P",(),{"__str__":lambda self:"/tmp/profile.json"})()
        with patch.object(cli,"load_profile",return_value=existing), patch.object(cli,"save_profile",return_value=fake_path) as save, \
             patch.object(cli.shared_context,"reconcile_enabled",return_value={"changed":True}), patch.object(cli.assistant,"disable",return_value={}):
            self.assertEqual(cli.main(["setup","--reset","lean"]),0)
        self.assertEqual(save.call_args.args[0]["nerve_modules"],{})
