import os
import requests
from openai import OpenAI
from flask import Flask, render_template, request
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
import time
import io

load_dotenv()
app = Flask(__name__)

huggingface_key = os.getenv('HUGGINGFACE_API_KEY')
print(f"🔑 HuggingFace ключ: {'ДА' if huggingface_key else 'НЕТ'}")

# === OpenAI-совместимый клиент Hugging Face ===
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=os.getenv("HUGGINGFACE_API_KEY")
)

def generate_post_hf_deepseek(topic):
    print(f"Генерируем пост: '{topic}'")

    prompt = f"""Write a short, engaging Instagram post about '{topic}'. 
    Include 1–2 emojis, 2–3 relevant hashtags, and keep it under 120 characters. 
    Make it positive and inspiring."""

    try:
        completion = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V3.2-Exp:novita",  # Работает!
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.7
        )
        text = completion.choices[0].message.content.strip()
        print(f"УСПЕХ: {text}")
        return text
    except Exception as e:
        print(f"Ошибка API: {e}")
        return generate_post_zagl(topic)


def generate_post_zagl(topic):
    """Заглушка текста"""
    templates = {
        "кофе": "☕️ Утренний кофе - заряд энергии! #кофе #утро",
        "спорт": "💪 Тренировка = результат! #спорт #мотивация",
        "программирование": "💻 Кодим будущее! #программирование #IT",
        "путешествия": "✈️ Новые горизонты! #путешествия"
    }

    topic_lower = topic.lower()
    for key in templates:
        if key in topic_lower:
            return templates[key]

    return f"🎉 {topic}! #AI #Generated"


def generate_image_hf(prompt):
    """Генерация через HF API"""
    print(f"🎨 Генерируем: '{prompt}'")

    if not huggingface_key:
        return None, "❌ Нет API ключа"

    MODELS = [
        "stabilityai/stable-diffusion-xl-base-1.0",  # Новая!
        "runwayml/stable-diffusion-v1-5",
        "CompVis/stable-diffusion-v1-4"
    ]

    headers = {"Authorization": f"Bearer {huggingface_key}"}

    for model in MODELS:
        try:
            API_URL = f"https://api-inference.huggingface.co/models/{model}"
            payload = {"inputs": f"{prompt}, digital art, high quality, vibrant"}

            print(f"🔄 Модель: {model}")
            response = requests.post(API_URL, headers=headers, json=payload, timeout=45)

            if response.status_code == 200 and response.content:
                image = Image.open(io.BytesIO(response.content))
                os.makedirs("static/images", exist_ok=True)
                filename = f"static/images/gen_{int(time.time())}.png"
                image.save(filename)
                print(f"✅ Изображение: {filename}")
                return filename, None
            else:
                print(f"❌ {model}: {response.status_code}")

        except Exception as e:
            print(f"❌ {model}: {e}")
            continue

    return None, "⏳ Модели загружаются"


def generate_image_zagl(prompt):
    """✅ ИСПРАВЛЕННАЯ заглушка - ТОЛЬКО ASCII"""
    os.makedirs("static/images", exist_ok=True)

    # ✅ Русский → Английский
    translations = {
        "спорт": "SPORT", "кофе": "COFFEE", "программирование": "CODING",
        "путешествия": "TRAVEL", "фитнес": "FITNESS", "еда": "FOOD"
    }

    english = translations.get(prompt.lower(), "AI ART")

    img = Image.new('RGB', (512, 512), color=(70, 130, 180))
    d = ImageDraw.Draw(img)

    try:
        font = ImageFont.load_default()
        d.text((50, 200), f"{english}\n#AI #Generated", fill=(255, 255, 255), font=font)
    except:
        d.text((50, 200), "AI IMAGE", fill=(255, 255, 255))

    filename = f"static/images/gen_{int(time.time())}.png"
    img.save(filename)

    return filename, None


@app.route('/', methods=['GET', 'POST'])
def index():
    generated_text = None
    generated_image = None
    user_topic = ""
    error_message = None

    if request.method == 'POST':
        user_topic = request.form.get('topic', '').strip()

        if user_topic:
            # Текст
            generated_text = generate_post_hf_deepseek(user_topic)

            # Изображение
            image_path, img_error = generate_image_hf(user_topic)

            if not image_path:
                image_path, _ = generate_image_zagl(user_topic)
                if img_error:
                    error_message = img_error

            generated_image = image_path

    return render_template('index.html',
                           generated_text=generated_text,
                           generated_image=generated_image,
                           user_topic=user_topic,
                           error_message=error_message)


if __name__ == '__main__':
    print("🚀 Запуск...")
    app.run(debug=True, host='0.0.0.0', port=5000)