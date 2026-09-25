# Nerve v0.2.2.dev4 setup

## Install

Install the plugin with the normal Hermes plugin flow, then validate registration:

```bash
hermes plugins doctor hermes-nerve --ci
```

Expected public surface: 8 tools, 7 hook names, and the optional `jev` ContextEngine.

## Provider

OpenRouter (live-tested historically in v0.1.x):

```bash
export OPENROUTER_API_KEY='...'
hermes config set plugins.entries.hermes-nerve.settings.jev_provider openrouter --force
hermes config set plugins.entries.hermes-nerve.settings.jev_model typesafe/jev-1.13 --force
```

Direct TypeSafe (wire-tested in v0.2.1.2; independently live-smoked on v0.2.1.1):

```bash
export TYPESAFE_API_KEY='...'
hermes config set plugins.entries.hermes-nerve.settings.jev_provider typesafe --force
hermes config set plugins.entries.hermes-nerve.settings.typesafe_model jev-latest --force
```

OpenCode Zen:

```bash
export OPENCODE_API_KEY='...'
hermes config set plugins.entries.hermes-nerve.settings.jev_provider opencode --force
hermes config set plugins.entries.hermes-nerve.settings.opencode_model jev-1.13 --force
```

OpenCode access in Nerve is paid-only. The `jev-1.13-free` tier is not supported because it does not work with Hermes.

Only the selected provider's credential is required.

## Nervous system defaults

```bash
hermes config set plugins.entries.hermes-nerve.settings.nervous_enabled true --force
hermes config set plugins.entries.hermes-nerve.settings.nervous_turn_admission true --force
hermes config set plugins.entries.hermes-nerve.settings.nervous_mode correct_next --force
hermes config set plugins.entries.hermes-nerve.settings.nervous_challenge_confidence 0.86 --force
hermes config set plugins.entries.hermes-nerve.settings.nervous_call_threshold 0.58 --force
```

The old synchronous pre-tool gate remains `off` by default. It is compatibility/special-purpose behavior, not the recommended v0.2 decision architecture.

## Manual structured events

Hermes/runtime integrations may call `nerve_nervous_event` to expose explicit accountable decisions. The event can include choices and `hermes_decision`, or a control-state event such as `RECOVERY`, `STRATEGY_CHANGE`, or `COMPLETION_CANDIDATE`.

## Telemetry

Inside Hermes:

```text
Call nerve_stats and return the nervous section.
```

Local files are profile-scoped under `$HERMES_HOME/jev/`, including nervous-event and decision-outcome JSONL ledgers.

## Personality/module setup

The new profile layer is deliberately separate from existing provider credentials and low-level tuning.

```bash
nerve setup --show
nerve setup --profile lean
nerve setup --profile operator
nerve setup --profile fat_cat
nerve setup --profile marie_kondo
```

Bare `nerve setup` opens the five-choice interactive selector. Full Configuration allows module-by-module selection. The sidecar is written atomically under the active Hermes home at:

```text
$HERMES_HOME/nerve/profile.json
```

If the sidecar is absent and no `nerve_profile` plugin setting exists, Nerve preserves current v0.2.3/Legacy registration behavior.

The module layer is resolved before plugin registration. A disabled module does not register its owned Hermes tool schemas or hooks. Important initial profile choices are:

- **Fat Cat:** Assistant + context/QoL features; Shared Context ON; remote workers only when hosts are configured.
- **Operator:** direct interactive Hermes; context/action supervision ON; Kanban/Assistant/remote-worker features OFF by default; Shared Context ON.
- **Lean:** work supervision + token trajectory + nervous/reflex core; QoL/context/remote/Assistant/Shared Context OFF pending evidence.
- **Marie Kondo:** Reflex + evidence/DoD/work completion + minimum receipts; most other modules OFF.

### Shared Context

Nerve only manages the external HermesContextBus plugin boundary.

```bash
nerve setup --explain
nerve setup --install-shared-context /path/to/HermesContextBus
```

After installation, run the printed Hermes Plugin Doctor command. Nerve does not integrate or own the WhatsApp bridge.

### Assistant module

When the `assistant_loops` module is enabled, Hermes gains `nerve_assistant`. Supported operations are install/disable/status, add/update/drop loop, and evidence-backed completion. The `assistant_audit` module adds recurring Reflex accountability advice. Turning audit off preserves persistent loops without per-turn audit calls.
