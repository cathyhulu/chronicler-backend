"""Neo4j database module for the Chronicler backend."""

import os
from typing import Any, Dict, List, Optional

from fastapi import Depends
from neo4j import GraphDatabase, Driver, Session, Result


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

    def run_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> Result:
        """Run a Cypher query.

        Args:
            query: Cypher query
            parameters: Query parameters

        Returns:
            Result: Query result
        """
        with self.get_session() as session:
            return session.run(query, parameters or {})

    def get_all_nodes(self, label: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all nodes with an optional label.

        Args:
            label: Node label filter

        Returns:
            List[Dict[str, Any]]: List of nodes
        """
        query = f"MATCH (n{':' + label if label else ''}) RETURN n"
        records = self.run_query(query)
        return [record["n"] for record in records]


# Create a database instance
def get_neo4j_db() -> Neo4jDatabase:
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
