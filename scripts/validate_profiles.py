#!/usr/bin/env python3
"""Run Hermes' own plugin validator under each Nerve profile."""
from __future__ import annotations
import json, os, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PROFILES=("legacy","fat_cat","operator","lean","marie_kondo")

def main()->int:
    hermes=shutil.which("hermes")
    if not hermes:
        print("SKIP: hermes CLI not found",file=sys.stderr); return 2
    failed=[]
    for profile in PROFILES:
        with tempfile.TemporaryDirectory(prefix=f"nerve-validate-{profile}-") as td:
            home=Path(td)
            if profile!="legacy":
                path=home/"nerve"/"profile.json";path.parent.mkdir(parents=True)
                path.write_text(json.dumps({"version":1,"nerve_profile":profile,"nerve_modules":{},"advanced":{}},indent=2)+"\n")
            env=os.environ.copy();env["HERMES_HOME"]=str(home)
            for key in ("HERMES_KANBAN_TASK","HERMES_KANBAN_TASK_ID","HERMES_KANBAN_RUN_ID","HERMES_KANBAN_CLAIM_LOCK"):
                env.pop(key,None)
            proc=subprocess.run([hermes,"plugins","validate",str(ROOT)],env=env,text=True,capture_output=True)
            output=(proc.stdout+proc.stderr).strip()
            print(f"=== {profile} ===\n{output}\n")
            if proc.returncode!=0: failed.append(profile)
    if failed:
        print("FAIL profiles: "+", ".join(failed),file=sys.stderr); return 1
    print("PASS: hermes plugins validate succeeded for all Nerve profiles")
    return 0
if __name__=="__main__": raise SystemExit(main())
