"""GraphQL schema for the Chronicler backend."""

import strawberry
from typing import List, Optional
from datetime import datetime

from chronicler_backend.db.neo4j import Neo4jDatabase


@strawberry.type
class Character:
    """Character node in the Chronicler database."""

    id: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime


@strawberry.type
class Location:
    """Location node in the Chronicler database."""

    id: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime


@strawberry.type
class Event:
    """Event node in the Chronicler database."""

    id: str
    name: str
    description: Optional[str] = None
    date: Optional[str] = None
    created_at: datetime
    updated_at: datetime


@strawberry.input
class CharacterInput:
    """Input for creating a Character."""

    name: str
    description: Optional[str] = None


@strawberry.input
class LocationInput:
    """Input for creating a Location."""

    name: str
    description: Optional[str] = None


@strawberry.input
class EventInput:
    """Input for creating an Event."""

    name: str
    description: Optional[str] = None
    date: Optional[str] = None


@strawberry.type
class Query:
    """GraphQL queries."""

    @strawberry.field
    def character(self, id: str, db: Neo4jDatabase) -> Optional[Character]:
        """Get a character by ID."""
        query = """
        MATCH (c:Character {id: $id})
        RETURN c
        """
        result = db.run_query(query, {"id": id})
        record = result.single()
        if not record:
            return None
        node = record["c"]
        return Character(
            id=node["id"],
            name=node["name"],
            description=node.get("description"),
            created_at=node["created_at"],
            updated_at=node["updated_at"],
        )

    @strawberry.field
    def characters(self, db: Neo4jDatabase) -> List[Character]:
        """Get all characters."""
        query = """
        MATCH (c:Character)
        RETURN c
        ORDER BY c.name
        """
        result = db.run_query(query)
        return [
            Character(
                id=record["c"]["id"],
                name=record["c"]["name"],
                description=record["c"].get("description"),
                created_at=record["c"]["created_at"],
                updated_at=record["c"]["updated_at"],
            )
            for record in result
        ]

    @strawberry.field
    def location(self, id: str, db: Neo4jDatabase) -> Optional[Location]:
        """Get a location by ID."""
        query = """
        MATCH (l:Location {id: $id})
        RETURN l
        """
        result = db.run_query(query, {"id": id})
        record = result.single()
        if not record:
            return None
        node = record["l"]
        return Location(
            id=node["id"],
            name=node["name"],
            description=node.get("description"),
            created_at=node["created_at"],
            updated_at=node["updated_at"],
        )

    @strawberry.field
    def locations(self, db: Neo4jDatabase) -> List[Location]:
        """Get all locations."""
        query = """
        MATCH (l:Location)
        RETURN l
        ORDER BY l.name
        """
        result = db.run_query(query)
        return [
            Location(
                id=record["l"]["id"],
                name=record["l"]["name"],
                description=record["l"].get("description"),
                created_at=record["l"]["created_at"],
                updated_at=record["l"]["updated_at"],
            )
            for record in result
        ]

    @strawberry.field
    def event(self, id: str, db: Neo4jDatabase) -> Optional[Event]:
        """Get an event by ID."""
        query = """
        MATCH (e:Event {id: $id})
        RETURN e
        """
        result = db.run_query(query, {"id": id})
        record = result.single()
        if not record:
            return None
        node = record["e"]
        return Event(
            id=node["id"],
            name=node["name"],
            description=node.get("description"),
            date=node.get("date"),
            created_at=node["created_at"],
            updated_at=node["updated_at"],
        )

    @strawberry.field
    def events(self, db: Neo4jDatabase) -> List[Event]:
        """Get all events."""
        query = """
        MATCH (e:Event)
        RETURN e
        ORDER BY e.date
        """
        result = db.run_query(query)
        return [
            Event(
                id=record["e"]["id"],
                name=record["e"]["name"],
                description=record["e"].get("description"),
                date=record["e"].get("date"),
                created_at=record["e"]["created_at"],
                updated_at=record["e"]["updated_at"],
            )
            for record in result
        ]


@strawberry.type
class Mutation:
    """GraphQL mutations."""

    @strawberry.mutation
    def create_character(self, input: CharacterInput, db: Neo4jDatabase) -> Character:
        """Create a new character."""
        query = """
        CREATE (c:Character {
            id: randomUUID(),
            name: $name,
            description: $description,
            created_at: datetime(),
            updated_at: datetime()
        })
        RETURN c
        """
        result = db.run_query(query, {"name": input.name, "description": input.description})
        node = result.single()["c"]
        return Character(
            id=node["id"],
            name=node["name"],
            description=node.get("description"),
            created_at=node["created_at"],
            updated_at=node["updated_at"],
        )

    @strawberry.mutation
    def create_location(self, input: LocationInput, db: Neo4jDatabase) -> Location:
        """Create a new location."""
        query = """
        CREATE (l:Location {
            id: randomUUID(),
            name: $name,
            description: $description,
            created_at: datetime(),
            updated_at: datetime()
        })
        RETURN l
        """
        result = db.run_query(query, {"name": input.name, "description": input.description})
        node = result.single()["l"]
        return Location(
            id=node["id"],
            name=node["name"],
            description=node.get("description"),
            created_at=node["created_at"],
            updated_at=node["updated_at"],
        )

    @strawberry.mutation
    def create_event(self, input: EventInput, db: Neo4jDatabase) -> Event:
        """Create a new event."""
        query = """
        CREATE (e:Event {
            id: randomUUID(),
            name: $name,
            description: $description,
            date: $date,
            created_at: datetime(),
            updated_at: datetime()
        })
        RETURN e
        """
        result = db.run_query(
            query, {"name": input.name, "description": input.description, "date": input.date}
        )
        node = result.single()["e"]
        return Event(
            id=node["id"],
            name=node["name"],
            description=node.get("description"),
            date=node.get("date"),
            created_at=node["created_at"],
            updated_at=node["updated_at"],
        )


schema = strawberry.Schema(query=Query, mutation=Mutation)
