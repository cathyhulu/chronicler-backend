"""GraphQL mutation types for the Chronicler backend."""

import uuid
from datetime import datetime
from typing import Annotated, List, Optional

import strawberry
from strawberry.types import Info

from chronicler_backend.db.node import NodeDatabase
from chronicler_backend.graphql.query import DateRange, Node, NodeType, RelationshipType
from chronicler_backend.models.node import DateRange as ModelDateRange
from chronicler_backend.models.node import Node as ModelNode
from chronicler_backend.models.node import NodeType as ModelNodeType
from chronicler_backend.models.node import RelationshipType as ModelRelationshipType
from chronicler_backend.utils.constants import VECTOR_DIMENSION
from chronicler_backend.utils.logging import get_logger

logger = get_logger(__name__)


@strawberry.input(description="Input type for date range creation and updates")
class DateRangeInput:
    """Input type for date range creation/updates."""

    start: Optional[datetime] = strawberry.field(
        default=None, description="Start date of the range (optional)"
    )
    end: Optional[datetime] = strawberry.field(
        default=None, description="End date of the range (optional)"
    )


@strawberry.input(description="Input type for node creation and updates")
class NodeInput:
    """Input type for node creation/updates."""

    name: str = strawberry.field(description="Name of the node")
    node_type: NodeType = strawberry.field(description="Type of the node (e.g., PERSON, EVENT)")
    description: Optional[str] = strawberry.field(
        default=None, description="Detailed description of the node"
    )
    date_range: Optional[DateRangeInput] = strawberry.field(
        default=None, description="Time period associated with this node"
    )
    vector_embedding: Optional[List[float]] = strawberry.field(
        default=None,
        description=f"Vector embedding for semantic search (must be {VECTOR_DIMENSION} dimensions)",
    )


@strawberry.type(description="Root mutation operations for the Chronicler API")
class Mutation:
    """Root mutation type for GraphQL API."""

    @strawberry.mutation(description="Create a new node in the knowledge graph")
    async def create_node(
        self,
        info: Info,
        input: Annotated[
            NodeInput, strawberry.argument(description="Input data for creating a new node")
        ],
    ) -> Node:
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
        created_node = await node_db.create_node(model_node)
        if not created_node:
            raise ValueError("Failed to create node")

        # Convert back to GraphQL type for response
        return Node(
            uuid=created_node.uuid,
            name=created_node.name,
            node_type=NodeType[created_node.node_type.name],
            description=created_node.description,
            date_range=DateRange.from_model(created_node.date_range),
            hierarchy_rank=created_node.node_type.value,
        )

    @strawberry.mutation(description="Update an existing node in the knowledge graph")
    async def update_node(
        self,
        info: Info,
        uuid: Annotated[
            str, strawberry.argument(description="Unique identifier of the node to update")
        ],
        input: Annotated[NodeInput, strawberry.argument(description="Updated data for the node")],
    ) -> Optional[Node]:
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

        if input.vector_embedding is not None:
            vector_embedding = input.vector_embedding
        else:
            vector_embedding = existing_node.vector_embedding

        # Update the node model with new values
        updated_model = ModelNode(
            uuid=uuid,
            name=input.name,
            node_type=node_type,
            description=input.description,
            date_range=date_range,
            vector_embedding=vector_embedding,
        )

        # Persist the update, regenerating the vector embedding if necessary
        updated_node = await node_db.update_node(updated_model)
        if not updated_node:
            return None

        # Convert back to GraphQL type for response
        return Node(
            uuid=updated_node.uuid,
            name=updated_node.name,
            node_type=NodeType[updated_node.node_type.name],
            description=updated_node.description,
            date_range=DateRange.from_model(updated_node.date_range),
            hierarchy_rank=updated_node.node_type.value,
        )

    @strawberry.mutation(description="Delete a node from the knowledge graph by UUID")
    def delete_node(
        self,
        info: Info,
        uuid: Annotated[
            str, strawberry.argument(description="Unique identifier of the node to delete")
        ],
    ) -> bool:
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

    @strawberry.mutation(
        description="Create a relationship between two nodes in the knowledge graph"
    )
    def create_relationship(
        self,
        info: Info,
        from_uuid: Annotated[
            str, strawberry.argument(description="Unique identifier of the source node")
        ],
        to_uuid: Annotated[
            str, strawberry.argument(description="Unique identifier of the target node")
        ],
        relationship_type: Annotated[
            RelationshipType,
            strawberry.argument(description="Type of relationship between the nodes"),
        ],
    ) -> bool:
        """Create a relationship between two nodes.

        Args:
            info: GraphQL resolver info with context
            from_uuid: UUID of the source node
            to_uuid: UUID of the target node
            relationship_type: Type of relationship from RelationshipType enum

        Returns:
            bool: True if relationship was created, False otherwise
        """
        db = info.context["db"]
        node_db = NodeDatabase(db)

        try:
            # Convert the GraphQL enum to the model enum by
            # constructing the model enum from the value
            model_relationship_type = ModelRelationshipType(relationship_type.value)

            # Use the NodeDatabase method with the converted model enum
            return node_db.create_relationship(from_uuid, to_uuid, model_relationship_type)
        except Exception as e:
            logger.error(f"Failed to create relationship: {e}")
            return False
