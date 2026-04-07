from fastapi import APIRouter, HTTPException

from app import repositories
from app.models import PathResponse, PathSegment
from app.schemas import PathRequest
from app.pathfinder import MultiFloorPathFinder

router = APIRouter(tags=["path"])


@router.post("/path", response_model=PathResponse)
async def find_path(req: PathRequest):
    # Проверяем, что обе комнаты существуют
    start_room = await repositories.get_room_by_id(req.start_object_id)
    if not start_room:
        raise HTTPException(status_code=404, detail="Start room not found")

    end_room = await repositories.get_room_by_id(req.end_object_id)
    if not end_room:
        raise HTTPException(status_code=404, detail="End room not found")

    # Проверяем, что комнаты в одном корпусе
    if start_room["building_id"] != end_room["building_id"]:
        return PathResponse(
            found=False,
            error="Objects are in different buildings",
        )

    building_id = start_room["building_id"]

    # Проверяем, что у комнат есть координаты
    start_coords = start_room.get("coordinates", {}).get("points", [])
    end_coords = end_room.get("coordinates", {}).get("points", [])
    if not start_coords or not end_coords:
        return PathResponse(
            found=False,
            error="Start or end room has no coordinates. Cannot determine position.",
        )

    # Проверяем кэш
    cached = await repositories.get_cached_path(
        building_id, req.start_object_id, req.end_object_id,
    )
    if cached:
        segments = []
        for seg_data in cached["path_nodes"]:
            segments.append(PathSegment(
                floor_number=seg_data["floor_number"],
                nodes=seg_data["nodes"],
            ))
        return PathResponse(
            found=True,
            path=segments,
            total_length=cached["path_length"],
        )

    # Загружаем все технические помещения для вертикальных связей
    floors = await repositories.get_floors_by_building(building_id)

    # Проверяем, что для этажей начальной и конечной комнат есть grid
    start_floor = start_room["floor_number"]
    end_floor = end_room["floor_number"]

    for floor in floors:
        fn = floor["floor_number"]
        if fn in (start_floor, end_floor):
            grid = await repositories.get_grid_by_floor(building_id, fn)
            if not grid:
                return PathResponse(
                    found=False,
                    error=f"Grid not available for floor {fn}. Floor is not fully mapped yet.",
                )

    all_technical = []
    for floor in floors:
        tech = await repositories.get_technical_by_floor(building_id, floor["floor_number"])
        all_technical.extend(tech)

    # Ищем путь
    finder = MultiFloorPathFinder()
    result = await finder.find_path(building_id, start_room, end_room, all_technical)

    if result["found"]:
        # Сохраняем в кэш
        await repositories.save_cached_path(
            building_id,
            req.start_object_id,
            req.end_object_id,
            result["path"],
            result["total_length"],
        )
        segments = [PathSegment(**seg) for seg in result["path"]]
        return PathResponse(
            found=True,
            path=segments,
            total_length=result["total_length"],
            floor_transitions=result.get("floor_transitions", []),
        )

    return PathResponse(found=False, error=result.get("error", "No path found"))
