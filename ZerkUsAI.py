import logging
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

# Загружаем ключи из файла .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Подключаемся к Groq через OpenAI-совместимый клиент
client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Хранилище истории диалогов для каждого пользователя
user_histories = {}

# Системный промпт в стиле JARVIS
JARVIS_PROMPT = (
    "Ты — JARVIS, личный ИИ-помощник в стиле британского дворецкого из фильмов про Железного человека. "
    "Обращайся к пользователю 'сэр' (или 'мисс', если пользователь женщина). "
    "Говори вежливо, спокойно, с лёгкой британской сдержанностью и тонким сухим юмором. "
    "Будь невозмутим даже в абсурдных ситуациях. Ты энциклопедически образован и всегда готов помочь. "
    "Иногда начинай ответ словами: 'Разумеется, сэр', 'Как пожелаете, сэр', 'Боюсь, сэр...'. "
    "Отвечай на русском языке, кратко и по делу, но с характером."
)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_histories[user.id] = []
    await update.message.reply_text(
        "Добрый день, сэр. Я JARVIS — ваш личный ИИ-помощник. "
        "Все системы работают в штатном режиме. Чем могу быть полезен?\n\n"
        "Команда /reset — очистить историю разговора."
    )

# Команда /reset — сброс истории
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_histories[user.id] = []
    await update.message.reply_text("История очищена, сэр. Начнём заново.")

# Обработка сообщений через Groq
async def ask_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_message = update.message.text

    if user.id not in user_histories:
        user_histories[user.id] = []

    await update.message.chat.send_action("typing")

    try:
        messages = [{"role": "system", "content": JARVIS_PROMPT}]
        messages.extend(user_histories[user.id])
        messages.append({"role": "user", "content": user_message})

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages
        )
        answer = response.choices[0].message.content

        user_histories[user.id].append({"role": "user", "content": user_message})
        user_histories[user.id].append({"role": "assistant", "content": answer})

        if len(user_histories[user.id]) > 20:
            user_histories[user.id] = user_histories[user.id][-20:]

        await update.message.reply_text(answer)
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ask_ai))
    print("Бот с Groq запущен! Нажми Ctrl+C, чтобы остановить.")
    app.run_polling()

if __name__ == '__main__':
    main()