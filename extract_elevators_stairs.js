// Скрипт для извлечения данных о лифтах и лестницах из SUSU Map
// Запустить в консоли браузера (F12) на странице https://online.susu.ru

(async () => {
    console.log('=== Начало сбора данных о лифтах и лестницах ===\n');
    
    // Список buildingId из предыдущего запроса
    const buildingIds = [
        "62f3830f-e7b8-49fb-b0bc-4a95244da786", // ЛПК
        "d83be114-f66c-4383-83c3-9c0f096a078b", // 7Р
        "e10f1a4a-68e7-4e92-af13-343a2ba37ee7", // 13Г
        "81ab6a1b-5c43-499e-b06e-9289745f2aaf", // УДК
        "ea98a106-c248-43a5-8d8e-2fcc2950169f", // ЛкАС
        "bce65150-c95a-40cb-a59e-9774f5e1b249", // Восточное крыло
        "9c7a0f84-03b0-40b0-8fb0-992e1008c11e", // Западное крыло
        "2adf108c-2394-4bcf-a0ec-151f5df8bd07", // 2в
        "3b011253-b7e5-43b4-a618-795a51393b2d", // Л.к.
        "a23d8946-baca-477c-9368-61abc77f90b0", // Т.к.
        "a6010bc2-5157-4c33-8cac-bce9bb01bc1c", // 4
        "89d6e1ec-6eac-4bcc-b4b4-c2683f30f653", // УСК
        "d992a78c-d00f-42a2-ace1-a7e6fa8216b9", // 6
        "06e7e741-405c-4019-9d13-3172aa4fefb7", // СК
        "8ff4c2a3-d85f-4e29-9a61-0fabe46f4f56", // 10М
        "dfe3f44f-9fb5-4f47-8b6b-35a3bfd2ee65", // 12О
        "8ecdf06a-1acd-4f31-b25b-1c5e9051a826", // Ш21
        "c1534c63-ebd0-400c-9f3d-cea4fd17bc1f", // 78Б
        "3ee85d4c-bc56-45c4-957a-34fd1401d075", // 8Э
        "a9781b13-37ac-4dfd-a691-a402309dd15a", // 1а
        "625d7e06-0632-49ce-9b5b-cb7755adfa2c", // 1б
        "05ce1485-31b1-4ba1-9eb7-532bc8e0f7d9", // 2
        "8daaefe1-444b-4635-a639-550f760504c3", // 3
        "bc1c5554-bcc6-499f-884d-25b8b5e42ad8", // 3б
        "19b87fc6-cf01-4909-9e5b-9caa419528be", // 3г
        "50fdc831-38d4-4e74-8c2d-bd194b26476a", // 3д
        "a8f48fd9-ea2f-4463-b6e8-48255afe800f", // ДС
        "4d22b5e4-e073-475f-b9ff-fa4671e869e0", // 9А
        "11c1d8e0-dc9b-450b-8a02-cc2c15075f99", // 11Ч
        "0db33e18-c2a0-43aa-a0f4-83ecd5ce7f81", // 5б
        "176fcafb-6d1d-4043-926e-302b1fec4c45", // 5а
        "e9e0d43e-f419-4f97-99d4-694c06d738d8"  // Центральная часть
    ];
    
    const results = {
        elevators: {},
        stairs: {}
    };
    
    // Заголовки из браузера
    const headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'ru,en;q=0.9',
        'authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJJZCI6IjhhMjVjMjAxLTg1NGMtNDYwNy1hY2NlLTM0YjgxNWE5ZjdjNiIsImh0dHA6Ly9zY2hlbWFzLnhtbHNvYXAub3JnL3dzLzIwMDUvMDUvaWRlbnRpdHkvY2xhaW1zL25hbWUiOiJldDI0MjJmYXY4IiwiaHR0cDovL3NjaGVtYXMubWljcm9zb2Z0LmNvbS93cy8yMDA4LzA2L2lkZW50aXR5L2NsYWltcy9yb2xlIjpbIkdyYWR1YXRlIiwiU3R1ZGVudCJdLCJhdWQiOlsiaHR0cHM6Ly9wd2Euc3VzdS5ydS8iLCJodHRwczovL29ubGluZS5zdXN1LnJ1IiwiaHR0cHM6Ly9wd2EtYmV0YS5zdXN1LnJ1IiwiaHR0cHM6Ly9wd2FsYi5zdXN1LnJ1Il0sImV4cCI6MTc3NTA2ODcwMywiaXNzIjoiU3VzdU9ubGluZSJ9.UJQtYmN6Ua0t_NXk2eT6Gs6ATOp3JntvLkt8P-lIILM',
        'sec-ch-ua': '"Not(A:Brand";v="8", "Chromium";v="144", "YaBrowser";v="26.3", "Yowser";v="2.5"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'Referer': 'https://online.susu.ru/map/floors',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 YaBrowser/26.3.0.0 Safari/537.36'
    };
    
    // Функция запроса к API
    async function fetchInfrastructure(buildingId) {
        const url = `https://online.susu.ru/microgateway/api/Map/Infrastructure/buildingId/${buildingId}`;
        try {
            const response = await fetch(url, {
                method: 'GET',
                headers: headers
            });
            
            if (!response.ok) {
                console.warn(`⚠ Корпус ${buildingId}: статус ${response.status}`);
                return null;
            }
            
            return await response.json();
        } catch (error) {
            console.error(`✗ Корпус ${buildingId}: ошибка ${error.message}`);
            return null;
        }
    }
    
    // Обработка данных
    for (const buildingId of buildingIds) {
        console.log(`Обработка корпуса ${buildingId}...`);
        
        const data = await fetchInfrastructure(buildingId);
        
        if (!data) {
            continue;
        }
        
        // Извлекаем лифты
        if (data.elevators && Array.isArray(data.elevators)) {
            results.elevators[buildingId] = data.elevators.map(e => ({
                id: e.id,
                name: e.name,
                floors: e.floors,
                coordinates: e.coordinates || e.geometry
            }));
            console.log(`  ✓ Лифты: ${results.elevators[buildingId].length}`);
        }
        
        // Извлекаем лестницы
        if (data.stairs && Array.isArray(data.stairs)) {
            results.stairs[buildingId] = data.stairs.map(s => ({
                id: s.id,
                name: s.name,
                floors: s.floors,
                coordinates: s.coordinates || s.geometry
            }));
            console.log(`  ✓ Лестницы: ${results.stairs[buildingId].length}`);
        }
        
        // Если структура другая, сохраняем весь ответ для анализа
        if (!data.elevators && !data.stairs) {
            console.log(`  ? Структура ответа:`, Object.keys(data));
            results.elevators[buildingId] = data;
        }
        
        // Небольшая задержка между запросами
        await new Promise(r => setTimeout(r, 100));
    }
    
    // Вывод результатов
    console.log('\n=== Результаты ===\n');
    console.log(JSON.stringify(results, null, 2));
    
    // Копирование в буфер обмена
    const jsonString = JSON.stringify(results, null, 2);
    await navigator.clipboard.writeText(jsonString).catch(() => {
        console.log('\n⚠ Не удалось скопировать в буфер обмена. Скопируйте вывод выше.');
    });
    
    console.log('\n=== Сбор данных завершён ===');
    console.log('Данные скопированы в буфер обмена!');
    console.log(`Всего корпусов с лифтами: ${Object.keys(results.elevators).length}`);
    console.log(`Всего корпусов с лестницами: ${Object.keys(results.stairs).length}`);
    
})();
