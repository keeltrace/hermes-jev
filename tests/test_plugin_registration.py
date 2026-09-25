from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

from hermes_nerve.provenance import VERSION

ROOT=Path(__file__).resolve().parents[1]


class FakeCtx:
    def __init__(self, home: Path):
        self.tools={}; self.hooks=[]; self.engine=None; self.home=home
    def get_config(self,key,default=None):
        overrides={
            "work_supervision_db": str(self.home/"work.db"),
            "remote_data_dir": str(self.home/"remote"),
        }
        return overrides.get(key,default)
    def register_tool(self,*,name,schema=None,handler=None,**kwargs): self.tools[name]=(schema,handler)
    def register_hook(self,name,callback): self.hooks.append((name,callback))
    def register_context_engine(self,engine): self.engine=engine


class RegistrationTests(unittest.TestCase):
    def load_plugin(self):
        spec=importlib.util.spec_from_file_location("hermes_nerve_plugin_root",ROOT/"__init__.py",submodule_search_locations=[str(ROOT)])
        mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod);return mod
    def test_version_and_tools_and_hooks(self):
        with tempfile.TemporaryDirectory() as td:
            mod=self.load_plugin();ctx=FakeCtx(Path(td));mod.register(ctx)
            self.assertEqual(VERSION,"0.2.3")
            self.assertEqual(len(ctx.tools),16)
            for name in ("nerve_decide","nerve_nervous_event","nerve_supervise_card","nerve_work_event","nerve_remote_delegate_task","nerve_remote_worker_control"):
                self.assertIn(name,ctx.tools)
            names={n for n,_ in ctx.hooks}
            self.assertEqual(names,{"pre_tool_call","post_tool_call","pre_llm_call","transform_tool_result","pre_verify","post_api_request","api_request_error","post_llm_call","on_session_end"})
            self.assertIsNotNone(ctx.engine)
            assess=ctx.tools["nerve_assess"][0]["parameters"]["properties"]["questions"]["additionalProperties"]["oneOf"]
            by_type={x["properties"]["type"]["enum"][0]:x for x in assess}
            self.assertEqual(by_type["choice"]["properties"]["criteria"]["minProperties"],2)
            self.assertEqual(by_type["score"]["properties"]["criteria"]["minItems"],2)
            for qtype in ("choice","score","noul"):
                self.assertIn("instructions",by_type[qtype]["required"])
            noul_criteria=by_type["noul"]["properties"]["criteria"]
            self.assertEqual(set(noul_criteria["required"]),{"true","false"})
            self.assertFalse(noul_criteria["additionalProperties"])


if __name__=="__main__":unittest.main()
