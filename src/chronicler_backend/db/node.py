"""Neo4j node operations for the Chronicler backend."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from chronicler_backend.db.neo4j import Neo4jDatabase
from chronicler_backend.models.node import DateRange, Node, NodeType, RelationshipType
from chronicler_backend.utils.constants import VECTOR_DIMENSION

logger = logging.getLogger(__name__)


class NodeDatabase:
    """Node database operations for Neo4j graph interactions.

    This class provides comprehensive functionality for CRUD
    operations on nodes, relationship management, and advanced
    search capabilities including vector similarity and temporal queries.

    Key methods:
    - create_node: Create a new node in the graph database
    - get_node: Retrieve a node by its UUID
    - update_node: Update an existing node's properties
    - delete_node: Remove a node and its relationships
    - get_node_neighbors: Find connected nodes
    - search_nodes_by_vector_similarity: Find semantically similar nodes
    - search_nodes_by_date_range: Find nodes within a time period
    - create_relationship: Connect two nodes with a typed relationship
    - get_relationships: Retrieve a node's connections
    - setup_vector_index: Initialize vector search capabilities
    - setup_date_range_index: Initialize temporal search capabilities
    """

    def __init__(self, db: Neo4jDatabase):
        """Initialize node database operations.

        Args:
            db: Neo4j database connection
        """
        self.db = db

    def create_node(self, node: Node) -> Optional[Node]:
        """Create a new node in the database.

        Args:
            node: Node to create

        Returns:
            Node: Created node or None if creation failed
        """
        # Convert date_range to Neo4j datetime if present
        node_data = node.model_dump(exclude={"vector_embedding", "properties"})

        # Handle date range conversion for Neo4j
        if node.date_range:
            if node.date_range.start:
                node_data["date_range_start"] = node.date_range.start
            if node.date_range.end:
                node_data["date_range_end"] = node.date_range.end

            # Remove the original date_range dict as we've flattened it
            node_data.pop("date_range")

        # Handle node_type
        node_data["node_type"] = node.node_type.name
        node_data["node_type_rank"] = node.node_type.value

        # Handle vector embedding as a separate parameter if present
        vector_param = {}
        if node.vector_embedding:
            vector_param = {"vector": node.vector_embedding}

        # Create the node with all properties
        query = """
        CREATE (n:Node {uuid: $uuid})
        SET n += $properties
        """

        if node.vector_embedding:
            query += """
            SET n.vector_embedding = $vector
            """

        query += """
        RETURN n.uuid as uuid, n.name as name, n.node_type as node_type,
               n.description as description, n.node_type_rank as node_type_rank,
               n.date_range_start as date_range_start, n.date_range_end as date_range_end,
               n.vector_embedding as vector_embedding
        """

        try:
            result = self.db.run_query(
                query,
                {"uuid": node.uuid, "properties": node_data, **vector_param},
                return_single=True,
            )

            if result:
                return self._record_to_node(result)
            return None
        except Exception as e:
            logger.error(f"Error creating node: {e}")
            return None

    def get_node(self, uuid: str) -> Optional[Node]:
        """Get a node by UUID.

        Args:
            uuid: Node UUID

        Returns:
            Node: Node if found, None otherwise
        """
        query = """
        MATCH (n:Node {uuid: $uuid})
        RETURN n.uuid as uuid, n.name as name, n.node_type as node_type,
               n.description as description, n.node_type_rank as node_type_rank,
               n.date_range_start as date_range_start, n.date_range_end as date_range_end,
               n.vector_embedding as vector_embedding
        """

        try:
            result = self.db.run_query(query, {"uuid": uuid}, return_single=True)
            if result:
                return self._record_to_node(result)
            return None
        except Exception as e:
            logger.error(f"Error getting node {uuid}: {e}")
            return None

    def update_node(self, node: Node) -> Optional[Node]:
        """Update an existing node.

        Args:
            node: Node with updated values

        Returns:
            Node: Updated node or None if update failed
        """
        # Check if node exists
        existing = self.get_node(node.uuid)
        if not existing:
            logger.warning(f"Cannot update non-existent node: {node.uuid}")
            return None

        # Convert node to dictionary and prepare for update
        node_data = node.model_dump(exclude={"vector_embedding", "properties"})

        # Handle date range conversion for Neo4j
        if node.date_range:
            if node.date_range.start:
                node_data["date_range_start"] = node.date_range.start
            if node.date_range.end:
                node_data["date_range_end"] = node.date_range.end

            # Remove the original date_range dict as we've flattened it
            node_data.pop("date_range")

        # Handle node_type
        node_data["node_type"] = node.node_type.name
        node_data["node_type_rank"] = node.node_type.value

        # Handle vector embedding as a separate parameter if present
        vector_param = {}
        if node.vector_embedding:
            vector_param = {"vector": node.vector_embedding}

        # Update the node
        query = """
        MATCH (n:Node {uuid: $uuid})
        SET n += $properties
        """

        if node.vector_embedding:
            query += """
            SET n.vector_embedding = $vector
            """

        query += """
        RETURN n.uuid as uuid, n.name as name, n.node_type as node_type,
               n.description as description, n.node_type_rank as node_type_rank,
               n.date_range_start as date_range_start, n.date_range_end as date_range_end,
               n.vector_embedding as vector_embedding
        """

        try:
            result = self.db.run_query(
                query,
                {"uuid": node.uuid, "properties": node_data, **vector_param},
                return_single=True,
            )

            if result:
                return self._record_to_node(result)
            return None
        except Exception as e:
            logger.error(f"Error updating node {node.uuid}: {e}")
            return None

    def delete_node(self, uuid: str) -> bool:
        """Delete a node by UUID.

        Args:
            uuid: Node UUID

        Returns:
            bool: True if deleted, False otherwise
        """
        query = """
        MATCH (n:Node {uuid: $uuid})
        DETACH DELETE n
        RETURN count(n) as deleted
        """

        try:
            result = self.db.run_query(query, {"uuid": uuid}, return_single=True)
            return result and result.get("deleted", 0) > 0
        except Exception as e:
            logger.error(f"Error deleting node {uuid}: {e}")
            return False

    def get_node_neighbors(
        self, uuid: str, same_type_only: bool = True, limit: int = 10, offset: int = 0
    ) -> List[Node]:
        """Get all neighbors of a node.

        Args:
            uuid: Node UUID
            same_type_only: Only return nodes of the same type
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List[Node]: List of neighbor nodes
        """
        # Query to get neighbors, with optional type filtering
        if same_type_only:
            query = """
            MATCH (n:Node {uuid: $uuid})-[r]-(neighbor:Node)
            WHERE neighbor.node_type = n.node_type
            RETURN neighbor.uuid as uuid, neighbor.name as name,
                   neighbor.node_type as node_type, neighbor.description as description,
                   neighbor.node_type_rank as node_type_rank,
                   neighbor.date_range_start as date_range_start,
                   neighbor.date_range_end as date_range_end,
                   neighbor.vector_embedding as vector_embedding
            ORDER BY neighbor.name
            SKIP $offset
            LIMIT $limit
            """
        else:
            query = """
            MATCH (n:Node {uuid: $uuid})-[r]-(neighbor:Node)
            RETURN neighbor.uuid as uuid, neighbor.name as name,
                   neighbor.node_type as node_type, neighbor.description as description,
                   neighbor.node_type_rank as node_type_rank,
                   neighbor.date_range_start as date_range_start,
                   neighbor.date_range_end as date_range_end,
                   neighbor.vector_embedding as vector_embedding
            ORDER BY neighbor.name
            SKIP $offset
            LIMIT $limit
            """

        try:
            results = self.db.run_query(query, {"uuid": uuid, "limit": limit, "offset": offset})
            return [self._record_to_node(record) for record in results]
        except Exception as e:
            logger.error(f"Error getting neighbors for node {uuid}: {e}")
            return []

    def search_nodes_by_vector_similarity(
        self, vector: List[float], limit: int = 10, offset: int = 0
    ) -> List[Node]:
        """Search nodes by vector similarity.

        This assumes Neo4j has vector indices set up properly.

        Args:
            vector: Query vector
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List[Node]: List of nodes sorted by similarity
        """
        # Note: This query requires Neo4j with vector index capabilities
        # such as Neo4j 5.11+ with the Vector Search Plugin
        query = """
        CALL db.index.vector.queryNodes('node_vector_index', $k, $vector)
        YIELD node, score
        RETURN node.uuid as uuid, node.name as name,
               node.node_type as node_type, node.description as description,
               node.node_type_rank as node_type_rank,
               node.date_range_start as date_range_start,
               node.date_range_end as date_range_end,
               node.vector_embedding as vector_embedding,
               score
        ORDER BY score DESC
        SKIP $offset
        LIMIT $limit
        """

        try:
            results = self.db.run_query(
                query, {"vector": vector, "k": limit + offset, "offset": offset, "limit": limit}
            )
            return [self._record_to_node(record) for record in results]
        except Exception as e:
            logger.error(f"Error searching nodes by vector similarity: {e}")
            return []

    def search_nodes_by_date_range(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        node_type: Optional[Union[str, NodeType]] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Node]:
        """Search nodes by date range.

        Args:
            start_date: Start date for search range
            end_date: End date for search range
            node_type: Optional node type filter
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List[Node]: List of nodes in the specified date range
        """
        # Build query dynamically based on the provided filters
        query_parts = ["MATCH (n:Node)"]
        query_params = {"limit": limit, "offset": offset}
        where_clauses = []

        # Date range conditions
        if start_date:
            where_clauses.append("n.date_range_end >= $start_date")
            query_params["start_date"] = start_date

        if end_date:
            where_clauses.append("n.date_range_start <= $end_date")
            query_params["end_date"] = end_date

        # Node type filter
        if node_type:
            if isinstance(node_type, NodeType):
                where_clauses.append("n.node_type = $node_type")
                query_params["node_type"] = node_type.name
            else:
                where_clauses.append("n.node_type = $node_type")
                query_params["node_type"] = node_type

        # Add WHERE clause if we have conditions
        if where_clauses:
            query_parts.append("WHERE " + " AND ".join(where_clauses))

        # Complete the query
        query_parts.extend(
            [
                "RETURN n.uuid as uuid, n.name as name,",
                "n.node_type as node_type, n.description as description,",
                "n.node_type_rank as node_type_rank,",
                "n.date_range_start as date_range_start,",
                "n.date_range_end as date_range_end,",
                "n.vector_embedding as vector_embedding",
                "ORDER BY n.date_range_start",
                "SKIP $offset",
                "LIMIT $limit",
            ]
        )

        query = "\n".join(query_parts)

        try:
            results = self.db.run_query(query, query_params)
            return [self._record_to_node(record) for record in results]
        except Exception as e:
            logger.error(f"Error searching nodes by date range: {e}")
            return []

    def setup_vector_index(self) -> bool:
        """Set up vector index for similarity search.

        This should be called during app initialization.

        Returns:
            bool: True if successful, False otherwise
        """
        # Check if index exists
        check_query = """
        CALL db.indexes() YIELD name, type
        WHERE name = 'node_vector_index'
        RETURN count(*) > 0 as exists
        """

        try:
            result = self.db.run_query(check_query, return_single=True)
            if result and result.get("exists", False):
                logger.info("Vector index already exists")
                return True

            # Create index
            create_query = f"""
            CALL db.index.vector.createNodeIndex(
                'node_vector_index',
                'Node',
                'vector_embedding',
                {VECTOR_DIMENSION},
                'cosine'
            )
            """

            self.db.run_query(create_query)
            logger.info("Vector index created successfully")
            return True
        except Exception as e:
            logger.error(f"Error setting up vector index: {e}")
            return False

    def setup_date_range_index(self) -> bool:
        """Set up date range index for temporal queries.

        This should be called during app initialization.

        Returns:
            bool: True if successful, False otherwise
        """
        # Create indexes for date range fields
        try:
            # Create index on start date
            self.db.run_query(
                "CREATE INDEX node_date_start_idx "
                "IF NOT EXISTS FOR (n:Node) ON (n.date_range_start)"
            )

            # Create index on end date
            self.db.run_query(
                "CREATE INDEX node_date_end_idx IF NOT EXISTS FOR (n:Node) ON (n.date_range_end)"
            )

            # Create index on UUID
            self.db.run_query("CREATE INDEX node_uuid_idx IF NOT EXISTS FOR (n:Node) ON (n.uuid)")

            logger.info("Date range indexes created successfully")
            return True
        except Exception as e:
            logger.error(f"Error setting up date range indexes: {e}")
            return False

    def _record_to_node(self, record: Dict[str, Any]) -> Node:
        """Convert a Neo4j record to a Node model.

        Args:
            record: Neo4j record dictionary

        Returns:
            Node: Converted Node model
        """
        # Handle date range with Neo4j datetime conversion
        date_range = None
        start_date = record.get("date_range_start")
        end_date = record.get("date_range_end")

        # Convert Neo4j datetime objects to Python datetime objects if needed
        if start_date and hasattr(start_date, "to_native"):
            start_date = start_date.to_native()
        if end_date and hasattr(end_date, "to_native"):
            end_date = end_date.to_native()

        if start_date or end_date:
            date_range = DateRange(start=start_date, end=end_date)

        # Handle node type conversion from string to enum
        node_type = record.get("node_type")
        try:
            node_type = NodeType[node_type] if node_type else NodeType.EVENT
        except (KeyError, TypeError):
            logger.warning(f"Invalid node_type: {node_type}, defaulting to EVENT")
            node_type = NodeType.EVENT

        # Create and return the Node
        return Node(
            uuid=record.get("uuid"),
            name=record.get("name", ""),
            node_type=node_type,
            description=record.get("description"),
            date_range=date_range,
            vector_embedding=record.get("vector_embedding"),
        )

    def create_relationship(
        self, from_uuid: str, to_uuid: str, relationship_type: RelationshipType
    ) -> bool:
        """Create a relationship between two nodes with defined relationship type.

        Args:
            from_uuid: UUID of the source node
            to_uuid: UUID of the target node
            relationship_type: Type of relationship from RelationshipType enum

        Returns:
            bool: True if relationship was created, False otherwise
        """
        query = f"""
        MATCH (a:Node {{uuid: $from_uuid}})
        MATCH (b:Node {{uuid: $to_uuid}})
        CREATE (a)-[r:`{relationship_type.value}`]->(b)
        RETURN count(r) as created
        """

        try:
            result = self.db.run_query(
                query, {"from_uuid": from_uuid, "to_uuid": to_uuid}, return_single=True
            )
            return result and result.get("created", 0) > 0
        except Exception as e:
            logger.error(f"Error creating relationship {relationship_type.value}: {e}")
            return False

    def get_relationships(
        self,
        node_uuid: str,
        relationship_type: Optional[RelationshipType] = None,
        direction: str = "ANY",
    ) -> List[Dict[str, Any]]:
        """Get all relationships for a node, optionally filtered by type and direction.

        Args:
            node_uuid: UUID of the node
            relationship_type: Optional filter for relationship type
            direction: Direction of relationship: "OUTGOING", "INCOMING", or "ANY" (default)

        Returns:
            List[Dict]: List of relationships with connected node information
        """
        # Set up direction pattern for query
        if direction.upper() == "OUTGOING":
            direction_pattern = "-[r]->"
        elif direction.upper() == "INCOMING":
            direction_pattern = "<-[r]-"
        else:  # ANY
            direction_pattern = "-[r]-"

        # Set up relationship type filter
        rel_type_filter = ""
        params = {"node_uuid": node_uuid}

        if relationship_type:
            rel_type_filter = f":`{relationship_type.value}`"

        query = f"""
        MATCH (n:Node {{uuid: $node_uuid}}){direction_pattern}{rel_type_filter}(other:Node)
        RETURN r.uuid as relationship_id,
               type(r) as relationship_type,
               other.uuid as other_node_uuid,
               other.name as other_node_name,
               other.node_type as other_node_type,
               CASE WHEN startNode(r) = n THEN 'OUTGOING' ELSE 'INCOMING' END as direction
        """
        try:
            return self.db.run_query(query, params)
        except Exception as e:
            logger.error(f"Error getting relationships for node {node_uuid}: {e}")
            return []
