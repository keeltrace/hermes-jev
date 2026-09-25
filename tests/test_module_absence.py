from __future__ import annotations
import importlib.util, os, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]

class Ctx:
    def __init__(self,home:Path,extra=None):
        self.home=home; self.extra=extra or {}; self.tools={}; self.hooks=[]; self.engine=None
    def get_config(self,key,default=None):
        values={"work_supervision_db":str(self.home/"work.db"),"remote_data_dir":str(self.home/"remote")}; values.update(self.extra); return values.get(key,default)
    def register_tool(self,*,name,schema=None,handler=None,**kwargs): self.tools[name]=(schema,handler)
    def register_hook(self,name,callback): self.hooks.append((name,callback))
    def register_context_engine(self,engine): self.engine=engine

def load_plugin():
    spec=importlib.util.spec_from_file_location("nerve_modular_test_root",ROOT/"__init__.py",submodule_search_locations=[str(ROOT)])
    mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod);return mod

class ModuleAbsenceTests(unittest.TestCase):
    def register(self, profile, extra=None):
        td=tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
        env=patch.dict(os.environ,{"HERMES_HOME":td.name},clear=False); env.start(); self.addCleanup(env.stop)
        mod=load_plugin(); values={"nerve_profile":profile}; values.update(extra or {}); ctx=Ctx(Path(td.name),values); mod.register(ctx); return mod,ctx

    def test_lean_removes_qol_surfaces_and_hooks(self):
        mod,ctx=self.register("lean")
        self.assertIn("nerve_supervise_card",ctx.tools); self.assertIn("nerve_nervous_event",ctx.tools)
        self.assertNotIn("nerve_context_curate",ctx.tools); self.assertNotIn("nerve_remote_delegate_task",ctx.tools); self.assertNotIn("nerve_assistant",ctx.tools)
        self.assertIsNone(ctx.engine)
        self.assertFalse(any(cb is mod.ledger.observe_tool_call for _,cb in ctx.hooks))
        self.assertFalse(any(cb is mod.gate.pre_tool_call for _,cb in ctx.hooks))

    def test_operator_removes_factory_and_remote_surfaces(self):
        _,ctx=self.register("operator")
        self.assertIn("nerve_context_curate",ctx.tools); self.assertIn("nerve_nervous_event",ctx.tools)
        self.assertNotIn("nerve_supervise_card",ctx.tools); self.assertNotIn("nerve_remote_delegate_task",ctx.tools); self.assertNotIn("nerve_assistant",ctx.tools)
        names={n for n,_ in ctx.hooks}; self.assertNotIn("post_api_request",names); self.assertNotIn("api_request_error",names); self.assertIsNotNone(ctx.engine)

    def test_marie_kondo_is_minimal_and_has_no_nervous_or_context_hooks(self):
        mod,ctx=self.register("marie_kondo")
        self.assertIn("nerve_decide",ctx.tools); self.assertIn("nerve_supervise_card",ctx.tools); self.assertIn("nerve_stats",ctx.tools)
        self.assertNotIn("nerve_nervous_event",ctx.tools); self.assertNotIn("nerve_context_curate",ctx.tools); self.assertNotIn("nerve_remote_delegate_task",ctx.tools); self.assertNotIn("nerve_assistant",ctx.tools)
        self.assertIsNone(ctx.engine)
        self.assertFalse(any(cb is mod.nervous.post_tool_call for _,cb in ctx.hooks))
        self.assertFalse(any(cb is mod.ledger.observe_tool_call for _,cb in ctx.hooks))

    def test_fat_cat_uses_existing_event_tool_for_assistant_and_remote_is_conditional(self):
        _,ctx=self.register("fat_cat",{"remote_hosts":{}})
        self.assertIn("nerve_nervous_event",ctx.tools); self.assertIn("nerve_context_curate",ctx.tools)
        self.assertNotIn("nerve_assistant",ctx.tools); self.assertNotIn("nerve_remote_delegate_task",ctx.tools)
        self.assertIn("pre_llm_call",{n for n,_ in ctx.hooks})

    def test_explicit_module_override_wins(self):
        _,ctx=self.register("lean",{"nerve_modules":{"context_governor":True}})
        self.assertIn("nerve_context_curate",ctx.tools); self.assertIsNotNone(ctx.engine)
