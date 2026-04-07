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
        "INSERT INTO map_app.entrance (object_id, object_type, building_id, floor_number, x, y, room_number) VALUES"
    ]

    values = []
    stats = {"total": 0, "by_type": {}}

    for composite_key, objects in entrances_data.items():
        # Ключ вида "buildingId_floor"
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

    sql_lines.append(',\n'.join(values))
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
