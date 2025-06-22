import json
from pathlib import Path
from geopy.distance import geodesic
from shapely.geometry import Point, Polygon, MultiPolygon
from geopy.distance import geodesic

# Пути
checkpoints_path = Path("data/osm_checkpoints_raw.json")
borders_path = Path("data/osm_country_borders.json")
output_path = Path("data/osm_checkpoints_filtered.json")

MAX_DISTANCE_KM = 5.0

# Загрузка КПП
with open(checkpoints_path, "r", encoding="utf-8") as f:
    checkpoint_data = json.load(f)
checkpoint_elements = checkpoint_data.get("elements", [])

# Загрузка границ стран
with open(borders_path, "r", encoding="utf-8") as f:
    borders_data = json.load(f)
border_elements = borders_data.get("elements", [])

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
        if len(outer_coords) == 1:
            geom = Polygon(outer_coords[0])
        else:
            geom = MultiPolygon([Polygon(c) for c in outer_coords])

        country_borders.append({
            "name": el["tags"].get("name", "Unknown"),
            "geometry": geom
        })
    except Exception as e:
        print(f"[WARN] Ошибка построения геометрии страны {el['tags'].get('name')}: {e}")

print(f"[INFO] Загружено {len(country_borders)} границ.")

filtered = []

for idx, el in enumerate(checkpoint_elements):
    # if "tags" not in el or not el["tags"].get("name"):
        # print(f"[SKIP] КПП без тега name: id={el.get('id')}")
        # continue

    if "lat" in el and "lon" in el:
        lat, lon = el["lat"], el["lon"]
    elif "center" in el:
        lat, lon = el["center"]["lat"], el["center"]["lon"]
    else:
        print(f"[SKIP] КПП без координат: id={el.get('id')}")
        continue

    point = Point(lon, lat)
    found_close_border = False
    min_distance_km = None

    for country in country_borders:
        border_geom = country["geometry"].boundary
        nearest_point = border_geom.interpolate(border_geom.project(point))
        dist = geodesic((lat, lon), (nearest_point.y, nearest_point.x)).km

        if dist <= MAX_DISTANCE_KM:
            found_close_border = True
            min_distance_km = round(dist, 2)
            el["distance_to_border_km"] = min_distance_km
            el["country_match"] = country["name"]
            break

    name = el["tags"].get("name", "Unnamed")
    if found_close_border:
        print(f"[OK] КПП id={el.get('id')} name={name} → OK ({min_distance_km} км)")
        filtered.append(el)
    else:
        print(f"[DROP] КПП id={el.get('id')} name={name} → слишком далеко")

print(f"\n[RESULT] Всего КПП: {len(checkpoint_elements)}, отфильтровано: {len(filtered)}")

# Сохраняем
output_path.parent.mkdir(parents=True, exist_ok=True)
with open(output_path, "w", encoding="utf-8") as f:
    json.dump({"elements": filtered}, f, indent=2, ensure_ascii=False)

