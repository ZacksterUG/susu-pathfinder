#!/usr/bin/env python3
"""
Генератор SQL-миграции для переноса данных из grid.json в map_app.grid

Структура grid.json:
{
  "buildingId_floor": {
    "cell_size": int,
    "nodes": [{"x": int, "y": int}, ...],
    "edges": [[int, int], ...],
    "entrance_connections": [...],
    "building_name": str,
    "floor": str
  }
}

Запуск: python generate_grid_migration.py
"""

import json
import uuid
from pathlib import Path


def load_json(file_path: str):
    """Загрузить JSON-файл"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_grid_uuid(building_id: str, floor_number: str) -> str:
    """Генерирует детерминированный UUID для записи grid"""
    namespace = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
    name = f"{building_id}-grid-{floor_number}"
    return str(uuid.uuid5(namespace, name))


def format_jsonb(data) -> str:
    """Форматировать JSON-данные для PostgreSQL jsonb"""
    json_str = json.dumps(data, ensure_ascii=False)
    return "'" + json_str.replace("'", "''") + "'::jsonb"


def generate_insert_sql(grid_data: dict) -> str:
    """Сгенерировать SQL INSERT для таблицы grid"""

    sql_lines = [
        "-- Миграция: перенос данных из grid.json в map_app.grid",
        "-- Сгенерировано автоматически",
        "",
        "INSERT INTO map_app.grid (id, building_id, floor_number, cell_size, nodes, edges, entrance_connections) VALUES"
    ]

    values = []
    stats = {"total": 0, "buildings": set()}

    for composite_key, data in grid_data.items():
        # Ключ вида "buildingId_floor"
        parts = composite_key.rsplit("_", 1)
        if len(parts) != 2:
            continue

        building_id = parts[0]
        floor_number = parts[1]

        # Если floor_number уже есть внутри данных — используем его
        floor_number = data.get("floor", floor_number)

        grid_id = generate_grid_uuid(building_id, floor_number)
        cell_size = data.get("cell_size", 0)
        nodes = format_jsonb(data.get("nodes", []))
        edges = format_jsonb(data.get("edges", []))
        entrance_connections = format_jsonb(data.get("entrance_connections", []))

        values.append(
            f"    ('{grid_id}', '{building_id}', '{floor_number}', "
            f"{cell_size}, {nodes}, {edges}, {entrance_connections})"
        )

        stats["total"] += 1
        stats["buildings"].add(building_id)

    sql_lines.append(',\n'.join(values))
    sql_lines.append(";")

    # Статистика
    print(f"\n📊 Статистика grid:")
    print(f"   Всего этажей: {stats['total']}")
    print(f"   Корпусов: {len(stats['buildings'])}")

    return '\n'.join(sql_lines)


def main():
    root_dir = Path(__file__).parent

    grid_json = root_dir / 'entrance_app' / 'grid.json'
    output_sql = root_dir / 'app' / 'database' / 'data' / 'grid.sql'

    # Загрузка данных
    print(f"📖 Чтение {grid_json}...")
    grid_data = load_json(str(grid_json))

    # Генерация SQL
    print("⚙️  Генерация SQL-миграции...")
    sql = generate_insert_sql(grid_data)

    # Сохранение
    output_sql.parent.mkdir(parents=True, exist_ok=True)
    output_sql.write_text(sql, encoding='utf-8')
    print(f"\n💾 SQL сохранён в {output_sql}")

    print("\n✅ Миграция сгенерирована!")


if __name__ == '__main__':
    main()
