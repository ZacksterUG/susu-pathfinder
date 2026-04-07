from fastapi import APIRouter, HTTPException

from app import repositories
from app.models import Floor

router = APIRouter(tags=["floors"])


@router.get("/buildings/{building_id}/floors", response_model=list[Floor])
async def list_floors(building_id: str):
    building = await repositories.get_building(building_id)
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")
    return await repositories.get_floors_by_building(building_id)
