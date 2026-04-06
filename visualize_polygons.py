import json
import os
from PIL import Image, ImageDraw

# Создаём папку для карт
os.makedirs('map', exist_ok=True)

# Загружаем данные
with open('coordinates.json', 'r', encoding='utf-8') as f:
    coordinates = json.load(f)

with open('buildings.json', 'r', encoding='utf-8') as f:
    buildings = json.load(f)

# Словарь названий корпусов
building_names = {b['Id']: b['ShortName'] for b in buildings}

# Масштаб для отрисовки (увеличим для наглядности)
SCALE = 1.5
MARGIN = 50

for building_id, floors in coordinates.items():
    building_name = building_names.get(building_id, building_id[:8])
    
    for floor, data in floors.items():
        # Парсим JSON строку с точками
        if isinstance(data, str):
            data = json.loads(data)
        
        points_str = data.get('points', [])
        
        if not points_str:
            continue
        
        # Преобразуем координаты
        points = [(p['x'], p['y']) for p in points_str]
        
        # Находим размеры для определения размера холста
        min_x = min(p[0] for p in points)
        max_x = max(p[0] for p in points)
        min_y = min(p[1] for p in points)
        max_y = max(p[1] for p in points)
        
        width = int((max_x - min_x + 2 * MARGIN) * SCALE)
        height = int((max_y - min_y + 2 * MARGIN) * SCALE)
        
        # Создаём изображение
        img = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(img)
        
        # Смещаем точки
        offset_x = -min_x + MARGIN
        offset_y = -min_y + MARGIN
        scaled_points = [(int((x + offset_x) * SCALE), int((y + offset_y) * SCALE)) for x, y in points]
        
        # Рисуем полигон коридора
        draw.polygon(scaled_points, fill='#ADD8E6', outline='#000080', width=2)
        
        # Рисуем вершины
        for px, py in scaled_points:
            draw.ellipse([px-3, py-3, px+3, py+3], fill='red')
        
        # Добавляем подпись
        label = f"{building_name} - Этаж {floor}"
        draw.text((10, 10), label, fill='black')
        
        # Сохраняем (с ID для уникальности)
        short_id = building_id[:8]
        filename = f"map/{building_name}_{short_id}_floor{floor}.png"
        img.save(filename)
        print(f"✓ {filename}")

print("\n=== Готово! ===")
print(f"Изображения сохранены в папку 'map/'")
