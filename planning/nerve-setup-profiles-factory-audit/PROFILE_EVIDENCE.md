# Profile Evidence Matrix

This file records why each default is currently ON or OFF. "Pending" means the profile intentionally chooses the conservative state until an A/B or ablation exists.

| Module | Fat Cat | Operator | Lean | Marie Kondo | Evidence / rationale |
|---|---:|---:|---:|---:|---|
| Reflex core | ON | ON | ON | ON | Typed review substrate for Nerve decisions/completion. |
| Nervous system | ON | ON | ON | OFF | Local-first/sparse architecture; Marie Kondo excludes until indispensable value is isolated. |
| Work supervision | ON | OFF | ON | ON | Strongest factory evidence: locked DoD, evidence, independent completion. |
| Token trajectory | ON | OFF | ON | ON | Tail-control evidence includes a measured 4.760M-token pathological run; keep in minimal factory profile for now. |
| Action gate | ON | ON | OFF | OFF | Interactive/operator value; factory value/cost ablation pending. |
| Context governor | ON | ON | OFF | OFF | Useful long-session feature; factory runtime/storage ablation pending. |
| Remote workers | conditional | OFF | OFF | OFF | Only useful with configured hosts; schema/runtime tax otherwise. |
| Shared Context | ON | ON | OFF | OFF | Existing 28-test implementation; factory token/recovery A/B pending. |
| Assistant loops | ON | OFF | OFF | OFF | Digital-assistant QoL, not factory core. |
| Assistant audit | ON | OFF | OFF | OFF | Recurring provider/prompt cost is appropriate only for opt-in assistant profile. |
| Shadow testing | OFF | OFF | OFF | OFF | Development/calibration duplicate-call cost. |
| Receipts | ON | ON | ON | ON | Bounded provenance/evidence; now independently disableable. |
| Local learning | ON | ON | OFF | OFF | Useful calibration data but not yet proven necessary for factory execution. |

## Promotion rule

A feature can move into Lean when it demonstrates either:
- meaningful net token/runtime savings, or
- material correctness/completion improvement that justifies its cost.

Marie Kondo uses a stronger test: removing the feature must measurably make Hermes worse.
