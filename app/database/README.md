# Database Migrations

Миграции базы данных управляются через **Liquibase 4.24**.

## Структура директорий

```
database/
├── db.changelog-master.xml          # Точка входа — все include отсюда
│
├── schema/                          # Создание схемы и расширений
│   ├── 001-create-extensions.xml
│   └── 002-create-schema.xml
│
├── tables/                          # DDL: таблицы и индексы
│   ├── building.xml                 # Таблица building
│   ├── floor.xml                    # Таблица floor
│   ├── room.xml                     # Таблица room
│   ├── technical.xml                # Таблица technical
│   ├── entrance.xml                 # Таблица entrance
│   ├── grid.xml                     # Таблица grid
│   ├── path-cache.xml               # Таблица path_cache
│   └── indexes.xml                  # Индексы + триггеры
│
├── triggers/                        # SQL-триггеры и функции
│   └── update-grid-updated-at.sql
│
└── data/                            # DML: данные (SQL из JSON)
    ├── buildings.xml                # Changelog для buildings
    ├── buildings.sql                # INSERT-данные корпусов
    ├── floors.xml
    ├── floors.sql
    ├── technical.xml
    ├── technical.sql
    ├── rooms.xml
    └── rooms.sql
```

## Создание нового changeset-а

### 1. Добавить новую таблицу

Создайте файл `tables/<имя>.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<databaseChangeLog
        xmlns="http://www.liquibase.org/xml/ns/dbchangelog"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://www.liquibase.org/xml/ns/dbchangelog
                            http://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-4.24.xsd">

    <changeSet id="<имя-таблицы>" author="<ваше-имя>">
        <comment>Создание таблицы <ОПИСАНИЕ></comment>
        <createTable schemaName="map_app" tableName="<имя_таблицы>">
            <!-- columns -->
        </createTable>

        <rollback>
            <dropTable schemaName="map_app" tableName="<имя_таблицы>"/>
        </rollback>
    </changeSet>

</databaseChangeLog>
```

Добавьте `<include>` в `db.changelog-master.xml`:
```xml
<include file="tables/<имя>.xml" relativeToChangelogFile="true"/>
```

### 2. Добавить данные из JSON

1. Создайте Python-генератор в корне проекта (по аналогии с `generate_rooms_migration.py`)
2. Выходной путь: `app/database/data/<имя>.sql`
3. Создайте `data/<имя>.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<databaseChangeLog
        xmlns="http://www.liquibase.org/xml/ns/dbchangelog"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://www.liquibase.org/xml/ns/dbchangelog
        http://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-4.24.xsd">

    <changeSet id="<имя>" author="<ваше-имя>">
        <comment>Перенос данных из <источник> в таблицу <таблица></comment>
        <sqlFile path="<имя>.sql" relativeToChangelogFile="true" splitStatements="true"/>
        <rollback>
            <delete tableName="<таблица>" schemaName="map_app"/>
        </rollback>
    </changeSet>

</databaseChangeLog>
```

4. Добавьте `<include>` в `db.changelog-master.xml`:
```xml
<include file="data/<имя>.xml" relativeToChangelogFile="true"/>
```

### 3. Добавить триггер/функцию

1. Положите SQL в `triggers/<имя>.sql`
2. Вызовите через `<sqlFile>` в соответствующем changeset-е

## Запуск миграций

```bash
docker-compose -f app/docker-compose.yml run --rm liquibase update
```

## Откат миграций

```bash
# Откат всех изменений
docker-compose -f app/docker-compose.yml run --rm liquibase rollbackAll

# Откат до конкретного тега
docker-compose -f app/docker-compose.yml run --rm liquibase rollback --tag=<tag>
```

## Подключение к БД

- **Хост:** localhost
- **Порт:** 5434
- **БД:** map_app
- **Пользователь:** postgres
- **Пароль:** postgres
