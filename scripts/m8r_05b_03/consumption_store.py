"""Filesystem-backed single-use claim/finalization using exclusive creation."""
from __future__ import annotations

import json
from pathlib import Path

from scripts.m8r_filesystem_safety import FilesystemSafetyError, atomic_create_text_exclusive, atomic_write_text, safe_destination

from .canonical import canonical_json
from .errors import OrchestrationError


class ConsumptionStore:
    """A claim file is itself fail-closed state if the process stops mid-execution."""

    def __init__(self, root: str | Path):
        self.root = Path(root)

    @staticmethod
    def _relative(binding: dict) -> Path:
        return Path("consumption") / f"{binding['authorization_id']}.json"

    def claim(self, binding: dict, *, claimed_at: str, receipt_id: str) -> Path:
        record = {
            "schema_version": "m8r_05b_03_consumption_state.v1",
            "authorization_id": binding["authorization_id"],
            "authorization_hash": binding["authorization_hash"],
            "consumption_binding_id": binding["consumption_binding_id"],
            "consumption_binding_hash": binding["consumption_binding_hash"],
            "registry_contract_version": "m8r_05b_03.v1",
            "state": "claimed",
            "claimed_at": claimed_at,
            "receipt_id": receipt_id,
        }
        try:
            return atomic_create_text_exclusive(self.root, self._relative(binding), canonical_json(record) + "\n").path
        except FilesystemSafetyError as exc:
            raise OrchestrationError("authorization_already_consumed" if exc.code == "already_consumed_or_replayed" else exc.code) from exc

    def finalize(self, binding: dict, *, claimed_at: str, finished_at: str, receipt_id: str, execution_status: str) -> Path:
        relative = self._relative(binding)
        try:
            safe_destination(self.root, relative, create_parent=True)
            record = {
                "schema_version": "m8r_05b_03_consumption_state.v1",
                "authorization_id": binding["authorization_id"],
                "authorization_hash": binding["authorization_hash"],
                "consumption_binding_id": binding["consumption_binding_id"],
                "consumption_binding_hash": binding["consumption_binding_hash"],
                "registry_contract_version": "m8r_05b_03.v1",
                "state": "consumed",
                "claimed_at": claimed_at,
                "finalized_at": finished_at,
                "receipt_id": receipt_id,
                "execution_status": execution_status,
            }
            return atomic_write_text(self.root, relative, canonical_json(record) + "\n")
        except FilesystemSafetyError as exc:
            raise OrchestrationError(exc.code) from exc
