"""GraphQL query types for the Chronicler backend."""

from typing import List, Optional

import strawberry


@strawberry.type
class Character:
    """A character entity in the Chronicler system."""

    id: str
    name: str
    description: Optional[str] = None


@strawberry.type
class Query:
    """Root query type for GraphQL API."""

    @strawberry.field
    def hello(self) -> str:
        """Simple hello world query to test GraphQL setup."""
        return "Hello, Chronicler!"

    @strawberry.field
    def characters(self, info) -> List[Character]:
        """Query to get all characters.

        Args:
            info: GraphQL resolver info with context

        Returns:
            List[Character]: List of characters
        """
        db = info.context["db"]
        result = db.run_query(
            "MATCH (c:Character) RETURN c.id as id, c.name as name, c.description as description"
        )

        characters = []
        for record in result:
            characters.append(
                Character(id=record["id"], name=record["name"], description=record["description"])
            )
        return characters

    @strawberry.field
    def character(self, info, id: str) -> Optional[Character]:
        """Query to get a character by ID.

        Args:
            info: GraphQL resolver info with context
            id: Character ID

        Returns:
            Optional[Character]: Character if found, None otherwise
        """
        db = info.context["db"]
        result = db.run_query(
            "MATCH (c:Character {id: $id}) "
            "RETURN c.id as id, c.name as name, c.description as description",
            {"id": id},
            return_single=True,
        )

        if result:
            return Character(
                id=result["id"], name=result["name"], description=result["description"]
            )
        return None
