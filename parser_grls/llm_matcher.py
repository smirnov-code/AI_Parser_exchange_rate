import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# Загружаем переменные из файла .env
load_dotenv()

# Инициализируем клиент ProxyAPI
client = OpenAI(
    api_key=os.getenv("PROXY_API_KEY"),
    base_url="https://api.proxyapi.ru/v1"
)


def choose_best_match(drug_name, manufacturer, parsed_rows):
    """
    Отправляет список строк в DeepSeek и возвращает ID лучшей.
    parsed_rows: список словарей [{'id': 0, 'name': '...', 'manuf': '...'}, ...]
    """
    if not parsed_rows:
        return None

    # Формируем текст для LLM
    rows_text = "\n".join([
        f"ID: {row['id']} | Название: {row['name']} | Производитель: {row['manuf']}"
        for row in parsed_rows
    ])

    prompt = f"""
    Ты — ассистент фармацевта. Твоя задача — найти наиболее подходящую строку в реестре лекарственных средств.

    Пользователь ищет препарат с названием: "{drug_name}"
    Производитель (примерно): "{manufacturer}"

    Вот список найденных строк:
    {rows_text}

    Выбери ID той строки, которая лучше всего соответствует запросу (название должно быть максимально близким, производитель должен совпадать или быть синонимом).
    Если ни одна строка не подходит (например, название совершенно другое или это другое лекарство), верни "None".
    Верни ТОЛЬКО JSON в формате: {{"id": <номер_id_или_None>}}
    """

    try:
        response = client.chat.completions.create(
            model="deepseek/deepseek-v4.1-flash",  # Используем быструю и дешевую модель
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.0  # Максимальная точность, без фантазий
        )

        result_text = response.choices[0].message.content
        result_json = json.loads(result_text)
        chosen_id = result_json.get("id")

        return chosen_id

    except Exception as e:
        print(f"    ❌ Ошибка LLM: {e}")
        return None