from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
import json
import os
from unittest.mock import patch
from pathlib import Path

from hermes_nerve.provenance import VERSION
from hermes_nerve import assistant
from hermes_nerve.client import JevResponse
from hermes_nerve.engine import DecisionEngine

ROOT=Path(__file__).resolve().parents[1]


class FakeCtx:
    def __init__(self, home: Path, extra=None):
        self.tools={}; self.hooks=[]; self.engine=None; self.home=home; self.extra=extra or {}
    def get_config(self,key,default=None):
        overrides={
            "work_supervision_db": str(self.home/"work.db"),
            "remote_data_dir": str(self.home/"remote"),
            "assistant_data_dir": str(self.home/"assistant"),
        }
        overrides.update(self.extra)
        return overrides.get(key,default)
    def register_tool(self,*,name,schema=None,handler=None,**kwargs): self.tools[name]=(schema,handler)
    def register_hook(self,name,callback): self.hooks.append((name,callback))
    def register_context_engine(self,engine): self.engine=engine


class _Provider:
    def __init__(self,value,confidence=.95): self.value=value; self.confidence=confidence; self.calls=0
    def system_one(self,*,state,questions,model=None):
        self.calls+=1; labels=list(questions["decision"]["criteria"]); probs={x:(self.confidence if x==self.value else (1-self.confidence)/(len(labels)-1)) for x in labels}
        return JevResponse(model="test",answers={"decision":{"choice":self.value,"confidence":self.confidence,"probabilities":probs}},usage={},latency_ms=1)


class RegistrationTests(unittest.TestCase):
    def load_plugin(self):
        spec=importlib.util.spec_from_file_location("hermes_nerve_plugin_root",ROOT/"__init__.py",submodule_search_locations=[str(ROOT)])
        mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod);return mod
    def test_version_and_tools_and_hooks(self):
        with tempfile.TemporaryDirectory() as td:
            mod=self.load_plugin();ctx=FakeCtx(Path(td));mod.register(ctx)
            self.assertEqual(VERSION,"0.2.3")
            self.assertEqual(len(ctx.tools),17)
            for name in ("nerve_decide","nerve_nervous_event","nerve_assistant","nerve_supervise_card","nerve_work_event","nerve_remote_delegate_task","nerve_remote_worker_control"):
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

    def test_assistant_public_lifecycle_restart_hook_and_headless_isolation(self):
        with tempfile.TemporaryDirectory() as td:
            home=Path(td); mod=self.load_plugin(); ctx=FakeCtx(home); mod.register(ctx)
            tool=ctx.tools["nerve_assistant"][1]
            self.assertTrue(json.loads(tool({"action":"install"}))["assistant"]["enabled"])
            created=json.loads(tool({"action":"add_loop","title":"Finish report","next":"run checks","definition_of_done":"checks pass"}))
            loop_id=created["assistant"]["id"]
            p=_Provider("NUDGE",.91); mod.assistant._engine_factory=lambda: DecisionEngine(p)
            pre_llm=dict(ctx.hooks)["pre_llm_call"]
            hint=pre_llm(user_message="continue")
            self.assertIn("NERVE ASSISTANT",hint); self.assertIn("REFLEX ACCOUNTABILITY REVIEW",hint); self.assertEqual(p.calls,1)
            p2=_Provider("PASS",.96); mod.assistant._engine_factory=lambda: DecisionEngine(p2)
            completed=json.loads(tool({"action":"complete","loop_id":loop_id,"evidence":{"checks":"pass"}}))
            self.assertTrue(completed["assistant"]["closed"]); self.assertEqual(completed["assistant"]["loop"]["state"],"done")
            mod.assistant._engine_factory=DecisionEngine
            ctx2=FakeCtx(home); mod.register(ctx2)
            status=json.loads(ctx2.tools["nerve_assistant"][1]({"action":"status"}))["assistant"]
            self.assertTrue(status["enabled"]); self.assertEqual(status["active_loop_count"],0); self.assertEqual(status["loop_count"],1)
            with patch.dict(os.environ,{"HERMES_KANBAN_TASK":"task-1"},clear=False):
                headless=FakeCtx(home,{"work_supervision_enabled":False,"work_headless_workers":True})
                mod.register(headless)
                self.assertNotIn("nerve_assistant",headless.tools)
                pre=dict(headless.hooks)["pre_llm_call"]
                out=pre(user_message="worker turn")
                self.assertTrue(out is None or "NERVE ASSISTANT" not in str(out))



if __name__=="__main__":unittest.main()
