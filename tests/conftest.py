"""
These fixtures are shared among all tests.
"""

import os
from typing import Generator

import pytest
from neo4j.exceptions import ServiceUnavailable

from chronicler_backend.db.neo4j import Neo4jDatabase
from chronicler_backend.utils.logging import get_logger

logger = get_logger(__name__)


@pytest.fixture(scope="module")
def neo4j_uri() -> str:
    """Get Neo4j URI for testing with proper host resolution.

    Returns:
        str: Neo4j URI
    """
    # Get test URI from environment variable with default that matches docker-compose.yml
    uri = os.getenv("NEO4J_TEST_URI", "bolt://neo4j-test:7687")
    logger.debug(f"Using Neo4j test URI: {uri}")
    return uri


@pytest.fixture(scope="module")
def neo4j_auth() -> tuple[str, str]:
    """Get Neo4j authentication for testing.

    Returns:
        tuple: Neo4j username and password
    """
    # Use test container auth if available
    user = os.getenv("NEO4J_TEST_USER", "neo4j")
    password = os.getenv("NEO4J_TEST_PASSWORD", "test")
    logger.debug(f"Using Neo4j test auth: ({user}, {'*' * len(password)})")
    return user, password


@pytest.fixture(scope="module")
def neo4j_db(neo4j_uri: str, neo4j_auth: tuple[str, str]) -> Generator[Neo4jDatabase, None, None]:
    """Create and return a Neo4j database instance for testing.

    Args:
        neo4j_uri: Neo4j URI
        neo4j_auth: Neo4j authentication

    Returns:
        Neo4jDatabase: Database instance
    """
    user, password = neo4j_auth
    db = Neo4jDatabase(uri=neo4j_uri, user=user, password=password)

    try:
        # Test the connection and clear database before tests
        with db.get_session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            logger.debug("Connected to Neo4j test database and cleared data")
    except ServiceUnavailable as e:
        logger.error(f"Failed to connect to Neo4j: {e}")
        raise pytest.skip(f"Neo4j database not available: {e}")

    yield db

    # Clear database after tests
    try:
        with db.get_session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            logger.debug("Cleared Neo4j test data after tests")
    except Exception as e:
        logger.warning(f"Failed to clear Neo4j data after tests: {e}")

    # Close connection after tests
    try:
        db.close()
        logger.debug("Closed Neo4j connection")
    except Exception as e:
        logger.warning(f"Error while closing Neo4j connection: {e}")
