"""
These fixtures are shared among all tests.
"""

import pytest
import strawberry

from chronicler_backend.query import MyQuery


@pytest.fixture(scope="session")
def schema_fixture() -> strawberry.Schema:
    return strawberry.Schema(query=MyQuery)
