# Bazzar Terminal — common tasks. (Windows: use Git Bash / WSL, or run the
# underlying commands directly.)

.PHONY: setup check lint format test build dev

setup: ## Install all dependencies (Python + Node + hooks)
	pip install -r requirements-dev.txt
	npm install
	pre-commit install
check: ## Run the full quality gate (matches CI)
	ruff check .
	ruff format --check .
	mypy
	pytest
	npm run lint
	npm run format:check
	npm run test
	npm run build

lint: ## Auto-fix lint issues (Python + JS)
	ruff check --fix .
	npm run lint:fix

format: ## Format everything
	ruff format .
	npm run format
test: ## Run test suites
	pytest
	npm run test

build: ## Build the renderer
	npm run build
dev: ## Run the Vite dev server
	npm run dev
