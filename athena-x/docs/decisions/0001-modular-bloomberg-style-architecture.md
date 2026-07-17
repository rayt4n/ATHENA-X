# ADR-0001: Modular Bloomberg-Style Architecture

## Status
Accepted

## Context
The original Space site was a monolithic tab-switched SPA with no real
backend, no agents, and no persistence. To rebuild as an institutional-grade
terminal, we needed a paradigm shift — from pages to modules.

## Decision
Adopt a Bloomberg-style modular architecture where each module is an
independently launchable, multi-instance, headless-capable unit. Modules
communicate only through a typed event bus. No direct cross-module calls.

## Consequences
- Pros: extreme modularity, plugin extensibility, parallel development
- Cons: more upfront infrastructure, learning curve for new contributors
- Mitigation: comprehensive docs + scaffolding tools
