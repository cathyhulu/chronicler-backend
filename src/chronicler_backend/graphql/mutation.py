"""GraphQL mutation types for the Chronicler backend."""

import uuid
from datetime import datetime
from typing import List, Optional

import strawberry

from chronicler_backend.db.node import NodeDatabase
from chronicler_backend.graphql.query import DateRange, Node, NodeType
from chronicler_backend.models.node import DateRange as ModelDateRange
from chronicler_backend.models.node import Node as ModelNode
from chronicler_backend.models.node import NodeType as ModelNodeType
from chronicler_backend.utils.constants import VECTOR_DIMENSION
from chronicler_backend.utils.logging import get_logger

logger = get_logger(__name__)


@strawberry.input
class DateRangeInput:
    """Input type for date range creation/updates."""

    start: Optional[datetime] = None
    end: Optional[datetime] = None


@strawberry.input
class NodeInput:
    """Input type for node creation/updates."""

    name: str
    node_type: NodeType
    description: Optional[str] = None
    date_range: Optional[DateRangeInput] = None
    vector_embedding: Optional[List[float]] = None


@strawberry.type
class Mutation:
    """Root mutation type for GraphQL API."""

    @strawberry.mutation
    def create_node(self, info, input: NodeInput) -> Node:
        """Create a new node.

        Args:
            info: GraphQL resolver info with context
            input: Node creation input data

        Returns:
            Node: Created node
        """
        db = info.context["db"]
        node_db = NodeDatabase(db)

        # Validate vector dimensions if provided
        if input.vector_embedding and len(input.vector_embedding) != VECTOR_DIMENSION:
            raise ValueError(
                f"Vector embedding must have exactly {VECTOR_DIMENSION} dimensions,"
                f" got {len(input.vector_embedding)}"
            )

        # Convert date_range from input if provided
        date_range = None
        if input.date_range:
            date_range = ModelDateRange(start=input.date_range.start, end=input.date_range.end)

        # Convert GraphQL enum to model enum
        node_type = ModelNodeType[input.node_type.name]

        # Create a model node
        model_node = ModelNode(
            uuid=str(uuid.uuid4()),
            name=input.name,
            node_type=node_type,
            description=input.description,
            date_range=date_range,
            vector_embedding=input.vector_embedding,
        )

        # Persist to database
        created_node = node_db.create_node(model_node)
        if not created_node:
            raise ValueError("Failed to create node")

        # Convert back to GraphQL type for response
        return Node(
            uuid=created_node.uuid,
            name=created_node.name,
            node_type=NodeType[created_node.node_type.name],
            description=created_node.description,
            date_range=(
                DateRange(start=created_node.date_range.start, end=created_node.date_range.end)
                if created_node.date_range
                else None
            ),
            hierarchy_rank=created_node.node_type.value,
        )

    @strawberry.mutation
    def update_node(self, info, uuid: str, input: NodeInput) -> Optional[Node]:
        """Update an existing node.

        Args:
            info: GraphQL resolver info with context
            uuid: UUID of the node to update
            input: Node update input data

        Returns:
            Optional[Node]: Updated node or None if not found
        """
        db = info.context["db"]
        node_db = NodeDatabase(db)

        # First, get the existing node
        existing_node = node_db.get_node(uuid)
        if not existing_node:
            return None

        # Convert date_range from input if provided
        date_range = None
        if input.date_range:
            date_range = ModelDateRange(start=input.date_range.start, end=input.date_range.end)

        # Convert GraphQL enum to model enum
        node_type = ModelNodeType[input.node_type.name]

        # Update the node model with new values
        updated_model = ModelNode(
            uuid=uuid,
            name=input.name,
            node_type=node_type,
            description=input.description,
            date_range=date_range,
            vector_embedding=input.vector_embedding or existing_node.vector_embedding,
        )

        # Persist the update
        updated_node = node_db.update_node(updated_model)
        if not updated_node:
            return None

        # Convert back to GraphQL type for response
        return Node(
            uuid=updated_node.uuid,
            name=updated_node.name,
            node_type=NodeType[updated_node.node_type.name],
            description=updated_node.description,
            date_range=(
                DateRange(start=updated_node.date_range.start, end=updated_node.date_range.end)
                if updated_node.date_range
                else None
            ),
            hierarchy_rank=updated_node.node_type.value,
        )

    @strawberry.mutation
    def delete_node(self, info, uuid: str) -> bool:
        """Delete a node by UUID.

        Args:
            info: GraphQL resolver info with context
            uuid: UUID of the node to delete

        Returns:
            bool: True if node was deleted, False otherwise
        """
        db = info.context["db"]
        node_db = NodeDatabase(db)

        return node_db.delete_node(uuid)

    @strawberry.mutation
    def create_relationship(
        self, info, from_uuid: str, to_uuid: str, relationship_type: str
    ) -> bool:
        """Create a relationship between two nodes.

        Args:
            info: GraphQL resolver info with context
            from_uuid: UUID of the source node
            to_uuid: UUID of the target node
            relationship_type: Type of relationship

        Returns:
            bool: True if relationship was created, False otherwise
        """
        db = info.context["db"]

        # Uppercase the relationship type for Neo4j convention
        rel_type = relationship_type.upper().replace(" ", "_")

        # Create the relationship
        query = f"""
        MATCH (a:Node {{uuid: $from_uuid}})
        MATCH (b:Node {{uuid: $to_uuid}})
        CREATE (a)-[r:`{rel_type}`]->(b)
        RETURN count(r) as created
        """

        try:
            result = db.run_query(
                query, {"from_uuid": from_uuid, "to_uuid": to_uuid}, return_single=True
            )

            return result and result.get("created", 0) > 0
        except Exception as e:
            logger.error(f"Failed to create relationship: {e}")
            return False
