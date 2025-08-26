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

**Key Principles** (from `docs/.cursorrules`):
1. Prefer **LangGraph workflows** over free-form agents
2. Keep **MCP-style tools** pure (I/O only) - no business logic in tools
3. **Evals are the release gate** - failing PRs do not merge
4. Honor **output schemas** exactly - breaking schemas is a blocker
5. Keep diffs small; write tests/evals before refactors

## Critical Development Commands

**Setup & Dependencies**:
- `make install-deps` - Install Python dependencies from requirements.txt
- `make dev-setup` - Complete development environment setup (creates dirs, installs deps)
- Copy `.env.example` to `.env` and configure budget/cache settings

**Core Development**:
- `make run` - Start FastAPI server with uvicorn on port 8080 (hot reload enabled)
- `make ui` - Launch modern UI interface on port 8501 (default, clean interface)
- `make ui-legacy` - Launch legacy multi-tab dashboard (complex interface)
- `make ui-test` - Test modern UI components and functionality

**Testing & Validation**:
- `make eval` - Run all evaluators against latest healthcare results (must pass for PRs)
- `make test` - Run pytest test suite (note: tests not yet implemented)
- `make fmt` - Format code with ruff and black

**Evaluation Pipeline** (every PR must pass):
- `make eval` - Run complete evaluation suite
- Individual evaluators:
  - `python -m evals.schema_validate --schema docs/schemas/healthcare_headers.txt --csv runs/latest/healthcare.csv`
  - `python -m evals.schema_completeness runs/latest/healthcare.csv`
  - `python -m evals.tier_mapping runs/latest/healthcare.csv` 
  - `python -m evals.evidence_support runs/latest/healthcare.csv`

**Monitoring & Debug**:
- `make cache-stats` - View cache hit rates and performance (requires running server)
- `make system-health` - Check runtime health metrics
- `make batch-status` - Monitor batching system status
- `make tracing-status` - Check distributed tracing status
- `make clean` - Remove cache files and build artifacts
- `make docker-build` / `make docker-run` - Docker deployment commands

**FastAPI Server Endpoints**:
- `POST /run` - Execute workflow (body: `{"segment": "healthcare|corporate|providers", "targetcount": 50, "mode": "fast|deep", "region": "na|emea|both"}`)
- `GET /health` - Health check endpoint
- `GET /metrics` - Prometheus-style metrics

## User Interface Architecture

**Modern UI (Default)** - Clean, user-friendly interface at `src/ui/modern_app.py`:
- **Single-purpose screens**: Home → Setup → Progress → Results
- **Progressive disclosure**: One decision at a time, no overwhelming tabs
- **3-step setup wizard**: Target selection, scope configuration, confirmation
- **Real-time progress**: Elegant tracking with time estimates
- **Clean results dashboard**: Focused display with export capabilities
- **Mobile responsive**: Works on desktop, tablet, and mobile
- **Launch**: `make ui` or `python launch_dashboard.py`

**Legacy Dashboard (Backup)** - Complex multi-tab interface at `src/ui/dashboard.py`:
- **Multi-tab layout**: Workflow, Results, Monitoring, Health, Analytics tabs
- **Information dense**: All features visible simultaneously
- **Complex configuration**: Multiple options and settings per screen
- **Comprehensive monitoring**: Detailed system metrics and analytics
- **Launch**: `make ui-legacy` or `python launch_legacy_dashboard.py`

**Interface Selection Guidelines**:
- **Use Modern UI** for: End users, demonstrations, production deployments
- **Use Legacy Dashboard** for: System monitoring, detailed analytics, debugging
- **Default**: Modern UI is now the primary interface (launch_dashboard.py)

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

**Fully Implemented**:
- Healthcare flow with LangGraph workflow (`src/flows/healthcare_flow.py`)
- FastAPI server with health/metrics endpoints (`src/server/app.py`)
- Complete evaluation system (`evals/` directory)
- MCP-style tools (webtools, explorium, sheets)
- Budget management and caching layers
- Tracing and monitoring infrastructure

**Stub Files** (need implementation):
- `src/flows/corporate_flow_stub.py`
- `src/flows/providers_flow_stub.py`

**Architecture Components**:
- **Runtime**: Budget tracking, cache layers, batch processing, tracing
- **Tools**: WebSearch, WebFetch, ExploriumClient, SheetsLedger (all in `/src/tools/`)
- **Flows**: LangGraph state machines (seed→harvest→extract→score→dedupe→enrich→output)
- **Scoring**: Dedicated scoring logic per ICP (`src/scoring/healthcare.py`)
- **Evaluation**: 4 evaluators for schema validation, completeness, tier mapping, evidence support

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
1. `schema_validate` - Exact header matching against schema files
2. `schema_completeness` - All required columns present and populated  
3. `tier_mapping` - Score thresholds correctly applied
4. `evidence_support` - URLs contain supporting phrases via regex

**Process**: Every PR → run `make eval` → block on failure  
**Thresholds**: schema 100%, tier map 100%, evidence ≥90%

## Tools Architecture

MCP-style tools with pure I/O contracts (no business logic):
- `web.search({q, max, site?}) -> [{title,url,snippet}]`
- `web.fetch({url}) -> {status,url,html,text}`
- `explorium.enrich({company|domain}) -> {size_range, industry, country, ...}`
- `ledger.load({segment}) -> [org_names]`
- `ledger.upsert([{organization, segment, region, tier, score, evidence_url, notes}])`

Tool signatures in `/src/tools/*.py` must not change without PRD update.

## Project Dependencies & Runtime

**Python Stack** (from requirements.txt):

- **LangGraph** (≥0.1.0) - Stateful workflow orchestration and graph execution
- **FastAPI** (≥0.111.0) + **Uvicorn** - REST API server with auto-reload
- **Pydantic** (≥2.7.0) - Data validation, serialization, and state models
- **httpx** (≥0.27.0) - Async HTTP client for web requests  
- **trafilatura** (≥1.9.0) - Web content extraction and cleaning
- **ddgs** (≥6.1.3) - DuckDuckGo search API wrapper
- **tenacity** (≥8.2.3) - Retry logic and resilience patterns
- **Redis** (≥5.0.0) - Caching layer and session storage
- **OpenTelemetry** (≥1.20.0) - Distributed tracing and observability

**File Structure**:

```text
src/
├── flows/          # LangGraph workflows per ICP
├── tools/          # MCP-style I/O tools  
├── runtime/        # Budget, cache, batch, tracing
├── scoring/        # ICP-specific scoring logic
├── server/         # FastAPI application
├── extraction/     # Entity extraction rules
└── deduplication/  # Duplicate detection
evals/              # Evaluation pipeline
docs/schemas/       # CSV column definitions (immutable)
runs/latest/        # Generated CSV outputs
```

## LangGraph Workflow Pattern

All flows follow this deterministic node sequence:

```text
seed → harvest → extract → score → dedupe → enrich → output → ledger_upsert
```

**State Models**: Each ICP has a Pydantic state class (e.g., `HCState`) that carries data through nodes
**Budget Integration**: All nodes respect `BudgetManager` limits and raise `BudgetExceeded` on limits
**Error Handling**: Node failures are captured in state.summary; workflows continue with partial data
**Tracing**: Each node logs entry/exit with redacted sensitive data for observability

## Environment Configuration

Create `.env` from `.env.example`:

```bash
# Runtime budgets
BUDGET_MAX_SEARCHES=120     # Max search queries per run
BUDGET_MAX_FETCHES=150      # Max web page fetches per run
BUDGET_MAX_ENRICH=80        # Max Explorium enrichments per run
CACHE_TTL_SECS=604800       # Cache expiry (7 days default)
PER_DOMAIN_FETCH_CAP=25     # Per-domain fetch limit
MODE=fast                   # fast|deep|strict
ALLOWLIST_DOMAINS=          # Comma-separated allowed domains
```

**Mode effects**:

- `fast` (default): Standard budgets
- `deep`: 2x searches/fetches, 1.5x enrichments
- `strict`: 0.5x all budgets

## Immediate Development Tasks (from `.cursorrules`)

1. **Healthcare schema completeness**: Implement exact headers from `/docs/schemas/healthcare_headers.txt`
2. **Extractor improvements**: Add dedicated extraction for Organization, EHR_Vendor, GoLive_Date, Lifecycle_Phase
3. **Regional targeting**: Implement NA/EMEA split and backfill logic
4. **Corporate & Providers flows**: Clone healthcare flow, implement scoring tables, match schema headers
5. **Eval expansion**: Add more evaluators, wire to `make eval`
6. **Testing**: Implement pytest tests (currently none exist)
