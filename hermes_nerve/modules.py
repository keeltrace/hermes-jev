"""Dependency-free, declarative registry; importing it starts no services."""
from dataclasses import dataclass
from types import MappingProxyType


@dataclass(frozen=True)
class ModuleSpec:
    id: str
    name: str
    description: str
    dependencies: tuple[str, ...] = ()


_SPECS = (
    ModuleSpec('reflex', 'Reflex core', 'Cheap typed review through Jev/Laya/OpenJev.'),
    ModuleSpec('nervous', 'Nervous system', 'Supervise decisions and turn admission.'),
    ModuleSpec('work_supervision', 'Work supervision', 'DoD, evidence and completion checks for workers.'),
    ModuleSpec('token_trajectory', 'Token trajectory', 'Watch worker budget, repetition and likely completion.', ('work_supervision',)),
    ModuleSpec('action_gate', 'Action gate', 'Review individual tool actions before execution.'),
    ModuleSpec('context_governor', 'Context governor', 'Curate/recover context and protect important state.'),
    ModuleSpec('remote_workers', 'Remote workers', 'Delegate and control Hermes workers on other hosts.'),
    ModuleSpec('shared_context', 'Shared Context', 'Share bounded handoffs across Hermes agents/surfaces.'),
    ModuleSpec('assistant_loops', 'Assistant loops', 'Persist goals, dependencies, triggers and follow-through.'),
    ModuleSpec('assistant_audit', 'Assistant audit', 'Reflex-check active goals during normal Hermes turns.', ('assistant_loops', 'reflex')),
    ModuleSpec('shadow_testing', 'Shadow testing', 'Compare Reflex backends for development/calibration.', ('reflex',)),
    ModuleSpec('receipts', 'Receipts', 'Keep bounded evidence for supervisory decisions.'),
    ModuleSpec('local_learning', 'Local learning', 'Learn from bounded local supervisory outcomes.'),
)
MODULES = MappingProxyType({spec.id: spec for spec in _SPECS})
MODULE_REGISTRY = MODULES
