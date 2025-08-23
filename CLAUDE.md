# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

The ICP Discovery Engine is a LangGraph-based workflow system that discovers and scores potential clients across three ICPs (Ideal Customer Profiles):
- **Healthcare EHR Adoption & Training**: Provider organizations with active EHR lifecycle and VILT training
- **Corporate Academy**: Large enterprises (≥7,500 employees) with named academies using VILT
- **Professional Training Providers**: B2B training companies with live virtual instruction and public calendars

## Architecture & Patterns

**Core Pattern**: Stateful LangGraph workflow → deterministic nodes → MCP-style tools for I/O
```
seed → harvest → extract → score → dedupe → enrich → output → ledger_upsert
```

**Key Principles** (from `.cursorrules`):
1. Prefer **LangGraph workflows** over free-form agents
2. Keep **MCP-style tools** pure (I/O only) - no business logic in tools
3. **Evals are the release gate** - failing PRs do not merge
4. Honor **output schemas** exactly - breaking schemas is a blocker
5. Keep diffs small; write tests/evals before refactors

## Critical Development Commands

Since no Makefile, package.json, or requirements.txt exists yet, the system expects:
- `make eval` - Run evaluation pipeline (mentioned in docs but not yet implemented)
- Runtime will be FastAPI with `POST /run` endpoint
- Testing framework not yet established - check for pytest or similar when implementing

## Data Contracts (NEVER CHANGE WITHOUT PRD UPDATE)

**Output Schema Files** (single source of truth):
- `/docs/schemas/healthcare_headers.txt`
- `/docs/schemas/corporate_headers.txt` 
- `/docs/schemas/providers_headers.txt`

**Scoring Matrices**: `/docs/scoring/SCORING.md` defines official weights and thresholds
- Healthcare: ≥90 points + all MUST signals → Confirmed
- Corporate: Same threshold logic
- Providers: Same threshold logic with red flag exclusions

## Current Implementation Status

**Implemented**: Foundational documentation and schema definitions
**Stub Files**: 
- `src/flows/corporate_flow_stub.py`
- `src/flows/providers_flow_stub.py`

**Next Priority Tasks** (from agent prompt):
1. Healthcare schema completeness with CSV writer
2. Extractor improvements for Organization, EHR_Vendor, etc.
3. Regional targeting (NA/EMEA 80/20 split)
4. Evals expansion with schema_completeness + tier_mapping evaluators

## Security & Compliance

- Never commit secrets or service account JSON
- Never log tokens/keys/PII
- Domain allow-lists required for web scraping
- All traces must redact sensitive information

## Definition of Done

Every change must meet:
- All unit checks pass
- **Evals** meet thresholds (schema 100%, tier map 100%, evidence ≥90%)
- Traces/logs added for new nodes with secrets redacted
- PRD updated if tool contracts change

## Evaluation System

**Local Evaluators**:
1. `schema_completeness` - All required columns present and populated
2. `evidence_support` - URLs contain supporting phrases via regex
3. `tier_mapping` - Score thresholds correctly applied

**Process**: Every PR → run `make eval` → block on failure

## Tools Architecture

MCP-style tools with pure I/O contracts (no business logic):
- `web.search({q, max, site?}) -> [{title,url,snippet}]`
- `web.fetch({url}) -> {status,url,html,text}`
- `explorium.enrich({company|domain}) -> {size_range, industry, country, ...}`
- `ledger.load({segment}) -> [org_names]`
- `ledger.upsert([{organization, segment, region, tier, score, evidence_url, notes}])`

Tool signatures in `/src/tools/*.py` must not change without PRD update.