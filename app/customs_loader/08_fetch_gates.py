import requests
import urllib.parse
import json
from pathlib import Path
from time import sleep

# Зона покрытия: грубо весь мир (можно ограничить под себя)
LAT_MIN, LAT_MAX = -60, 75
LON_MIN, LON_MAX = -180, 180
STEP = 20.0  # шаг в градусах (можно уменьшить)

output_path = Path("data/osm_gates_raw.json")
output_path.parent.mkdir(parents=True, exist_ok=True)

all_elements = []

print("🔄 Загружаем шлагбаумы по тайлам:")

for lat in range(int(LAT_MIN), int(LAT_MAX), int(STEP)):
    for lon in range(int(LON_MIN), int(LON_MAX), int(STEP)):
        south, north = lat, lat + STEP
        west, east = lon, lon + STEP

        query = f"""
        [out:json][timeout:60];
        (
          nwr["barrier"="lift_gate"]({south},{west},{north},{east});
        );
        out center tags;
        """.strip()

        encoded_query = urllib.parse.quote(query)
        url = f"https://overpass-api.de/api/interpreter?data={encoded_query}"

        print(f"📦 Запрос: ({south}, {west}) — ({north}, {east})")

        try:
            resp = requests.get(url)
            resp.raise_for_status()
            data = resp.json()
            elements = data.get("elements", [])
            all_elements.extend(elements)
            print(f"✅ Найдено: {len(elements)}")
        except Exception as e:
            print(f"❌ Ошибка: {e}")

        sleep(0.05)  # пауза между запросами, чтобы не словить бан

# Удаление дубликатов по ID
unique_elements = {el["id"]: el for el in all_elements}.values()
print(f"\n🧩 Всего уникальных объектов: {len(unique_elements)}")

# Сохраняем
with open(output_path, "w", encoding="utf-8") as f:
    json.dump({"elements": list(unique_elements)}, f, indent=2, ensure_ascii=False)
