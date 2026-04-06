#!/usr/bin/env python3
"""
Генератор SQL-миграции для переноса данных из buildings.json в таблицу map_app.building
Запуск: python generate_buildings_migration.py
"""

import json
import uuid
from pathlib import Path


def load_buildings(json_path: str) -> list:
    """Загрузить данные из buildings.json"""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_insert_sql(buildings: list) -> str:
    """Сгенерировать SQL INSERT для таблицы building"""
    sql_lines = [
        "-- Миграция: перенос данных из buildings.json в map_app.building",
        "-- Сгенерировано автоматически",
        "",
        "INSERT INTO map_app.building (id, name, short_name) VALUES"
    ]
    
    values = []
    for building in buildings:
        building_id = building.get('Id', str(uuid.uuid4()))
        name = building.get('Name', '').replace("'", "''")
        short_name = building.get('ShortName', '').replace("'", "''")
        
        values.append(
            f"    ('{building_id}', '{name}', '{short_name}')"
        )
    
    sql_lines.append(',\n'.join(values))
    sql_lines.append(";")
    
    return '\n'.join(sql_lines)


def main():
    # Пути относительно корня проекта
    root_dir = Path(__file__).parent
    buildings_json = root_dir / 'entrance_app' / 'buildings.json'
    output_sql = root_dir / 'app' / 'database' / 'sql' / 'V001__insert_buildings.sql'
    
    # Загрузка данных
    print(f"📖 Чтение {buildings_json}...")
    buildings = load_buildings(str(buildings_json))
    print(f"✅ Загружено {len(buildings)} корпусов")
    
    # Генерация SQL
    sql = generate_insert_sql(buildings)
    
    # Сохранение
    output_sql.parent.mkdir(parents=True, exist_ok=True)
    output_sql.write_text(sql, encoding='utf-8')
    print(f"💾 SQL сохранён в {output_sql}")
    
    # Вывод статистики
    print("\n📊 Корпуса:")
    for b in buildings:
        print(f"   - {b.get('Name', 'N/A')} ({b.get('ShortName', 'N/A')})")
    
    print("\n✅ Миграция сгенерирована!")
    print(f"   Для применения выполните: docker-compose -f app/docker-compose.yml run --rm liquibase --changeLogFile=database/sql/V001__insert_buildings.sql update")


if __name__ == '__main__':
    main()
