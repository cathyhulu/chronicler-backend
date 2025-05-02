"""
These fixtures are shared among medium-sized tests.
Unlike small tests, these may connect to real databases and services.
"""

import pytest

from chronicler_backend.db.node import NodeDatabase
from chronicler_backend.embeddings.api import get_model_manager
from chronicler_backend.utils.logging import get_logger

logger = get_logger(__name__)


@pytest.fixture(scope="function")
async def model_manager():
    """
    Create model manager instance for testing.

    Unlike small tests, this uses the actual model for embedding generation.

    Returns:
        ModelManager: Model manager instance
    """
    manager = await get_model_manager()
    manager.load_model(quantized=True, backend="onnx", verbose=True)
    return manager


@pytest.fixture(scope="module")
def node_db(neo4j_db):
    """
    Create a NodeDatabase instance for testing.

    Args:
        neo4j_db: Neo4j database instance

    Returns:
        NodeDatabase: Node database instance
    """
    db = NodeDatabase(neo4j_db)

    # Set up vector index
    assert db.setup_vector_index() is True

    return db
