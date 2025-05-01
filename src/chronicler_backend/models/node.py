"""Node model definitions for Chronicler backend."""

import uuid
from datetime import datetime
from enum import Enum, IntEnum
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator

from chronicler_backend.utils.constants import (
    TRUNCATE_DESCRIPTION_LENGTH,
    VECTOR_DIMENSION,
)
from chronicler_backend.utils.logging import get_logger

logger = get_logger(__name__)


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
    """Node model for graph entities representing historical elements."""

    uuid: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for the historical entity",
    )
    name: str = Field(
        ...,
        description=(
            "Historical name or title of the entity (e.g., 'Battle of Waterloo', 'Roman Empire')"
        ),
    )
    node_type: NodeType = Field(
        ...,
        description=(
            "Classification of the historical entity "
            "(e.g., EVENT, WAR, COUNTRY, ERA) with hierarchical importance"
        ),
    )
    description: Optional[str] = Field(
        None, description="Historical description and significance of the entity"
    )
    date_range: Optional[DateRange] = Field(
        None, description="Temporal period during which the historical entity existed or occurred"
    )
    vector_embedding: Optional[List[float]] = Field(
        None,
        description=(
            "Vector representation for semantic search and similarity "
            "between historical entities"
        ),
    )
    properties: Optional[Dict] = Field(
        default_factory=dict,
        description=(
            "Flexible key-value pairs for storing node-type specific attributes"
            " that don't fit into standard fields"
        ),
    )

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

    @field_validator("description")
    def validate_description_length(cls, value: Optional[str]) -> Optional[str]:
        """Log a warning if description exceeds 200 words.

        Args:
            value: Description text

        Returns:
            str: Original description
        """
        if value is not None:
            words = value.split()
            if len(words) > TRUNCATE_DESCRIPTION_LENGTH:
                logger.warning(
                    f"Description exceeds {TRUNCATE_DESCRIPTION_LENGTH} words"
                    f" (has {len(words)} words). Will be truncated before"
                    " conversion to vector embedding."
                )
        return value
