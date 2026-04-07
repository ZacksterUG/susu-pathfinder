#!/usr/bin/env python3
"""
Генератор SQL-миграции для переноса данных о технических помещениях в map_app.technical
Использует floors.json (координаты, типы) и network_data.json (связи для лифтов/лестниц)

Типы технических помещений:
  - Лестница, Лифт (has_entrance=True, заполняется linked)
  - Туалет мужской, Туалет женский, Подсобное помещение, Гардероб, Пост охраны, Пункт питания (has_entrance=False)

Запуск: python generate_technical_migration.py
"""

import json
import re
from pathlib import Path


# Маппинг типов из floors.json в type таблицы technical
TYPE_MAPPING = {
    "Лестница": "Лестница",
    "Лифт": "Лифт",
    "Туалет мужской": "Туалет",
    "Туалет женский": "Туалет",
    "Подсобное помещение": "Подсобное",
    "Пост охраны": "Охрана",
    "Гардероб": "Гардероб",
    "Пункт питания": "Пункт питания",
}

# Типы, для которых has_entrance = True
ENTRANCE_TYPES = {"Лестница", "Лифт"}


def load_json(file_path: str):
    """Загрузить JSON-файл"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def build_linked_map(network_data: dict) -> dict:
    """
    Построить маппинг: object_id -> [список всех object_id в той же network]
    Только для сетей типа elevator и stairs.
    """
    linked_map = {}

    for building_id, building_data in network_data.items():
        networks = building_data.get("networks", [])
        for network in networks:
            network_type = network.get("type", "")
            if network_type not in ("elevator", "stairs"):
                continue

            # Собираем все ID объектов в этой сети
            object_ids = [obj["id"] for obj in network.get("objects", [])]

            # Для каждого объекта linked = все ОСТАЛЬНЫЕ объекты в сети
            for obj_id in object_ids:
                linked_map[obj_id] = [oid for oid in object_ids if oid != obj_id]

    return linked_map


def is_technical_type(infrastructure_type: str) -> bool:
    """Проверить, является ли тип техническим помещением"""
    return infrastructure_type in TYPE_MAPPING


def get_technical_type(infrastructure_type: str) -> str:
    """Получить тип для таблицы technical"""
    return TYPE_MAPPING.get(infrastructure_type, infrastructure_type)


def has_entrance(tech_type: str) -> bool:
    """Определить, нужно ли заполнять has_entrance"""
    return tech_type in ENTRANCE_TYPES


def format_coordinates(coord_str: str) -> str:
    """
    Преобразовать координаты из формата floors.json в JSONB-совместимый формат.
    Вход: '{"points":[{"x":240,"y":0},{"x":240,"y":65},...]}'
    Выход: тот же JSON, экранированный для SQL
    """
    if not coord_str or coord_str == "null":
        return "{}"
    # Экранируем одинарные кавычки для SQL
    return coord_str.replace("'", "''")


def format_linked_array(linked_ids: list) -> str:
    """
    Форматировать массив UUID для PostgreSQL.
    Вход: ['id1', 'id2']
    Выход: '{"id1","id2"}'
    """
    if not linked_ids:
        return "ARRAY[]::uuid[]"
    formatted = ",".join(f"'{oid}'" for oid in linked_ids)
    return f"ARRAY[{formatted}]::uuid[]"


def generate_insert_sql(floors_data: dict, network_data: dict) -> str:
    """Сгенерировать SQL INSERT для таблицы technical"""

    # Строим маппинг связей из network_data
    linked_map = build_linked_map(network_data)

    sql_lines = [
        "-- Миграция: перенос данных о технических помещениях в map_app.technical",
        "-- Сгенерировано автоматически",
        "-- Технические помещения: лестницы, лифты, туалеты, гардеробы, охрана, подсобные, пункты питания",
        "",
        "INSERT INTO map_app.technical (building_id, floor_number, name, type, coordinates, has_entrance, linked) VALUES"
    ]

    values = []
    stats = {"total": 0, "by_type": {}}

    # Структура floors_data: {"elevators": {building_id: [...]}, "stairs": {building_id: [...]}}
    # Проходим по всем секциям (elevators, stairs)
    for section_name, section_data in floors_data.items():
        if not isinstance(section_data, dict):
            continue

        # Проходим по всем корпусам внутри секции
        for building_id, items in section_data.items():
            if not items:
                continue

            for item in items:
                infra_type = item.get("InfrastructureObjectType", "")

                # Пропускаем, если это не техническое помещение
                if not is_technical_type(infra_type):
                    continue

                tech_type = get_technical_type(infra_type)
                obj_id = item.get("Id", "")
                name = item.get("Name", "") or tech_type
                floor_number = str(item.get("Floor", ""))
                coordinates = format_coordinates(item.get("Coordinates", ""))
                entrance = has_entrance(tech_type)

                # Определяем linked (только для лестниц и лифтов)
                linked_ids = []
                if entrance and obj_id in linked_map:
                    linked_ids = linked_map[obj_id]

                linked_sql = format_linked_array(linked_ids)

                # Экранируем name для SQL
                name_escaped = name.replace("'", "''")

                values.append(
                    f"    ('{building_id}', '{floor_number}', '{name_escaped}', "
                    f"'{tech_type}', '{coordinates}'::jsonb, {str(entrance).lower()}, {linked_sql})"
                )

                stats["total"] += 1
                stats["by_type"][tech_type] = stats["by_type"].get(tech_type, 0) + 1

    sql_lines.append(',\n'.join(values))
    sql_lines.append(";")

    # Статистика
    print(f"\n📊 Статистика технических помещений:")
    print(f"   Всего: {stats['total']}")
    for tech_type, count in sorted(stats["by_type"].items()):
        print(f"   - {tech_type}: {count}")

    return '\n'.join(sql_lines)


def main():
    root_dir = Path(__file__).parent

    floors_json = root_dir / 'entrance_app' / 'floors.json'
    network_json = root_dir / 'entrance_app' / 'network_data.json'
    output_sql = root_dir / 'app' / 'database' / 'sql' / 'V003__insert_technical.sql'

    # Загрузка данных
    print(f"📖 Чтение {floors_json}...")
    floors_data = load_json(str(floors_json))

    print(f"📖 Чтение {network_json}...")
    network_data = load_json(str(network_json))

    # Генерация SQL
    print("⚙️  Генерация SQL-миграции...")
    sql = generate_insert_sql(floors_data, network_data)

    # Сохранение
    output_sql.parent.mkdir(parents=True, exist_ok=True)
    output_sql.write_text(sql, encoding='utf-8')
    print(f"\n💾 SQL сохранён в {output_sql}")

    print("\n✅ Миграция сгенерирована!")
    print("   Не забудьте добавить <include> в db.changelog-master.xml")


if __name__ == '__main__':
    main()
