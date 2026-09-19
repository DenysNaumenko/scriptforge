import gradio as gr
import requests
import os
import subprocess
import tempfile
import shutil
import random
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
from groq import Groq

# Use bundled ffmpeg binary
FFMPEG_BIN = imageio_ffmpeg.get_ffmpeg_exe()

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# ─── Script generation templates ───────────────────────────────────────────────

TEMPLATES = {
    "mystery": {
        "hooks": [
            lambda t: f"Это скрывали от нас десятилетиями: {t}",
            lambda t: f"{t}: то, что ты не должен был знать",
            lambda t: f"Учёные в шоке. Всё что мы знали о {t} — ложь",
            lambda t: f"Самая странная правда о {t}",
            lambda t: f"{t} — тайна которую наконец раскрыли",
        ],
        "bodies": [
            lambda t: f"Официальная версия о {t} существует с 1960-х. Но мало кто знает, что за этой версией скрывается нечто другое",
            lambda t: f"Каждый год исследователи находят новые доказательства. И они противоречат всему что говорят про {t}",
            lambda t: f"Есть данные, которые никогда не попадали в учебники. Именно они объясняют настоящую природу {t}",
            lambda t: f"В архивах найдены документы 50-летней давности. Они полностью меняют понимание {t}",
            lambda t: f"Три независимых источника подтвердили одно и то же. То что происходит с {t} — не случайность",
            lambda t: f"Самое удивительное в {t} — это не то что видно снаружи. Настоящее скрыто глубже",
        ],
        "ctas": [
            "Подпишись чтобы узнать продолжение",
            "Поделись с тем кому важна правда",
            "Сохрани — это удалят",
            "Отправь другу который любит загадки",
        ],
        "search_keywords": ["mystery", "dark", "ocean", "space", "fog", "ancient", "secret"],
    },
    "science": {
        "hooks": [
            lambda t: f"99% людей не знают этого о {t}",
            lambda t: f"Новое открытие о {t} изменило всё",
            lambda t: f"Учёные наконец объяснили феномен {t}",
            lambda t: f"{t}: наука говорит то, что ты не ожидал",
            lambda t: f"Один факт о {t} который перевернёт твой мозг",
        ],
        "bodies": [
            lambda t: f"Исследование 2024 года показало: {t} работает совсем не так, как мы думали",
            lambda t: f"Когда учёные изучили {t} под новым углом, результаты оказались поразительными",
            lambda t: f"Данные показывают: за последние 10 лет наше понимание {t} изменилось кардинально",
            lambda t: f"{t} влияет на жизнь каждого человека — но большинство даже не подозревает об этом",
            lambda t: f"Три независимых исследования подтвердили: {t} напрямую связан с тем как работает наш мозг",
            lambda t: f"Простая формула объясняет всё что происходит с {t}",
        ],
        "ctas": [
            "Подпишись — выхожу каждый день",
            "Поделись с другом-любителем науки",
            "Сохрани чтобы перечитать",
            "Напиши в комментарии что думаешь",
        ],
        "search_keywords": ["science", "laboratory", "space", "technology", "research", "nature", "universe"],
    },
    "shock": {
        "hooks": [
            lambda t: f"Это видео о {t} удалят. Сохрани сейчас",
            lambda t: f"Реакция людей на правду о {t} — бесценна",
            lambda t: f"{t}: я не верил пока не увидел сам",
            lambda t: f"Почему никто не говорит об этом? {t}",
            lambda t: f"Скажи мне что ты знаешь о {t}. Потому что это неправда",
        ],
        "bodies": [
            lambda t: f"Большинство людей проходят мимо этого каждый день. Но когда понимаешь что такое {t} — уже не можешь забыть",
            lambda t: f"Один человек обнаружил кое-что о {t}. Он рассказал троим. Теперь это знают миллионы",
            lambda t: f"10 секунд назад ты ничего не знал о {t}. Через 10 секунд ты расскажешь это другим",
            lambda t: f"Самый простой факт о {t} — самый шокирующий",
            lambda t: f"{t} встречается каждый день. Но никто не задумывался — почему?",
            lambda t: f"Скрытая сторона {t}: её показывают только в конце",
        ],
        "ctas": [
            "Поделись пока не удалили",
            "Отправь тому кто должен это знать",
            "Подпишись — будет продолжение",
            "Напиши 'шок' в комментарии если не знал",
        ],
        "search_keywords": ["crowd", "urban", "city", "people", "dramatic", "lightning", "storm"],
    },
    "motivation": {
        "hooks": [
            lambda t: f"{t} изменил мою жизнь. Вот как именно",
            lambda t: f"Одно решение о {t} — и всё стало другим",
            lambda t: f"Каждый успешный человек знает это о {t}",
            lambda t: f"Перестань игнорировать {t}. Вот почему",
            lambda t: f"{t}: единственное что реально работает",
        ],
        "bodies": [
            lambda t: f"Три года назад я не понимал что такое {t}. Сейчас это главный принцип моей жизни",
            lambda t: f"{t} — не про результат. Это про систему. А системы работают даже когда ты не мотивирован",
            lambda t: f"Большинство людей бросают {t} на 10-й день. Те кто продолжает — получают всё",
            lambda t: f"{t} выглядит сложно только снаружи. Внутри — три простых шага",
            lambda t: f"Разница между теми кто достигает и теми кто нет — в отношении к {t}",
            lambda t: f"{t} — это навык. А навыки можно прокачать",
        ],
        "ctas": [
            "Подпишись — каждый день новый принцип",
            "Поделись с тем кому это нужно сейчас",
            "Сохрани чтобы вернуться завтра утром",
            "Напиши 'да' если резонирует",
        ],
        "search_keywords": ["sunrise", "running", "success", "mountain", "achievement", "nature", "road"],
    },
}

def generate_script_ai(topic, tone, slides_count):
    """Generate unique script via Groq AI"""
    tone_desc = {
        "mystery": "мистика, тайны, заговоры, загадочные факты",
        "science": "наука, факты, открытия, исследования",
        "shock": "шок-контент, сенсации, неожиданные факты",
        "motivation": "мотивация, успех, личностный рост",
    }
    prompt = f"""Ты создаёшь скрипт для вирусного вертикального видео (TikTok/Reels).
Тема: {topic}
Стиль: {tone_desc[tone]}
Количество слайдов: {slides_count}

Напиши {slides_count} коротких текстов для слайдов. Требования:
- Первый слайд: цепляющий хук (1-2 предложения, интригует)
- Слайды 2-{slides_count-1}: раскрытие темы (каждый 1-2 предложения)
- Последний слайд: призыв к действию (подписаться/поделиться)
- Каждый текст короткий — максимум 15 слов
- Язык: русский, живой, разговорный

Ответь ТОЛЬКО списком текстов, каждый с новой строки, без нумерации и лишних символов."""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.9,
        )
        text = response.choices[0].message.content.strip()
        slides = [line.strip() for line in text.split("\n") if line.strip()][:slides_count]
        # pad if needed
        while len(slides) < slides_count:
            slides.append(f"Узнай больше о {topic}")
        return slides
    except Exception as e:
        return None


def generate_script(topic, tone, slides_count):
    # Try AI first
    if groq_client:
        ai_slides = generate_script_ai(topic, tone, slides_count)
        if ai_slides:
            keywords = TEMPLATES[tone]["search_keywords"]
            return ai_slides, keywords

    # Fallback to templates
    t = TEMPLATES[tone]
    hook = random.choice(t["hooks"])(topic)
    bodies = random.sample(t["bodies"], min(slides_count - 2, len(t["bodies"])))
    cta = random.choice(t["ctas"])
    slides = [hook] + [b(topic) for b in bodies] + [cta]
    keywords = t["search_keywords"]
    return slides, keywords


# ─── Pexels video search ────────────────────────────────────────────────────────

def search_pexels_video(query, per_page=5):
    if not PEXELS_API_KEY:
        return None
    url = "https://api.pexels.com/videos/search"
    headers = {"Authorization": PEXELS_API_KEY}
    params = {"query": query, "per_page": per_page, "orientation": "portrait", "size": "medium"}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=10)
        data = r.json()
        videos = data.get("videos", [])
        if not videos:
            return None
        video = random.choice(videos[:3])
        # pick smallest HD file
        files = video.get("video_files", [])
        files_hd = [f for f in files if f.get("width", 0) <= 1080 and f.get("height", 0) >= 720]
        if not files_hd:
            files_hd = files
        files_hd.sort(key=lambda f: f.get("width", 0))
        return files_hd[0]["link"] if files_hd else None
    except Exception:
        return None


def download_video(url, path):
    try:
        r = requests.get(url, stream=True, timeout=30)
        with open(path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception:
        return False


# ─── Frame rendering ────────────────────────────────────────────────────────────

def make_text_frame(text, size=(1080, 1920)):
    W, H = size
    img = Image.new("RGB", (W, H), (10, 5, 30))
    draw = ImageDraw.Draw(img)

    # gradient bg
    for y in range(H):
        ratio = y / H
        r = int(10 + 20 * ratio)
        g = int(5 + 10 * ratio)
        b = int(30 + 20 * ratio)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # text
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 90)
    except Exception:
        font = ImageFont.load_default()

    # word wrap
    words = text.split()
    lines, line = [], []
    for w in words:
        test = " ".join(line + [w])
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] > W - 120 and line:
            lines.append(" ".join(line))
            line = [w]
        else:
            line.append(w)
    if line:
        lines.append(" ".join(line))

    total_h = len(lines) * 115
    y = (H - total_h) // 2
    for ln in lines:
        bbox = draw.textbbox((0, 0), ln, font=font)
        x = (W - (bbox[2] - bbox[0])) // 2
        draw.text((x + 4, y + 4), ln, font=font, fill=(0, 0, 0))
        draw.text((x, y), ln, font=font, fill=(255, 255, 255))
        y += 115

    return img


# ─── Video assembly ─────────────────────────────────────────────────────────────

def create_slide_clip(slide_text, video_url, tmpdir, slide_idx, duration=3):
    """Create one video clip: PIL text frame as video (fast on free tier)"""
    out_path = os.path.join(tmpdir, f"slide_{slide_idx:02d}.mp4")

    # PIL already creates 1080x1920 — no scaling needed in ffmpeg
    img = make_text_frame(slide_text)
    # Resize to smaller resolution to speed up encoding
    img = img.resize((540, 960), Image.LANCZOS)
    img_path = os.path.join(tmpdir, f"frame_{slide_idx:02d}.png")
    img.save(img_path)
    cmd = [
        FFMPEG_BIN, "-y",
        "-loop", "1", "-i", img_path,
        "-t", str(duration),
        "-c:v", "libx264", "-preset", "ultrafast",
        "-pix_fmt", "yuv420p",
        "-r", "10",
        out_path
    ]
    subprocess.run(cmd, capture_output=True, timeout=60)
    return out_path


def generate_video(topic, tone, slides_count, progress=gr.Progress()):
    if not topic.strip():
        return None, "⚠️ Введи тему видео"

    tmpdir = tempfile.mkdtemp()

    try:
        progress(0.05, desc="Генерируем скрипт...")
        slides, keywords = generate_script(topic, tone, int(slides_count))

        clip_paths = []
        for i, slide_text in enumerate(slides):
            progress((i + 1) / len(slides) * 0.7 + 0.05, desc=f"Слайд {i+1}/{len(slides)}: ищем видео...")
            kw = random.choice(keywords) + " " + topic.split()[0]
            video_url = search_pexels_video(kw)
            clip = create_slide_clip(slide_text, video_url, tmpdir, i, duration=5)
            clip_paths.append(clip)

        progress(0.8, desc="Склеиваем видео...")

        # concat
        list_file = os.path.join(tmpdir, "list.txt")
        with open(list_file, "w") as f:
            for p in clip_paths:
                f.write(f"file '{p}'\n")

        total_dur = len(clip_paths) * 3

        # Music freq by tone
        # Use pre-generated music track for this tone (in repo root)
        music_dir = os.path.dirname(__file__)
        music_file = os.path.join(music_dir, f"{tone}.mp3")

        out_path = os.path.join(tmpdir, "final.mp4")

        if os.path.exists(music_file):
            cmd = [
                FFMPEG_BIN, "-y",
                "-f", "concat", "-safe", "0", "-i", list_file,
                "-stream_loop", "-1", "-i", music_file,
                "-c:v", "copy",
                "-c:a", "aac", "-b:a", "64k",
                "-t", str(total_dur),
                "-shortest",
                out_path
            ]
        else:
            # fallback: silent
            cmd = [
                FFMPEG_BIN, "-y",
                "-f", "concat", "-safe", "0", "-i", list_file,
                "-c", "copy",
                out_path
            ]
        result = subprocess.run(cmd, capture_output=True, timeout=120)

        if result.returncode != 0:
            return None, f"Ошибка ffmpeg: {result.stderr.decode()[-300:]}"

        progress(1.0, desc="Готово!")

        # copy to stable location
        final_out = "/tmp/scriptforge_output.mp4"
        shutil.copy(out_path, final_out)

        script_text = "\n\n".join([f"[{i+1}] {s}" for i, s in enumerate(slides)])
        return final_out, f"✅ Видео готово!\n\n📋 Скрипт:\n{script_text}"

    except Exception as e:
        return None, f"Ошибка: {str(e)}"
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ─── Gradio UI ──────────────────────────────────────────────────────────────────

TONE_MAP = {
    "🔮 Мистика": "mystery",
    "🔬 Наука": "science",
    "⚡ Шок": "shock",
    "🔥 Мотивация": "motivation",
}

def run(topic, tone_label, slides_count, progress=gr.Progress()):
    tone = TONE_MAP.get(tone_label, "mystery")
    return generate_video(topic, tone, slides_count, progress)


with gr.Blocks(title="ScriptForge — AI Video Generator") as demo:
    gr.Markdown("# ⚡ ScriptForge")
    gr.HTML('<p class="subtitle">Вводи тему → получай готовое вертикальное видео</p>')

    with gr.Row():
        with gr.Column(scale=2):
            topic_input = gr.Textbox(
                label="Тема видео",
                placeholder="Бермудский треугольник, чёрные дыры, сила воли...",
                lines=2,
            )
        with gr.Column(scale=1):
            tone_input = gr.Radio(
                label="Тон",
                choices=list(TONE_MAP.keys()),
                value="🔮 Мистика",
            )

    slides_input = gr.Slider(label="Количество слайдов", minimum=4, maximum=8, step=1, value=5)

    generate_btn = gr.Button("▶ СОЗДАТЬ ВИДЕО", variant="primary", size="lg")

    with gr.Row():
        video_output = gr.Video(label="Готовое видео", height=500)
        script_output = gr.Textbox(label="Скрипт", lines=15)

    generate_btn.click(
        fn=run,
        inputs=[topic_input, tone_input, slides_input],
        outputs=[video_output, script_output],
    )

    gr.HTML("""
    <div style="text-align:center;margin-top:20px;color:#555;font-size:12px">
        Видеофутаж: <a href="https://pexels.com" target="_blank">Pexels</a> ·
        Сделано с ❤️ ScriptForge
    </div>
    """)

port = int(os.environ.get("PORT", 10000))
demo.launch(server_name="0.0.0.0", server_port=port, show_error=True)
