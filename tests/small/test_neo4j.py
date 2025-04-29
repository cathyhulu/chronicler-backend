"""Unit tests for Neo4j database integration."""


def test_connection(neo4j_db):
    """Test Neo4j connection."""
    # Use return_single parameter to get the result directly
    result = neo4j_db.run_query("RETURN 1 AS one", return_single=True)
    assert result["one"] == 1
