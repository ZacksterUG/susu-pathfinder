#!/usr/bin/env python3
"""
Генератор SQL-миграции для переноса данных из coordinates.json в таблицу map_app.floor
Запуск: python generate_floors_migration.py
"""

import json
import uuid
from pathlib import Path


def load_coordinates(json_path: str) -> dict:
    """Загрузить данные из coordinates.json"""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_floor_uuid(building_id: str, floor_number: str) -> str:
    """
    Генерирует детерминированный UUID на основе building_id и floor_number
    Использует namespace UUID для создания уникального но повторяемого ID
    """
    namespace = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')  # DNS namespace
    name = f"{building_id}-floor-{floor_number}"
    return str(uuid.uuid5(namespace, name))


def generate_insert_sql(coordinates: dict) -> str:
    """
    Сгенерировать SQL INSERT для таблицы floor
    
    Структура JSON для corridor_points:
    {
        "points": [
            {"x": <int>, "y": <int>},
            {"x": <int>, "y": <int>},
            ...
        ]
    }
    
    где:
    - points: массив точек полигона коридора
    - x, y: координаты точки в пикселях относительно начала этажа
    """
    sql_lines = [
        "-- Миграция: перенос данных из coordinates.json в map_app.floor",
        "-- Сгенерировано автоматически",
        "",
        "-- Структура JSON для corridor_points:",
        "-- {",
        "--   \"points\": [",
        "--     {\"x\": <int>, \"y\": <int>},",
        "--     {\"x\": <int>, \"y\": <int>},",
        "--     ...",
        "--   ]",
        "-- }",
        "-- где points - массив точек полигона коридора,",
        "-- x, y - координаты точки в пикселях относительно начала этажа",
        "",
        "INSERT INTO map_app.floor (id, building_id, floor_number, corridor_points) VALUES"
    ]
    
    values = []
    
    for building_id, floors in coordinates.items():
        for floor_number, corridor_data in floors.items():
            # Генерируем валидный UUID на основе building_id и floor_number
            floor_id = generate_floor_uuid(building_id, floor_number)
            
            # Экранируем одинарные кавычки в JSON
            corridor_json = corridor_data.replace("'", "''")
            
            values.append(
                f"    ('{floor_id}', '{building_id}', '{floor_number}', '{corridor_json}'::jsonb)"
            )
    
    sql_lines.append(',\n'.join(values))
    sql_lines.append(";")
    
    return '\n'.join(sql_lines)


def main():
    # Пути относительно корня проекта
    root_dir = Path(__file__).parent
    coordinates_json = root_dir / 'entrance_app' / 'coordinates.json'
    output_sql = root_dir / 'app' / 'database' / 'data' / 'floors.sql'
    
    # Загрузка данных
    print(f"📖 Чтение {coordinates_json}...")
    coordinates = load_coordinates(str(coordinates_json))
    
    # Подсчёт этажей
    total_floors = sum(len(floors) for floors in coordinates.values())
    print(f"✅ Загружено {len(coordinates)} корпусов, {total_floors} этажей")
    
    # Генерация SQL
    sql = generate_insert_sql(coordinates)
    
    # Сохранение
    output_sql.parent.mkdir(parents=True, exist_ok=True)
    output_sql.write_text(sql, encoding='utf-8')
    print(f"💾 SQL сохранён в {output_sql}")
    
    # Вывод статистики
    print("\n📊 Этажи по корпусам:")
    for building_id, floors in coordinates.items():
        floor_nums = sorted(floors.keys(), key=int)
        print(f"   - {building_id[:8]}...: этажи {', '.join(floor_nums)}")
    
    print("\n✅ Миграция сгенерирована!")


if __name__ == '__main__':
    main()
