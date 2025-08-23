# Patch: Cost/Usage Guardrails (Budgets, Cache, Rate Limits)

This is build **1755913596**.

**Adds**
- Hard **budgets** per run (searches, fetches, enrich calls, LLM tokens).
- **Disk cache** for fetched pages (TTL default 7 days).
- **Domain allow-list** + per-domain ceilings.
- Server returns `budget` snapshot & `summary`.
- `/run` accepts `mode: fast|deep|strict` to scale budgets.
- Docs: `docs/cost_guardrails.md`, `docs/CONFIG.md`, `.env.append`.

**Apply**
1) Copy files into your repo (preserve paths).
2) Append env vars from `.env.append` to your `.env`.
3) `make run` then:
   ```bash
   curl -s -X POST http://localhost:8080/run      -H "Content-Type: application/json"      -d '{"segment":"healthcare","targetcount":30,"mode":"fast","region":"both"}' | jq
   ```
4) Confirm `budget` counters and `summary` behave as expected.
