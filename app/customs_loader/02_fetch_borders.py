import requests
import json
from pathlib import Path
import urllib.parse

query = """
[out:json][timeout:600];
relation["admin_level"="2"]["boundary"="administrative"];
out geom;
""".strip()

encoded_query = urllib.parse.quote(query)
url = f"https://overpass-api.de/api/interpreter?data={encoded_query}"

print("🔄 Загружаем границы стран...")
response = requests.get(url, timeout=300)
response.raise_for_status()

data = response.json()

output_path = Path("data/osm_country_borders.json")
output_path.parent.mkdir(parents=True, exist_ok=True)
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"✅ Загружено {len(data.get('elements', []))} границ. Сохранено в {output_path}")
