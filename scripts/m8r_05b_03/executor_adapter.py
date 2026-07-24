"""Protocol for reviewed adapters bridging existing executor contracts."""
from __future__ import annotations

from typing import Protocol

from .execution_context import ExecutionContext


class ExecutorAdapter(Protocol):
    def __call__(self, context: ExecutionContext) -> dict: ...
