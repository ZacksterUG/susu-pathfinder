#!/usr/bin/env python3
"""
Генератор SQL-миграции для переноса данных из rooms.json в map_app.room

Поля rooms.json:
  - Id: UUID комнаты
  - Number: номер комнаты (обязательное)
  - Name: название (может быть null)
  - RoomType: тип (Учебная аудитория, Учебная лаборатория, и т.д.)
  - Floor: номер этажа
  - Coordinates: JSON-строка с полигоном или null

Запуск: python generate_rooms_migration.py
"""

import json
from pathlib import Path


def load_json(file_path: str):
    """Загрузить JSON-файл"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def format_coordinates(coord) -> str:
    """
    Преобразовать координаты в JSONB-совместимый формат.
    Может быть null или строкой с JSON.
    """
    if coord is None:
        return "NULL"
    # Экранируем одинарные кавычки для SQL
    return "'" + coord.replace("'", "''") + "'::jsonb"


def escape_sql(value: str) -> str:
    """Экранировать строку для SQL (одинарные кавычки)"""
    if value is None:
        return "NULL"
    return "'" + value.replace("'", "''") + "'"


def generate_insert_sql(rooms_data: dict) -> str:
    """Сгенерировать SQL INSERT для таблицы room"""

    sql_lines = [
        "-- Миграция: перенос данных из rooms.json в map_app.room",
        "-- Сгенерировано автоматически",
        "",
        "INSERT INTO map_app.room (id, building_id, floor_number, number, name, room_type, coordinates) VALUES"
    ]

    values = []
    stats = {"total": 0, "by_type": {}, "buildings": 0}
    buildings_seen = set()

    # Проходим по всем корпусам
    for building_id, rooms in rooms_data.items():
        if not rooms:
            continue

        buildings_seen.add(building_id)

        for room in rooms:
            room_id = room.get("Id", "")
            number = room.get("Number", "")
            name = room.get("Name")  # может быть null
            room_type = room.get("RoomType", "")
            floor = room.get("Floor", 0)
            coordinates = room.get("Coordinates")  # может быть null

            floor_str = str(floor)
            coord_sql = format_coordinates(coordinates)
            name_sql = escape_sql(name)
            room_type_sql = escape_sql(room_type) if room_type else "NULL"

            values.append(
                f"    ('{room_id}', '{building_id}', '{floor_str}', "
                f"'{number}', {name_sql}, {room_type_sql}, {coord_sql})"
            )

            stats["total"] += 1
            if room_type:
                stats["by_type"][room_type] = stats["by_type"].get(room_type, 0) + 1

    stats["buildings"] = len(buildings_seen)

    sql_lines.append(',\n'.join(values))
    sql_lines.append(";")

    # Статистика
    print(f"\n📊 Статистика помещений:")
    print(f"   Всего: {stats['total']}")
    print(f"   Корпусов: {stats['buildings']}")
    for room_type, count in sorted(stats["by_type"].items()):
        print(f"   - {room_type}: {count}")

    return '\n'.join(sql_lines)


def main():
    root_dir = Path(__file__).parent

    rooms_json = root_dir / 'entrance_app' / 'rooms.json'
    output_sql = root_dir / 'app' / 'database' / 'sql' / 'V004__insert_rooms.sql'

    # Загрузка данных
    print(f"📖 Чтение {rooms_json}...")
    rooms_data = load_json(str(rooms_json))

    # Генерация SQL
    print("⚙️  Генерация SQL-миграции...")
    sql = generate_insert_sql(rooms_data)

    # Сохранение
    output_sql.parent.mkdir(parents=True, exist_ok=True)
    output_sql.write_text(sql, encoding='utf-8')
    print(f"\n💾 SQL сохранён в {output_sql}")

    print("\n✅ Миграция сгенерирована!")
    print("   Не забудьте создать db.changelog-rooms.xml и добавить <include> в master")


if __name__ == '__main__':
    main()
