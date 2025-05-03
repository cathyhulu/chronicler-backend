"""
Medium-sized tests that utilize schema.execute_sync() for API functionality testing.

These tests execute GraphQL queries and mutations directly against the schema
without mocking the resolvers, providing more comprehensive integration testing.
"""

from datetime import datetime

import pytest

from chronicler_backend.graphql.schema import schema
from chronicler_backend.models.node import DateRange, Node, NodeType, RelationshipType
from chronicler_backend.utils.logging import get_logger

logger = get_logger(__name__)


class TestGraphQLSchemaExecution:
    """Test class for executing GraphQL operations through the schema."""

    @pytest.mark.asyncio
    async def test_create_and_query_node(self, neo4j_db, node_db):
        """Test creating a node via GraphQL and then querying it."""
        # Define a GraphQL mutation to create a node
        create_mutation = """
        mutation CreateTestNode($input: NodeInput!) {
            createNode(input: $input) {
                uuid
                name
                nodeType
                description
                dateRange {
                    start
                    end
                }
                hierarchyRank
            }
        }
        """

        # Define the input variables
        node_input = {
            "name": "Test GraphQL Node",
            "nodeType": "EVENT",
            "description": "This node was created through a GraphQL mutation",
            "dateRange": {"start": "2020-01-01T00:00:00", "end": "2020-12-31T23:59:59"},
        }

        # Execute the mutation
        # Fix: Use root_value with context key instead of context parameter
        result = await schema.execute(
            create_mutation, variable_values={"input": node_input}, context_value={"db": neo4j_db}
        )

        # Check for errors
        assert result.errors is None, f"GraphQL errors: {result.errors}"

        # Verify the response data
        assert result.data is not None
        created_node = result.data["createNode"]
        assert created_node["name"] == "Test GraphQL Node"
        assert created_node["nodeType"] == "EVENT"
        assert created_node["hierarchyRank"] == NodeType.EVENT.value

        # Store the UUID for subsequent query
        node_uuid = created_node["uuid"]

        # Now query the node to verify it was created
        query = """
        query GetNode($uuid: String!) {
            node(uuid: $uuid) {
                uuid
                name
                nodeType
                description
                dateRange {
                    start
                    end
                }
            }
        }
        """

        # Execute the query
        result = await schema.execute(
            query, variable_values={"uuid": node_uuid}, context_value={"db": neo4j_db}
        )

        # Check for errors
        assert result.errors is None, f"GraphQL errors: {result.errors}"

        # Verify the response data
        assert result.data is not None
        queried_node = result.data["node"]
        assert queried_node["uuid"] == node_uuid
        assert queried_node["name"] == "Test GraphQL Node"
        assert queried_node["nodeType"] == "EVENT"

        # Clean up - delete the node
        try:
            delete_mutation = """
            mutation DeleteNode($uuid: String!) {
                deleteNode(uuid: $uuid)
            }
            """
            result = await schema.execute(
                delete_mutation, variable_values={"uuid": node_uuid}, context_value={"db": neo4j_db}
            )
            assert result.errors is None
            assert result.data["deleteNode"] is True
        except Exception as e:
            logger.error(f"Error cleaning up test node: {e}")
            # Fallback cleanup using NodeDatabase
            node_db.delete_node(node_uuid)

    @pytest.mark.asyncio
    async def test_semantic_search_via_graphql(self, neo4j_db, node_db):
        """Test semantic search via GraphQL API."""
        # Create test nodes first
        nodes = [
            Node(
                name="French Revolution",
                node_type=NodeType.EVENT,
                description=(
                    "A period of radical social and political upheaval "
                    "in France from 1789 to 1799."
                ),
                date_range=DateRange(start=datetime(1789, 7, 14), end=datetime(1799, 11, 9)),
            ),
            Node(
                name="Roman Empire",
                node_type=NodeType.CIVILIZATION,
                description=(
                    "Ancient civilization centered around the city of Rome,"
                    " spanning from 27 BC to 476 AD."
                ),
                date_range=DateRange(start=datetime(27, 1, 1, 0, 0, 0), end=datetime(476, 9, 4)),
            ),
            Node(
                name="Industrial Revolution",
                node_type=NodeType.ERA,
                description=(
                    "Transition to new manufacturing processes in "
                    "Europe and the United States, from 1760 to 1840."
                ),
                date_range=DateRange(start=datetime(1760, 1, 1), end=datetime(1840, 12, 31)),
            ),
        ]

        created_nodes = []
        for node in nodes:
            created_node = await node_db.create_node(node)
            created_nodes.append(created_node)

        try:
            # Query using the searchNodesByText operation
            search_query = """
            query SearchNodes($searchText: String!, $limit: Int!) {
                searchNodesByText(searchText: $searchText, limit: $limit) {
                    uuid
                    name
                    nodeType
                    description
                }
            }
            """

            # Search for content related to "ancient Rome"
            result = await schema.execute(
                search_query,
                variable_values={"searchText": "ancient Rome civilization", "limit": 1},
                context_value={"db": neo4j_db},
            )

            # Check for errors
            assert result.errors is None, f"GraphQL errors: {result.errors}"

            # Verify Roman Empire is in the results
            search_results = result.data["searchNodesByText"]
            assert any(
                node["name"] == "Roman Empire" for node in search_results
            ), "Roman Empire should be in search results"

            # Search for revolutions and verify both French and Industrial Revolutions are found
            result = await schema.execute(
                search_query,
                variable_values={"searchText": "revolution political changes", "limit": 2},
                context_value={"db": neo4j_db},
            )

            # Check for errors
            assert result.errors is None, f"GraphQL errors: {result.errors}"

            # Verify both revolution nodes are in the results
            search_results = result.data["searchNodesByText"]
            found_french = any(node["name"] == "French Revolution" for node in search_results)
            found_industrial = any(
                node["name"] == "Industrial Revolution" for node in search_results
            )

            # At least one of them should be found
            # (ideally both, but semantic search is probabilistic)
            assert (
                found_french and found_industrial
            ), "At least one revolution node should be in search results"

        finally:
            # Clean up - delete test nodes
            for node in created_nodes:
                node_db.delete_node(node.uuid)

    @pytest.mark.asyncio
    async def test_create_and_query_relationship(self, neo4j_db, node_db):
        """Test creating a relationship via GraphQL and then querying it via node_neighbors."""
        # Create two nodes first through the GraphQL API
        create_mutation = """
        mutation CreateNode($input: NodeInput!) {
            createNode(input: $input) {
                uuid
                name
            }
        }
        """

        # Create parent node
        country_input = {
            "name": "Great Britain",
            "nodeType": "COUNTRY",
            "description": "Island nation in northwestern Europe",
        }

        result = await schema.execute(
            create_mutation,
            variable_values={"input": country_input},
            context_value={"db": neo4j_db},
        )

        assert result.errors is None
        country_uuid = result.data["createNode"]["uuid"]

        # Create child node
        city_input = {
            "name": "London",
            "nodeType": "CITY",
            "description": "Capital city of Great Britain",
        }

        result = await schema.execute(
            create_mutation, variable_values={"input": city_input}, context_value={"db": neo4j_db}
        )

        assert result.errors is None
        city_uuid = result.data["createNode"]["uuid"]

        try:
            # Create relationship
            create_relationship_mutation = """
            mutation CreateRelationship(
                $fromUuid: String!,
                $toUuid: String!,
                $relType: RelationshipType!
            ) {
                createRelationship(
                    fromUuid: $fromUuid,
                    toUuid: $toUuid,
                    relationshipType: $relType
                )
            }
            """

            result = await schema.execute(
                create_relationship_mutation,
                variable_values={
                    "fromUuid": country_uuid,
                    "toUuid": city_uuid,
                    "relType": "CONTAINS",
                },
                context_value={"db": neo4j_db},
            )

            assert result.errors is None
            assert result.data["createRelationship"] is True

            # Query relationship through nodeNeighbors
            query = """
            query GetNeighbors($uuid: String!, $sameTypeOnly: Boolean!) {
                nodeNeighbors(uuid: $uuid, sameTypeOnly: $sameTypeOnly) {
                    uuid
                    name
                    nodeType
                    description
                }
            }
            """

            result = await schema.execute(
                query,
                variable_values={"uuid": country_uuid, "sameTypeOnly": False},
                context_value={"db": neo4j_db},
            )

            assert result.errors is None
            neighbors = result.data["nodeNeighbors"]
            assert len(neighbors) == 1
            assert neighbors[0]["uuid"] == city_uuid
            assert neighbors[0]["name"] == "London"

            # Query with rank filter
            rank_query = """
            query GetNeighborsWithRankFilter($uuid: String!, $rankFilter: RankFilterType!) {
                nodeNeighbors(uuid: $uuid, rankFilter: $rankFilter) {
                    uuid
                    name
                    nodeType
                }
            }
            """

            result = await schema.execute(
                rank_query,
                variable_values={"uuid": country_uuid, "rankFilter": "LOWER"},
                context_value={"db": neo4j_db},
            )

            # Check country has lower rank neighbor (city)
            assert result.errors is None
            neighbors = result.data["nodeNeighbors"]
            assert len(neighbors) == 1
            assert neighbors[0]["uuid"] == city_uuid
            assert neighbors[0]["nodeType"] == "CITY"

        finally:
            # Clean up - delete nodes
            node_db.delete_node(country_uuid)
            node_db.delete_node(city_uuid)

    @pytest.mark.asyncio
    async def test_update_node_via_graphql(self, neo4j_db, node_db):
        """Test updating a node via GraphQL."""
        # Create a node first
        node = Node(
            name="Original Node",
            node_type=NodeType.PERIOD,  # Changed from PERSON to PERIOD (an existing enum value)
            description="Original description",
            date_range=DateRange(start=datetime(1900, 1, 1), end=datetime(1970, 12, 31)),
        )

        created_node = await node_db.create_node(node)
        node_uuid = created_node.uuid

        try:
            # Update the node via GraphQL
            update_mutation = """
            mutation UpdateNode($uuid: String!, $input: NodeInput!) {
                updateNode(uuid: $uuid, input: $input) {
                    uuid
                    name
                    nodeType
                    description
                    dateRange {
                        start
                        end
                    }
                }
            }
            """

            update_input = {
                "name": "Updated Node",
                "nodeType": "PERIOD",
                "description": "Updated description with more details",
                "dateRange": {"start": "1900-01-01T00:00:00", "end": "1980-12-31T23:59:59"},
            }

            result = await schema.execute(
                update_mutation,
                variable_values={"uuid": node_uuid, "input": update_input},
                context_value={"db": neo4j_db},
            )

            # Check for errors
            assert result.errors is None, f"GraphQL errors: {result.errors}"

            # Verify update was successful
            updated = result.data["updateNode"]
            assert updated["name"] == "Updated Node"
            assert updated["description"] == "Updated description with more details"
            assert "1980" in updated["dateRange"]["end"]

            # Query to verify persistence
            query = """
            query GetNode($uuid: String!) {
                node(uuid: $uuid) {
                    name
                    description
                    dateRange {
                        end
                    }
                }
            }
            """

            result = await schema.execute(
                query, variable_values={"uuid": node_uuid}, context_value={"db": neo4j_db}
            )

            # Verify the node was updated in the database
            assert result.errors is None
            queried = result.data["node"]
            assert queried["name"] == "Updated Node"
            assert queried["description"] == "Updated description with more details"
            assert "1980" in queried["dateRange"]["end"]

        finally:
            # Clean up
            node_db.delete_node(node_uuid)

    @pytest.mark.asyncio
    async def test_node_relationships(self, neo4j_db, node_db):
        """Test getting node relationships via GraphQL."""
        # Create three nodes with relationships between them

        # Create first node - a historical event
        event_node = Node(
            name="World War II",
            node_type=NodeType.EVENT,
            description="Global conflict from 1939 to 1945",
            date_range=DateRange(start=datetime(1939, 9, 1), end=datetime(1945, 9, 2)),
        )

        # Create second node - a battle within that event
        battle_node = Node(
            name="Battle of Stalingrad",
            node_type=NodeType.BATTLE,
            description="Major battle during World War II",
            date_range=DateRange(start=datetime(1942, 8, 23), end=datetime(1943, 2, 2)),
        )

        # Create third node - a person who participated in the battle
        person_node = Node(
            name="Marshal Zhukov",
            node_type=NodeType.ENTITY,
            description="Soviet military commander",
        )

        # Create nodes in the database
        created_event = await node_db.create_node(event_node)
        created_battle = await node_db.create_node(battle_node)
        created_person = await node_db.create_node(person_node)

        # Get UUIDs for relationships
        event_uuid = created_event.uuid
        battle_uuid = created_battle.uuid
        person_uuid = created_person.uuid

        # Create relationships
        # Battle is part of the Event
        node_db.create_relationship(battle_uuid, event_uuid, RelationshipType.PART_OF)

        # Person participated in the Battle
        node_db.create_relationship(person_uuid, battle_uuid, RelationshipType.PARTICIPATED_IN)

        try:
            # Query for relationships using the nodeRelationships query
            query = """
            query GetNodeRelationships($uuid: String!, $limit: Int!) {
                nodeRelationships(uuid: $uuid, limit: $limit) {
                    sourceNodeUUID
                    targetNodeUUID
                    relationshipType
                }
            }
            """

            # Test relationships for the battle node (should have 2 relationships)
            result = await schema.execute(
                query,
                variable_values={"uuid": battle_uuid, "limit": 10},
                context_value={"db": neo4j_db},
            )

            # Check for errors
            assert result.errors is None, f"GraphQL errors: {result.errors}"

            # Verify relationships
            relationships = result.data["nodeRelationships"]
            assert len(relationships) == 2

            # Check for both relationships
            battle_event_rel = next(
                (
                    r
                    for r in relationships
                    if r["sourceNodeUUID"] == battle_uuid and r["targetNodeUUID"] == event_uuid
                ),
                None,
            )
            assert battle_event_rel is not None
            assert battle_event_rel["relationshipType"] == RelationshipType.PART_OF.value

            person_battle_rel = next(
                (
                    r
                    for r in relationships
                    if r["sourceNodeUUID"] == person_uuid and r["targetNodeUUID"] == battle_uuid
                ),
                None,
            )
            assert person_battle_rel is not None
            assert person_battle_rel["relationshipType"] == RelationshipType.PARTICIPATED_IN.value

            # Test with a limit
            limited_result = await schema.execute(
                query,
                variable_values={"uuid": battle_uuid, "limit": 1},
                context_value={"db": neo4j_db},
            )

            assert limited_result.errors is None
            limited_relationships = limited_result.data["nodeRelationships"]
            assert len(limited_relationships) == 1

        finally:
            # Clean up - delete nodes in reverse order to avoid constraint issues
            node_db.delete_node(person_uuid)
            node_db.delete_node(battle_uuid)
            node_db.delete_node(event_uuid)
