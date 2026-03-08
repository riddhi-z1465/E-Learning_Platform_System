from contextlib import asynccontextmanager
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from schema import schema
from db import init_db, close_driver


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create constraints + counter nodes
    init_db()
    yield
    # Shutdown: close Neo4j driver
    close_driver()


app = FastAPI(
    title="E-Learning Platform – GraphQL API (Neo4j Aura)",
    lifespan=lifespan,
)

graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")


@app.get("/")
def root():
    return {
        "message": "E-Learning Platform API (Neo4j Aura backend)",
        "graphql_playground": "/graphql",
    }