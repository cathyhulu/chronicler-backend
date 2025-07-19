"""Large integration tests for full-stack GraphQL HTTP flow."""


def test_create_node_via_http(test_client, cleanup_test_nodes):
    """Test creating a node through the full HTTP → GraphQL → Neo4j stack."""
    # Sample test data
    node_data = {
        "name": "Test Historical Event",
        "nodeType": "EVENT",
        "description": "A test event for integration testing",
        "dateRange": {"start": "1945-05-08T00:00:00Z", "end": "1945-05-08T23:59:59Z"},
    }

    # Create node via HTTP GraphQL request
    create_mutation = """
    mutation CreateNode($input: NodeInput!) {
        createNode(input: $input) {
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

    response = test_client.post(
        "/graphql", json={"query": create_mutation, "variables": {"input": node_data}}
    )

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert "errors" not in data

    created_node = data["data"]["createNode"]
    node_id = created_node["uuid"]
    cleanup_test_nodes.append(node_id)  # Register for cleanup

    # Verify created node data
    assert created_node["name"] == node_data["name"]
    assert created_node["nodeType"] == node_data["nodeType"]
    assert created_node["description"] == node_data["description"]
    assert created_node["dateRange"]["start"] == node_data["dateRange"]["start"]
    assert created_node["dateRange"]["end"] == node_data["dateRange"]["end"]


def test_query_node_via_http(test_client, cleanup_test_nodes):
    """Test querying a node through the full HTTP → GraphQL → Neo4j stack."""
    # First create a test node
    node_data = {
        "name": "Test Person",
        "nodeType": "PERSON",
        "description": "A test person for querying",
        "dateRange": {"start": "1920-01-01T00:00:00Z", "end": "1990-12-31T23:59:59Z"},
    }

    create_mutation = """
    mutation CreateNode($input: NodeInput!) {
        createNode(input: $input) {
            uuid
        }
    }
    """

    create_response = test_client.post(
        "/graphql", json={"query": create_mutation, "variables": {"input": node_data}}
    )

    node_id = create_response.json()["data"]["createNode"]["uuid"]
    cleanup_test_nodes.append(node_id)

    # Now query the node
    query = """
    query GetNode($uuid: String!) {
        node(uuid: $uuid) {
            uuid
            name
            nodeType
            description
        }
    }
    """

    response = test_client.post("/graphql", json={"query": query, "variables": {"uuid": node_id}})

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert "errors" not in data

    queried_node = data["data"]["node"]
    assert queried_node["uuid"] == node_id
    assert queried_node["name"] == node_data["name"]
    assert queried_node["nodeType"] == node_data["nodeType"]
    assert queried_node["description"] == node_data["description"]


def test_graphql_context_has_database_connection(test_client, cleanup_test_nodes):
    """Test that GraphQL context properly receives the database connection from app state."""
    # This test specifically validates the fix made to main.py
    # where GraphQL context now uses request.app.state.db

    node_data = {
        "name": "DB Connection Test Node",
        "nodeType": "EVENT",
        "description": "Testing database connection in GraphQL context",
    }

    create_mutation = """
    mutation CreateNode($input: NodeInput!) {
        createNode(input: $input) {
            uuid
            name
        }
    }
    """

    response = test_client.post(
        "/graphql", json={"query": create_mutation, "variables": {"input": node_data}}
    )

    # If this succeeds, it means:
    # 1. FastAPI started correctly and created app.state.db
    # 2. GraphQL context getter received request.app.state.db
    # 3. GraphQL resolvers successfully used the database connection
    assert response.status_code == 200
    data = response.json()
    assert "errors" not in data

    node_id = data["data"]["createNode"]["uuid"]
    cleanup_test_nodes.append(node_id)

    # Verify the node was actually created in the database
    assert data["data"]["createNode"]["name"] == node_data["name"]
