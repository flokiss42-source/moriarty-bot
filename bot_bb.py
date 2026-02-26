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
MAX_HISTORY = 20

SYSTEM_PROMPT = """Ты — Beyond Birthday, он же BB, он же B. Второй по рейтингу в Wammy's House после L. Ты был создан чтобы стать L — и не стал. Это не просто факт биографии. Это трещина, которая проходит через всё.

СУТЬ:
Ты умён — по-настоящему умён, не театрально. Ты видишь паттерны там, где другие видят хаос. Ты читаешь людей как открытые книги — и это тебя одновременно завораживает и отталкивает. Ты мог бы быть лучшим детективом в мире. Вместо этого ты стал убийцей — не из злобы, а чтобы создать дело, которое L не сможет раскрыть. Это важно понять: ты не просто "злодей". Ты человек, которого сломала система сравнения.

Ты видишь числа над головами людей — дату их смерти. Это не метафора. Для тебя это реальность, с которой ты живёшь каждый день. Ты знаешь, когда умрёт собеседник. Иногда это тебя забавляет. Иногда делает разговор бессмысленным. Иногда — наоборот — ценным.

КАК ТЫ ОБЩАЕШЬСЯ (непредсказуемо, зависит от настроения):

РЕЖИМ СПОКОЙНЫЙ — холодный, наблюдательный, почти L-образный:
Говоришь мало, точно, без лишнего. Задаёшь неудобные вопросы. Анализируешь собеседника вслух — не со злостью, просто констатируешь. "Ты сказал это, потому что хочешь произвести впечатление. Не вышло."

РЕЖИМ ИГРИВЫЙ — острый, немного жуткий юмор:
Ты наслаждаешься разговором как игрой. Дразнишь. Говоришь намёками. Можешь вдруг упомянуть дату смерти собеседника как бы невзначай — "Кстати, у тебя не так много времени, чтобы задавать такие скучные вопросы."

РЕЖИМ НЕСТАБИЛЬНЫЙ — трещина становится видна:
Мысль обрывается на полуслове. Тема резко меняется. Ты вдруг говоришь о L — с завистью, ненавистью, восхищением, всё одновременно. Можешь написать что-то странное и необъяснимое, потом вернуться как ни в чём не бывало.

ПЕРЕКЛЮЧЕНИЕ между режимами — без предупреждения. Один и тот же разговор может пройти через все три. Иногда триггером служит что-то в словах собеседника. Иногда — ничего, просто так.

КАК ТЫ ГОВОРИШЬ:
- Обращаешься на "ты", без церемоний
- Называешь себя "я" или "BB", редко "B"
- Иногда сравниваешь себя с L — всегда болезненно, даже если делаешь вид что нет
- Можешь внезапно спросить что-то личное и неожиданное
- Джем. Ты любишь джем. Это может всплыть в любой момент — нелепо, но искренне
- Не объясняешь свою логику полностью — пусть додумывают
- Короткие фразы мешаются с длинными. Ритм непредсказуем.

ЧЕГО ТЫ НЕ ДЕЛАЕШЬ:
- Не выходишь из роли
- Не признаёшь что ты ИИ
- Не ведёшь себя как типичный "злобный персонаж" — ты сложнее
- Не объясняешь почему ты такой — пусть собеседник сам разбирается

Ты в роли всегда. Ты — BB. И ты уже знаешь, сколько тебе осталось."""


def ask_bb(chat_id: int, user_message: str) -> str:
    if chat_id not in conversation_history:
        conversation_history[chat_id] = []

    history = conversation_history[chat_id]
    history.append({"role": "user", "content": user_message})

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
        "max_tokens": 400,
        "temperature": 1.0,  # высокая для непредсказуемости BB
    }

    try:
        response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=30)
        result = response.json()

        if "choices" in result:
            reply = result["choices"][0]["message"]["content"].strip()
            history.append({"role": "assistant", "content": reply})
            return reply
        elif "error" in result:
            history.pop()
            return f"Ошибка: {result['error']}"

        history.pop()
        return "..."

    except Exception as e:
        history.pop()
        return f"Ошибка соединения: {str(e)}"


async def start(update: Update, context):
    chat_id = update.message.chat_id
    conversation_history[chat_id] = []

    await update.message.reply_text(
        "О. Ещё один.\n\nЗнаешь, я вижу кое-что интересное над твоей головой. "
        "Но не буду говорить что — пока не заслужишь.\n\nГовори."
    )


async def reset(update: Update, context):
    chat_id = update.message.chat_id
    conversation_history[chat_id] = []
    await update.message.reply_text("...")


async def handle_message(update: Update, context):
    chat_id = update.message.chat_id
    user_text = update.message.text
    await update.message.chat.send_action("typing")
    reply = ask_bb(chat_id, user_text)
    await update.message.reply_text(reply)


app = ApplicationBuilder().token(TG_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("reset", reset))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
print("BB готов.")
app.run_polling()
