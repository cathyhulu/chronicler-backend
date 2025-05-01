"""Unit tests for GraphQL schema."""

from datetime import datetime

from chronicler_backend.graphql.query import DateRange, NodeType, Query
from chronicler_backend.models.node import DateRange as ModelDateRange
from chronicler_backend.models.node import Node as ModelNode
from chronicler_backend.models.node import NodeType as ModelNodeType


class MockInfo:
    """Mock class for Strawberry GraphQL info object."""

    def __init__(self, context):
        self.context = context


def test_nodetype_enum_matches_model():
    """Test that the GraphQL NodeType enum matches the model's NodeType enum."""
    # Check that all model enum values are present in the GraphQL enum
    for model_type in ModelNodeType:
        # Check that the name exists in NodeType
        assert hasattr(
            NodeType, model_type.name
        ), f"NodeType.{model_type.name} missing from GraphQL enum"

        # Check that the value matches (in GraphQL enums, values are strings of the names)
        graphql_value = getattr(NodeType, model_type.name).value
        assert (
            graphql_value == model_type.name
        ), f"NodeType.{model_type.name} has value {graphql_value}, expected {model_type.name}"

    # Check that both enums have the same number of values
    model_enum_count = len(list(ModelNodeType))
    graphql_enum_count = len(list(NodeType))
    assert (
        graphql_enum_count == model_enum_count
    ), f"GraphQL enum has {graphql_enum_count} values, but model enum has {model_enum_count}"


def test_query_node(mocker):
    """Test the node query resolver."""
    # Mock the NodeDatabase instance
    mock_node_db = mocker.MagicMock()

    # Create a sample model node that will be returned by the mock
    sample_date_range = ModelDateRange(start=datetime(2020, 1, 1), end=datetime(2021, 1, 1))
    sample_model_node = ModelNode(
        uuid="test-uuid",
        name="Test Node",
        node_type=ModelNodeType.EVENT,
        description="Test description",
        date_range=sample_date_range,
    )

    # Configure the mock to return our sample node
    mock_node_db.get_node.return_value = sample_model_node

    # Create mock db for context
    mock_db = mocker.MagicMock()

    # Create mock info object with proper context structure
    mock_info = MockInfo(context={"db": mock_db})

    # Mock the NodeDatabase constructor to return our mock instance
    mocker.patch("chronicler_backend.graphql.query.NodeDatabase", return_value=mock_node_db)

    # Create an instance of the Query class and call the resolver
    query = Query()
    result = query.node(mock_info, uuid="test-uuid")

    # Verify that NodeDatabase.get_node was called with the correct UUID
    mock_node_db.get_node.assert_called_once_with("test-uuid")

    # Verify the returned GraphQL node matches our model node
    assert result is not None
    assert result.uuid == "test-uuid"
    assert result.name == "Test Node"
    assert result.node_type == NodeType.EVENT
    assert result.description == "Test description"
    assert result.hierarchy_rank == ModelNodeType.EVENT.value
    assert result.date_range is not None
    assert result.date_range.start == datetime(2020, 1, 1)
    assert result.date_range.end == datetime(2021, 1, 1)


def test_query_node_not_found(mocker):
    """Test node query when the node is not found."""
    # Mock the NodeDatabase instance
    mock_node_db = mocker.MagicMock()

    # Configure the mock to return None (node not found)
    mock_node_db.get_node.return_value = None

    # Create mock db for context
    mock_db = mocker.MagicMock()

    # Create mock info object with proper context structure
    mock_info = MockInfo(context={"db": mock_db})

    # Mock the NodeDatabase constructor to return our mock instance
    mocker.patch("chronicler_backend.graphql.query.NodeDatabase", return_value=mock_node_db)

    # Create an instance of the Query class and call the resolver
    query = Query()
    result = query.node(mock_info, uuid="nonexistent-uuid")

    # Verify that NodeDatabase.get_node was called with the correct UUID
    mock_node_db.get_node.assert_called_once_with("nonexistent-uuid")

    # Verify the result is None
    assert result is None


def test_query_nodes(mocker):
    """Test the nodes query resolver."""
    # Mock the NodeDatabase instance
    mock_node_db = mocker.MagicMock()

    # Create sample model nodes that will be returned by the mock
    sample_model_nodes = [
        ModelNode(
            uuid=f"test-uuid-{i}",
            name=f"Test Node {i}",
            node_type=ModelNodeType.EVENT,
            description=f"Description {i}",
        )
        for i in range(3)
    ]

    # Configure the mock to return our sample nodes
    mock_node_db.search_nodes_by_date_range.return_value = sample_model_nodes

    # Create mock db for context
    mock_db = mocker.MagicMock()

    # Create mock info object with proper context structure
    mock_info = MockInfo(context={"db": mock_db})

    # Mock the NodeDatabase constructor to return our mock instance
    mocker.patch("chronicler_backend.graphql.query.NodeDatabase", return_value=mock_node_db)

    # Create an instance of the Query class and call the resolver
    query = Query()
    result = query.nodes(mock_info, limit=10, offset=0)

    # Verify that NodeDatabase.search_nodes_by_date_range was called with the correct params
    mock_node_db.search_nodes_by_date_range.assert_called_once_with(limit=10, offset=0)

    # Verify the returned GraphQL nodes match our model nodes
    assert len(result) == 3
    for i, node in enumerate(result):
        assert node.uuid == f"test-uuid-{i}"
        assert node.name == f"Test Node {i}"
        assert node.node_type == NodeType.EVENT
        assert node.description == f"Description {i}"
        assert node.hierarchy_rank == ModelNodeType.EVENT.value


def test_query_node_neighbors(mocker):
    """Test the node_neighbors query resolver."""
    # Mock the NodeDatabase instance
    mock_node_db = mocker.MagicMock()

    # Create sample neighbor nodes
    sample_neighbors = [
        ModelNode(
            uuid=f"neighbor-{i}",
            name=f"Neighbor {i}",
            node_type=ModelNodeType.BATTLE,
            description=f"Neighbor Description {i}",
        )
        for i in range(2)
    ]

    # Configure the mock to return our sample neighbors
    mock_node_db.get_node_neighbors.return_value = sample_neighbors

    # Create mock db for context
    mock_db = mocker.MagicMock()

    # Create mock info object with proper context structure
    mock_info = MockInfo(context={"db": mock_db})

    # Mock the NodeDatabase constructor to return our mock instance
    mocker.patch("chronicler_backend.graphql.query.NodeDatabase", return_value=mock_node_db)

    # Create an instance of the Query class and call the resolver
    query = Query()
    result = query.node_neighbors(
        mock_info, uuid="test-uuid", same_type_only=True, limit=5, offset=0
    )

    # Verify that NodeDatabase.get_node_neighbors was called with the correct params
    mock_node_db.get_node_neighbors.assert_called_once_with(
        "test-uuid", same_type_only=True, limit=5, offset=0
    )

    # Verify the returned GraphQL nodes match our model nodes
    assert len(result) == 2
    for i, node in enumerate(result):
        assert node.uuid == f"neighbor-{i}"
        assert node.name == f"Neighbor {i}"
        assert node.node_type == NodeType.BATTLE
        assert node.description == f"Neighbor Description {i}"
        assert node.hierarchy_rank == ModelNodeType.BATTLE.value


def test_query_nodes_by_date_range(mocker):
    """Test the nodes_by_date_range query resolver."""
    # Mock the NodeDatabase instance
    mock_node_db = mocker.MagicMock()

    # Create sample model nodes with date ranges
    start_date = datetime(2020, 1, 1)
    end_date = datetime(2022, 1, 1)

    sample_model_nodes = [
        ModelNode(
            uuid=f"date-node-{i}",
            name=f"Date Node {i}",
            node_type=ModelNodeType.WAR,
            description=f"Date Range Node {i}",
            date_range=ModelDateRange(start=datetime(2020, i + 1, 1), end=datetime(2021, i + 1, 1)),
        )
        for i in range(2)
    ]

    # Configure the mock to return our sample nodes
    mock_node_db.search_nodes_by_date_range.return_value = sample_model_nodes

    # Create mock db for context
    mock_db = mocker.MagicMock()

    # Create mock info object with proper context structure
    mock_info = MockInfo(context={"db": mock_db})

    # Mock the NodeDatabase constructor to return our mock instance
    mocker.patch("chronicler_backend.graphql.query.NodeDatabase", return_value=mock_node_db)

    # Create an instance of the Query class and call the resolver
    query = Query()
    result = query.nodes_by_date_range(
        mock_info,
        start_date=start_date,
        end_date=end_date,
        node_type=NodeType.WAR,
        limit=10,
        offset=0,
    )

    # Verify that NodeDatabase.search_nodes_by_date_range was called with the correct params
    mock_node_db.search_nodes_by_date_range.assert_called_once_with(
        start_date=start_date, end_date=end_date, node_type=ModelNodeType.WAR, limit=10, offset=0
    )

    # Verify the returned GraphQL nodes match our model nodes
    assert len(result) == 2
    for i, node in enumerate(result):
        assert node.uuid == f"date-node-{i}"
        assert node.name == f"Date Node {i}"
        assert node.node_type == NodeType.WAR
        assert node.description == f"Date Range Node {i}"
        assert node.hierarchy_rank == ModelNodeType.WAR.value
        assert node.date_range is not None
        assert node.date_range.start == datetime(2020, i + 1, 1)
        assert node.date_range.end == datetime(2021, i + 1, 1)


def test_search_nodes_by_vector(mocker):
    """Test the search_nodes_by_vector query resolver."""
    # Mock the NodeDatabase instance
    mock_node_db = mocker.MagicMock()

    # Create sample model nodes
    sample_model_nodes = [
        ModelNode(
            uuid=f"vector-node-{i}",
            name=f"Vector Node {i}",
            node_type=ModelNodeType.CITY,
            description=f"Vector Search Node {i}",
        )
        for i in range(3)
    ]

    # Configure the mock to return our sample nodes
    mock_node_db.search_nodes_by_vector_similarity.return_value = sample_model_nodes

    # Create mock db for context
    mock_db = mocker.MagicMock()

    # Create mock info object with proper context structure
    mock_info = MockInfo(context={"db": mock_db})

    # Mock the NodeDatabase constructor to return our mock instance
    mocker.patch("chronicler_backend.graphql.query.NodeDatabase", return_value=mock_node_db)

    # Create a test vector (simplified for testing)
    test_vector = [0.1] * 10

    # Create an instance of the Query class and call the resolver
    query = Query()
    result = query.search_nodes_by_vector(mock_info, vector=test_vector, limit=10, offset=0)

    # Verify that NodeDatabase.search_nodes_by_vector_similarity was called with the correct params
    mock_node_db.search_nodes_by_vector_similarity.assert_called_once_with(
        vector=test_vector, limit=10, offset=0
    )

    # Verify the returned GraphQL nodes match our model nodes
    assert len(result) == 3
    for i, node in enumerate(result):
        assert node.uuid == f"vector-node-{i}"
        assert node.name == f"Vector Node {i}"
        assert node.node_type == NodeType.CITY
        assert node.description == f"Vector Search Node {i}"
        assert node.hierarchy_rank == ModelNodeType.CITY.value


def test_date_range_from_model():
    """Test the DateRange.from_model class method."""
    # Test with a valid model date range
    model_date_range = ModelDateRange(start=datetime(2020, 1, 1), end=datetime(2021, 1, 1))

    graphql_date_range = DateRange.from_model(model_date_range)

    assert graphql_date_range is not None
    assert graphql_date_range.start == datetime(2020, 1, 1)
    assert graphql_date_range.end == datetime(2021, 1, 1)

    # Test with None input
    assert DateRange.from_model(None) is None
