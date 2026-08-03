"""Public contract surface for M8R-05B-03 Commit 2."""

from .controlled_dispatch import claim_and_dispatch_approved
from .dispatch import RuntimeAdapterRegistration, RuntimeAdapterRegistry
from .preflight import build_orchestrator_preflight

__all__ = [
    "RuntimeAdapterRegistration",
    "RuntimeAdapterRegistry",
    "build_orchestrator_preflight",
    "claim_and_dispatch_approved",
]
