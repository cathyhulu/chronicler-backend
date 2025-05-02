import pytest

from chronicler_backend.db.node import NodeDatabase
from chronicler_backend.utils.constants import VECTOR_DIMENSION
from chronicler_backend.utils.logging import get_logger

logger = get_logger(__name__)


@pytest.fixture(autouse=True)
def mock_generate_vector_embedding(mocker):
    """Automatically mock vector embedding generation to return a default vector.

    This mocks the actual method in the NodeDatabase class, not the import path.

    Args:
        mocker: pytest's mocker fixture

    Returns:
        Mock object for the _generate_vector_embedding method
    """
    # Create a default vector of ones with the correct dimension
    default_vector = [1.0] * VECTOR_DIMENSION

    # Mock the actual method on the class itself
    original_method = NodeDatabase._generate_vector_embedding

    async def mock_generate_vector(*args, **kwargs):
        logger.debug("Using mocked vector embedding generator")
        return default_vector

    # Replace the method on the class
    NodeDatabase._generate_vector_embedding = mock_generate_vector

    yield

    # Restore the original method after tests
    NodeDatabase._generate_vector_embedding = original_method
