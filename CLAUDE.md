# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

This project uses Docker/Podman for containerized development (recommended) or local development with UV.

### Setup Commands
- `make setup-dev` - Full development setup (Docker, dependencies, pre-commit hooks)
- `make setup-local-dev` - Local Python environment setup with UV

### Container Management
- `make docker-up` - Start all services (FastAPI + Neo4j)
- `make docker-down` - Stop all services
- `make docker-shell` - Access container shell for development
- `make neo4j-only` - Start only Neo4j services for local development

### Code Quality and Testing
- `make format` - Run all code formatters (isort, black, flake8, pylint)
- `make test-small` - Run fast unit tests
- `make test-medium` - Run integration tests with database
- `make test-all` - Run complete test suite with coverage
- `make test-module TEST_PATH=tests/small/test_module.py` - Run specific test module
- `make test-case TEST_PATH=tests/small/test_module.py TEST_CASE="test_function"` - Run specific test

### Model Management
- `make download-model-docker` - Download/setup ML model in container
- `make download-model-local` - Download ML model locally

## Architecture Overview

### Core Components
- **FastAPI Application**: Main API server with GraphQL endpoint (`src/chronicler_backend/main.py`)
- **Neo4j Database**: Graph database for storing historical entities and relationships
- **Vector Embeddings**: Sentence transformer models for semantic search capabilities
- **GraphQL Schema**: Strawberry-based API with queries and mutations

### Key Modules
- `db/neo4j.py` - Database connection and session management
- `db/node.py` - Node CRUD operations and graph queries
- `embeddings/manager.py` - Singleton model manager with ONNX optimization
- `graphql/` - GraphQL schema, queries, and mutations
- `models/node.py` - Data models and type definitions

### Database Design
- Historical events, people, places stored as interconnected Neo4j nodes
- Vector embeddings generated for semantic similarity search
- Date range indexing for temporal queries
- Vector index for efficient similarity searches

### ML Model Integration
- Uses quantized sentence transformer models for efficiency
- Singleton pattern ensures model is loaded once across FastAPI workers
- ONNX backend optimization for production performance
- Token-aware text truncation to prevent model input limits

## Environment Configuration

Required environment variables (see `.env.example`):
- `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` - Database connection
- `FASTAPI_PORT`, `NEO4J_PORT` - Service ports
- CORS settings for cross-origin requests

## Testing Strategy

Tests are organized by complexity:
- `tests/small/` - Fast unit tests, no external dependencies
- `tests/medium/` - Integration tests requiring database
- `tests/large/` - Full system tests (if present)

Always run `make test-small` before commits. Use `make test-medium` for database-related changes.