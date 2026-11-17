import os
import base64
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("PROXY_API_KEY"), base_url="https://api.proxyapi.ru/v1")

def solve_captcha_llm(image_path):
    """Отправляет картинку капчи в DeepSeek Vision (без рассуждений)."""
    try:
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')

        response = client.chat.completions.create(
            model="deepseek/deepseek-v4-flash-vision-exp",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": "Прочитай капчу. Верни ТОЛЬКО символы."},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                ]
            }],
            max_tokens=2000,
            temperature=0.0,
            extra_body={"thinking": {"type": "disabled"}} # Отключаем размышления
        )
        content = response.choices[0].message.content
        return content.strip().replace('"', '').replace("'", "").replace(" ", "") if content else None
    except Exception as e:
        print(f"    ❌ Ошибка LLM Vision: {e}")
        return None