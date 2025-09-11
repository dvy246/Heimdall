# Heimdall Financial Intelligence System - Development Makefile

.PHONY: help install install-dev test test-coverage lint format type-check security-check clean docker-build docker-run pre-commit setup-dev

# Default target
help:
	@echo "Heimdall Financial Intelligence System - Available Commands:"
	@echo ""
	@echo "Setup Commands:"
	@echo "  setup-dev        Set up development environment"
	@echo "  install          Install production dependencies"
	@echo "  install-dev      Install development dependencies"
	@echo ""
	@echo "Code Quality Commands:"
	@echo "  format           Format code with black and isort"
	@echo "  lint             Run flake8 linting"
	@echo "  type-check       Run mypy type checking"
	@echo "  security-check   Run bandit security analysis"
	@echo "  pre-commit       Run all pre-commit hooks"
	@echo ""
	@echo "Testing Commands:"
	@echo "  test             Run pytest test suite"
	@echo "  test-coverage    Run tests with coverage report"
	@echo ""
	@echo "Docker Commands:"
	@echo "  docker-build     Build Docker image"
	@echo "  docker-run       Run application in Docker"
	@echo ""
	@echo "Utility Commands:"
	@echo "  clean            Clean up temporary files"

# Development setup
setup-dev: install-dev pre-commit
	@echo "Development environment setup complete!"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install -e .[dev]

# Code formatting and quality
format:
	black src/ tests/ --line-length 120
	isort src/ tests/ --profile black --line-length 120

lint:
	flake8 src/ tests/ --max-line-length 120 --extend-ignore E203,W503

type-check:
	mypy src/ --ignore-missing-imports

security-check:
	bandit -r src/ -f json

pre-commit:
	pre-commit install
	pre-commit run --all-files

# Testing
test:
	pytest tests/ -v

test-coverage:
	pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

# Docker
docker-build:
	docker build -t heimdall:latest .

docker-run:
	docker run --env-file .env heimdall:latest

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .coverage htmlcov/ .pytest_cache/ .mypy_cache/
