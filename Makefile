# Makefile for code-review-agentic-framework

.PHONY: help install test lint format clean setup run-demo

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	poetry install

install-tools: ## Install with analysis tools
	poetry install --with tools

setup: ## Initial setup (copy .env.example, create directories)
	cp -n .env.example .env || true
	mkdir -p artifacts logs eval/dataset eval/results
	@echo "✓ Setup complete. Please edit .env with your API keys."

test: ## Run tests
	poetry run pytest -v

test-cov: ## Run tests with coverage
	poetry run pytest -v --cov=. --cov-report=html --cov-report=term

lint: ## Run linters
	poetry run ruff check .
	poetry run mypy . --ignore-missing-imports

format: ## Format code
	poetry run ruff format .

clean: ## Clean build artifacts
	rm -rf __pycache__ .pytest_cache .ruff_cache .mypy_cache
	rm -rf htmlcov .coverage
	rm -rf dist build *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

run-demo: ## Run demo review (requires setup)
	poetry run code-review review \
		--pr-id "demo-001" \
		--title "Demo PR" \
		--language python \
		--multi-agent \
		.

init-dataset: ## Initialize evaluation dataset
	poetry run code-review init-dataset ./eval/dataset

collect-dataset: ## Collect PR dataset from GitHub (requires GITHUB_TOKEN)
	@if [ -z "$$GITHUB_TOKEN" ]; then \
		echo "Error: GITHUB_TOKEN environment variable not set"; \
		echo "Create token at: https://github.com/settings/tokens"; \
		exit 1; \
	fi
	poetry run python eval/dataset/collect_dataset.py collect --repos 15 --prs-per-repo 3 --balanced --min-lines 0 --max-lines 999999

collect-dataset-large: ## Collect large dataset (20+ repos, more PRs)
	@if [ -z "$$GITHUB_TOKEN" ]; then \
		echo "Error: GITHUB_TOKEN not set"; \
		exit 1; \
	fi
	poetry run python eval/dataset/collect_dataset.py collect --repos 25 --prs-per-repo 4 --balanced --min-lines 0 --max-lines 999999

collect-dataset-large: ## Collect larger dataset
	@if [ -z "$$GITHUB_TOKEN" ]; then \
		echo "Error: GITHUB_TOKEN not set"; \
		exit 1; \
	fi
	poetry run python eval/dataset/collect_dataset.py --repos 10 --prs-per-repo 10 --balanced

list-repos: ## List available repositories for collection
	poetry run python eval/dataset/collect_dataset.py list-repos

check: lint test ## Run all checks (lint + test)

.DEFAULT_GOAL := help

