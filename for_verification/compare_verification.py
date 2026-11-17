import json
import sys
from pathlib import Path

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def normalize_name(name):
    """Нормализует название для сопоставления."""
    if not isinstance(name, str):
        return name
    return " ".join(name.strip().lower().split())

def normalize_days(value):
    """Приводит значение course/days к int или None."""
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        value = value.strip()
        if value.isdigit():
            return int(value)
        digits = "".join(ch for ch in value if ch.isdigit())
        return int(digits) if digits else None
    return None

def is_bad(item):
    """Проверяет, является ли позиция БАДом (по полю type)."""
    t = item.get("type")
    if not isinstance(t, str):
        return False
    return t.strip().lower() == "бад"

def main():
    base = Path(__file__).parent
    test_path = base / "test_data_for_verification.json"
    result_path = base / "result_for_verification.json"

    if not test_path.exists() or not result_path.exists():
        print("Ошибка: не найдены test_data_for_verification.json или result_for_verification.json")
        sys.exit(1)

    test_data = load_json(test_path)
    result_data = load_json(result_path)

    if not isinstance(test_data, list) or not isinstance(result_data, list):
        print("Ошибка: оба файла должны содержать JSON-массивы.")
        sys.exit(1)

    # --- Исключаем БАДы из test_data ---
    filtered_test = [item for item in test_data if not is_bad(item)]
    excluded_bad_count = len(test_data) - len(filtered_test)

    # Строим словарь result по нормализованному названию
    result_map = {}
    for item in result_data:
        name = item.get("drug_name")
        if name is None:
            continue
        result_map[normalize_name(name)] = item

    total = len(filtered_test)
    matches = 0
    diffs = []
    missing_in_result = []

    for test_item in filtered_test:
        name = test_item.get("name_medicinal_product")
        code = test_item.get("code")
        expected_days = normalize_days(test_item.get("course"))
        key = normalize_name(name)

        result_item = result_map.get(key)

        if result_item is None:
            missing_in_result.append({
                "name": name,
                "code": code,
                "expected_days": expected_days,
                "reason": "нет в result_for_verification.json"
            })
            continue

        actual_days = normalize_days(result_item.get("days"))

        if expected_days == actual_days:
            matches += 1
        else:
            diffs.append({
                "name": name,
                "code": code,
                "expected_days": expected_days,
                "actual_days": actual_days,
                "reason": "несовпадение days"
            })

    # Позиции, которые есть в result, но отсутствуют в filtered_test (лишние)
    # При этом БАДы из result тоже не должны учитываться как "лишние",
    # если их нет в test — но мы не знаем их type в result.
    # Поэтому просто исключаем те, что не относятся к отфильтрованным именам.
    test_names = {normalize_name(item.get("name_medicinal_product")) for item in filtered_test}
    extra_in_result = [
        {"drug_name": item.get("drug_name"), "days": item.get("days")}
        for key, item in result_map.items()
        if key not in test_names
    ]

    percent = (matches / total * 100) if total else 0.0

    print(f"Исключено БАДов из рассмотрения: {excluded_bad_count}")
    print(f"Всего позиций в test (без БАД): {total}")
    print(f"Совпало: {matches}")
    print(f"Процент схожести: {percent:.2f}%")
    print()

    if diffs:
        print(f"Расхождения по days ({len(diffs)}):")
        for d in diffs:
            print(json.dumps(d, ensure_ascii=False, indent=2))
        print()

    if missing_in_result:
        print(f"Отсутствуют в результате ({len(missing_in_result)}):")
        for d in missing_in_result:
            print(json.dumps(d, ensure_ascii=False, indent=2))
        print()

    if extra_in_result:
        print(f"Лишние позиции в результате ({len(extra_in_result)}):")
        for d in extra_in_result:
            print(json.dumps(d, ensure_ascii=False, indent=2))
        print()

    if not diffs and not missing_in_result and not extra_in_result:
        print("Все позиции совпадают.")

if __name__ == "__main__":
    main()