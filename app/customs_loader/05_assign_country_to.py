import json
from pathlib import Path
from shapely.geometry import Point
from geopy.distance import geodesic
from shapely.geometry import Polygon, MultiPolygon

# Пути
checkpoints_path = Path("data/osm_checkpoints_clustered.json")
borders_path = Path("data/osm_country_borders.json")
output_path = Path("data/osm_checkpoints_final.json")

MAX_DIST_KM = 10.0  # допускаем поиск второй страны чуть дальше

# Загрузка КПП
with open(checkpoints_path, "r", encoding="utf-8") as f:
    checkpoint_data = json.load(f)
checkpoint_elements = checkpoint_data.get("elements", [])

# Загрузка границ
with open(borders_path, "r", encoding="utf-8") as f:
    borders_data = json.load(f)
border_elements = borders_data.get("elements", [])

# Преобразуем границы в структуры
country_borders = []

for el in border_elements:
    if el["type"] != "relation" or "tags" not in el or "members" not in el:
        continue

    outer_coords = []
    for member in el["members"]:
        if member.get("role") == "outer" and "geometry" in member:
            coords = [(pt["lon"], pt["lat"]) for pt in member["geometry"]]
            if len(coords) >= 3:
                outer_coords.append(coords)

    if not outer_coords:
        continue

    try:
        geom = MultiPolygon([Polygon(c) for c in outer_coords]) if len(outer_coords) > 1 else Polygon(outer_coords[0])
        country_borders.append({
            "name": el["tags"].get("name", "Unknown"),
            "geometry": geom
        })
    except Exception as e:
        print(f"[WARN] Проблема с геометрией страны {el['tags'].get('name')}: {e}")

print(f"[INFO] Загружено {len(country_borders)} границ")

# Назначаем country_to
for cp in checkpoint_elements:
    lat = cp.get("lat") or cp.get("center", {}).get("lat")
    lon = cp.get("lon") or cp.get("center", {}).get("lon")
    if not lat or not lon:
        continue

    this_country = cp.get("country_match")
    point = Point(lon, lat)

    closest_country = None
    closest_dist = float("inf")

    for country in country_borders:
        if country["name"] == this_country:
            continue

        border = country["geometry"].boundary
        nearest = border.interpolate(border.project(point))
        dist = geodesic((lat, lon), (nearest.y, nearest.x)).km

        if dist < closest_dist and dist <= MAX_DIST_KM:
            closest_country = country["name"]
            closest_dist = dist

    if closest_country:
        cp["country_to"] = closest_country
        print(f"[SET] КПП {cp.get('tags', {}).get('name', 'Unnamed')} → country_to = {closest_country}")
    else:
        print(f"[MISS] КПП {cp.get('tags', {}).get('name', 'Unnamed')} → вторая страна не найдена")

# Сохраняем результат
output_path.parent.mkdir(parents=True, exist_ok=True)
with open(output_path, "w", encoding="utf-8") as f:
    json.dump({"elements": checkpoint_elements}, f, indent=2, ensure_ascii=False)

print(f"\n[RESULT] Обработано КПП: {len(checkpoint_elements)}")
