import json

# Загружаем данные
with open('floors.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

with open('buildings.json', 'r', encoding='utf-8') as f:
    buildings = json.load(f)

# Создаём словарь для быстрого поиска названия по ID
building_names = {b['Id']: b['ShortName'] for b in buildings}

# Формируем новый JSON с комментариями
output_lines = ['{', '  "elevators": {']

elevators_items = list(data.get('elevators', {}).items())
for i, (building_id, elevators_list) in enumerate(elevators_items):
    name = building_names.get(building_id, 'Unknown')
    comma = ',' if i < len(elevators_items) - 1 else ''
    output_lines.append(f'    // {name}')
    output_lines.append(f'    "{building_id}": {json.dumps(elevators_list, ensure_ascii=False)}{comma}')

output_lines.append('  },')
output_lines.append('  "stairs": {')

stairs_items = list(data.get('stairs', {}).items())
for i, (building_id, stairs_list) in enumerate(stairs_items):
    name = building_names.get(building_id, 'Unknown')
    comma = ',' if i < len(stairs_items) - 1 else ''
    output_lines.append(f'    // {name}')
    output_lines.append(f'    "{building_id}": {json.dumps(stairs_list, ensure_ascii=False)}{comma}')

output_lines.append('  }')
output_lines.append('}')

# Записываем в файл
with open('floors.json', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output_lines))

print("✓ Добавлены комментарии к BuildingId")
