import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from hermes_nerve import client, engine, nervous, provenance, schemas, tools


class CountingProvider:
    def __init__(self, *, request_id="req-patch", answer_choice="SAFE"):
        self.calls = 0
        self.request_id = request_id
        self.answer_choice = answer_choice

    def system_one(self, *, state, questions, model=None):
        self.calls += 1
        answers = {}
        for name, question in questions.items():
            qtype = question.get("type")
            if qtype == "choice":
                labels = list((question.get("criteria") or {}).keys())
                choice = self.answer_choice if self.answer_choice in labels else labels[0]
                answers[name] = {
                    "type": "choice",
                    "choice": choice,
                    "confidence": 0.91,
                    "probabilities": {label: (0.91 if label == choice else 0.09 / max(1, len(labels) - 1)) for label in labels},
                }
            elif qtype == "score":
                answers[name] = {"type": "score", "score": 1, "probabilities": [0.1, 0.9]}
            else:
                answers[name] = {"type": "noul", "noul": 0.91}
        return client.JevResponse(
            model="jev-patch-test",
            answers=answers,
            usage={"input_tokens": 11, "output_tokens": 3, "cost": 0.00001},
            latency_ms=7.5,
            request_id=self.request_id,
            provider="TypeSafe",
        )


class NoopNervousEngine:
    calls = []

    def __init__(self):
        pass

    @classmethod
    def reset(cls):
        cls.calls = []

    def decide(self, **kwargs):
        self.__class__.calls.append(("decide", kwargs))
        raise AssertionError("Jev-internal observation must not reach nervous provider")

    def assess(self, **kwargs):
        self.__class__.calls.append(("assess", kwargs))
        raise AssertionError("Jev-internal observation must not reach nervous provider")


class Patch0211Tests(unittest.TestCase):
    def test_deferred_nerve_assess_schema_exposes_runtime_choice_and_score_constraints(self):
        questions = schemas.NERVE_ASSESS["parameters"]["properties"]["questions"]
        self.assertEqual(questions["minProperties"], 1)
        variants = questions["additionalProperties"]["oneOf"]
        by_type = {variant["properties"]["type"]["enum"][0]: variant for variant in variants}
        self.assertEqual(set(by_type), {"choice", "score", "noul"})
        self.assertEqual(by_type["choice"]["properties"]["criteria"]["minProperties"], 2)
        self.assertIn("criteria", by_type["choice"]["required"])
        self.assertEqual(by_type["score"]["properties"]["criteria"]["minItems"], 2)
        self.assertIn("criteria", by_type["score"]["required"])
        self.assertNotIn("criteria", by_type["noul"]["required"])
        for qtype in ("choice", "score", "noul"):
            self.assertIn("instructions", by_type[qtype]["required"])
        noul_criteria = by_type["noul"]["properties"]["criteria"]
        self.assertEqual(set(noul_criteria["properties"]), {"true", "false"})
        self.assertEqual(set(noul_criteria["required"]), {"true", "false"})
        self.assertFalse(noul_criteria["additionalProperties"])

    def test_valid_choice_reaches_provider_once_and_invalid_choice_stays_local(self):
        provider = CountingProvider()
        with tempfile.TemporaryDirectory() as td, patch.dict(os.environ, {"HERMES_NERVE_RECEIPTS": str(Path(td) / "r.jsonl")}, clear=False):
            runtime = engine.DecisionEngine(provider)
            result = runtime.assess(
                state={"candidate": "cache.tmp"},
                questions={
                    "is_disposable": {
                        "type": "choice",
                        "instructions": "Classify candidate.",
                        "criteria": {"SAFE": "Evidence supports deletion", "KEEP": "Retain it"},
                    }
                },
                contract="patch/schema/v1",
            )
            self.assertEqual(provider.calls, 1)
            self.assertTrue(result["receipt_id"].startswith("jevrec-"))
            self.assertEqual(result["provenance_status"], provenance.VERIFIED)
            with self.assertRaisesRegex(ValueError, "at least two criteria labels"):
                runtime.assess(
                    state={},
                    questions={"is_disposable": {"type": "choice", "instructions": "Classify candidate.", "criteria": {"SAFE": "only one"}}},
                )
            self.assertEqual(provider.calls, 1, "invalid input must not call the provider")

    def test_assess_rejects_provider_invalid_shapes_locally(self):
        provider = CountingProvider()
        runtime = engine.DecisionEngine(provider)

        with self.assertRaisesRegex(ValueError, "question 'missing' requires instructions"):
            runtime.assess(
                state={},
                questions={"missing": {"type": "noul"}},
            )

        with self.assertRaisesRegex(ValueError, "noul question 'alias' criteria must contain exactly 'true' and 'false' keys"):
            runtime.assess(
                state={},
                questions={
                    "alias": {
                        "type": "noul",
                        "instructions": "Is this true?",
                        "criteria": {"yes": "yes", "no": "no"},
                    }
                },
            )

        with self.assertRaisesRegex(ValueError, "noul question 'bad_value' criteria.true must be JSON-compatible text/context"):
            runtime.assess(
                state={},
                questions={
                    "bad_value": {
                        "type": "noul",
                        "instructions": "Is this true?",
                        "criteria": {"true": None, "false": "no"},
                    }
                },
            )

        self.assertEqual(provider.calls, 0, "provider-invalid questions must fail before network/provider work")

    def test_deferred_assess_public_tool_rejects_invalid_and_accepts_valid_16_batch(self):
        provider = CountingProvider()
        runtime = engine.DecisionEngine(provider)
        questions = {
            f"q{i:02d}": {
                "type": "noul",
                "instructions": f"Evaluate item {i}.",
                "criteria": {"true": "yes", "false": "no"},
            }
            for i in range(16)
        }
        original = tools._engine_factory
        tools._engine_factory = lambda: runtime
        try:
            missing = json.loads(tools.nerve_assess(
                {"state": {}, "questions": {"missing": {"type": "noul"}}}
            ))
            self.assertFalse(missing["ok"])
            self.assertEqual(missing["error"], "question 'missing' requires instructions")
            self.assertEqual(provider.calls, 0)

            aliases = json.loads(tools.nerve_assess({
                "state": {},
                "questions": {
                    "alias": {
                        "type": "noul",
                        "instructions": "Is this true?",
                        "criteria": {"yes": "yes", "no": "no"},
                    }
                },
            }))
            self.assertFalse(aliases["ok"])
            self.assertIn("exactly 'true' and 'false' keys", aliases["error"])
            self.assertEqual(provider.calls, 0)

            with tempfile.TemporaryDirectory() as td, patch.dict(
                os.environ, {"HERMES_NERVE_RECEIPTS": str(Path(td) / "r.jsonl")}, clear=False
            ):
                result = json.loads(tools.nerve_assess({
                    "state": {"batch": "synthetic"},
                    "questions": questions,
                    "contract": "issue-8/valid-16/v1",
                }))
                self.assertTrue(result["ok"])
                self.assertEqual(provider.calls, 1)
                self.assertEqual(len(result["answers"]), 16)
                self.assertTrue(result["receipt_id"].startswith("jevrec-"))
                self.assertTrue((Path(td) / "r.jsonl").exists())
        finally:
            tools._engine_factory = original

    def test_jev_internal_failure_is_recorded_and_never_remotely_supervised(self):
        NoopNervousEngine.reset()
        with tempfile.TemporaryDirectory() as td, patch.dict(os.environ, {
            "HERMES_NERVE_NERVOUS_EVENTS": str(Path(td) / "nervous.jsonl"),
            "HERMES_NERVE_OUTCOMES": str(Path(td) / "outcomes.jsonl"),
        }, clear=False):
            system = nervous.NervousSystem(engine_factory=NoopNervousEngine)
            system.configure(enabled=True, admission_enabled=False, mode="correct_next")
            system.start_turn(user_message="verify candidates", session_id="s1", turn_id="t1")
            result = system.observe_tool_call(
                tool_name="nerve_assess",
                args={"questions": {"bad": {"type": "choice"}}},
                status="error",
                error_message="choice question requires at least two criteria labels",
                result="tool error",
                tool_call_id="jev-call-1",
                session_id="s1",
                turn_id="t1",
            )
            self.assertFalse(result["forwarded"])
            self.assertEqual(result["reason"], "nerve-internal")
            self.assertEqual(NoopNervousEngine.calls, [])
            metrics = system.report()["metrics"]
            self.assertEqual(metrics.get("nerve_internal_seen"), 1)
            self.assertEqual(metrics.get("nerve_internal_suppressed"), 1)
            quality = system.quality_metrics()
            self.assertEqual(quality["nerve_internal_events_suppressed"], 1)
            self.assertNotIn("nerve_assess", quality["provider_calls_by_origin"])

    def test_valid_explicit_jev_call_does_not_self_amplify_after_post_tool_observation(self):
        direct_provider = CountingProvider()
        NoopNervousEngine.reset()
        with tempfile.TemporaryDirectory() as td, patch.dict(os.environ, {
            "HERMES_NERVE_RECEIPTS": str(Path(td) / "receipts.jsonl"),
            "HERMES_NERVE_NERVOUS_EVENTS": str(Path(td) / "nervous.jsonl"),
            "HERMES_NERVE_OUTCOMES": str(Path(td) / "outcomes.jsonl"),
        }, clear=False):
            result = engine.DecisionEngine(direct_provider).assess(
                state={"candidate": "cache.tmp"},
                questions={"safe": {"type": "choice", "instructions": "Classify candidate.", "criteria": {"SAFE": "yes", "KEEP": "no"}}},
            )
            self.assertEqual(direct_provider.calls, 1)
            system = nervous.NervousSystem(engine_factory=NoopNervousEngine)
            system.configure(enabled=True, admission_enabled=False)
            system.start_turn(user_message="verify", session_id="s1", turn_id="t1")
            observed = system.observe_tool_call(
                tool_name="nerve_assess", args={}, status="success", result=json.dumps(result),
                tool_call_id="jev-call-ok", session_id="s1", turn_id="t1",
            )
            self.assertFalse(observed["forwarded"])
            self.assertEqual(direct_provider.calls, 1)
            self.assertEqual(NoopNervousEngine.calls, [])

    def test_remote_decide_rank_assess_verify_are_receipt_backed(self):
        provider = CountingProvider()
        with tempfile.TemporaryDirectory() as td, patch.dict(os.environ, {"HERMES_NERVE_RECEIPTS": str(Path(td) / "r.jsonl")}, clear=False):
            runtime = engine.DecisionEngine(provider)
            results = [
                runtime.decide(state={"n": 1}, instructions="choose", choices=["SAFE", "KEEP"]).as_dict(),
                runtime.rank(state={"n": 2}, instructions="rank", items={"SAFE": "safe", "KEEP": "keep"}),
                runtime.assess(state={"n": 3}, questions={"q": {"type": "choice", "instructions": "choose", "criteria": {"SAFE": "safe", "KEEP": "keep"}}}),
                runtime.verify(state={"n": 4}, instructions="verify").as_dict(),
            ]
            self.assertEqual(provider.calls, 4)
            for result in results:
                self.assertEqual(result["provenance_status"], provenance.VERIFIED)
                self.assertTrue(result["receipt_id"].startswith("jevrec-"))
                self.assertEqual(result["provenance"]["receipt_id"], result["receipt_id"])
                self.assertTrue(result["provenance"]["subject_sha256"])
                self.assertTrue(result["provenance"]["result_sha256"])
                self.assertEqual(result["execution"]["provenance_status"], provenance.VERIFIED)
            receipts_on_disk = [json.loads(line) for line in (Path(td) / "r.jsonl").read_text().splitlines()]
            self.assertEqual(len(receipts_on_disk), 4)
            self.assertEqual({r["receipt_id"] for r in receipts_on_disk}, {r["receipt_id"] for r in results})

    def test_provider_without_request_id_is_still_auditable_by_receipt(self):
        provider = CountingProvider(request_id="")
        with tempfile.TemporaryDirectory() as td, patch.dict(os.environ, {"HERMES_NERVE_RECEIPTS": str(Path(td) / "r.jsonl")}, clear=False):
            result = engine.DecisionEngine(provider).decide(
                state={"x": 1}, instructions="choose", choices=["SAFE", "KEEP"]
            ).as_dict()
            self.assertEqual(result["request_id"], "")
            self.assertTrue(result["receipt_id"].startswith("jevrec-"))
            self.assertEqual(result["provenance_status"], provenance.VERIFIED)


    def test_provider_error_and_stale_result_are_not_verified(self):
        class FailingProvider:
            def system_one(self, **kwargs):
                raise RuntimeError("provider unavailable")

        runtime = engine.DecisionEngine(FailingProvider())
        with tempfile.TemporaryDirectory() as td, patch.dict(os.environ, {"HERMES_NERVE_RECEIPTS": str(Path(td) / "r.jsonl")}, clear=False):
            with patch.object(tools, "_engine_factory", lambda: runtime):
                provider_error = json.loads(tools.nerve_verify({"state": {}, "instructions": "verify"}))
            self.assertFalse(provider_error["ok"])
            self.assertEqual(provider_error["provenance_status"], provenance.ERROR)
            self.assertFalse((Path(td) / "r.jsonl").exists())

        stale = json.loads(tools._ok({
            "value": "PASS",
            "request_id": "req-old",
            "receipt_id": "jevrec-old",
            "provider": "TypeSafe",
            "model": "jev-test",
            "contract": "verify/v1",
            "stale": True,
            "execution": provenance.execution_provenance(
                live_provider_call=True, request_id="req-old", receipt_id="jevrec-old"
            ),
        }))
        self.assertEqual(stale["provenance_status"], provenance.UNVERIFIED)
        self.assertEqual(stale["execution"]["provenance_status"], provenance.UNVERIFIED)
        self.assertTrue(stale["provenance"]["stale"])

    def test_error_and_local_results_cannot_present_as_verified(self):
        error = json.loads(tools.nerve_assess({"questions": {"q": {"type": "choice", "criteria": {"only": "x"}}}}))
        self.assertFalse(error["ok"])
        self.assertEqual(error["provenance_status"], provenance.ERROR)
        self.assertFalse(error["execution"]["live_provider_call"])
        self.assertEqual(error["execution"]["provenance_status"], provenance.ERROR)

        with tempfile.TemporaryDirectory() as td, patch.dict(os.environ, {
            "HERMES_NERVE_RECEIPTS": str(Path(td) / "r.jsonl"),
            "HERMES_NERVE_GATE_EVENTS": str(Path(td) / "g.jsonl"),
            "HERMES_NERVE_CONTEXT_LEDGER": str(Path(td) / "c.jsonl"),
            "HERMES_NERVE_NERVOUS_EVENTS": str(Path(td) / "n.jsonl"),
            "HERMES_NERVE_OUTCOMES": str(Path(td) / "o.jsonl"),
        }, clear=False):
            local = json.loads(tools.nerve_stats({"section": "summary"}))
            self.assertEqual(local["provenance_status"], provenance.LOCAL_ONLY)
            self.assertEqual(local["execution"]["provenance_status"], provenance.LOCAL_ONLY)


if __name__ == "__main__":
    unittest.main()
