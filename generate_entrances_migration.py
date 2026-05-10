#!/usr/bin/env python3
"""
Генератор SQL-миграции для переноса данных из entrances.json в map_app.entrance

Структура entrances.json:
{
  "buildingId_floor": {
    "objectId": {
      "x": int,
      "y": int,
      "room_number": str,
      "type": str
    }
  }
}

Запуск: python generate_entrances_migration.py
"""

import json
from pathlib import Path


def load_json(file_path: str):
    """Загрузить JSON-файл"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_insert_sql(entrances_data: dict) -> str:
    """Сгенерировать SQL INSERT для таблицы entrance"""

    sql_lines = [
        "-- Миграция: перенос данных из entrances.json в map_app.entrance",
        "-- Сгенерировано автоматически",
        "",
    ]

    values = []
    stats = {"total": 0, "by_type": {}}

    # 1. Обычные входы (комнаты, лестницы, лифты)
    for composite_key, objects in entrances_data.items():
        if composite_key.startswith("_"):
            continue

        parts = composite_key.rsplit("_", 1)
        if len(parts) != 2:
            continue

        building_id = parts[0]
        floor_number = parts[1]

        for object_id, data in objects.items():
            obj_type = data.get("type", "")
            x = data.get("x", 0)
            y = data.get("y", 0)
            room_number = data.get("room_number", "")

            room_escaped = room_number.replace("'", "''")
            type_escaped = obj_type.replace("'", "''")

            values.append(
                f"    ('{object_id}', '{type_escaped}', '{building_id}', "
                f"'{floor_number}', {x}, {y}, '{room_escaped}')"
            )

            stats["total"] += 1
            stats["by_type"][obj_type] = stats["by_type"].get(obj_type, 0) + 1

    # 2. Входы в корпус
    be_values = []
    building_entrances = entrances_data.get("_building_entrances", {})
    for composite_key, entrances in building_entrances.items():
        parts = composite_key.rsplit("_", 1)
        if len(parts) != 2:
            continue

        building_id = parts[0]
        floor_number = parts[1]

        for entrance in entrances:
            obj_id = entrance.get("id", "")
            x = entrance.get("x", 0)
            y = entrance.get("y", 0)
            name = entrance.get("name", "вход")

            name_escaped = name.replace("'", "''")

            be_values.append(
                f"    ('{obj_id}', 'building_entrance', '{building_id}', "
                f"'{floor_number}', {x}, {y}, '{name_escaped}')"
            )

            stats["total"] += 1
            stats["by_type"]["building_entrance"] = stats["by_type"].get("building_entrance", 0) + 1

    # Формируем SQL
    if values:
        sql_lines.append("INSERT INTO map_app.entrance (object_id, object_type, building_id, floor_number, x, y, room_number) VALUES")
        sql_lines.append(',\n'.join(values))
        sql_lines.append(";")

    if be_values:
        if values:
            sql_lines.append("")
            sql_lines.append("-- Входы в корпус")
        sql_lines.append("INSERT INTO map_app.entrance (object_id, object_type, building_id, floor_number, x, y, room_number) VALUES")
        sql_lines.append(',\n'.join(be_values))
        sql_lines.append(";")

    # Статистика
    print(f"\n📊 Статистика входов:")
    print(f"   Всего: {stats['total']}")
    for obj_type, count in sorted(stats["by_type"].items()):
        print(f"   - {obj_type}: {count}")

    return '\n'.join(sql_lines)


def main():
    root_dir = Path(__file__).parent

    entrances_json = root_dir / 'entrance_app' / 'entrances.json'
    output_sql = root_dir / 'app' / 'database' / 'data' / 'entrances.sql'

    # Загрузка данных
    print(f"📖 Чтение {entrances_json}...")
    entrances_data = load_json(str(entrances_json))

    # Генерация SQL
    print("⚙️  Генерация SQL-миграции...")
    sql = generate_insert_sql(entrances_data)

    # Сохранение
    output_sql.parent.mkdir(parents=True, exist_ok=True)
    output_sql.write_text(sql, encoding='utf-8')
    print(f"\n💾 SQL сохранён в {output_sql}")

    print("\n✅ Миграция сгенерирована!")


if __name__ == '__main__':
    main()
