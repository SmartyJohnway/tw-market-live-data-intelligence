"""Offline loaders and immutable hash checks for M8R-05B-01."""
from __future__ import annotations
import copy
import json
from pathlib import Path
from typing import Any, Mapping
from .canonical import sha256_json
from .models import PlanningError

def load_json(path: str | Path) -> dict[str, Any]:
    try:
        value=json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        raise PlanningError('input_schema_invalid', str(exc)) from exc
    if not isinstance(value,dict): raise PlanningError('input_schema_invalid','root_not_object')
    return value

def artifact_hash(value: Mapping[str, Any]) -> str: return sha256_json(value)

def verify_artifact(value: Mapping[str, Any], declared_hash: str, *, code: str, expected_version: str | None=None) -> None:
    if not isinstance(declared_hash,str) or artifact_hash(value)!=declared_hash: raise PlanningError(code)
    if expected_version is not None and value.get('schema_version')!=expected_version: raise PlanningError('unsupported_contract_version')

def executor_index(inventory: Mapping[str,Any]) -> dict[str,dict[str,Any]]:
    surfaces=inventory.get('surfaces')
    if not isinstance(surfaces,list): raise PlanningError('input_schema_invalid','executor_inventory_surfaces')
    result={}
    for surface in surfaces:
        if isinstance(surface,dict) and isinstance(surface.get('surface_id'),str): result[surface['surface_id']]=copy.deepcopy(surface)
    return result
