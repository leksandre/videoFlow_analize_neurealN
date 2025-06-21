from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from some import BOT_TOKEN, MODEL_PATH, SYSTEM_PROMPT, CHROMA_DB_DIR
from llama_cpp import Llama

# Инициализация модели
llm = Llama(
    model_path= MODEL_PATH,
    n_ctx=8192,  # Размер контекста
    n_threads=5,  # Количество потоков
    verbose=False,
)
print('Llama загружена')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот с LLM. Напиши мне что-нибудь.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    print("user_input - ", user_input)
    
    await update.message.reply_text('здравствуйте')
    
    # Генерация ответа с помощью модели
    output = llm.create_chat_completion(
        messages=[{"role": "user", "content": user_input}],
        max_tokens=256,
        temperature=0.7,
    )
    print(output)
    bot_response = output["choices"][0]["message"]["content"]
 
    print(bot_response)
    await update.message.reply_text(bot_response)

if __name__ == "__main__":
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    app.run_polling()