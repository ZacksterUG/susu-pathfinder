import requests
import json
from datetime import datetime

BASE_URL = "https://online.susu.ru/microgateway/api/Map/Infrastructure/buildingId"

# Список buildingId
BUILDING_IDS = [
    "62f3830f-e7b8-49fb-b0bc-4a95244da786", "d83be114-f66c-4383-83c3-9c0f096a078b",
    "e10f1a4a-68e7-4e92-af13-343a2ba37ee7", "81ab6a1b-5c43-499e-b06e-9289745f2aaf",
    "ea98a106-c248-43a5-8d8e-2fcc2950169f", "bce65150-c95a-40cb-a59e-9774f5e1b249",
    "9c7a0f84-03b0-40b0-8fb0-992e1008c11e", "2adf108c-2394-4bcf-a0ec-151f5df8bd07",
    "3b011253-b7e5-43b4-a618-795a51393b2d", "a23d8946-baca-477c-9368-61abc77f90b0",
    "a6010bc2-5157-4c33-8cac-bce9bb01bc1c", "89d6e1ec-6eac-4bcc-b4b4-c2683f30f653",
    "d992a78c-d00f-42a2-ace1-a7e6fa8216b9", "06e7e741-405c-4019-9d13-3172aa4fefb7",
    "8ff4c2a3-d85f-4e29-9a61-0fabe46f4f56", "dfe3f44f-9fb5-4f47-8b6b-35a3bfd2ee65",
    "8ecdf06a-1acd-4f31-b25b-1c5e9051a826", "c1534c63-ebd0-400c-9f3d-cea4fd17bc1f",
    "3ee85d4c-bc56-45c4-957a-34fd1401d075", "a9781b13-37ac-4dfd-a691-a402309dd15a",
    "625d7e06-0632-49ce-9b5b-cb7755adfa2c", "05ce1485-31b1-4ba1-9eb7-532bc8e0f7d9",
    "8daaefe1-444b-4635-a639-550f760504c3", "bc1c5554-bcc6-499f-884d-25b8b5e42ad8",
    "19b87fc6-cf01-4909-9e5b-9caa419528be", "50fdc831-38d4-4e74-8c2d-bd194b26476a",
    "a8f48fd9-ea2f-4463-b6e8-48255afe800f", "4d22b5e4-e073-475f-b9ff-fa4671e869e0",
    "11c1d8e0-dc9b-450b-8a02-cc2c15075f99", "0db33e18-c2a0-43aa-a0f4-83ecd5ce7f81",
    "176fcafb-6d1d-4043-926e-302b1fec4c45", "e9e0d43e-f419-4f97-99d4-694c06d738d8"
]

# Заголовки из браузера
HEADERS = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Accept-Language': 'ru,en;q=0.9',
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJJZCI6IjhhMjVjMjAxLTg1NGMtNDYwNy1hY2NlLTM0YjgxNWE5ZjdjNiIsImh0dHA6Ly9zY2hlbWFzLnhtbHNvYXAub3JnL3dzLzIwMDUvMDUvaWRlbnRpdHkvY2xhaW1zL25hbWUiOiJldDI0MjJmYXY4IiwiaHR0cDovL3NjaGVtYXMubWljcm9zb2Z0LmNvbS93cy8yMDA4LzA2L2lkZW50aXR5L2NsYWltcy9yb2xlIjpbIkdyYWR1YXRlIiwiU3R1ZGVudCJdLCJhdWQiOlsiaHR0cHM6Ly9wd2Euc3VzdS5ydS8iLCJodHRwczovL29ubGluZS5zdXN1LnJ1IiwiaHR0cHM6Ly9wd2EtYmV0YS5zdXN1LnJ1IiwiaHR0cHM6Ly9wd2FsYi5zdXN1LnJ1Il0sImV4cCI6MTc3NTA2ODcwMywiaXNzIjoiU3VzdU9ubGluZSJ9.UJQtYmN6Ua0t_NXk2eT6Gs6ATOp3JntvLkt8P-lIILM',
    'Cookie': 'tmr_lvid=5f17f22d321a9d78dd60040c4d1da418; tmr_lvidTS=1767728752468; _ym_uid=1773381678708680115; _ym_d=1773381678; _ym_isad=1; domain_sid=bv8YItJOFpA02PSoqRGlY%3A1775063259438; _ym_visorc=w; tmr_detect=1%7C1775067102964',
    'Referer': 'https://online.susu.ru/map/floors',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 YaBrowser/26.3.0.0 Safari/537.36',
    'sec-ch-ua': '"Not(A:Brand";v="8", "Chromium";v="144", "YaBrowser";v="26.3", "Yowser";v="2.5"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin'
}

def save_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✓ Сохранено: {filename}")

def fetch_infrastructure(building_id):
    """Получить данные о лифтах и лестницах"""
    url = f"{BASE_URL}/{building_id}"
    headers = HEADERS
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200 and response.text.strip():
            return response.json()
        elif response.status_code == 404:
            return None
        else:
            print(f"   Статус: {response.status_code}")
            return {"raw_status": response.status_code, "raw_text": response.text[:500]}
    except Exception as e:
        print(f"   Ошибка: {e}")
        return None

def main():
    print("=== Сбор данных о лифтах и лестницах SUSU Map ===\n")
    
    results = {
        "elevators": {},
        "stairs": {},
        "raw_responses": {}
    }
    
    for i, building_id in enumerate(BUILDING_IDS, 1):
        print(f"[{i}/{len(BUILDING_IDS)}] Корпус {building_id}...")
        
        data = fetch_infrastructure(building_id)
        
        if data:
            # Сохраняем сырой ответ для анализа
            results["raw_responses"][building_id] = data
            
            # Пытаемся извлечь лифты и лестницы
            if isinstance(data, dict):
                if "elevators" in data and data["elevators"]:
                    results["elevators"][building_id] = data["elevators"]
                    print(f"   Лифты: {len(data['elevators'])}")
                if "stairs" in data and data["stairs"]:
                    results["stairs"][building_id] = data["stairs"]
                    print(f"   Лестницы: {len(data['stairs'])}")
                if "elevators" not in data and "stairs" not in data:
                    print(f"   Структура: {list(data.keys())}")
            else:
                print(f"   Формат: {type(data)}")
        else:
            print(f"   Нет данных")
    
    # Сохраняем результаты
    save_json(results, "infrastructure.json")
    
    # Статистика
    print("\n=== Итоги ===")
    print(f"Корпуса с лифтами: {len(results['elevators'])}")
    print(f"Корпуса с лестницами: {len(results['stairs'])}")
    print(f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
