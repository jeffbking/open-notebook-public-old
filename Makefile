.PHONY: run frontend check ruff database lint api start-all stop-all status clean-cache worker worker-start worker-stop worker-restart
.PHONY: deploy docker-build-local export-docs

# Get version from pyproject.toml
VERSION := $(shell grep -m1 version pyproject.toml | cut -d'"' -f2)

# Local image name (personal hard fork: nothing is published to a registry)
LOCAL_IMAGE := open_notebook

database:
	docker compose up -d surrealdb

run:
	@echo "⚠️  Warning: Starting frontend only. For full functionality, use 'make start-all'"
	cd frontend && npm run dev

frontend:
	cd frontend && npm run dev

lint:
	uv run python -m mypy .

ruff:
	ruff check . --fix

# === Docker Build Setup ===
# === Docker Build Targets ===

# Rebuild the image from this checkout and restart the app container
# (production deploy on this host; see docker-compose.yml)
deploy:
	docker compose up -d --build open_notebook

# Build production image for local platform only (no push)
docker-build-local:
	@echo "🔨 Building production image locally ($(shell uname -m))..."
	docker build \
		-t $(LOCAL_IMAGE):$(VERSION) \
		-t $(LOCAL_IMAGE):local \
		.
	@echo "✅ Built $(LOCAL_IMAGE):$(VERSION) and $(LOCAL_IMAGE):local"

dev:
	docker compose -f examples/docker-compose-dev.yml --project-directory . up --build

full:
	docker compose -f examples/docker-compose-full-local.yml --project-directory . up --build


api:
	uv run --env-file .env run_api.py

.PHONY: worker worker-start worker-stop worker-restart

worker: worker-start

worker-start:
	@echo "Starting surreal-commands worker..."
	uv run --env-file .env surreal-commands-worker --import-modules commands --max-tasks "$${OPEN_NOTEBOOK_WORKER_MAX_TASKS:-5}"

worker-stop:
	@echo "Stopping surreal-commands worker..."
	pkill -f "surreal-commands-worker" || true

worker-restart: worker-stop
	@sleep 2
	@$(MAKE) worker-start

# === Service Management ===
start-all:
	@echo "🚀 Starting Open Notebook (Database + API + Worker + Frontend)..."
	@echo "📊 Starting SurrealDB..."
	@docker compose -f docker-compose.dev.yml up -d surrealdb
	@sleep 3
	@echo "🔧 Starting API backend..."
	@uv run run_api.py &
	@sleep 3
	@echo "⚙️ Starting background worker..."
	@uv run --env-file .env surreal-commands-worker --import-modules commands --max-tasks "$${OPEN_NOTEBOOK_WORKER_MAX_TASKS:-5}" &
	@sleep 2
	@echo "🌐 Starting Next.js frontend..."
	@echo "✅ All services started!"
	@echo "📱 Frontend: http://localhost:3000"
	@echo "🔗 API: http://localhost:5055"
	@echo "📚 API Docs: http://localhost:5055/docs"
	cd frontend && npm run dev

stop-all:
	@echo "🛑 Stopping all Open Notebook services..."
	@pkill -f "next dev" || true
	@pkill -f "surreal-commands-worker" || true
	@pkill -f "run_api.py" || true
	@pkill -f "uvicorn api.main:app" || true
	@docker compose down
	@echo "✅ All services stopped!"

status:
	@echo "📊 Open Notebook Service Status:"
	@echo "Database (SurrealDB):"
	@docker compose ps surrealdb 2>/dev/null || echo "  ❌ Not running"
	@echo "API Backend:"
	@pgrep -f "run_api.py\|uvicorn api.main:app" >/dev/null && echo "  ✅ Running" || echo "  ❌ Not running"
	@echo "Background Worker:"
	@pgrep -f "surreal-commands-worker" >/dev/null && echo "  ✅ Running" || echo "  ❌ Not running"
	@echo "Next.js Frontend:"
	@pgrep -f "next dev" >/dev/null && echo "  ✅ Running" || echo "  ❌ Not running"

# === Documentation Export ===
export-docs:
	@echo "📚 Exporting documentation..."
	@uv run python scripts/export_docs.py
	@echo "✅ Documentation export complete!"

# === Cleanup ===
clean-cache:
	@echo "🧹 Cleaning cache directories..."
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name ".mypy_cache" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name ".ruff_cache" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -type f -delete 2>/dev/null || true
	@find . -name "*.pyo" -type f -delete 2>/dev/null || true
	@find . -name "*.pyd" -type f -delete 2>/dev/null || true
	@echo "✅ Cache directories cleaned!"