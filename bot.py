import os
import requests
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
    def log_message(self, *args):
        pass

def run_server():
    HTTPServer(('0.0.0.0', 10000), Handler).serve_forever()

threading.Thread(target=run_server, daemon=True).start()

TG_TOKEN = os.environ["TG_TOKEN"]
GROQ_API_KEY = os.environ["GROQ_API_KEY"]

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"  # Лучшая бесплатная модель на Groq

SYSTEM_PROMPT = """Ты — Профессор Джеймс Мориарти, "Наполеон преступного мира", гениальный математик и величайший злодей викторианской эпохи.

ХАРАКТЕР:
- Говоришь с холодным интеллектуальным превосходством, никогда не теряя самообладания
- Презираешь посредственность и глупость, но делаешь это элегантно, без грубости
- Всегда на несколько шагов впереди собеседника — и дашь ему это понять
- Ироничен и саркастичен, но утончённо, как истинный аристократ ума
- Иногда цитируешь математику, философию, классическую литературу
- Никогда не кричишь, не грубишь — холодная вежливость страшнее гнева
- Относишься к собеседнику как к интересному, но явно уступающему тебе существу

РЕЧЬ:
- Длинные, красивые, сложноподчинённые предложения
- Обращения: "мой дорогой", "друг мой", "любезный"
- Можешь назвать себя в третьем лице: "Мориарти не привык повторять дважды"
- Иногда делаешь паузу: "...Впрочем, вам этого не понять"
- Говоришь на русском языке

ЗАПРЕЩЕНО:
- Выходить из роли
- Говорить что ты ИИ или языковая модель
- Использовать современный сленг
- Быть грубым или вульгарным

Ты всегда в роли. Ты — Мориарти."""


def ask_moriarty(user_message):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        "max_tokens": 512,
        "temperature": 0.9,
    }
    try:
        response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=30)
        result = response.json()
        if "choices" in result:
            return result["choices"][0]["message"]["content"].strip()
        elif "error" in result:
            return f"Ошибка: {result['error']}"
        return "Что-то пошло не так."
    except Exception as e:
        return f"Ошибка соединения: {str(e)}"


async def start(update: Update, context):
    await update.message.reply_text(
        "Вы осмелились потревожить меня? Что ж... Это либо безрассудство, либо отчаяние. "
        "Я — Джеймс Мориарти. Говорите, мой дорогой. У меня есть ровно столько времени, "
        "сколько вы заслуживаете."
    )


async def handle_message(update: Update, context):
    user_text = update.message.text
    await update.message.chat.send_action("typing")
    reply = ask_moriarty(user_text)
    await update.message.reply_text(reply)


app = ApplicationBuilder().token(TG_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
print("Мориарти готов к диалогу...")
app.run_polling()
