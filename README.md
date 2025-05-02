# chronicler-backend

A GraphQL API for [chronicler](https://github.com/cathyhulu/chronicler) with Neo4j database integration.

## Overview

Chronicler-backend is a knowledge graph system for historical events and narratives. Historical events are stored on a Neo4j knowledge graph, where a sentence transformer model generates vector embeddings for semantic search capabilities. The system features:

- **Knowledge Graph Storage**: Historical events, people, places, and their relationships are modeled as interconnected nodes in a Neo4j graph database, enabling complex queries across linked data
- **Vector Embeddings**: Utilizes optimized and quantized sentence transformer models to generate semantic vector representations of textual content
- **Semantic Search**: Find historically related entities and events based on semantic meaning rather than just keyword matching
- **GraphQL API**: Flexible, strongly-typed API that allows for precise queries and mutations with minimal over-fetching
- **Scalable Architecture**: Containerized deployment with Docker/Podman for consistent development and production environments

This backend powers historical data exploration and visualization, allowing users to discover connections between historical events, people, and places through both explicit relationships and semantic similarity.

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) or [Podman](https://podman.io/docs/installation)
- [Git](https://git-scm.com/downloads)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/chronicler-backend.git
   cd chronicler-backend
   ```
2. Copy the `.env.example` file to a new `.env` file, and fill out the credential fields

3. Run the setup command:
   ```bash
   make setup-dev
   ```

   This will:
   - Build the Docker images
   - Start all services
   - Install pre-commit hooks

4. Access the application:
   - GraphiQL interface: http://localhost:8000/graphql
   - Neo4j Browser: http://localhost:7474 (Define username and password `.env`)

## Alternative: Local Development

For a simpler development workflow (especially for IDE integration)

1) Install [uv](https://docs.astral.sh/uv/getting-started/installation/)
2) Run `make setup-local-dev` to create a venv and install dependencies

## Development Workflow

This project supports two development approaches: container-based (recommended) and local development. Choose the one that best fits your needs.

### Container-Based Development (Recommended)

The containerized approach ensures consistent environments and includes all dependencies (including Neo4j).

```bash
# Start all services
make docker-up

# Run linting in the container
make format

# Run tests in the container
make test-small

# Access container shell
make docker-shell
```

#### Container Management

- Start all services: `make docker-up`
- Stop all services: `make docker-down`
- Rebuild and restart: `make docker-restart`
- View logs: `make docker-logs`
- Check status: `make docker-status`
- Clean unused resources: `make docker-clean`
- Deep clean all resources: `make docker-deep-clean`

#### Code Quality (Container-Based)

- Format all code: `make format`
- Run isort: `make isort`
- Run black: `make black`
- Run flake8: `make flake8`
- Run pylint: `make pylint`

#### Testing (Container-Based)

- Run all tests: `make test-all`
- Run small tests: `make test-small`
- Run medium tests: `make test-medium`
- Run large tests: `make test-large`
- Run specific module: `make test-module TEST_PATH=tests/small/test_module.py`
- Run specific test: `make test-case TEST_PATH=tests/small/test_module.py TEST_CASE="test_function"`

### Local Development (Simpler Option)

For a more straightforward workflow with better IDE integration:

```bash
# Set up local virtual environment
make setup-local-dev

# Start just the Neo4j services
make neo4j-only

# Run linting locally
uv run black .
uv run isort .
uv run flake8
uv run pylint **/*.py

# Run tests locally
PYTHONPATH=./src uv run pytest tests/small
```

This approach provides:
- Faster development cycles
- Simpler IDE integration (code navigation, autocomplete)
- Native execution of pre-commit hooks
- Local control of Python tooling

**Note:** You'll still need Neo4j running for database operations. Use `make neo4j-only` to start just the database containers.

### Database Access

- Connect to Neo4j shell: `make neo4j-shell`
- Connect to Neo4j test shell: `make neo4j-test-shell`
- Access Neo4j Browser: http://localhost:7474

### Pre-commit Hooks

This project uses pre-commit hooks to ensure code quality. For both local and container
based development, hooks are installed during setup

For container based devs, you can run pre-commit manually with:

```bash
make pre-commit-run
```

### IDE Integration

For VS Code users:
1. Set up local development with `make setup-local-dev`
2. Point VS Code to your local virtual environment
3. Use the Neo4j services with `make neo4j-only`

For development container users:
- Install the "Dev Containers" extension in VS Code
- Use the "Remote-Containers: Reopen in Container" command
- Note: This works best with Docker; Podman support is limited

## Project Structure

```
./
├── src/                           # Source code
│   └── chronicler_backend/
│       ├── main.py                # FastAPI application with API endpoints
│       ├── db/                    # Neo4j database integration and connection management
│       │   ├── neo4j.py           # Neo4j database connection and session management
│       │   └── node.py            # Node database operations and queries
│       ├── embeddings/            # Vector embedding functionality
│       │   ├── api.py             # Public API for embeddings
│       │   └── manager.py         # ModelManager for handling embeddings generation
│       ├── graphql/               # Strawberry GraphQL schema with types, queries and mutations
│       │   ├── mutation.py        # GraphQL mutation definitions
│       │   ├── query.py           # GraphQL query definitions
│       │   └── schema.py          # Main GraphQL schema configuration
│       ├── models/                # Data models and types
│       │   └── node.py            # Node model definitions and enums
│       └── utils/                 # Utility functions
│           ├── constants.py       # Application constants
│           └── logging.py         # Logging configuration
├── tests/                         # Tests
│   ├── small/                     # Small unit tests (fast, no external dependencies)
│   ├── medium/                    # Medium integration tests (DB interactions)
│   ├── large/                     # Large system tests (full API)
│   └── conftest.py                # Pytest fixtures and configuration
├── model_weights/                 # Directory for storing ML model weights
│   └── quantized-model/           # Quantized sentence transformer models
├── scripts/                       # Utility scripts
│   ├── download_model.py          # Script to download and quantize ML models
│   ├── entrypoint.sh              # Docker container entrypoint
│   ├── run-in-container.sh        # Script to run commands in Docker/Podman container
│   └── precommit-docker-check.sh  # Pre-commit hook to verify container status
├── logs/                          # Log files (gitignored)
├── .env.example                   # Example environment variables
├── docker-compose.yml             # Docker Compose configuration for services
├── Dockerfile                     # Dockerfile for FastAPI application
├── Makefile                       # Makefile with development commands
├── pyproject.toml                 # Project dependencies and configuration
├── TODO.md                        # Project task list and goals
└── README.md                      # Project documentation
```

## Configuration

The application is configured using environment variables defined in the `.env` file:

- `NEO4J_URI`: URI for connecting to Neo4j
- `NEO4J_USER`: Neo4j username
- `NEO4J_PASSWORD`: Neo4j password
- `FASTAPI_PORT`: Port for FastAPI server
- `NEO4J_PORT`: Port for Neo4j HTTP interface

See `.env.example` for the full list of configuration options.

## Architecture

This project uses:

- **Python 3.12**: Latest stable Python version
- **FastAPI**: Modern, fast web framework for building APIs
- **Neo4j**: Graph database for storing and querying connected data
- **GraphQL**: API query language for more flexible requests
- **Docker/Podman**: Containerization for consistent development and deployment
- **UV**: Fast Python package installer and resolver (using official UV container images)

## Contributing

1. Create a feature branch: `git checkout -b feature/my-feature`
2. Make your changes
3. Ensure Docker containers are running: `make docker-status`
4. Add dependencies (if needed)
```bash
make docker-shell
# Inside the container:
uv add package_name
# Exit with Ctrl+D when done
```
1. Run tests: `make docker-test`
2. Format code: `make format`
3. Commit your changes (pre-commit hooks will run automatically)
4. Push and create a pull request

### Pre-commit Hooks
This project uses pre-commit hooks to ensure code quality. The hooks run:
- Code formatting (isort, black, flake8, pylint)
- Small tests

Pre-commit hooks work with both Docker and Podman and require:
1. The containers to be running (make docker-up)
2. Script files to be executable (make scripts-executable)

You can run pre-commit manually with:

```bash
make pre-commit-run
```