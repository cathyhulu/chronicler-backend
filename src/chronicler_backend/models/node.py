"""Node model definitions for Chronicler backend."""

import uuid
from datetime import datetime
from enum import Enum, IntEnum
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator

from chronicler_backend.utils.constants import VECTOR_DIMENSION


class NodeType(IntEnum):
    """Node type enum with hierarchical ranking.

    Higher integer values represent higher hierarchical importance.
    """

    EVENT = 10
    BATTLE = 20
    WAR = 30
    PERIOD = 40
    CITY = 50
    REGION = 60
    COUNTRY = 70
    CONTINENT = 80
    CIVILIZATION = 90
    ERA = 100

    @classmethod
    def get_hierarchy_value(cls, node_type: Union[str, "NodeType"]) -> int:
        """Get the hierarchical value for a node type.

        Args:
            node_type: Node type as string or enum value

        Returns:
            int: Hierarchy value
        """
        if isinstance(node_type, str):
            return cls[node_type.upper()].value
        return node_type.value


class RelationshipType(str, Enum):
    """Defines allowed relationship types between nodes in the graph.

    These relationships represent historical and geographical connections
    between entities in the knowledge graph.
    """

    # Temporal relationships
    PRECEDES = "PRECEDES"  # Event A precedes Event B in time
    FOLLOWS = "FOLLOWS"  # Event A follows Event B in time
    DURING = "DURING"  # Event A occurred during Event B

    # Geographical relationships
    LOCATED_IN = "LOCATED_IN"  # Place A is located in Place B
    BORDERS = "BORDERS"  # Place A borders Place B
    CAPITAL_OF = "CAPITAL_OF"  # City is capital of Country

    # Causal relationships
    CAUSED = "CAUSED"  # Event A caused Event B
    INFLUENCED = "INFLUENCED"  # Entity A influenced Entity B
    PARTICIPATED_IN = "PARTICIPATED_IN"  # Entity A participated in Event B

    # Hierarchical relationships
    PART_OF = "PART_OF"  # Entity A is part of Entity B
    CONTAINS = "CONTAINS"  # Entity A contains Entity B


class DateRange(BaseModel):
    """Date range model for node temporal context."""

    start: Optional[datetime] = None
    end: Optional[datetime] = None


class Node(BaseModel):
    """Node model for graph entities."""

    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    node_type: NodeType
    description: Optional[str] = None
    date_range: Optional[DateRange] = None
    vector_embedding: Optional[List[float]] = None
    properties: Optional[Dict] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=False)

    @field_validator("vector_embedding")
    def validate_vector_embedding(cls, value: Optional[List[float]]) -> Optional[List[float]]:
        """Validate the vector embedding dimension.

        Args:
            value: Vector embedding list

        Returns:
            List[float]: Validated vector embedding
        """
        if value is not None and len(value) != VECTOR_DIMENSION:
            raise ValueError(f"Vector embedding must be of dimension {VECTOR_DIMENSION}.")
        return value
