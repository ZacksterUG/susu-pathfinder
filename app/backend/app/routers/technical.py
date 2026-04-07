from fastapi import APIRouter, HTTPException

from app import repositories
from app.models import Technical

router = APIRouter(tags=["technical"])


@router.get(
    "/buildings/{building_id}/floors/{floor_number}/technical",
    response_model=list[Technical],
)
async def list_technical(building_id: str, floor_number: str):
    building = await repositories.get_building(building_id)
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")
    return await repositories.get_technical_by_floor(building_id, floor_number)
