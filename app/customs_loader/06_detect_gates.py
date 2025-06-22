import json
import numpy as np
from pathlib import Path
from geopy.distance import geodesic
from sklearn.neighbors import BallTree

# Пути к файлам
checkpoints_path = Path("data/osm_checkpoints_final.json")
gates_raw_path = Path("data/osm_gates_raw.json")
output_path = Path("data/osm_gates_linked.json")

# Настройки
RADIUS_KM = 1.0
EARTH_RADIUS_KM = 6371.0

# Загрузка КПП
with open(checkpoints_path, "r", encoding="utf-8") as f:
    checkpoints = json.load(f)["elements"]

# Загрузка шлагбаумов
with open(gates_raw_path, "r", encoding="utf-8") as f:
    gates_raw = json.load(f)["elements"]

# Подготовка шлагбаумов
gate_coords = []
gate_info = []

for g in gates_raw:
    lat, lon = (g.get("lat"), g.get("lon")) if "lat" in g else (g["center"]["lat"], g["center"]["lon"])
    gate_coords.append([np.radians(lat), np.radians(lon)])
    gate_info.append({
        "id": g["id"],
        "lat": lat,
        "lon": lon,
        "tags": g.get("tags", {}),
        "type": g.get("type", "node")
    })

# Строим BallTree
tree = BallTree(np.array(gate_coords), metric='haversine')

# Привязка ворот к КПП
linked_data = []

for checkpoint in checkpoints:
    lat, lon = (checkpoint.get("lat"), checkpoint.get("lon")) if "lat" in checkpoint else (checkpoint["center"]["lat"], checkpoint["center"]["lon"])
    point_rad = np.radians([[lat, lon]])

    # Найти все индексы шлагбаумов в радиусе
    indices = tree.query_radius(point_rad, r=RADIUS_KM / EARTH_RADIUS_KM)[0]

    matched_gates = []
    for idx in indices:
        gate = gate_info[idx]
        dist = geodesic((lat, lon), (gate["lat"], gate["lon"])).km
        gate["distance_to_checkpoint_km"] = round(dist, 3)
        matched_gates.append(gate)

    linked_data.append({
        "checkpoint_id": checkpoint["id"],
        "checkpoint_name": checkpoint["tags"].get("name", "Unknown"),
        "checkpoint_lat": lat,
        "checkpoint_lon": lon,
        "gates": matched_gates
    })

    print(f"[INFO] КПП {checkpoint['id']} — найдено входов: {len(matched_gates)}")

# Сохраняем результат
output_path.parent.mkdir(parents=True, exist_ok=True)
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(linked_data, f, indent=2, ensure_ascii=False)

print(f"\n[RESULT] Обработано КПП: {len(linked_data)}")
