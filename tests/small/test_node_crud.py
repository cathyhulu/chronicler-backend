"""Unit tests for Node database operations."""

from datetime import datetime, timedelta

from chronicler_backend.db.node import NodeDatabase
from chronicler_backend.models.node import DateRange, Node, NodeType, RelationshipType
from chronicler_backend.utils.constants import VECTOR_DIMENSION


def test_node_crud_operations(neo4j_db):
    """Test basic CRUD operations for nodes."""
    # Create a NodeDatabase instance
    node_db = NodeDatabase(neo4j_db)

    # Create a test node
    test_node = Node(
        name="World War II",
        node_type=NodeType.WAR,
        description="Global war that lasted from 1939 to 1945",
        date_range=DateRange(start=datetime(1939, 9, 1), end=datetime(1945, 9, 2)),
    )

    # Create the node
    created_node = node_db.create_node(test_node)
    assert created_node is not None
    assert created_node.uuid == test_node.uuid
    assert created_node.name == "World War II"
    assert created_node.node_type == NodeType.WAR
    assert created_node.description == "Global war that lasted from 1939 to 1945"
    assert created_node.date_range is not None
    assert created_node.date_range.start.year == 1939
    assert created_node.date_range.end.year == 1945

    # Retrieve the node
    retrieved_node = node_db.get_node(created_node.uuid)
    assert retrieved_node is not None
    assert retrieved_node.uuid == created_node.uuid
    assert retrieved_node.name == created_node.name
    assert retrieved_node.node_type == created_node.node_type

    # Update the node
    retrieved_node.description = "Updated description for WWII"
    updated_node = node_db.update_node(retrieved_node)
    assert updated_node is not None
    assert updated_node.description == "Updated description for WWII"

    # Delete the node
    deleted = node_db.delete_node(created_node.uuid)
    assert deleted is True

    # Verify it's gone
    assert node_db.get_node(created_node.uuid) is None


def test_node_relationships(neo4j_db):
    """Test relationships between nodes."""
    # Create a NodeDatabase instance
    node_db = NodeDatabase(neo4j_db)

    # Create a parent node (country)
    country = Node(
        name="United States", node_type=NodeType.COUNTRY, description="North American nation"
    )
    created_country = node_db.create_node(country)

    # Create two child nodes (battles)
    battle1 = Node(
        name="Battle of Midway",
        node_type=NodeType.BATTLE,
        description="Naval battle in the Pacific Theater",
        date_range=DateRange(start=datetime(1942, 6, 4), end=datetime(1942, 6, 7)),
    )
    created_battle1 = node_db.create_node(battle1)

    battle2 = Node(
        name="D-Day",
        node_type=NodeType.BATTLE,
        description="Allied invasion of Normandy",
        date_range=DateRange(start=datetime(1944, 6, 6), end=datetime(1944, 6, 6)),
    )
    created_battle2 = node_db.create_node(battle2)

    # Create relationships using the new relationship type enum
    assert node_db.create_relationship(
        created_country.uuid, created_battle1.uuid, RelationshipType.PARTICIPATED_IN
    )
    assert node_db.create_relationship(
        created_country.uuid, created_battle2.uuid, RelationshipType.PARTICIPATED_IN
    )

    # Test getting relationships
    country_relationships = node_db.get_relationships(created_country.uuid, direction="OUTGOING")
    assert len(country_relationships) == 2

    # Check relationship types
    rel_types = [r["relationship_type"] for r in country_relationships]
    assert all(rel_type == RelationshipType.PARTICIPATED_IN.value for rel_type in rel_types)

    # Check that related nodes are the battles
    related_nodes = [r["other_node_uuid"] for r in country_relationships]
    assert created_battle1.uuid in related_nodes
    assert created_battle2.uuid in related_nodes

    # Get neighbors - should find both battles
    neighbors = node_db.get_node_neighbors(created_country.uuid, same_type_only=False)
    assert len(neighbors) == 2
    neighbor_names = [n.name for n in neighbors]
    assert "Battle of Midway" in neighbor_names
    assert "D-Day" in neighbor_names

    # Get neighbors of same type - should find none since there are no other countries
    same_type_neighbors = node_db.get_node_neighbors(created_country.uuid, same_type_only=True)
    assert len(same_type_neighbors) == 0

    # Clean up
    node_db.delete_node(created_battle1.uuid)
    node_db.delete_node(created_battle2.uuid)
    node_db.delete_node(created_country.uuid)


def test_search_by_date_range(neo4j_db):
    """Test searching nodes by date range."""
    node_db = NodeDatabase(neo4j_db)

    # Create nodes with different date ranges
    now = datetime.now()

    # Past event
    past_event = Node(
        name="Ancient Event",
        node_type=NodeType.EVENT,
        description="An event from ancient history",
        date_range=DateRange(
            start=now - timedelta(days=3650),  # ~10 years ago
            end=now - timedelta(days=3600),  # ~9.9 years ago
        ),
    )
    node_db.create_node(past_event)

    # Recent event
    recent_event = Node(
        name="Recent Event",
        node_type=NodeType.EVENT,
        description="A recent event",
        date_range=DateRange(
            start=now - timedelta(days=30),  # 30 days ago
            end=now - timedelta(days=25),  # 25 days ago
        ),
    )
    node_db.create_node(recent_event)

    # Ongoing event
    ongoing_event = Node(
        name="Ongoing Event",
        node_type=NodeType.EVENT,
        description="An ongoing event",
        date_range=DateRange(
            start=now - timedelta(days=10),  # 10 days ago
            end=now + timedelta(days=10),  # 10 days in future
        ),
    )
    node_db.create_node(ongoing_event)

    # Future event
    future_event = Node(
        name="Future Event",
        node_type=NodeType.EVENT,
        description="A future event",
        date_range=DateRange(
            start=now + timedelta(days=30),  # 30 days in future
            end=now + timedelta(days=40),  # 40 days in future
        ),
    )
    node_db.create_node(future_event)

    try:
        # Search for current events (should find ongoing)
        current_events = node_db.search_nodes_by_date_range(start_date=now, end_date=now)
        assert len(current_events) == 1
        assert current_events[0].name == "Ongoing Event"

        # Search for recent events (should find recent and ongoing)
        recent_events = node_db.search_nodes_by_date_range(
            start_date=now - timedelta(days=35), end_date=now
        )
        assert len(recent_events) == 2
        names = [event.name for event in recent_events]
        assert "Recent Event" in names
        assert "Ongoing Event" in names

        # Search for future events (should find ongoing and future)
        future_events = node_db.search_nodes_by_date_range(
            start_date=now, end_date=now + timedelta(days=50)
        )
        assert len(future_events) == 2
        names = [event.name for event in future_events]
        assert "Ongoing Event" in names
        assert "Future Event" in names

    finally:
        # Clean up
        for node in node_db.search_nodes_by_date_range():
            node_db.delete_node(node.uuid)


def test_vector_index_and_similarity_search(neo4j_db):
    """Test vector index setup and similarity search functionality."""
    # Create a NodeDatabase instance
    node_db = NodeDatabase(neo4j_db)

    # Set up vector index
    assert node_db.setup_vector_index() is True

    # Create test nodes with vector embeddings
    # Node 1 - History node with history-related vector
    history_node = Node(
        name="American Civil War",
        node_type=NodeType.WAR,
        description="Civil war fought in the United States from 1861 to 1865",
        date_range=DateRange(start=datetime(1861, 4, 12), end=datetime(1865, 5, 9)),
        # Simple test vector - mostly 1s in first half, 0s in second half
        vector_embedding=[1.0] * (VECTOR_DIMENSION // 2) + [0.0] * (VECTOR_DIMENSION // 2),
    )
    created_history = node_db.create_node(history_node)
    assert created_history is not None

    # Node 2 - Similar to Node 1 (high similarity)
    similar_history_node = Node(
        name="US Civil War Battle",
        node_type=NodeType.BATTLE,
        description="Major battle of the American Civil War",
        date_range=DateRange(start=datetime(1863, 7, 1), end=datetime(1863, 7, 3)),
        # Similar vector - mostly 1s in first half, small values in second half
        vector_embedding=[1.0] * (VECTOR_DIMENSION // 2) + [0.1] * (VECTOR_DIMENSION // 2),
    )
    created_similar = node_db.create_node(similar_history_node)
    assert created_similar is not None

    # Node 3 - Different topic node (low similarity)
    different_node = Node(
        name="Scientific Discovery",
        node_type=NodeType.EVENT,
        description="Major scientific breakthrough",
        date_range=DateRange(start=datetime(1945, 1, 1), end=datetime(1945, 12, 31)),
        # Different vector - 0s in first half, 1s in second half
        vector_embedding=[0.0] * (VECTOR_DIMENSION // 2) + [1.0] * (VECTOR_DIMENSION // 2),
    )
    created_different = node_db.create_node(different_node)
    assert created_different is not None

    try:
        # Search with a vector similar to the history nodes
        query_vector = [0.9] * (VECTOR_DIMENSION // 2) + [0.1] * (VECTOR_DIMENSION // 2)
        results = node_db.search_nodes_by_vector_similarity(query_vector, limit=3)

        # We should get at least 2 results
        assert len(results) >= 2

        # Extract names for easier assertions
        result_names = [node.name for node in results]

        # The most similar nodes should be the history-related ones
        assert "American Civil War" in result_names
        assert "US Civil War Battle" in result_names

        # The first result should be one of the history nodes (either the Civil War or Battle)
        assert results[0].name in ["American Civil War", "US Civil War Battle"]

        # The different node should be last if returned
        # (may not be returned if more than 3 nodes exist)
        if "Scientific Discovery" in result_names:
            last_index = result_names.index("Scientific Discovery")
            assert last_index == len(result_names) - 1

    finally:
        # Clean up
        node_db.delete_node(created_history.uuid)
        node_db.delete_node(created_similar.uuid)
        node_db.delete_node(created_different.uuid)
