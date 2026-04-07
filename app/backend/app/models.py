"""Pydantic-модели для API-ответов."""

from typing import Optional
from pydantic import BaseModel


# ─── Building ────────────────────────────────────────────────

class Building(BaseModel):
    id: str
    name: str
    short_name: Optional[str] = None


# ─── Floor ───────────────────────────────────────────────────

class Floor(BaseModel):
    id: str
    building_id: str
    floor_number: str
    corridor_points: Optional[dict] = None


# ─── Room ────────────────────────────────────────────────────

class Room(BaseModel):
    id: str
    building_id: str
    floor_number: str
    number: str
    name: Optional[str] = None
    room_type: Optional[str] = None
    coordinates: Optional[dict] = None


# ─── Technical ───────────────────────────────────────────────

class Technical(BaseModel):
    id: str
    building_id: str
    floor_number: str
    name: Optional[str] = None
    type: str
    coordinates: Optional[dict] = None
    has_entrance: bool
    linked: list[str] = []


# ─── Entrance ────────────────────────────────────────────────

class Entrance(BaseModel):
    object_id: str
    object_type: str
    building_id: str
    floor_number: str
    x: int
    y: int
    room_number: Optional[str] = None


# ─── Grid ────────────────────────────────────────────────────

class Grid(BaseModel):
    building_id: str
    floor_number: str
    cell_size: int
    nodes: list[dict] = []
    edges: list[dict] = []
    entrance_connections: list[dict] = []


# ─── Path ────────────────────────────────────────────────────

class PathSegment(BaseModel):
    floor_number: str
    nodes: list[dict]


class PathResponse(BaseModel):
    found: bool
    path: list[PathSegment] = []
    total_length: float = 0.0
    floor_transitions: list[tuple[str, str]] = []
    error: Optional[str] = None
