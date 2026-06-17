# TW-Market Live Data Intelligence

AI-native research project for discovering, validating, benchmarking, and documenting feasible methods for AI systems to access Taiwan equity market information with high freshness, legal safety, reproducibility, and maintainability.

## Mission

Build a Taiwan market live-data acquisition framework that enables ChatGPT, Codex, and future AI agents to reliably access near real-time Taiwan market information through legally available interfaces.

This repository does **not** assume any single implementation. TWSE MIS, Yahoo Finance, Fugle, Fubon Neo, FinMind, TWSE/TPEx OpenAPI, browser automation, MCP, WebSocket, and other methods are all research candidates.

## Core Principle

This is not a one-off crawler. It is a research and engineering workbench for:

- evidence-based market data source discovery,
- reproducible probing,
- protocol and schema analysis,
- AI integration design,
- safe long-term maintainability.

## What this repo should produce

1. Architecture survey
2. Data-source capability matrix
3. Probe results and failure logs
4. Protocol/session/header/cookie analysis where applicable
5. Data contracts and timestamp semantics
6. AI integration patterns, including ChatGPT, Codex, MCP, and browser automation
7. Recommended architecture with tradeoffs

## First milestone

Establish a minimal, reproducible source-probe framework for:

- TWSE MIS candidate endpoints
- Yahoo Finance / Yahoo Taiwan Finance candidates
- TWSE official OpenAPI / public pages
- TPEx official OpenAPI / public pages
- Fugle / Fubon Neo feasibility research, without embedding secrets

## Legal and ethical constraints

- Respect website terms of service.
- Avoid abusive crawling or excessive polling.
- Do not bypass authentication or access controls.
- Do not store API keys in Git.
- Treat unofficial endpoints as fragile and document their risk clearly.

## Repository status

Initial scaffold for AI Vibe Coding long-task collaboration.
