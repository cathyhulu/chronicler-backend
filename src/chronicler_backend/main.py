"""Main FastAPI application for the Chronicler backend."""

import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter

from chronicler_backend.db.neo4j import Neo4jDatabase, get_db
from chronicler_backend.db.node import NodeDatabase
from chronicler_backend.embeddings.api import load_model_on_startup
from chronicler_backend.graphql.schema import schema
from chronicler_backend.utils.logging import get_logger

logger = get_logger(__name__)


# Setup startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Add any initialization here
    logger.info("Starting up Chronicler Backend...")
    # Store the database connection for later cleanup
    app.state.db = Neo4jDatabase(
        uri=os.getenv("NEO4J_URI", "bolt://neo4j:7687"),
        user=os.getenv("NEO4J_USER", "neo4j"),
        password=os.getenv("NEO4J_PASSWORD", "chroniclerpass"),
    )

    # Initialize node database with necessary indexes
    logger.info("Setting up database indexes...")
    node_db = NodeDatabase(app.state.db)
    if node_db.setup_date_range_index():
        logger.info("Date range indexes set up successfully")
    else:
        logger.warning("Failed to set up date range indexes")

    # Set up vector index for similarity search
    try:
        if node_db.setup_vector_index():
            logger.info("Vector index set up successfully")
        else:
            logger.warning("Failed to set up vector index")
    except Exception as e:
        logger.warning(f"Error setting up vector index: {e}")

    # Start loading the model in the background during startup
    logger.info("Loading sentence transformer model...")
    load_model_on_startup()
    logger.info("Model loading initiated")

    yield
    # Shutdown: Add any cleanup here
    logger.info("Shutting down Chronicler Backend...")
    if hasattr(app.state, "db"):
        app.state.db.close()


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
    context_getter=lambda request: {"db": request.app.state.db},
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
