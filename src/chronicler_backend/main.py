import strawberry
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter

from chronicler_backend.query import MyQuery

schema = strawberry.Schema(query=MyQuery)
graphql_app = GraphQLRouter(schema)

app = FastAPI()
app.include_router(graphql_app, prefix="/graphql")
