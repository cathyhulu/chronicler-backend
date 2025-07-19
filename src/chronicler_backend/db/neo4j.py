"""Neo4j database module for the Chronicler backend."""

import os
from typing import Generator

from fastapi import Depends
from neo4j import GraphDatabase, Session


class Neo4jDatabase:
    """Neo4j database connection manager."""

    def __init__(self, uri: str, user: str, password: str):
        """Initialize Neo4j database connection.

        Args:
            uri: Neo4j URI
            user: Neo4j username
            password: Neo4j password
        """
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self) -> None:
        """Close the Neo4j driver connection."""
        self.driver.close()

    def get_session(self) -> Session:
        """Get a Neo4j session.

        Returns:
            Session: Neo4j session
        """
        return self.driver.session()

    def run_query(self, query, params=None, return_single=False):
        """Execute a Cypher query and return results.

        Args:
            query (str): Cypher query
            params (dict, optional): Query parameters
            return_single (bool, optional): If True, returns the single record as a dict

        Returns:
            List[Dict] or Dict: List of records or single record as dict
        """
        with self.get_session() as session:
            result = session.run(query, params or {})
            if return_single:
                record = result.single()
                if record:
                    return dict(record)
                return None
            # Collect all records into a list before the session closes
            return [dict(record) for record in result]


# Create a database instance
def get_neo4j_db() -> Generator[Neo4jDatabase, None, None]:
    """Get Neo4j database instance.

    Returns:
        Neo4jDatabase: Database instance
    """
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "chroniclerpass")

    db = Neo4jDatabase(uri=uri, user=user, password=password)
    try:
        yield db
    finally:
        db.close()


# Dependency for FastAPI
def get_db() -> Neo4jDatabase:
    """FastAPI dependency for Neo4j database.

    Returns:
        Neo4jDatabase: Database instance
    """
    return Depends(get_neo4j_db)
