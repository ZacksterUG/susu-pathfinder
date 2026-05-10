"""Pydantic-модели для API-запросов."""

from typing import Optional
from pydantic import BaseModel


class PathRequest(BaseModel):
    building_id: str
    start_object_id: Optional[str] = None
    end_object_id: Optional[str] = None
    # Опциональные координаты для начала/конца пути (для входов/выходов корпуса)
    start_coordinates: Optional[dict] = None  # {"x": float, "y": float, "floor_number": str}
    end_coordinates: Optional[dict] = None  # {"x": float, "y": float, "floor_number": str}
