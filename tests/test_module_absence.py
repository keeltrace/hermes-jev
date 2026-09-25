from __future__ import annotations
import importlib.util, sys, tempfile, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class Ctx:
    def __init__(self,home:Path,extra=None):
        self.home=home; self.extra=extra or {}; self.tools={}; self.hooks=[]; self.engine=None
    def get_config(self,key,default=None):
        values={"work_supervision_db":str(self.home/"work.db"),"remote_data_dir":str(self.home/"remote")}
        values.update(self.extra)
        return values.get(key,default)
    def register_tool(self,*,name,schema=None,handler=None,**kwargs): self.tools[name]=(schema,handler)
    def register_hook(self,name,callback): self.hooks.append((name,callback))
    def register_context_engine(self,engine): self.engine=engine

def load_plugin():
    spec=importlib.util.spec_from_file_location("nerve_modular_test_root",ROOT/"__init__.py",submodule_search_locations=[str(ROOT)])
    mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod);return mod

class ModuleAbsenceTests(unittest.TestCase):
    def test_lean_removes_qol_surfaces(self):
        with tempfile.TemporaryDirectory() as td:
            ctx=Ctx(Path(td),{"nerve_profile":"lean"})
            load_plugin().register(ctx)
            self.assertIn("nerve_decide",ctx.tools)
            self.assertIn("nerve_supervise_card",ctx.tools)
            self.assertIn("nerve_nervous_event",ctx.tools)
            self.assertNotIn("nerve_context_curate",ctx.tools)
            self.assertNotIn("nerve_remote_delegate_task",ctx.tools)
            self.assertNotIn("nerve_assistant",ctx.tools)
            self.assertIsNone(ctx.engine)

    def test_operator_removes_factory_and_remote_surfaces(self):
        with tempfile.TemporaryDirectory() as td:
            ctx=Ctx(Path(td),{"nerve_profile":"operator"})
            load_plugin().register(ctx)
            self.assertIn("nerve_context_curate",ctx.tools)
            self.assertIn("nerve_nervous_event",ctx.tools)
            self.assertNotIn("nerve_supervise_card",ctx.tools)
            self.assertNotIn("nerve_remote_delegate_task",ctx.tools)
            self.assertNotIn("nerve_assistant",ctx.tools)
            names={n for n,_ in ctx.hooks}
            self.assertNotIn("post_api_request",names)
            self.assertNotIn("api_request_error",names)
            self.assertIsNotNone(ctx.engine)

    def test_marie_kondo_is_minimal(self):
        with tempfile.TemporaryDirectory() as td:
            ctx=Ctx(Path(td),{"nerve_profile":"marie_kondo"})
            load_plugin().register(ctx)
            self.assertIn("nerve_decide",ctx.tools)
            self.assertIn("nerve_supervise_card",ctx.tools)
            self.assertIn("nerve_stats",ctx.tools)
            self.assertNotIn("nerve_nervous_event",ctx.tools)
            self.assertNotIn("nerve_context_curate",ctx.tools)
            self.assertNotIn("nerve_remote_delegate_task",ctx.tools)
            self.assertNotIn("nerve_assistant",ctx.tools)

    def test_fat_cat_has_assistant_but_remote_is_conditional(self):
        with tempfile.TemporaryDirectory() as td:
            ctx=Ctx(Path(td),{"nerve_profile":"fat_cat","remote_hosts":{}})
            load_plugin().register(ctx)
            self.assertIn("nerve_assistant",ctx.tools)
            self.assertIn("nerve_context_curate",ctx.tools)
            self.assertNotIn("nerve_remote_delegate_task",ctx.tools)

    def test_explicit_module_override_wins(self):
        with tempfile.TemporaryDirectory() as td:
            ctx=Ctx(Path(td),{"nerve_profile":"lean","nerve_modules":{"context_governor":True}})
            load_plugin().register(ctx)
            self.assertIn("nerve_context_curate",ctx.tools)
            self.assertIsNotNone(ctx.engine)
