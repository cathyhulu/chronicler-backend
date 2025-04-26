"""Unit tests for Neo4j database integration."""


def test_connection(neo4j_db):
    """Test Neo4j connection."""
    # Use return_single parameter to get the result directly
    result = neo4j_db.run_query("RETURN 1 AS one", return_single=True)
    assert result["one"] == 1


def test_create_and_retrieve_nodes(neo4j_db):
    """Test creating and retrieving nodes."""
    # Create a test node with return_single parameter
    result = neo4j_db.run_query(
        "CREATE (p:Person {name: $name, age: $age}) RETURN p",
        {"name": "Alice", "age": 30},
        return_single=True,
    )
    # Assert that "p" is in the result
    assert "p" in result
    assert result["p"]["name"] == "Alice"
    assert result["p"]["age"] == 30

    # Retrieve nodes with the Person label
    nodes = neo4j_db.get_all_nodes("Person")

    # Assert that we have at least one Person node
    assert len(nodes) >= 1

    # Find Alice in the nodes
    alice = next((n for n in nodes if n["name"] == "Alice"), None)
    assert alice is not None
    assert alice["age"] == 30
