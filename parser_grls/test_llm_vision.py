import os
import base64
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(
    api_key=os.getenv("PROXY_API_KEY"),
    base_url="https://api.proxyapi.ru/v1"
)


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def test_vision(image_path):
    if not os.path.exists(image_path):
        print(f"❌ Файл {image_path} не найден!")
        return

    print("Отправляем картинку в DeepSeek (reasoning_effort='low')...")
    base64_image = encode_image(image_path)

    try:
        response = client.chat.completions.create(
            model="deepseek/deepseek-v4-flash-vision-exp",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Прочитай капчу. Верни ТОЛЬКО символы."},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                    ]
                }
            ],
            max_tokens=500,  # Даем запас, чтобы модель успела и подумать, и ответить
            temperature=0.0,
            reasoning_effort="low"  # Пробуем снизить глубину размышлений
        )

        usage = response.usage
        print("\n--- СТАТИСТИКА РАСХОДА ТОКЕНОВ ---")
        print(f"Входные токены: {usage.prompt_tokens}")
        print(f"Выходные токены: {usage.completion_tokens}")

        reasoning_tokens = 0
        if hasattr(usage, 'completion_tokens_details') and usage.completion_tokens_details:
            reasoning_tokens = usage.completion_tokens_details.reasoning_tokens or 0
            print(f"Из них токенов на размышления: {reasoning_tokens}")

        content = response.choices[0].message.content
        reasoning = getattr(response.choices[0].message, 'reasoning', None)

        print("\n--- РЕЗУЛЬТАТ ---")
        if reasoning_tokens > 0:
            print(f"⚠️ Модель всё равно думала (reasoning_tokens = {reasoning_tokens}).")
        else:
            print("✅ Модель НЕ думала, сразу выдала ответ!")

        if content:
            print(f"✅ Распознанный текст: '{content.strip()}'")
        else:
            print(f"⚠️ Пустой ответ. Причина завершения: {response.choices[0].finish_reason}")

    except Exception as e:
        print(f"❌ Ошибка API: {e}")


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(current_dir, "test_cap.PNG")
    test_vision(image_path)