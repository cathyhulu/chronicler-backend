import strawberry
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter

from chronicler_backend.query import MyQuery

schema = strawberry.Schema(query=MyQuery)
graphql_app = GraphQLRouter(schema)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allow only frontend URL
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Specify allowed methods
    allow_headers=["Content-Type", "Authorization"],  # Specify allowed headers
)

app.include_router(graphql_app, prefix="/graphql")
