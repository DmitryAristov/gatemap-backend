
import requests
import urllib.parse
import json
from pathlib import Path

query = """
[out:json][timeout:600];
(
  nwr["barrier"="border_control"];
  nwr["government"="border_control"];
  nwr["government"="customs"];
);
out center tags;
""".strip()

encoded_query = urllib.parse.quote(query)
url = f"https://overpass-api.de/api/interpreter?data={encoded_query}"

print("🔄 Загружаем КПП...")
response = requests.get(url)
response.raise_for_status()

data = response.json()

print(f"Загружено объектов: {len(data.get('elements', []))}")

output_path = Path("data/osm_checkpoints_raw.json")
output_path.parent.mkdir(parents=True, exist_ok=True)
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
