"""Resolve Nerve personalities without initializing providers or runtimes."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

from .modules import MODULES
from .profiles import PROFILES, load_profile, normalize_profile_name, validate_profile


@dataclass
class ResolvedNerveConfig:
    profile: str
    modules: dict[str, bool]
    advanced: dict[str, Any]
    reasons: dict[str, str]
    _adapter: Callable = field(repr=False)

    def enabled(self, module: str) -> bool:
        return bool(self.modules.get(module, False))

    def get_config(self, key: str, default=None):
        return self.advanced[key] if key in self.advanced else self._adapter(key, default)


def _parse_module_overrides(value: Any) -> dict[str, bool]:
    if value in (None, "", {}):
        return {}
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return {}
    if not isinstance(value, Mapping):
        return {}
    return {str(k): bool(v) for k, v in value.items() if k in MODULES and type(v) is bool}


def resolve_config(get_config: Callable | None = None, *, home=None, profile: dict | None = None) -> ResolvedNerveConfig:
    """Resolve defaults -> selected profile -> same-source overrides -> advanced settings.

    No sidecar and no explicit Hermes ``nerve_profile`` means exact Legacy mode.
    If Hermes selects a different profile from the sidecar, sidecar overrides and
    advanced values do not bleed into that different profile.
    """
    getter = get_config or (lambda key, default=None: default)
    document = load_profile(home) if profile is None else validate_profile(profile)

    configured_profile = normalize_profile_name(getter("nerve_profile", ""))
    configured_modules = _parse_module_overrides(getter("nerve_modules", None))
    sidecar_name = document["nerve_profile"] if document else ""

    if configured_profile:
        if configured_profile not in PROFILES:
            raise ValueError(f"Unknown Nerve profile: {configured_profile}")
        name = configured_profile
        use_sidecar_values = bool(document and sidecar_name == configured_profile)
    else:
        name = sidecar_name or "legacy"
        use_sidecar_values = bool(document)

    if name not in PROFILES:
        raise ValueError(f"Unknown Nerve profile: {name}")

    advanced = dict(document.get("advanced", {})) if use_sidecar_values and document else {}

    def get(key, default=None):
        return advanced[key] if key in advanced else getter(key, default)

    if name in ("legacy", "custom"):
        modules = {
            "reflex": True,
            "nervous": bool(get("nervous_enabled", True)),
            "work_supervision": bool(get("work_supervision_enabled", True)),
            "token_trajectory": bool(get("work_nerve_observer_enabled", True)),
            "action_gate": get("gate_mode", "off") != "off",
            "context_governor": bool(get("context_ledger_enabled", True) or get("context_engine_register", True) or get("context_curation_mode", "shadow") != "off"),
            "remote_workers": True,
            "shared_context": False,
            "assistant_loops": False,
            "assistant_audit": False,
            "shadow_testing": get("reflex_backend", "jev") == "shadow",
            "receipts": True,
            "local_learning": bool(get("nervous_local_learning", True)),
        }
    else:
        modules = dict(PROFILES[name])
        if name == "fat_cat":
            modules["remote_workers"] = bool(get("remote_hosts", {}))

    reasons = {key: ("existing configuration" if name in ("legacy", "custom") else name + " preset") for key in MODULES}

    merged_overrides = {}
    if use_sidecar_values and document:
        merged_overrides.update(_parse_module_overrides(document.get("nerve_modules", {})))
    merged_overrides.update(configured_modules)
    for key, value in merged_overrides.items():
        modules[key] = value
        reasons[key] = "explicit override"

    if name != "legacy":
        changed = True
        while changed:
            changed = False
            for key, spec in MODULES.items():
                missing = [dep for dep in spec.dependencies if not modules.get(dep, False)]
                if modules.get(key, False) and missing:
                    modules[key] = False
                    reasons[key] = "requires " + ", ".join(missing)
                    changed = True

    return ResolvedNerveConfig(name, modules, advanced, reasons, getter)


resolve_nerve_config = resolve_config
