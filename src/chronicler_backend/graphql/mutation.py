"""GraphQL mutation types for the Chronicler backend."""

import uuid
from typing import Optional

import strawberry

from chronicler_backend.graphql.query import Character


@strawberry.input
class CharacterInput:
    """Input type for character creation/updates."""

    name: str
    description: Optional[str] = None


@strawberry.type
class Mutation:
    """Root mutation type for GraphQL API."""

    @strawberry.mutation
    def create_character(self, info, input: CharacterInput) -> Character:
        """Create a new character.

        Args:
            info: GraphQL resolver info with context
            input: Character creation input data

        Returns:
            Character: Created character
        """
        db = info.context["db"]

        # Generate a UUID for the new character
        character_id = str(uuid.uuid4())

        # Create the character in Neo4j
        result = db.run_query(
            """
            CREATE (c:Character {
                id: $id,
                name: $name,
                description: $description
            })
            RETURN c.id as id, c.name as name, c.description as description
            """,
            {"id": character_id, "name": input.name, "description": input.description},
            return_single=True,
        )

        return Character(id=result["id"], name=result["name"], description=result["description"])

    @strawberry.mutation
    def update_character(self, info, id: str, input: CharacterInput) -> Optional[Character]:
        """Update an existing character.

        Args:
            info: GraphQL resolver info with context
            id: ID of the character to update
            input: Character update input data

        Returns:
            Optional[Character]: Updated character or None if not found
        """
        db = info.context["db"]

        # Update the character in Neo4j
        result = db.run_query(
            """
            MATCH (c:Character {id: $id})
            SET c.name = $name, c.description = $description
            RETURN c.id as id, c.name as name, c.description as description
            """,
            {"id": id, "name": input.name, "description": input.description},
            return_single=True,
        )

        if result:
            return Character(
                id=result["id"], name=result["name"], description=result["description"]
            )
        return None

    @strawberry.mutation
    def delete_character(self, info, id: str) -> bool:
        """Delete a character by ID.

        Args:
            info: GraphQL resolver info with context
            id: ID of the character to delete

        Returns:
            bool: True if character was deleted, False otherwise
        """
        db = info.context["db"]

        # Delete the character from Neo4j
        result = db.run_query(
            "MATCH (c:Character {id: $id}) DELETE c RETURN count(c) as deleted",
            {"id": id},
            return_single=True,
        )

        return result["deleted"] > 0
