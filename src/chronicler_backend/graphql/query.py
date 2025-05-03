"""GraphQL query types for the Chronicler backend."""

import enum
from datetime import datetime
from typing import Annotated, List, Optional

import strawberry
from strawberry.types import Info

from chronicler_backend.db.node import NodeDatabase
from chronicler_backend.embeddings.api import get_model_manager
from chronicler_backend.models.node import DateRange as ModelDateRange
from chronicler_backend.models.node import NodeType as ModelNodeType
from chronicler_backend.models.node import RelationshipType as ModelRelationshipType
from chronicler_backend.utils.constants import TRUNCATE_DESCRIPTION_LENGTH
from chronicler_backend.utils.logging import get_logger

logger = get_logger(__name__)

# Auto-generate NodeType enum for GraphQL from the model definition
# Create the enum dynamically based on the model's NodeType
NodeTypeDict = {node_type.name: node_type.name for node_type in ModelNodeType}
NodeType = strawberry.enum(
    enum.Enum("NodeType", NodeTypeDict), description="Types of nodes in the knowledge graph"
)

# Auto-generate RelationshipType enum for GraphQL from the model definition
RelationshipTypeDict = {rel_type.name: rel_type.value for rel_type in ModelRelationshipType}
RelationshipType = strawberry.enum(
    enum.Enum("RelationshipType", RelationshipTypeDict),
    description="Types of relationships between nodes in the knowledge graph",
)


# Define rank filter enum options
@strawberry.enum(description="Options for filtering nodes by their hierarchical rank")
class RankFilterType(enum.Enum):
    """Enum for rank filter options when querying node neighbors."""

    HIGHER = "higher"
    LOWER = "lower"
    HIGHER_EQUAL = "higher_equal"
    LOWER_EQUAL = "lower_equal"


# Auto-generate DateRange type for GraphQL from the model definition
@strawberry.type(description="Date range with optional start and end dates")
class DateRange:
    """Date range type for GraphQL, auto-generated from model definition."""

    # Match the fields from ModelDateRange
    start: Optional[datetime] = strawberry.field(
        default=None, description="Start date of the range (optional)"
    )
    end: Optional[datetime] = strawberry.field(
        default=None, description="End date of the range (optional)"
    )

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


@strawberry.type(description="Node in the knowledge graph representing an entity or event")
class Node:
    """Node type for GraphQL API."""

    uuid: str = strawberry.field(description="Unique identifier for the node")
    name: str = strawberry.field(description="Name of the node")
    node_type: NodeType = strawberry.field(description="Type of the node (e.g., PERSON, EVENT)")
    description: Optional[str] = strawberry.field(
        default=None, description="Detailed description of the node"
    )
    date_range: Optional[DateRange] = strawberry.field(
        default=None, description="Time period associated with this node"
    )
    hierarchy_rank: int = strawberry.field(
        description="Hierarchical rank in the knowledge grap (higher is more important)"
    )


@strawberry.type(description="Relationship between nodes in the knowledge graph")
class NodeRelationship:
    """NodeRelationship type for GraphQL API."""

    sourceNodeUUID: str = strawberry.field(description="UUID of the source node")
    targetNodeUUID: str = strawberry.field(description="UUID of the target node")
    relationshipType: str = strawberry.field(description="Type of the relationship")


@strawberry.type(description="Root query operations for the Chronicler API")
class Query:
    """Root query type for GraphQL API."""

    @strawberry.field(
        description=(
            "Get the maximum description length (in characters)"
            " before truncation for vector embeddings"
        )
    )
    def max_description_length(self, info: Info) -> int:
        """Get the maximum description length before truncation for vector embeddings.

        Args:
            info: GraphQL resolver info with context

        Returns:
            int: Maximum number of characters before truncation
        """
        return TRUNCATE_DESCRIPTION_LENGTH

    @strawberry.field(description="Retrieve a single node by its unique identifier")
    def node(
        self,
        info: Info,
        uuid: Annotated[
            str, strawberry.argument(description="Unique identifier of the node to retrieve")
        ],
    ) -> Optional[Node]:
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

    @strawberry.field(description="Retrieve a list of all nodes with pagination support")
    def nodes(
        self,
        info: Info,
        limit: Annotated[
            int, strawberry.argument(description="Maximum number of nodes to return")
        ] = 10,
        offset: Annotated[
            int, strawberry.argument(description="Number of nodes to skip for pagination")
        ] = 0,
    ) -> List[Node]:
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

    @strawberry.field(description="Retrieve a list of neighbor nodes for a given node")
    def node_neighbors(
        self,
        info: Info,
        uuid: Annotated[
            str,
            strawberry.argument(description="Unique identifier of the node to find neighbors for"),
        ],
        same_type_only: Annotated[
            bool, strawberry.argument(description="Filter to only return nodes of the same type")
        ] = True,
        rank_filter: Annotated[
            Optional[RankFilterType],
            strawberry.argument(
                description="Filter by node type rank relative to the current node"
            ),
        ] = None,
        limit: Annotated[
            int, strawberry.argument(description="Maximum number of nodes to return")
        ] = 10,
        offset: Annotated[
            int, strawberry.argument(description="Number of nodes to skip for pagination")
        ] = 0,
    ) -> List[Node]:
        """Query to get neighbors of a node.

        Args:
            info: GraphQL resolver info with context
            uuid: Node UUID
            same_type_only: Only return nodes of the same type
            rank_filter: Filter by node type rank relative to the current node
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List[Node]: List of neighbor nodes
        """
        db = info.context["db"]
        node_db = NodeDatabase(db)

        # Convert the enum value to string if rank_filter is provided
        rank_filter_value = rank_filter.value if rank_filter else None

        neighbors = node_db.get_node_neighbors(
            uuid,
            same_type_only=same_type_only,
            rank_filter=rank_filter_value,
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
            for node in neighbors
        ]

    @strawberry.field(description="Retrieve a list of nodes within a specified date range")
    def nodes_by_date_range(
        self,
        info: Info,
        start_date: Annotated[
            Optional[datetime], strawberry.argument(description="Start date for date range search")
        ] = None,
        end_date: Annotated[
            Optional[datetime], strawberry.argument(description="End date for date range search")
        ] = None,
        node_type: Annotated[
            Optional[NodeType], strawberry.argument(description="Filter results by node type")
        ] = None,
        limit: Annotated[
            int, strawberry.argument(description="Maximum number of nodes to return")
        ] = 10,
        offset: Annotated[
            int, strawberry.argument(description="Number of nodes to skip for pagination")
        ] = 0,
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

    @strawberry.field(description="Search nodes by vector similarity")
    def search_nodes_by_vector(
        self,
        info: Info,
        vector: Annotated[
            List[float], strawberry.argument(description="Query vector for similarity search")
        ],
        limit: Annotated[
            int, strawberry.argument(description="Maximum number of nodes to return")
        ] = 10,
        offset: Annotated[
            int, strawberry.argument(description="Number of nodes to skip for pagination")
        ] = 0,
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

    @strawberry.field(description="Search nodes by semantic similarity to the given text")
    async def search_nodes_by_text(
        self,
        info: Info,
        search_text: Annotated[
            str, strawberry.argument(description="Text to search for semantic similarity")
        ],
        limit: Annotated[
            int, strawberry.argument(description="Maximum number of nodes to return")
        ] = 10,
        offset: Annotated[
            int, strawberry.argument(description="Number of nodes to skip for pagination")
        ] = 0,
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
            # Get model manager from FastAPI dependency
            model_manager = await get_model_manager()

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

    @strawberry.field(description="Retrieve relationships for a specific node")
    def node_relationships(
        self,
        info: Info,
        uuid: Annotated[
            str, strawberry.argument(description="UUID of the node to get relationships for")
        ],
        limit: Annotated[
            int, strawberry.argument(description="Maximum number of relationships to return")
        ] = 10,
        offset: Annotated[
            int, strawberry.argument(description="Number of relationships to skip for pagination")
        ] = 0,
    ) -> List[NodeRelationship]:
        """Query to get all relationships for a node.

        Args:
            info: GraphQL resolver info with context
            uuid: Node UUID
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List[NodeRelationship]: List of relationships for the node
        """
        db = info.context["db"]
        node_db = NodeDatabase(db)

        relationships = node_db.get_relationships(uuid, limit=limit, offset=offset)

        # Convert from database result to GraphQL type
        return [
            NodeRelationship(
                sourceNodeUUID=uuid if rel["direction"] == "OUTGOING" else rel["other_node_uuid"],
                targetNodeUUID=rel["other_node_uuid"] if rel["direction"] == "OUTGOING" else uuid,
                relationshipType=rel["relationship_type"],
            )
            for rel in relationships
        ]
