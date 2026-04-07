from fastapi import APIRouter, HTTPException

from app import repositories
from app.models import Building

router = APIRouter(prefix="/buildings", tags=["buildings"])


@router.get("", response_model=list[Building])
async def list_buildings():
    return await repositories.get_all_buildings()


@router.get("/{building_id}", response_model=Building)
async def get_building(building_id: str):
    building = await repositories.get_building(building_id)
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")
    return building
