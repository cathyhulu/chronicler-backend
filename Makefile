.PHONY: clean

SOURCE_DIR=./src
SOURCE_PATH=./src/chronicler-backend
TESTS_DIR=./tests
PYTEST_LOG_LEVEL=DEBUG
PYTEST_COV_MIN=50

# Load all environment variables from .env
# so that they are preloaded before running any command here
ifneq (,$(wildcard ./.env))
include .env
export
endif

# +++++++ +++++++ +++++++
# Housekeeping
# +++++++ +++++++ +++++++
clean:
	find . -type f -name ".DS_Store" -exec rm -rf {} +
	find . -type f -name "*.py[cod]" -exec rm -rf {} +
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ipynb_checkpoints" -exec rm -rf {} +

isort:
	uv run isort .

black:
	uv run black .

flake8:
# Configuration cotrolled by .flake8
	uv run flake8

pylint:
# Configuration cotrolled by .pylintrc
	uv run pylint **/*.py

format: isort black flake8 pylint

# ++++++++++++++++++++++++
# Local development
# ++++++++++++++++++++++++
setup-local-dev:
	uv venv
	uv pip install -e .[dev,test]
	uv run pre-commit install

run-local-server:
	uv run uvicorn src.chronicler_backend.main:app --reload

# ++++++++++++++++++++++++
# Unit testing
# ++++++++++++++++++++++++
define run_tests
	uv run pytest $1 \
	--cov-report term-missing --durations=5
endef

# Run all unit tests with coverage report
test-all:
	$(call run_tests,${TESTS_DIR}) --cov=${REPO_BASE_MODULE_NAME} \
	--cov-fail-under=${PYTEST_MIN_COVERAGE}

# Run small-sized unit tests with coverage report
test-small:
	$(call run_tests,${TESTS_DIR}/small)
	
# Run medium-sized unit tests with coverage report
test-medium:
	$(call run_tests,${TESTS_DIR}/medium)

# Run large-sized unit tests with coverage report
test-large:
	$(call run_tests,${TESTS_DIR}/large)

# Omit coverage report for precommit, which causes issues during cleanup when looking
# for .coverage.<some_id> files
test-precommit:
	uv run pytest ${TESTS_DIR}/small