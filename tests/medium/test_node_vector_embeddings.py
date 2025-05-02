"""
Medium-sized tests validating node creation with vector embeddings and semantic querying.

These tests use actual model inference and Neo4j connections.
"""

from datetime import datetime

import pytest

from chronicler_backend.models.node import DateRange, Node, NodeType
from chronicler_backend.utils.constants import VECTOR_DIMENSION
from chronicler_backend.utils.logging import get_logger

logger = get_logger(__name__)


@pytest.mark.asyncio
async def test_create_node_with_embedded_description(node_db):
    """Test creating nodes with vector embeddings generated from descriptions."""
    # Create a node with a rich description
    world_war_node = Node(
        name="World War II",
        node_type=NodeType.WAR,
        description=(
            "Global conflict from 1939-1945 involving most nations"
            " including the US, USSR, UK, and Germany. "
            "It was the most widespread war in history"
            " with fighting in Europe, Pacific, and Africa."
        ),
        date_range=DateRange(start=datetime(1939, 9, 1), end=datetime(1945, 9, 2)),
    )

    # Create node without manually providing a vector embedding
    created_node = await node_db.create_node(world_war_node)

    # Verify the node was created
    assert created_node is not None
    assert created_node.uuid == world_war_node.uuid

    # Verify that a vector embedding was automatically generated
    assert created_node.vector_embedding is not None
    assert len(created_node.vector_embedding) == VECTOR_DIMENSION

    # All vectors should be float values between -1 and 1
    assert all(-1 <= x <= 1 for x in created_node.vector_embedding)

    return created_node


@pytest.mark.asyncio
async def test_semantic_search_related_wars(node_db, model_manager):
    """Test semantic search by finding related wars."""
    # Create multiple war nodes with different descriptions
    ww2_node = Node(
        name="World War II",
        node_type=NodeType.WAR,
        description=(
            "Global conflict from 1939-1945 involving most nations "
            "including the US, USSR, UK, and Germany. "
            "It was the most widespread war in history with fighting"
            " in Europe, Pacific, and Africa."
        ),
        date_range=DateRange(start=datetime(1939, 9, 1), end=datetime(1945, 9, 2)),
    )

    civil_war_node = Node(
        name="American Civil War",
        node_type=NodeType.WAR,
        description=(
            "War fought in the United States from 1861 to 1865 "
            "between the Union and the Confederacy "
            "over slavery and states' rights."
        ),
        date_range=DateRange(start=datetime(1861, 4, 12), end=datetime(1865, 5, 9)),
    )

    vietnam_war_node = Node(
        name="Vietnam War",
        node_type=NodeType.WAR,
        description=(
            "Cold War-era conflict in Vietnam, Laos, and Cambodia"
            " from 1954 to 1975 between North Vietnam "
            "and South Vietnam, with the US supporting South Vietnam."
        ),
        date_range=DateRange(start=datetime(1954, 11, 1), end=datetime(1975, 4, 30)),
    )

    # Node with unrelated historical content
    moon_landing_node = Node(
        name="Apollo 11 Moon Landing",
        node_type=NodeType.EVENT,
        description=(
            "NASA's mission in July 1969 that "
            "landed the first humans on the Moon, "
            "with Neil Armstrong and Buzz Aldrin."
        ),
        date_range=DateRange(start=datetime(1969, 7, 16), end=datetime(1969, 7, 24)),
    )

    # Create all nodes
    created_nodes = []
    for node in [ww2_node, civil_war_node, vietnam_war_node, moon_landing_node]:
        created_node = await node_db.create_node(node)
        assert created_node is not None
        created_nodes.append(created_node)

    try:
        # Test 1: Search for content related to "global conflict involving many countries"
        search_text = "global conflict involving many countries"
        vector = model_manager.encode(search_text)
        results = node_db.search_nodes_by_vector_similarity(vector, limit=10)

        # Should find WW2 as most relevant
        assert any(n.name == "World War II" for n in results)
        # Check that WW2 is more relevant than other nodes
        ww2_index = next(i for i, n in enumerate(results) if n.name == "World War II")
        assert ww2_index <= 1, "World War II should be one of the most relevant results"

        # Test 2: Search for content related to "civil rights conflict"
        search_text = "civil rights struggle in America"
        vector = model_manager.encode(search_text)
        results = node_db.search_nodes_by_vector_similarity(vector, limit=10)

        # Should find Civil War as most relevant
        assert any(n.name == "American Civil War" for n in results)
        civil_war_index = next(i for i, n in enumerate(results) if n.name == "American Civil War")
        assert civil_war_index <= 1, "American Civil War should be one of the most relevant results"

        # Test 3: Search for content related to "space exploration"
        search_text = "space exploration astronauts"
        vector = model_manager.encode(search_text)
        results = node_db.search_nodes_by_vector_similarity(vector, limit=10)

        # Should find Moon Landing as most relevant
        assert any(n.name == "Apollo 11 Moon Landing" for n in results)
        moon_index = next(i for i, n in enumerate(results) if n.name == "Apollo 11 Moon Landing")
        assert moon_index <= 1, "Moon Landing should be one of the most relevant results"

    finally:
        # Clean up - remove test nodes
        for node in created_nodes:
            node_db.delete_node(node.uuid)


@pytest.mark.asyncio
async def test_vector_update_on_description_change(node_db, model_manager):
    """Test that changing a node's description updates its vector embedding."""
    # Create a node with initial description
    event_node = Node(
        name="Battle of Gettysburg",
        node_type=NodeType.BATTLE,
        description="Major battle of the American Civil War",
        date_range=DateRange(start=datetime(1863, 7, 1), end=datetime(1863, 7, 3)),
    )

    created_node = await node_db.create_node(event_node)
    assert created_node is not None
    original_vector = created_node.vector_embedding.copy()

    try:
        # Update the node with a more detailed description
        updated_node = Node(
            uuid=created_node.uuid,
            name=created_node.name,
            node_type=created_node.node_type,
            description=(
                "Major battle of the American Civil War fought in"
                " Pennsylvania over three days in July 1863, "
                "considered a turning point of the war with a decisive Union victory."
            ),
            date_range=created_node.date_range,
        )

        # Update the node and check that the vector has changed
        result = await node_db.update_node(updated_node)
        assert result is not None

        # The vector should have changed
        new_vector = result.vector_embedding
        assert new_vector is not None
        assert len(new_vector) == VECTOR_DIMENSION

        # Calculate difference between vectors to confirm they changed
        vector_diff = sum((a - b) ** 2 for a, b in zip(original_vector, new_vector))
        assert vector_diff > 0.1, "Vector embedding should change when description changes"

        # Verify original and new vectors are not the same
        assert original_vector != new_vector

    finally:
        # Clean up
        node_db.delete_node(created_node.uuid)
