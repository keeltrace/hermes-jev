"""Adapter for the separately maintained HermesContextBus plugin.

Nerve never vendors or imports the bus runtime. Setup-time integration uses
Hermes' own plugin CLI for enable/disable and local manifest/SQLite inspection.
"""
from __future__ import annotations

import re
import shutil
import sqlite3
import subprocess
from pathlib import Path
from typing import Any

from ..paths import hermes_home

PLUGIN_DIRNAME="hermes-context-bus"

def plugin_dir(home:Path|None=None)->Path:
    return (home or hermes_home())/"plugins"/PLUGIN_DIRNAME

def _manifest_info(target:Path)->dict[str,Any]:
    manifest=target/"plugin.yaml"
    info={"manifest":manifest.exists(),"version":"","health_tool":False}
    if not manifest.exists():return info
    text=manifest.read_text(errors="replace")
    m=re.search(r"(?m)^version:\s*[\"']?([^\"'\n]+)",text)
    info["version"]=m.group(1).strip() if m else ""
    info["health_tool"]=bool(re.search(r"(?m)^\s*-\s*shared_context_health\s*$",text))
    return info

def _sqlite_health(home:Path|None=None)->dict[str,Any]:
    root=home or hermes_home()
    db=root/"shared-context"/"context.db"
    if not db.exists():return {"db_exists":False,"schema_version":None}
    try:
        conn=sqlite3.connect(f"file:{db}?mode=ro",uri=True,timeout=1)
        try:
            version=int(conn.execute("PRAGMA user_version").fetchone()[0])
            statuses={}
            try:
                for state,count in conn.execute("SELECT status,COUNT(*) FROM context_messages GROUP BY status"):
                    statuses[str(state)]=int(count)
            except sqlite3.Error:
                pass
            return {"db_exists":True,"schema_version":version,"statuses":statuses,"db_path":str(db)}
        finally:conn.close()
    except sqlite3.Error as exc:
        return {"db_exists":True,"schema_version":None,"error":str(exc),"db_path":str(db)}

def detect(home:Path|None=None)->dict[str,Any]:
    target=plugin_dir(home)
    info=_manifest_info(target)
    health=_sqlite_health(home)
    return {
        "installed":target.is_dir(),
        "path":str(target),
        "manifest":info["manifest"],
        "version":info["version"],
        "health_tool":info["health_tool"],
        "schema_version":health.get("schema_version"),
        "sqlite":health,
        "doctor_command":f"hermes plugins doctor {target} --ci" if target.is_dir() else "",
        "authority":"coordination-data-only",
    }

def install_from_source(source:str|Path,home:Path|None=None,*,replace:bool=False)->dict[str,Any]:
    src=Path(source).expanduser().resolve()
    if not src.is_dir():raise ValueError(f"Shared Context source directory not found: {src}")
    if not (src/"plugin.yaml").exists() and not (src/"pyproject.toml").exists():
        raise ValueError("Shared Context source is missing plugin.yaml/pyproject.toml")
    target=plugin_dir(home)
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():
        if not replace:return detect(home)
        shutil.rmtree(target)
    ignore=shutil.ignore_patterns(".git","__pycache__",".pytest_cache","runtime","state")
    shutil.copytree(src,target,ignore=ignore)
    return detect(home)

def reconcile_enabled(enabled:bool,*,runner=subprocess.run)->dict[str,Any]:
    status=detect()
    if enabled and not status["installed"]:
        return {**status,"desired_enabled":True,"changed":False,"warning":"HermesContextBus is not installed"}
    if not status["installed"]:
        return {**status,"desired_enabled":False,"changed":False}
    cmd=["hermes","plugins","enable",PLUGIN_DIRNAME,"--no-allow-tool-override"] if enabled else ["hermes","plugins","disable",PLUGIN_DIRNAME]
    proc=runner(cmd,capture_output=True,text=True)
    if proc.returncode!=0:
        raise RuntimeError((proc.stderr or proc.stdout or "Hermes plugin reconciliation failed").strip())
    return {**detect(),"desired_enabled":bool(enabled),"changed":True,"command":" ".join(cmd)}

def explain(home:Path|None=None)->str:
    st=detect(home)
    if st["installed"]:
        version=st.get("version") or "unknown"
        schema=st.get("schema_version")
        health="health-tool" if st.get("health_tool") else "no-health-tool"
        return f"Shared Context {version} installed at {st['path']}; schema={schema}; {health}; coordination data only."
    return "Shared Context is selected by some Nerve profiles but HermesContextBus is not installed for this Hermes home."
