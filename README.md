# chronicler-backend

A GraphQL API for [chronicler](https://github.com/cathyhulu/chronicler) with Neo4j database integration.

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) or [Podman](https://podman.io/docs/installation)
- [Git](https://git-scm.com/downloads)

### Quick Setup

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

## Development Workflow

### Starting and Stopping Services

- Start all services: `make docker-up`
- Stop all services: `make docker-down`
- Rebuild and restart: `make docker-restart`
- View logs: `make docker-logs`
- Check status: `make docker-status`
- Clean unused resources: `make docker-clean`
- Deep clean all resources: `make docker-deep-clean`

### Code Quality

All code quality tools run inside the Docker container:

- Format all code: `make format`
- Run isort: `make isort`
- Run black: `make black`
- Run flake8: `make flake8`
- Run pylint: `make pylint`

### Testing

Tests run inside the Docker container with access to a dedicated Neo4j test instance:

- Run all tests: `make docker-test`
- Run small tests: `make docker-test-small`
- Run medium tests: `make docker-test-medium`
- Run large tests: `make docker-test-large`

### Database Access

- Connect to Neo4j shell: `make neo4j-shell`
- Connect to Neo4j test shell: `make neo4j-test-shell`
- Access Neo4j Browser: http://localhost:7474

### Container Access

- Open a shell in the FastAPI container: `make docker-shell`

## Project Structure

```
./
├── src/                           # Source code
│   └── chronicler_backend/
│       ├── main.py                # FastAPI application
│       ├── db/
│       │   └── neo4j.py           # Neo4j database integration
│       └── graphql/               # Strawberry GraphQL schema
├── tests/                         # Tests
│   ├── small/                     # Small tests
│   ├── medium/                    # Medium tests
│   └── large/                     # Large tests
├── .env.example                   # Example environment variables
├── docker-compose.yml             # Docker Compose configuration
├── Dockerfile                     # Dockerfile for FastAPI application
├── Makefile                       # Makefile with various commands
├── pyproject.toml                 # Project dependencies and configuration
└── README.md                      # This file
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