"""Evidence envelope: the uniform result contract for every tool call."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any


def ok(data: Any, *, sources: Iterable[str], limitations: Iterable[str] | None = None,
       unknowns: Iterable[str] | None = None) -> dict:
    return {
        "ok": True,
        "data": data,
        "error": None,
        "evidence": {
            "sources": list(sources),
            "limitations": list(limitations or []),
            "unknowns": list(unknowns or []),
        },
    }


def err(message: str, *, kind: str = "upstream", sources: Iterable[str] = (),
        limitations: Iterable[str] | None = None,
        unknowns: Iterable[str] | None = None) -> dict:
    return {
        "ok": False,
        "data": None,
        "error": {"kind": kind, "message": message},
        "evidence": {
            "sources": list(sources),
            "limitations": list(limitations or []),
            "unknowns": list(unknowns or []),
        },
    }
