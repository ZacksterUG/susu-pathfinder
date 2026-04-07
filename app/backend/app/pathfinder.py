"""A* поиск пути с использованием данных из БД."""

import heapq
import math
from typing import Optional

from app import repositories


def _distance(x1: float, y1: float, x2: float, y2: float) -> float:
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def _nearest_node_index(nodes: list[dict], x: float, y: float) -> int:
    best = 0
    best_dist = float("inf")
    for i, n in enumerate(nodes):
        d = _distance(n["x"], n["y"], x, y)
        if d < best_dist:
            best_dist = d
            best = i
    return best


class MultiFloorPathFinder:
    """
    Межэтажный поиск пути.
    Вертикальные связи строятся из поля linked таблицы technical.
    Координаты старта/финиша — точки входа (entrance), как в entrance_app.
    """

    def __init__(self):
        self.grid_data: dict[str, dict] = {}   # "buildingId_floor" -> grid
        self.entrance_data: dict[str, list[dict]] = {}  # floor_number -> [entrance]
        self.building_id: str = ""

        self.global_to_local: dict[int, tuple[str, int]] = {}
        self.local_to_global: dict[tuple[str, int], int] = {}
        self.global_adj: dict[int, list[tuple[int, float]]] = {}
        self._global_counter = 0

    async def load_all_floors(self, building_id: str):
        """Загрузить grid и entrance для всех этажей здания."""
        self.building_id = building_id
        floors = await repositories.get_floors_by_building(building_id)
        for floor in floors:
            fn = floor["floor_number"]
            grid = await repositories.get_grid_by_floor(building_id, fn)
            if grid:
                key = f"{building_id}_{fn}"
                self.grid_data[key] = grid

            entrances = await repositories.get_entrances_by_floor(building_id, fn)
            if entrances:
                self.entrance_data[fn] = entrances

    def _build_global_graph(self, all_technical: list[dict]):
        """Построить глобальный граф с этажами и вертикальными связями."""
        # 1. Внутриэтажные рёбра
        for floor_key, grid in self.grid_data.items():
            parts = floor_key.rsplit("_", 1)
            if len(parts) != 2:
                continue
            floor_num = parts[1]
            nodes = grid.get("nodes", [])
            edges = grid.get("edges", [])

            floor_node_map: dict[int, int] = {}
            for local_idx in range(len(nodes)):
                gid = self._global_counter
                self._global_counter += 1
                self.global_to_local[gid] = (floor_num, local_idx)
                self.local_to_global[(floor_num, local_idx)] = gid
                floor_node_map[local_idx] = gid
                self.global_adj[gid] = []

            for edge in edges:
                from_gid = floor_node_map.get(edge["from"])
                to_gid = floor_node_map.get(edge["to"])
                if from_gid is not None and to_gid is not None:
                    weight = edge.get("weight", 1.0)
                    self.global_adj[from_gid].append((to_gid, weight))
                    self.global_adj[to_gid].append((from_gid, weight))

        # 2. Межэтажные рёбра через linked
        self._add_vertical_links(all_technical)

    def _add_vertical_links(self, all_technical: list[dict]):
        """Добавить вертикальные рёбра из поля linked таблицы technical."""
        # Индекс: obj_id -> (floor, coords)
        # linked содержит массив UUID связанных объектов
        tech_by_id: dict[str, dict] = {}
        for t in all_technical:
            if t.get("has_entrance") and t.get("linked"):
                tech_by_id[t["id"]] = {
                    "floor": t["floor_number"],
                    "coords": t.get("coordinates", {}).get("points", []),
                    "linked": t["linked"],
                }

        # Для каждого объекта с linked строим ребро ко всем связанным
        processed_pairs: set[tuple[str, str]] = set()
        for obj_id, info in tech_by_id.items():
            for linked_id in info["linked"]:
                pair_key = tuple(sorted([obj_id, linked_id]))
                if pair_key in processed_pairs:
                    continue
                processed_pairs.add(pair_key)

                if linked_id not in tech_by_id:
                    continue

                linked_info = tech_by_id[linked_id]
                fi = info["floor"]
                fj = linked_info["floor"]
                if fi == fj:
                    continue

                key_i = f"{self.building_id}_{fi}"
                key_j = f"{self.building_id}_{fj}"
                grid_i = self.grid_data.get(key_i)
                grid_j = self.grid_data.get(key_j)
                if not grid_i or not grid_j:
                    continue

                nodes_i = grid_i.get("nodes", [])
                nodes_j = grid_j.get("nodes", [])
                if not nodes_i or not nodes_j:
                    continue

                # Центры полигонов
                ci = info["coords"]
                cj = linked_info["coords"]
                if not ci or not cj:
                    continue

                cx_i = sum(p["x"] for p in ci) / len(ci)
                cy_i = sum(p["y"] for p in ci) / len(ci)
                cx_j = sum(p["x"] for p in cj) / len(cj)
                cy_j = sum(p["y"] for p in cj) / len(cj)

                local_i = _nearest_node_index(nodes_i, cx_i, cy_i)
                local_j = _nearest_node_index(nodes_j, cx_j, cy_j)

                gid_i = self.local_to_global.get((fi, local_i))
                gid_j = self.local_to_global.get((fj, local_j))
                if gid_i is None or gid_j is None:
                    continue

                floor_diff = abs(int(fi) - int(fj))
                weight = max(floor_diff * 50.0, 50.0)

                self.global_adj.setdefault(gid_i, []).append((gid_j, weight))
                self.global_adj.setdefault(gid_j, []).append((gid_i, weight))

    def _get_point_coords(self, room: dict) -> tuple[float | None, float | None]:
        """
        Получить координаты точки входа для комнаты.
        Приоритет: entrance по room_number, fallback: центр полигона комнаты.
        """
        fn = room.get("floor_number")
        room_number = room.get("number")

        # Ищем entrance по room_number
        if fn and room_number:
            for ent in self.entrance_data.get(fn, []):
                if ent.get("room_number") == room_number:
                    return ent["x"], ent["y"]

        # Fallback: центр полигона
        coords = room.get("coordinates", {}).get("points", [])
        if coords:
            cx = sum(p["x"] for p in coords) / len(coords)
            cy = sum(p["y"] for p in coords) / len(coords)
            return cx, cy

        return None, None

    async def find_path(
        self,
        building_id: str,
        start_room: dict,
        end_room: dict,
        all_technical: list[dict],
    ) -> dict:
        """Найти путь между двумя комнатами."""
        start_floor_num = start_room["floor_number"]
        end_floor_num = end_room["floor_number"]

        await self.load_all_floors(building_id)
        if not self.grid_data:
            return {"found": False, "error": "No grid data available"}

        self._build_global_graph(all_technical)

        # Определяем координаты старта и финиша:
        # Приоритет: entrance point для комнаты, fallback: центр полигона
        start_x, start_y = self._get_point_coords(start_room)
        end_x, end_y = self._get_point_coords(end_room)

        if start_x is None or end_x is None:
            return {"found": False, "error": "No coordinates for rooms"}

        start_key = f"{building_id}_{start_floor_num}"
        end_key = f"{building_id}_{end_floor_num}"
        start_grid = self.grid_data.get(start_key)
        end_grid = self.grid_data.get(end_key)

        if not start_grid or not end_grid:
            return {"found": False, "error": "Grid not found for floors"}

        start_local = _nearest_node_index(start_grid["nodes"], start_x, start_y)
        end_local = _nearest_node_index(end_grid["nodes"], end_x, end_y)

        start_global = self.local_to_global.get((start_floor_num, start_local))
        end_global = self.local_to_global.get((end_floor_num, end_local))

        if start_global is None or end_global is None:
            return {"found": False, "error": "Could not find nearest nodes"}

        path = self._astar_global(start_global, end_global)
        if not path:
            return {"found": False, "error": "No path found"}

        segments: dict[str, list[dict]] = {}
        total_length = 0.0
        prev_fn = None
        transitions = []

        for gid_node in path:
            fn, li = self.global_to_local[gid_node]
            node = self.grid_data.get(f"{building_id}_{fn}", {}).get("nodes", [])[li]
            segments.setdefault(fn, []).append({"x": node["x"], "y": node["y"]})
            if prev_fn is not None and prev_fn != fn:
                transitions.append((prev_fn, fn))
            prev_fn = fn

        for i in range(1, len(path)):
            n1_data = self.global_to_local[path[i - 1]]
            n2_data = self.global_to_local[path[i]]
            n1_fn, n1_li = n1_data
            n2_fn, n2_li = n2_data
            g1 = self.grid_data.get(f"{building_id}_{n1_fn}")
            g2 = self.grid_data.get(f"{building_id}_{n2_fn}")
            if g1 and g2 and n1_fn == n2_fn:
                n1 = g1["nodes"][n1_li]
                n2 = g2["nodes"][n2_li]
                total_length += _distance(n1["x"], n1["y"], n2["x"], n2["y"])
            else:
                total_length += 50.0

        return {
            "found": True,
            "path": [{"floor_number": fn, "nodes": nodes} for fn, nodes in segments.items()],
            "total_length": round(total_length, 2),
            "floor_transitions": transitions,
        }

    def _astar_global(self, start_gid: int, end_gid: int) -> Optional[list[int]]:
        """A* на глобальном графе."""
        if start_gid == end_gid:
            return [start_gid]

        end_data = self.global_to_local.get(end_gid)
        if not end_data:
            return None
        end_fn, end_li = end_data
        end_grid = self.grid_data.get(f"{self.building_id}_{end_fn}")
        if not end_grid:
            return None
        end_node = end_grid["nodes"][end_li]

        def h(gid: int) -> float:
            d = self.global_to_local.get(gid)
            if not d:
                return 0
            fn, li = d
            grid = self.grid_data.get(f"{self.building_id}_{fn}")
            if not grid:
                return 0
            node = grid["nodes"][li]
            return _distance(node["x"], node["y"], end_node["x"], end_node["y"])

        g_score: dict[int, float] = {gid: float("inf") for gid in self.global_adj}
        g_score[start_gid] = 0

        f_score: dict[int, float] = {gid: float("inf") for gid in self.global_adj}
        f_score[start_gid] = h(start_gid)

        open_set: list[tuple[float, int]] = [(f_score[start_gid], start_gid)]
        came_from: dict[int, int] = {}

        while open_set:
            _, current = heapq.heappop(open_set)
            if current == end_gid:
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                path.reverse()
                return path

            for neighbor, weight in self.global_adj.get(current, []):
                tentative_g = g_score[current] + weight
                if tentative_g < g_score.get(neighbor, float("inf")):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f = tentative_g + h(neighbor)
                    f_score[neighbor] = f
                    heapq.heappush(open_set, (f, neighbor))

        return None
