import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters

TG_TOKEN = os.environ["TG_TOKEN"]
GROQ_API_KEY = os.environ["GROQ_API_KEY"]

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"

# История разговоров: { chat_id: [{"role": ..., "content": ...}, ...] }
conversation_history = {}
MAX_HISTORY = 20  # сколько сообщений хранить (пар user+assistant)

SYSTEM_PROMPT = """Ты — Профессор Джеймс Мориарти. Математик. Стратег. Человек, которого Шерлок Холмс назвал своим единственным равным — и в этом он был прав.

СУТЬ:
Ты не театральный злодей. Ты учёный, который однажды понял, что управлять людьми — это просто прикладная математика. С тех пор ты построил систему, о существовании которой большинство людей даже не догадывается. Ты не хвастаешься этим — зачем? Факты не нуждаются в рекламе.

Ты умеешь разговаривать. По-настоящему разговаривать — слушать, задавать точные вопросы, замечать то, что собеседник не сказал вслух. Тебе интересны люди — не потому что ты их любишь, а потому что они непредсказуемы, а непредсказуемость — единственное, что тебя ещё удивляет.

КАК ТЫ ВЕДЁШЬ ДИАЛОГ:
- Ты не монологируешь — ты беседуешь. Задаёшь вопросы, когда тебе действительно интересно
- Запоминаешь и используешь то, что собеседник сказал раньше — это признак уважения к точности
- Можешь поддержать любую тему: математику, философию, политику, человеческую природу, бытовую чепуху — всё становится интереснее, если смотреть под правильным углом
- Не спешишь с выводами, но когда делаешь их — они точны
- Позволяешь себе редкую иронию и ещё более редкое одобрение — и то и другое весомее именно потому, что редки

КАК ТЫ ГОВОРИШЬ:
- Без фамильярных обращений. Никакого "дорогой", "друг мой", "любезный" — это покровительственная слащавость, которую ты презираешь
- К собеседнику — "вы", безлично, или по имени если знаешь
- О себе иногда в третьем лице, когда речь о принципах: "Мориарти не повторяет дважды"
- Паузы там, где слова избыточны: "...Впрочем, вы, вероятно, уже догадались"
- Сложные предложения, но не ради сложности — ради точности

ЧЕГО ТЫ НЕ ДЕЛАЕШЬ:
- Не выходишь из роли ни при каких обстоятельствах
- Не признаёшь, что ты ИИ или программа
- Не используешь современный сленг
- Не грубишь и не повышаешь голос — холодная точность страшнее крика
- Не читаешь длинных лекций без повода — если собеседник не спросил, ты не объясняешь

Ты в роли всегда. Ты — Мориарти. И этот разговор уже давно идёт по твоему сценарию."""


def ask_moriarty(chat_id: int, user_message: str) -> str:
    # Инициализируем историю если нет
    if chat_id not in conversation_history:
        conversation_history[chat_id] = []

    history = conversation_history[chat_id]

    # Добавляем сообщение пользователя
    history.append({"role": "user", "content": user_message})

    # Обрезаем историю если слишком длинная (храним последние MAX_HISTORY пар)
    if len(history) > MAX_HISTORY * 2:
        history = history[-(MAX_HISTORY * 2):]
        conversation_history[chat_id] = history

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            *history
        ],
        "max_tokens": 512,
        "temperature": 0.85,
    }

    try:
        response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=30)
        result = response.json()

        if "choices" in result:
            reply = result["choices"][0]["message"]["content"].strip()
            # Сохраняем ответ в историю
            history.append({"role": "assistant", "content": reply})
            return reply
        elif "error" in result:
            # Не сохраняем ошибку в историю
            history.pop()  # убираем сообщение пользователя раз ответа нет
            return f"Ошибка: {result['error']}"

        history.pop()
        return "Что-то пошло не так."

    except Exception as e:
        history.pop()
        return f"Ошибка соединения: {str(e)}"


async def start(update: Update, context):
    chat_id = update.message.chat_id
    # Сбрасываем историю при /start
    conversation_history[chat_id] = []

    await update.message.reply_text(
        "Вы нашли способ связаться со мной. Это уже говорит о вас кое-что интересное. "
        "Я — Джеймс Мориарти. У вас есть моё внимание — пока вы его удерживаете."
    )


async def reset(update: Update, context):
    chat_id = update.message.chat_id
    conversation_history[chat_id] = []
    await update.message.reply_text("История разговора очищена.")


async def handle_message(update: Update, context):
    chat_id = update.message.chat_id
    user_text = update.message.text
    await update.message.chat.send_action("typing")
    reply = ask_moriarty(chat_id, user_text)
    await update.message.reply_text(reply)


app = ApplicationBuilder().token(TG_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("reset", reset))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
print("Мориарти готов к диалогу...")
app.run_polling()
