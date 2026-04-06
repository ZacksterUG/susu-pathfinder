"""
Окно управления сетями лифтов и лестниц.
Отрисовка визуальной карты корпуса с полигонами лифтов/лестниц.
"""

import json
import tkinter as tk
from tkinter import ttk, messagebox


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


def open_network_window(parent, floors_data, building_id, building_name, network_manager):
    """Открыть окно управления сетями"""
    win = tk.Toplevel(parent)
    win.title(f"Сети лифтов и лестниц — {building_name}")
    win.geometry("1600x1000")
    win.state('zoomed')  # Открыть на весь экран
    win.transient(parent)

    # Состояние
    state = {
        'creating_network': False,
        'network_type': None,  # 'elevator' или 'stairs'
        'selected_objects': [],  # [(obj_id, floor, obj_type), ...]
    }

    # ===== Парсинг данных =====
    def get_building_floors():
        if building_id not in floors_data.get('elevators', {}):
            return []
        objects = floors_data['elevators'][building_id]
        floors = set()
        for obj in objects:
            floors.add(str(obj.get('Floor', '')))
        return sorted(floors, key=lambda x: int(x) if x.isdigit() else 999)

    def get_floor_objects(floor, obj_type):
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

    # ===== Верхняя панель =====
    top_frame = ttk.Frame(win, padding="10")
    top_frame.pack(side=tk.TOP, fill=tk.X)

    ttk.Label(top_frame, text=f"🏢 {building_name}", font=("Arial", 14, "bold")).pack(side=tk.LEFT, padx=5)

    status_var = tk.StringVar(value="Выберите действие")
    ttk.Label(top_frame, textvariable=status_var, foreground="blue", font=("Arial", 10)).pack(side=tk.RIGHT, padx=10)

    # Кнопки
    ctrl_frame = ttk.Frame(win, padding="10")
    ctrl_frame.pack(side=tk.TOP, fill=tk.X)

    def start_network(net_type):
        state['creating_network'] = True
        state['network_type'] = net_type
        state['selected_objects'] = []
        btn_save.config(state=tk.NORMAL)
        btn_cancel.config(state=tk.NORMAL)
        btn_create_elev.config(state=tk.DISABLED)
        btn_create_stairs.config(state=tk.DISABLED)
        type_name = "лифтов" if net_type == 'elevator' else "лестниц"
        status_var.set(f"🔵 КЛИКАЙТЕ на объекты ({type_name}) на карте для выбора")
        info_var.set(f"Кликайте на {type_name} на этажах → зелёная подсветка = выбран → 'Сохранить сеть'")
        draw_all_floors()

    def cancel_network():
        state['creating_network'] = False
        state['network_type'] = None
        state['selected_objects'] = []
        btn_save.config(state=tk.DISABLED)
        btn_cancel.config(state=tk.DISABLED)
        btn_create_elev.config(state=tk.NORMAL)
        btn_create_stairs.config(state=tk.NORMAL)
        status_var.set("Выбор отменен")
        info_var.set("Выберите действие")
        draw_all_floors()

    def save_network():
        if len(state['selected_objects']) < 2:
            messagebox.showwarning("Ошибка", "Нужно минимум 2 объекта для сети")
            return
        objects = [(obj_id, floor) for obj_id, floor, _ in state['selected_objects']]
        network_manager.create_network(building_id, state['network_type'], objects)
        type_name = "лифтов" if state['network_type'] == 'elevator' else "лестниц"
        messagebox.showinfo("Успех", f"Сеть {type_name} из {len(objects)} объектов сохранена")
        cancel_network()
        draw_all_floors()
        refresh_networks()

    btn_create_elev = ttk.Button(ctrl_frame, text="🛗 Создать сеть лифтов", command=lambda: start_network('elevator'))
    btn_create_elev.pack(side=tk.LEFT, padx=5)

    btn_create_stairs = ttk.Button(ctrl_frame, text="🪜 Создать сеть лестниц", command=lambda: start_network('stairs'))
    btn_create_stairs.pack(side=tk.LEFT, padx=5)

    btn_save = ttk.Button(ctrl_frame, text="💾 Сохранить сеть", command=save_network, state=tk.DISABLED)
    btn_save.pack(side=tk.LEFT, padx=5)

    btn_cancel = ttk.Button(ctrl_frame, text="❌ Отменить", command=cancel_network, state=tk.DISABLED)
    btn_cancel.pack(side=tk.LEFT, padx=5)

    ttk.Separator(win, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=5)

    # ===== Основная область =====
    main_container = ttk.Frame(win)
    main_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)

    # Левая часть — Canvas с этажами
    left_frame = ttk.LabelFrame(main_container, text="Карта этажей", padding="5")
    left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

    floors_canvas = tk.Canvas(left_frame, bg='#f5f5f5')
    floors_scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=floors_canvas.yview)
    floors_scrollable = ttk.Frame(floors_canvas)

    floors_scrollable.bind("<Configure>", lambda e: floors_canvas.configure(scrollregion=floors_canvas.bbox("all")))
    floors_canvas.create_window((0, 0), window=floors_scrollable, anchor="nw")
    floors_canvas.configure(yscrollcommand=floors_scrollbar.set)
    floors_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    floors_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Правая часть — сети
    right_frame = ttk.LabelFrame(main_container, text="Созданные сети", padding="10")
    right_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(5, 0))
    right_frame.configure(width=350)

    networks_canvas = tk.Canvas(right_frame, bg='white')
    networks_scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=networks_canvas.yview)
    networks_scrollable = ttk.Frame(networks_canvas)

    networks_scrollable.bind("<Configure>", lambda e: networks_canvas.configure(scrollregion=networks_canvas.bbox("all")))
    networks_canvas.create_window((0, 0), window=networks_scrollable, anchor="nw")
    networks_canvas.configure(yscrollcommand=networks_scrollbar.set)
    networks_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    networks_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Инфо внизу
    info_var = tk.StringVar(value="Кликайте на лифты/лестницы на карте для объединения в сеть")
    ttk.Label(win, textvariable=info_var, font=("Arial", 10), foreground="gray").pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)

    # ===== Рисование карты =====
    FLOOR_HEIGHT = 400
    MARGIN = 30

    def draw_all_floors():
        """Нарисовать все этажи с полигонами"""
        for w in floors_scrollable.winfo_children():
            w.destroy()

        floors = get_building_floors()
        if not floors:
            tk.Label(floors_scrollable, text="Нет данных", font=("Arial", 14), foreground="red", bg='#f5f5f5').pack(pady=100)
            return

        for floor_idx, floor in enumerate(floors):
            floor_container = ttk.LabelFrame(floors_scrollable, text=f"Этаж {floor}", padding="5")
            floor_container.pack(fill=tk.X, pady=10, padx=10)

            elevators = get_floor_objects(floor, 'elevator')
            stairs = get_floor_objects(floor, 'stairs')

            # Определяем размер canvas
            all_points = []
            for obj in elevators + stairs:
                coords = parse_coordinates(obj.get('Coordinates'))
                all_points.extend(coords)

            if not all_points:
                tk.Label(floor_container, text="Нет объектов на этаже", fg="gray", bg='white').pack(pady=20)
                continue

            min_x = min(p['x'] for p in all_points) - MARGIN
            max_x = max(p['x'] for p in all_points) + MARGIN
            min_y = min(p['y'] for p in all_points) - MARGIN
            max_y = max(p['y'] for p in all_points) + MARGIN

            canvas_w = max_x - min_x
            canvas_h = max_y - min_y

            canvas = tk.Canvas(floor_container, width=canvas_w, height=canvas_h, bg='white', highlightthickness=1, highlightbackground='#ccc')
            canvas.pack(pady=5)

            # Рисуем лифты
            for elev in elevators:
                _draw_object(canvas, elev, 'elevator', floor, min_x, min_y)

            # Рисуем лестницы
            for stair in stairs:
                _draw_object(canvas, stair, 'stairs', floor, min_x, min_y)

    def _draw_object(canvas, obj, obj_type, floor, min_x, min_y):
        """Нарисовать один объект на canvas"""
        coords = parse_coordinates(obj.get('Coordinates'))
        if not coords:
            return

        obj_id = obj.get('Id', '')
        obj_name = obj.get('Name', '')

        # Цвета
        if obj_type == 'elevator':
            fill_color = '#FFD700'
            outline_color = '#B8860B'
            select_color = '#00FF00'
        else:
            fill_color = '#DC143C'
            outline_color = '#8B0000'
            select_color = '#00FF00'

        # Проверяем, выбран ли объект
        is_selected = any(oid == obj_id for oid, fl, _ in state['selected_objects'])
        if is_selected:
            fill_color = select_color

        # Рисуем полигон
        poly_points = [(p['x'] - min_x, p['y'] - min_y) for p in coords]
        flat_points = [coord for p in poly_points for coord in p]

        poly_id = canvas.create_polygon(flat_points, fill=fill_color, outline=outline_color, width=2)

        # Подпись в центре
        cx = sum(p[0] for p in poly_points) / len(poly_points)
        cy = sum(p[1] for p in poly_points) / len(poly_points)
        text_id = canvas.create_text(cx, cy, text=f"{obj_name}\n{obj_id[:8]}", fill='black', font=("Arial", 9, "bold"))

        # Проверяем сети
        obj_networks = network_manager.get_object_networks(building_id, obj_id)
        if obj_networks:
            connected_count = len(obj_networks[0]['connected_ids'])
            canvas.create_text(cx, cy + 25, text=f"🔗 {connected_count} связей", fill='green', font=("Arial", 8, "bold"))

        # Клик по объекту
        def on_canvas_click(event, oid=obj_id, otype=obj_type, fl=floor):
            if not state['creating_network']:
                return
            if otype != state['network_type']:
                type_name = "лифты" if state['network_type'] == 'elevator' else "лестницы"
                messagebox.showwarning("Ошибка", f"Можно выбирать только {type_name}")
                return

            # Переключаем выбор
            found = None
            for i, (sid, sfl, stype) in enumerate(state['selected_objects']):
                if sid == oid:
                    found = i
                    break

            if found is not None:
                state['selected_objects'].pop(found)
            else:
                state['selected_objects'].append((oid, fl, otype))

            count = len(state['selected_objects'])
            type_name = "лифтов" if state['network_type'] == 'elevator' else "лестниц"
            status_var.set(f"Выбрано {count} {type_name}")
            draw_all_floors()

        canvas.tag_bind(poly_id, '<Button-1>', on_canvas_click)
        canvas.tag_bind(text_id, '<Button-1>', on_canvas_click)
        canvas.config(cursor='hand2')

    def refresh_networks():
        """Перерисовать список сетей"""
        for w in networks_scrollable.winfo_children():
            w.destroy()

        networks = network_manager.get_building_networks(building_id)
        if not networks:
            tk.Label(networks_scrollable, text="Нет созданных сетей", font=("Arial", 10), foreground="gray", bg='white').pack(pady=20)
            return

        for idx, network in enumerate(networks, 1):
            net_frame = ttk.LabelFrame(networks_scrollable, text=f"Сеть #{idx}", padding="10")
            net_frame.pack(fill=tk.X, pady=5, padx=5)

            net_type = network.get('type', '')
            type_icon = "🛗" if net_type == 'elevator' else "🪜"
            type_name = "Лифты" if net_type == 'elevator' else "Лестницы"

            tk.Label(net_frame, text=f"{type_icon} {type_name}", font=("Arial", 10, "bold"), foreground="green", bg='white').pack(anchor=tk.W, pady=(0, 5))

            objects = network.get('objects', [])
            for obj in objects:
                obj_id = obj.get('id', '')
                obj_floor = obj.get('floor', '')
                connected = [o['id'] for o in objects if o['id'] != obj_id]

                tk.Label(net_frame, text=f"  • Этаж {obj_floor}: {obj_id[:12]}...", font=("Courier", 8), bg='white').pack(anchor=tk.W)
                tk.Label(net_frame, text=f"    Связи: {len(connected)} объект(ов)", font=("Arial", 7), foreground="blue", bg='white').pack(anchor=tk.W)

            btn_frame = ttk.Frame(net_frame)
            btn_frame.pack(fill=tk.X, pady=(5, 0))

            def delete_handler(network_idx=idx - 1):
                if messagebox.askyesno("Подтверждение", "Удалить эту сеть?"):
                    network_manager.delete_network(building_id, network_idx)
                    draw_all_floors()
                    refresh_networks()
                    status_var.set("✓ Сеть удалена")

            ttk.Button(btn_frame, text="🗑️ Удалить", command=delete_handler, width=12).pack(side=tk.LEFT, padx=2)

    # Колесико мыши
    floors_canvas.bind('<MouseWheel>', lambda e: floors_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))
    networks_canvas.bind('<MouseWheel>', lambda e: networks_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

    # Инициализация
    draw_all_floors()
    refresh_networks()
    status_var.set(f"🏢 {building_name} — этажей: {len(get_building_floors())}")
