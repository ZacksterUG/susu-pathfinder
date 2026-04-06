import json
import os
from PIL import Image, ImageDraw, ImageFont

# Создаём папку для карт
os.makedirs('map/full', exist_ok=True)

# Загружаем данные
with open('coordinates.json', 'r', encoding='utf-8') as f:
    coordinates = json.load(f)

with open('rooms.json', 'r', encoding='utf-8') as f:
    rooms = json.load(f)

with open('floors.json', 'r', encoding='utf-8') as f:
    infrastructure = json.load(f)

with open('buildings.json', 'r', encoding='utf-8') as f:
    buildings = json.load(f)

# Словарь названий корпусов
building_names = {b['Id']: b['ShortName'] for b in buildings}

# Выбираем корпус для визуализации (Западное крыло - 5 этажей, много аудиторий)
TARGET_BUILDING = "9c7a0f84-03b0-40b0-8fb0-992e1008c11e"  # Западное крыло

SCALE = 1.0
MARGIN = 50

def get_centroid(points):
    """Вычислить центроид полигона"""
    x_coords = [p['x'] for p in points]
    y_coords = [p['y'] for p in points]
    return sum(x_coords) / len(x_coords), sum(y_coords) / len(y_coords)

def parse_coordinates(coord_str):
    """Парсить JSON строку с координатами"""
    if isinstance(coord_str, str):
        try:
            data = json.loads(coord_str)
            return data.get('points', [])
        except:
            return []
    elif isinstance(coord_str, dict):
        return coord_str.get('points', [])
    return []

for building_id, floors_data in coordinates.items():
    building_name = building_names.get(building_id, building_id[:8])
    
    # Получаем аудитории для этого корпуса
    building_rooms = rooms.get(building_id, [])
    
    # Получаем инфраструктуру (лестницы/лифты)
    building_elevators = infrastructure.get('elevators', {}).get(building_id, [])
    building_stairs = infrastructure.get('stairs', {}).get(building_id, [])
    
    # Объединяем лестницы из elevators (там хранятся все объекты)
    all_infrastructure = building_elevators
    
    for floor, data in floors_data.items():
        # Парсим координаты коридора
        corridor_points = parse_coordinates(data)
        
        if not corridor_points:
            continue
        
        # Находим размеры холста
        min_x = min(p['x'] for p in corridor_points) if corridor_points else 0
        max_x = max(p['x'] for p in corridor_points) if corridor_points else 100
        min_y = min(p['y'] for p in corridor_points) if corridor_points else 0
        max_y = max(p['y'] for p in corridor_points) if corridor_points else 100
        
        width = int((max_x - min_x + 2 * MARGIN) * SCALE)
        height = int((max_y - min_y + 2 * MARGIN) * SCALE)
        
        # Создаём изображение
        img = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(img)
        
        # Смещение для координат
        offset_x = -min_x + MARGIN
        offset_y = -min_y + MARGIN
        
        def scale_point(x, y):
            return (int((x + offset_x) * SCALE), int((y + offset_y) * SCALE))
        
        # 1. Рисуем коридор (серый фон)
        corridor_scaled = [scale_point(p['x'], p['y']) for p in corridor_points]
        draw.polygon(corridor_scaled, fill='#E0E0E0', outline='#808080', width=2)
        
        # 2. Рисуем аудитории (синие прямоугольники)
        floor_rooms = [r for r in building_rooms if str(r.get('Floor', '')) == str(floor)]
        
        for room in floor_rooms:
            room_coords = room.get('Coordinates')
            if room_coords:
                room_points = parse_coordinates(room_coords)
                if room_points:
                    # Вычисляем bounding box
                    rx_coords = [p['x'] for p in room_points]
                    ry_coords = [p['y'] for p in room_points]
                    rx_min, rx_max = min(rx_coords), max(rx_coords)
                    ry_min, ry_max = min(ry_coords), max(ry_coords)
                    
                    # Рисуем прямоугольник
                    p1 = scale_point(rx_min, ry_min)
                    p2 = scale_point(rx_max, ry_max)
                    draw.rectangle([p1, p2], fill='#4169E1', outline='#000080', width=1)
                    
                    # Добавляем номер аудитории
                    room_number = room.get('Number', '?')
                    cx = (p1[0] + p2[0]) // 2
                    cy = (p1[1] + p2[1]) // 2
                    
                    # Определяем размер шрифта
                    font_size = max(10, min(16, (p2[0] - p1[0]) // 4))
                    try:
                        font = ImageFont.truetype("arial.ttf", font_size)
                    except:
                        font = ImageFont.load_default()
                    
                    # Текст с тенью
                    draw.text((cx-1, cy-1), str(room_number), fill='white', font=font, anchor="mm")
                    draw.text((cx+1, cy+1), str(room_number), fill='black', font=font, anchor="mm")
        
        # 3. Рисуем лестницы (красные)
        floor_stairs = [s for s in all_infrastructure 
                       if str(s.get('Floor', '')) == str(floor) 
                       and s.get('InfrastructureObjectType') == 'Лестница']
        
        for stair in floor_stairs:
            stair_points = parse_coordinates(stair.get('Coordinates'))
            if stair_points:
                sx_coords = [p['x'] for p in stair_points]
                sy_coords = [p['y'] for p in stair_points]
                sx_min, sx_max = min(sx_coords), max(sx_coords)
                sy_min, sy_max = min(sy_coords), max(sy_coords)
                
                p1 = scale_point(sx_min, sy_min)
                p2 = scale_point(sx_max, sy_max)
                draw.rectangle([p1, p2], fill='#DC143C', outline='#8B0000', width=1)
        
        # 4. Рисуем лифты (жёлтые) - ищем объекты с "Лифт" в названии типа
        floor_elevators = [e for e in all_infrastructure 
                          if str(e.get('Floor', '')) == str(floor) 
                          and 'Лифт' in e.get('InfrastructureObjectType', '')]
        
        for elevator in floor_elevators:
            elev_points = parse_coordinates(elevator.get('Coordinates'))
            if elev_points:
                ex_coords = [p['x'] for p in elev_points]
                ey_coords = [p['y'] for p in elev_points]
                ex_min, ex_max = min(ex_coords), max(ex_coords)
                ey_min, ey_max = min(ey_coords), max(ey_coords)
                
                p1 = scale_point(ex_min, ey_min)
                p2 = scale_point(ex_max, ey_max)
                draw.rectangle([p1, p2], fill='#FFD700', outline='#B8860B', width=1)
        
        # 5. Добавляем легенду
        legend_y = 10
        legend_x = 10
        
        # Коридор
        draw.rectangle([legend_x, legend_y, legend_x+15, legend_y+15], fill='#E0E0E0', outline='#808080')
        draw.text((legend_x+20, legend_y), "Коридор", fill='black', anchor="lm")
        
        # Аудитория
        legend_y += 20
        draw.rectangle([legend_x, legend_y, legend_x+15, legend_y+15], fill='#4169E1', outline='#000080')
        draw.text((legend_x+20, legend_y), "Аудитория", fill='black', anchor="lm")
        
        # Лестница
        legend_y += 20
        draw.rectangle([legend_x, legend_y, legend_x+15, legend_y+15], fill='#DC143C', outline='#8B0000')
        draw.text((legend_x+20, legend_y), "Лестница", fill='black', anchor="lm")
        
        # Лифт
        legend_y += 20
        draw.rectangle([legend_x, legend_y, legend_x+15, legend_y+15], fill='#FFD700', outline='#B8860B')
        draw.text((legend_x+20, legend_y), "Лифт", fill='black', anchor="lm")
        
        # Заголовок
        title = f"{building_name} - Этаж {floor}"
        try:
            title_font = ImageFont.truetype("arial.ttf", 16)
        except:
            title_font = ImageFont.load_default()
        draw.text((width//2, 10), title, fill='black', font=title_font, anchor="mt")
        
        # Сохраняем
        short_id = building_id[:8]
        filename = f"map/full/{building_name}_{short_id}_floor{floor}_full.png"
        img.save(filename)
        print(f"✓ {filename} (аудиторий: {len(floor_rooms)}, лестниц: {len(floor_stairs)})")

print("\n=== Готово! ===")
print(f"Изображения сохранены в папку 'map/full/'")
