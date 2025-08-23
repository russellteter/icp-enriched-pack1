.PHONY: run eval test fmt build docker-run docker-stop

run:
	uvicorn src.server.app:app --port 8080 --reload

eval:
	python -m evals.schema_validate --schema docs/schemas/healthcare_headers.txt --csv runs/latest/healthcare.csv || true
	python -m evals.schema_completeness runs/latest/healthcare.csv || true
	python -m evals.tier_mapping runs/latest/healthcare.csv || true
	python -m evals.evidence_support runs/latest/healthcare.csv || true

test:
	pytest -q || true

fmt:
	ruff check . || true
	black . || true

build:
	docker build -t icp-discovery-engine .

docker-run:
	docker run -d --name icp-engine -p 8080:8080 icp-discovery-engine

docker-stop:
	docker stop icp-engine && docker rm icp-engine

# Phase 4: Scaling & Optimization commands
install-deps:
	pip install -r requirements.txt

cache-stats:
	curl -s http://localhost:8080/cache/stats | jq

tracing-status:
	curl -s http://localhost:8080/tracing/status | jq

system-health:
	curl -s http://localhost:8080/system/health | jq

batch-status:
	curl -s http://localhost:8080/batch/status | jq

# Development utilities
clean:
	rm -rf __pycache__ */__pycache__ */*/__pycache__
	rm -rf .pytest_cache
	rm -rf checkpoints/*.json
	rm -rf runs/latest/*

dev-setup: install-deps
	mkdir -p checkpoints
	mkdir -p runs/latest