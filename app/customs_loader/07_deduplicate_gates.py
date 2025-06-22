import json
from pathlib import Path

input_path = Path("data/osm_gates_linked.json")
output_path = Path("data/osm_gates_linked_deduplicated.json")

# Загружаем данные
with open(input_path, "r", encoding="utf-8") as f:
    linked_data = json.load(f)

# Создаём словарь: gate_id → список {checkpoint_id, dist, idx_in_linked_data}
gate_refs = {}

for idx, cp in enumerate(linked_data):
    for gate in cp["gates"]:
        gate_id = gate["id"]
        entry = {
            "checkpoint_idx": idx,
            "distance": gate["distance_to_checkpoint_km"]
        }
        gate_refs.setdefault(gate_id, []).append(entry)

# Оставляем только ближайшее вхождение
for gate_id, refs in gate_refs.items():
    if len(refs) <= 1:
        continue  # только у одного КПП — всё ок

    # Найдём ближайшее КПП
    closest = min(refs, key=lambda x: x["distance"])

    # Удалим из других КПП
    for ref in refs:
        if ref != closest:
            cp_idx = ref["checkpoint_idx"]
            linked_data[cp_idx]["gates"] = [
                g for g in linked_data[cp_idx]["gates"] if g["id"] != gate_id
            ]

# Сохраняем
output_path.parent.mkdir(parents=True, exist_ok=True)
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(linked_data, f, indent=2, ensure_ascii=False)

print(f"[OK] Завершено. Результат сохранён в: {output_path}")
