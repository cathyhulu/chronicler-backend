"""GraphQL query types for the Chronicler backend."""

import enum
from datetime import datetime
from typing import List, Optional

import strawberry
from strawberry.types import Info

from chronicler_backend.db.node import NodeDatabase
from chronicler_backend.models.node import DateRange as ModelDateRange
from chronicler_backend.models.node import NodeType as ModelNodeType
from chronicler_backend.utils.embeddings import model_manager
from chronicler_backend.utils.logging import get_logger

logger = get_logger(__name__)

# Auto-generate NodeType enum for GraphQL from the model definition
# Create the enum dynamically based on the model's NodeType
NodeTypeDict = {node_type.name: node_type.name for node_type in ModelNodeType}
NodeType = strawberry.enum(enum.Enum("NodeType", NodeTypeDict))


# Auto-generate DateRange type for GraphQL from the model definition
@strawberry.type
class DateRange:
    """Date range type for GraphQL, auto-generated from model definition."""

    # Match the fields from ModelDateRange
    start: Optional[datetime] = None
    end: Optional[datetime] = None

    @classmethod
    def from_model(cls, model_date_range: Optional[ModelDateRange]) -> Optional["DateRange"]:
        """Create a GraphQL DateRange from model DateRange.

        Args:
            model_date_range: DateRange model instance

        Returns:
            Optional[DateRange]: GraphQL DateRange instance or None
        """
        if model_date_range is None:
            return None
        return cls(start=model_date_range.start, end=model_date_range.end)


@strawberry.type
class Node:
    """Node type for GraphQL API."""

    uuid: str
    name: str
    node_type: NodeType
    description: Optional[str] = None
    date_range: Optional[DateRange] = None
    hierarchy_rank: int


@strawberry.type
class Query:
    """Root query type for GraphQL API."""

    @strawberry.field
    def node(self, info: Info, uuid: str) -> Optional[Node]:
        """Query to get a node by UUID.

        Args:
            info: GraphQL resolver info with context
            uuid: Node UUID

        Returns:
            Optional[Node]: Node if found, None otherwise
        """
        db = info.context["db"]
        node_db = NodeDatabase(db)

        node = node_db.get_node(uuid)
        if node:
            # Convert from model to GraphQL type
            return Node(
                uuid=node.uuid,
                name=node.name,
                node_type=NodeType[node.node_type.name],
                description=node.description,
                date_range=DateRange.from_model(node.date_range),
                hierarchy_rank=node.node_type.value,
            )
        return None

    @strawberry.field
    def nodes(self, info: Info, limit: int = 10, offset: int = 0) -> List[Node]:
        """Query to get all nodes with pagination.

        Args:
            info: GraphQL resolver info with context
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List[Node]: List of nodes
        """
        db = info.context["db"]

        # Use date range search with no filters to get all nodes
        node_db = NodeDatabase(db)
        nodes = node_db.search_nodes_by_date_range(limit=limit, offset=offset)

        # Convert from model to GraphQL type
        return [
            Node(
                uuid=node.uuid,
                name=node.name,
                node_type=NodeType[node.node_type.name],
                description=node.description,
                date_range=DateRange.from_model(node.date_range),
                hierarchy_rank=node.node_type.value,
            )
            for node in nodes
        ]

    @strawberry.field
    def node_neighbors(
        self, info: Info, uuid: str, same_type_only: bool = True, limit: int = 10, offset: int = 0
    ) -> List[Node]:
        """Query to get neighbors of a node.

        Args:
            info: GraphQL resolver info with context
            uuid: Node UUID
            same_type_only: Only return nodes of the same type
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List[Node]: List of neighbor nodes
        """
        db = info.context["db"]
        node_db = NodeDatabase(db)

        neighbors = node_db.get_node_neighbors(
            uuid, same_type_only=same_type_only, limit=limit, offset=offset
        )

        # Convert from model to GraphQL type
        return [
            Node(
                uuid=node.uuid,
                name=node.name,
                node_type=NodeType[node.node_type.name],
                description=node.description,
                date_range=DateRange.from_model(node.date_range),
                hierarchy_rank=node.node_type.value,
            )
            for node in neighbors
        ]

    @strawberry.field
    def nodes_by_date_range(
        self,
        info: Info,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        node_type: Optional[NodeType] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Node]:
        """Query nodes by date range.

        Args:
            info: GraphQL resolver info with context
            start_date: Start date for search range
            end_date: End date for search range
            node_type: Optional node type filter
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List[Node]: List of nodes in the specified date range
        """
        db = info.context["db"]
        node_db = NodeDatabase(db)

        # Convert GraphQL enum to model enum if provided
        model_node_type = None
        if node_type:
            model_node_type = ModelNodeType[node_type.name]

        nodes = node_db.search_nodes_by_date_range(
            start_date=start_date,
            end_date=end_date,
            node_type=model_node_type,
            limit=limit,
            offset=offset,
        )

        # Convert from model to GraphQL type
        return [
            Node(
                uuid=node.uuid,
                name=node.name,
                node_type=NodeType[node.node_type.name],
                description=node.description,
                date_range=DateRange.from_model(node.date_range),
                hierarchy_rank=node.node_type.value,
            )
            for node in nodes
        ]

    @strawberry.field
    def search_nodes_by_vector(
        self, info: Info, vector: List[float], limit: int = 10, offset: int = 0
    ) -> List[Node]:
        """Search nodes by vector similarity.

        Args:
            info: GraphQL resolver info with context
            vector: Query vector
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List[Node]: List of nodes sorted by similarity
        """
        db = info.context["db"]
        node_db = NodeDatabase(db)

        nodes = node_db.search_nodes_by_vector_similarity(vector=vector, limit=limit, offset=offset)

        # Convert from model to GraphQL type
        return [
            Node(
                uuid=node.uuid,
                name=node.name,
                node_type=NodeType[node.node_type.name],
                description=node.description,
                date_range=DateRange.from_model(node.date_range),
                hierarchy_rank=node.node_type.value,
            )
            for node in nodes
        ]

    @strawberry.field
    def search_nodes_by_text(
        self, info: Info, search_text: str, limit: int = 10, offset: int = 0
    ) -> List[Node]:
        """Search nodes by semantic similarity to the given text.

        This query converts the input text to a vector embedding and
        then performs a vector similarity search.

        Args:
            info: GraphQL resolver info with context
            search_text: Text to search for
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List[Node]: List of nodes sorted by semantic similarity
        """
        db = info.context["db"]
        node_db = NodeDatabase(db)

        try:
            # Generate embedding from search text
            vector = model_manager.encode(search_text)

            # Search using the vector
            nodes = node_db.search_nodes_by_vector_similarity(
                vector=vector, limit=limit, offset=offset
            )

            # Convert from model to GraphQL type
            return [
                Node(
                    uuid=node.uuid,
                    name=node.name,
                    node_type=NodeType[node.node_type.name],
                    description=node.description,
                    date_range=DateRange.from_model(node.date_range),
                    hierarchy_rank=node.node_type.value,
                )
                for node in nodes
            ]
        except Exception as e:
            # Log error but don't expose details to client
            logger.error(f"Error in search_nodes_by_text: {e}")
            return []
