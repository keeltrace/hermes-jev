from __future__ import annotations

import argparse
import sys

from .config_resolver import resolve_config
from .integrations import shared_context
from .modules import MODULES
from .profiles import save_profile

_ORDER=("fat_cat","operator","lean","marie_kondo")
_DISPLAY={
    "legacy":"Legacy",
    "custom":"Full Configuration",
    "fat_cat":"Fat Cat",
    "operator":"Operator",
    "lean":"Lean",
    "marie_kondo":"Marie Kondo",
}
_DESC={
    "fat_cat":"Max assistant quality; spend more tokens for capability.",
    "operator":"Direct Hermes power use: tools, coding, agents, context.",
    "lean":"Factory-first nervous system with token-heavy extras off.",
    "marie_kondo":"Minimum Nerve: only features that clearly earn their cost.",
}

def _current():
    return resolve_config()

def _show(r):
    print(f"Profile: {_DISPLAY.get(r.profile,r.profile)}")
    for mid,spec in MODULES.items():
        print(f"[{'ON ' if r.enabled(mid) else 'OFF'}] {spec.name:<18} {spec.description}")

def _save(profile, overrides=None):
    doc={"version":1,"nerve_profile":profile,"nerve_modules":dict(overrides or {}),"advanced":{}}
    path=save_profile(doc)
    resolved=resolve_config(profile=doc)
    shared=shared_context.reconcile_enabled(resolved.enabled("shared_context"))
    if shared.get("warning"):
        print("Shared Context: "+shared["warning"],file=sys.stderr)
    return path

def _interactive():
    cur=_current()
    print("NERVE SETUP\n")
    print("1. Full Configuration - Pick every Nerve module and advanced option yourself.")
    for i,p in enumerate(_ORDER,2):
        print(f"{i}. {_DISPLAY[p]:<18} - {_DESC[p]}")
    try:
        raw=input("\nSelect [1-5]: ").strip()
    except (EOFError,KeyboardInterrupt):
        return 1
    if raw=="1":
        mods=dict(cur.modules)
        for mid,spec in MODULES.items():
            val=input(f"{spec.name} [{'Y/n' if mods[mid] else 'y/N'}] {spec.description} ").strip().lower()
            if val in {"y","yes","on","1"}:
                mods[mid]=True
            elif val in {"n","no","off","0"}:
                mods[mid]=False
        path=_save("custom",mods)
        print(f"Saved {path}")
        return 0
    try:
        profile=_ORDER[int(raw)-2]
    except Exception:
        print("Invalid selection",file=sys.stderr)
        return 2
    proposed=resolve_config(profile={"version":1,"nerve_profile":profile,"nerve_modules":{},"advanced":{}})
    _show(proposed)
    if input("Apply? [y/N]: ").strip().lower() not in {"y","yes"}:
        return 1
    path=_save(profile)
    print(f"Saved {path}")
    return 0

def main(argv=None):
    parser=argparse.ArgumentParser(prog="nerve")
    sub=parser.add_subparsers(dest="command")
    setup=sub.add_parser("setup")
    setup.add_argument("--show",action="store_true")
    setup.add_argument("--profile",choices=_ORDER)
    setup.add_argument("--reset",choices=_ORDER)
    setup.add_argument("--explain",action="store_true")
    setup.add_argument("--install-shared-context",metavar="SOURCE")
    args=parser.parse_args(argv)
    if args.command!="setup":
        parser.print_help()
        return 2
    if args.profile and args.reset:
        setup.error("--profile and --reset are mutually exclusive")
    if args.install_shared_context:
        status=shared_context.install_from_source(args.install_shared_context)
        print(f"Shared Context installed: {status['path']}")
        print(f"Doctor: {status['doctor_command']}")
        if _current().enabled("shared_context"):
            shared_context.reconcile_enabled(True)
            print("Shared Context enabled for the current Nerve profile.")
        return 0
    if args.show or args.explain:
        current=_current()
        _show(current)
        if args.explain:
            print("\nShared Context: "+shared_context.explain())
        return 0
    target=args.profile or args.reset
    if target:
        path=_save(target)
        _show(resolve_config(profile={"version":1,"nerve_profile":target,"nerve_modules":{},"advanced":{}}))
        print(f"Saved {path}")
        return 0
    if not sys.stdin.isatty():
        setup.error("interactive setup requires a TTY; use --profile")
    return _interactive()

if __name__=="__main__":
    raise SystemExit(main())
