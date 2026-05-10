from fastapi import APIRouter, HTTPException

from app import repositories
from app.models import PathResponse, PathSegment
from app.schemas import PathRequest
from app.pathfinder import MultiFloorPathFinder

router = APIRouter(tags=["path"])


@router.get("/building_entrances")
async def get_building_entrances(building_id: str):
    """Получить входы/выходы в корпус (object_type='building_entrance')"""
    entrances = await repositories.get_building_entrances(building_id)
    return entrances


@router.post("/path", response_model=PathResponse)
async def find_path(req: PathRequest):
    # Проверяем, что обе комнаты существуют
    start_room = await repositories.get_room_by_id(req.start_object_id)
    if not start_room:
        raise HTTPException(status_code=404, detail="Start room not found")

    end_room = await repositories.get_room_by_id(req.end_object_id)
    if not end_room:
        raise HTTPException(status_code=404, detail="End room not found")

    # Если разные корпуса — строим межкорпусный маршрут
    if start_room["building_id"] != end_room["building_id"]:
        # Получаем входы/выходы в корпуса
        start_entrances = await repositories.get_building_entrances(start_room["building_id"])
        end_entrances = await repositories.get_building_entrances(end_room["building_id"])

        if not start_entrances or not end_entrances:
            return PathResponse(
                found=False,
                error="Для одного из корпусов не найдены входы/выходы",
            )

        # Берём первый вход/выход для каждого корпуса (TODO: выбирать ближайший)
        start_entrance = start_entrances[0]
        end_entrance = end_entrances[0]

        # --- Путь 1: от комнаты А до выхода корпуса А ---
        building_id_a = start_room["building_id"]
        floors_a = await repositories.get_floors_by_building(building_id_a)
        all_tech_a = []
        for floor in floors_a:
            tech = await repositories.get_technical_by_floor(building_id_a, floor["floor_number"])
            all_tech_a.extend(tech)

        finder1 = MultiFloorPathFinder()
        result1 = await finder1.find_path_to_point(
            building_id_a,
            start_room,
            start_entrance["x"], start_entrance["y"], start_entrance["floor_number"],
            all_tech_a
        )

        # --- Путь 2: от входа корпуса Б до комнаты Б ---
        building_id_b = end_room["building_id"]
        floors_b = await repositories.get_floors_by_building(building_id_b)
        all_tech_b = []
        for floor in floors_b:
            tech = await repositories.get_technical_by_floor(building_id_b, floor["floor_number"])
            all_tech_b.extend(tech)

        finder2 = MultiFloorPathFinder()
        result2 = await finder2.find_path_from_point(
            building_id_b,
            end_entrance["x"], end_entrance["y"], end_entrance["floor_number"],
            end_room,
            all_tech_b
        )

        # Объединяем результаты
        def to_segments(result):
            if not result.get("found"):
                return []
            return [PathSegment(**seg) for seg in result.get("path", [])]

        seg1 = to_segments(result1)
        seg2 = to_segments(result2)
        total_length = (result1.get("total_length", 0) + result2.get("total_length", 0))

        return PathResponse(
            found=True,
            inter_building=True,
            path_part1=seg1,
            path_part2=seg2,
            total_length=total_length,
        )

    # --- Обычный путь внутри одного корпуса ---
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

    # Проверяем, что для этажей начальной и конечной комнаты есть grid
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
