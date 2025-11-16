.PHONY: help install install-dev setup run run-web run-server test lint format clean verify

help: ## Show this help message
	@echo "Fantasy Football Agent - Makefile Commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install project dependencies
	pip install -r requirements.txt
	@if [ -d "fantasy-football-mcp-public" ]; then \
		pip install -r fantasy-football-mcp-public/requirements.txt; \
	fi

install-dev: install ## Install development dependencies
	pip install -e ".[dev]"

setup: ## Run full setup (creates venv, installs deps, clones MCP server)
	./setup.sh

run: ## Run the agent directly
	python -m app.agent

run-web: ## Start ADK web interface (port 8080)
	./start_adk_web.sh

run-server: ## Start FastAPI server (port 8080)
	python -m app.server

test: ## Run tests
	pytest

lint: ## Run linter
	ruff check app/

format: ## Format code
	black app/

clean: ## Clean build artifacts and cache
	find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true
	rm -rf build/ dist/ .pytest_cache/ .ruff_cache/

verify: ## Verify setup and dependencies
	python verify_setup.py

# MCP Server Management
mcp-yahoo: ## Start Yahoo Fantasy MCP Server in HTTP mode (port 8001)
	cd fantasy-football-mcp-public && PORT=8001 python fastmcp_server.py

mcp-browser: ## Show Browser MCP setup instructions
	@echo "Browser MCP uses Chrome extension - no server to start"
	@echo "Install extension: https://browsermcp.io/"

# Development
dev-install: install-dev ## Install for development
	@echo "Development environment ready"

dev-run: ## Run in development mode with auto-reload
	uvicorn app.server:app --reload --port 8080

# Documentation
docs: ## Generate documentation (if using sphinx/mkdocs)
	@echo "Documentation generation not configured"

# Environment
env-example: ## Create .env.example from template
	@if [ ! -f .env.example ]; then \
		cp .env .env.example 2>/dev/null || echo "Create .env.example manually"; \
	fi

