.PHONY: run eval test fmt build docker-run docker-stop ui ui-legacy ui-test ui-select docker-ui docker-ui-stop

run:
	uvicorn src.server.app:app --port 8080 --reload

# UI Interface Commands
ui:
	@echo "🚀 Starting Modern ICP Discovery UI (default interface)..."
	python launch_dashboard.py

ui-legacy:
	@echo "🔧 Starting Legacy ICP Discovery UI (complex multi-tab interface)..."
	python launch_legacy_dashboard.py

ui-test:
	@echo "🧪 Testing Modern UI components..."
	python test_modern_ui.py

ui-select:
	@echo "🎯 Interactive UI Selection..."
	python launch_ui.py

eval:
	@echo "=== Healthcare Evaluations ==="
	python -m evals.schema_validate --schema docs/schemas/healthcare_headers.txt --csv runs/latest/healthcare.csv || true
	python -m evals.schema_completeness runs/latest/healthcare.csv || true
	python -m evals.tier_mapping runs/latest/healthcare.csv || true
	python -m evals.evidence_support runs/latest/healthcare.csv || true
	python -m evals.geographic_accuracy runs/latest/healthcare.csv || true
	python -m evals.organization_uniqueness runs/latest/healthcare.csv || true
	@echo
	@echo "=== Corporate Evaluations ==="
	python -m evals.schema_validate --schema docs/schemas/corporate_headers.txt --csv runs/latest/corporate.csv || true
	python -m evals.schema_completeness runs/latest/corporate.csv || true
	python -m evals.tier_mapping runs/latest/corporate.csv || true
	python -m evals.evidence_support runs/latest/corporate.csv || true
	python -m evals.geographic_accuracy runs/latest/corporate.csv || true
	python -m evals.organization_uniqueness runs/latest/corporate.csv || true
	@echo
	@echo "=== Providers Evaluations ==="
	python -m evals.schema_validate --schema docs/schemas/providers_headers.txt --csv runs/latest/providers.csv || true
	python -m evals.schema_completeness runs/latest/providers.csv || true
	python -m evals.tier_mapping runs/latest/providers.csv || true
	python -m evals.evidence_support runs/latest/providers.csv || true
	python -m evals.geographic_accuracy runs/latest/providers.csv || true
	python -m evals.organization_uniqueness runs/latest/providers.csv || true

test:
	@echo "🧪 Running backend tests..."
	pytest -q || true
	@echo "🧪 Testing Modern UI components..."
	python test_modern_ui.py

fmt:
	ruff check . || true
	black . || true

build:
	docker build -t icp-discovery-engine .

docker-run:
	docker run -d --name icp-engine -p 8080:8080 icp-discovery-engine

docker-stop:
	docker stop icp-engine && docker rm icp-engine

# Docker commands for Modern UI
docker-ui:
	@echo "🚀 Starting Modern UI with Docker Compose..."
	docker-compose up -d api ui

docker-ui-legacy:
	@echo "🔧 Starting Legacy UI with Docker Compose..."
	docker-compose --profile legacy up -d api legacy-ui

docker-ui-stop:
	@echo "🛑 Stopping UI services..."
	docker-compose down

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