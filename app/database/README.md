# Liquibase миграции для базы данных map_app

## Структура файлов

```
database/
├── db.changelog-master.xml          # Главный файл changelog
├── db.changelog-buildings.xml       # Changelog для данных корпусов
├── db.changelog-floors.xml          # Changelog для данных этажей
├── 001-create-extensions.xml        # Расширения PostgreSQL (uuid-ossp)
├── 002-create-schema.xml            # Создание схемы map_app
├── 003-create-building-table.xml
├── 004-create-floor-table.xml
├── 005-create-room-table.xml
├── 006-create-technical-table.xml
├── 007-create-entrance-table.xml
├── 008-create-grid-table.xml
├── 009-create-path-cache-table.xml
├── 010-create-indexes.xml           # Индексы и триггеры
└── sql/
    ├── 010-create-trigger.sql       # Триггер updated_at
    ├── V001__insert_buildings.sql   # Данные: корпуса (из buildings.json)
    └── V002__insert_floors.sql      # Данные: этажи (из coordinates.json)
```

## Схема базы данных

Все таблицы создаются в схеме `map_app`:

| Таблица | Описание |
|---------|----------|
| building | Корпуса |
| floor | Этажи (с полигоном коридора) |
| room | Аудитории |
| technical | Технические объекты (лестницы, лифты, туалеты и т.д.) |
| entrance | Входы в помещения |
| grid | Навигационная сетка (JSON) |
| path_cache | Кэш путей между аудиториями |

## Запуск миграций

### Через Liquibase CLI

```bash
liquibase \
  --url="jdbc:postgresql://localhost:5432/your_database" \
  --username=your_user \
  --password=your_password \
  --changeLogFile=database/db.changelog-master.xml \
  update
```

### Через Docker

```bash
docker run --rm \
  -v $(pwd)/database:/liquibase/changelog \
  liquibase/liquibase \
  --url="jdbc:postgresql://host.docker.internal:5432/your_database" \
  --username=your_user \
  --password=your_password \
  --changeLogFile=changelog/db.changelog-master.xml \
  update
```

### Через Maven

```xml
<plugin>
    <groupId>org.liquibase</groupId>
    <artifactId>liquibase-maven-plugin</artifactId>
    <version>4.24.0</version>
    <configuration>
        <changeLogFile>database/db.changelog-master.xml</changeLogFile>
        <url>jdbc:postgresql://localhost:5432/your_database</url>
        <username>your_user</username>
        <password>your_password</password>
        <defaultSchemaName>map_app</defaultSchemaName>
    </configuration>
</plugin>
```

```bash
mvn liquibase:update
```

## Откат миграций

```bash
liquibase \
  --url="jdbc:postgresql://localhost:5432/your_database" \
  --username=your_user \
  --password=your_password \
  --changeLogFile=database/db.changelog-master.xml \
  rollbackCount 1
```

## Проверка статуса

```bash
liquibase \
  --url="jdbc:postgresql://localhost:5432/your_database" \
  --username=your_user \
  --password=your_password \
  --changeLogFile=database/db.changelog-master.xml \
  status
```

## Типы данных PostgreSQL

| Тип в схеме | Тип PostgreSQL |
|-------------|----------------|
| uuid | UUID |
| string | VARCHAR(n) |
| int | INTEGER |
| float | DOUBLE PRECISION |
| bool | BOOLEAN |
| json | JSONB |
| timestamp | TIMESTAMP WITH TIME ZONE |
| uuid[] | UUID[] (массив) |

## Особенности

1. **uuid-ossp** — расширение для генерации UUID
2. **JSONB** — бинарный JSON для эффективного хранения и поиска
3. **GIN-индекс** — для быстрого поиска по массиву `linked`
4. **Триггер** — автоматическое обновление `updated_at` в таблице `grid`
