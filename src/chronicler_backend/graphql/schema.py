"""GraphQL schema for the Chronicler backend."""

import strawberry

from chronicler_backend.graphql.mutation import Mutation
from chronicler_backend.graphql.query import Query

# Create the schema with query and mutation types
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
)
