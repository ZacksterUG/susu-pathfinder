import requests
import json
from datetime import datetime

BASE_URL = "https://mapapi.susu.ru/integration/map"

def save_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✓ Сохранено: {filename}")

def fetch_buildings():
    """Получить список всех зданий"""
    url = f"{BASE_URL}/buildings"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()

def fetch_building_coordinates(building_id, floor):
    """Получить координаты коридоров этажа"""
    url = f"{BASE_URL}/BuildingCoordinates/buildingId/{building_id}/floor/{floor}"
    response = requests.get(url, timeout=30)
    if response.status_code == 200 and response.text.strip():
        try:
            return response.json()
        except:
            return {"raw": response.text}
    return None

def fetch_rooms(building_id):
    """Получить координаты кабинетов"""
    url = f"{BASE_URL}/rooms/buildingId/{building_id}"
    response = requests.get(url, timeout=30)
    if response.status_code == 200 and response.text.strip():
        try:
            return response.json()
        except:
            return {"raw": response.text}
    return None

def fetch_floors(building_id):
    """Получить информацию об этажах"""
    url = f"{BASE_URL}/floors/buildingId/{building_id}"
    response = requests.get(url, timeout=30)
    if response.status_code == 200 and response.text.strip():
        try:
            return response.json()
        except:
            return {"raw": response.text}
    return None

def main():
    print("=== Сбор данных API SUSU Map ===\n")
    
    # 1. Получаем список зданий
    print("1. Получаем список зданий...")
    buildings = fetch_buildings()
    save_json(buildings, "buildings.json")
    print(f"   Найдено зданий: {len(buildings)}\n")
    
    # 2. Для каждого здания получаем данные
    all_rooms = {}
    all_floors = {}
    all_coordinates = {}
    
    for building in buildings:
        building_id = building["Id"]
        building_name = building["ShortName"]
        print(f"2. Обработка корпуса {building_name} ({building_id})...")
        
        # Получаем этажи
        floors_data = fetch_floors(building_id)
        if floors_data:
            all_floors[building_id] = floors_data
            if isinstance(floors_data, list):
                print(f"   Этажи: {floors_data}")
            else:
                print(f"   Этажи: {floors_data}")
        
        # Получаем аудитории
        rooms_data = fetch_rooms(building_id)
        if rooms_data:
            all_rooms[building_id] = rooms_data
            if isinstance(rooms_data, list):
                print(f"   Аудиторий найдено: {len(rooms_data)}")
            else:
                print(f"   Аудитории: {rooms_data}")
        
        # Получаем координаты коридоров для каждого этажа (1-10)
        building_coords = {}
        for floor in range(1, 11):
            coords = fetch_building_coordinates(building_id, floor)
            if coords:
                building_coords[str(floor)] = coords
                print(f"   Этаж {floor}: коридоры есть")
        
        if building_coords:
            all_coordinates[building_id] = building_coords
        
        print()
    
    # Сохраняем результаты
    save_json(all_rooms, "rooms.json")
    save_json(all_floors, "floors.json")
    save_json(all_coordinates, "coordinates.json")
    
    print("=== Сбор данных завершён ===")
    print(f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
