"""Versioned profile sidecar with serialized writers and atomic replacement."""
from __future__ import annotations

from contextlib import contextmanager
import json
import os
from pathlib import Path
import tempfile
from types import MappingProxyType

from .modules import MODULES
from .paths import hermes_home

PROFILE_NAMES = ('fat_cat', 'operator', 'lean', 'marie_kondo', 'custom', 'legacy')
_ENABLED = {
    'fat_cat': set(MODULES) - {'shadow_testing'},
    'operator': {'reflex', 'nervous', 'action_gate', 'context_governor', 'shared_context', 'receipts', 'local_learning'},
    'lean': {'reflex', 'nervous', 'work_supervision', 'token_trajectory', 'receipts'},
    'marie_kondo': {'reflex', 'work_supervision', 'token_trajectory', 'receipts'},
    'custom': set(),
    'legacy': set(),
}
PROFILES = MappingProxyType({name: MappingProxyType({key: key in enabled for key in MODULES}) for name, enabled in _ENABLED.items()})


def profile_path(home: str | Path | None = None) -> Path:
    return (Path(home).expanduser() if home is not None else hermes_home()) / 'nerve' / 'profile.json'


def validate_profile(data: dict) -> dict:
    if not isinstance(data, dict) or set(data) - {'version', 'nerve_profile', 'nerve_modules', 'advanced'}:
        raise ValueError('Invalid profile document')
    if type(data.get('version')) is not int or data['version'] != 1:
        raise ValueError('Unsupported profile version')
    if data.get('nerve_profile') not in PROFILE_NAMES:
        raise ValueError('Unknown Nerve profile')
    modules = data.get('nerve_modules', {})
    advanced = data.get('advanced', {})
    if not isinstance(modules, dict) or any(k not in MODULES or type(v) is not bool for k, v in modules.items()):
        raise ValueError('Module overrides must contain known module IDs and booleans')
    if not isinstance(advanced, dict) or any(not isinstance(k, str) or k.startswith('nerve_') for k in advanced):
        raise ValueError('Invalid advanced settings')
    # Round-trip also rejects values that cannot be persisted as JSON.
    return json.loads(json.dumps(dict(data, nerve_modules=modules, advanced=advanced), allow_nan=False))


def load_profile(home: str | Path | None = None) -> dict | None:
    try:
        with profile_path(home).open(encoding='utf-8') as stream:
            return validate_profile(json.load(stream))
    except FileNotFoundError:
        return None


@contextmanager
def _lock(path: Path):
    # Keep the lock inode: unlinking it would allow overlapping writer locks.
    with path.open('a+b') as stream:
        if os.name == 'nt':
            import msvcrt
            stream.seek(0)
            stream.write(b'\0')
            stream.flush()
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            if os.name == 'nt':
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def _atomic_write(path: Path, payload: bytes):
    fd, temporary = tempfile.mkstemp(prefix='.' + path.name, dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def save_profile(data: dict, home: str | Path | None = None) -> Path:
    payload = (json.dumps(validate_profile(data), indent=2, sort_keys=True, allow_nan=False) + '\n').encode()
    path = profile_path(home)
    path.parent.mkdir(parents=True, exist_ok=True)
    with _lock(path.with_suffix('.lock')):
        if path.exists():
            _atomic_write(path.with_suffix('.json.bak'), path.read_bytes())
        _atomic_write(path, payload)
        if os.name != 'nt':
            fd = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
    return path