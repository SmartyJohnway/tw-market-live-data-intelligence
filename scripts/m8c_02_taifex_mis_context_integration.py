"""Pure M8C-02 TAIFEX MIS context integration helpers."""
from __future__ import annotations
from scripts.m8c_taifex_mis_context_adapter import build_taifex_mis_m8_observations
from scripts.m8_multi_source_context_builder import build_multi_source_market_context
from scripts.m8_controlled_conversation_context import build_controlled_conversation_context


def build_taifex_mis_multi_source_context(execution_result, source_registry, now_utc=None):
    return build_multi_source_market_context(build_taifex_mis_m8_observations(execution_result), source_registry, now_utc=now_utc)


def build_taifex_mis_controlled_conversation_context(execution_result, source_registry, now_utc=None, include_markdown=True):
    return build_controlled_conversation_context(build_taifex_mis_multi_source_context(execution_result, source_registry, now_utc=now_utc), include_markdown=include_markdown)
