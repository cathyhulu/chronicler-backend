"""Main FastAPI application for the Chronicler backend."""

import os
from contextlib import asynccontextmanager
from typing import Any, Dict, List

import strawberry
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter

from chronicler_backend.db.neo4j import Neo4jDatabase, get_db
from chronicler_backend.graphql.schema import schema


# Setup startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Add any initialization here
    print("Starting up Chronicler Backend...")
    yield
    # Shutdown: Add any cleanup here
    print("Shutting down Chronicler Backend...")


# Initialize FastAPI app
app = FastAPI(
    title="Chronicler Backend",
    description="GraphQL API for the Chronicler application",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS settings from environment variables
cors_origins = os.getenv("CORS_ALLOW_ORIGINS", "*").split(",")
cors_methods = os.getenv("CORS_ALLOW_METHODS", "*").split(",")
cors_headers = os.getenv("CORS_ALLOW_HEADERS", "*").split(",")
cors_credentials = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=cors_credentials,
    allow_methods=cors_methods,
    allow_headers=cors_headers,
)

# Create GraphQL router with context that includes database
graphql_app = GraphQLRouter(
    schema,
    context_getter=lambda: {
        "db": Neo4jDatabase(
            uri=os.getenv("NEO4J_URI", "bolt://neo4j:7687"),
            user=os.getenv("NEO4J_USER", "neo4j"),
            password=os.getenv("NEO4J_PASSWORD", "chroniclerpass"),
        )
    },
)

# Add GraphQL routes
app.include_router(graphql_app, prefix="/graphql")


@app.get("/")
async def root():
    """Root endpoint.

    Returns:
        Dict: Basic API info
    """
    return {
        "message": "Welcome to Chronicler API",
        "graphql_endpoint": "/graphql",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health")
async def health(db: Neo4jDatabase = Depends(get_db)):
    """Health check endpoint.

    Args:
        db: Neo4j database dependency

    Returns:
        Dict: Health status
    """
    try:
        # Test database connection
        result = db.run_query("RETURN 1 as n")
        record = result.single()
        db_status = record and record["n"] == 1

        return {
            "status": "healthy" if db_status else "unhealthy",
            "database": "connected" if db_status else "disconnected",
            "version": "0.1.0",
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "version": "0.1.0",
        }
