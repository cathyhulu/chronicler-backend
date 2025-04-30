"""Unit tests for GraphQL mutations."""

from datetime import datetime

import pytest

from chronicler_backend.graphql.mutation import DateRangeInput, Mutation, NodeInput
from chronicler_backend.graphql.query import NodeType
from chronicler_backend.models.node import DateRange as ModelDateRange
from chronicler_backend.models.node import Node as ModelNode
from chronicler_backend.models.node import NodeType as ModelNodeType
from chronicler_backend.utils.constants import VECTOR_DIMENSION


class MockInfo:
    """Mock class for Strawberry GraphQL info object."""

    def __init__(self, context):
        self.context = context


@pytest.fixture
def mock_uuid() -> str:
    """Return a hardcoded UUID string for testing."""
    return "12345678-1234-5678-1234-567812345678"


def test_create_node(mocker, mock_uuid):
    """Test create_node mutation."""
    # Mock the NodeDatabase instance
    mock_node_db = mocker.MagicMock()

    # Setup the mock to return a node on creation
    created_model_node = ModelNode(
        uuid=mock_uuid,
        name="Test Node",
        node_type=ModelNodeType.EVENT,
        description="Test description",
        date_range=ModelDateRange(start=datetime(2020, 1, 1), end=datetime(2021, 1, 1)),
    )
    mock_node_db.create_node.return_value = created_model_node

    # Create mock db for context
    mock_db = mocker.MagicMock()

    # Create mock info object with proper context
    mock_info = MockInfo(context={"db": mock_db})

    # Mock NodeDatabase constructor
    mocker.patch("chronicler_backend.graphql.mutation.NodeDatabase", return_value=mock_node_db)

    # Create test input
    date_range_input = DateRangeInput(start=datetime(2020, 1, 1), end=datetime(2021, 1, 1))
    node_input = NodeInput(
        name="Test Node",
        node_type=NodeType.EVENT,
        description="Test description",
        date_range=date_range_input,
    )

    # Execute the mutation
    mutation = Mutation()
    result = mutation.create_node(mock_info, node_input)

    # Verify the database was called correctly
    mock_node_db.create_node.assert_called_once()

    # Verify the returned GraphQL node matches expected values
    assert result is not None
    assert result.uuid == mock_uuid
    assert result.name == "Test Node"
    assert result.node_type == NodeType.EVENT
    assert result.description == "Test description"
    assert result.hierarchy_rank == ModelNodeType.EVENT.value
    assert result.date_range is not None
    assert result.date_range.start == datetime(2020, 1, 1)
    assert result.date_range.end == datetime(2021, 1, 1)


def test_create_node_with_vector(mocker, mock_uuid):
    """Test create_node mutation with vector embedding."""
    # Mock the NodeDatabase instance
    mock_node_db = mocker.MagicMock()

    test_vector = [0.1] * VECTOR_DIMENSION

    # Setup the mock to return a node on creation
    created_model_node = ModelNode(
        uuid=mock_uuid,
        name="Vector Node",
        node_type=ModelNodeType.BATTLE,
        description="Node with vector",
        vector_embedding=test_vector,
    )
    mock_node_db.create_node.return_value = created_model_node

    # Create mock db for context and mock info
    mock_db = mocker.MagicMock()
    mock_info = MockInfo(context={"db": mock_db})

    # Mock NodeDatabase constructor
    mocker.patch("chronicler_backend.graphql.mutation.NodeDatabase", return_value=mock_node_db)

    # Create test input with vector
    node_input = NodeInput(
        name="Vector Node",
        node_type=NodeType.BATTLE,
        description="Node with vector",
        vector_embedding=test_vector,
    )

    # Execute the mutation
    mutation = Mutation()
    result = mutation.create_node(mock_info, node_input)

    # Verify the database was called correctly
    mock_node_db.create_node.assert_called_once()

    # Verify the returned GraphQL node
    assert result is not None
    assert result.name == "Vector Node"
    assert result.node_type == NodeType.BATTLE


def test_update_node(mocker):
    """Test update_node mutation."""
    # Mock the NodeDatabase instance
    mock_node_db = mocker.MagicMock()

    # Setup the mock to return a node on update
    updated_model_node = ModelNode(
        uuid="existing-uuid",
        name="Updated Node",
        node_type=ModelNodeType.WAR,
        description="Updated description",
        date_range=ModelDateRange(start=datetime(2020, 1, 1), end=datetime(2022, 1, 1)),
    )
    mock_node_db.update_node.return_value = updated_model_node

    # Also mock get_node to return an existing node
    existing_node = ModelNode(
        uuid="existing-uuid",
        name="Original Node",
        node_type=ModelNodeType.EVENT,
        description="Original description",
    )
    mock_node_db.get_node.return_value = existing_node

    # Create mock db and info
    mock_db = mocker.MagicMock()
    mock_info = MockInfo(context={"db": mock_db})

    # Mock NodeDatabase constructor
    mocker.patch("chronicler_backend.graphql.mutation.NodeDatabase", return_value=mock_node_db)

    # Create test input
    date_range_input = DateRangeInput(start=datetime(2020, 1, 1), end=datetime(2022, 1, 1))
    node_input = NodeInput(
        name="Updated Node",
        node_type=NodeType.WAR,
        description="Updated description",
        date_range=date_range_input,
    )

    # Execute the mutation
    mutation = Mutation()
    result = mutation.update_node(mock_info, uuid="existing-uuid", input=node_input)

    # Verify the database was called correctly
    mock_node_db.get_node.assert_called_once_with("existing-uuid")
    mock_node_db.update_node.assert_called_once()

    # Verify the returned GraphQL node
    assert result is not None
    assert result.uuid == "existing-uuid"
    assert result.name == "Updated Node"
    assert result.node_type == NodeType.WAR
    assert result.description == "Updated description"
    assert result.date_range is not None
    assert result.date_range.start == datetime(2020, 1, 1)
    assert result.date_range.end == datetime(2022, 1, 1)


def test_update_node_not_found(mocker):
    """Test update_node when the node doesn't exist."""
    # Mock the NodeDatabase instance
    mock_node_db = mocker.MagicMock()

    # Configure mock to return None (node not found)
    mock_node_db.get_node.return_value = None

    # Create mock db and info
    mock_db = mocker.MagicMock()
    mock_info = MockInfo(context={"db": mock_db})

    # Mock NodeDatabase constructor
    mocker.patch("chronicler_backend.graphql.mutation.NodeDatabase", return_value=mock_node_db)

    # Create test input
    node_input = NodeInput(
        name="Updated Node",
        node_type=NodeType.WAR,
        description="Updated description",
    )

    # Execute the mutation
    mutation = Mutation()
    result = mutation.update_node(mock_info, uuid="nonexistent-uuid", input=node_input)

    # Verify get_node was called but update_node was not
    mock_node_db.get_node.assert_called_once_with("nonexistent-uuid")
    mock_node_db.update_node.assert_not_called()

    # Result should be None for non-existent node
    assert result is None


def test_delete_node(mocker):
    """Test delete_node mutation."""
    # Mock the NodeDatabase instance
    mock_node_db = mocker.MagicMock()

    # Configure the mock to return True on deletion (success)
    mock_node_db.delete_node.return_value = True

    # Create mock db and info
    mock_db = mocker.MagicMock()
    mock_info = MockInfo(context={"db": mock_db})

    # Mock NodeDatabase constructor
    mocker.patch("chronicler_backend.graphql.mutation.NodeDatabase", return_value=mock_node_db)

    # Execute the mutation
    mutation = Mutation()
    result = mutation.delete_node(mock_info, uuid="test-uuid-to-delete")

    # Verify the database was called correctly
    mock_node_db.delete_node.assert_called_once_with("test-uuid-to-delete")

    # Verify result is True (success)
    assert result is True


def test_delete_node_failure(mocker):
    """Test delete_node mutation when deletion fails."""
    # Mock the NodeDatabase instance
    mock_node_db = mocker.MagicMock()

    # Configure the mock to return False on deletion (failure)
    mock_node_db.delete_node.return_value = False

    # Create mock db and info
    mock_db = mocker.MagicMock()
    mock_info = MockInfo(context={"db": mock_db})

    # Mock NodeDatabase constructor
    mocker.patch("chronicler_backend.graphql.mutation.NodeDatabase", return_value=mock_node_db)

    # Execute the mutation
    mutation = Mutation()
    result = mutation.delete_node(mock_info, uuid="nonexistent-uuid")

    # Verify the database was called correctly
    mock_node_db.delete_node.assert_called_once_with("nonexistent-uuid")

    # Verify result is False (failure)
    assert result is False


def test_create_relationship(mocker):
    """Test create_relationship mutation."""
    # Mock the database
    mock_db = mocker.MagicMock()

    # Configure the mock to return a success result for run_query
    mock_db.run_query.return_value = {"created": 1}

    # Create mock info object
    mock_info = MockInfo(context={"db": mock_db})

    # Execute the mutation
    mutation = Mutation()
    result = mutation.create_relationship(
        mock_info,
        from_uuid="source-uuid",
        to_uuid="target-uuid",
        relationship_type="PARTICIPATED_IN",
    )

    # Verify the database was called correctly
    mock_db.run_query.assert_called_once()

    # Check parameters passed to run_query
    call_args = mock_db.run_query.call_args
    assert "source-uuid" in str(call_args)
    assert "target-uuid" in str(call_args)
    assert "PARTICIPATED_IN" in str(call_args)

    # Verify result is True (relationship created)
    assert result is True


def test_create_relationship_failure(mocker):
    """Test create_relationship mutation when creation fails."""
    # Mock the database with an exception
    mock_db = mocker.MagicMock()
    mock_db.run_query.side_effect = Exception("Database error")

    # Create mock info object
    mock_info = MockInfo(context={"db": mock_db})

    # Mock logger to avoid test output noise
    mocker.patch("chronicler_backend.graphql.mutation.logger")

    # Execute the mutation
    mutation = Mutation()
    result = mutation.create_relationship(
        mock_info,
        from_uuid="invalid-uuid",
        to_uuid="invalid-uuid-2",
        relationship_type="INVALID_TYPE",
    )

    # Verify result is False (failed to create relationship)
    assert result is False


def test_create_node_invalid_vector_dimension(mocker):
    """Test create_node mutation with invalid vector dimension."""
    # Mock the NodeDatabase instance
    mock_node_db = mocker.MagicMock()

    # Create mock db and info
    mock_db = mocker.MagicMock()
    mock_info = MockInfo(context={"db": mock_db})

    # Mock NodeDatabase constructor
    mocker.patch("chronicler_backend.graphql.mutation.NodeDatabase", return_value=mock_node_db)

    # Create test input with an invalid vector dimension
    invalid_vector = [0.1] * 10  # Should be VECTOR_DIMENSION
    node_input = NodeInput(
        name="Invalid Vector Node",
        node_type=NodeType.EVENT,
        description="Node with invalid vector",
        vector_embedding=invalid_vector,
    )

    # Execute the mutation and expect ValueError
    mutation = Mutation()
    with pytest.raises(ValueError) as excinfo:
        mutation.create_node(mock_info, node_input)

    # Verify error message mentions vector dimension
    assert "Vector embedding must have exactly" in str(excinfo.value)
    assert f"{VECTOR_DIMENSION}" in str(excinfo.value)

    # Verify create_node was not called
    mock_node_db.create_node.assert_not_called()
