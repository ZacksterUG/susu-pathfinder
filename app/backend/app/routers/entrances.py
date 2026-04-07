from fastapi import APIRouter, HTTPException

from app import repositories
from app.models import Entrance

router = APIRouter(tags=["entrances"])


@router.get(
    "/buildings/{building_id}/floors/{floor_number}/entrances",
    response_model=list[Entrance],
)
async def list_entrances(building_id: str, floor_number: str):
    building = await repositories.get_building(building_id)
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")
    return await repositories.get_entrances_by_floor(building_id, floor_number)
