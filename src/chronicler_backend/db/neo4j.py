"""Neo4j database module for the Chronicler backend."""

import os
from typing import Any, Dict, List, Optional

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
            Result object or dict: Neo4j result or single record as dict
        """
        with self.get_session() as session:
            result = session.run(query, params or {})
            if return_single:
                record = result.single()
                if record:
                    return dict(record)
                return None
            return result

    def get_all_nodes(self, label: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all nodes with an optional label.

        Args:
            label: Node label filter

        Returns:
            List[Dict[str, Any]]: List of nodes
        """
        query = f"MATCH (n{':' + label if label else ''}) RETURN n"
        with self.get_session() as session:
            records = session.run(query)
            return [dict(record)["n"] for record in records]


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
