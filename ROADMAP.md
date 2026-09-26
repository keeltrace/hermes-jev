# Roadmap

## v0.2.1.x — nervous-system control hardening

Implemented:

- asynchronous OFF/WATCH/ON turn admission
- structured event bus and explicit `nerve_nervous_event`
- local adaptive semantic router (no fixed-N polling primary trigger)
- decision-state hysteresis / lease reuse
- in-flight event batching
- confidence-gated challenges and stale-state rejection
- shadow / correct-next / precommit authority modes
- direct TypeSafe + OpenRouter transports, plus paid OpenCode Zen on the v0.2.2 development line
- local outcome dataset and historical relevance calibration seam
- nervous-system decision-quality telemetry in `nerve_stats`
- existing v0.1.x tools, selective gate, evidence ledger, rehydration, and ContextEngine compatibility
- repeated-failure fingerprints and local third-strike REPLAN loop breaker
- enforceable decision/control leases at the composed pre-tool seam
- stable decision-id attribution from decision -> delivery -> next action -> outcome
- repeat-failure provider-call deduplication and semantic lease reuse
- correlated gate-hook observations even when the legacy gate is disabled
- bounded/sectioned `nerve_stats` output with recent telemetry opt-in

External/live follow-up:

- calibrate turn admission and challenge confidence on real Hermes workloads
- collect enough labeled outcomes to assess the local historical relevance model
- continue collecting independent direct TypeSafe live-account interoperability reports across current releases
- measure useful-disagreement precision and false-PASS rate over long autonomous tasks
- pressure-test context anchoring/rehydration during real long-turn compaction
- collect long-session data for the v0.2.1.2 bounded-selection and fail-open context-engine path
- validate v0.2.2 completed-turn eviction under long-lived Hermes processes
- compare provider-reported cost coverage across OpenRouter, direct TypeSafe, and OpenCode without treating missing cost as zero

## vNext - profiles, factory-first defaults, and optional modules

Current product/configuration direction:

- `planning/nerve-setup-profiles-factory-audit/IMPLEMENTATION_PLAN.md`

This work adds `nerve setup`, Full Configuration plus Fat Cat/Operator/Lean/Marie Kondo profiles, a full factory-cost audit, hard-OFF module semantics, optional Shared Context integration, and a later rebase of Assistant Accountability behind optional module switches.

The existing vNext nervous-system plan remains historical engineering context and is not replaced by this plan.
