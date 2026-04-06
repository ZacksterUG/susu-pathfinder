"""
Алгоритмы поиска пути (A*) для межэтажной навигации.
Использует сети лифтов и лестниц для перехода между этажами.
"""

import math
import heapq


def heuristic(node_a, node_b):
    """Эвристика для A* — евклидово расстояние"""
    return math.sqrt((node_a[0] - node_b[0])**2 + (node_a[1] - node_b[1])**2)


def find_nearest_node_to_point(x, y, nodes):
    """Найти ближайший узел сетки к точке"""
    if not nodes:
        return None, float('inf')
    min_dist = float('inf')
    nearest_idx = None
    for i, node in enumerate(nodes):
        dist = math.sqrt((x - node['x'])**2 + (y - node['y'])**2)
        if dist < min_dist:
            min_dist = dist
            nearest_idx = i
    return nearest_idx, min_dist


def build_adjacency_list(nodes, edges):
    """Построить список смежности для графа"""
    adj = {i: [] for i in range(len(nodes))}
    for edge in edges:
        from_idx = edge['from']
        to_idx = edge['to']
        weight = edge.get('weight', 1.0)
        adj[from_idx].append((to_idx, weight))
        adj[to_idx].append((from_idx, weight))
    return adj


def astar_on_floor(start_node_idx, end_node_idx, nodes, edges):
    """
    A* на одном этаже
    Возвращает список индексов узлов пути или None
    """
    if start_node_idx is None or end_node_idx is None:
        return None
    if start_node_idx == end_node_idx:
        return [start_node_idx]

    adj = build_adjacency_list(nodes, edges)

    g_score = {i: float('inf') for i in range(len(nodes))}
    g_score[start_node_idx] = 0

    f_score = {i: float('inf') for i in range(len(nodes))}
    start_pos = (nodes[start_node_idx]['x'], nodes[start_node_idx]['y'])
    end_pos = (nodes[end_node_idx]['x'], nodes[end_node_idx]['y'])
    f_score[start_node_idx] = heuristic(start_pos, end_pos)

    open_set = [(f_score[start_node_idx], start_node_idx)]
    came_from = {}

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == end_node_idx:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return path

        for neighbor, weight in adj.get(current, []):
            tentative_g = g_score[current] + weight
            if tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                neighbor_pos = (nodes[neighbor]['x'], nodes[neighbor]['y'])
                f_score[neighbor] = tentative_g + heuristic(neighbor_pos, end_pos)
                heapq.heappush(open_set, (f_score[neighbor], neighbor))

    return None


class MultiFloorPathFinder:
    """
    Межэтажный поиск пути.
    Строит граф, где узлы — это (floor, node_index), а рёбра включают:
    - горизонтальные (в рамках этажа)
    - вертикальные (через лифты/лестницы между этажами)
    """

    def __init__(self, grid_data, building_id, network_manager=None, floors_data=None):
        """
        Args:
            grid_data: dict {floor_key: {nodes, edges, ...}}
            building_id: ID корпуса
            network_manager: NetworkManager для получения связей лифтов/лестниц
            floors_data: данные о лифтах/лестницах из floors.json
        """
        self.grid_data = grid_data
        self.building_id = building_id
        self.network_manager = network_manager
        self.floors_data = floors_data or {}

        # Индексируем узлы: (floor, node_idx) -> global_id
        self.global_to_local = {}  # global_id -> (floor, node_idx)
        self.local_to_global = {}  # (floor, node_idx) -> global_id
        self._global_counter = 0

        # Строим глобальный граф
        self.global_adj = {}  # global_id -> [(global_id, weight)]
        self._build_global_graph()

    def _build_global_graph(self):
        """Построить глобальный граф со всеми этажами и связями"""
        # 1. Добавляем внутриэтажные рёбра
        for floor_key, grid in self.grid_data.items():
            # floor_key = "buildingId_floor"
            parts = floor_key.rsplit('_', 1)
            if len(parts) != 2:
                continue
            floor = parts[1]
            nodes = grid.get('nodes', [])
            edges = grid.get('edges', [])

            # Создаём global_id для каждого узла
            floor_node_map = {}  # local_idx -> global_id
            for local_idx in range(len(nodes)):
                gid = self._global_counter
                self._global_counter += 1
                self.global_to_local[gid] = (floor, local_idx)
                self.local_to_global[(floor, local_idx)] = gid
                floor_node_map[local_idx] = gid
                self.global_adj[gid] = []

            # Добавляем рёбра
            for edge in edges:
                from_gid = floor_node_map[edge['from']]
                to_gid = floor_node_map[edge['to']]
                weight = edge.get('weight', 1.0)
                self.global_adj[from_gid].append((to_gid, weight))
                self.global_adj[to_gid].append((from_gid, weight))

        # 2. Добавляем межэтажные рёбра через сети лифтов/лестниц
        if self.network_manager:
            networks = self.network_manager.get_building_networks(self.building_id)
            for network in networks:
                objects = network.get('objects', [])
                if len(objects) < 2:
                    continue

                # Для каждой пары объектов в сети добавляем вертикальные рёбра
                for i in range(len(objects)):
                    for j in range(i + 1, len(objects)):
                        obj1 = objects[i]
                        obj2 = objects[j]
                        floor1 = obj1['floor']
                        floor2 = obj2['floor']
                        obj1_id = obj1['id']
                        obj2_id = obj2['id']

                        self._add_vertical_edge(floor1, floor2, obj1_id, obj2_id)

    def _add_vertical_edge(self, floor1, floor2, obj1_id, obj2_id):
        """Добавить вертикальное ребро между объектами на разных этажах"""
        import json as json_module
        # floor1, floor2 — номера этажей (1, 2, 3...)
        grid1 = self.grid_data.get(f"{self.building_id}_{floor1}")
        grid2 = self.grid_data.get(f"{self.building_id}_{floor2}")

        if not grid1 or not grid2:
            return

        # Находим координаты объектов из floors_data
        obj1_coords = None
        obj2_coords = None
        
        building_objects = []
        if self.building_id in self.floors_data.get('elevators', {}):
            building_objects = self.floors_data['elevators'][self.building_id]
        
        for obj in building_objects:
            if obj.get('Id') == obj1_id:
                obj1_coords = obj.get('Coordinates')
            if obj.get('Id') == obj2_id:
                obj2_coords = obj.get('Coordinates')

        nodes1 = grid1.get('nodes', [])
        nodes2 = grid2.get('nodes', [])

        if not nodes1 or not nodes2:
            return

        # Парсим координаты и берём центр полигона
        def get_polygon_center(coords_str):
            if not coords_str:
                return None, None
            try:
                coords = json_module.loads(coords_str) if isinstance(coords_str, str) else coords_str
                points = coords.get('points', [])
                if points:
                    cx = sum(p['x'] for p in points) / len(points)
                    cy = sum(p['y'] for p in points) / len(points)
                    return cx, cy
            except:
                pass
            return None, None

        center1_x, center1_y = get_polygon_center(obj1_coords)
        center2_x, center2_y = get_polygon_center(obj2_coords)

        # Если не удалось получить координаты — используем центры сеток
        if center1_x is None:
            center1_x = sum(n['x'] for n in nodes1) / len(nodes1)
            center1_y = sum(n['y'] for n in nodes1) / len(nodes1)
        if center2_x is None:
            center2_x = sum(n['x'] for n in nodes2) / len(nodes2)
            center2_y = sum(n['y'] for n in nodes2) / len(nodes2)

        # Находим ближайшие узлы к центрам объектов
        gid1, _ = find_nearest_node_to_point(center1_x, center1_y, nodes1)
        gid2, _ = find_nearest_node_to_point(center2_x, center2_y, nodes2)

        if gid1 is None or gid2 is None:
            return

        global_id1 = self.local_to_global.get((floor1, gid1))
        global_id2 = self.local_to_global.get((floor2, gid2))

        if global_id1 is None or global_id2 is None:
            return

        # Добавляем ребро с весом = расстояние по вертикали (условно 50 единиц на этаж)
        floor1_num = int(floor1) if floor1.isdigit() else 0
        floor2_num = int(floor2) if floor2.isdigit() else 0
        floor_diff = abs(floor1_num - floor2_num)
        weight = max(floor_diff * 50.0, 50.0)

        self.global_adj[global_id1].append((global_id2, weight))
        self.global_adj[global_id2].append((global_id1, weight))

    def find_path(self, start_floor, start_x, start_y, end_floor, end_x, end_y):
        """
        Найти путь между двумя точками (возможно на разных этажах)
        start_floor, end_floor — полные ключи формата "buildingId_floor"
        """
        # Извлекаем номер этажа из полного ключа
        start_floor_num = start_floor.rsplit('_', 1)[-1] if '_' in start_floor else start_floor
        end_floor_num = end_floor.rsplit('_', 1)[-1] if '_' in end_floor else end_floor
        
        start_grid = self.grid_data.get(start_floor)
        end_grid = self.grid_data.get(end_floor)

        if not start_grid or not end_grid:
            return {'path': {}, 'total_length': 0, 'floor_transitions': [], 'found': False}

        start_nodes = start_grid.get('nodes', [])
        end_nodes = end_grid.get('nodes', [])

        start_local, _ = find_nearest_node_to_point(start_x, start_y, start_nodes)
        end_local, _ = find_nearest_node_to_point(end_x, end_y, end_nodes)

        if start_local is None or end_local is None:
            return {'path': {}, 'total_length': 0, 'floor_transitions': [], 'found': False}

        # Используем номер этажа (не полный ключ) для поиска в local_to_global
        start_global = self.local_to_global.get((start_floor_num, start_local))
        end_global = self.local_to_global.get((end_floor_num, end_local))

        if start_global is None or end_global is None:
            return {'path': {}, 'total_length': 0, 'floor_transitions': [], 'found': False}

        # Запускаем A* на глобальном графе
        global_path = self._astar_global(start_global, end_global)

        if not global_path:
            return {'path': {}, 'total_length': 0, 'floor_transitions': [], 'found': False}

        # Разбиваем глобальный путь по этажам
        floor_path = {}
        current_floor = None
        current_floor_nodes = []
        floor_transitions = []
        total_length = 0

        for i, gid in enumerate(global_path):
            floor, local_idx = self.global_to_local[gid]

            if floor != current_floor:
                if current_floor is not None:
                    floor_path[current_floor] = current_floor_nodes
                    floor_transitions.append((current_floor, floor))
                current_floor = floor
                current_floor_nodes = [local_idx]
            else:
                current_floor_nodes.append(local_idx)

            # Считаем длину
            if i > 0:
                prev_gid = global_path[i - 1]
                prev_floor, prev_local = self.global_to_local[prev_gid]
                prev_grid = self.grid_data.get(f"{self.building_id}_{prev_floor}")
                curr_grid = self.grid_data.get(f"{self.building_id}_{floor}")

                if prev_grid and curr_grid and prev_floor == floor:
                    n1 = prev_grid['nodes'][prev_local]
                    n2 = curr_grid['nodes'][local_idx]
                    total_length += math.sqrt((n1['x'] - n2['x'])**2 + (n1['y'] - n2['y'])**2)
                else:
                    # Межэтажный переход
                    total_length += 50.0  # Условное расстояние

        if current_floor_nodes:
            floor_path[current_floor] = current_floor_nodes

        return {
            'path': floor_path,
            'total_length': total_length,
            'floor_transitions': floor_transitions,
            'found': True
        }

    def _astar_global(self, start_gid, end_gid):
        """A* на глобальном графе"""
        if start_gid == end_gid:
            return [start_gid]

        g_score = {gid: float('inf') for gid in self.global_adj}
        g_score[start_gid] = 0

        floor1, idx1 = self.global_to_local[start_gid]
        floor2, idx2 = self.global_to_local[end_gid]
        # Ищем grid по полному ключу
        grid1 = self.grid_data.get(f"{self.building_id}_{floor1}")
        grid2 = self.grid_data.get(f"{self.building_id}_{floor2}")

        if grid1 and grid2:
            n1 = grid1['nodes'][idx1]
            n2 = grid2['nodes'][idx2]
            f_score = {gid: float('inf') for gid in self.global_adj}
            f_score[start_gid] = heuristic((n1['x'], n1['y']), (n2['x'], n2['y']))
        else:
            f_score = {gid: float('inf') for gid in self.global_adj}
            f_score[start_gid] = 0

        open_set = [(f_score[start_gid], start_gid)]
        came_from = {}

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
                if tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g

                    n_floor, n_idx = self.global_to_local[neighbor]
                    end_floor, end_idx = self.global_to_local[end_gid]
                    n_grid = self.grid_data.get(f"{self.building_id}_{n_floor}")
                    e_grid = self.grid_data.get(f"{self.building_id}_{end_floor}")

                    if n_grid and e_grid:
                        nn = n_grid['nodes'][n_idx]
                        en = e_grid['nodes'][end_idx]
                        h = heuristic((nn['x'], nn['y']), (en['x'], en['y']))
                    else:
                        h = 0

                    f_score[neighbor] = tentative_g + h
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))

        return None
