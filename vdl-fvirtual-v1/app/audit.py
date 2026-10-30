"""Auditoría encadenada por hash: modificar o borrar un evento rompe la cadena."""
from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable, Protocol

GENESIS = "0" * 64


class AuditLike(Protocol):
    ts: str
    actor: str
    role: str
    event_type: str
    payload: str
    prev_hash: str
    hash: str


def canonical(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str, ensure_ascii=False)


def compute_hash(prev_hash: str, ts: str, actor: str, role: str, event_type: str, payload_json: str) -> str:
    material = "|".join([prev_hash, ts, actor, role, event_type, payload_json])
    return hashlib.sha256(material.encode()).hexdigest()


def verify_chain(rows: Iterable[AuditLike]) -> tuple[bool, int | None]:
    """Devuelve (ok, índice del primer evento inconsistente)."""
    prev = GENESIS
    for i, r in enumerate(rows):
        if r.prev_hash != prev:
            return False, i
        if compute_hash(r.prev_hash, r.ts, r.actor, r.role, r.event_type, r.payload) != r.hash:
            return False, i
        prev = r.hash
    return True, None
