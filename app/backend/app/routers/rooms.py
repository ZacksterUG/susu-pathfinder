from fastapi import APIRouter, HTTPException

from app import repositories
from app.models import Room

router = APIRouter(tags=["rooms"])


@router.get(
    "/buildings/{building_id}/floors/{floor_number}/rooms",
    response_model=list[Room],
)
async def list_rooms(building_id: str, floor_number: str):
    building = await repositories.get_building(building_id)
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")
    return await repositories.get_rooms_by_floor(building_id, floor_number)
