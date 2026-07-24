"""Explicit executor allowlist.  It deliberately does not auto-discover modules."""
from __future__ import annotations

from collections.abc import Mapping

from .errors import OrchestrationError
from .executor_adapter import ExecutorAdapter


class ExecutorRegistry:
    def __init__(self, adapters: Mapping[str, ExecutorAdapter] | None = None):
        self._adapters = dict(adapters or {})

    def resolve(self, executor_id: str) -> ExecutorAdapter:
        adapter = self._adapters.get(executor_id)
        if not callable(adapter):
            raise OrchestrationError("executor_not_registered")
        return adapter

    def ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._adapters))
