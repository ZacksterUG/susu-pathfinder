"""Pydantic-модели для API-запросов."""

from pydantic import BaseModel


class PathRequest(BaseModel):
    building_id: str
    start_object_id: str
    end_object_id: str
