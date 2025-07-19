"""Large test fixtures for full-stack integration testing."""

import os

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient

from chronicler_backend.main import app
from chronicler_backend.utils.logging import get_logger

logger = get_logger(__name__)

# Load environment variables from .env file
load_dotenv()


@pytest.fixture
def test_client():
    """FastAPI test client that runs the full application stack with test database."""
    # Override environment variables to use test database from .env
    original_env = {}
    test_env = {
        "NEO4J_URI": os.getenv("NEO4J_TEST_URI"),
        "NEO4J_USER": os.getenv("NEO4J_TEST_USER"),
        "NEO4J_PASSWORD": os.getenv("NEO4J_TEST_PASSWORD"),
    }

    # Validate that all required test environment variables are set
    for key, value in test_env.items():
        if value is None:
            raise ValueError(f"Required test environment variable {key} is not set in .env file")

    # Store original values and set test values
    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value

    try:
        # Create test client with test environment
        client = TestClient(app)
        yield client
    finally:
        # Restore original environment
        for key, original_value in original_env.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value


@pytest.fixture
def cleanup_test_nodes(test_client):
    """
    Fixture that provides a list for tracking test node IDs and ensures cleanup
    even on test failure.

    Usage:
        def test_something(cleanup_test_nodes):
            # Create test node
            node_id = create_node_somehow()
            cleanup_test_nodes.append(node_id)  # Register for cleanup
            # Test continues...
    """
    created_node_ids = []

    # Yield the list that tests can append to
    yield created_node_ids

    # Cleanup always runs, even on test failure
    if created_node_ids:
        try:
            # Use GraphQL mutation to clean up test nodes one by one
            for node_id in created_node_ids:
                cleanup_mutation = """
                mutation DeleteNode($uuid: String!) {
                    deleteNode(uuid: $uuid)
                }
                """

                response = test_client.post(
                    "/graphql", json={"query": cleanup_mutation, "variables": {"uuid": node_id}}
                )

                if response.status_code != 200:
                    logger.warning(
                        f"Failed to delete test node {node_id}: HTTP {response.status_code}"
                    )

        except Exception as e:
            # Log cleanup failure but don't fail the test
            logger.warning(f"Failed to cleanup test nodes {created_node_ids}: {e}")
