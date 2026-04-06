"""
Окно построения маршрута между аудиториями.
Визуализация карты, выбор start/end, отображение пути.
"""

import json
import tkinter as tk
from tkinter import ttk, messagebox
import math

from .finder import MultiFloorPathFinder


def parse_coordinates(coord_str):
    """Распарсить JSON координат полигона"""
    if isinstance(coord_str, str):
        try:
            data = json.loads(coord_str)
            return data.get('points', [])
        except:
            return []
    elif isinstance(coord_str, dict):
        return coord_str.get('points', [])
    return []


def open_pathfinder_window(parent, rooms_data, coordinates_data, floors_data,
                           grid_data, entrances_data, building_id, building_name,
                           network_manager=None):
    """
    Открыть окно построения пути

    Args:
        parent: родительское окно
        rooms_data: данные об аудиториях (rooms.json)
        coordinates_data: координаты коридоров (coordinates.json)
        floors_data: лифты/лестницы (floors.json)
        grid_data: сетки (grid.json)
        entrances_data: точки входа (entrances.json)
        building_id: ID корпуса
        building_name: название корпуса
        network_manager: менеджер сетей (опционально)
    """
    win = tk.Toplevel(parent)
    win.title(f"Построение пути — {building_name}")
    win.geometry("1600x1000")
    win.state('zoomed')  # Открыть на весь экран
    win.transient(parent)

    # Состояние
    state = {
        'start_room': None,
        'end_room': None,
        'start_floor': None,
        'end_floor': None,
        'current_path': None,
        'path_length': 0,
        'path_floors': [],  # этажи, через которые проходит путь
        'floor_transitions': [],  # [(from_floor, to_floor), ...]
    }

    # ===== Парсинг данных =====
    def get_building_rooms():
        """Получить все аудитории корпуса, сгруппированные по этажам"""
        building_rooms = rooms_data.get(building_id, [])
        floors = {}
        for room in building_rooms:
            floor = str(room.get('Floor', ''))
            if floor not in floors:
                floors[floor] = []
            floors[floor].append(room)
        # Сортируем по номеру
        for floor in floors:
            floors[floor].sort(key=lambda r: str(r.get('Number', '')))
        return floors

    def get_room_entrance(room_number, floor):
        """Найти точку входа для аудитории"""
        entrances_key = f"{building_id}_{floor}"
        floor_entrances = entrances_data.get(entrances_key, {})
        for obj_id, entrance_data in floor_entrances.items():
            if entrance_data.get('room_number') == room_number:
                return (entrance_data['x'], entrance_data['y'])
        return None

    def get_grid_for_floor(floor):
        """Получить сетку для этажа"""
        grid_key = f"{building_id}_{floor}"
        return grid_data.get(grid_key)

    def get_floor_objects(floor, obj_type):
        """Получить лифты/лестницы на этаже"""
        if building_id not in floors_data.get('elevators', {}):
            return []
        objects = floors_data['elevators'][building_id]
        result = []
        for obj in objects:
            obj_floor = str(obj.get('Floor', ''))
            obj_type_str = obj.get('InfrastructureObjectType', '')
            if obj_floor == floor:
                if obj_type == 'elevator' and 'Лифт' in obj_type_str:
                    result.append(obj)
                elif obj_type == 'stairs' and 'Лестница' in obj_type_str:
                    result.append(obj)
        return result

    def get_corridor_points(floor):
        """Получить координаты коридора для этажа"""
        building_coords = coordinates_data.get(building_id, {})
        floor_data = building_coords.get(floor, {})
        if isinstance(floor_data, dict):
            coords = floor_data.get('points', [])
            if coords:
                return coords
        return []

    # ===== Верхняя панель =====
    top_frame = ttk.Frame(win, padding="10")
    top_frame.pack(side=tk.TOP, fill=tk.X)

    ttk.Label(top_frame, text=f"🏢 {building_name}", font=("Arial", 14, "bold")).pack(side=tk.LEFT, padx=5)

    status_var = tk.StringVar(value="Выберите аудитории отправления и назначения")
    ttk.Label(top_frame, textvariable=status_var, foreground="blue", font=("Arial", 10)).pack(side=tk.RIGHT, padx=10)

    # Выбор аудиторий
    select_frame = ttk.Frame(win, padding="10")
    select_frame.pack(side=tk.TOP, fill=tk.X)

    # Откуда
    ttk.Label(select_frame, text="От:", font=("Arial", 11, "bold")).pack(side=tk.LEFT, padx=5)
    start_var = tk.StringVar()
    start_combo = ttk.Combobox(select_frame, textvariable=start_var, width=30)
    start_combo.pack(side=tk.LEFT, padx=5)

    # Куда
    ttk.Label(select_frame, text="До:", font=("Arial", 11, "bold")).pack(side=tk.LEFT, padx=(20, 5))
    end_var = tk.StringVar()
    end_combo = ttk.Combobox(select_frame, textvariable=end_var, width=30)
    end_combo.pack(side=tk.LEFT, padx=5)

    def on_selection_change(*args):
        start_text = start_var.get()
        end_text = end_var.get()
        if start_text:
            for floor, rooms in all_rooms.items():
                for room in rooms:
                    if str(room.get('Number', '')) == start_text:
                        state['start_room'] = start_text
                        state['start_floor'] = floor
                        break
        if end_text:
            for floor, rooms in all_rooms.items():
                for room in rooms:
                    if str(room.get('Number', '')) == end_text:
                        state['end_room'] = end_text
                        state['end_floor'] = floor
                        break

    start_var.trace_add('write', on_selection_change)
    end_var.trace_add('write', on_selection_change)

    # Кнопки
    btn_frame = ttk.Frame(select_frame)
    btn_frame.pack(side=tk.LEFT, padx=20)

    def build_path():
        if not state['start_room'] or not state['end_room']:
            messagebox.showwarning("Ошибка", "Выберите аудитории отправления и назначения")
            return
        if state['start_room'] == state['end_room']:
            messagebox.showinfo("Инфо", "Аудитории совпадают")
            return

        start_entrance = get_room_entrance(state['start_room'], state['start_floor'])
        end_entrance = get_room_entrance(state['end_room'], state['end_floor'])

        if not start_entrance:
            messagebox.showwarning("Ошибка", f"Нет точки входа для аудитории {state['start_room']}")
            return
        if not end_entrance:
            messagebox.showwarning("Ошибка", f"Нет точки входа для аудитории {state['end_room']}")
            return

        # Создаём межэтажный поиск пути
        pathfinder = MultiFloorPathFinder(
            grid_data,
            building_id,
            network_manager,
            floors_data  # Передаём данные о лифтах/лестницах
        )

        # Формируем ключи этажей в формате grid_data
        start_floor_key = f"{building_id}_{state['start_floor']}"
        end_floor_key = f"{building_id}_{state['end_floor']}"

        result = pathfinder.find_path(
            start_floor_key, start_entrance[0], start_entrance[1],
            end_floor_key, end_entrance[0], end_entrance[1]
        )

        if result['found']:
            state['current_path'] = result['path']
            state['path_length'] = result['total_length']
            state['path_floors'] = list(result['path'].keys())
            state['floor_transitions'] = result['floor_transitions']

            # Формируем описание маршрута
            route_desc = f"✅ Маршрут построен\n\n"
            route_desc += f"От: {state['start_room']} (этаж {state['start_floor']})\n"
            route_desc += f"До: {state['end_room']} (этаж {state['end_floor']})\n\n"
            route_desc += f"Длина: {result['total_length']:.1f}\n\n"

            if result['floor_transitions']:
                route_desc += f"🔄 Переходы между этажами:\n"
                for from_f, to_f in result['floor_transitions']:
                    route_desc += f"  Этаж {from_f} → Этаж {to_f}\n"
                route_desc += "\n"

            route_desc += f"📍 Этажи маршрута: {', '.join(sorted(state['path_floors'], key=lambda x: int(x) if x.isdigit() else 999))}"

            route_text.delete('1.0', tk.END)
            route_text.insert(tk.END, route_desc)

            status_var.set(f"🛣️ Путь: {state['start_room']} → {state['end_room']}, длина: {result['total_length']:.1f}")
            draw_all_floors()
        else:
            messagebox.showwarning("Ошибка", "Путь не найден. Проверьте наличие сетки на этажах и связей между этажами.")

    def clear_path():
        state['current_path'] = None
        state['path_length'] = 0
        state['path_floors'] = []
        state['floor_transitions'] = []
        state['start_room'] = None
        state['end_room'] = None
        start_var.set('')
        end_var.set('')
        status_var.set("Путь сброшен")
        draw_all_floors()

    ttk.Button(btn_frame, text="🔍 Построить путь", command=build_path).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text="❌ Сбросить", command=clear_path).pack(side=tk.LEFT, padx=5)

    ttk.Separator(win, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=5)

    # ===== Основная область =====
    main_container = ttk.Frame(win)
    main_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)

    # Карта этажей
    map_frame = ttk.LabelFrame(main_container, text="Карта этажей с маршрутом", padding="5")
    map_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

    floors_canvas = tk.Canvas(map_frame, bg='#f5f5f5')
    floors_scrollbar_v = ttk.Scrollbar(map_frame, orient="vertical", command=floors_canvas.yview)
    floors_scrollbar_h = ttk.Scrollbar(map_frame, orient="horizontal", command=floors_canvas.xview)
    floors_scrollable = ttk.Frame(floors_canvas)

    floors_scrollable.bind("<Configure>", lambda e: floors_canvas.configure(scrollregion=floors_canvas.bbox("all")))
    floors_canvas.create_window((0, 0), window=floors_scrollable, anchor="nw")
    floors_canvas.configure(yscrollcommand=floors_scrollbar_v.set, xscrollcommand=floors_scrollbar_h.set)

    floors_scrollbar_v.pack(side=tk.RIGHT, fill=tk.Y)
    floors_scrollbar_h.pack(side=tk.BOTTOM, fill=tk.X)
    floors_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Информация о пути справа
    info_frame = ttk.LabelFrame(main_container, text="Информация о пути", padding="10")
    info_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(5, 0))
    info_frame.configure(width=300)

    ttk.Label(info_frame, text="Маршрут:", font=("Arial", 11, "bold")).pack(anchor=tk.W, pady=(0, 5))

    route_text = tk.Text(info_frame, height=20, width=35, font=("Courier", 9), wrap=tk.WORD)
    route_text.pack(fill=tk.BOTH, expand=True, pady=5)

    # Заполняем комбобоксы
    all_rooms = get_building_rooms()
    all_room_numbers = []
    for floor, rooms in all_rooms.items():
        all_room_numbers.extend([str(r.get('Number', '')) for r in rooms])

    start_combo['values'] = all_room_numbers
    end_combo['values'] = all_room_numbers
    if all_room_numbers:
        start_combo.current(0)
        end_combo.current(min(1, len(all_room_numbers) - 1))

    # ===== Рисование карты =====
    MARGIN = 30
    MAP_SCALE = 2.0  # Масштаб карты

    def draw_all_floors():
        """Нарисовать все этажи с путём"""
        for w in floors_scrollable.winfo_children():
            w.destroy()

        floors = sorted(all_rooms.keys(), key=lambda x: int(x) if x.isdigit() else 999)
        if not floors:
            tk.Label(floors_scrollable, text="Нет данных", font=("Arial", 14), fg="red", bg='#f5f5f5').pack(pady=100)
            return

        # Обновляем информацию о пути
        route_text.delete('1.0', tk.END)
        if state['current_path']:
            route_text.insert(tk.END, f"✅ Маршрут построен\n\n")
            route_text.insert(tk.END, f"От: {state['start_room']}\n")
            route_text.insert(tk.END, f"До: {state['end_room']}\n\n")
            route_text.insert(tk.END, f"Длина: {state['path_length']:.1f}\n\n")
            route_text.insert(tk.END, f"Этажи: {', '.join(state['path_floors'])}")
        else:
            route_text.insert(tk.END, "Выберите аудитории\nи нажмите 'Построить путь'")

        for floor in floors:
            floor_container = ttk.LabelFrame(floors_scrollable, text=f"Этаж {floor}", padding="5")
            floor_container.pack(fill=tk.X, pady=10, padx=10)

            # Собираем все точки
            all_points = []
            corridor = get_corridor_points(floor)
            all_points.extend(corridor)

            building_rooms = all_rooms.get(floor, [])
            for room in building_rooms:
                coords = parse_coordinates(room.get('Coordinates'))
                all_points.extend(coords)

            elevators = get_floor_objects(floor, 'elevator')
            stairs = get_floor_objects(floor, 'stairs')
            for obj in elevators + stairs:
                coords = parse_coordinates(obj.get('Coordinates'))
                all_points.extend(coords)

            if not all_points:
                tk.Label(floor_container, text="Нет данных", fg="gray", bg='white').pack(pady=20)
                continue

            min_x = min(p['x'] for p in all_points) - MARGIN
            max_x = max(p['x'] for p in all_points) + MARGIN
            min_y = min(p['y'] for p in all_points) - MARGIN
            max_y = max(p['y'] for p in all_points) + MARGIN

            canvas_w = int((max_x - min_x) * MAP_SCALE)
            canvas_h = int((max_y - min_y) * MAP_SCALE)

            canvas = tk.Canvas(floor_container, width=canvas_w, height=canvas_h, bg='white',
                              highlightthickness=1, highlightbackground='#ccc')
            canvas.pack(pady=5)

            # Коридор
            if corridor:
                poly_points = [((p['x'] - min_x) * MAP_SCALE, (p['y'] - min_y) * MAP_SCALE) for p in corridor]
                flat = [c for p in poly_points for c in p]
                canvas.create_polygon(flat, fill='#E0E0E0', outline='#808080', width=2)

            # Аудитории
            for room in building_rooms:
                coords = parse_coordinates(room.get('Coordinates'))
                if coords:
                    room_number = str(room.get('Number', ''))
                    poly_points = [((p['x'] - min_x) * MAP_SCALE, (p['y'] - min_y) * MAP_SCALE) for p in coords]
                    flat = [c for p in poly_points for c in p]

                    # Подсветка start/end
                    if room_number == state['start_room']:
                        fill_color = '#00FF00'
                        outline_color = '#006400'
                    elif room_number == state['end_room']:
                        fill_color = '#FF4500'
                        outline_color = '#8B0000'
                    else:
                        fill_color = '#4169E1'
                        outline_color = '#000080'

                    canvas.create_polygon(flat, fill=fill_color, outline=outline_color, width=2)
                    cx = sum(p[0] for p in poly_points) / len(poly_points)
                    cy = sum(p[1] for p in poly_points) / len(poly_points)
                    canvas.create_text(cx, cy, text=room_number, fill='white', font=("Arial", 11, "bold"))

            # Лифты
            for elev in elevators:
                coords = parse_coordinates(elev.get('Coordinates'))
                if coords:
                    poly_points = [((p['x'] - min_x) * MAP_SCALE, (p['y'] - min_y) * MAP_SCALE) for p in coords]
                    flat = [c for p in poly_points for c in p]
                    canvas.create_polygon(flat, fill='#FFD700', outline='#B8860B', width=2)
                    cx = sum(p[0] for p in poly_points) / len(poly_points)
                    cy = sum(p[1] for p in poly_points) / len(poly_points)
                    canvas.create_text(cx, cy, text=elev.get('Name', 'Лифт'), fill='black', font=("Arial", 10, "bold"))

            # Лестницы
            for stair in stairs:
                coords = parse_coordinates(stair.get('Coordinates'))
                if coords:
                    poly_points = [((p['x'] - min_x) * MAP_SCALE, (p['y'] - min_y) * MAP_SCALE) for p in coords]
                    flat = [c for p in poly_points for c in p]
                    canvas.create_polygon(flat, fill='#DC143C', outline='#8B0000', width=2)
                    cx = sum(p[0] for p in poly_points) / len(poly_points)
                    cy = sum(p[1] for p in poly_points) / len(poly_points)
                    canvas.create_text(cx, cy, text=stair.get('Name', 'Лестница'), fill='white', font=("Arial", 10, "bold"))

            # Путь — ключи в result['path'] теперь номера этажей, не полные ключи
            if state['current_path'] and floor in state['current_path']:
                grid = get_grid_for_floor(floor)
                if grid:
                    nodes = grid.get('nodes', [])
                    path = state['current_path'][floor]
                    path_coords = []
                    for local_idx in path:
                        if local_idx < len(nodes):
                            node = nodes[local_idx]
                            path_coords.extend([(node['x'] - min_x) * MAP_SCALE, (node['y'] - min_y) * MAP_SCALE])
                    if len(path_coords) >= 4:
                        canvas.create_line(path_coords, fill='#FF4500', width=12, capstyle=tk.ROUND, joinstyle=tk.ROUND)

    # Колесико мыши
    def on_mouse_wheel(event):
        if event.state & 0x1:  # Shift нажат — горизонтальная прокрутка
            floors_canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")
        else:
            floors_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    floors_canvas.bind('<MouseWheel>', on_mouse_wheel)

    # Инициализация
    draw_all_floors()
    status_var.set(f"🏢 {building_name} — выберите аудитории для построения пути")
