from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import close_pool
from app.routers import buildings, floors, rooms, technical, entrances, path


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    yield
    # shutdown
    await close_pool()


app = FastAPI(
    title="Map App API",
    description="API для навигации по зданиям с построением маршрутов",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(buildings.router)
app.include_router(floors.router)
app.include_router(rooms.router)
app.include_router(technical.router)
app.include_router(entrances.router)
app.include_router(path.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
