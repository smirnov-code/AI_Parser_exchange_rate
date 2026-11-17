import json
import sys
from pathlib import Path


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def find_key_field(data):
    """Пытается угадать, по какому полю идентифицировать записи."""
    if isinstance(data, list) and data and isinstance(data[0], dict):
        # Приоритетные варианты имён
        for candidate in ["drug_name", "name", "Номенклатура", "Код", "id"]:
            if candidate in data[0]:
                return candidate
        # Иначе — первое строковое поле
        for k, v in data[0].items():
            if isinstance(v, str):
                return k
    return None


def normalize(value):
    """Приводит значения к сравнимому виду."""
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip().lower()
    return value


def compare_lists(test_data, result_data, key_field):
    """Сравнивает два списка словарей по ключевому полю."""
    test_map = {normalize(item.get(key_field)): item for item in test_data if key_field in item}
    result_map = {normalize(item.get(key_field)): item for item in result_data if key_field in item}

    all_keys = set(test_map.keys()) | set(result_map.keys())
    total = len(all_keys)
    matches = 0
    diffs = []

    for key in all_keys:
        t = test_map.get(key)
        r = result_map.get(key)

        if t is None:
            diffs.append({"key": key, "reason": "отсутствует в test_data", "test": None, "result": r})
            continue
        if r is None:
            diffs.append({"key": key, "reason": "отсутствует в result_data", "test": t, "result": None})
            continue

        # Сравниваем все поля, кроме ключевого
        fields = set(t.keys()) | set(r.keys())
        field_diffs = {}
        for f in fields:
            if f == key_field:
                continue
            tv = normalize(t.get(f))
            rv = normalize(r.get(f))
            if tv != rv:
                field_diffs[f] = {"test": t.get(f), "result": r.get(f)}

        if field_diffs:
            diffs.append({"key": key, "reason": "различие в полях", "details": field_diffs})
        else:
            matches += 1

    percent = (matches / total * 100) if total else 0.0
    return percent, total, matches, diffs

def compare_dicts(test_data, result_data):
    """Сравнивает два словаря (ключ -> значение)."""
    all_keys = set(test_data.keys()) | set(result_data.keys())
    total = len(all_keys)
    matches = 0
    diffs = []

    for key in all_keys:
        tv = normalize(test_data.get(key))
        rv = normalize(result_data.get(key))
        if tv == rv:
            matches += 1
        else:
            diffs.append({"key": key, "test": test_data.get(key), "result": result_data.get(key)})

    percent = (matches / total * 100) if total else 0.0
    return percent, total, matches, diffs

def main():
    base = Path(__file__).parent
    test_path = base / "test_data_for_verification.json"
    result_path = base / "result_for_verification.json"

    if not test_path.exists() or not result_path.exists():
        print("Ошибка: не найдены файлы test_data_for_verification.json или result_for_verification.json в папке скрипта.")
        sys.exit(1)

    test_data = load_json(test_path)
    result_data = load_json(result_path)

    # Определяем тип структуры
    if isinstance(test_data, list) and isinstance(result_data, list):
        key_field = find_key_field(test_data) or find_key_field(result_data)
        if not key_field:
            print("Не удалось определить ключевое поле для сравнения списков.")
            sys.exit(1)
        print(f"Сравнение списков по полю: '{key_field}'")
        percent, total, matches, diffs = compare_lists(test_data, result_data, key_field)
    elif isinstance(test_data, dict) and isinstance(result_data, dict):
        print("Сравнение словарей по ключам.")
        percent, total, matches, diffs = compare_dicts(test_data, result_data)
    else:
        print("Ошибка: файлы имеют разную структуру или неподдерживаемый формат.")
        sys.exit(1)

    print(f"\nВсего позиций: {total}")
    print(f"Совпало: {matches}")
    print(f"Процент схожести: {percent:.2f}%\n")

    if diffs:
        print(f"Найдено различий: {len(diffs)}")
        print("Позиции с различиями:")
        for d in diffs:
            print(json.dumps(d, ensure_ascii=False, indent=2))
    else:
        print("Различий не найдено — файлы идентичны.")

if __name__ == "__main__":
    main()