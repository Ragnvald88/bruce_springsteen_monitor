# Makefile for Bruce Springsteen Ticket Monitor

.PHONY: help install test test-unit test-integration lint format clean run run-gui setup-dev

# Default target
help:
	@echo "Available commands:"
	@echo "  install      - Install dependencies"
	@echo "  test         - Run all tests"
	@echo "  test-unit    - Run unit tests only"
	@echo "  test-integration - Run integration tests only"
	@echo "  lint         - Run linting checks"
	@echo "  format       - Format code"
	@echo "  clean        - Clean up temporary files"
	@echo "  run          - Run the ticket monitor (CLI)"
	@echo "  run-gui      - Run the ticket monitor (GUI)"
	@echo "  setup-dev    - Setup development environment"

# Install dependencies
install:
	pip install -r requirements.txt

# Run all tests
test:
	pytest -v

# Run unit tests only
test-unit:
	pytest -v -m "unit or not integration"

# Run integration tests only
test-integration:
	pytest -v -m "integration"

# Run linting checks
lint:
	python -m flake8 src/ tests/ --max-line-length=100 --ignore=E203,W503
	python -m mypy src/ --ignore-missing-imports

# Format code
format:
	python -m black src/ tests/ --line-length=100
	python -m isort src/ tests/

# Clean up temporary files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/

# Run the ticket monitor (CLI)
run:
	python src/main.py

# Run the ticket monitor (GUI)
run-gui:
	python src/main.py --gui

# Setup development environment
setup-dev: install
	pip install black isort flake8 mypy
	playwright install
	@echo "Development environment setup complete!"

# Run tests with coverage
test-coverage:
	pytest --cov=src --cov-report=html --cov-report=term-missing

# Quick diagnostic test
test-quick:
	python Testing_Scripts/quick_network_diagnostic.py

# Run stealth test
test-stealth:
	python Testing_Scripts/advanced_diagnostic_test.py