# Factory Audit — Nerve profiles and optional modules

**Status:** implementation-time audit for the profile/module PR  
**Baseline:** Nerve v0.2.3 (`faecfafe`)  
**Rule:** factory defaults are earned by measured value, not by feature availability.

## Existing evidence

The repository already establishes several factory facts:

- ordinary Kanban workers intentionally receive **zero Nerve tool schemas**;
- the healthy-run target is **<=2% fixed overhead**, with **<=0.5%** as the stretch target;
- the local ROI router is designed to remain silent on healthy work;
- completion combines deterministic local checks with bounded semantic review;
- `docs/DEV16_SESSION_FINDINGS.md` records healthy supervised runs at 376k, 484k, and 968k combined tokens;
- the same findings record one pathological 4.760M-token run;
- supervisor overhead in that cohort was about 1.5k tokens/run, so tail/loop control—not micro-optimizing the supervisor—is the main factory economic target;
- zero provider calls after verified PASS is a release invariant.

## v0.2.3 default-cost inventory

| Subsystem | v0.2.3 posture | Fixed/recurring cost concern | PR posture |
|---|---|---|---|
| Reflex typed decisions | available | provider calls when invoked | core substrate |
| Nervous turn supervision | ON | runtime + possible provider calls | ON Lean, OFF Marie Kondo |
| Work/DoD supervision | ON | runtime/storage + sparse provider calls | ON Lean + Marie Kondo |
| Token trajectory observer | ON | runtime + sparse provider calls | ON Lean; evidence-gated for Marie Kondo |
| Legacy action gate | mode OFF | synchronous/provider cost if enabled | OFF Lean/Marie Kondo |
| Context ledger | ON | disk writes + observation runtime | OFF Lean/Marie Kondo |
| ContextEngine registration | ON/shadow | runtime/compaction shadow work | OFF Lean/Marie Kondo |
| Remote worker tools | always exposed to controller | schema + SSH/runtime surface | module-gated |
| Local nervous learning | ON | disk/runtime | OFF Lean until measured |
| Shadow backend | configurable | duplicate provider/network cost | OFF all presets by default |
| Receipts | ON | bounded disk writes | minimal ON Lean/Marie Kondo |
| Assistant accountability | absent in v0.2.3 | prompt/provider/storage | Fat Cat only by default |
| Shared Context | external project | schema/prompt/storage | Fat Cat + Operator initially |

## Hard-OFF audit implemented by this PR

When a module is disabled, plugin registration now omits its owned model-facing surfaces instead of registering everything and hoping configuration keeps it quiet.

Profile tests prove:
- Lean omits context, remote-worker, and Assistant tools and does not register the Nerve ContextEngine.
- Operator omits work/Kanban, remote-worker, and Assistant tools.
- Marie Kondo omits nervous-event, context, remote-worker, action-gate, Assistant, and shadow/QoL surfaces.
- Fat Cat includes Assistant, but remote-worker schemas remain absent unless remote hosts are configured.
- headless Kanban workers continue to receive zero Nerve schemas.

## Decisions supported by current evidence

### Keep ON in Lean

**Work supervision / DoD / evidence / completion.**  
This is Nerve's strongest proven factory value: it prevents worker self-certification and supports controller-owned completion.

**Token trajectory.**  
The measured 4.760M-token pathological run and repo's existing tail-control design justify keeping trajectory supervision in the factory-oriented profile while benchmarking continues.

**Reflex core.**  
Required substrate for bounded semantic/completion decisions.

**Nervous supervision.**  
Kept in Lean because it is already architected for sparse, local-first routing; the factory benchmark must still verify its actual fixed/provider overhead under the new profile.

**Bounded receipts.**  
Retained for evidence/provenance and benchmarkability. This PR makes receipt persistence independently disableable.

### Keep OFF in Lean pending evidence

**Shared Context.**  
Plausible factory win: bounded handoffs may avoid expensive rediscovery across workers/orchestrators. There is not yet a live factory A/B proving net savings, so Lean remains OFF.

**Context governor.**  
Useful in long sessions, but no current factory ablation proves the ledger + shadow ContextEngine earn their runtime/storage cost in headless factory work.

**Action gate.**  
Useful for direct interactive/operator safety, but synchronous per-action supervision is not yet justified as a factory default.

**Remote workers.**  
Useful when explicitly configured, but unrelated factories should not pay schema/runtime tax.

**Assistant loops / audit.**  
QoL/digital-assistant features. Explicitly excluded from factory defaults.

**Local learning and shadow testing.**  
Valuable for calibration/development, but not required for production factory execution.

## New benchmark work required

The post-PR benchmark matrix must compare:
1. v0.2.3 legacy behavior;
2. Lean;
3. Marie Kondo;
4. Lean + Shared Context;
5. Lean + context governor;
6. Lean + action gate;
7. module-by-module ablations.

Record:
- tool-schema token footprint;
- injected prompt/context tokens;
- worker tokens;
- supervisor tokens;
- provider calls and cost;
- wall-clock;
- completion success;
- false PASS;
- duplicated investigation;
- restart/replacement recovery cost;
- useful intervention rate.

Shared Context may graduate to Lean only if bounded handoffs demonstrably save more duplicated/recovery work than they inject.

## Audit status

This PR completes the **static/default-surface audit and hard-OFF implementation**. It does **not** claim new live A/B results for Shared Context, context governor, or action gate. Those remain evidence-gated profile decisions.
