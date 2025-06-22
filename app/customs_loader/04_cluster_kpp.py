import json
from pathlib import Path
from geopy.distance import geodesic

input_path = Path("data/osm_checkpoints_filtered.json")
output_path = Path("data/osm_checkpoints_clustered.json")

CLUSTER_RADIUS_KM = 1.0

with open(input_path, "r", encoding="utf-8") as f:
    elements = json.load(f).get("elements", [])

def get_coords(el):
    if "lat" in el and "lon" in el:
        return (el["lat"], el["lon"])
    elif "center" in el:
        return (el["center"]["lat"], el["center"]["lon"])
    return None

def get_country(el):
    return el.get("country_match")

def get_name(el):
    return el.get("tags", {}).get("name", "")

def get_name_length(el):
    return len(get_name(el))

processed = set()
clusters = []

for i, el in enumerate(elements):
    if i in processed:
        continue

    coords_i = get_coords(el)
    country_i = get_country(el)
    name_i = get_name(el)
    if not coords_i or not country_i:
        continue

    cluster = [el]
    processed.add(i)

    for j in range(i + 1, len(elements)):
        if j in processed:
            continue

        el_j = elements[j]
        coords_j = get_coords(el_j)
        country_j = get_country(el_j)
        if not coords_j or not country_j:
            continue

        if country_i != country_j:
            continue

        distance = geodesic(coords_i, coords_j).km
        if distance <= CLUSTER_RADIUS_KM:
            cluster.append(el_j)
            processed.add(j)

    # Сортируем кластер по длине имени
    cluster.sort(key=get_name_length, reverse=True)
    chosen = cluster[0]

    # Лог
    print(f"\n📍 Обрабатывается КПП: {name_i} ({coords_i[0]:.4f}, {coords_i[1]:.4f})")
    print(f" → Найдено в кластере: {len(cluster)}")
    for el_c in cluster:
        coords_c = get_coords(el_c)
        dist = geodesic(coords_i, coords_c).km
        print(f"    • {get_name(el_c)} ({coords_c[0]:.4f}, {coords_c[1]:.4f}) - {dist:.2f} км")

    print(f" ✅ Сохранён как главный: {get_name(chosen)}")

    clusters.append(chosen)

# Сохраняем результат
output_path.parent.mkdir(parents=True, exist_ok=True)
with open(output_path, "w", encoding="utf-8") as f:
    json.dump({"elements": clusters}, f, indent=2, ensure_ascii=False)

print(f"\n🎯 Кластеризация завершена. Было {len(elements)}, осталось {len(clusters)}.")
