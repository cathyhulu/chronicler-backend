"""
These fixtures are shared among all tests.
"""

import os
import pytest
from neo4j import GraphDatabase

from chronicler_backend.db.neo4j import Neo4jDatabase


@pytest.fixture(scope="module")
def neo4j_uri():
    """Get Neo4j URI for testing.

    Returns:
        str: Neo4j URI
    """
    # Use test container URI if available
    return os.getenv("NEO4J_TEST_URI", "bolt://localhost:7688")


@pytest.fixture(scope="module")
def neo4j_auth():
    """Get Neo4j authentication for testing.

    Returns:
        tuple: Neo4j username and password
    """
    # Use test container auth if available
    user = os.getenv("NEO4J_TEST_USER", "neo4j")
    password = os.getenv("NEO4J_TEST_PASSWORD", "test")
    return user, password


@pytest.fixture(scope="module")
def neo4j_db(neo4j_uri, neo4j_auth):
    """Create and return a Neo4j database instance for testing.

    Args:
        neo4j_uri: Neo4j URI
        neo4j_auth: Neo4j authentication

    Returns:
        Neo4jDatabase: Database instance
    """
    user, password = neo4j_auth
    db = Neo4jDatabase(uri=neo4j_uri, user=user, password=password)

    # Clear database before tests
    with db.get_session() as session:
        session.run("MATCH (n) DETACH DELETE n")

    yield db
    db.close()
