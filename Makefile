.PHONY: clean docker-up docker-down docker-clean docker-deep-clean docker-build docker-logs docker-status \
		docker-shell docker-test docker-test-small docker-test-medium docker-test-large \
		format isort black flake8 pylint neo4j-shell neo4j-test-shell scripts-executable \
		podman-check download-model-local download-model-docker

SOURCE_DIR=./src
SOURCE_PATH=./src/chronicler-backend
MODEL_DIR=./model_weights
MODEL_PATH=./model_weights/quantized-model
TESTS_DIR=./tests
PYTEST_LOG_LEVEL=DEBUG
PYTEST_COV_MIN=50

# Docker/Podman configuration
DOCKER_CMD := $(strip $(shell command -v podman 2> /dev/null || echo docker))
DOCKER_CMD := $(notdir $(DOCKER_CMD))
# Check if using podman and adjust compose command accordingly
ifeq ($(DOCKER_CMD),podman)
	COMPOSE_CMD := $(DOCKER_CMD) compose
else
	COMPOSE_CMD := $(DOCKER_CMD)-compose
endif

# Podman specific settings
MACHINE_NAME := podman-machine-default
MACHINE_CPUS := 4
MACHINE_MEMORY := 4096

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
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name ".coverage*" -exec rm -f {} +

# Clean Neo4j database data with confirmation
clean-data:
	@echo "WARNING: This will delete all Neo4j database data!"
	@echo "This operation cannot be undone."
	@read -p "Are you sure you want to continue? [y/N] " confirm; \
	if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then \
		echo "Removing Neo4j data directory..."; \
		rm -rf ./data/neo4j; \
		echo "Neo4j data cleaned up"; \
	else \
		echo "Operation cancelled."; \
	fi

# Clean everything, including code and data
clean-all: clean clean-data

# ++++++++++++
# Code quality
# ++++++++++++
isort:
	$(DOCKER_CMD) exec -it chronicler-backend uv run isort .

black:
	$(DOCKER_CMD) exec -it chronicler-backend uv run black .

flake8:
	$(DOCKER_CMD) exec -it chronicler-backend uv run flake8

pylint:
	$(DOCKER_CMD) exec -it chronicler-backend uv run pylint **/*.py

format: 
	$(DOCKER_CMD) exec -it chronicler-backend /bin/bash -c "uv run isort . && uv run black . && uv run flake8 && uv run pylint **/*.py"

# Make all script files executable
scripts-executable:
	@chmod +x scripts/*.sh
	@echo "Made script files executable"

# Run pre-commit checks manually
pre-commit-run: scripts-executable
	pre-commit run --all-files

# ++++++++++++++++++++++++
# Initial setup
# ++++++++++++++++++++++++
setup-dev: scripts-executable
	@echo "Setting up development environment with Docker..."
	@if [ ! -f .env ]; then \
		echo "Error: .env file not found"; \
		echo "Please create a .env file before setting up the development environment."; \
		echo "You can use .env.example as a reference."; \
		exit 1; \
	fi
	@echo "Building docker images..."
	make docker-build
	@echo "Starting services..."
	make docker-up
	@echo "Installing pre-commit hooks..."
	$(DOCKER_CMD) exec -it chronicler-backend uv run pre-commit install
	@echo "Setup complete! Your development environment is ready."
	@echo "GraphiQL available at: http://localhost:8000/graphql"
	@echo "Neo4j Browser available at: http://localhost:7474"

# ++++++++++++++++++++++++
# Local development option
# ++++++++++++++++++++++++
setup-local-dev:
	@echo "Setting up local development environment..."
	@echo "Creating virtual environment..."
	uv venv
	uv pip install -e .[dev,test]
	@echo "Installing pre-commit hooks..."
	uv run pre-commit install
	@echo "Local development environment ready!"
	@echo "Note: You'll still need Neo4j running for database operations"
	@echo "Consider 'make neo4j-only' for just the Neo4j service if needed"
	@echo "You also may need to download the model locally using 'make download-model-local'"

# ++++++++++++++++++++++++
# Docker Compose Commands
# ++++++++++++++++++++++++
# Add podman-check target to handle Podman machine initialization
podman-check:
ifeq "$(DOCKER_CMD)" "podman"
	@echo "Detected podman, checking machine status..."
	@if ! podman machine list | grep -q "$(MACHINE_NAME).*Running"; then \
		echo "Initializing and starting podman machine..."; \
		podman machine init --cpus $(MACHINE_CPUS) --memory $(MACHINE_MEMORY) $(MACHINE_NAME) || true; \
		podman machine start $(MACHINE_NAME) || true; \
		echo "Podman machine started"; \
	else \
		echo "Podman machine is already running"; \
	fi
endif

# For running just Neo4j without the full stack
neo4j-only: podman-check
	$(COMPOSE_CMD) up -d neo4j neo4j-test
	@echo "Neo4j services started"
	@echo "Neo4j Browser available at: http://localhost:7474"

# Start all services with Docker Compose
docker-up: podman-check
	$(COMPOSE_CMD) up -d
	@echo "All services started with Docker Compose"
	@echo "Neo4j: http://localhost:$(NEO4J_PORT)"
	@echo "FastAPI: http://localhost:$(FASTAPI_PORT)/graphql"

# Stop all services with Docker Compose
docker-down: podman-check
	$(COMPOSE_CMD) down
	@echo "All services stopped with Docker Compose"

# Clean Docker/Podman resources (images, containers, etc.)
docker-clean: docker-down
	@echo "Cleaning Docker/Podman resources..."
	$(DOCKER_CMD) system prune -f
	@echo "Removed unused containers, networks, and dangling images"

# Deep clean all Docker/Podman resources including volumes
docker-deep-clean: docker-down
	@echo "WARNING: This will remove ALL Docker/Podman resources including volumes!"
	@echo "This operation cannot be undone."
	@read -p "Are you sure you want to continue? [y/N] " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		echo "Performing deep clean of Docker/Podman resources..."; \
		$(DOCKER_CMD) system prune -af --volumes; \
		if [ "$(DOCKER_CMD)" = "podman" ]; then \
			echo "Removing podman machine..."; \
			podman machine rm -f $(MACHINE_NAME) || true; \
			echo "Podman machine removed"; \
		fi; \
		echo "Deep clean completed"; \
	else \
		echo "Deep clean cancelled"; \
	fi

# Rebuild all services with Docker Compose
docker-build: podman-check
	$(COMPOSE_CMD) --progress=plain build
	@echo "All services rebuilt with Docker Compose"

# Rebuild and restart all services
docker-restart: docker-down docker-build docker-up

# Show logs for all services
docker-logs: podman-check
	$(COMPOSE_CMD) logs -f

# Show status of all services
docker-status: podman-check
	$(COMPOSE_CMD) ps

# Connect to the FastAPI container shell
docker-shell: podman-check
	$(DOCKER_CMD) exec -it chronicler-backend bash

# Connect to Neo4j shell
neo4j-shell: podman-check
	$(DOCKER_CMD) exec -it chronicler-neo4j cypher-shell \
	-u $(NEO4J_USER) -p $(NEO4J_PASSWORD)

# Connect to Neo4j test shell
neo4j-test-shell: podman-check
	$(DOCKER_CMD) exec -it chronicler-neo4j-test cypher-shell \
	-u $(NEO4J_TEST_USER) -p $(NEO4J_TEST_PASSWORD)

# Check Docker image sizes
docker-size: podman-check
	@echo "Checking Docker image sizes..."
	@echo "--------------------------------"
	@$(DOCKER_CMD) images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" | grep -E 'chronicler|REPOSITORY'
	@echo "--------------------------------"
	@echo "Total disk space used by Docker:"
	@$(DOCKER_CMD) system df


# +++++++ +++++++ +++++++
# Sized testing
# +++++++ +++++++ +++++++
define run_tests
	@mkdir -p logs
	export PYTHONPATH=${SOURCE_DIR} && \
	$(DOCKER_CMD) exec -it chronicler-backend /bin/bash -c " \
		uv run coverage run --data-file=/app/logs/.coverage --source=${SOURCE_DIR} --omit=\"*/tests/*\" \
		-m pytest -rs -vv --log-level=${PYTEST_LOG_LEVEL} $1" \
		> logs/pytest_output.log && \
	if [ -n "$2" ]; then \
		$(DOCKER_CMD) exec -it chronicler-backend uv run coverage report --data-file=/app/logs/.coverage \
		--fail-under=$2 -m >> logs/pytest_output.log; \
	else \
		$(DOCKER_CMD) exec -it chronicler-backend uv run coverage report --data-file=/app/logs/.coverage \
		-m >> logs/pytest_output.log; \
	fi
endef

test-all: podman-check
	$(call run_tests,${TESTS_DIR},${PYTEST_COV_MIN})

test-small: podman-check
	$(call run_tests,${TESTS_DIR}/small)

test-medium: podman-check
	$(call run_tests,${TESTS_DIR}/medium)

test-large: podman-check
	$(call run_tests,${TESTS_DIR}/large)

test-module: podman-check
ifndef TEST_PATH
	$(error TEST_PATH is not set. Set TEST_PATH to run it.)
endif
	@mkdir -p logs
	$(call run_tests,${TEST_PATH})

test-case: podman-check
ifndef TEST_PATH
	$(error TEST_PATH is not set. Set TEST_PATH to the module containing the test case.)
endif
ifndef TEST_CASE
	$(error TEST_CASE is not set. Set TEST_CASE to the name of the test case to run.)
endif
	@mkdir -p logs
	$(call run_tests,$(TEST_PATH) -k "$(TEST_CASE)")

# ++++++++++++++++++++++++
# Model Management
# ++++++++++++++++++++++++
# Download and quantize the sentence transformer model locally
# Usage: make download-model-local [force=true]
# force=true will force the download even if the model already exists
download-model-local:
	@echo "Downloading and quantizing sentence transformer model locally..."
	@mkdir -p $(MODEL_DIR) && \
	uv run scripts/download_model.py --output-dir $(MODEL_PATH) $(if $(filter true,$(force)),--force,)

# Download and quantize the sentence transformer model within the Docker container
download-model-docker: podman-check
	@echo "Checking for existing model files..."
	@if [ -d "$(MODEL_PATH)" ] && [ "$$(ls -A $(MODEL_PATH) 2>/dev/null)" ]; then \
		echo "Found existing model files, copying to container..."; \
		MODEL_PATH_DOCKER=$$(echo $(MODEL_PATH) | sed 's|^\./|/app/|'); \
		$(DOCKER_CMD) exec -it chronicler-backend bash -c "mkdir -p $$MODEL_PATH_DOCKER"; \
		$(DOCKER_CMD) cp $(MODEL_PATH)/. chronicler-backend:$$MODEL_PATH_DOCKER/; \
		echo "Model files copied to container!"; \
	else \
		echo "No existing model found. Downloading and quantizing in container..."; \
		MODEL_PATH_DOCKER=$$(echo $(MODEL_PATH) | sed 's|^\./|/app/|'); \
		$(DOCKER_CMD) exec -it chronicler-backend bash -c "mkdir -p $$MODEL_PATH_DOCKER \
		&& MODEL_PATH=$$MODEL_PATH_DOCKER uv run /app/scripts/download_model.py"; \
	fi
	@echo "Model setup complete!"
