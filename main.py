import pandas as pd
import json
import math


def compare_excel_and_json(excel_path, json_path):
    print("🔄 Загрузка данных...")

    # 1. Загружаем Excel
    df = pd.read_excel(excel_path)

    # 2. Загружаем JSON с ответами
    with open(json_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)

    # Создаем словарь для быстрого поиска ответов из JSON по названию
    # (на случай, если порядок в JSON и Excel не совпадает)
    json_dict = {item["name_medicinal_product"].strip(): item["days"] for item in json_data}

    matches = 0
    total_compared = 0
    mismatches = []

    print("🔍 Сравнение результатов...\n")

    # 3. Проходим по строкам Excel
    for index, row in df.iterrows():
        drug_name = str(row['Номенклатура']).strip()
        expected = row['курс']

        # Если в Excel пусто (NaN), считаем, что правильный ответ - "Требует ручной проверки" или None
        if pd.isna(expected):
            expected_clean = "Требует ручной проверки"
        else:
            # Превращаем 20.0 в 20
            expected_clean = int(expected)

        # Ищем ответ модели для этого препарата
        got = json_dict.get(drug_name, "НЕТ В JSON")

        # Нормализуем ответ модели (если это число в виде строки, делаем int)
        if isinstance(got, (int, float)):
            if not math.isnan(got):
                got_clean = int(got)
            else:
                got_clean = "Требует ручной проверки"
        else:
            got_clean = str(got).strip()

        # Логика сравнения
        # Если в Excel пусто, а модель вернула "Требует ручной проверки" (или None) - это совпадение
        if expected_clean == "Требует ручной проверки" and got_clean in ["Требует ручной проверки", "None", None]:
            is_match = True
        elif expected_clean == got_clean:
            is_match = True
        else:
            is_match = False

        # Считаем статистику
        if not (expected_clean == "Требует ручной проверки" and got_clean == "НЕТ В JSON"):
            total_compared += 1
            if is_match:
                matches += 1
            else:
                mismatches.append({
                    "Препарат": drug_name,
                    "Ожидалось": expected_clean,
                    "Получено": got_clean
                })

    # 4. Выводим итоги
    if total_compared > 0:
        accuracy = (matches / total_compared) * 100
        print(f"{'=' * 50}")
        print(f"📊 ИТОГОВАЯ ТОЧНОСТЬ: {accuracy:.1f}% ({matches} из {total_compared})")
        print(f"{'=' * 50}\n")

    if mismatches:
        print(f"❌ НАЙДЕНЫ РАСХОЖДЕНИЯ ({len(mismatches)} шт.):")
        for err in mismatches:
            print(f"  • {err['Препарат']}")
            print(f"    Ожидалось: {err['Ожидалось']} | Получено: {err['Получено']}")
            print("-" * 40)
    else:
        print("🎉 Идеально! Все ответы совпали с эталоном.")


# Запуск
compare_excel_and_json('test_sample.xlsx', 'result.json')