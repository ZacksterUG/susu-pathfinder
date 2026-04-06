import json
import tkinter as tk
from tkinter import ttk, messagebox
import math
import heapq

# Загружаем данные
with open('coordinates.json', 'r', encoding='utf-8') as f:
    coordinates = json.load(f)

with open('rooms.json', 'r', encoding='utf-8') as f:
    rooms = json.load(f)

with open('floors.json', 'r', encoding='utf-8') as f:
    infrastructure = json.load(f)

with open('buildings.json', 'r', encoding='utf-8') as f:
    buildings = json.load(f)

# Словари - сортируем по полному названию (Name)
buildings_sorted = sorted(buildings, key=lambda b: b['Name'])
building_names = {b['Id']: b['Name'] for b in buildings_sorted}
building_ids = [b['Id'] for b in buildings_sorted]

# Файлы для сохранения
ENTRANCES_FILE = 'entrances.json'
GRID_FILE = 'grid.json'

def load_entrances():
    try:
        with open(ENTRANCES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_entrances(data):
    with open(ENTRANCES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_grid():
    try:
        with open(GRID_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_grid(data):
    with open(GRID_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def parse_coordinates(coord_str):
    if isinstance(coord_str, str):
        try:
            data = json.loads(coord_str)
            return data.get('points', [])
        except:
            return []
    elif isinstance(coord_str, dict):
        return coord_str.get('points', [])
    return []

def point_in_polygon(px, py, polygon):
    """Проверка попадания точки в полигон"""
    n = len(polygon)
    if n == 0:
        return False
    inside = False
    x, y = px, py
    p1x, p1y = polygon[0]['x'], polygon[0]['y']
    for i in range(n + 1):
        p2x, p2y = polygon[i % n]['x'], polygon[i % n]['y']
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    else:
                        xinters = p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside

def point_on_polygon_boundary(px, py, polygon, tolerance=2.0):
    """Проверка, находится ли точка на границе полигона (с допуском)"""
    n = len(polygon)
    if n < 2:
        return False
    for i in range(n):
        p1 = polygon[i]
        p2 = polygon[(i + 1) % n]
        dist = point_to_segment_distance(px, py, p1['x'], p1['y'], p2['x'], p2['y'])
        if dist <= tolerance:
            return True
    return False

def point_to_segment_distance(px, py, x1, y1, x2, y2):
    """Расстояние от точки до отрезка"""
    dx = x2 - x1
    dy = y2 - y1
    if dx == 0 and dy == 0:
        return math.sqrt((px - x1)**2 + (py - y1)**2)
    t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
    proj_x = x1 + t * dx
    proj_y = y1 + t * dy
    return math.sqrt((px - proj_x)**2 + (py - proj_y)**2)

def find_nearest_boundary_point(px, py, polygon):
    """Найти ближайшую точку на границе полигона (целочисленную)"""
    if not polygon or len(polygon) < 2:
        return None, None
    min_dist = float('inf')
    nearest_x, nearest_y = px, py
    n = len(polygon)
    for i in range(n):
        p1 = polygon[i]
        p2 = polygon[(i + 1) % n]
        x1, y1 = p1['x'], p1['y']
        x2, y2 = p2['x'], p2['y']
        dx = x2 - x1
        dy = y2 - y1
        if dx == 0 and dy == 0:
            t = 0
        else:
            t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
        proj_x = x1 + t * dx
        proj_y = y1 + t * dy
        for rx in [math.floor(proj_x), math.ceil(proj_x)]:
            for ry in [math.floor(proj_y), math.ceil(proj_y)]:
                dist_to_seg = point_to_segment_distance(rx, ry, x1, y1, x2, y2)
                if dist_to_seg <= 1.5:
                    dist = math.sqrt((px - rx)**2 + (py - ry)**2)
                    if dist < min_dist:
                        min_dist = dist
                        nearest_x, nearest_y = rx, ry
    return nearest_x, nearest_y

def filter_nodes_on_boundary(nodes, obstacles, tolerance=2.0):
    """
    Удалить узлы, которые лежат на контуре препятствий (аудитории/лестницы/лифты)
    """
    filtered = []
    for node in nodes:
        x, y = node['x'], node['y']
        is_on_boundary = False
        for obstacle in obstacles:
            if point_on_polygon_boundary(x, y, obstacle, tolerance):
                is_on_boundary = True
                break
        if not is_on_boundary:
            filtered.append(node)
    return filtered

def find_nearest_edge_point(entrance_x, entrance_y, nodes, edges, cell_size):
    """
    Найти ближайшую точку на ребре сетки для подключения входа
    Возвращает (edge_index, projection_x, projection_y, distance)
    """
    if not edges or not nodes:
        return None, None, None, float('inf')
    
    min_dist = float('inf')
    best_edge = None
    best_proj = None
    
    for i, edge in enumerate(edges):
        n1 = nodes[edge['from']]
        n2 = nodes[edge['to']]
        
        x1, y1 = n1['x'], n1['y']
        x2, y2 = n2['x'], n2['y']
        
        # Проекция точки на отрезок
        dx = x2 - x1
        dy = y2 - y1
        
        if dx == 0 and dy == 0:
            t = 0
        else:
            t = max(0, min(1, ((entrance_x - x1) * dx + (entrance_y - y1) * dy) / (dx * dx + dy * dy)))
        
        proj_x = x1 + t * dx
        proj_y = y1 + t * dy
        
        dist = math.sqrt((entrance_x - proj_x)**2 + (entrance_y - proj_y)**2)
        
        if dist < min_dist:
            min_dist = dist
            best_edge = i
            best_proj = (proj_x, proj_y)
    
    return best_edge, best_proj[0], best_proj[1], min_dist

def generate_grid_nodes(corridor_points, obstacles, cell_size):
    """
    Генерация узлов сетки для коридора
    """
    if not corridor_points:
        return []
    
    x_coords = [p['x'] for p in corridor_points]
    y_coords = [p['y'] for p in corridor_points]
    min_x, max_x = int(min(x_coords)), int(max(x_coords))
    min_y, max_y = int(min(y_coords)), int(max(y_coords))
    
    nodes = []
    
    for x in range(min_x, max_x + 1, cell_size):
        for y in range(min_y, max_y + 1, cell_size):
            if not point_in_polygon(x, y, corridor_points):
                continue
            
            is_blocked = False
            for obstacle in obstacles:
                if point_in_polygon(x, y, obstacle):
                    is_blocked = True
                    break
            
            if not is_blocked:
                nodes.append({'x': x, 'y': y})
    
    # Фильтруем узлы на контуре препятствий
    nodes = filter_nodes_on_boundary(nodes, obstacles, tolerance=cell_size * 0.3)
    
    return nodes

def connect_nodes(nodes, cell_size, corridor_points, obstacles):
    """
    Соединение узлов сетки в граф
    """
    edges = []
    nodes_set = {(n['x'], n['y']) for n in nodes}
    node_index = {(n['x'], n['y']): i for i, n in enumerate(nodes)}
    
    for i, node in enumerate(nodes):
        x, y = node['x'], node['y']
        
        neighbors = [
            (x + cell_size, y),
            (x - cell_size, y),
            (x, y + cell_size),
            (x, y - cell_size),
        ]
        
        for nx, ny in neighbors:
            if (nx, ny) in node_index:
                ni = node_index[(nx, ny)]
                if ni <= i:  # Избегаем дублирования
                    continue
                
                mid_x = (x + nx) / 2
                mid_y = (y + ny) / 2
                
                if not point_in_polygon(mid_x, mid_y, corridor_points):
                    continue
                
                is_blocked = False
                for obstacle in obstacles:
                    if point_in_polygon(mid_x, mid_y, obstacle):
                        is_blocked = True
                        break
                
                if not is_blocked:
                    dist = math.sqrt((nx - x)**2 + (ny - y)**2)
                    edges.append({
                        'from': i,
                        'to': ni,
                        'weight': dist
                    })
    
    return edges

def connect_entrance_to_grid(entrance_x, entrance_y, nodes, edges, corridor_points, obstacles):
    """
    Подключить точку входа к сетке:
    1. Найти ближайшее ребро
    2. Добавить новый узел в точке проекции
    3. Добавить рёбра от нового узла к концам исходного ребра
    4. Добавить ребро от точки входа к новому узлу
    """
    edge_idx, proj_x, proj_y, dist = find_nearest_edge_point(entrance_x, entrance_y, nodes, edges, 20)
    
    if edge_idx is None or dist > 100:  # Слишком далеко
        return nodes, edges, False
    
    # Находим узлы исходного ребра
    edge = edges[edge_idx]
    n1_idx = edge['from']
    n2_idx = edge['to']
    n1 = nodes[n1_idx]
    n2 = nodes[n2_idx]
    
    # Округляем проекцию до целых
    proj_x = int(round(proj_x))
    proj_y = int(round(proj_y))
    
    # Проверяем, что проекция внутри коридора и не в препятствии
    if not point_in_polygon(proj_x, proj_y, corridor_points):
        return nodes, edges, False
    
    for obstacle in obstacles:
        if point_in_polygon(proj_x, proj_y, obstacle):
            return nodes, edges, False
    
    # Добавляем новый узел (проекция на ребро)
    new_node_idx = len(nodes)
    nodes.append({'x': proj_x, 'y': proj_y})
    
    # Добавляем узел точки входа
    entrance_node_idx = len(nodes)
    nodes.append({'x': entrance_x, 'y': entrance_y})
    
    # Удаляем старое ребро
    edges.pop(edge_idx)
    
    # Добавляем новые рёбра: n1 -> new_node, new_node -> n2
    edges.append({
        'from': n1_idx,
        'to': new_node_idx,
        'weight': math.sqrt((proj_x - n1['x'])**2 + (proj_y - n1['y'])**2)
    })
    
    edges.append({
        'from': new_node_idx,
        'to': n2_idx,
        'weight': math.sqrt((n2['x'] - proj_x)**2 + (n2['y'] - proj_y)**2)
    })
    
    # Добавляем ребро от проекции ко входу
    edges.append({
        'from': new_node_idx,
        'to': entrance_node_idx,
        'weight': math.sqrt((entrance_x - proj_x)**2 + (entrance_y - proj_y)**2)
    })
    
    return nodes, edges, True

def heuristic(node_a, node_b):
    """Эвристика для A* - евклидово расстояние"""
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
        adj[to_idx].append((from_idx, weight))  # Граф неориентированный
    
    return adj

def astar_pathfinding(start_node_idx, end_node_idx, nodes, edges):
    """
    Алгоритм A* для поиска кратчайшего пути между узлами
    Возвращает список индексов узлов пути или None если путь не найден
    """
    if start_node_idx is None or end_node_idx is None:
        return None
    
    if start_node_idx == end_node_idx:
        return [start_node_idx]
    
    adj = build_adjacency_list(nodes, edges)
    
    # g_score - стоимость пути от старта до текущего узла
    g_score = {i: float('inf') for i in range(len(nodes))}
    g_score[start_node_idx] = 0
    
    # f_score = g_score + heuristic
    f_score = {i: float('inf') for i in range(len(nodes))}
    start_pos = (nodes[start_node_idx]['x'], nodes[start_node_idx]['y'])
    end_pos = (nodes[end_node_idx]['x'], nodes[end_node_idx]['y'])
    f_score[start_node_idx] = heuristic(start_pos, end_pos)
    
    # Очередь с приоритетом (f_score, node_idx)
    open_set = [(f_score[start_node_idx], start_node_idx)]
    
    # Для восстановления пути
    came_from = {}
    
    while open_set:
        _, current = heapq.heappop(open_set)
        
        if current == end_node_idx:
            # Восстанавливаем путь
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
    
    return None  # Путь не найден

class MapApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Разметка входов и сетки СУСУ")
        self.root.geometry("1400x950")

        self.current_building = None
        self.current_floor = None
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.entrances = load_entrances()
        self.grid_data = load_grid()

        self.preview_dot = None
        self.current_hover_obj = None
        self.hover_x = 0
        self.hover_y = 0
        self.nearest_boundary_x = None
        self.nearest_boundary_y = None

        self.cell_size = 20
        self.grid_nodes = []
        self.grid_edges = []
        self.show_grid = False

        self.room_polygons = {}
        self.obstacles = []
        self.corridor_points = []

        # Для подключения входов
        self.entrance_connections = []  # Список подключённых входов

        # Для поиска пути
        self.path_start_room = None  # Выбранная аудитория отправления
        self.path_end_room = None    # Выбранная аудитория назначения
        self.current_path = None     # Текущий найденный путь (список индексов узлов)

        self.setup_ui()
        
    def setup_ui(self):
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(side=tk.TOP, fill=tk.X)
        
        # Выбор корпуса
        ttk.Label(control_frame, text="Корпус:").pack(side=tk.LEFT, padx=5)
        self.building_var = tk.StringVar()
        self.building_combo = ttk.Combobox(control_frame, textvariable=self.building_var, width=50)
        self.building_combo['values'] = [building_names[bid] for bid in building_ids]
        self.building_combo.pack(side=tk.LEFT, padx=5)
        self.building_combo.bind('<<ComboboxSelected>>', self.on_building_select)
        
        # Выбор этажа
        ttk.Label(control_frame, text="Этаж:").pack(side=tk.LEFT, padx=5)
        self.floor_var = tk.StringVar()
        self.floor_combo = ttk.Combobox(control_frame, textvariable=self.floor_var, width=5)
        self.floor_combo.pack(side=tk.LEFT, padx=5)
        self.floor_combo.bind('<<ComboboxSelected>>', self.on_floor_select)
        
        # Разделитель
        ttk.Separator(control_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=20, fill=tk.Y)
        
        # Размер клетки
        ttk.Label(control_frame, text="📐 Клетка:").pack(side=tk.LEFT, padx=5)
        self.cell_size_var = tk.IntVar(value=20)
        self.cell_size_slider = ttk.Scale(control_frame, from_=5, to=100, 
                                          orient=tk.HORIZONTAL, variable=self.cell_size_var,
                                          command=self.on_cell_size_change)
        self.cell_size_slider.pack(side=tk.LEFT, padx=5)
        self.cell_size_label = ttk.Label(control_frame, text="20", width=3)
        self.cell_size_label.pack(side=tk.LEFT, padx=5)
        
        # Кнопки сетки
        ttk.Button(control_frame, text="🕸️ Построить сетку", command=self.build_grid).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="👁️ Показать/скрыть", command=self.toggle_grid).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="💾 Сохранить сетку", command=self.save_grid_ui).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="🔗 Подключить входы", command=self.connect_entrances).pack(side=tk.LEFT, padx=5)
        
        # Разделитель
        ttk.Separator(control_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=20, fill=tk.Y)
        
        # Кнопки входов
        ttk.Button(control_frame, text="🟢 Сохранить входы", command=self.save_entrances_ui).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="🗑️ Очистить входы", command=self.clear_entrances).pack(side=tk.LEFT, padx=5)

        # Статус
        self.status_label = ttk.Label(control_frame, text="", foreground="green", font=("Arial", 10))
        self.status_label.pack(side=tk.RIGHT, padx=10)

        # Вторая строка - Поиск пути
        path_frame = ttk.Frame(self.root, padding="10")
        path_frame.pack(side=tk.TOP, fill=tk.X)
        
        ttk.Label(path_frame, text="🛣️ Поиск пути:").pack(side=tk.LEFT, padx=5)
        ttk.Label(path_frame, text="От:").pack(side=tk.LEFT, padx=5)
        self.path_start_var = tk.StringVar()
        self.path_start_combo = ttk.Combobox(path_frame, textvariable=self.path_start_var, width=10)
        self.path_start_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(path_frame, text="До:").pack(side=tk.LEFT, padx=5)
        self.path_end_var = tk.StringVar()
        self.path_end_combo = ttk.Combobox(path_frame, textvariable=self.path_end_var, width=10)
        self.path_end_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(path_frame, text="🔍 Построить путь", command=self.build_path).pack(side=tk.LEFT, padx=5)
        ttk.Button(path_frame, text="❌ Сбросить путь", command=self.clear_path).pack(side=tk.LEFT, padx=5)
        
        # Холст
        self.canvas_frame = ttk.Frame(self.root)
        self.canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg='white', cursor='crosshair')
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Скроллбары
        v_scroll = ttk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll = ttk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.canvas.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        # Обработчики
        self.canvas.bind('<Motion>', self.on_mouse_move)
        self.canvas.bind('<Button-1>', self.on_canvas_click)
        self.canvas.bind('<Leave>', self.on_mouse_leave)
        self.canvas.bind('<MouseWheel>', self.on_mouse_wheel)
        
        # Информация
        self.info_frame = ttk.Frame(self.root, padding="10")
        self.info_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.info_label = ttk.Label(self.info_frame, text="Наведите на контур аудитории/лестницы и кликните для установки точки входа", font=("Arial", 11))
        self.info_label.pack()
        
        self.current_room_label = ttk.Label(self.info_frame, text="", font=("Arial", 10, "bold"), foreground="blue")
        self.current_room_label.pack()
        
        self.coord_label = ttk.Label(self.info_frame, text="", font=("Arial", 9), foreground="gray")
        self.coord_label.pack()
        
        self.grid_info_label = ttk.Label(self.info_frame, text="", font=("Arial", 9), foreground="purple")
        self.grid_info_label.pack()
        
        # Легенда
        self.legend_frame = ttk.Frame(self.root, padding="5")
        self.legend_frame.pack(side=tk.BOTTOM)

        ttk.Label(self.legend_frame, text=" Аудитория  🔴 Лестница  🟡 Лифт   Тех.помещение   Вход  ⚪ Предпросмотр  🔵 Узел  🟢 Подключение",
                 font=("Arial", 10)).pack()
        
        ttk.Label(self.legend_frame, text=" 🟠 Путь",
                 font=("Arial", 10), foreground="#FF4500").pack()
        
    def on_building_select(self, event):
        selected = self.building_combo.get()
        for bid in building_ids:
            if building_names[bid] == selected:
                self.current_building = bid
                self.update_floor_combo()
                break
        
    def update_floor_combo(self):
        if not self.current_building:
            return
        floors = list(coordinates.get(self.current_building, {}).keys())
        self.floor_combo['values'] = floors
        if floors:
            self.floor_combo.current(0)
            self.on_floor_select(None)
            
    def on_floor_select(self, event):
        if not self.current_building:
            return
        floor_str = self.floor_var.get()
        if not floor_str:
            return
        self.current_floor = floor_str
        self.room_polygons = {}
        self.obstacles = []
        self.grid_nodes = []
        self.grid_edges = []
        self.show_grid = False
        self.entrance_connections = []
        self.corridor_points = []
        
        # Сброс поиска пути
        self.path_start_room = None
        self.path_end_room = None
        self.current_path = None

        # Загружаем сохранённую сетку для этого этажа
        grid_key = f"{self.current_building}_{self.current_floor}"
        if grid_key in self.grid_data:
            saved_grid = self.grid_data[grid_key]
            self.grid_nodes = saved_grid.get('nodes', [])
            self.grid_edges = saved_grid.get('edges', [])
            self.entrance_connections = saved_grid.get('entrance_connections', [])
            self.cell_size = saved_grid.get('cell_size', 20)
            self.cell_size_var.set(self.cell_size)
            self.cell_size_label.config(text=str(self.cell_size))
            self.show_grid = True
        
        # Заполняем комбобоксы аудиториями
        self.update_room_combos()

        self.draw_map()

        if self.grid_nodes:
            self.grid_info_label.config(text=f"🕸️ Сетка: {len(self.grid_nodes)} узлов, {len(self.grid_edges)} рёбер (загружена)")
            self.status_label.config(text=f"✓ Сетка загружена из {GRID_FILE}")
    
    def update_room_combos(self):
        """Заполнить комбобоксы выбора аудиторий"""
        if not self.current_building or not self.current_floor:
            return
        
        building_rooms = rooms.get(self.current_building, [])
        floor_rooms = [r for r in building_rooms if str(r.get('Floor', '')) == str(self.current_floor)]
        
        # Сортируем по номеру
        floor_rooms_sorted = sorted(floor_rooms, key=lambda r: str(r.get('Number', '')))
        
        room_numbers = [r.get('Number', str(r.get('Id', ''))) for r in floor_rooms_sorted]
        
        self.path_start_combo['values'] = room_numbers
        self.path_end_combo['values'] = room_numbers
        if room_numbers:
            self.path_start_combo.current(0)
            self.path_end_combo.current(len(room_numbers) - 1 if len(room_numbers) > 1 else 0)
        
    def on_cell_size_change(self, value):
        self.cell_size = int(float(value))
        self.cell_size_label.config(text=str(self.cell_size))
        if self.show_grid and self.grid_nodes:
            self.build_grid()
        
    def build_grid(self):
        """Построить сетку"""
        if not self.current_building or not self.current_floor:
            messagebox.showwarning("Ошибка", "Выберите корпус и этаж")
            return

        corridor_data = coordinates.get(self.current_building, {}).get(self.current_floor, {})
        self.corridor_points = parse_coordinates(corridor_data)

        if not self.corridor_points:
            messagebox.showwarning("Ошибка", "Нет данных о коридорах")
            return

        # Собираем все препятствия: аудитории, лестницы, лифты, технические помещения
        obstacles = []
        for obj_id, obj_data in self.room_polygons.items():
            obstacles.append(obj_data['polygon'])

        self.obstacles = obstacles

        self.grid_nodes = generate_grid_nodes(self.corridor_points, obstacles, self.cell_size)
        self.grid_edges = connect_nodes(self.grid_nodes, self.cell_size, self.corridor_points, obstacles)

        self.show_grid = True
        self.entrance_connections = []  # Сброс подключений
        self.draw_map()

        self.grid_info_label.config(text=f"🕸️ Сетка: {len(self.grid_nodes)} узлов, {len(self.grid_edges)} рёбер")
        self.status_label.config(text=f"✓ Сетка построена (клетка={self.cell_size}), узлы на контуре удалены")
        
    def toggle_grid(self):
        """Показать/скрыть сетку"""
        if self.grid_nodes:
            self.show_grid = not self.show_grid
            self.draw_map()
            self.status_label.config(text=f"{'✓ Сетка показана' if self.show_grid else '○ Сетка скрыта'}")
        else:
            messagebox.showinfo("Инфо", "Сначала постройте сетку")
        
    def connect_entrances(self):
        """Подключить все входы к сетке"""
        if not self.grid_nodes:
            messagebox.showwarning("Ошибка", "Сначала постройте сетку")
            return
        
        entrances_key = f"{self.current_building}_{self.current_floor}"
        floor_entrances = self.entrances.get(entrances_key, {})
        
        if not floor_entrances:
            messagebox.showinfo("Инфо", "Нет точек входа для подключения")
            return
        
        connected_count = 0
        for obj_id, entrance_data in floor_entrances.items():
            if 'x' not in entrance_data or 'y' not in entrance_data:
                continue
            
            ex, ey = entrance_data['x'], entrance_data['y']
            
            # Проверяем, не подключён ли уже
            if any(c['entrance_id'] == obj_id for c in self.entrance_connections):
                continue
            
            # Подключаем
            new_nodes, new_edges, success = connect_entrance_to_grid(
                ex, ey, self.grid_nodes, self.grid_edges, 
                self.corridor_points, self.obstacles
            )
            
            if success:
                self.grid_nodes = new_nodes
                self.grid_edges = new_edges
                self.entrance_connections.append({
                    'entrance_id': obj_id,
                    'entrance_x': ex,
                    'entrance_y': ey,
                    'connection_node_idx': len(self.grid_nodes) - 1
                })
                connected_count += 1
        
        self.draw_map()
        self.grid_info_label.config(text=f"🕸️ Сетка: {len(self.grid_nodes)} узлов, {len(self.grid_edges)} рёбер")
        self.status_label.config(text=f"✓ Подключено входов: {connected_count}")

    def find_entrance_for_room(self, room_number):
        """
        Найти точку входа для аудитории по номеру
        Возвращает (x, y) координаты входа или None
        """
        if not self.current_building or not self.current_floor:
            return None
        
        entrances_key = f"{self.current_building}_{self.current_floor}"
        floor_entrances = self.entrances.get(entrances_key, {})
        
        # Ищем вход по номеру комнаты
        for obj_id, entrance_data in floor_entrances.items():
            if entrance_data.get('room_number') == room_number:
                return (entrance_data['x'], entrance_data['y'])
        
        return None
    
    def find_room_polygon_by_number(self, room_number):
        """
        Найти полигон аудитории по номеру
        Возвращает (obj_id, polygon) или None
        """
        for obj_id, obj_data in self.room_polygons.items():
            if obj_data.get('number') == room_number:
                return (obj_id, obj_data['polygon'])
        return None

    def build_path(self):
        """Построить путь от одной аудитории к другой"""
        if not self.grid_nodes:
            messagebox.showwarning("Ошибка", "Сначала постройте сетку")
            return
        
        start_room = self.path_start_var.get()
        end_room = self.path_end_var.get()
        
        if not start_room or not end_room:
            messagebox.showwarning("Ошибка", "Выберите аудитории отправления и назначения")
            return
        
        if start_room == end_room:
            messagebox.showinfo("Инфо", "Аудитории совпадают")
            return
        
        # Находим входы для аудиторий
        start_entrance = self.find_entrance_for_room(start_room)
        end_entrance = self.find_entrance_for_room(end_room)
        
        if not start_entrance:
            messagebox.showwarning("Ошибка", f"Нет точки входа для аудитории {start_room}")
            return
        
        if not end_entrance:
            messagebox.showwarning("Ошибка", f"Нет точки входа для аудитории {end_room}")
            return
        
        # Находим ближайшие узлы сетки к точкам входов
        start_node_idx, _ = find_nearest_node_to_point(start_entrance[0], start_entrance[1], self.grid_nodes)
        end_node_idx, _ = find_nearest_node_to_point(end_entrance[0], end_entrance[1], self.grid_nodes)
        
        if start_node_idx is None or end_node_idx is None:
            messagebox.showwarning("Ошибка", "Не удалось найти узлы сетки для входов")
            return
        
        # Запускаем A*
        path = astar_pathfinding(start_node_idx, end_node_idx, self.grid_nodes, self.grid_edges)
        
        if path:
            self.current_path = path
            self.path_start_room = start_room
            self.path_end_room = end_room
            
            # Считаем длину пути
            path_length = 0
            for i in range(len(path) - 1):
                n1 = self.grid_nodes[path[i]]
                n2 = self.grid_nodes[path[i + 1]]
                path_length += math.sqrt((n1['x'] - n2['x'])**2 + (n1['y'] - n2['y'])**2)
            
            self.draw_map()
            self.status_label.config(text=f"🛣️ Путь: {start_room} → {end_room}, длина: {path_length:.1f}")
        else:
            messagebox.showwarning("Ошибка", "Путь не найден")

    def clear_path(self):
        """Сбросить путь"""
        self.current_path = None
        self.path_start_room = None
        self.path_end_room = None
        self.draw_map()
        self.status_label.config(text="Путь сброшен")

    def save_grid_ui(self):
        """Сохранить сетку"""
        if not self.grid_nodes:
            messagebox.showwarning("Ошибка", "Сначала постройте сетку")
            return
        
        grid_key = f"{self.current_building}_{self.current_floor}"
        
        if grid_key not in self.grid_data:
            self.grid_data[grid_key] = {}
        
        self.grid_data[grid_key] = {
            'cell_size': self.cell_size,
            'nodes': self.grid_nodes,
            'edges': self.grid_edges,
            'entrance_connections': self.entrance_connections,
            'building_name': building_names.get(self.current_building, ''),
            'floor': self.current_floor
        }
        
        save_grid(self.grid_data)
        self.status_label.config(text=f"💾 Сетка сохранена в {GRID_FILE}")
        
    def draw_map(self):
        if not self.current_building or not self.current_floor:
            return
            
        self.canvas.delete('all')
        
        corridor_data = coordinates.get(self.current_building, {}).get(self.current_floor, {})
        corridor_points = parse_coordinates(corridor_data)
        
        if not corridor_points:
            return
        
        min_x = min(p['x'] for p in corridor_points)
        max_x = max(p['x'] for p in corridor_points)
        min_y = min(p['y'] for p in corridor_points)
        max_y = max(p['y'] for p in corridor_points)
        
        map_width = max_x - min_x + 100
        map_height = max_y - min_y + 100
        
        self.scale = 2.0
        self.offset_x = 50 - min_x * self.scale
        self.offset_y = 50 - min_y * self.scale
        
        def scale_point(x, y):
            return (x * self.scale + self.offset_x, y * self.scale + self.offset_y)
        
        # Коридор
        corridor_scaled = [scale_point(p['x'], p['y']) for p in corridor_points]
        self.canvas.create_polygon(corridor_scaled, fill='#E0E0E0', outline='#808080', width=2, tags='corridor')
        
        # Аудитории
        building_rooms = rooms.get(self.current_building, [])
        floor_rooms = [r for r in building_rooms if str(r.get('Floor', '')) == str(self.current_floor)]
        
        for room in floor_rooms:
            room_coords = room.get('Coordinates')
            if room_coords:
                room_points = parse_coordinates(room_coords)
                if room_points:
                    room_id = room.get('Id', room.get('Number', ''))
                    room_number = room.get('Number', '?')

                    # Отрисовка полигона (не прямоугольника)
                    room_scaled = [scale_point(p['x'], p['y']) for p in room_points]
                    self.canvas.create_polygon(room_scaled, fill='#4169E1', outline='#000080', width=1,
                                               tags=('room', room_id))

                    # Вычисляем центр для подписи
                    cx = sum(p[0] for p in room_scaled) / len(room_scaled)
                    cy = sum(p[1] for p in room_scaled) / len(room_scaled)
                    self.canvas.create_text(cx, cy, text=str(room_number), fill='white',
                                           font=('Arial', 12, 'bold'), tags=('room_text', room_id))

                    self.room_polygons[room_id] = {
                        'polygon': room_points,
                        'room': room,
                        'type': 'room',
                        'number': room_number,
                        'bbox': (min(p['x'] for p in room_points), max(p['x'] for p in room_points),
                                 min(p['y'] for p in room_points), max(p['y'] for p in room_points))
                    }
        
        # Лестницы
        building_infra = infrastructure.get('elevators', {}).get(self.current_building, [])
        floor_stairs = [s for s in building_infra
                       if str(s.get('Floor', '')) == str(self.current_floor)
                       and s.get('InfrastructureObjectType') == 'Лестница']

        for stair in floor_stairs:
            stair_points = parse_coordinates(stair.get('Coordinates'))
            if stair_points:
                stair_id = stair.get('Id', '')
                
                # Отрисовка полигона
                stair_scaled = [scale_point(p['x'], p['y']) for p in stair_points]
                self.canvas.create_polygon(stair_scaled, fill='#DC143C', outline='#8B0000', width=1,
                                            tags=('stairs', stair_id))

                self.room_polygons[stair_id] = {
                    'polygon': stair_points,
                    'room': stair,
                    'type': 'stairs',
                    'number': f"Лестница {stair.get('Floor', '?')}",
                    'bbox': (min(p['x'] for p in stair_points), max(p['x'] for p in stair_points),
                             min(p['y'] for p in stair_points), max(p['y'] for p in stair_points)),
                    'can_enter': True  # Можно ставить входы
                }

        # Лифты
        floor_elevators = [e for e in building_infra
                          if str(e.get('Floor', '')) == str(self.current_floor)
                          and 'Лифт' in e.get('InfrastructureObjectType', '')]

        for elevator in floor_elevators:
            elev_points = parse_coordinates(elevator.get('Coordinates'))
            if elev_points:
                elev_id = elevator.get('Id', '')
                
                # Отрисовка полигона
                elev_scaled = [scale_point(p['x'], p['y']) for p in elev_points]
                self.canvas.create_polygon(elev_scaled, fill='#FFD700', outline='#B8860B', width=1,
                                            tags=('elevator', elev_id))

                self.room_polygons[elev_id] = {
                    'polygon': elev_points,
                    'room': elevator,
                    'type': 'elevator',
                    'number': f"Лифт {elevator.get('Floor', '?')}",
                    'bbox': (min(p['x'] for p in elev_points), max(p['x'] for p in elev_points),
                             min(p['y'] for p in elev_points), max(p['y'] for p in elev_points)),
                    'can_enter': True  # Можно ставить входы
                }
        
        # Технические помещения (туалеты, охрана, подсобки и т.д.)
        TECH_TYPES = ['Туалет', 'Охрана', 'Подсобное', 'Гардероб', 'Кафетерий', 'Пункт питания', 'Зона']
        floor_tech = [t for t in building_infra
                     if str(t.get('Floor', '')) == str(self.current_floor)
                     and any(tt in t.get('InfrastructureObjectType', '') for tt in TECH_TYPES)
                     and t.get('InfrastructureObjectType') != 'Лестница'
                     and 'Лифт' not in t.get('InfrastructureObjectType', '')]

        for tech in floor_tech:
            tech_points = parse_coordinates(tech.get('Coordinates'))
            if tech_points:
                tech_id = tech.get('Id', '')
                tech_name = tech.get('Name', 'Тех. помещение')
                tech_type = tech.get('InfrastructureObjectType', '')

                # Отрисовка полигона
                tech_scaled = [scale_point(p['x'], p['y']) for p in tech_points]
                self.canvas.create_polygon(tech_scaled, fill='#FFFFFF', outline='#808080', width=1,
                                            tags=('tech', tech_id))

                # Подпись для некоторых типов
                if 'Туалет' in tech_type or 'Охрана' in tech_type:
                    cx = sum(p[0] for p in tech_scaled) / len(tech_scaled)
                    cy = sum(p[1] for p in tech_scaled) / len(tech_scaled)
                    self.canvas.create_text(cx, cy, text=tech_name[:10], fill='#808080',
                                           font=('Arial', 8), tags=('tech_text', tech_id))

                self.room_polygons[tech_id] = {
                    'polygon': tech_points,
                    'room': tech,
                    'type': 'tech',
                    'number': f"{tech_type}",
                    'bbox': (min(p['x'] for p in tech_points), max(p['x'] for p in tech_points),
                             min(p['y'] for p in tech_points), max(p['y'] for p in tech_points)),
                    'can_enter': False  # Нельзя ставить входы
                }
        
        # Сетка
        if self.show_grid and self.grid_nodes:
            # Рёбра
            for edge in self.grid_edges:
                if edge['from'] < len(self.grid_nodes) and edge['to'] < len(self.grid_nodes):
                    n1 = self.grid_nodes[edge['from']]
                    n2 = self.grid_nodes[edge['to']]
                    x1, y1 = scale_point(n1['x'], n1['y'])
                    x2, y2 = scale_point(n2['x'], n2['y'])
                    self.canvas.create_line(x1, y1, x2, y2, fill='#006400', width=1, 
                                           tags='grid_edge')
            
            # Узлы
            for i, node in enumerate(self.grid_nodes):
                nx, ny = scale_point(node['x'], node['y'])
                
                # Проверяем, это точка подключения?
                is_connection = any(
                    c['connection_node_idx'] == i or 
                    (c.get('entrance_x') == node['x'] and c.get('entrance_y') == node['y'])
                    for c in self.entrance_connections
                )
                
                if is_connection:
                    # Точка подключения - больший зелёный круг
                    self.canvas.create_oval(nx-5, ny-5, nx+5, ny+5, 
                                           fill='#00FF00', outline='#006400', width=2,
                                           tags='grid_node')
                else:
                    # Обычный узел
                    self.canvas.create_oval(nx-3, ny-3, nx+3, ny+3,
                                           fill='#00BFFF', outline='#006400', width=1,
                                           tags='grid_node')

        # Визуализация пути
        if self.current_path and self.grid_nodes:
            # Рисуем линию пути толщиной с узел
            path_coords = []
            for node_idx in self.current_path:
                node = self.grid_nodes[node_idx]
                sx, sy = scale_point(node['x'], node['y'])
                path_coords.extend([sx, sy])
            
            if len(path_coords) >= 4:
                self.canvas.create_line(path_coords, fill='#FF4500', width=12,
                                       tags='path_line', capstyle=tk.ROUND, joinstyle=tk.ROUND)

        # Точки входа
        self.draw_entrances(scale_point)
        
        self.canvas.configure(scrollregion=(0, 0, map_width * self.scale + 100, map_height * self.scale + 100))
        
        building_name = building_names.get(self.current_building, self.current_building[:50])
        self.canvas.create_text(100, 25, text=f"{building_name} - Этаж {self.current_floor}", 
                               font=('Arial', 14, 'bold'), fill='black', anchor='w')
        
    def draw_entrances(self, scale_point):
        entrances_key = f"{self.current_building}_{self.current_floor}"
        floor_entrances = self.entrances.get(entrances_key, {})
        
        for obj_id, entrance_data in floor_entrances.items():
            if 'x' in entrance_data and 'y' in entrance_data:
                ex, ey = scale_point(entrance_data['x'], entrance_data['y'])
                self.canvas.create_oval(ex-6, ey-6, ex+6, ey+6, 
                                          fill='#00FF00', outline='#006400', width=2,
                                          tags=f'entrance_{obj_id}')
                self.canvas.create_oval(ex-3, ey-3, ex+3, ey+3, 
                                          fill='white', tags=f'entrance_center_{obj_id}')
                
    def on_mouse_move(self, event):
        if not self.current_building or not self.current_floor:
            return
        
        if self.preview_dot:
            self.canvas.delete(self.preview_dot)
            self.preview_dot = None
        
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        map_x = (canvas_x - self.offset_x) / self.scale
        map_y = (canvas_y - self.offset_y) / self.scale
        
        clicked_obj = None
        
        for obj_id, obj_data in self.room_polygons.items():
            if point_in_polygon(map_x, map_y, obj_data['polygon']):
                clicked_obj = obj_data
                clicked_obj['id'] = obj_id
                
                # Проверяем, можно ли ставить входы для этого типа объекта
                if not obj_data.get('can_enter', True):
                    # Техническое помещение - нельзя ставить входы
                    self.current_hover_obj = None
                    self.info_label.config(text=f"⛔ {obj_data['number']} - входы запрещены")
                    self.current_room_label.config(text="")
                    self.coord_label.config(text="")
                    return
                
                self.current_hover_obj = clicked_obj
                
                nearest_x, nearest_y = find_nearest_boundary_point(map_x, map_y, obj_data['polygon'])
                
                if nearest_x is not None:
                    self.nearest_boundary_x = nearest_x
                    self.nearest_boundary_y = nearest_y
                    
                    sx = nearest_x * self.scale + self.offset_x
                    sy = nearest_y * self.scale + self.offset_y
                    
                    self.preview_dot = self.canvas.create_oval(
                        sx-8, sy-8, sx+8, sy+8,
                        fill='white', outline='red', width=2,
                        tags='preview'
                    )
                    
                    self.info_label.config(text=f"Кликните для установки точки входа на контуре")
                    self.current_room_label.config(text=f"{clicked_obj['number']} ({clicked_obj['type']})")
                    self.coord_label.config(text=f"Координаты: ({nearest_x}, {nearest_y})")
                else:
                    self.current_hover_obj = None
                    self.info_label.config(text="Наведите на аудиторию (синюю) или лестницу (красную)")
                    self.current_room_label.config(text="")
                    self.coord_label.config(text="")
                return
        
        self.current_hover_obj = None
        self.nearest_boundary_x = None
        self.nearest_boundary_y = None
        self.info_label.config(text="Наведите на аудиторию (синюю), лестницу (красную) или лифт (жёлтый)")
        self.current_room_label.config(text="")
        self.coord_label.config(text="")
        
    def on_mouse_leave(self, event):
        if self.preview_dot:
            self.canvas.delete(self.preview_dot)
            self.preview_dot = None

    def on_mouse_wheel(self, event):
        """Прокрутка колесиком мыши:
        - Без Shift: вертикальная прокрутка
        - С Shift: горизонтальная прокрутка
        """
        # Определяем направление прокрутки (Windows)
        delta = event.delta
        
        # Проверяем, зажат ли Shift
        if event.state & 0x1:  # Shift нажат
            # Горизонтальная прокрутка
            self.canvas.xview_scroll(int(-1 * (delta / 120)), "units")
        else:
            # Вертикальная прокрутка
            self.canvas.yview_scroll(int(-1 * (delta / 120)), "units")

    def on_canvas_click(self, event):
        if not self.current_hover_obj or self.nearest_boundary_x is None:
            return

        obj_id = self.current_hover_obj['id']
        room_number = self.current_hover_obj['number']
        obj_type = self.current_hover_obj['type']

        # Проверяем, есть ли уже вход для этого объекта
        entrances_key = f"{self.current_building}_{self.current_floor}"
        if entrances_key in self.entrances and obj_id in self.entrances[entrances_key]:
            # Удаляем старый вход перед установкой нового
            del self.entrances[entrances_key][obj_id]

        self.set_entrance(obj_id, self.nearest_boundary_x, self.nearest_boundary_y, room_number, obj_type)

    def set_entrance(self, obj_id, x, y, room_number, obj_type):
        entrances_key = f"{self.current_building}_{self.current_floor}"

        if entrances_key not in self.entrances:
            self.entrances[entrances_key] = {}

        self.entrances[entrances_key][obj_id] = {
            'x': x,
            'y': y,
            'room_number': room_number,
            'type': obj_type
        }

        self.draw_map()

        self.status_label.config(text=f"✓ Вход: {room_number} ({x}, {y})")
        self.info_label.config(text=f"✅ Точка входа установлена на контуре!")
        
    def save_entrances_ui(self):
        save_entrances(self.entrances)
        self.status_label.config(text=f"💾 Входы сохранены в {ENTRANCES_FILE}")
        
    def clear_entrances(self):
        if messagebox.askyesno("Подтверждение", "Удалить все точки входа?"):
            self.entrances = {}
            self.entrance_connections = []
            self.draw_map()
            self.status_label.config(text="🗑️ Все входы удалены")

def main():
    root = tk.Tk()
    app = MapApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
