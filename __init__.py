"""Nerve plugin registration — v0.2.2 Nerve supervision and open Reflex backends."""
from __future__ import annotations

import logging
import os
from pathlib import Path

try:
    # Hermes plugin loader imports the plugin as a package. Relative imports are
    # required there because the plugin root itself is not added to sys.path.
    from .hermes_nerve import client, context, gate, ledger, nervous, receipts, schemas, tools
    from .hermes_nerve import reflex
    from .hermes_nerve.context_engine import NerveContextEngine
    from .hermes_nerve.provenance import VERSION
    from .hermes_nerve.remote import control as remote_control
    from .hermes_nerve.remote import runtime as remote_runtime
    from .hermes_nerve.remote import tools as remote_tools
    from .hermes_nerve.work import hooks as work_hooks
    from .hermes_nerve.work import runtime as work_runtime
    from .hermes_nerve.work import tools as work_tools
except ImportError:
    # Pytest and direct offline verification may import this file as bare
    # ``__init__``. Preserve that source-tree workflow without regressing the
    # real Hermes package-loader fix above.
    from hermes_nerve import client, context, gate, ledger, nervous, receipts, schemas, tools
    from hermes_nerve import reflex
    from hermes_nerve.context_engine import NerveContextEngine
    from hermes_nerve.provenance import VERSION
    from hermes_nerve.remote import control as remote_control
    from hermes_nerve.remote import runtime as remote_runtime
    from hermes_nerve.remote import tools as remote_tools
    from hermes_nerve.work import hooks as work_hooks
    from hermes_nerve.work import runtime as work_runtime
    from hermes_nerve.work import tools as work_tools

logger = logging.getLogger("hermes_nerve")


def register(ctx):
    is_kanban_worker = bool(
        str(os.getenv("HERMES_KANBAN_TASK") or os.getenv("HERMES_KANBAN_TASK_ID") or "").strip()
    )
    headless_worker = is_kanban_worker and bool(ctx.get_config("work_headless_workers", True))
    legacy_model = ctx.get_config("model_id", "typesafe/jev-1.13")
    client.configure(
        provider=ctx.get_config("jev_provider", "openrouter"),
        model=ctx.get_config("jev_model", legacy_model),
        typesafe_model=ctx.get_config("typesafe_model", "jev-latest"),
        opencode_model=ctx.get_config("opencode_model", "jev-1.13"),
        timeout=ctx.get_config("timeout_seconds", 10.0),
    )
    reflex.configure(
        backend=ctx.get_config("reflex_backend", "jev"),
        laya_base_url=ctx.get_config("reflex_laya_base_url", os.getenv("HERMES_REFLEX_LAYA_BASE_URL", "http://127.0.0.1:8765")),
        laya_model=ctx.get_config("reflex_laya_model", os.getenv("HERMES_REFLEX_LAYA_MODEL", "convaiinnovations/laya-typed-decisions")),
        laya_timeout_seconds=ctx.get_config("reflex_laya_timeout_seconds", os.getenv("HERMES_REFLEX_LAYA_TIMEOUT", 5.0)),
        laya_token=ctx.get_config("reflex_laya_token", os.getenv("HERMES_REFLEX_LAYA_TOKEN", "")),
        openjev_base_url=ctx.get_config("reflex_openjev_base_url", os.getenv("HERMES_REFLEX_OPENJEV_BASE_URL", "http://127.0.0.1:3000")),
        openjev_model=ctx.get_config("reflex_openjev_model", os.getenv("HERMES_REFLEX_OPENJEV_MODEL", "openjev")),
        openjev_timeout_seconds=ctx.get_config("reflex_openjev_timeout_seconds", os.getenv("HERMES_REFLEX_OPENJEV_TIMEOUT", 10.0)),
        openjev_token=ctx.get_config("reflex_openjev_token", os.getenv("HERMES_REFLEX_OPENJEV_TOKEN", "")),
        openjev_expected_identity=ctx.get_config("reflex_openjev_expected_identity", os.getenv("HERMES_REFLEX_OPENJEV_EXPECTED_IDENTITY", "")),
        shadow_backend=ctx.get_config("reflex_shadow_backend", "laya"),
        shadow_async=ctx.get_config("reflex_shadow_async", True),
        shadow_log=ctx.get_config("reflex_shadow_log", ""),
    )
    gate.configure(
        mode=ctx.get_config("gate_mode", "off"),
        min_confidence=ctx.get_config("min_confidence", 0.80),
        min_allow_probability=ctx.get_config("min_allow_probability", os.getenv("HERMES_NERVE_MIN_ALLOW_PROBABILITY", 0.90)),
        scope=ctx.get_config("gate_scope", "selective"),
    )
    receipts.configure(detail=ctx.get_config("receipt_detail", "hash"))
    ledger.configure(
        enabled=ctx.get_config("context_ledger_enabled", True),
        detail=ctx.get_config("context_ledger_detail", "sanitized"),
    )
    nervous.configure(
        enabled=ctx.get_config("nervous_enabled", True),
        admission_enabled=ctx.get_config("nervous_turn_admission", True),
        mode=ctx.get_config("nervous_mode", "correct_next"),
        challenge_confidence=ctx.get_config("nervous_challenge_confidence", 0.86),
        call_threshold=ctx.get_config("nervous_call_threshold", 0.58),
        max_provider_calls_per_turn=ctx.get_config("nervous_max_provider_calls_per_turn", 96),
        event_preview_chars=ctx.get_config("nervous_event_preview_chars", 1200),
        retain_recent_events=ctx.get_config("nervous_retain_recent_events", 64),
        emit_prompt_hint=ctx.get_config("nervous_emit_prompt_hint", False),
        local_learning=ctx.get_config("nervous_local_learning", True),
        local_learning_min_samples=ctx.get_config("nervous_local_learning_min_samples", 8),
        repeated_failure_local_replan_at=ctx.get_config("nervous_repeated_failure_local_replan_at", 3),
    )
    context.configure(
        preview_chars=ctx.get_config("context_preview_chars", 1200),
        anchor_chars=ctx.get_config("context_anchor_chars", 220),
        preserve_tail=ctx.get_config("context_preserve_tail", 4),
        mode=ctx.get_config("context_curation_mode", "shadow"),
        drop_max_needed=ctx.get_config("context_drop_max_needed", 0.20),
        drop_max_exact=ctx.get_config("context_drop_max_exact", 0.20),
        drop_min_superseded=ctx.get_config("context_drop_min_superseded", 0.75),
        anchor_max_needed=ctx.get_config("context_anchor_max_needed", 0.55),
        anchor_max_exact=ctx.get_config("context_anchor_max_exact", 0.45),
        conflict_pin_min=ctx.get_config("context_conflict_pin_min", 0.70),
    )
    # dev11: retain Hermes' supported in-process tool dispatcher so a passing
    # pre_verify gate can complete the owning Kanban run without another model turn.
    # Older/offline test contexts may not expose dispatch_tool; fail closed there.
    work_runtime.set_tool_dispatcher(getattr(ctx, "dispatch_tool", None))
    work_runtime.configure(
        enabled=ctx.get_config("work_supervision_enabled", True),
        mode=ctx.get_config("work_supervision_mode", "advisory"),
        store_path=ctx.get_config("work_supervision_db", ""),
        preview_chars=ctx.get_config("work_evidence_preview_chars", 1200),
        calibration_min_samples=ctx.get_config("work_calibration_min_samples", 12),
        calibration_max_brier=ctx.get_config("work_calibration_max_brier", 0.24),
        enforcement_override=ctx.get_config("work_enforcement_override", False),
        control_confidence=ctx.get_config("work_control_confidence", 0.86),
        reviewer=ctx.get_config("work_reviewer", ""),
        auto_bind_kanban=ctx.get_config("work_auto_bind_kanban", True),
        headless_workers=ctx.get_config("work_headless_workers", True),
        default_task_budget_tokens=ctx.get_config("work_default_task_budget_tokens", 70000),
        checkpoint_fractions=ctx.get_config("work_checkpoint_fractions", "0.40,0.70"),
        supervisor_budget_fraction=ctx.get_config("work_supervisor_budget_fraction", 0.03),
        roi_min_expected_savings_tokens=ctx.get_config("work_roi_min_expected_savings_tokens", 1500),
        provider_decision_cooldown_tokens=ctx.get_config("work_provider_decision_cooldown_tokens", 8000),
        estimated_decision_call_tokens=ctx.get_config("work_estimated_decision_call_tokens", ctx.get_config("work_estimated_jev_call_tokens", 800)),
        estimated_jev_call_tokens=ctx.get_config("work_estimated_jev_call_tokens", 800),
        provider_decisions_enabled=ctx.get_config("work_provider_decisions_enabled", True),
        directive_high_confidence=ctx.get_config("work_directive_high_confidence", 0.90),
        directive_watch_confidence=ctx.get_config("work_directive_watch_confidence", 0.75),
        repeated_failure_trigger=ctx.get_config("work_repeated_failure_trigger", 2),
        directive_max_chars=ctx.get_config("work_directive_max_chars", 320),
        completion_controller_attempts=ctx.get_config("work_completion_controller_attempts", 3),
        auto_estimate_task_budget=ctx.get_config("work_auto_estimate_task_budget", True),
        budget_dod_required=ctx.get_config("work_budget_dod_required", True),
        budget_dod_tolerance=ctx.get_config("work_budget_dod_tolerance", 1.10),
        budget_estimator_base_tokens=ctx.get_config("work_budget_estimator_base_tokens", 120000),
        budget_estimator_per_criterion_tokens=ctx.get_config("work_budget_estimator_per_criterion_tokens", 75000),
        budget_estimator_body_char_factor=ctx.get_config("work_budget_estimator_body_char_factor", 25.0),
        budget_estimator_safety_multiplier=ctx.get_config("work_budget_estimator_safety_multiplier", 1.25),
        budget_estimator_max_tokens=ctx.get_config("work_budget_estimator_max_tokens", 2000000),
        nerve_observer_enabled=ctx.get_config("work_nerve_observer_enabled", True),
        nerve_auto_kill=ctx.get_config("work_nerve_auto_kill", True),
        nerve_watch_fraction=ctx.get_config("work_nerve_watch_fraction", 0.65),
        nerve_replan_fraction=ctx.get_config("work_nerve_replan_fraction", 0.90),
        nerve_hard_budget_multiplier=ctx.get_config("work_nerve_hard_budget_multiplier", 1.75),
        nerve_min_calls_before_kill=ctx.get_config("work_nerve_min_calls_before_kill", 12),
        nerve_repeated_failure_kill=ctx.get_config("work_nerve_repeated_failure_kill", 3),
        nerve_high_context_streak_kill=ctx.get_config("work_nerve_high_context_streak_kill", 3),
    )
    # dev7: establish the exact Kanban run + locked DoD before the worker's
    # first provider call. This is local-only and therefore adds no LLM/token
    # overhead. Later hooks refresh the session id but do not own bootstrap.
    startup_identity = None
    if headless_worker and work_runtime.enabled():
        startup_identity = work_hooks.bootstrap_kanban_worker()

    remote_runtime.configure(
        hosts=ctx.get_config("remote_hosts", {}),
        default_host=ctx.get_config("remote_default_host", ""),
        default_max_turns=ctx.get_config("remote_default_max_turns", 100),
        default_task_timeout_seconds=ctx.get_config("remote_default_task_timeout_seconds", 3600),
        data_dir=ctx.get_config("remote_data_dir", ""),
    )

    registrations = [
        ("nerve_decide", schemas.NERVE_DECIDE, tools.nerve_decide),
        ("nerve_rank", schemas.NERVE_RANK, tools.nerve_rank),
        ("nerve_verify", schemas.NERVE_VERIFY, tools.nerve_verify),
        ("nerve_assess", schemas.NERVE_ASSESS, tools.nerve_assess),
        ("nerve_context_curate", schemas.NERVE_CONTEXT_CURATE, tools.nerve_context_curate),
        ("nerve_context_rehydrate", schemas.NERVE_CONTEXT_REHYDRATE, tools.nerve_context_rehydrate),
        ("nerve_stats", schemas.NERVE_STATS, tools.nerve_stats),
        ("nerve_nervous_event", schemas.NERVE_NERVOUS_EVENT, tools.nerve_nervous_event),
        ("nerve_supervise_card", schemas.NERVE_SUPERVISE_CARD, work_tools.nerve_supervise_card),
        ("nerve_work_event", schemas.NERVE_WORK_EVENT, work_tools.nerve_work_event),
        ("nerve_work_status", schemas.NERVE_WORK_STATUS, work_tools.nerve_work_status),
        ("nerve_remote_delegate_task", schemas.NERVE_REMOTE_DELEGATE_TASK, remote_tools.nerve_remote_delegate_task),
        ("nerve_remote_worker_status", schemas.NERVE_REMOTE_WORKER_STATUS, remote_tools.nerve_remote_worker_status),
        ("nerve_remote_worker_result", schemas.NERVE_REMOTE_WORKER_RESULT, remote_tools.nerve_remote_worker_result),
        ("nerve_remote_worker_cancel", schemas.NERVE_REMOTE_WORKER_CANCEL, remote_tools.nerve_remote_worker_cancel),
        ("nerve_remote_worker_control", schemas.NERVE_REMOTE_WORKER_CONTROL, remote_tools.nerve_remote_worker_control),
    ]
    # Controller/admin sessions retain the full Nerve surface. Ordinary Kanban
    # workers are deliberately headless: exposing these schemas was the largest
    # fixed token cost in the first A/B benchmark and encouraged the worker to
    # spend turns operating its own supervisor.
    if not headless_worker:
        for name, schema, handler in registrations:
            ctx.register_tool(name=name, toolset="nerve", schema=schema, handler=handler)

    def _pre_tool_control(**kwargs):
        callbacks = (remote_control.pre_tool_call, work_hooks.pre_tool_call)
        if not headless_worker:
            callbacks += (nervous.pre_tool_call, gate.pre_tool_call)
        for callback in callbacks:
            directive = callback(**kwargs)
            if directive is not None:
                return directive
        return None

    def _pre_llm(**kwargs):
        work_result = work_hooks.pre_llm_call(**kwargs)
        if headless_worker:
            return work_result
        nervous_result = nervous.pre_llm_call(**kwargs)
        return work_result if work_result is not None else nervous_result

    def _transform_tool_result(**kwargs):
        work_result = work_hooks.transform_tool_result(**kwargs)
        if work_result is not None:
            return work_result
        if not headless_worker:
            return nervous.transform_tool_result(**kwargs)
        return None

    def _post_llm(**kwargs):
        work_hooks.post_llm_call(**kwargs)
        if not headless_worker:
            nervous.post_llm_call(**kwargs)

    def _session_end(**kwargs):
        work_hooks.on_session_end(**kwargs)
        if not headless_worker:
            nervous.on_session_end(**kwargs)

    ctx.register_hook("pre_tool_call", _pre_tool_control)
    ctx.register_hook("post_tool_call", work_hooks.post_tool_call)
    if not headless_worker:
        ctx.register_hook("post_tool_call", ledger.observe_tool_call)
        ctx.register_hook("post_tool_call", nervous.post_tool_call)
    ctx.register_hook("pre_llm_call", _pre_llm)
    ctx.register_hook("transform_tool_result", _transform_tool_result)
    ctx.register_hook("pre_verify", work_hooks.pre_verify if headless_worker else nervous.pre_verify)
    ctx.register_hook("post_api_request", work_hooks.post_api_request)
    ctx.register_hook("api_request_error", work_hooks.api_request_error)
    ctx.register_hook("post_llm_call", _post_llm)
    ctx.register_hook("on_session_end", _session_end)

    if not headless_worker and bool(ctx.get_config("context_engine_register", True)) and hasattr(ctx, "register_context_engine"):
        ctx.register_context_engine(NerveContextEngine(
            mode=ctx.get_config("context_engine_mode", "shadow"),
            threshold_percent=ctx.get_config("context_engine_threshold_percent", 0.72),
            protect_first_n=ctx.get_config("context_engine_protect_first_n", 3),
            protect_last_n=ctx.get_config("context_engine_protect_last_n", 6),
            shadow_trigger_percent=ctx.get_config("context_engine_shadow_trigger_percent", 0.55),
            fallback_builtin=ctx.get_config("context_engine_fallback_builtin", True),
        ))
    logger.info(
        "Nerve %s loaded from %s; tools=%d headless_worker=%s work_supervision=%s",
        VERSION, Path(__file__).resolve().parent, 0 if headless_worker else len(registrations), headless_worker,
        ctx.get_config("work_supervision_enabled", True),
    )
    if headless_worker:
        if startup_identity is not None:
            logger.info(
                "Nerve headless supervision bound at startup: task=%s run=%s contract=%s",
                startup_identity.task_id, startup_identity.run_id, startup_identity.contract_hash[:12],
            )
        else:
            message = (
                "Nerve headless supervision did not bind at startup; inspect supervision_diagnostics "
                "before treating this run as a valid Nerve-supervised measurement"
            )
            if os.getenv("HERMES_NERVE_OFFLINE_VERIFY") == "1":
                logger.info("%s (offline verifier: not applicable)", message)
            else:
                logger.warning(message)
